"""Igoristan Corsicamon unhappy paths test suite."""

from typing import TYPE_CHECKING

from lib.ext.ocarina.adapters.playwright.test_suite import TestSuite
from tests.scenarios.corsicamon.add_corsicamon import (
    test_try_to_add_corsicamon_using_already_in_draw_id,
    test_try_to_add_corsicamon_using_invalid_id,
)

if TYPE_CHECKING:
    from ocarina.custom_types.playwright.web_drivers_pool import PlaywrightDriversPool


def create_igoristan_corsicamon_unhappy_paths_test_suite(
    *,
    drivers_pool: PlaywrightDriversPool,
) -> TestSuite:
    """Create the Igoristan's Corsicamon unhappy paths test suite."""
    return TestSuite(
        name="Corsicamon unhappy paths",
        tests=[
            test_try_to_add_corsicamon_using_invalid_id,
            test_try_to_add_corsicamon_using_already_in_draw_id,
        ],
        drivers_pool=drivers_pool,
    )
