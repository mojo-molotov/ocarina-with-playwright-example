"""Igoristan's dashboard login page."""

import random
import time
from contextlib import suppress
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, final

from ocarina.custom_errors.test_framework.pages import PageVerificationError
from ocarina.dsl.invariants.assertions import (
    is_iso_utc_date_string,
    is_positive,
    is_str,
    is_truthy,
)
from ocarina.dsl.invariants.internals.validation_chain import chain_validations
from ocarina.dsl.invariants.validate import validate
from ocarina.infra.playwright.mixins import PlaywrightTitleMixin
from ocarina.pom.base import POMBase
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from api.retrieve_dashboard_otp_code import retrieve_dashboard_otp_code
from constants.pages.dashboard import DASHBOARD_URL
from constants.sys.redis_keys import OTP_SEND_LOCK_KEY
from lib.custom_errors.transient_error import TransientError
from lib.ext.ocarina.adapters.agnostic.env_getters import create_env_getters
from lib.ext.ocarina.adapters.playwright.cli_getters import get_max_workers, get_timeout
from lib.ext.ocarina.adapters.playwright.screenshotter import take_screenshot
from lib.ext.playwright.pages.verify_elements_presence import verify_elements_presence
from lib.ext.playwright.pages.waits import (
    wait_for_h1_contains,
    wait_for_hidden,
    wait_for_title_contains,
)
from lib.ext.redis.client import get_redis_client

if TYPE_CHECKING:
    from dogpile.cache import CacheRegion
    from ocarina.custom_types.effect import Effect
    from ocarina.infra.playwright.driver import PlaywrightDriver
    from ocarina.opinionated.infra.env import (
        ImmutableCredentials,
    )
    from ocarina.ports.ilogger import ILogger
    from playwright.sync_api import Page
    from redis.lock import Lock as RedisLock

_PAGE_TITLE = "the Igoristan dashboard login page"


def _get_lock() -> RedisLock:
    client = get_redis_client()
    redis_lock: RedisLock = client.lock(OTP_SEND_LOCK_KEY, timeout=60)
    return redis_lock


@final
class DashboardLoginPage(PlaywrightTitleMixin, POMBase):
    """Igoristan's dashboard login page."""

    def __init__(self, *, driver: PlaywrightDriver, url: str = DASHBOARD_URL) -> None:
        """Initialize dashboard login POM."""
        use_otp_checkbox_id = "use-otp"
        self._driver = driver
        self._URL = url
        self._username_input = "#username"
        self._password_input = "#password"  # noqa: S105 — CSS selector, not a secret
        self._igor_api_key_input = "#otp-api-key"
        self._use_otp_checkbox = f"#{use_otp_checkbox_id}"
        self._use_otp_checkbox_label = f"xpath=//label[@for='{use_otp_checkbox_id}']"
        self._login_btn = '[data-testid="login-btn"]'
        self._back_to_igoristan_link = 'a[href="/igoristan/"]'

        self._confirm_otp_btn_on_otp_screen = '[data-testid="otp-btn"]'
        self._otp_field_on_otp_screen = "#otp-code"
        self._invalid_credentials_msg = (
            "xpath=//*[contains(text(), 'Invalid credentials.')]"
        )

        timeout = get_timeout()

        self._login_without_otp_action_dispatchers: dict[str, Effect] = {
            "focus_username_input_then_press_enter": lambda: self._press_enter(
                self._username_input, timeout
            ),
            "focus_password_input_then_press_enter": lambda: self._press_enter(
                self._password_input, timeout
            ),
            "click_login_button": lambda: self._click(self._login_btn, timeout),
            "focus_login_button_then_press_enter": lambda: self._press_enter(
                self._login_btn, timeout
            ),
        }

        self._login_with_otp_action_dispatchers: dict[str, Effect] = {
            **self._login_without_otp_action_dispatchers,
            "focus_api_key_input_then_press_enter": lambda: self._press_enter(
                self._igor_api_key_input, timeout
            ),
        }

        self._confirm_otp_action_dispatchers: dict[str, Effect] = {
            "focus_otp_input_then_press_enter": lambda: self._press_enter(
                self._otp_field_on_otp_screen, timeout
            ),
            "click_otp_button": lambda: self._click(
                self._confirm_otp_btn_on_otp_screen, timeout
            ),
            "focus_otp_button_then_press_enter": lambda: self._press_enter(
                self._confirm_otp_btn_on_otp_screen, timeout
            ),
        }

    # --- low-level marshalled primitives -------------------------------------

    def _press_enter(self, selector: str, timeout: float) -> None:
        self._driver.submit(
            lambda page: page.locator(selector).first.press(
                "Enter", timeout=int(timeout * 1000)
            )
        )

    def _click(self, selector: str, timeout: float) -> None:
        self._driver.submit(
            lambda page: page.locator(selector).first.click(timeout=int(timeout * 1000))
        )

    def _fill(self, selector: str, value: str, timeout: float) -> None:
        self._driver.submit(
            lambda page: page.locator(selector).first.fill(
                value, timeout=int(timeout * 1000)
            )
        )

    def _is_otp_checkbox_checked(self) -> bool:
        selector = self._use_otp_checkbox
        return self._driver.submit(
            lambda page: page.locator(selector).first.is_checked()
        )

    def _login_submit_succeeded(self, timeout: float) -> bool:
        """Race the two post-submit outcomes; return True only on success.

        The dashboard randomly rejects even valid credentials (~10% of the time),
        showing an "Invalid credentials." error while the form stays put. Success
        instead unmounts the password field (we move on to the welcome/OTP
        screen).

        ⚠️ Playwright has no implicit wait, so the previous `wait_for_hidden` on
        the still-present password field blocked for the WHOLE timeout budget on
        every random failure before the loop could retry — that was the drag.
        Here we wait for whichever outcome settles first: the password field
        leaving the DOM/becoming hidden (success) OR the error surfacing
        (failure). On failure we return immediately so the caller retries at
        once. Same spirit as ``_network_error_is_showing`` in corsicamon.
        """
        settled_js = """
        () => {
            const pwd = document.querySelector('#password');
            const visible = pwd
                && (pwd.offsetWidth || pwd.offsetHeight || pwd.getClientRects().length);
            if (!visible) return 'success';
            const failed = Array.from(document.querySelectorAll('div')).some(
                (d) => (d.textContent || '').includes('Invalid credentials.')
            );
            if (failed) return 'failure';
            return false;
        }
        """

        def _wait(page: Page) -> str:
            handle = page.wait_for_function(settled_js, timeout=int(timeout * 1000))
            return str(handle.json_value())

        try:
            return self._driver.submit(_wait) == "success"
        except PlaywrightTimeoutError:
            return False

    # --- dispatchers ----------------------------------------------------------

    def _get_random_login_without_otp_action_key(self) -> str:
        return random.choice(  # noqa: S311
            list(self._login_without_otp_action_dispatchers.keys())
        )

    def _get_random_login_with_otp_action_key(self) -> str:
        return random.choice(  # noqa: S311
            list(self._login_with_otp_action_dispatchers.keys())
        )

    def _get_random_confirm_otp_action_key(self) -> str:
        return random.choice(  # noqa: S311
            list(self._confirm_otp_action_dispatchers.keys())
        )

    # --- public API -----------------------------------------------------------

    def open(self) -> DashboardLoginPage:
        """Open the page."""
        self._driver.submit(lambda page: page.goto(self._URL))
        return self

    def verify(self, *, timeout: float | None = None) -> DashboardLoginPage:
        """Verify function."""
        try:
            if timeout is None:
                timeout = get_timeout()

            verify_elements_presence(
                driver=self._driver,
                selectors={
                    "Username input": self._username_input,
                    "Password input": self._password_input,
                    "OTP checkbox": self._use_otp_checkbox,
                    "Login button": self._login_btn,
                    "Back to Igoristan link": self._back_to_igoristan_link,
                },
                page_title=_PAGE_TITLE,
                timeout=timeout,
            )

            wait_for_title_contains(self._driver, "Dashboard", timeout)
            wait_for_h1_contains(self._driver, "Authentication Required", timeout)
        except PlaywrightTimeoutError as exc:
            raise PageVerificationError from exc

        return self

    def click_back_to_igoristan_link(self) -> DashboardLoginPage:
        """Click on the back to Igoristan link."""
        timeout = get_timeout()
        self._click(self._back_to_igoristan_link, timeout)
        wait_for_hidden(self._driver, self._back_to_igoristan_link, timeout)
        return self

    def login_without_otp(self, creds: ImmutableCredentials) -> DashboardLoginPage:
        """Fill creds and trigger login btn."""
        timeout = get_timeout()

        self._fill(self._username_input, creds["login"], timeout)
        self._fill(self._password_input, creds["password"], timeout)

        self._login_without_otp_action_dispatchers[
            self._get_random_login_without_otp_action_key()
        ]()

        return self

    def login_without_otp_and_with_retries(
        self,
        creds: ImmutableCredentials,
        retries: int,
        *,
        logger: ILogger,
    ) -> DashboardLoginPage:
        """Fill creds and click on the login btn (n retries)."""
        validate(retries, name="retries").assert_that(
            is_positive
        ).execute().raise_if_invalid()

        attempts_count = 1

        while attempts_count <= retries:
            self.login_without_otp(creds)

            timeout = get_timeout()
            if self._login_submit_succeeded(timeout):
                break

            current_url = self._driver.submit(lambda page: page.url)
            msg = (
                "Failed to connect to the dashboard, without OTP."
                "\n"
                f"Life: {attempts_count}/{retries}"
                "\n"
                f"Current URL: {current_url}"
            )

            logger.warning(msg)
            take_screenshot(driver=self._driver, logger=logger, category="WARNING")
            attempts_count += 1

        s = "s" if attempts_count > 1 else ""
        msg = (
            "Connected to the dashboard, without OTP."
            " "
            f"After {attempts_count} attempt{s}."
        )

        logger.info(msg)

        return self

    def start_to_login_with_otp(
        self,
        creds: ImmutableCredentials,
        *,
        username_cache_key: str,
        otp_send_button_click_date_cache_key: str,
        cache: CacheRegion,
    ) -> DashboardLoginPage:
        """Enable OTP, fill fields and confirm to reach the OTP screen."""

        def _send(username: str) -> None:
            cache.set(username_cache_key, username)
            cache.set(
                otp_send_button_click_date_cache_key,
                datetime.now(UTC).isoformat(),
            )

            self._login_with_otp_action_dispatchers[
                self._get_random_login_with_otp_action_key()
            ]()

        username = creds["login"]
        timeout = get_timeout()
        igor_api_key = create_env_getters().get_value("igor_api_key")

        # Enable the OTP checkbox by clicking its label (the input itself is
        # visually hidden). Idempotent: only toggle when not already checked.
        self._driver.submit(
            lambda page: page.locator(self._use_otp_checkbox_label).first.wait_for(
                state="visible", timeout=int(timeout * 1000)
            )
        )

        if not self._is_otp_checkbox_checked():
            self._click(self._use_otp_checkbox_label, timeout)

        validate(
            self._is_otp_checkbox_checked(), name="checkbox_is_selected"
        ).assert_that(
            is_truthy, msg="Couldn't select the OTP checkbox."
        ).execute().raise_if_invalid()

        self._fill(self._username_input, username, timeout)
        self._fill(self._password_input, creds["password"], timeout)
        self._fill(self._igor_api_key_input, igor_api_key, timeout)

        workers = get_max_workers()

        if workers > 1:
            with _get_lock():
                time.sleep(2.5)
                _send(username)
        else:
            _send(username)

        return self

    def start_to_login_with_otp_and_with_retries(  # noqa: PLR0913
        self,
        creds: ImmutableCredentials,
        retries: int,
        *,
        username_cache_key: str,
        otp_send_button_click_date_cache_key: str,
        logger: ILogger,
        cache: CacheRegion,
    ) -> DashboardLoginPage:
        """Enable OTP, fill fields and confirm to reach the OTP screen (n retries)."""
        validate(retries, name="retries").assert_that(
            is_positive
        ).execute().raise_if_invalid()

        attempts_count = 1

        while attempts_count <= retries:
            self.start_to_login_with_otp(
                creds,
                username_cache_key=username_cache_key,
                otp_send_button_click_date_cache_key=otp_send_button_click_date_cache_key,
                cache=cache,
            )

            timeout = get_timeout()

            if self._login_submit_succeeded(timeout):
                break

            current_url = self._driver.submit(lambda page: page.url)
            msg = (
                "Failed to reach the OTP screen."
                "\n"
                f"Life: {attempts_count}/{retries}"
                "\n"
                f"Current URL: {current_url}"
            )

            logger.warning(msg)
            take_screenshot(driver=self._driver, logger=logger, category="WARNING")
            attempts_count += 1

        s = "s" if attempts_count > 1 else ""
        msg = f"Reached the OTP screen.\nAfter {attempts_count} attempt{s}."

        logger.info(msg)

        return self

    def verify_invalid_creds_msg_is_displayed(self) -> DashboardLoginPage:
        """Verify the invalid creds msg is displayed."""
        try:
            timeout = get_timeout()

            verify_elements_presence(
                driver=self._driver,
                selectors={
                    "Invalid credentials msg": self._invalid_credentials_msg,
                },
                timeout=timeout,
            )

        except PlaywrightTimeoutError as exc:
            raise PageVerificationError from exc

        return self

    def verify_otp_screen(self) -> DashboardLoginPage:
        """Verify the OTP screen."""
        try:
            timeout = get_timeout()

            verify_elements_presence(
                driver=self._driver,
                selectors={
                    "OTP field": self._otp_field_on_otp_screen,
                },
                page_title="the Igoristan dashboard login page (OTP screen)",
                timeout=timeout,
            )
        except PlaywrightTimeoutError as exc:
            raise PageVerificationError from exc
        else:
            return self

    def type_otp(
        self,
        *,
        username_cache_key: str,
        otp_send_button_click_date_cache_key: str,
        logger: ILogger,
        cache: CacheRegion,
    ) -> DashboardLoginPage:
        """Type the OTP code and confirm it."""
        unsafe_username: Any = cache.get(username_cache_key)
        unsafe_min_date: Any = cache.get(otp_send_button_click_date_cache_key)

        try:
            chain_validations(
                validate(unsafe_username, name="cached_username").assert_that(is_str),
                validate(unsafe_min_date, name="cached_min_date")
                .assert_that(is_str)
                .assert_that(is_iso_utc_date_string),
            ).execute().raise_if_invalid()
        except Exception as exc:
            raise TransientError from exc

        username: str = unsafe_username
        min_utc_date = datetime.fromisoformat(unsafe_min_date)

        msg = f"min_utc_date: {min_utc_date}"
        logger.info(msg)

        timeout = get_timeout()

        otp_code = retrieve_dashboard_otp_code(
            min_utc_date=min_utc_date, timeout=timeout
        )

        if otp_code is None:
            msg = "No matching OTP found."
            raise TransientError(msg)

        msg = f"Found OTP: {otp_code}"
        logger.info(msg)

        msg = f"Username: {username}"
        logger.info(msg)

        self._fill(self._otp_field_on_otp_screen, otp_code, timeout)

        self._confirm_otp_action_dispatchers[
            self._get_random_confirm_otp_action_key()
        ]()

        return self

    def type_otp_with_retries(
        self,
        retries: int,
        *,
        username_cache_key: str,
        otp_send_button_click_date_cache_key: str,
        logger: ILogger,
        cache: CacheRegion,
    ) -> DashboardLoginPage:
        """Enable OTP, fill fields and confirm to reach the OTP screen (n retries)."""
        validate(retries, name="retries").assert_that(
            is_positive
        ).execute().raise_if_invalid()

        attempts_count = 1

        while attempts_count <= retries:
            self.type_otp(
                logger=logger,
                username_cache_key=username_cache_key,
                otp_send_button_click_date_cache_key=otp_send_button_click_date_cache_key,
                cache=cache,
            )

            timeout = get_timeout()

            with suppress(Exception):
                wait_for_hidden(self._driver, self._otp_field_on_otp_screen, timeout)
                break

            current_url = self._driver.submit(lambda page: page.url)
            msg = (
                "Failed to escape the OTP screen."
                "\n"
                f"Life: {attempts_count}/{retries}"
                "\n"
                f"Current URL: {current_url}"
            )

            logger.warning(msg)
            take_screenshot(driver=self._driver, logger=logger, category="WARNING")
            attempts_count += 1

        s = "s" if attempts_count > 1 else ""
        msg = f"Escaped the OTP screen.\nAfter {attempts_count} attempt{s}."

        logger.info(msg)

        return self
