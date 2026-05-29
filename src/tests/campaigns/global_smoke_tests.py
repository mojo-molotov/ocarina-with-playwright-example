"""Igoristan's global smoke tests campaign."""

from typing import TYPE_CHECKING

from lib.ext.ocarina.adapters.playwright.test_campaign import TestCampaign
from tests.suites.global_smoke_tests import create_igoristan_global_smoke_tests_suite

if TYPE_CHECKING:
    from ocarina.custom_types.playwright.web_drivers_pool import PlaywrightDriversPool


def create_igoristan_global_smoke_campaign(
    *, drivers_pool: PlaywrightDriversPool
) -> TestCampaign:
    """Igoristan's global smoke tests campaign."""
    return TestCampaign(
        name="Prerequisites",
        suites=[
            create_igoristan_global_smoke_tests_suite(drivers_pool=drivers_pool),
        ],
    )
