"""Madness page."""

from typing import TYPE_CHECKING, Never, final

from ocarina.infra.playwright.mixins import PlaywrightTitleMixin
from ocarina.pom.base import POMBase

from constants.pages.madness import MADNESS_PAGE_URL

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver


@final
class MadnessPage(PlaywrightTitleMixin, POMBase):
    """Is madness."""

    def __init__(
        self, *, driver: PlaywrightDriver, url: str = MADNESS_PAGE_URL
    ) -> None:
        """Initialize POM."""
        self._driver = driver
        self._URL = url

    def open(self) -> MadnessPage:
        """Open the page."""
        self._driver.submit(lambda page: page.goto(self._URL))
        return self

    def verify(self, *, timeout: float | None = None) -> Never:
        """Verify function."""
        msg = "Verify is undecidable on this POM, use matchers."
        raise NotImplementedError(msg)
