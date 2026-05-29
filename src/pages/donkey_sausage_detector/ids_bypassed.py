"""Igoristan's donkey sausage eater detector page."""

from typing import TYPE_CHECKING, final

from ocarina.custom_errors.test_framework.pages import PageVerificationError
from ocarina.infra.playwright.mixins import PlaywrightTitleMixin
from ocarina.pom.base import POMBase
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from lib.ext.ocarina.adapters.playwright.cli_getters import get_timeout
from lib.ext.playwright.pages.verify_elements_presence import verify_elements_presence
from lib.ext.playwright.pages.waits import wait_for_hidden, wait_for_title_contains

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver
    from playwright.sync_api import Page


@final
class IDSBypassedPage(PlaywrightTitleMixin, POMBase):
    """Igoristan's donkey sausage eater detector IDS bypassed page."""

    def __init__(self, *, driver: PlaywrightDriver) -> None:
        """Initialize donkey sausage detector (IDS bypassed) POM."""
        self._back_to_igoristan_link = 'a[href="/igoristan/"]'
        self._driver = driver

    def verify(self, *, timeout: float | None = None) -> IDSBypassedPage:
        """Verify function."""
        try:
            if timeout is None:
                timeout = get_timeout()

            verify_elements_presence(
                driver=self._driver,
                selectors={
                    "Back to Igoristan link": self._back_to_igoristan_link,
                },
                page_title="the Igoristan DSED IDS bypassed page",
                timeout=timeout,
            )

            wait_for_title_contains(
                self._driver, "The donkey sausage eater detector", timeout
            )
        except PlaywrightTimeoutError as exc:
            raise PageVerificationError from exc

        return self

    def click_back_to_igoristan_link(self) -> IDSBypassedPage:
        """Click on the back to Igoristan link."""
        timeout = get_timeout()
        selector = self._back_to_igoristan_link

        def _click(page: Page) -> None:
            page.locator(selector).first.click(timeout=timeout * 1000)

        self._driver.submit(_click)

        wait_for_hidden(self._driver, selector, timeout)

        return self
