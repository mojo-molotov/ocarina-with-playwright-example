# CLAUDE.md — ocarina-with-playwright

Context for resuming the project with Claude Code from this folder.

## What it is

Fork of [`ocarina-example`](https://github.com/mojo-molotov/ocarina-example) where the
**Selenium** adapter has been swapped for the **Playwright** adapter of
[Ocarina](https://github.com/mojo-molotov). Goal: prove that swapping Ocarina's adapter is a
**single-layer** change — the test logic (page objects, steps, scenarios, suites, campaigns,
`e2e` cycle) stays identical.
## Current state

✅ Full port complete and **validated live** against the Igoristan site
(`https://mojo-molotov.github.io/igoristan`): **full suite 47/47 PASSED** via
`python src/main.py --browser chromium --workers 3` (dashboard OTP/no-OTP, corsicamon,
sacred upload, randomness, smoke). DOCX/JSON reports + screenshots generated.

## The porting model (understand this before touching the pages)

Playwright's **sync** API binds its objects to a single thread. Ocarina's `PlaywrightDriver`
therefore confines every Playwright call to an owner thread: page objects **never touch `page`
directly**, they marshal the work through `self._driver.submit(lambda page: ...)`.

| | Selenium (origin) | Playwright (here) |
|---|---|---|
| Pool / CLI / factories | `ocarina.infra.selenium`, `...cli.selenium`, `create_selenium_test/watcher` | `...playwright`, `create_playwright_test/watcher` |
| POM driving | `driver.find_element(...).click()` | `driver.submit(lambda p: p.locator(...).click())` |
| Title mixin | `SeleniumTitleMixin` | `PlaywrightTitleMixin` |
| Selectors | `(By.X, "v")` tuples | Playwright strings (`"#id"`, `"[data-testid=...]"`, `"xpath=..."`) |
| Local adapters | `src/lib/ext/.../selenium/*` | `src/lib/ext/.../playwright/*` |
| Transient errors | `selenium.common.WebDriverException` | `playwright.sync_api.Error` |

In-house wait helpers: [src/lib/ext/playwright/pages/waits.py](src/lib/ext/playwright/pages/waits.py)
and [verify_elements_presence.py](src/lib/ext/playwright/pages/verify_elements_presence.py).
Humanized typing: transparent `HumanizedPlaywrightDriver` wrapper
([src/lib/ext/playwright/humanize/proxy.py](src/lib/ext/playwright/humanize/proxy.py)).

## ⚠️ Pitfall #1: no implicit wait in Playwright

Ocarina's Selenium driver runs with `driver.implicitly_wait(wait_timeout)`. Playwright has **no**
global equivalent. Consequence: a `locator.wait_for(state="hidden")` resolves **instantly** when
the element is not (yet) in the DOM. This breaks any retry logic that detects success via "the
error went away": instead **wait for the error to appear** (otherwise = success). See
`_network_error_is_showing` in
[src/pages/corsicamon/enter_api_key.py](src/pages/corsicamon/enter_api_key.py), and
`_login_submit_succeeded` in [src/pages/dashboard/login.py](src/pages/dashboard/login.py)
(login randomly rejects valid creds ~10% of the time; the old `wait_for_hidden(password)` burned
the whole timeout before each retry — now it races success-vs-error and retries instantly).

## ⚠️ Pitfall #2: `match_page` matchers that probe one signal for the whole budget

`match_page` evaluates the `when()` branches in order. If a matcher waits for ITS title for
15-30 s while the page has already settled on the other outcome, you eat a long pause. Applied
solution: **wait once for the page to settle on one OR the other**, then decide instantly. See
[src/pages/donkey_sausage_detector/matchers.py](src/pages/donkey_sausage_detector/matchers.py)
and [src/pages/madness/matchers.py](src/pages/madness/matchers.py).

⚠️ **Sub-pitfall: the settle signal must not be pollutable during loading.**
On DSED, the title ALREADY equals `The donkey sausage eater detector` (= the IDS-bypassed title,
set by `+title.ts`) **while the loader is still spinning**. Settling on the title therefore
fired during the loading phase and made `is_ids_bypassed_page()` win even for pages about to
become a BSOD → the IDS branch then failed to find its elements, retried the whole test 8×
(`max_retries_per_test`) and killed it. Note `match_page` re-raises the `transient_errors` raised
while evaluating conditions. The reliable signal is the content wrapper's `id`
(`#content-loading` → `#content-error` / `#content-success`), which only flips once the outcome
is actually decided. Madness doesn't have this pitfall: its `h1` (`CORS Errors:` / `This is
bastia`) doesn't exist during loading, so settling on it is correct.

## ⚠️ Pitfall #3: prefer Locators, never keep an ElementHandle

Playwright has two notions: `ElementHandle` (a live reference to a DOM element) and `Locator` (a
lazy description, re-resolved on each use). Playwright's own docs explicitly tell you to **prefer
Locators and avoid holding `ElementHandle`s** — precisely because a kept handle goes stale,
breaks on re-render, etc. A Locator is meant to be recreated every time (`page.locator(sel)`):
it's free and it's the idiom. Concretely: don't reach for `page.query_selector(...)` /
`element_handle()` to test presence — use a re-resolved Locator, e.g.
`page.locator(sel).count() > 0`. See `_is_present` in
[src/pages/donkey_sausage_detector/matchers.py](src/pages/donkey_sausage_detector/matchers.py).
This isn't just a style nudge: the rule forbids exactly what Playwright itself warns against.

## Running the project

Prerequisites: Python 3.14, Redis on `localhost:6379`, Playwright browsers installed (already
present under `~/Library/Caches/ms-playwright`), `.env` filled.

```bash
# ⚠️ bare `make` is a broken zsh stub on this machine → use /usr/bin/make
/usr/bin/make install            # creates .venv + deps + pre-commit
/usr/bin/make playwright-install # if the browsers are missing

# Redis (local CLI, not docker)
redis-server --daemonize yes --port 6379

# Full suite
./.venv/bin/python -u ./src/main.py --browser chromium --workers 3
# To watch with your eyes: --workers 1 --not-headless
# To run a single test: --only "Connect to the dashboard, without OTP" (matches test_id = name)
# Engines: chromium | firefox | webkit
```

Style: `/usr/bin/make check-coding-style` (mypy + ruff). `mypy src/` only covers `src/`.

## Secrets / env (`.env`, gitignored)

`DASH_USERNAME` / `DASH_PASSWORD` (example: `SacredFigatellu` / `figatellu`),
`IGOR_API_KEY` (Vercel OTP worker key — required for dashboard-OTP and corsicamon),
`REDIS_URL=redis://localhost:6379`.

## Environment specifics

- bare `make` = broken zsh stub → always `/usr/bin/make` (or `command make`).
- The `.venv` is **not** relocatable: recreate it after moving the folder.

## Run artifacts (gitignored)

`.reports/tests_docx_output/`, `.reports/tests_json_output/`, `.ocarina_logs/`, `.screenshots/`.

## Reference

See [README.md](README.md) for the full Selenium↔Playwright correspondence table and the CLI
flag details (`--video-dir`, `--trace-dir` replace `--driver-path`).
