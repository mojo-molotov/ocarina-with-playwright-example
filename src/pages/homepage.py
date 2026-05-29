"""Igoristan's homepage."""

from typing import TYPE_CHECKING, final

from ocarina.custom_errors.test_framework.pages import PageVerificationError
from ocarina.infra.playwright.mixins import PlaywrightTitleMixin
from ocarina.pom.base import POMBase
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from constants.pages.homepage import HOMEPAGE_URL
from lib.ext.ocarina.adapters.playwright.cli_getters import get_timeout
from lib.ext.playwright.pages.waits import wait_for_h1_contains, wait_for_title_is

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver


@final
class Homepage(PlaywrightTitleMixin, POMBase):
    """Igoristan's homepage."""

    def __init__(self, *, driver: PlaywrightDriver, url: str = HOMEPAGE_URL) -> None:
        """Initialize homepage POM."""
        self._driver = driver
        self._URL = url

    def open(self) -> Homepage:
        """Open the page."""
        self._driver.submit(lambda page: page.goto(self._URL))
        return self

    def verify(self, *, timeout: float | None = None) -> Homepage:
        """Verify function."""
        try:
            if timeout is None:
                timeout = get_timeout()

            wait_for_title_is(self._driver, "Igoristan", timeout)
            wait_for_h1_contains(self._driver, "Igoristan", timeout)
        except PlaywrightTimeoutError as exc:
            raise PageVerificationError from exc

        return self
