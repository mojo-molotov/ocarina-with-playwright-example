"""Igoristan's donkey sausage eater detector page."""

from typing import TYPE_CHECKING, final

from ocarina.custom_errors.test_framework.pages import PageVerificationError
from ocarina.infra.playwright.mixins import PlaywrightTitleMixin
from ocarina.pom.base import POMBase
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from lib.ext.ocarina.adapters.playwright.cli_getters import get_timeout
from lib.ext.playwright.pages.verify_elements_presence import verify_elements_presence
from lib.ext.playwright.pages.waits import wait_for_title_contains

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver


@final
class BSODPage(PlaywrightTitleMixin, POMBase):
    """Igoristan's donkey sausage eater detector BSOD page."""

    def __init__(self, *, driver: PlaywrightDriver) -> None:
        """Initialize donkey sausage detector BSOD POM."""
        self._driver = driver
        self._watchdog_discriminant = (
            "xpath=//*[contains(text(), 'Corsica_watchdog.sys')]"
        )

    def verify(self, *, timeout: float | None = None) -> BSODPage:
        """Verify function."""
        try:
            if timeout is None:
                timeout = get_timeout()

            verify_elements_presence(
                driver=self._driver,
                selectors={
                    "Dialog box": self._watchdog_discriminant,
                },
                page_title="the Igoristan BSOD page",
                timeout=timeout,
            )

            wait_for_title_contains(self._driver, "You donkey sausage eater!", timeout)
        except PlaywrightTimeoutError as exc:
            raise PageVerificationError from exc

        return self
