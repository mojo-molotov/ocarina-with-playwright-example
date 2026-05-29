"""Playwright utility that mimics human typing behavior when filling in fields.

Faithful port of the Selenium humanizer: instead of setting the value instantly
(``locator.fill``), it focuses the field and types character by character with
variable delays, occasional typos drawn from AZERTY keyboard neighbors, and two
realistic correction strategies (immediate and late). Where the Selenium version
called ``element.send_keys(...)``, this version drives the keyboard through a
Playwright ``Locator`` (``press_sequentially`` for text, ``press("Backspace")``
for corrections).

Because Playwright's sync objects are bound to the driver's owner thread, the
whole typing routine is meant to run *inside* a single ``PlaywrightDriver.submit``
call (see :mod:`lib.ext.playwright.humanize.proxy`), so the ``time.sleep`` pauses
happen on the owner thread, exactly like Selenium blocked the worker thread.

Usage:

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        page = p.chromium.launch().new_page()
        page.goto("https://example.com/login")
        humanized_type(page, "#username", "napoleon@mail.com", wpm=70, typo_rate=0.06)

"""

import random
import time
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page


class KeyboardConfig(TypedDict, total=False):
    """Typing configuration forwarded verbatim to humanized_type.

    All fields are optional — any omitted key falls back to the default
    value defined in humanized_type.

    Attributes:
        wpm:                       Target typing speed in words per minute.
        typo_rate:                 Probability of a typo on any given character.
        hesitation_rate:           Probability of a natural pause between keystrokes.
        burst_rate:                Probability of an unusually fast keystroke sequence.
        late_correction_rate:      Probability that a typo is corrected late rather
                                   than immediately.
        max_chars_before_noticing: Maximum characters typed after a typo before
                                   the user notices and corrects it.

    """

    wpm: int
    typo_rate: float
    hesitation_rate: float
    burst_rate: float
    late_correction_rate: float
    max_chars_before_noticing: int


_AZERTY_NEIGHBORS: dict[str, str] = {
    "a": "qzs",
    "z": "aeqs",
    "e": "rzd",
    "r": "etf",
    "t": "ryg",
    "y": "tuh",
    "u": "yij",
    "i": "uok",
    "o": "ipl",
    "p": "om",
    "q": "asz",
    "s": "qzaed",
    "d": "sefx",
    "f": "drgv",
    "g": "fthb",
    "h": "gynj",
    "j": "hukm",
    "k": "jil",
    "l": "kom",
    "w": "xsc",
    "x": "wcd",
    "c": "xvf",
    "v": "cbg",
    "b": "vnh",
    "n": "bmj",
    "m": "nk",
    "1": "2a",
    "2": "1ze3",
    "3": "2er4",
    "4": "3rt5",
    "5": "4ty6",
    "6": "5yu7",
    "7": "6ui8",
    "8": "7io9",
    "9": "8op0",
    "0": "9p",
}


def _is_typable(char: str) -> bool:
    """Return True if the character is eligible for a simulated typo."""
    return char.lower() in _AZERTY_NEIGHBORS and not char.isspace()


def _pick_blind_length(text: str, typo_index: int, max_chars: int) -> int:
    """Sample how many characters the user types after a typo before noticing it."""
    remaining = len(text) - typo_index - 1
    max_possible = min(max_chars, remaining)
    if max_possible <= 0:
        return 0

    return random.choices(  # noqa: S311
        range(1, max_possible + 1),
        weights=[1 / k for k in range(1, max_possible + 1)],
        k=1,
    )[0]


def _human_delay(base: float, burst_rate: float, hesitation_rate: float) -> None:
    """Sleep for a variable, human-like duration between two keystrokes."""
    r = random.random()  # noqa: S311

    if r < burst_rate:
        delay = base * random.uniform(0.2, 0.5)  # noqa: S311
    elif r < burst_rate + hesitation_rate:
        delay = base * random.uniform(2.5, 5.0)  # noqa: S311
    else:
        delay = random.gauss(base, base * 0.3)
        delay = max(delay, base * 0.1)

    time.sleep(delay)


def _press(locator: Locator, text: str) -> None:
    """Type literal ``text`` into the focused locator, one key event per char."""
    if text:
        locator.press_sequentially(text)


def _backspace(locator: Locator) -> None:
    """Erase one character before the caret."""
    locator.press("Backspace")


def humanized_type(  # noqa: PLR0912, PLR0913, PLR0915
    page: Page,
    selector: str,
    text: str,
    wpm: int = 80,
    typo_rate: float = 0.05,
    hesitation_rate: float = 0.08,
    burst_rate: float = 0.10,
    late_correction_rate: float = 0.6,
    max_chars_before_noticing: int = 6,
) -> None:
    """Type a string into a Playwright field in a human-like fashion.

    Focuses the element matched by ``selector``, clears it, then types ``text``
    character by character with variable keystroke delays, natural hesitations,
    bursts of fast typing, and two kinds of typo corrections: immediate
    (catch-and-fix right away) and late (keep typing for a few chars, then
    backspace back to the mistake and retype cleanly).

    Raises:
        ValueError: If any parameter is out of its valid range.

    """
    if wpm <= 0:
        msg = "wpm must be greater than 0"
        raise ValueError(msg)
    if not 0.0 <= typo_rate <= 1.0:
        msg = "typo_rate must be between 0.0 and 1.0"
        raise ValueError(msg)
    if not 0.0 <= hesitation_rate <= 1.0:
        msg = "hesitation_rate must be between 0.0 and 1.0"
        raise ValueError(msg)
    if not 0.0 <= burst_rate <= 1.0:
        msg = "burst_rate must be between 0.0 and 1.0"
        raise ValueError(msg)
    if burst_rate + hesitation_rate > 1.0:
        msg = "burst_rate + hesitation_rate must not exceed 1.0"
        raise ValueError(msg)
    if not 0.0 <= late_correction_rate <= 1.0:
        msg = "late_correction_rate must be between 0.0 and 1.0"
        raise ValueError(msg)
    if max_chars_before_noticing < 1:
        msg = "max_chars_before_noticing must be at least 1"
        raise ValueError(msg)

    base_delay = 60 / (wpm * 5)

    element = page.locator(selector).first
    element.click()
    element.fill("")

    i = 0
    while i < len(text):
        char = text[i]

        if _is_typable(char) and random.random() < typo_rate:  # noqa: S311
            neighbors = _AZERTY_NEIGHBORS[char.lower()]
            typo_char = random.choice(neighbors)  # noqa: S311
            if char.isupper():
                typo_char = typo_char.upper()

            if random.random() < late_correction_rate:  # noqa: S311
                blind_chars = _pick_blind_length(text, i, max_chars_before_noticing)
                actually_typed = min(blind_chars, len(text) - i - 1)
                blind_sequence = text[i + 1 : i + 1 + actually_typed]

                _press(element, typo_char)

                for c in blind_sequence:
                    _human_delay(base_delay, burst_rate, hesitation_rate)
                    _press(element, c)

                time.sleep(random.uniform(0.3, 0.7))  # noqa: S311

                for _ in range(actually_typed + 1):
                    delay = random.uniform(0.04, 0.18)  # noqa: S311
                    if random.random() < 0.1:  # noqa: PLR2004, S311
                        delay += random.uniform(0.1, 0.3)  # noqa: S311
                    time.sleep(delay)
                    _backspace(element)

                time.sleep(random.uniform(0.2, 0.5))  # noqa: S311

                _press(element, char)

                for c in blind_sequence:
                    _human_delay(base_delay, burst_rate, hesitation_rate)
                    _press(element, c)

                i += actually_typed + 1
                _human_delay(base_delay, burst_rate, hesitation_rate)
                continue

            _press(element, typo_char)
            _backspace(element)
            _press(element, char)
            time.sleep(random.uniform(0.1, 0.4))  # noqa: S311

        else:
            _press(element, char)
            if i < len(text) - 1:
                _human_delay(base_delay, burst_rate, hesitation_rate)

        i += 1


def humanized_type_with_config(
    page: Page,
    selector: str,
    text: str,
    config: KeyboardConfig,
) -> None:
    """Type a string into a Playwright field using a KeyboardConfig mapping."""
    humanized_type(page, selector, text, **config)
