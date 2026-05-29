"""CLI getters, intended to be quickly changed if required."""

from typing import TYPE_CHECKING

from ocarina.opinionated.cli.playwright.cli_store_singleton import (
    PlaywrightCliStoreSingleton,
)

if TYPE_CHECKING:
    from ocarina.custom_types.playwright.supported_browsers import (
        SupportedPlaywrightBrowser,
    )
    from ocarina.opinionated.loggers.custom_types.supported_loggers import (
        SupportedLogger,
    )


def get_timeout() -> int:
    """Get timeout in seconds from CLI."""
    timeout: int = PlaywrightCliStoreSingleton().get("wait_timeout")
    return timeout


def get_logger_mode() -> SupportedLogger:
    """Get logger mode from CLI."""
    logger_mode: SupportedLogger = PlaywrightCliStoreSingleton().get("logger")
    return logger_mode


def get_max_workers() -> int:
    """Get max workers amount from CLI."""
    max_workers: int = PlaywrightCliStoreSingleton().get("workers")
    return max_workers


def get_only() -> list[str]:
    """Get only test ids from CLI."""
    only: list[str] = PlaywrightCliStoreSingleton().get("only")
    return only


def get_exclude() -> list[str]:
    """Get excluded test ids from CLI."""
    exclude: list[str] = PlaywrightCliStoreSingleton().get("exclude")
    return exclude


def get_browser() -> SupportedPlaywrightBrowser:
    """Get browser engine from CLI (chromium/firefox/webkit)."""
    browser: SupportedPlaywrightBrowser = PlaywrightCliStoreSingleton().get("browser")
    return browser


def get_headless() -> bool:
    """Get headless flag from CLI."""
    headless: bool = PlaywrightCliStoreSingleton().get("headless")
    return headless


def get_profile_path() -> str | None:
    """Get browser profile path from CLI (None when --profile-path is omitted)."""
    profile_path: str | None = PlaywrightCliStoreSingleton().get("profile_path")
    return profile_path


def get_video_dir() -> str | None:
    """Get session video directory from CLI (None when --video-dir is omitted)."""
    video_dir: str | None = PlaywrightCliStoreSingleton().get("video_dir")
    return video_dir


def get_trace_dir() -> str | None:
    """Get Playwright trace directory from CLI (None when --trace-dir is omitted)."""
    trace_dir: str | None = PlaywrightCliStoreSingleton().get("trace_dir")
    return trace_dir
