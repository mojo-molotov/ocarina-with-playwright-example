"""Igoristan's sacred upload page."""

import random
from pathlib import Path
from typing import TYPE_CHECKING, final

from ocarina.custom_errors.test_framework.pages import PageVerificationError
from ocarina.dsl.invariants.assertions import is_not_zero, is_positive
from ocarina.dsl.invariants.validate import validate
from ocarina.infra.playwright.mixins import PlaywrightTitleMixin
from ocarina.pom.base import POMBase
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from constants.pages.sacred_upload import SACRED_UPLOAD_PAGE_URL
from lib.ext.ocarina.adapters.playwright.cli_getters import get_timeout
from lib.ext.playwright.pages.waits import wait_for_hidden, wait_for_title_contains

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver


# Wait until exactly ``expected`` preview images are present in the container.
_PREVIEWS_COUNT_JS = """
args => {
    const [selector, expected] = args;
    return document.querySelectorAll(selector).length === expected;
}
"""

# Wait until the dropzone error message contains ``needle``.
_DROPZONE_ERROR_JS = """
args => {
    const [selector, needle] = args;
    const el = document.querySelector(selector);
    return !!el && (el.textContent || '').includes(needle);
}
"""


@final
class SacredUploadPage(PlaywrightTitleMixin, POMBase):
    """Igoristan's sacred upload page."""

    def __init__(
        self, *, driver: PlaywrightDriver, url: str = SACRED_UPLOAD_PAGE_URL
    ) -> None:
        """Initialize sacred upload POM."""
        self._driver = driver
        self._URL = url

        self._images_input = "#images"

        self._previews_container_selector = (
            '[data-testid="upload-form-previews-container"]'
        )
        self._upload_btn = '[data-testid="upload-btn"]'
        self._amen_btn = '[data-testid="amen-btn"]'
        self._sin_btn = '[data-testid="forgive-me-btn"]'

        self._images_dropzone_error_message = (
            '[data-testid="images-dropzone-error-msg"]'
        )
        self._back_to_igoristan_link = 'a[href="/igoristan/"]'

    @staticmethod
    def _delete_img_btn(idx: int) -> str:
        """Delete image btn selector."""
        return f'[data-testid="delete-image-{idx}-btn"]'

    def _click(self, selector: str, timeout: float) -> None:
        self._driver.submit(
            lambda page: page.locator(selector).first.click(timeout=int(timeout * 1000))
        )

    def _wait_previews_count(self, expected: int, timeout: float) -> None:
        selector = f"{self._previews_container_selector} img"
        self._driver.submit(
            lambda page: page.wait_for_function(
                _PREVIEWS_COUNT_JS,
                arg=[selector, expected],
                timeout=int(timeout * 1000),
            )
        )

    def _verify_images_dropzone_error_message(
        self, error_message_needle: str
    ) -> SacredUploadPage:
        """Verify dropzone error message contains the needle."""
        timeout = get_timeout()
        selector = self._images_dropzone_error_message
        self._driver.submit(
            lambda page: page.wait_for_function(
                _DROPZONE_ERROR_JS,
                arg=[selector, error_message_needle],
                timeout=int(timeout * 1000),
            )
        )
        return self

    def open(self) -> SacredUploadPage:
        """Open the page."""
        self._driver.submit(lambda page: page.goto(self._URL))
        return self

    def verify(self, *, timeout: float | None = None) -> SacredUploadPage:
        """Verify function."""
        try:
            if timeout is None:
                timeout = get_timeout()

            wait_for_title_contains(
                self._driver, "Blessed file upload simulator", timeout
            )
        except PlaywrightTimeoutError as exc:
            raise PageVerificationError from exc

        return self

    def add_images(
        self,
        *,
        images_amount: int,
        failing: bool = False,
        forced_expected_img_amount: int = -1,
    ) -> SacredUploadPage:
        """Add images to the sacred upload form."""
        validate(images_amount, name="images_amount").assert_that(
            is_positive
        ).assert_that(is_not_zero).execute().raise_if_invalid()

        timeout = get_timeout()

        root = Path(__file__).parent / "fixtures"
        img_paths = [
            root / "bayu_bayushki_bayu.jpg",
            root / "cozy_bear.jpg",
            root / "napoleon.jpg",
        ]

        selected = [
            str(random.choice(img_paths))  # noqa: S311
            for _ in range(images_amount)
        ]

        images_input = self._images_input
        # Mirror ocarina-example's `arguments[0].value = ''` workaround: when the
        # same file is re-selected (random.choice can repeat the previous pick),
        # the input's value is unchanged, so the browser fires NO `change` event
        # and react-dropzone's onDrop never runs — no new preview appears and the
        # preview-count wait times out (~1/3 of the time on the cancel/delete
        # scenarios where a second add follows). Clearing the value first
        # guarantees a value change, hence a `change` event, on every add.
        self._driver.submit(
            lambda page: page.locator(images_input).first.evaluate(
                "el => { el.value = ''; }"
            )
        )
        self._driver.submit(
            lambda page: page.locator(images_input).first.set_input_files(
                selected, timeout=int(timeout * 1000)
            )
        )

        if failing:
            self._verify_images_dropzone_error_message(error_message_needle="Maximum")
        else:
            expected_len = (
                forced_expected_img_amount
                if forced_expected_img_amount >= 0
                else images_amount
            )
            self._wait_previews_count(expected_len, timeout)

        return self

    def click_on_upload_btn(self) -> SacredUploadPage:
        """Click on upload button."""
        self._click(self._upload_btn, get_timeout())
        return self

    def click_on_delete_img_btn(self, idx: int) -> SacredUploadPage:
        """Click on upload button."""
        self._click(self._delete_img_btn(idx), get_timeout())
        return self

    def click_on_amen_btn(self) -> SacredUploadPage:
        """Click on amen button."""
        self._click(self._amen_btn, get_timeout())
        return self

    def click_on_sin_btn(self) -> SacredUploadPage:
        """Click on sin button."""
        self._click(self._sin_btn, get_timeout())
        return self

    def verify_dropzone_is_empty(self) -> SacredUploadPage:
        """Verify dropzone is empty."""
        timeout = 20  # Hard-coded since loaders are slow here.
        self._wait_previews_count(0, timeout)
        return self

    def click_back_to_igoristan_link(self) -> SacredUploadPage:
        """Click on the back to Igoristan link."""
        timeout = get_timeout()
        self._click(self._back_to_igoristan_link, timeout)
        wait_for_hidden(self._driver, self._back_to_igoristan_link, timeout)
        return self
