# Crawler

Browser-based crawl engine for Shared Namespace Attacks (SNA) and Isolated Namespace Attacks (INA). Each crawler worker launches a headless Chromium instance via Playwright, loads a single extension, visits a set of test-server URLs, and stores coverage, hook, proxy, and mutation logs in PostgreSQL.

## Prerequisites

### System dependencies

- Linux (tested on Ubuntu 22.04+)
- Python ≥ 3.12
- Node.js + npm (for Playwright runner)
- Docker + docker-compose (for the test server)
- Xvfb (`xvfb-run` must be on `$PATH`)
- `mount`/`umount` with permission to mount tmpfs
- PostgreSQL accessible from the crawl host

### Python dependencies

Install all Python dependencies from the repository root using `uv`:

```bash
uv sync
```

### Node dependencies

From the repository root:

```bash
npm install
```

This installs Playwright, dotenv, xmlhttprequest, acorn-loose, and all other packages listed in the root `package.json`.

### Test server

The crawler posts data to `http://testserver.com:9000/` and `https://testserver.com:9010/`. The server must be reachable at that hostname. `crawler.py` brings it up via:

```
docker-compose --env-file ~/chaos/.env up --build -d
```

Add `testserver.com` to `/etc/hosts` if needed.

---

## Configuration

### Environment file

The crawler reads `~/chaos/.env` at startup (both Python and Node sides). Create it with at minimum:

```
DB_HOST=localhost
DB_NAME=chaos
DB_USER=your_user
DB_PASS=your_password
CHAT_ID=dummy_chat_id
BOT_KEY=dummy_bot_key
DEBUG=false
ADVANCED_TEST=false
```

`CHAT_ID` / `BOT_KEY` are for Telegram notifications. Set `CHAT_ID=dummy_chat_id` to disable them.

### Shell environment variables

Set these before running the crawler. All are required; none have safe defaults.

| Variable | Description |
|---|---|
| `DATASET` | Dataset identifier matching the extension directory name (e.g. `crx_2026-04-14`). Written to the `dataset` column of every DB row. |
| `TEST_TYPE` | `shared` (SNA) or `isolated` (INA). Selects the DB table prefix and the URL set namespace. |
| `META_TEST_TYPE` | `basic` or `advanced`. Controls log directory naming and whether HTML snapshots are saved. |
| `TABLE_SUFFIX` | Date-stamped identifier appended to all DB table names (e.g. `2026_04_24`). Determines which tables the analyzer reads. |
| `CRAWL_URL_TYPE` | URL set key from `crawl_urls.json`. See the table below for all valid values. |
| `DIR_EXTENSION` | Subdirectory under `/mnt/extensions/` where unpacked extensions live (e.g. `basic`). |
| `USER_DATA_DIR` | *(optional)* Chromium user data directory. Default: `/tmp/chaos/chromiumDataDir/`. Must be on a fast disk; the crawler mounts tmpfs there. |

### CRAWL_URL_TYPE values

| `TEST_TYPE` | `CRAWL_URL_TYPE` | URLs visited | Used for |
|---|---|---|---|
| `shared` | `simple` | 15 URLs (all 5 SNA attack + break pairs + extras) | SNA main crawl |
| `shared` | `proto` | 2 URLs (proto_poison pair only) | Proto-poison standalone run |
| `shared` | `honey` | 10 honey-body URLs (HTTP + HTTPS, no break scripts) | SNA baseline / honey |
| `isolated` | `clobber` | 4 URLs (raider, mutation, proxy, targeted clobber payload) | INA main crawl |
| `isolated` | `clobber_targeted` | 1 URL (targeted clobber payload only) | INA targeted-only re-run |
| `isolated` | `clobber_taint` | 2 URLs (baseline + targeted) | INA taint crawl |
| `isolated` | `clobber_trigger` | 2 URLs (trigger + targeted) | INA trigger crawl |
| `isolated` | `clobber_gbs_trace` | 1 URL (type=baseline, honey body) | GBS pre-crawl: collect CS traces |
| `isolated` | `clobber_gbs_attack` | 1 URL (clobber_gbs_payload) | GBS attack crawl |
| `isolated` | `simple` | 4 URLs (raider + mutation, HTTP + HTTPS) | INA baseline (no clobber) |
| `isolated` | `honey` | 4 honey-body URLs | INA honey |

---

## Directory layout

```
crawler/
├── crawl_urls.json          # All URL sets, keyed by TEST_TYPE → CRAWL_URL_TYPE
├── package.json             # Node dependencies
├── pyproject.toml           # Python project metadata
└── src/
    ├── config.py            # All env var reads and constants
    ├── env.py               # Env var accessor/setter helpers
    ├── db.py                # Table creation, extension queue management
    ├── crawler.py           # Orchestration: setup → server → worker pool → cleanup
    ├── inspector.py         # Background CPU/process watchdog
    ├── proc.py              # psutil wrappers + timing constants
    ├── runner/
    │   ├── crx_runner.js       # Playwright browser worker (one process per extension/visit)
    │   └── playwright_config.js  # Browser launch args, timeouts, log paths
    └── hooks/
        └── hook_logger.js      # Injected page-side logger for hook/proxy/mutation events
```

---

## How a crawl runs

1. **DB setup** (`db.py:create_test_tables`): Creates all `{TEST_TYPE}_*_{TABLE_SUFFIX}` tables and indexes if they do not exist. For `isolated`, also creates `isolated_clobber_hook_log_*` and `isolated_cs_trace_log_*`.
2. **Extension queue** (`db.py:insert_extensions`): Inserts one row per extension from `/mnt/extensions/{DIR_EXTENSION}/{DATASET}/` into `{TEST_TYPE}_test_extensions`, with `test_status=0`.
3. **Ramdisk mount**: `crawler.py:setup_ramdisk_space` mounts a 10 GB tmpfs at `USER_DATA_DIR` for Chromium profile data.
4. **Test server**: `crawler.py:init_server` starts the Docker-based test server via docker-compose.
5. **Worker pool** (`crawler.py:init_crawler`): Spawns `WORKERS` Python processes, each running `start_crawl(idx)`.
6. **Per-extension loop** (`crawler.py:start_crawl`): Each worker pulls the next unclaimed extension from `test_extensions` (SELECT … FOR UPDATE), marks it `status=1`, then for each URL × visit calls `crawl()`.
7. **Per-URL crawl** (`crawler.py:crawl`): Calls `xvfb-run node crx_runner.js` with a JSON argument containing `{id, url, visit, uid}`.
8. **Browser worker** (`crx_runner.js`): Launches Chromium with the extension loaded, injects `hook_logger.js` (unless visiting the test server directly), navigates to the URL, collects V8 code coverage via CDP, waits `WAIT_TIMEOUT` (6 s), then closes. Coverage is POSTed to the server's `/coverage` endpoint; errors to `/error`.
9. **Process watchdog** (`inspector.py`): Runs independently on a 60-second loop. Terminates any browser process running beyond the TERMINATOR threshold (2.5 min); kills any running beyond VIPER (3 min). Terminates all crawlers if CPU exceeds 90%.
10. **Cleanup**: After all workers finish, `crawler.py` calls `terminate()`, `clean_tmp()`, sends a Telegram notification, and shuts down docker-compose.

### Timing constants (from `proc.py` / `config.py`)

| Constant | Value | Meaning |
|---|---|---|
| `CRAWL_TIMEOUT` | 5 min | `subprocess.Popen.wait()` timeout for one `node crx_runner.js` call |
| `INSPECTION_INTERVAL` | 1 min | Inspector polling interval |
| `TERMINATOR` | 2.5 min | Grace-terminate browser if running longer |
| `VIPER` | 3 min | Force-kill browser if still alive |
| `CPU_THRESHOLD` | 90% | Terminate all crawlers if CPU exceeds this |

---

## Running a crawl

### SNA main crawl

```bash
DATASET=crx_2026-04-14 \
TEST_TYPE=shared \
META_TEST_TYPE=basic \
TABLE_SUFFIX=2026_04_24 \
CRAWL_URL_TYPE=simple \
DIR_EXTENSION=basic \
  python src/crawler.py
```

The SNA crawl visits all 15 URLs in `shared.simple` for every extension, 3 times each (`MAX_VISIT=3` — edit `config.py` to change). Produces tables: `shared_coverage_log_{TABLE_SUFFIX}`, `shared_hook_log_{TABLE_SUFFIX}`, `shared_errors_{TABLE_SUFFIX}`, etc.

### INA main crawl

```bash
DATASET=crx_2026-04-14 \
TEST_TYPE=isolated \
META_TEST_TYPE=basic \
TABLE_SUFFIX=2026_V3 \
CRAWL_URL_TYPE=clobber \
DIR_EXTENSION=basic \
  python src/crawler.py
```

The INA crawl visits 4 URLs (raider_simple, mutation_simple, clobber_proxy_simple, and the targeted clobber payload) for each extension. Produces tables: `isolated_proxy_log_{TABLE_SUFFIX}`, `isolated_mutation_log_{TABLE_SUFFIX}`, `isolated_clobber_hook_log_{TABLE_SUFFIX}`, etc.

### GBS pre-crawl

The GBS pre-crawl collects CS (content-script) traces to identify extensions that read a window global before setting it. Run with a separate `TABLE_SUFFIX`.

```bash
DATASET=crx_2026-04-14 \
TEST_TYPE=isolated \
META_TEST_TYPE=basic \
TABLE_SUFFIX=2026_GBS_PRE \
CRAWL_URL_TYPE=clobber_gbs_trace \
DIR_EXTENSION=basic \
  python src/crawler.py
```

After this crawl completes, run `analyzer/ina/extract_gbs_variables.py` (with `GBS_PRE_SUFFIX=2026_GBS_PRE`) to produce the GBS candidate extension list at `crawler/extension_lists/clobber_gbs_attack.json`.

### GBS attack crawl

Point the crawler at the candidate list produced by `extract_gbs_variables.py`. Use a custom `DIR_EXTENSION` symlink directory containing only the GBS candidate extensions.

```bash
DATASET=crx_2026-04-14 \
TEST_TYPE=isolated \
META_TEST_TYPE=basic \
TABLE_SUFFIX=2026_GBS_ATK \
CRAWL_URL_TYPE=clobber_gbs_attack \
DIR_EXTENSION=gbs_attack_exts \
  python src/crawler.py
```

### Taint crawl

```bash
DATASET=crx_2026-04-14 \
TEST_TYPE=isolated \
META_TEST_TYPE=basic \
TABLE_SUFFIX=2026_TAINT \
CRAWL_URL_TYPE=clobber_taint \
DIR_EXTENSION=basic \
  python src/crawler.py
```

Visits both `type=baseline` and `type=targeted` URLs so the taint analyzer can compare pre- and post-clobber property reads.

---

## Extension directory layout

The crawler reads extensions from `/mnt/extensions/{DIR_EXTENSION}/{DATASET}/`. Each extension must be an unpacked directory named by its Chrome extension ID:

```
/mnt/extensions/
└── basic/
    └── crx_2026-04-14/
        ├── abcdefghijklmnop/     # extension ID → unpacked CRX
        │   ├── manifest.json
        │   └── ...
        └── ...
```

To run a sub-crawl on a specific extension subset, create a directory of symlinks and set `DIR_EXTENSION` accordingly (see the GBS attack crawl example above).

---

## Database tables

All table names follow the pattern `{TEST_TYPE}_{log_type}_{TABLE_SUFFIX}`.

### Shared tables (both TEST_TYPE values)

| Table | Contents |
|---|---|
| `{tt}_test_extensions` | Extension queue (shared across visits; no suffix) |
| `{tt}_hook_log_{s}` | JS API call intercept records (stacktrace, arguments, caller) |
| `{tt}_coverage_log_{s}` | Per-script V8 code coverage (total bytes, executed bytes) |
| `{tt}_mutation_log_{s}` | DOM MutationObserver records (added/removed nodes, target, type) |
| `{tt}_errors_{s}` | Runner and extension JS errors |
| `{tt}_storage_log_{s}` | localStorage / sessionStorage reads/writes |
| `{tt}_cookies_log_{s}` | Cookie reads/writes |
| `{tt}_idb_log_{s}` | IndexedDB operations |
| `{tt}_message_log_{s}` | Extension message-passing records |
| `{tt}_variable_log_{s}` | JS variable state snapshots |
| `{tt}_proxy_log_{s}` | Proxy trap records (property reads off clobbered elements) |
| `{tt}_csp_log_{s}` | CSP violation reports |

`tt` = TEST_TYPE, `s` = TABLE_SUFFIX.

### Isolated-only tables

| Table | Contents |
|---|---|
| `isolated_clobber_hook_log_{s}` | Hook records specific to the clobber payload page |
| `isolated_cs_trace_log_{s}` | Content-script trace records (used by GBS pre-crawl) |

---

## Log files

Crawler logs are written to:

```
~/chaos/crawler/logs/{META_TEST_TYPE}/{TEST_TYPE}/{DATASET[:4]}{TABLE_SUFFIX}_{CRAWL_URL_TYPE}/
```

For example, for `META_TEST_TYPE=basic`, `TEST_TYPE=shared`, `DATASET=crx_2026-04-14`, `TABLE_SUFFIX=2026_04_24`, `CRAWL_URL_TYPE=simple`:

```
~/chaos/crawler/logs/basic/shared/crx_2026_04_24_simple/
├── shared_crawler.log     # Python orchestration log
└── runner.log             # Node Playwright worker log (per-extension errors)
```

If `META_TEST_TYPE=advanced`, HTML snapshots of visited pages are also saved under `~/chaos/crawler/html/`.

---

## Troubleshooting

**`FileNotFoundError` at startup:** The extension mount path `/mnt/extensions/{DIR_EXTENSION}/{DATASET}/` does not exist or is empty. Verify extensions are unpacked and the mount is populated before running the crawler.

**`psycopg2.OperationalError`:** Database credentials in `~/chaos/.env` are missing or incorrect. Check `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS`.

**Tmpfs mount fails:** The crawler process needs permission to run `mount -t tmpfs`. Run as root or grant `CAP_SYS_ADMIN` to the Python process.

**Browser never detects extension (`No extensions detected`):** The unpacked extension directory structure is wrong. Chromium requires the `manifest.json` to be at `{extension_id}/manifest.json` directly under `EXTENSION_DIR`.

**Workers stall / never finish:** Check `inspector.py` is not running separately and competing. The inspector's TERMINATOR and VIPER thresholds are intentionally aggressive — a visit that genuinely takes more than 2.5 min will be killed. Increase `TERMINATOR` / `VIPER` in `proc.py` if testing on slow hardware.

**`CRAWL_URL_TYPE` gives `None` for `TEST_URLS`:** The key is not present under the `TEST_TYPE` namespace in `crawl_urls.json`. Check the exact string matches one of the keys in the URL table above.
