"""Igoristan's randomness test campaign."""

from typing import TYPE_CHECKING

from lib.ext.ocarina.adapters.playwright.test_campaign import TestCampaign
from tests.suites.randomness import (
    create_igoristan_randomness_level_1_test_suite,
    create_igoristan_randomness_level_2_test_suite,
    create_igoristan_randomness_level_3_test_suite,
    create_igoristan_randomness_level_4_test_suite,
)

if TYPE_CHECKING:
    from ocarina.custom_types.playwright.web_drivers_pool import PlaywrightDriversPool


def create_igoristan_randomness_campaign(
    *, drivers_pool: PlaywrightDriversPool
) -> TestCampaign:
    """Igoristan's randomness test campaign."""
    return TestCampaign(
        name="Random pages",
        suites=[
            create_igoristan_randomness_level_1_test_suite(drivers_pool=drivers_pool),
            create_igoristan_randomness_level_2_test_suite(drivers_pool=drivers_pool),
            create_igoristan_randomness_level_3_test_suite(drivers_pool=drivers_pool),
            create_igoristan_randomness_level_4_test_suite(drivers_pool=drivers_pool),
        ],
    )
