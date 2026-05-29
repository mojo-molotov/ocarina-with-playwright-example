"""Igoristan's sacred upload test campaign."""

from typing import TYPE_CHECKING

from lib.ext.ocarina.adapters.playwright.test_campaign import TestCampaign
from tests.suites.sacred_upload.happy_paths import (
    create_igoristan_sacred_upload_happy_paths_test_suite,
)
from tests.suites.sacred_upload.unhappy_paths import (
    create_igoristan_sacred_upload_unhappy_paths_test_suite,
)

if TYPE_CHECKING:
    from ocarina.custom_types.playwright.web_drivers_pool import PlaywrightDriversPool


def create_igoristan_sacred_upload_campaign(
    *, drivers_pool: PlaywrightDriversPool
) -> TestCampaign:
    """Igoristan's sacred upload test campaign."""
    return TestCampaign(
        name="Sacred upload",
        suites=[
            create_igoristan_sacred_upload_happy_paths_test_suite(
                drivers_pool=drivers_pool
            ),
            create_igoristan_sacred_upload_unhappy_paths_test_suite(
                drivers_pool=drivers_pool
            ),
        ],
    )
