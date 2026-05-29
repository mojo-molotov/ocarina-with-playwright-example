# Ocarina with Playwright

A fork of [`ocarina-example`](https://github.com/mojo-molotov/ocarina-example) that
swaps the **Selenium** backend for the **Playwright** one, to prove that
[Ocarina](https://github.com/mojo-molotov)'s Playwright adapter is a drop-in
replacement for its Selenium adapter.

The test logic is **unchanged**: the same page objects, test steps, scenarios,
suites, campaigns and the same `e2e` cycle run against the same live site. Only
the framework-coupling layer was rewritten:

| Concern | `ocarina-example` (Selenium) | this project (Playwright) |
| --- | --- | --- |
| Driver pool | `ocarina.infra.selenium.create_drivers_pool` | `ocarina.infra.playwright.create_drivers_pool` |
| CLI store | `ocarina.opinionated.cli.selenium` | `ocarina.opinionated.cli.playwright` |
| Test/watcher factories | `create_selenium_test` / `create_selenium_watcher` | `create_playwright_test` / `create_playwright_watcher` |
| Title mixin | `SeleniumTitleMixin` | `PlaywrightTitleMixin` |
| Page Object driving | `driver.find_element(...).click()` | `driver.submit(lambda page: page.locator(...).click())` |
| Local extras | `src/lib/ext/selenium/*` | `src/lib/ext/playwright/*` |
| Local Ocarina adapters | `src/lib/ext/ocarina/adapters/selenium/*` | `src/lib/ext/ocarina/adapters/playwright/*` |

The key difference is the driving model. Playwright's *sync* API binds its objects
to one thread, so Ocarina's `PlaywrightDriver` confines every Playwright call to a
private owner thread; page objects never touch `page` directly, they marshal work
onto it with `driver.submit(lambda page: ...)`. Everything else — Railway Oriented
Programming chains, `match_page` retries, watchers, parallel workers, DOCX/JSON
reports, screenshots — is identical to the Selenium version.

## What this runs against

The suite targets **Igoristan**, a public demo application hosted on GitHub Pages at
<https://mojo-molotov.github.io/igoristan>. No local server is required.

## Prerequisites

- Python **3.14+**.
- **Playwright** browser binaries (installed with `playwright install`). Unlike
  Selenium there is **no WebDriver binary** to download and **no `--driver-path`** —
  Playwright ships its own Chromium/Firefox/WebKit engines.
- A running **Redis 6+** instance, used to coordinate OTP fetches across parallel
  workers. `docker run -p 6379:6379 redis:8` is enough locally.
- An `IGOR_API_KEY` value, required by tests that retrieve one-time passwords from
  the Igoristan OTP API. Host your own
  [tests workers](https://github.com/mojo-molotov/tests-workers) on Vercel.

## Setup

```bash
git clone <this-repo>
cd ocarina-with-playwright

make create-venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
make install                         # installs deps + the chosen Playwright browser

cp .env.example .env
# then edit .env with your values
```

> To install a single engine instead of all three, set `PLAYWRIGHT_BROWSER`
> (default: `chromium`), e.g. `make playwright-install PLAYWRIGHT_BROWSER=firefox`.

## Environment variables

Read from `.env` via `python-dotenv`. Values below come from [`.env.example`](.env.example).

| Variable | Purpose |
| --- | --- |
| `DASH_USERNAME` | Dashboard username (sample value: `SacredFigatellu`). |
| `DASH_PASSWORD` | Dashboard password (sample value: `figatellu`). |
| `IGOR_API_KEY` | Secret key used to retrieve OTP codes from the Igoristan API. |
| `REDIS_URL` | Redis connection string, e.g. `redis://localhost:6379`. |

## Running the suite

1. Start Redis.
2. Make sure the Playwright browser is installed (`make playwright-install`).
3. Run the entry point:

```bash
python -u ./src/main.py \
  --browser chromium \
  --workers 3
```

`--browser` accepts `chromium`, `firefox` or `webkit`. Headless mode is the default;
pass `--not-headless` to see the browsers. The Playwright CLI replaces Selenium's
`--driver-path` with two optional artifact flags — `--video-dir` (record a session
video per driver) and `--trace-dir` (write a `trace_<id>.zip` per driver, open with
`playwright show-trace`). All other flags (`--wait-timeout`, `--profile-path`,
`--logger`, `--only`, `--exclude`, …) come straight from Ocarina's opinionated
Playwright CLI.

The exit code is `0` on success and `1` if any test fails, so the command is
CI-friendly as-is.

## Artifacts

A run writes all the following under the repo root:

- `.reports/tests_docx_output/` — DOCX proof documents.
- `.reports/tests_json_output/` — JSON results.
- `.ocarina_logs/` — structured log files.
- `.screenshots/` — screenshots captured on failure and at explicit checkpoints.

## Project layout

```
src/
├── main.py                         # entry point: CLI → Playwright driver pool → bootstrap(cycle)
├── pages/                          # Page Object Models (POMBase subclasses, Playwright-driven)
├── api/                            # API clients (e.g. OTP retrieval)
├── caches/                         # L1 in-memory cache + cache-key reservation
├── constants/                      # URLs, Redis keys, transient error sets
├── lib/
│   ├── connectors/test_steps/      # pure action functions operating on POMs (unchanged)
│   ├── custom_errors/              # HttpErrorPageReachedError, TransientError, …
│   └── ext/                        # adapters for Ocarina (Playwright), Redis, Playwright extras
└── tests/
    ├── cycles/                     # TestCycle definitions (e2e)
    ├── campaigns/                  # TestCampaign definitions
    ├── suites/                     # TestSuite definitions
    └── scenarios/                  # Scenario factories and test datasets
```

## Continuous integration

Two GitHub Actions workflows live in [`.github/workflows/`](.github/workflows):

- [`main_ci.yml`](.github/workflows/main_ci.yml) — runs on every push and PR to `main`,
  across Ubuntu and Windows with Python 3.14. Executes `make check-coding-style`
  (mypy + ruff) only; no browser tests.
- [`e2e.yml`](.github/workflows/e2e.yml) — manual-dispatch workflow that spins up a
  Redis service, installs the Playwright Chromium engine
  (`playwright install --with-deps chromium`), runs the full suite, and uploads
  `.screenshots/`, `.ocarina_logs/`, and `.reports/`. `IGOR_API_KEY` is read from the
  `OC` GitHub environment.

## Development

```bash
make check-coding-style   # mypy + ruff
make ruff-check           # lint only
make ruff-format          # apply formatting
make clean                # remove .venv, caches, egg-info
```

## License

MIT — Igor Casanova.

---

Built by [@mojo-molotov](https://github.com/mojo-molotov)  
Ported to Playwright as a proof that Ocarina's adapter swap is a one-layer change.  
Fueled by figatellu and Квас.
