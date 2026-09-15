# Server

Django + Gunicorn + Nginx stack that serves attack pages to the browser and receives all log data from the Playwright runner. The stack runs inside two Docker containers: one for the Django/Gunicorn app (`web`) and one for Nginx (`nginx`).

This README assumes the crawler component is **not** available. All startup, configuration, and management is done directly against Docker and Gunicorn.

---

## Architecture overview

```
Browser (Playwright) ──→ nginx :80 (HTTP)  ─┐
                    ──→ nginx :443 (HTTPS) ─┤──→ Gunicorn :9000 ──→ Django
                                             └──→ /static/ (served by nginx directly)
```

- **nginx** terminates both HTTP (port 9000 externally) and HTTPS (port 9010 externally), proxies to Gunicorn, and serves static files directly from `staticfiles/`.
- **Gunicorn** runs 10 gthread workers × 8 threads (120 concurrent requests), bound to `0.0.0.0:9000` inside the container network.
- **Django** handles all URL routing, renders attack-page templates, generates per-extension clobber payloads dynamically, and writes all log data to PostgreSQL.

---

## Prerequisites

- Docker + docker-compose
- PostgreSQL accessible from the Docker host (the containers connect via `DB_HOST` from the env file)
- TLS certificate at `server/cert/localhost.crt` and `server/cert/localhost.key` (self-signed is fine; the browser is launched with `--ignore-certificate-errors`)
- `testserver.com` must resolve to `127.0.0.1` on the machine that will send requests. Add it to `/etc/hosts`:

```
127.0.0.1  testserver.com
```

---

## Configuration

### Environment file: `~/chaos/.env`

Both containers read `~/chaos/.env` at startup via python-dotenv. Create it on the host before starting:

```
# Database
DB_HOST=<postgres-host>
DB_NAME=chaos
DB_USER=<your-user>
DB_PASS=<your-password>

# Crawl identity — must match the tables already created in PostgreSQL
DATASET=crx_2026-04-14
TEST_TYPE=isolated
META_TEST_TYPE=basic
TABLE_SUFFIX=2026_V3
CRAWL_URL_TYPE=clobber

# INA GBS branch only
GBS_PRE_SUFFIX=2026_GBS_PRE

DEBUG=false
```

`config.py` derives the server-side log directory from these values:

```
/var/logs/{META_TEST_TYPE}/{TEST_TYPE}/{DATASET[:4]}{TABLE_SUFFIX}_{CRAWL_URL_TYPE}/
```

Inside the container, `/var/logs/` is bind-mounted from `../crawler/logs/` on the host (relative to the `server/` directory). Logs therefore land at `crawler/logs/{META_TEST_TYPE}/{TEST_TYPE}/...` on the host.

### Environment variables reference

| Variable | Required | Description |
|---|---|---|
| `DB_HOST` | yes | PostgreSQL host. Must be reachable from inside the Docker network. Use the host machine's IP or Docker gateway (e.g. `172.17.0.1`), not `localhost`. |
| `DB_NAME` | yes | Database name (e.g. `chaos`). |
| `DB_USER` | yes | Database user. |
| `DB_PASS` | yes | Database password. |
| `DATASET` | yes | Dataset identifier matching the `dataset` column in all DB tables (e.g. `crx_2026-04-14`). |
| `TEST_TYPE` | yes | `shared` (SNA) or `isolated` (INA). Selects DB table prefix and URL routing namespace. |
| `META_TEST_TYPE` | yes | `basic` or `advanced`. Used for log directory naming only. |
| `TABLE_SUFFIX` | yes | Suffix of the DB tables to write into (e.g. `2026_V3`). Tables must already exist (created by the crawler's `db.py:create_test_tables`). |
| `CRAWL_URL_TYPE` | yes | URL set key (e.g. `clobber`). Used for log directory naming only. |
| `GBS_PRE_SUFFIX` | INA/GBS only | Table suffix for the GBS pre-crawl `variable_log`. Read by `gbs_trace_script/`. Default: `2026_GBS_PRE`. |

---

## Directory layout

```
server/
├── cert/
│   ├── localhost.crt          # TLS certificate (self-signed)
│   └── localhost.key          # TLS private key
├── docker-compose.yml         # Defines web + nginx services
├── nginx/
│   ├── Dockerfile             # nginx:latest, replaces default.conf
│   └── nginx.conf             # HTTP :80 + HTTPS :443, upstream=web:9000
└── src/
    ├── Dockerfile             # python:3.13-alpine, installs requirements
    ├── requirements.txt       # Python dependencies
    └── server/
        ├── config.py          # Env var reads, DB connection string, log path setup
        ├── gunicorn.conf.py   # 10 workers × 2 threads, timeout=120s, wsgi_app=server.wsgi
        ├── manage.py          # Django management entry point
        ├── server/            # Django project package
        │   ├── settings.py    # INSTALLED_APPS, STATIC_ROOT, ALLOWED_HOSTS=*
        │   ├── urls.py        # Root URL conf: /shared/, /isolated/, /csp, /admin/
        │   ├── db.py          # All DB store/query functions, psycopg connection pool
        │   ├── shared_view.py # All view handlers and dynamic page generators
        │   ├── wsgi.py
        │   └── asgi.py
        ├── shared/            # SNA Django app
        │   ├── templates/shared/   # SNA attack-page templates
        │   ├── views.py       # index, hook, mutation
        │   └── urls.py        # /shared/* routes
        ├── isolated/          # INA Django app
        │   ├── templates/isolated/ # INA attack-page templates
        │   ├── views.py       # index (with clobber_payload + clobber_gbs_payload dispatch)
        │   └── urls.py        # /isolated/* routes
        └── static/
            ├── scripts/       # All attack and instrumentation JavaScript
            ├── img/           # Honey images
            ├── media/         # Honey audio/video
            ├── css/
            ├── fonts/
            └── manifest/
```

---

## Starting the server

### With docker-compose (standard path)

From the `server/` directory:

```bash
docker-compose --env-file ~/chaos/.env up --build -d
```

This builds both images if needed, starts the `web` container (Gunicorn on port 9000 inside the Docker network) and the `nginx` container (ports 9000:80 and 9010:443 on the host), and detaches.

Verify both containers are up:

```bash
docker-compose ps
```

Expected output:

```
NAME      IMAGE           STATUS    PORTS
nginx     server-nginx    Up        0.0.0.0:9000->80/tcp, 0.0.0.0:9010->443/tcp
web       server-web      Up        9000/tcp
```

Follow logs:

```bash
docker-compose logs -f web      # Gunicorn + Django application logs
docker-compose logs -f nginx    # nginx access and error logs
```

Stop and remove containers:

```bash
docker-compose down
```

### Rebuilding after source changes

Any change to Python files, templates, or static assets requires a rebuild:

```bash
docker-compose --env-file ~/chaos/.env up --build -d
```

### Starting the Gunicorn container only (no nginx)

If you only need HTTP access (e.g. for local testing without TLS):

```bash
docker-compose --env-file ~/chaos/.env up --build -d web
```

The Django app will be reachable at `http://localhost:9000/` directly.

### Stopping gunicorn without docker-compose

If Gunicorn was started standalone (not via docker-compose), use the PID file:

```bash
kill $(cat /var/logs/.../gunicorn_server.pid)
```

---

## Gunicorn configuration

`gunicorn.conf.py` is referenced by the docker-compose `command` field and loaded automatically. There is no need to pass `--workers` or `--threads` flags manually.

| Setting | Value | Notes |
|---|---|---|
| `bind` | `0.0.0.0:9000` | Listens on all interfaces inside the container |
| `workers` | 10 | gthread worker class |
| `threads` | 2 | 120 concurrent requests total |
| `timeout` | 120 s | Worker killed if silent for this long |
| `keepalive` | 75 s | Matches nginx `keepalive_timeout 75s` |
| `preload` | `True` | DB connection pool (`ConnectionPool`) initialised once in the master process, shared across workers via fork |
| `wsgi_app` | `server.wsgi` | Django WSGI application |
| `max_requests` | 0 | Workers never recycled due to request count |
| `errorlog` | `/var/logs/.../gunicorn.log` | Worker stdout/stderr captured here |
| `pidfile` | `/var/logs/.../gunicorn_server.pid` | |

To change worker count or timeout without a full image rebuild, edit `src/server/gunicorn.conf.py` and re-run `docker-compose up --build -d web`.

---

## Nginx configuration

`nginx/nginx.conf` defines two server blocks:

**HTTP — listens on :80 (host port 9000)**

- Proxies all requests to `upstream django` (Gunicorn at `web:9000` inside the Docker network)
- Serves `/static/` directly from `/usr/src/app/staticfiles/` (no Gunicorn round-trip)
- `client_max_body_size 1000M` — coverage payloads can be several MB per request
- Access log: `/var/logs/nginx/http.access.log`
- Error log: `/var/logs/nginx/http.error.log`

**HTTPS — listens on :443 (host port 9010)**

- Same proxy config as HTTP
- TLS via `cert/localhost.crt` + `cert/localhost.key` (mounted into the nginx container)
- Adds `Access-Control-Allow-Origin: *` on all GET/POST responses
- Access log: `/var/logs/nginx/https.access.log`
- Error log: `/var/logs/nginx/https.error.log`

The `net.ipv4.ip_local_port_range: "8999 65535"` sysctls on the nginx service allow opening enough ephemeral ports for high-concurrency crawls.

**On the host**, nginx logs land at `crawler/logs/nginx/` (via the volume mount). The analyzer reads `https.error.log` — symlink or copy it to `analyzer/https.error.log` before running `sna_error_log_analysis.py` or `ina_error_log_analysis.py`.

---

## URL routes

### Root (`/`)

| URL | Handler | Description |
|---|---|---|
| `/admin/` | Django admin | |
| `/favicon.ico` | `shared_view.favicon` | |
| `/csp` | `shared_view.csp_endpoint` | POST: receives CSP violation reports |

### Shared namespace (`/shared/`) — SNA

| URL | Handler | Description |
|---|---|---|
| `/shared/?template=<name>.html` | `shared.views.index` | Renders `shared/templates/shared/<name>.html` |
| `/shared/scripts/?name=<js>` | `shared_view.scripts` | Serves `static/scripts/<js>` as `application/javascript` |
| `/shared/images/?name=<img>` | `shared_view.images` | Serves `static/img/<img>` |
| `/shared/media/?name=<file>` | `shared_view.media` | Serves `static/media/<file>` |
| `/shared/preassign_script/?extensionId=<id>` | `shared_view.preassign_script` | Dynamically generates the global pre-assignment break script for this extension |
| `/shared/error` | `shared_view.error_logs` | POST: stores JS errors from the runner |
| `/shared/hook` | `shared_view.hook_logs` | POST: stores hook intercept records |
| `/shared/mutation` | `shared_view.mutation_logs` | POST: stores MutationObserver records |
| `/shared/poll` | `shared_view.poll_logs` | POST: stores cookies / localStorage / IDB / messages / variables / cs_trace |
| `/shared/coverage` | `shared_view.coverage_logs` | POST: stores V8 code coverage |
| `/shared/proxy` | `shared_view.proxy_logs` | POST: stores proxy trap records |

### Isolated namespace (`/isolated/`) — INA

All `/shared/` log endpoints are also present under `/isolated/`, plus:

| URL | Handler | Description |
|---|---|---|
| `/isolated/?template=clobber_payload&type=targeted&extensionId=<id>` | `shared_view.clobber_payload` | Per-extension clobber page: attacker payload (prepended) + honey body |
| `/isolated/?template=clobber_payload&type=baseline` | `shared_view.clobber_payload` | Honey body only — no attacker payload. Used as within-crawl FD/SF baseline |
| `/isolated/?template=clobber_payload&type=trigger&extensionId=<id>` | `shared_view.clobber_trigger_payload` | executeScript-coordination trigger variant |
| `/isolated/?template=clobber_gbs_payload&extensionId=<id>` | `shared_view.clobber_gbs_payload` | GBS attack page: `<a id="V">` elements in `<head>` for each GBS variable |
| `/isolated/clobber` | `shared_view.clobber_logs` | POST: stores clobber hook records (includes `proxy_data` field) |
| `/isolated/gbs_trace_script/?extensionId=<id>&preSuffix=<s>` | `shared_view.gbs_trace_script` | Dynamically generates transparent GBS get/set trace hooks |

---

## Dynamic page generation

Three endpoints generate per-extension content at request time. These require their respective DB tables to be populated before the crawl starts.

### `clobber_payload` — INA targeted clobber

Reads `extension_clobber_payloads.payload_html` for the `extensionId`, then builds an HTML page with:

1. Instrumentation scripts in `<head>` (`lifecycle_tracker.js`, `sparkmd5.js`, `mutation_hashes.js`, `mutation.js`, `v2_dispatch.js`)
2. The per-extension attacker payload **prepended** at the top of `<body>`
3. The honey body (inner HTML of `isolated/templates/isolated/clobber_proxy.html`, cached in-process after first read) appended after the payload

Prepending over appending gives the attacker elements first-in-document-order priority so `getElementById` and selector first-match return the clobbered element — the realistic DOM-clobbering scenario.

**DB prerequisite:** `extension_clobber_payloads` must be populated by the static analysis component before the INA crawl starts.

### `preassign_script` — SNA global_preassign

Queries `extension_vars` (static analysis) and `{TEST_TYPE}_variable_log_{TABLE_SUFFIX}` (dynamic observation) for the extension. Returns synchronous JavaScript that installs `Object.defineProperty` traps with `configurable: false` on each variable, causing both reads and writes to throw before the extension's content script can set them.

**DB prerequisite:** `extension_vars` must be populated by the static analysis component.

### `clobber_gbs_payload` and `gbs_trace_script` — INA GBS branch

- `clobber_gbs_payload`: reads `extension_gbs_vars.var_names` and injects `<a id="V" name="V" style="display:none">` in `<head>` for each variable, so elements exist before any content script runs at `document_start`.
- `gbs_trace_script`: reads `isolated_variable_log_{GBS_PRE_SUFFIX}` and generates transparent `defineProperty` hooks that record get/set order and dispatch a `cs_trace` event via `__dispatchPollData`.

**DB prerequisite:** `extension_gbs_vars` must be populated by `analyzer/ina/extract_gbs_variables.py` before the GBS attack crawl starts.

---

## Database connection pool

`server/db.py` initialises a `psycopg_pool.ConnectionPool` at import time:

```python
CONNECTION_POOL = ConnectionPool(conninfo=CONNECTION_INFO, min_size=5, max_size=10, timeout=30)
```

Because Gunicorn runs with `preload=True`, this pool is created once in the master process and inherited by all 10 workers via `fork()`. All store functions use `with CONNECTION_POOL.connection()` — connections are returned automatically after each request.

If the pool is exhausted (all 10 connections busy), new requests wait up to 30 seconds before raising `PoolTimeout`. For crawls with more than ~100 parallel browser workers, raise `max_size` in `db.py` and rebuild the `web` container.

---

## Static files

`settings.py` sets `STATIC_ROOT = src/server/static/`. The docker-compose volume mounts `src/server/` into `/usr/src/app/` inside the container, so the full path inside the container is `/usr/src/app/static/`. Nginx serves `/static/` from this path directly.

### Attack and instrumentation scripts (`static/scripts/`)

| Script | Purpose |
|---|---|
| `hook.js` / `hook_break.js` | SNA hook attack and break variant |
| `raider.js` / `raider_break.js` | SNA DOM raider attack and break variant |
| `mutation.js` / `mutation_hashes.js` | MutationObserver instrumentation + MD5 deduplication |
| `proto_poison.js` / `proto_poison_break.js` | SNA prototype poisoning |
| `event_swallow.js` / `event_swallow_break.js` | SNA event swallowing |
| `global_preassign.js` / `global_preassign_break.js` | SNA global pre-assignment (static variant) |
| `promise_poison.js` / `promise_poison_break.js` | SNA promise poisoning |
| `eval_poison.js` / `eval_poison_break.js` | SNA eval poisoning |
| `clobber_ui.js` | INA clobber proxy instrumentation |
| `clobber_taint.js` | INA taint sentinel injection |
| `clobber_trigger.js` | INA executeScript-coordination trigger |
| `lifecycle_tracker.js` | Lifecycle stage tracking (`document_start` / `DOMContentLoaded` / `load`) |
| `v2_dispatch.js` | Unified hook and poll data dispatcher |
| `sparkmd5.js` | SparkMD5 for mutation deduplication |
| `mo.js` | MutationObserver bootstrap |
| `hook_ui.js` / `hook_helper.js` | Hook UI helpers |
| `ads.js` / `ads_hooked.js` | Ad-slot honey content |

---

## Attack-page templates

### Shared namespace (`shared/templates/shared/`)

Each attack has a base template (no break script) and a `_break` variant. The V8 code coverage delta between the two is what `sna_execution_impact.py` measures as fck.

| Template pair | Attack |
|---|---|
| `hook_simple.html` / `hook_simple_break.html` | API hooking |
| `raider_simple.html` / `raider_simple_break.html` | DOM raiding |
| `proto_poison_simple.html` / `proto_poison_simple_break.html` | Prototype poisoning |
| `event_swallow_simple.html` / `event_swallow_simple_break.html` | Event swallowing |
| `global_preassign_simple.html` / `global_preassign_simple_break.html` | Global pre-assignment |
| `promise_poison_simple.html` / `promise_poison_simple_break.html` | Promise poisoning |
| `eval_poison_simple.html` / `eval_poison_simple_break.html` | Eval poisoning |
| `hook.html` / `raider.html` / `mutation.html` | Honey body baseline pages |

### Isolated namespace (`isolated/templates/isolated/`)

| Template | Purpose |
|---|---|
| `raider_simple.html` | INA baseline raider |
| `mutation_simple.html` | INA baseline mutation |
| `clobber_proxy.html` | Honey body source (inner HTML cached by `_load_honey_body()` at runtime) |
| `clobber_proxy_simple.html` | Simple clobber proxy variant |
| `clobber_taint_simple.html` | Taint crawl variant |
| `clobber_trigger_simple.html` / `clobber_trigger_baseline.html` | Trigger crawl variants |
| `clobber_gbs_simple.html` | GBS reference template |

The main clobber payload page (`clobber_payload`) and GBS attack page (`clobber_gbs_payload`) are generated entirely in Python and have no static template files.

---

## Log files produced

| Path on host (relative to repo root) | Contents |
|---|---|
| `crawler/logs/{META}/{TEST}/{DATASET[:4]}{SUFFIX}_{TYPE}/{TEST_TYPE}.log` | Django + Gunicorn application log |
| `crawler/logs/{META}/{TEST}/{DATASET[:4]}{SUFFIX}_{TYPE}/gunicorn.log` | Gunicorn worker stdout/stderr |
| `crawler/logs/{META}/{TEST}/{DATASET[:4]}{SUFFIX}_{TYPE}/gunicorn_server.pid` | Gunicorn PID |
| `crawler/logs/nginx/http.access.log` | nginx HTTP access log |
| `crawler/logs/nginx/https.access.log` | nginx HTTPS access log |
| `crawler/logs/nginx/http.error.log` | nginx HTTP error log |
| `crawler/logs/nginx/https.error.log` | nginx HTTPS error log (read by the analyzer) |

To use the error log with the analyzer, symlink or copy it:

```bash
ln -s ../crawler/logs/nginx/https.error.log analyzer/https.error.log
```

---

## Troubleshooting

**Container exits immediately with `KeyError` or `TypeError: 'NoneType'`:** `config.py` runs at import time and calls `DATASET[:4]` to build the log path. If `DATASET` is absent from the env file, the import crashes before Django starts. Check that `--env-file ~/chaos/.env` is passed and all required variables are present.

**nginx 502 Bad Gateway:** Gunicorn is not responding. Run `docker-compose logs web` for Django import errors or DB connection failures. The most common cause: `DB_HOST=localhost` resolves to the container's own loopback — set it to the host machine's IP or the Docker bridge gateway (`172.17.0.1` by default).

**`PoolTimeout` in logs:** The psycopg connection pool hit `max_size=10`. Raise `max_size` in `server/db.py` and rebuild: `docker-compose up --build -d web`.

**`clobber_payload` returns `No clobber payload found`:** The `extension_clobber_payloads` table is empty or not populated for this dataset. The static analysis component must run before the INA crawl.

**`gbs_trace_script` returns `// No variables found`:** Either `extension_gbs_vars` is not populated (run `extract_gbs_variables.py` first) or `GBS_PRE_SUFFIX` points to the wrong table suffix.

**`preassign_script` returns `// No variables found`:** `extension_vars` is not populated for this dataset. Run the static analysis component first.

**Port 9000 or 9010 already in use:** Stop the conflicting process (`lsof -i :9000`) or stop a previous docker-compose deployment (`docker-compose down`) before starting again.

**TLS handshake errors from the browser:** The certificate at `cert/localhost.crt` is expired or missing. Generate a new self-signed cert:

```bash
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout server/cert/localhost.key \
  -out server/cert/localhost.crt \
  -subj "/CN=localhost"
```

Then rebuild: `docker-compose up --build -d`.
