"""DSED -> Matchers."""

from typing import TYPE_CHECKING, final

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver

# The DSED page shows a (slow) loader, then resolves to EITHER the BSOD page or
# the "victory" / IDS-bypassed page. We wait ONCE for it to settle on either
# outcome, then each matcher decides instantly from the settled state. This
# avoids the trap of probing one outcome for the full timeout while the page has
# already settled on the OTHER one (which made a branch pause for the whole
# budget before being confirmed).
#
# ⚠️ We must NOT settle on the document title: while the loader is still showing,
# the title already equals the IDS-bypassed title ("The donkey sausage eater
# detector", from +title.ts). Settling on the title therefore fires DURING the
# loading phase and makes is_ids_bypassed_page() win even for pages that are
# about to become a BSOD — the BSOD branch is never taken, the IDS branch then
# fails to find its elements, retries the whole test 8x and dies. The page's
# content wrapper carries an id of `content-${state}` (content-loading /
# content-error / content-success), which only flips to error/success once the
# outcome is actually decided. That id is the reliable settle + decision signal.
_CONTENT_ERROR = "#content-error"
_CONTENT_SUCCESS = "#content-success"

_SETTLED_JS = f"""
() => !!(
    document.querySelector('{_CONTENT_ERROR}')
    || document.querySelector('{_CONTENT_SUCCESS}')
)
"""


@final
class DSEDPageMatchers:
    """No Sicilian allowed."""

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

    def _is_present(self, selector: str) -> bool:
        # Use a Locator (re-resolved on each use), never a kept ElementHandle:
        # ``.count()`` re-queries the live DOM and returns nothing to hold onto.
        return self._driver.submit(lambda page: page.locator(selector).count() > 0)

    def is_bsod_page(self) -> bool:
        """Quickly verify is BSOD page."""
        timeout = 15  # Hard-coded since loaders are slow here.
        if not self._wait_until_settled(timeout):
            return False
        return self._is_present(_CONTENT_ERROR)

    def is_ids_bypassed_page(self) -> bool:
        """Quickly verify is 'success' page."""
        timeout = 15  # Hard-coded since loaders are slow here.
        if not self._wait_until_settled(timeout):
            return False
        return self._is_present(_CONTENT_SUCCESS)
