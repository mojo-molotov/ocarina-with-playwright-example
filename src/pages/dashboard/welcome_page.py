"""Igoristan's dashboard welcome page."""

from typing import TYPE_CHECKING, final

from ocarina.custom_errors.test_framework.pages import PageVerificationError
from ocarina.infra.playwright.mixins import PlaywrightTitleMixin
from ocarina.pom.base import POMBase
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from constants.pages.dashboard import DASHBOARD_URL
from lib.ext.ocarina.adapters.playwright.cli_getters import get_timeout
from lib.ext.playwright.pages.verify_elements_presence import verify_elements_presence
from lib.ext.playwright.pages.waits import wait_for_h1_contains, wait_for_title_contains

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver
    from playwright.sync_api import Page


@final
class DashboardWelcomePage(PlaywrightTitleMixin, POMBase):
    """Igoristan's dashboard welcome page."""

    def __init__(self, *, driver: PlaywrightDriver, url: str = DASHBOARD_URL) -> None:
        """Initialize dashboard welcome POM."""
        self._driver = driver
        self._URL = url
        self._logout_btn = '[data-testid="logout-btn"]'
        self._dashboard_protected_page_link = '[data-testid="go-to-nested-page-btn"]'
        self._missing_otp_msg = (
            "xpath=//*[contains(text(), 'requires OTP authentication')]"
        )

    def open(self) -> DashboardWelcomePage:
        """Open the page."""
        self._driver.submit(lambda page: page.goto(self._URL))
        return self

    def verify(self, *, timeout: float | None = None) -> DashboardWelcomePage:
        """Verify function."""
        try:
            if timeout is None:
                timeout = get_timeout()

            verify_elements_presence(
                driver=self._driver,
                selectors={
                    "Logout button": self._logout_btn,
                    "Go to nested page button": self._dashboard_protected_page_link,
                },
                page_title="the Igoristan dashboard welcome page",
                timeout=timeout,
            )

            wait_for_title_contains(self._driver, "Dashboard", timeout)
            wait_for_h1_contains(self._driver, "Dashboard", timeout)
        except PlaywrightTimeoutError as exc:
            raise PageVerificationError from exc

        return self

    def verify_missing_otp_msg_is_displayed(self) -> DashboardWelcomePage:
        """Verify the missing OTP msg is displayed."""
        try:
            timeout = get_timeout()

            verify_elements_presence(
                driver=self._driver,
                selectors={
                    "Missing OTP msg": self._missing_otp_msg,
                },
                timeout=timeout,
            )

        except PlaywrightTimeoutError as exc:
            raise PageVerificationError from exc

        return self

    def click_on_go_to_nested_page_btn(self) -> DashboardWelcomePage:
        """Click on go to nested page btn."""
        timeout = get_timeout()
        selector = self._dashboard_protected_page_link

        def _click(page: Page) -> None:
            page.locator(selector).first.click(timeout=timeout * 1000)

        self._driver.submit(_click)
        return self
