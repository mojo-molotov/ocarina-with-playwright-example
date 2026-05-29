"""Igoristan sacred upload form unhappy paths test suite."""

from typing import TYPE_CHECKING

from lib.ext.ocarina.adapters.playwright.test_suite import TestSuite
from tests.scenarios.sacred_upload.upload_files import (
    test_sacred_upload_try_with_too_much_files_after_first_insertion,
    test_sacred_upload_try_with_too_much_files_immediately,
)

if TYPE_CHECKING:
    from ocarina.custom_types.playwright.web_drivers_pool import PlaywrightDriversPool


def create_igoristan_sacred_upload_unhappy_paths_test_suite(
    *,
    drivers_pool: PlaywrightDriversPool,
) -> TestSuite:
    """Create the Igoristan's sacred upload form unhappy paths test suite."""
    return TestSuite(
        name="Upload unhappy paths",
        tests=[
            test_sacred_upload_try_with_too_much_files_immediately,
            test_sacred_upload_try_with_too_much_files_after_first_insertion,
        ],
        drivers_pool=drivers_pool,
    )
