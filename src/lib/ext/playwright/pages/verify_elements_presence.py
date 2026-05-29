"""Utilities to verify elements presence on a page."""

from typing import TYPE_CHECKING

from ocarina.custom_errors.test_framework.pages import PageVerificationError
from ocarina.infra.playwright.driver_healthcheck import playwright_driver_healthcheck
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver
    from playwright.sync_api import Page


def verify_elements_presence(
    *,
    driver: PlaywrightDriver,
    selectors: dict[str, str],
    timeout: float | None,
    page_title: str = "",
) -> None:
    """Check that all given selectors resolve to a visible element on the page.

    ``selectors`` maps a human-readable element name to a Playwright selector
    string (CSS by default; prefix with ``xpath=`` for XPath).
    """
    errors: list[str] = []

    normalized_timeout = timeout if timeout is not None else 10.0
    timeout_ms = int(normalized_timeout * 1000)

    for element_name, selector in selectors.items():
        playwright_driver_healthcheck(driver)

        def _wait(page: Page, selector: str = selector) -> None:
            page.locator(selector).first.wait_for(state="visible", timeout=timeout_ms)

        try:
            driver.submit(_wait)
        except PlaywrightTimeoutError:
            if page_title:
                errors.append(
                    f"{element_name} not found with '{selector}': not on {page_title}."
                )
            else:
                errors.append(f"{element_name} not found with '{selector}'.")

    if errors:
        raise PageVerificationError("\n".join(errors))
