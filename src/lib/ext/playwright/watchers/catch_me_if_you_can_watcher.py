"""Catch me if you can watcher. Used to snap popping at any time elements."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ocarina.dsl.testing.playwright.create_watcher import PlaywrightWatcher

# Collect every ``.catch-me-if-you-can`` node in the browser and return FLAT,
# JSON-serializable data only (never live handles) — required because the result
# crosses back from the driver's owner thread to the watcher's polling thread.
_COLLECT_JS = """
els => els.map(el => ({
    tag:    el.tagName.toLowerCase(),
    text:   (el.innerText || '').trim(),
    id:     el.id,
    cls:    el.className,
    name:   el.getAttribute('name') || '',
    testid: el.getAttribute('data-testid') || '',
}))
"""


def catch_me_if_you_can_cb(watcher: PlaywrightWatcher) -> None:
    """Detect any element with CSS class 'catch-me-if-you-can' on the current page."""
    # Observe-only: a single marshalled read, returning flat data. See
    # ocarina.dsl.testing.playwright.create_watcher for the watcher convention.
    raw = watcher.driver.submit(
        lambda page: page.eval_on_selector_all(".catch-me-if-you-can", _COLLECT_JS)
    )

    if not raw:
        return

    # Batch per poll: a single poll can match several simultaneously-present
    # ``.catch-me-if-you-can`` nodes. Emitting one report() (= log + screenshot)
    # per node bursts the proofs — and on Playwright each screenshot is
    # marshalled onto the driver's owner thread, so the burst lands as several
    # near-identical captures glued together in the DOCX. Instead, collect every
    # NEW element seen this cycle and emit a single report() summarising them all
    # (one screenshot), without losing any detection (each text is listed).
    fresh: list[dict[str, str]] = []
    for attrs in raw:
        fingerprint = ":".join(
            filter(
                None,
                [
                    attrs["tag"],
                    attrs["text"],
                    attrs["id"],
                    attrs["cls"],
                    attrs["name"],
                    attrs["testid"],
                ],
            )
        )

        if fingerprint in watcher.cache:
            continue

        watcher.cache.add(fingerprint)
        fresh.append(attrs)

    if not fresh:
        return

    detected = "; ".join(f"<{a['tag']}> {a['text']!r}" for a in fresh)
    watcher.report(
        f"catch-me-if-you-can element(s) detected: {detected}",
        label="CATCH_ME_IF_YOU_CAN",
    )
