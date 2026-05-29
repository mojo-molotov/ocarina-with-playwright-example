"""Igoristan's random loaders page."""

from typing import TYPE_CHECKING, final

from ocarina.custom_errors.test_framework.pages import PageVerificationError
from ocarina.infra.playwright.mixins import PlaywrightTitleMixin
from ocarina.pom.base import POMBase
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from constants.pages.random_loaders import RANDOM_LOADERS_PAGE_URL
from lib.ext.ocarina.adapters.playwright.cli_getters import get_timeout
from lib.ext.playwright.pages.verify_elements_presence import verify_elements_presence
from lib.ext.playwright.pages.waits import wait_for_hidden, wait_for_title_contains

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver
    from playwright.sync_api import Page


_DECK = [
    "0JjQtNC4INC90LAg0YXRg9C5IQ==",
    "0J/QvtGI0ZHQuyDQvdCw0YXRg9C5IQ==",
    "0JjQtNC4INCyINC20L7Qv9GDIQ==",
    "0J/QuNC30LTQtdGGIQ==",
    "0J7RhdGD0LXRgtGMIQ==",
    "0JHQu9GPIQ==",
    "0IHQsSDRgtCy0L7RjiDQvNCw0YLRjCE=",
    "0KfRkdGA0YIg0L/QvtCx0LXRgNC4IQ==",
    "0KLRiyDQvNC10L3RjyDQtNC+0YHRgtCw0Lsh",
    "0JfQsNC10LHQsNC7IQ==",
    "0J7RgtGK0LXQsdC40YHRjCE=",
    "0J/RgNC+0LLQsNC70LjQstCw0Lkh",
    "0JjQtNC4INC+0YLRgdGO0LTQsCE=",
    "0KHRg9C60LAh",
    "0KPQsdC70Y7QtNC+0Loh",
    "0JzRg9C00LDQuiE=",
    "0JTQvtC70LHQvtGR0LEh",
    "0JTQtdCx0LjQuyE=",
    "0JjQtNC40L7RgiE=",
    "0JTRg9GA0LDQuiE=",
    "0JrQvtC30ZHQuyE=",
    "0KHQstC40L3RjNGPIQ==",
    "0JPQsNC0IQ==",
    "0KLQstCw0YDRjCE=",
    "0KPRgNC+0LQh",
    "0JzRgNCw0LfRjCE=",
    "0J/QsNC00LvQsCE=",
    "0JPQvdC40LTQsCE=",
    "0KXRg9C50LvQviE=",
    "0J/QuNC00L7RgCE=",
    "0LXQsdCw0YLRjCDRgtC10LHRjw==",
    "VGVzdGEgZGkgY2F6enU=",
    "TWFuZ2hqYSBtZXJkYQ==",
    "U29mZmlhbWkgaW4gY3VsdQ==",
    "RmFjY2lhY2NpYQ==",
    "UHVyY2FjY2l1",
    "VmEgZmFuIGN1bG8=",
    "UG9yY3U=",
    "U3VtZXJl",
    "U3VtZXJvbmU=",
    "Q2FuYWNjaXU=",
    "UGlkb2doanU=",
    "WmVjY2E=",
    "TXVsaXp6w7I=",
    "TXV6emEgc2VjY2E=",
    "VmEgw6AgZmF0dGkgbGVnaGpl",
    "VMO5IGJydXNnaQ==",
    "QmF1bGzDsg==",
    "Q2FnaMOo",
    "RmF2YQ==",
    "UHV0dGFuYQ==",
    "UHV0dGFuYWNjaWE=",
    "QmFzdGFyZHU=",
    "UGluenV0dQ==",
    "Q2FjY2FydQ==",
    "QmFiYm9uZQ==",
]

_EXPECTED_LOADERS_COUNT = 64

_ALL_LOADERS_PRESENT_AND_VALID_JS = """
deck => {
    const els = document.querySelectorAll('.random-loader-element');
    if (els.length !== __EXPECTED_COUNT__) return false;
    for (const el of els) {
        const h1 = el.querySelector('h1');
        if (!h1 || !deck.includes((h1.textContent || '').trim())) return false;
    }
    return true;
}
""".replace("__EXPECTED_COUNT__", str(_EXPECTED_LOADERS_COUNT))


@final
class RandomLoadersPage(PlaywrightTitleMixin, POMBase):
    """Igoristan's random loaders page."""

    def __init__(
        self, *, driver: PlaywrightDriver, url: str = RANDOM_LOADERS_PAGE_URL
    ) -> None:
        """Initialize random loaders POM."""
        self._driver = driver
        self._URL = url

        self._random_loaders_container = (
            '[data-testid="random-loaded-elements-container"]'
        )
        self._back_to_igoristan_link = 'a[href="/igoristan/"]'

    def open(self) -> RandomLoadersPage:
        """Open the page."""
        self._driver.submit(lambda page: page.goto(self._URL))
        return self

    def verify(self, *, timeout: float | None = None) -> RandomLoadersPage:
        """Verify function."""
        try:
            if timeout is None:
                timeout = get_timeout()

            verify_elements_presence(
                driver=self._driver,
                selectors={
                    "Random loaders container": self._random_loaders_container,
                    "Back to Igoristan link": self._back_to_igoristan_link,
                },
                page_title="the Igoristan random loaders page",
                timeout=timeout,
            )

            wait_for_title_contains(self._driver, "Random loaders", timeout)
        except PlaywrightTimeoutError as exc:
            raise PageVerificationError from exc

        return self

    def verify_full_load(self) -> RandomLoadersPage:
        """Verify that all random loaders page is loaded."""
        timeout = 20  # Hard-coded since loaders are slow here.

        self._driver.submit(
            lambda page: page.wait_for_function(
                _ALL_LOADERS_PRESENT_AND_VALID_JS,
                arg=_DECK,
                timeout=timeout * 1000,
            )
        )

        return self

    def click_back_to_igoristan_link(self) -> RandomLoadersPage:
        """Click on the back to Igoristan link."""
        timeout = get_timeout()
        selector = self._back_to_igoristan_link

        def _click(page: Page) -> None:
            page.locator(selector).first.click(timeout=timeout * 1000)

        self._driver.submit(_click)

        wait_for_hidden(self._driver, selector, timeout)

        return self
