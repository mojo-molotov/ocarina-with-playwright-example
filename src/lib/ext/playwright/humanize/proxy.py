"""Transparent Playwright wrapper that makes form typing human-like.

The Selenium port wrapped ``WebDriver``/``WebElement`` so that every
``send_keys`` became humanized without touching page-object code. Playwright's
page objects don't call ``send_keys`` on elements — they marshal work through
``PlaywrightDriver.submit`` — so the equivalent transparency is achieved with:

- ``HumanizedPlaywrightDriver``: a drop-in wrapper around a ``PlaywrightDriver``.
  It delegates everything (``submit``, ``quit``, ``save_screenshot``,
  ``set_default_timeout`` …) to the wrapped driver via ``__getattr__`` and only
  adds a ``keyboard_config`` and a humanized ``fill``.
- ``humanized_fill(driver, selector, text)``: the function page objects call. If
  the driver is a ``HumanizedPlaywrightDriver`` it types like a human (using the
  wrapper's config); otherwise it falls back to a plain ``locator.fill``. Page
  code is identical whether or not the driver is wrapped — exactly the
  transparent injection the Selenium ``HumanizedDriver`` provided.

Usage:
    driver = HumanizedPlaywrightDriver(raw_driver, wpm=125, typo_rate=0.14)
    page = ChaoticFormPage(driver=driver)  # typing is now humanized, transparently
"""

from typing import Any, Unpack

from ocarina.infra.playwright.driver import PlaywrightDriver

from lib.ext.playwright.humanize.keyboard import (
    KeyboardConfig,
    humanized_type_with_config,
)


# ``PlaywrightDriver`` is decorated ``@final`` upstream (unlike Selenium's
# ``WebDriver``, which the ocarina-example port subclasses freely). We still
# subclass it so the wrapper is a true ``PlaywrightDriver`` subtype for the type
# checker — the alternative (typing every consumer as a union) would ripple
# through the whole POM layer. The one ``misc`` ignore is the cost of that quirk.
class HumanizedPlaywrightDriver(PlaywrightDriver):  # type: ignore[misc]
    """Proxy for a ``PlaywrightDriver`` whose ``fill`` types like a human.

    Subclasses ``PlaywrightDriver`` so it is a drop-in wherever a
    ``PlaywrightDriver`` is expected — mirroring how the Selenium port's
    ``HumanizedDriver`` subclasses ``WebDriver`` (see ocarina-example). The
    parent ``__init__`` (which spawns a browser) is deliberately bypassed via
    ``object.__init__``: this is a *wrapper*, every method/attribute not defined
    here is transparently delegated to the wrapped driver through ``__getattr__``
    (``submit``, ``quit``, ``save_screenshot``, ``default_timeout_ms``, …).
    """

    def __init__(
        self, driver: PlaywrightDriver, **keyboard_config: Unpack[KeyboardConfig]
    ) -> None:
        """Wrap a ``PlaywrightDriver`` with a shared humanized-typing config.

        Args:
            driver:            The real ``PlaywrightDriver`` to wrap.
            **keyboard_config: Keyword arguments forwarded verbatim to
                               ``humanized_type`` (e.g. wpm=125, typo_rate=0.14).

        """
        object.__init__(self)
        self._driver = driver
        self._config = keyboard_config

    @property
    def keyboard_config(self) -> KeyboardConfig:
        """The humanized-typing configuration this wrapper applies."""
        return self._config

    def fill(self, selector: str, text: str) -> None:
        """Type ``text`` into ``selector`` like a human, on the owner thread."""
        config = self._config

        self._driver.submit(
            lambda page: humanized_type_with_config(page, selector, text, config)
        )

    def __getattr__(self, name: str):  # noqa: ANN204
        """Delegate any unrecognized attribute to the wrapped PlaywrightDriver."""
        return getattr(self._driver, name)


def humanized_fill(
    driver: PlaywrightDriver | HumanizedPlaywrightDriver, selector: str, text: str
) -> None:
    """Fill ``selector`` with ``text``, humanized when the driver is wrapped.

    Page objects always call this; whether typing is humanized depends solely on
    the driver they were handed — preserving transparent injection.
    """
    if isinstance(driver, HumanizedPlaywrightDriver):
        driver.fill(selector, text)
        return

    def _fill(page: Any) -> None:  # noqa: ANN401
        page.locator(selector).first.fill(text)

    driver.submit(_fill)
