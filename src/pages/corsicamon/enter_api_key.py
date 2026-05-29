"""Igoristan's corsicamon enter API key page."""

import random
from typing import TYPE_CHECKING, final

from ocarina.custom_errors.test_framework.pages import PageVerificationError
from ocarina.dsl.invariants.assertions import (
    is_positive,
)
from ocarina.dsl.invariants.validate import validate
from ocarina.infra.playwright.mixins import PlaywrightTitleMixin
from ocarina.pom.base import POMBase
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from constants.pages.corsicamon import CORSICAMON_PAGE_URL
from lib.ext.ocarina.adapters.agnostic.env_getters import create_env_getters
from lib.ext.ocarina.adapters.playwright.cli_getters import get_timeout
from lib.ext.ocarina.adapters.playwright.screenshotter import take_screenshot
from lib.ext.playwright.pages.verify_elements_presence import verify_elements_presence
from lib.ext.playwright.pages.waits import wait_for_h1_contains, wait_for_title_contains

if TYPE_CHECKING:
    from ocarina.custom_types.effect import Effect
    from ocarina.infra.playwright.driver import PlaywrightDriver
    from ocarina.ports.ilogger import ILogger


@final
class CorsicamonEnterApiKeyPage(PlaywrightTitleMixin, POMBase):
    """Igoristan's corsicamon enter API key page."""

    def __init__(
        self, *, driver: PlaywrightDriver, url: str = CORSICAMON_PAGE_URL
    ) -> None:
        """Initialize dashboard login POM."""
        self._URL = url
        self._driver = driver

        self._api_key_input = "#enter-api-key"
        self._back_to_igoristan_link = 'a[href="/igoristan/"]'
        self._access_corsicadex_btn = '[data-testid="access-corsicadex-btn"]'
        self._corsicamon_network_error_container = (
            '[data-testid="corsicadex-network-error"]'
        )
        self._corsicamon_network_error_retry_btn = (
            '[data-testid="corsicadex-network-error-retry-btn"]'
        )

        timeout = get_timeout()

        self._confirm_api_key_dispatchers: dict[str, Effect] = {
            "focus_api_key_input_then_press_enter": lambda: self._press_enter(
                self._api_key_input, timeout
            ),
            "click_access_corsicamon_button": lambda: self._click(
                self._access_corsicadex_btn, timeout
            ),
            "focus_access_corsicamon_button_then_press_enter": (
                lambda: self._press_enter(self._access_corsicadex_btn, timeout)
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

    def _network_error_is_showing(self, timeout: float) -> bool:
        """Wait up to ``timeout`` for the network-error container to APPEAR.

        Selenium's driver ran with an implicit wait, so the example detected
        success by waiting for the error container to be *invisible*, and the
        implicit wait gave the asynchronous error time to show up first.
        Playwright has no implicit wait, so a "wait for hidden" resolves
        instantly while the error is not yet in the DOM (lost race, breaks the
        retry loop prematurely). We instead wait for the error to appear: if it
        shows within ``timeout`` it is a failure (retry); if it never appears the
        key went through (success).
        """
        try:
            self._wait_visible(self._corsicamon_network_error_container, timeout)
        except PlaywrightTimeoutError:
            return False
        return True

    def _get_random_confirm_api_key_dispatchers_key(self) -> str:
        return random.choice(  # noqa: S311
            list(self._confirm_api_key_dispatchers.keys())
        )

    # --- public API -----------------------------------------------------------

    def open(self) -> CorsicamonEnterApiKeyPage:
        """Open the page."""
        self._driver.submit(lambda page: page.goto(self._URL))
        return self

    def verify(self, *, timeout: float | None = None) -> CorsicamonEnterApiKeyPage:
        """Verify function."""
        try:
            if timeout is None:
                timeout = get_timeout()

            verify_elements_presence(
                driver=self._driver,
                selectors={
                    "API key input": self._api_key_input,
                    "Back to Igoristan link": self._back_to_igoristan_link,
                    "Access Corsicadex button": self._access_corsicadex_btn,
                },
                page_title="Corsicamon enter API key page",
                timeout=timeout,
            )

            wait_for_title_contains(self._driver, "Corsicamon", timeout)
            wait_for_h1_contains(self._driver, "Enter API Key", timeout)
        except PlaywrightTimeoutError as exc:
            raise PageVerificationError from exc

        return self

    def click_retry_button(self) -> CorsicamonEnterApiKeyPage:
        """Click on the retry button."""
        timeout = get_timeout()
        self._click(self._corsicamon_network_error_retry_btn, timeout)
        return self

    def click_back_to_igoristan_link(self) -> CorsicamonEnterApiKeyPage:
        """Click on the back to Igoristan link."""
        timeout = get_timeout()
        self._click(self._back_to_igoristan_link, timeout)
        self._driver.submit(
            lambda page: page.locator(self._back_to_igoristan_link).first.wait_for(
                state="hidden", timeout=int(timeout * 1000)
            )
        )
        return self

    def fail_to_enter_api_key(self) -> CorsicamonEnterApiKeyPage:
        """Fail to enter API key."""
        timeout = get_timeout()

        self._fill(
            self._api_key_input,
            create_env_getters().get_value("igor_api_key") + "N-A-P-O-L-E-O-N",
            timeout,
        )

        self._confirm_api_key_dispatchers[
            self._get_random_confirm_api_key_dispatchers_key()
        ]()

        self._wait_visible(self._corsicamon_network_error_container, timeout)
        return self

    def enter_api_key(self) -> CorsicamonEnterApiKeyPage:
        """Enter API key."""
        timeout = get_timeout()

        self._fill(
            self._api_key_input,
            create_env_getters().get_value("igor_api_key"),
            timeout,
        )

        self._confirm_api_key_dispatchers[
            self._get_random_confirm_api_key_dispatchers_key()
        ]()
        return self

    def enter_api_key_with_retries(
        self, *, retries: int, logger: ILogger
    ) -> CorsicamonEnterApiKeyPage:
        """Enter API key (n retries)."""
        validate(retries, name="retries").assert_that(
            is_positive
        ).execute().raise_if_invalid()

        attempts_count = 1
        self.enter_api_key()

        while attempts_count <= retries:
            timeout = get_timeout()
            if not self._network_error_is_showing(timeout):
                break

            current_url = self._driver.submit(lambda page: page.url)
            msg = (
                "Failed to enter the API Key."
                "\n"
                f"Life: {attempts_count}/{retries}"
                "\n"
                f"Current URL: {current_url}"
            )

            logger.warning(msg)
            take_screenshot(driver=self._driver, logger=logger, category="WARNING")
            self.click_retry_button()
            attempts_count += 1

        s = "s" if attempts_count > 1 else ""
        msg = f"Entered the API Key. After {attempts_count} attempt{s}."

        logger.info(msg)
        return self
