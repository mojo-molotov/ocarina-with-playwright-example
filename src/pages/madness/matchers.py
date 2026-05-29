"""Madness -> Matchers."""

from typing import TYPE_CHECKING, final

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from lib.ext.ocarina.adapters.playwright.cli_getters import get_timeout

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver

# The madness page resolves (after a render delay) to EITHER a CORS-errors page
# or a "This is Bastia" page. Wait ONCE for it to settle on either outcome, then
# decide instantly — so the non-matching matcher doesn't burn the whole budget
# while the page has already settled on the other state.
_SETTLED_JS = """
() => {
    const h1 = document.querySelector('h1');
    if (!h1) return false;
    const t = (h1.textContent || '').toLowerCase();
    return t.includes('cors errors:') || t.includes('this is bastia');
}
"""

_CORS_H1_NEEDLE = "cors errors:"
_BASTIA_H1_NEEDLE = "this is bastia"


@final
class MadnessPageMatchers:
    """Is madness."""

    def __init__(self, *, driver: PlaywrightDriver) -> None:
        """Initialize helper."""
        self._driver = driver

    def _wait_until_settled(self, timeout: float) -> bool:
        """Wait (up to ``timeout``) for the page to settle on either outcome."""
        try:
            self._driver.submit(
                lambda page: page.wait_for_function(
                    _SETTLED_JS, timeout=int(timeout * 1000)
                )
            )
        except PlaywrightTimeoutError:
            return False
        return True

    def _h1_lower(self) -> str:
        return self._driver.submit(
            lambda page: (page.locator("h1").first.text_content() or "").lower()
        )

    def is_bastia_page(self) -> bool:
        """Quickly verify is bastia page."""
        timeout = min(get_timeout(), 5)
        if not self._wait_until_settled(timeout):
            return False
        return _BASTIA_H1_NEEDLE in self._h1_lower()

    def is_cors_page(self) -> bool:
        """Quickly verify is CORS page."""
        timeout = min(get_timeout(), 5)
        if not self._wait_until_settled(timeout):
            return False
        return _CORS_H1_NEEDLE in self._h1_lower()
