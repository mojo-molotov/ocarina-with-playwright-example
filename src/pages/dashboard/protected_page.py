"""Igoristan's dashboard protected page."""

from typing import TYPE_CHECKING, final

from ocarina.custom_errors.test_framework.pages import PageVerificationError
from ocarina.infra.playwright.mixins import PlaywrightTitleMixin
from ocarina.pom.base import POMBase
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from constants.pages.dashboard import DASHBOARD_PROTECTED_PAGE_URL
from lib.ext.ocarina.adapters.playwright.cli_getters import get_timeout
from lib.ext.playwright.pages.verify_elements_presence import verify_elements_presence
from lib.ext.playwright.pages.waits import wait_for_h1_contains, wait_for_title_contains

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver
    from playwright.sync_api import Page


@final
class DashboardProtectedPage(PlaywrightTitleMixin, POMBase):
    """Igoristan's dashboard protected page."""

    def __init__(
        self, *, driver: PlaywrightDriver, url: str = DASHBOARD_PROTECTED_PAGE_URL
    ) -> None:
        """Initialize dashboard protected POM."""
        self._driver = driver
        self._URL = url
        self._logout_btn = '[data-testid="logout-btn"]'
        self._dashboard_home_link = 'a[href="/igoristan/dashboard"]'

    def open(self) -> DashboardProtectedPage:
        """Open the page."""
        self._driver.submit(lambda page: page.goto(self._URL))
        return self

    def verify(self, *, timeout: float | None = None) -> DashboardProtectedPage:
        """Verify function."""
        try:
            if timeout is None:
                timeout = get_timeout()

            verify_elements_presence(
                driver=self._driver,
                selectors={
                    "Logout button": self._logout_btn,
                    "Go back to dashboard button": self._dashboard_home_link,
                },
                page_title="the Igoristan dashboard protected page",
                timeout=timeout,
            )

            wait_for_title_contains(self._driver, "Dashboard secret feature", timeout)
            wait_for_h1_contains(self._driver, "Nested Dashboard", timeout)
        except PlaywrightTimeoutError as exc:
            raise PageVerificationError from exc

        return self

    def click_on_back_to_dashboard_btn(self) -> DashboardProtectedPage:
        """Click on back to dashboard button."""
        timeout = get_timeout()
        selector = self._dashboard_home_link

        def _click(page: Page) -> None:
            page.locator(selector).first.click(timeout=timeout * 1000)

        self._driver.submit(_click)
        return self
