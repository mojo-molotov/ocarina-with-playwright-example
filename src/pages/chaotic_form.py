"""Igoristan's chaotic form page."""

from contextlib import suppress
from typing import TYPE_CHECKING, final

from ocarina.custom_errors.test_framework.pages import PageVerificationError
from ocarina.dsl.invariants.assertions import is_positive
from ocarina.dsl.invariants.validate import validate
from ocarina.infra.playwright.mixins import PlaywrightTitleMixin
from ocarina.pom.base import POMBase
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from constants.pages.chaotic_form import CHAOTIC_FORM_PAGE_URL
from lib.ext.ocarina.adapters.playwright.cli_getters import get_timeout
from lib.ext.ocarina.adapters.playwright.screenshotter import take_screenshot
from lib.ext.playwright.humanize.proxy import humanized_fill
from lib.ext.playwright.pages.waits import (
    wait_for_h1_contains,
    wait_for_title_contains,
    wait_for_visible,
)

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver
    from ocarina.ports.ilogger import ILogger
    from playwright.sync_api import Page


@final
class ChaoticFormPage(PlaywrightTitleMixin, POMBase):
    """Igoristan's chaotic form page."""

    def __init__(
        self, *, driver: PlaywrightDriver, url: str = CHAOTIC_FORM_PAGE_URL
    ) -> None:
        """Initialize chaotic form POM."""
        self._driver = driver
        self._URL = url

        self._bible_verse_input = "#bible-verse"
        self._corsican_city_input = "#corsican-city"
        self._inspiring_apostle_input = "#inspiring-apostle"
        self._cinto_height_input = "#cinto-height"
        self._personal_revelation_input = "#personal-revelation"
        self._submit_btn = '[data-testid="chaotic-form-submit-btn"]'
        self._success_msg = '[data-testid="success-message"]'

    def open(self) -> ChaoticFormPage:
        """Open the page."""
        self._driver.submit(lambda page: page.goto(self._URL))
        return self

    def verify(self, *, timeout: float | None = None) -> ChaoticFormPage:
        """Verify function."""
        try:
            if timeout is None:
                timeout = get_timeout()

            wait_for_title_contains(self._driver, "Chaotic form", timeout)
            wait_for_h1_contains(self._driver, "Sacred Corsican Registration", timeout)
        except PlaywrightTimeoutError as exc:
            raise PageVerificationError from exc

        return self

    def _select_inspiring_apostle(self, inspiring_apostle_index: int) -> None:
        """Select the apostle option, clamping to the last available option."""
        selector = self._inspiring_apostle_input

        def _select(page: Page) -> None:
            options_count = page.locator(f"{selector} option").count()
            clamped_index = min(inspiring_apostle_index, options_count - 1)
            page.locator(selector).first.select_option(index=clamped_index)

        self._driver.submit(_select)

    def _fill_form_and_send_it(  # noqa: PLR0913
        self,
        *,
        bible_verse: str,
        corsican_city: str,
        inspiring_apostle_index: int,
        cinto_height: float,
        personal_revelation: str,
        skip_final_check: bool = False,
    ) -> ChaoticFormPage:
        """Fill every field and submit the form.

        Args:
            bible_verse:             Text typed into the "Bible Verse" field.
            corsican_city:           Text typed into the "Corsican City" field.
            inspiring_apostle_index: Zero-based index of the option to select in the
                                     "Most Inspiring Apostle" dropdown. If the index
                                     exceeds the number of available options, the last
                                     option is selected instead. Must be >= 0.
            cinto_height:            Numeric value typed into the "Cinto Height" field.
            personal_revelation:     Text typed into the "Personal Revelation" field.
            skip_final_check:        Ignore the success message.

        Returns:
            The ChaoticFormPage instance, allowing method chaining.

        Raises:
            ValueError: If inspiring_apostle_index is negative.

        """
        validate(inspiring_apostle_index, name="inspiring_apostle_index").assert_that(
            is_positive
        ).execute().raise_if_invalid()

        timeout = get_timeout()

        humanized_fill(self._driver, self._bible_verse_input, bible_verse)
        humanized_fill(self._driver, self._corsican_city_input, corsican_city)
        self._select_inspiring_apostle(inspiring_apostle_index)
        humanized_fill(self._driver, self._cinto_height_input, str(cinto_height))
        humanized_fill(
            self._driver, self._personal_revelation_input, personal_revelation
        )

        submit_btn = self._submit_btn
        self._driver.submit(
            lambda page: page.locator(submit_btn).first.click(timeout=timeout * 1000)
        )

        if not skip_final_check:
            wait_for_visible(self._driver, self._success_msg, timeout)

        return self

    def fill_form_and_send_it_with_retries(  # noqa: PLR0913
        self,
        *,
        retries: int,
        logger: ILogger,
        bible_verse: str,
        corsican_city: str,
        inspiring_apostle_index: int,
        cinto_height: float,
        personal_revelation: str,
    ) -> ChaoticFormPage:
        """Fill every field and submit the form (n retries)."""
        validate(retries, name="retries").assert_that(
            is_positive
        ).execute().raise_if_invalid()

        attempts_count = 1
        self._fill_form_and_send_it(
            bible_verse=bible_verse,
            corsican_city=corsican_city,
            inspiring_apostle_index=inspiring_apostle_index,
            cinto_height=cinto_height,
            personal_revelation=personal_revelation,
            skip_final_check=True,
        )
        # Loop-invariant: hoisted out so the retry-click lambda below doesn't
        # close over loop variables (ruff B023).
        click_timeout = 20  # Hard-coded since loaders are slow here.
        submit_btn = self._submit_btn
        while attempts_count <= retries:
            timeout = min(get_timeout(), 5)  # Hard-coded since toast is fast here.
            with suppress(Exception):
                wait_for_visible(self._driver, self._success_msg, timeout)
                break

            current_url = self._driver.submit(lambda page: page.url)
            msg = (
                "Failed to send the form."
                "\n"
                f"Life: {attempts_count}/{retries}"
                "\n"
                f"Current URL: {current_url}"
            )

            logger.warning(msg)
            take_screenshot(driver=self._driver, logger=logger, category="WARNING")
            self._driver.submit(
                lambda page: page.locator(submit_btn).first.click(
                    timeout=click_timeout * 1000
                )
            )
            attempts_count += 1

        s = "s" if attempts_count > 1 else ""
        msg = f"Sent the form. After {attempts_count} attempt{s}."

        logger.info(msg)
        return self
