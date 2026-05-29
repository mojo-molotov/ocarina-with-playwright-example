"""Madness -> CORS Errors page."""

from typing import TYPE_CHECKING, final

from ocarina.custom_errors.test_framework.pages import PageVerificationError
from ocarina.infra.playwright.mixins import PlaywrightTitleMixin
from ocarina.pom.base import POMBase
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from lib.ext.ocarina.adapters.playwright.cli_getters import get_timeout
from lib.ext.playwright.pages.waits import (
    wait_for_h1_contains_ci,
    wait_for_title_contains,
)

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver
    from playwright.sync_api import Page


@final
class CorsPage(PlaywrightTitleMixin, POMBase):
    """Is madness."""

    def __init__(self, *, driver: PlaywrightDriver) -> None:
        """Initialize POM."""
        self._driver = driver
        self._use_api_anyway_btn = 'a[href="/igoristan/corsicamon"]'

    def verify(self, *, timeout: float | None = None) -> CorsPage:
        """Verify function."""
        try:
            if timeout is None:
                timeout = get_timeout()

            wait_for_title_contains(self._driver, "Madness", timeout)
            wait_for_h1_contains_ci(self._driver, "cors errors:", timeout)
        except PlaywrightTimeoutError as exc:
            raise PageVerificationError from exc

        return self

    def click_use_api_anyway_btn(self) -> CorsPage:
        """Click on use API anyway btn."""
        timeout = get_timeout()
        selector = self._use_api_anyway_btn

        def _click(page: Page) -> None:
            page.locator(selector).first.click(timeout=timeout * 1000)

        self._driver.submit(_click)
        return self
