"""Test that random loaders page can be fully loaded."""

from typing import TYPE_CHECKING

from ocarina.custom_types.scenario import Scenario
from ocarina.dsl.testing.playwright.create_test import create_playwright_test
from ocarina.opinionated.dsl.drive_page import drive_page

from lib.connectors.test_steps.actions.homepage import open_homepage
from lib.connectors.test_steps.actions.homepage import (
    verify_homepage as _verify_homepage,
)
from lib.ext.ocarina.adapters.agnostic.act import act
from lib.ext.ocarina.adapters.playwright.logs import (
    create_just_log_error,
    create_just_log_success,
    create_log_error_with_current_url,
    create_log_success_with_current_url_and_take_screenshot,
)
from pages.homepage import Homepage

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver
    from ocarina.ports.ilogger import ILogger


def _open_homepage(  # noqa: ANN202
    driver: PlaywrightDriver, logger: ILogger
):
    """Open the homepage."""
    on_homepage = Homepage(driver=driver)

    just_log_error = create_just_log_error(logger=logger)
    just_log_success = create_just_log_success(logger=logger)

    return [
        drive_page(
            act(on_homepage, open_homepage)
            .failure(just_log_error("Failed to open the homepage..."))
            .success(just_log_success("Opened the homepage!")),
        ),
    ]


def verify_homepage(driver: PlaywrightDriver, logger: ILogger):
    """Verify the homepage."""
    on_homepage = Homepage(driver=driver)

    log_error_with_current_url = create_log_error_with_current_url(
        logger=logger, driver=driver
    )
    log_success_with_current_url_and_take_screenshot = (
        create_log_success_with_current_url_and_take_screenshot(
            logger=logger, driver=driver
        )
    )

    return [
        drive_page(
            act(on_homepage, _verify_homepage)
            .failure(
                log_error_with_current_url(
                    "Failed to verify the homepage...",
                )
            )
            .success(
                log_success_with_current_url_and_take_screenshot(
                    "Verified the homepage!"
                )
            ),
        ),
    ]


test_homepage = create_playwright_test(
    name="Validate homepage",
    test_scenario=lambda driver, logger: Scenario(
        test_chain=verify_homepage(driver, logger)
    ),
    pre_test_scenarios_fragments=[_open_homepage],
)
