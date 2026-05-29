"""Playwright wait helpers mirroring the Selenium expected_conditions we relied on.

Each helper marshals a single ``page.wait_for_function`` (or locator wait) onto the
driver's owner thread via :meth:`PlaywrightDriver.submit`, so it is safe to call
from any worker thread. They raise ``playwright.sync_api.TimeoutError`` on timeout,
which page objects translate into ``PageVerificationError`` exactly like the
Selenium ``TimeoutException`` was translated before.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver
    from playwright.sync_api import Page


def _ms(timeout: float) -> int:
    return int(timeout * 1000)


def wait_for_title_is(driver: PlaywrightDriver, title: str, timeout: float) -> None:
    """Wait until ``document.title`` is exactly ``title``."""
    driver.submit(
        lambda page: page.wait_for_function(
            "expected => document.title === expected",
            arg=title,
            timeout=_ms(timeout),
        )
    )


def wait_for_title_contains(
    driver: PlaywrightDriver, needle: str, timeout: float
) -> None:
    """Wait until ``document.title`` contains ``needle``."""
    driver.submit(
        lambda page: page.wait_for_function(
            "needle => document.title.includes(needle)",
            arg=needle,
            timeout=_ms(timeout),
        )
    )


def wait_for_h1_contains(driver: PlaywrightDriver, needle: str, timeout: float) -> None:
    """Wait until the first ``<h1>`` text content contains ``needle``."""
    driver.submit(
        lambda page: page.wait_for_function(
            """needle => {
                const h1 = document.querySelector('h1');
                return !!h1 && h1.textContent.includes(needle);
            }""",
            arg=needle,
            timeout=_ms(timeout),
        )
    )


def wait_for_h1_contains_ci(
    driver: PlaywrightDriver, needle_lower: str, timeout: float
) -> None:
    """Wait until the first ``<h1>`` text contains ``needle_lower`` (case-insensitive).

    ``needle_lower`` must already be lower-cased by the caller.
    """
    driver.submit(
        lambda page: page.wait_for_function(
            """needle => {
                const h1 = document.querySelector('h1');
                return !!h1 && (h1.textContent || '').toLowerCase().includes(needle);
            }""",
            arg=needle_lower,
            timeout=_ms(timeout),
        )
    )


def wait_for_visible(driver: PlaywrightDriver, selector: str, timeout: float) -> None:
    """Wait until the first element matching ``selector`` is visible."""

    def _wait(page: Page) -> None:
        page.locator(selector).first.wait_for(state="visible", timeout=_ms(timeout))

    driver.submit(_wait)


def wait_for_hidden(driver: PlaywrightDriver, selector: str, timeout: float) -> None:
    """Wait until no element matching ``selector`` is visible (or it is detached)."""

    def _wait(page: Page) -> None:
        page.locator(selector).first.wait_for(state="hidden", timeout=_ms(timeout))

    driver.submit(_wait)
