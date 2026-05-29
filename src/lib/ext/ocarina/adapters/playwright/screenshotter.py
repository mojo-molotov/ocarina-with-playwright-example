"""Screnshotter functions."""

from typing import TYPE_CHECKING, Literal

from ocarina.infra.playwright.create_screenshotter import (
    create_playwright_screenshotter,
)

if TYPE_CHECKING:
    from ocarina.custom_types.effect import Effect
    from ocarina.infra.playwright.driver import PlaywrightDriver
    from ocarina.ports.ilogger import ILogger

_Category = Literal["SUCCESS", "FAIL", "WARNING"]


def take_screenshot(
    *, driver: PlaywrightDriver, logger: ILogger, category: _Category
) -> None:
    """Take a screenshot (standardized prefixes)."""
    take_screenshot_dispatchers: dict[_Category, Effect] = {
        "FAIL": lambda: create_playwright_screenshotter(driver, logger).take_screenshot(
            prefix="FAIL", shots=3, burst_delay=0.5
        ),
        "SUCCESS": lambda: create_playwright_screenshotter(
            driver, logger
        ).take_screenshot(prefix="SUCCESS"),
        "WARNING": lambda: create_playwright_screenshotter(
            driver, logger
        ).take_screenshot(prefix="WARNING"),
    }

    take_screenshot_dispatchers[category]()
