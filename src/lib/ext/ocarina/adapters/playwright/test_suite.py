"""Test suite adapter."""

from typing import TYPE_CHECKING, final

from ocarina.dsl.testing.oc_test_suite import TestSuite as OriginalTestSuite
from ocarina.infra.playwright.create_screenshotter import (
    create_playwright_screenshotter,
)
from ocarina.infra.playwright.driver import PlaywrightDriver
from ocarina.opinionated.loggers.create_matching_logger import create_matching_logger

from constants.sys.transient_errors import transient_errors
from lib.ext.ocarina.adapters.playwright.cli_getters import (
    get_exclude,
    get_logger_mode,
    get_only,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ocarina.custom_types.playwright.web_drivers_pool import PlaywrightDriversPool
    from ocarina.custom_types.thunk import Thunk
    from ocarina.dsl.testing.oc_test import Test
    from ocarina.ports.ilogger import ILogger


def _take_screenshot(driver: PlaywrightDriver, logger: ILogger, prefix: str) -> None:
    # This single callback is shared by two callers (see ITakeScreenshot):
    #   - the test executor on failure, with prefix "FAIL";
    #   - every watcher.report(), with prefix == the watcher's own label.
    # The 4-shot burst is deliberate ONLY for failures: it captures transient
    # on-fail state across ~1s. A watcher detection is a single, already-decided
    # observation — bursting it just machine-guns near-identical frames into the
    # DOCX proofs (one report() -> 4 screenshots), so it gets a single shot.
    shots = 4 if prefix == "FAIL" else 1
    create_playwright_screenshotter(driver, logger).take_screenshot(
        prefix=prefix, burst_delay=0.350, shots=shots
    )


@final
class TestSuite(OriginalTestSuite[PlaywrightDriver]):
    """TestSuite adapter."""

    def __init__(  # noqa: PLR0913
        self,
        *,
        name: str,
        tests: Sequence[Test[PlaywrightDriver]],
        drivers_pool: PlaywrightDriversPool,
        create_logger: Thunk[ILogger] | None = None,
        copy_indicator: str = "+",
        put_space_after_copy_indicator: bool = False,
        autoscreen_on_fail: bool = True,
        saturate_workers: bool | None = None,
    ) -> None:
        """Initialize the TestSuite."""
        if create_logger is None:

            def _create_logger():  # noqa: ANN202
                return create_matching_logger(get_logger_mode())

            create_logger = _create_logger

        super().__init__(
            name=name,
            tests=tests,
            only_ids=get_only(),
            exclude_ids=get_exclude(),
            max_retries_per_test=8,
            create_logger=create_logger,
            drivers_pool=drivers_pool,
            copy_indicator=copy_indicator,
            put_space_after_copy_indicator=put_space_after_copy_indicator,
            autoscreen_on_fail=autoscreen_on_fail,
            take_screenshot=_take_screenshot,
            transient_errors=transient_errors,
            saturate_workers=saturate_workers,
        )
