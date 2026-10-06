# Artifact Evaluation Guide

This document details on the steps to install, run, and evaluate the artifact for *Chaos: How Websites May Disrupt Browser Extensions?* (IEEE ACSAC 2026). While the primary [`README.md`](README.md) and the per-component READMEs remain the detailed reference; this file details on the individual component of the artifact, the runtime environment we used to run our experiments and potential system and software requirements on the evaluators' end.

**Badge scope**: We open-source our pipeline and claim for the **Artifact Available** badge here, and not Functional or Reproducible.

---

## 1. Installation and execution

One-time setup, from the repository root:

```bash
./install.sh
```

This installs Python dependencies (`uv sync`), Node.js dependencies (`npm install`), creates `~/chaos/.env` from `.env.example` (every component reads its configuration from this fixed path regardless of where the repo is cloned — edit it afterward with your database credentials), prompts to add `testserver.com` to `/etc/hosts`, and generates a self-signed TLS certificate for the server component.

Exact per-component execution commands are documented in [README.md](README.md#components-mapped-to-the-artifacts-claims) and the component READMEs ([`static/README.md`](static/README.md), [`server/README.md`](server/README.md), [`crawler/README.md`](crawler/README.md), [`analyzer/README.md`](analyzer/README.md)). There is no single command that runs the entire pipeline end to end — different components were used for different sub-analyses, and each is invoked separately with the environment variables documented in its README.

---

## 2. Supported OS and software versions

We implemented and ran our experiments on:

| Software | Version |
|---|---|
| OS | Debian 6.1.106-3 (kernel 6.1.0-25-amd64), x86_64 |
| Node.js | v22.17.1 |
| PostgreSQL | 14.24 (Ubuntu build) |
| Docker Engine | 24.0.5 |
| Docker Compose | v2.20.2 |
| CodeQL CLI | 2.26.3 |

Python: the repository pins `>=3.12` (`.python-version`, `pyproject.toml`). `install.sh` installs `uv`, which downloads and manages this Python version in an isolated environment automatically — the system's default `python` does not need to be upgraded (our own server runs Python 3.10.12 as the system default, but the pipeline runs under `uv`'s managed 3.12 environment).

---

## 3. Hardware, memory, disk, GPU, GUI, network, API, and licensing requirements

- **Hardware/CPU:** No special hardware required. `static/README.md` notes ≥16 cores recommended for the default `WORKERS=20–40` parallelism during static analysis; lower worker counts work on fewer cores at proportionally reduced throughput.
- **RAM:** ``16GB`` is sufficient for a small-scale/prototypical run (the example extension set in `tests/extensions/`). The original full-corpus runs used more, scaled to worker count.
- **Disk:** ``~128GB`` for a partial/batched/quick-test run; ~1TB for the full dataset (not included, as mentioned in [Known limitations](#7-known-limitations-nondeterminism-and-reduced-scale-alternatives)). The 10-extension sample set itself requires negligible disk (tens of MB); the 128GB figure covers unpacked extensions, per-extension CodeQL databases, Chromium profile data, and crawl logs at a representative sub-corpus scale.
- **GPU:** ``Not required``. No component uses GPU acceleration.
- **GUI/display:** ``Not required``. The crawler runs Chromium headed-but-virtual via `xvfb-run`; no physical display is needed on the evaluation machine.
- **Network:** Outbound network access is required for (a) one-time dependency installation (`uv`, `npm`, CodeQL CLI, Playwright's Chromium download), and (b) extension-initiated traffic during crawls — instrumented extensions may themselves attempt real outbound network calls (e.g. to their own backends or the Chrome Web Store) while under test, which the test server does not block. No inbound network access is required; the crawler and server communicate purely over localhost via the `testserver.com` hosts-file entry (``/etc/hosts``).
- **API keys/credentials:** None required for the core pipeline. `static/src/helpers/crx_metadata.py` queries the public Chrome Web Store listing pages for metadata and does not require an API key.
- **Licensing:** This repository is licensed under AGPLv3 ([`LICENSE`](LICENSE)). All third-party tools used (CodeQL CLI, Playwright/Chromium, PostgreSQL, Docker, Node.js packages) are also open-sourced;

---

## 4. Expected runtime

- **Minimal check** (install + a small-scale run against the 10 sample extensions in `tests/extensions/`): approximately **1 hour** for setup (`install.sh`, dependency downloads, Docker image builds) + **1 hour** for a representative pass through static filtering, the server/crawler, and the analyzer against the example set.
- **Full evaluation** (reproducing the paper's reported scale, requires the full dataset, as listed in [Known limitations](#7-known-limitations-nondeterminism-and-reduced-scale-alternatives)): **36+ hours** total, dominated by:
  - SNA crawl: ~24 hours
  - INA crawl (main + Getter-Before-Setter (GBS) branches): ~96 hours
  - INA CodeQL static taint analysis: ~3 hours (conservative estimate for the smaller, already-filtered candidate population that reaches this stage.)

---

## 5. Expected outputs and success criteria

| Component | Expected output | How to tell it succeeded |
|---|---|---|
| `static/` | Populates `extension_dom_queries`, `scripts`, and (for INA) `extension_gbs_vars` DB tables; classifies and instruments extensions under `/datasets/{shared,isolated}_namespace/...` | `main.py` prints per-extension classification counts on completion; no `ERROR`-level log lines in `static/logs/{DATASET}/{DIR_EXTENSION}/static_analyzer.log` |
| `server/` | Two running Docker containers (`web`, `nginx`) serving attack pages | `docker-compose ps` shows both containers `Up`; a browser/`curl` request to `https://testserver.com:9010/` (or `:9000` for SNA) returns a valid attack-page response, not a TLS or connection error |
| `crawler/` | Populates `{shared,isolated}_coverage_log_*`, `*_hook_log_*`, `*_proxy_log_*`, `*_mutation_log_*` tables per extension/visit | Crawler prints a per-extension completion summary; row counts in the above tables match (extensions × visits × URL types) with no persistent `ERROR` entries in crawler logs |
| CodeQL pipeline (`analyzer/ina/codeql_pipeline/`) | One CodeQL database per extension under the configured `db_root`; a JSON result file listing source-to-sink taint flows | `codeql_run_queries.py` prints flow counts per extension on completion; the output JSON's `per_extension_results` entries show `"status": "ok"` for extensions with available databases |
| `analyzer/sna/`, `analyzer/ina/` | JSON result files under `results/sna/{SNA_SUFFIX}/` and `results/ina/{INA_SUFFIX}/` | Each script prints its computed counts to stdout on completion; the corresponding JSON file exists and is non-empty |

A representative-scale success signal for the minimal check: running the pipeline against the 10 extensions in `tests/extensions/` should classify at least one extension per attack sub-vector (SNA: `hook`, `event_swallow`, `global_preassign`, `proto_poison`, `raider`; INA: GBS and selector-based) and produce non-empty result JSON files for each analyzer stage run.

---

## 6. Claim-to-script/Data Mapping

| # | Claim | Script(s) / data |
|---|---|---|
| 1 | Static filtering — candidate selection for individual attacks | [`static/src/main.py`](static/src/main.py) |
| 2 | CodeQL-driven static taint analysis for INA | [`static/src/dom_query_extractor.py`](static/src/dom_query_extractor.py), [`analyzer/ina/codeql_pipeline/`](analyzer/ina/codeql_pipeline/) (`codeql_select_files.py`, `codeql_build_databases.py`, `codeql_run_queries.py`), [`analyzer/ina/codeql_queries/`](analyzer/ina/codeql_queries/) |
| 3 | HTML test pages | [`server/src/server/shared/templates/`](server/src/server/shared/templates/), [`server/src/server/isolated/templates/`](server/src/server/isolated/templates/) |
| 4 | Runtime-behavior analysis scripts (SNA and INA) | [`analyzer/sna/`](analyzer/sna/), [`analyzer/ina/`](analyzer/ina/) |
| 5 | Crawler automation with per-script code coverage | [`crawler/src/crawler.py`](crawler/src/crawler.py) |
| 6 | Crawling server | [`server/`](server/) (Django + Gunicorn + Nginx) |
| 7 | Example extensions | [`tests/extensions/`](tests/extensions/) (10 real `.crx` files) |


---

## 7. Known limitations, Non-determinism, and Reduced-scale Alternatives

- **Full dataset unavailable.** The paper's corpus (200GB+, 54,058 extensions) is not distributed with this artifact. `tests/extensions/` ships 10 real `.crx` files — one per attack sub-vector of SNA (`hook`, `event_swallow`, `global_preassign`, `proto_poison`, `raider`) and INA (GBS and selector-based) — as a reduced-scale substitute for exercising the full pipeline end to end. None of these 10 were part of the paper's responsible-disclosure email campaign, and all were already delisted from the Chrome Web Store at the time of metadata collection, so no live product is being disclosed by their inclusion.
- **No single full-pipeline command.** Different components (static filtering, CodeQL analysis, crawling, runtime analysis) were used for different sub-analyses in the paper and are invoked separately.
- **Timing-sensitive signals.** Functional-disruption (FD) and silent-failure (SF) detection compare baseline vs. attack code-coverage/mutation behavior across crawl visits. Headless Chromium version drift, host machine load, and network latency can shift coverage percentages slightly between runs; the original analysis used a strict 3-visit consistency requirement specifically to bound this noise (as detailed in `analyzer/README.md`'s "Consistency terminology" section). Results from a re-run are expected to be close to, but not bit-for-bit identical to, the paper's reported numbers, especially on hardware or Chromium versions different from those listed in [Section 2](#2-supported-os-and-software-versions).
- **CodeQL query coverage.** The INA static taint queries (`analyzer/ina/codeql_queries/`) are intentionally conservative (documented false-positive filtering is applied downstream, not in this artifact's shipped pipeline) and may under- or over-report flows relative to the paper's fully-filtered, manually-reviewed numbers.
- **Extension-initiated network calls are not sandboxed.** Because some instrumented extensions attempt real outbound calls during crawling ([Section 3](#3-hardware-memory-disk-gpu-gui-network-api-and-licensing-requirements)), evaluators running this on a network-restricted machine may observe those specific calls fail without it affecting the core SNA/INA signal collection.

---