# Chaos: How Websites May Disrupt Browser Extensions?

Artifact for the paper *Chaos: How Websites May Disrupt Browser Extensions?* (IEEE ACSAC 2026). This repository contains the components used to measure Shared Namespace Attacks (SNA) and Isolated Namespace Attacks (INA) against Chrome browser extensions.

The full dataset used in the paper is 200GB+ and is not included; a small representative set of extensions ships for demonstration (see [Example extensions](#7-example-extensions)). Different components were used for different sub-analyses and data collection — there is no single command that runs the entire artifact end to end.

---

## One-time setup

Run the installer from the repository root:

```bash
./install.sh
```

This installs Python dependencies (via `uv`), Node.js dependencies (via `npm`), creates `~/chaos/.env` from `.env.example` (every component reads its configuration from this fixed path, regardless of where this repo is cloned), prompts to add `testserver.com` to `/etc/hosts`, and generates a self-signed TLS certificate for the server component. Edit `~/chaos/.env` afterward with your database credentials.

We recommend running this in an isolated virtual environment — installing dependencies system-wide can conflict with existing packages on your machine.

---

## Repository layout

```
chaos/
├── static/      # Static filtering, extension classification, CodeQL static taint analysis
├── server/      # Test server: attack pages served to the crawler
├── crawler/     # Browser automation: Playwright workers, code-coverage capture
├── analyzer/    # Runtime-behavior analysis for SNA and INA
├── install.sh
├── pyproject.toml   # Root uv workspace — all Python dependencies
├── package.json     # Root npm workspace — all Node.js dependencies
└── uv.lock
```

---

## Components, mapped to the artifact's claims

### 1. Static filtering — candidate selection for individual attacks

`static/src/main.py` unpacks CRX files and classifies each extension into the SNA and/or INA candidate populations, instrumenting INA candidates with the content-script hook (`static/src/hooks/__cs_hook.js`).

```bash
DATASET_TS=2026-04-14 python static/src/main.py
```

See [`static/README.md`](static/README.md).

### 2. CodeQL-driven static taint analysis for INA

`static/src/dom_query_extractor.py` extracts candidate DOM-query sinks per extension. `analyzer/ina/codeql_pipeline/` selects the relevant source files per extension, builds a CodeQL database per extension, and runs the taint queries in `analyzer/ina/codeql_queries/`:

```bash
DATASET=crx_2026-04-14 python static/src/dom_query_extractor.py

python analyzer/ina/codeql_pipeline/codeql_select_files.py
python analyzer/ina/codeql_pipeline/codeql_build_databases.py
python analyzer/ina/codeql_pipeline/codeql_run_queries.py \
    --query analyzer/ina/codeql_queries/ext_taint_locations_expanded.ql
```

Requires the [CodeQL CLI](https://github.com/github/codeql-cli-binaries) on `PATH`.

### 3. HTML test pages

`server/src/server/*/templates/` contains the attack-page templates served to the crawler for both SNA and INA (baseline and attack variants for each sub-vector).

### 4. Runtime-behavior analysis scripts (SNA and INA)

`analyzer/sna/` and `analyzer/ina/` compute functional disruption, silent failure, and dangerous-sink coverage from the logs written by the crawler:

```bash
cd analyzer
DATASET=crx_2026-04-14 SNA_SUFFIX=2026_04_24 python sna/run_all.py
DATASET=crx_2026-04-14 INA_SUFFIX=2026_V3 python ina/run_all.py
```

See [`analyzer/README.md`](analyzer/README.md).

### 5. Crawler automation with per-script code coverage

`crawler/src/crawler.py` runs a multiprocessing pool of Playwright workers that load each extension, visit attack pages, and capture per-script code coverage alongside hook, proxy, and mutation logs:

```bash
DATASET=crx_2026-04-14 \
TEST_TYPE=shared \
META_TEST_TYPE=basic \
TABLE_SUFFIX=2026_04_24 \
CRAWL_URL_TYPE=simple \
DIR_EXTENSION=basic \
  python crawler/src/crawler.py
```

See [`crawler/README.md`](crawler/README.md).

### 6. Crawling server

`server/` — Django + Gunicorn + Nginx stack serving the attack pages and receiving log data from the crawler.

```bash
export DATASET=crx_2026-04-14
export TEST_TYPE=shared
export META_TEST_TYPE=basic
export TABLE_SUFFIX=2026_04_24
export CRAWL_URL_TYPE=simple

cd server
docker-compose --env-file ~/chaos/.env up --build -d
```

The server must be running before the crawler starts. See [`server/README.md`](server/README.md).

### 7. Example extensions

`tests/extensions/` contains 10 real, packed `.crx` files covering every attack sub-vector — 5 SNA (one per sub-vector: `hook`, `event_swallow`, `global_preassign`, `proto_poison`, `raider`), 2 INA-GBS, 2 INA-selector, and 1 flagged under both INA categories. None of these were part of the paper's responsible-disclosure email campaign; all were already delisted from the Chrome Web Store by the time metadata was fetched, so there is no live product being disclosed.

`static/src/main.py` expects raw `.crx` files directly under `/datasets/{DATASET}/` (see `static/src/config.py`). To run the pipeline against this example set:

```bash
mkdir -p /datasets/crx_example
cp tests/extensions/*.crx /datasets/crx_example/
DATASET_TS=example python static/src/main.py
```

---

## Component READMEs

| Component | README | Purpose |
|---|---|---|
| Static analysis | [`static/README.md`](static/README.md) | CRX unpacking, extension classification, hook instrumentation, CodeQL taint analysis inputs |
| Server | [`server/README.md`](server/README.md) | Docker + Gunicorn + nginx setup, attack-page templates, log endpoints |
| Crawler | [`crawler/README.md`](crawler/README.md) | Playwright worker architecture, `CRAWL_URL_TYPE` values, per-crawl run commands, DB tables written |
| Analyzer | [`analyzer/README.md`](analyzer/README.md) | SNA and INA runtime-behavior analysis, environment variables, output files |
