"""Igoristan's corsicamon main page."""

import random
from contextlib import suppress
from typing import TYPE_CHECKING, final

from ocarina.custom_errors.test_framework.pages import PageVerificationError
from ocarina.dsl.invariants.assertions import is_positive
from ocarina.dsl.invariants.validate import validate
from ocarina.infra.playwright.mixins import PlaywrightTitleMixin
from ocarina.pom.base import POMBase
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from constants.pages.corsicamon import CORSICAMON_PAGE_URL
from lib.ext.ocarina.adapters.playwright.cli_getters import get_timeout
from lib.ext.ocarina.adapters.playwright.screenshotter import take_screenshot
from lib.ext.playwright.pages.verify_elements_presence import verify_elements_presence
from lib.ext.playwright.pages.waits import wait_for_hidden, wait_for_title_contains

if TYPE_CHECKING:
    from ocarina.custom_types.effect import Effect
    from ocarina.infra.playwright.driver import PlaywrightDriver
    from ocarina.ports.ilogger import ILogger
    from playwright.sync_api import Page


@final
class CorsicamonPage(PlaywrightTitleMixin, POMBase):
    """Igoristan's corsicamon main page."""

    def __init__(
        self, *, driver: PlaywrightDriver, url: str = CORSICAMON_PAGE_URL
    ) -> None:
        """Initialize dashboard login POM."""
        self._URL = url
        self._driver = driver

        self._back_to_igoristan_link = 'a[href="/igoristan/"]'
        self._new_draw_btn = '[data-testid="new-draw-btn"]'

        self._corsicamon_network_error_container = (
            '[data-testid="corsicadex-network-error"]'
        )
        self._corsicamon_network_error_retry_btn = (
            '[data-testid="corsicadex-network-error-retry-btn"]'
        )

        self._enter_id_input = "#enter-id-input"
        self._add_corsicamon_btn = '[data-testid="add-corsicamon-btn"]'

        self._invalid_id_msg = (
            "xpath=//*[contains(text(), 'Please enter a valid Corsicamon ID')]"
        )
        self._already_in_draw_msg = (
            "xpath=//*[contains(text(), 'is already in your draw!')]"
        )
        self._draw_complete_msg = "xpath=//*[contains(text(), 'Draw Complete!')]"
        self._failed_to_add_corsicamon_msg = (
            "xpath=//*[contains(text(), "
            "'Failed to load Corsicamon. Please try again.')]"
        )

        timeout = get_timeout()

        self._add_corsicamon_dispatchers: dict[str, Effect] = {
            "focus_add_corsicamon_input_then_press_enter": lambda: self._press_enter(
                self._add_corsicamon_btn, timeout
            ),
            "click_add_corsicamon_button": lambda: self._click(
                self._add_corsicamon_btn, timeout
            ),
            "focus_add_corsicamon_button_then_press_enter": lambda: self._press_enter(
                self._add_corsicamon_btn, timeout
            ),
        }

    # --- low-level marshalled primitives -------------------------------------

    def _press_enter(self, selector: str, timeout: float) -> None:
        self._driver.submit(
            lambda page: page.locator(selector).first.press(
                "Enter", timeout=int(timeout * 1000)
            )
        )

    def _click(self, selector: str, timeout: float) -> None:
        self._driver.submit(
            lambda page: page.locator(selector).first.click(timeout=int(timeout * 1000))
        )

    def _fill(self, selector: str, value: str, timeout: float) -> None:
        self._driver.submit(
            lambda page: page.locator(selector).first.fill(
                value, timeout=int(timeout * 1000)
            )
        )

    def _wait_visible(self, selector: str, timeout: float) -> None:
        self._driver.submit(
            lambda page: page.locator(selector).first.wait_for(
                state="visible", timeout=int(timeout * 1000)
            )
        )

    def _get_random_add_corsicamon_dispatchers_key(self) -> str:
        return random.choice(  # noqa: S311
            list(self._add_corsicamon_dispatchers.keys())
        )

    @staticmethod
    def _corsicamon_card_id(idx: int) -> str:
        """Corsicamon card ID area selector."""
        return f'[data-testid="pokemon-id-{idx}"]'

    def _read_card_id(self, idx: int, timeout: float) -> str:
        selector = self._corsicamon_card_id(idx)

        def _read(page: Page) -> str:
            loc = page.locator(selector).first
            loc.wait_for(state="visible", timeout=int(timeout * 1000))
            return loc.inner_text().replace("#", "")

        return self._driver.submit(_read)

    def _read_card_ids(self, timeout: float) -> list[str]:
        def _read(page: Page) -> list[str]:
            ids: list[str] = []
            for i in range(1, 4):
                loc = page.locator(self._corsicamon_card_id(i)).first
                loc.wait_for(state="visible", timeout=int(timeout * 1000))
                ids.append(loc.inner_text().replace("#", ""))
            return ids

        return self._driver.submit(_read)

    # --- public API -----------------------------------------------------------

    def open(self) -> CorsicamonPage:
        """Open the page."""
        self._driver.submit(lambda page: page.goto(self._URL))
        return self

    def verify(self, *, timeout: float | None = None) -> CorsicamonPage:
        """Verify function."""
        try:
            if timeout is None:
                timeout = get_timeout()

            verify_elements_presence(
                driver=self._driver,
                selectors={
                    "New draw button": self._new_draw_btn,
                    "Back to Igoristan link": self._back_to_igoristan_link,
                    "Add Corsicamon button": self._add_corsicamon_btn,
                    "Enter Corsicamon ID button": self._enter_id_input,
                    "First Corsicamon card": self._corsicamon_card_id(1),
                    "Second Corsicamon card": self._corsicamon_card_id(2),
                    "Third Corsicamon card": self._corsicamon_card_id(3),
                },
                page_title="Corsicamon page",
                timeout=timeout,
            )

            wait_for_title_contains(self._driver, "Corsicamon", timeout)
        except PlaywrightTimeoutError as exc:
            raise PageVerificationError from exc

        return self

    def click_back_to_igoristan_link(self) -> CorsicamonPage:
        """Click on the back to Igoristan link."""
        timeout = get_timeout()
        self._click(self._back_to_igoristan_link, timeout)
        wait_for_hidden(self._driver, self._back_to_igoristan_link, timeout)
        return self

    def enter_invalid_corsicamon_id(self) -> CorsicamonPage:
        """Enter the -1 id, then check the presence of an error message."""
        timeout = get_timeout()

        self._fill(self._enter_id_input, "-1", timeout)

        self._add_corsicamon_dispatchers[
            self._get_random_add_corsicamon_dispatchers_key()
        ]()

        self._wait_visible(self._invalid_id_msg, timeout)

        return self

    def enter_already_in_draw_corsicamon_id(self) -> CorsicamonPage:
        """Enter already in draw id, then check the presence of an error message."""
        timeout = get_timeout()

        corsicamon_id = self._read_card_id(random.randint(1, 3), timeout)  # noqa: S311

        self._fill(self._enter_id_input, corsicamon_id, timeout)

        self._add_corsicamon_dispatchers[
            self._get_random_add_corsicamon_dispatchers_key()
        ]()

        self._wait_visible(self._already_in_draw_msg, timeout)

        return self

    def enter_fresh_corsicamon_id(self, *, skip_check: bool = False) -> CorsicamonPage:
        """Enter fresh id, then check the presence of an error message."""
        timeout = get_timeout()

        corsicamon_ids = self._read_card_ids(timeout)

        corsicamon_id = random.choice(  # noqa: S311
            [str(i) for i in range(1, 9) if str(i) not in corsicamon_ids]
        )

        self._fill(self._enter_id_input, corsicamon_id, timeout)

        self._add_corsicamon_dispatchers[
            self._get_random_add_corsicamon_dispatchers_key()
        ]()

        if not skip_check:
            slow_timeout = 20  # Hard-coded since loaders are slow here.
            self._wait_visible(self._draw_complete_msg, slow_timeout)

        return self

    def enter_fresh_corsicamon_id_with_retries(
        self, *, retries: int, logger: ILogger
    ) -> CorsicamonPage:
        """Enter fresh Corsicamon ID (n retries)."""
        validate(retries, name="retries").assert_that(
            is_positive
        ).execute().raise_if_invalid()

        attempts_count = 1
        while attempts_count <= retries:
            self.enter_fresh_corsicamon_id(skip_check=True)
            timeout = get_timeout()
            with suppress(Exception):
                wait_for_hidden(self._driver, self._new_draw_btn, timeout)
                break

            current_url = self._driver.submit(lambda page: page.url)
            msg = (
                "Failed to enter fresh Corsicamon ID."
                "\n"
                f"Life: {attempts_count}/{retries}"
                "\n"
                f"Current URL: {current_url}"
            )

            logger.warning(msg)
            take_screenshot(driver=self._driver, logger=logger, category="WARNING")
            attempts_count += 1

        s = "s" if attempts_count > 1 else ""
        msg = f"Entered the fresh Corsicamon ID. After {attempts_count} attempt{s}."

        logger.info(msg)
        return self

    def make_a_new_draw(self, *, skip_check: bool = False) -> CorsicamonPage:
        """Make a new draw."""
        timeout = get_timeout()

        self._click(self._new_draw_btn, timeout)

        if not skip_check:
            slow_timeout = 20  # Hard-coded since loaders are slow here.
            self._wait_visible(self._new_draw_btn, slow_timeout)

        return self

    def make_a_new_draw_with_retries(
        self, *, retries: int, logger: ILogger
    ) -> CorsicamonPage:
        """Make a new draw (n retries)."""

        def _click_retry_button() -> CorsicamonPage:
            timeout = get_timeout()
            self._click(self._corsicamon_network_error_retry_btn, timeout)
            return self

        validate(retries, name="retries").assert_that(
            is_positive
        ).execute().raise_if_invalid()

        attempts_count = 1
        self.make_a_new_draw(skip_check=True)
        while attempts_count <= retries:
            slow_timeout = 20  # Hard-coded since loaders are slow here.
            with suppress(Exception):
                self._wait_visible(self._new_draw_btn, slow_timeout)
                break

            current_url = self._driver.submit(lambda page: page.url)
            msg = (
                "Failed to make a new draw."
                "\n"
                f"Life: {attempts_count}/{retries}"
                "\n"
                f"Current URL: {current_url}"
            )

            logger.warning(msg)
            take_screenshot(driver=self._driver, logger=logger, category="WARNING")
            _click_retry_button()
            attempts_count += 1

        s = "s" if attempts_count > 1 else ""
        msg = f"Made a new draw. After {attempts_count} attempt{s}."

        logger.info(msg)
        return self

    def verify_enter_id_field_empty(self) -> CorsicamonPage:
        """Verify enter ID field is empty."""
        timeout = get_timeout()
        selector = self._enter_id_input

        self._driver.submit(
            lambda page: page.wait_for_function(
                """sel => {
                    const e = document.querySelector(sel);
                    return !!e && e.value === '';
                }""",
                arg=selector,
                timeout=int(timeout * 1000),
            )
        )

        return self
