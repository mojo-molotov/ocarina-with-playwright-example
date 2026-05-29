"""Igoristan's random error page."""

from typing import TYPE_CHECKING, final

from ocarina.custom_errors.test_framework.pages import PageVerificationError
from ocarina.infra.playwright.mixins import PlaywrightTitleMixin
from ocarina.pom.base import POMBase
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from constants.pages.random_error_page import RANDOM_ERROR_PAGE_URL
from lib.ext.ocarina.adapters.playwright.cli_getters import get_timeout
from lib.ext.playwright.pages.waits import wait_for_title_contains

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver


@final
class RandomErrorPage(PlaywrightTitleMixin, POMBase):
    """Igoristan's random error page."""

    def __init__(
        self, *, driver: PlaywrightDriver, url: str = RANDOM_ERROR_PAGE_URL
    ) -> None:
        """Initialize random error POM."""
        self._driver = driver
        self._URL = url

    def open(self) -> RandomErrorPage:
        """Open the page."""
        self._driver.submit(lambda page: page.goto(self._URL))
        return self

    def verify(self, *, timeout: float | None = None) -> RandomErrorPage:
        """Verify function."""
        try:
            if timeout is None:
                timeout = get_timeout()

            expected_title_needle = "-404-"

            wait_for_title_contains(self._driver, expected_title_needle, timeout)
        except PlaywrightTimeoutError as exc:
            raise PageVerificationError from exc

        return self
