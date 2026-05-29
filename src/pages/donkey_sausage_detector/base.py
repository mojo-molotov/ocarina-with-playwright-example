"""Igoristan's donkey sausage eater detector page."""

from typing import TYPE_CHECKING, Never, final

from ocarina.infra.playwright.mixins import PlaywrightTitleMixin
from ocarina.pom.base import POMBase

from constants.pages.donkey_sausage_eater_detector import (
    DONKEY_SAUSAGE_EATER_DETECTOR_URL,
)

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver


@final
class DonkeySausageEaterDetectorPage(PlaywrightTitleMixin, POMBase):
    """Igoristan's donkey sausage eater detector page."""

    def __init__(
        self,
        *,
        driver: PlaywrightDriver,
        url: str = DONKEY_SAUSAGE_EATER_DETECTOR_URL,
    ) -> None:
        """Initialize donkey sausage detector POM."""
        self._driver = driver
        self._URL = url

    def open(self) -> DonkeySausageEaterDetectorPage:
        """Open the page."""
        self._driver.submit(lambda page: page.goto(self._URL))
        return self

    def verify(self, *, timeout: float | None = None) -> Never:
        """Verify function."""
        msg = "Verify is undecidable on this POM, use matchers."
        raise NotImplementedError(msg)
