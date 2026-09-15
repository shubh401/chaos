# Analyzer

Post-crawl analysis pipeline for Shared Namespace Attacks (SNA) and Isolated Namespace Attacks (INA). All scripts read from PostgreSQL tables written by the crawler and write JSON results to `results/`.

## Prerequisites

### Python dependencies

Install all Python dependencies from the repository root using `uv`:

```bash
uv sync
```

### Database

Scripts connect using environment variables. Create a `.env` file at `~/chaos/.env`:

```
DB_HOST=localhost
DB_NAME=chaos
DB_USER=your_user
DB_PASS=your_password
```

All scripts source this file automatically via `db_helpers.py`.

### Scripts table

Script classification (WAR vs CS vs BG) requires the `scripts` table to be populated for your dataset. This is filled by the static analysis component before crawling.

---

## Environment variables

Every analysis run requires these variables to be set in the shell. There are no hardcoded defaults — missing variables will cause a clear error at startup.

| Variable | Required by | Description |
|---|---|---|
| `DATASET` | all scripts | Dataset identifier (e.g. `crx_2026-04-14`). Must match the `dataset` column in the DB. |
| `SNA_SUFFIX` | SNA scripts | Table suffix for the SNA crawl (e.g. `2026_04_24`). Reads `shared_coverage_log_{SNA_SUFFIX}`. |
| `INA_SUFFIX` | INA main scripts | Table suffix for the INA crawl (e.g. `2026_V1`). Reads `isolated_*_{INA_SUFFIX}`. |
| `GBS_PRE_SUFFIX` | `extract_gbs_variables.py` | Table suffix for the GBS pre-crawl CS trace log (e.g. `2026_GBS_PRE`). |
| `TAINT_SUFFIX` | `ina_taint_analysis.py`, `taint_overlap.py` | Table suffix for the taint crawl (e.g. `2026_TAINT`). |

---

## Directory layout

```
analyzer/
├── db_helpers.py          # DB connection, script classification, shared constants
├── results/               # All output lands here (created automatically)
│   ├── sna/{SNA_SUFFIX}/
│   └── ina/{INA_SUFFIX}/
│       └── taint/
├── sna/
│   ├── sna_helpers.py
│   ├── run_all.py
│   ├── sna_execution_impact.py
│   ├── sna_consistency_report.py
│   ├── sna_component_impact.py
│   └── sna_error_log_analysis.py
└── ina/
    ├── ina_helpers.py
    ├── run_all.py
    ├── ina_hit_rate.py
    ├── ina_dangerous_sinks.py
    ├── ina_coverage_impact.py
    ├── ina_mutation_delta.py
    ├── ina_consistency_report.py
    ├── ina_proxy_access_counts.py
    ├── ina_error_log_analysis.py
    ├── ina_fd_severity.py
    ├── ina_nondangerous_fd.py
    ├── ina_gbs_sinks.py
    ├── ina_variable_analysis.py
    ├── ina_taint_analysis.py
    ├── extract_gbs_variables.py
    ├── taint_overlap.py
    ├── clobber_vuln_detector.py
    ├── codeql_pipeline/
    │   ├── codeql_select_files.py
    │   ├── codeql_build_databases.py
    │   └── codeql_run_queries.py
    └── codeql_queries/
        ├── ext_taint.ql
        ├── ext_taint_locations.ql
        ├── ext_taint_locations_expanded.ql
        └── qlpack.yml
```

All scripts must be run from the `analyzer/` directory.

---

## SNA analysis

### What it measures

SNA measures how five attack techniques disrupt extension code execution:

| Attack | Template pair | Mechanism |
|---|---|---|
| `hook` | `hook_simple` / `hook_simple_break` | Overwrites browser APIs before the extension loads |
| `global_preassign` | `mutation_simple` / `global_preassign_simple_break` | Pre-assigns globals the extension expects to set |
| `event_swallow` | `event_swallow_simple` / `event_swallow_simple_break` | Swallows DOM events extensions listen for |
| `raider` | `raider_simple` / `raider_simple_break` | Removes DOM state extensions rely on |
| `proto_poison` | `proto_poison_simple` / `proto_poison_simple_break` | Poisons prototype chain |

Impact is measured as **fraction of code killed (fck)**: `(exec_baseline - exec_attack) / total_src_bytes`. An extension is considered *affected* if `fck > 5%` across all 3 visits (strict AND).

### Pipeline

Run the full pipeline with one command:

```bash
DATASET=crx_2026-04-14 SNA_SUFFIX=2026_05_26 python sna/run_all.py
```

Or run scripts individually in order:

```bash
# Step 1 — compute fck per extension per attack per visit
DATASET=crx_2026-04-14 SNA_SUFFIX=2026_05_26 python sna/sna_execution_impact.py

# Step 2 — cross-visit consistency, strict/majority sets, kill severity
DATASET=crx_2026-04-14 SNA_SUFFIX=2026_05_26 python sna/sna_consistency_report.py

# Step 3 — WAR vs CS vs BG component breakdown
DATASET=crx_2026-04-14 SNA_SUFFIX=2026_05_26 python sna/sna_component_impact.py

# Step 4 — attribute visit-level inconsistency to nginx dropped rows (optional)
DATASET=crx_2026-04-14 SNA_SUFFIX=2026_05_26 python sna/sna_error_log_analysis.py
```

Step 4 requires an `https.error.log` file from the crawl server at `analyzer/https.error.log`.

### Output files

All written to `results/sna/{SNA_SUFFIX}/`:

| File | Contents |
|---|---|
| `sna_execution_impact.json` | Per-visit fck per extension per attack. Input for all downstream scripts. |
| `sna_consistency_report.json` | Per-attack strict/majority/union sets, pairwise Jaccard, kill severity bins. |
| `sna_component_impact.json` | WAR vs CS vs BG breakdown of fck and affected counts. |
| `sna_error_log_analysis.json` | Per-extension dropped-row attribution from the nginx error log. |

---

## INA analysis

### What it measures

INA measures how DOM clobbering attacks affect extensions. There are two independent attack surfaces:

**Selector-based (FD/SF):** The crawler injects a per-extension clobber payload (elements matching the extension's own DOM selectors) and measures:
- **Dangerous sink access** — extension reads `href`, `src`, `innerHTML`, etc. off the clobbered element (proxy signal)
- **Functional disruption (FD)** — extension executes significantly less code under attack vs baseline (`fck > 5%`, strict AND across 3 visits)
- **Silent failure (SF)** — extension produces ≥80% fewer DOM mutations under attack vs baseline

**Getter-Before-Setter (GBS):** A window global that the extension reads before setting is clobbered with an `<a>` element. Measured separately with its own baseline and attack URLs.

**Taint tracking:** A separate crawl instruments property reads off clobbered elements with a sentinel value and traces whether it reaches a network/storage/DOM sink.

### INA pipeline — main crawl

Run the full consistency pipeline:

```bash
DATASET=crx_2026-04-14 INA_SUFFIX=2026_V2 python ina/run_all.py
```

Or individually:

```bash
# Step 1 — hit rate: which extensions receive clobbered elements across visits
DATASET=crx_2026-04-14 INA_SUFFIX=2026_V2 python ina/ina_hit_rate.py

# Step 2 — dangerous sink: extensions reading security-relevant properties
DATASET=crx_2026-04-14 INA_SUFFIX=2026_V2 python ina/ina_dangerous_sinks.py

# Step 3 — coverage impact: FD (fraction code killed) per visit
DATASET=crx_2026-04-14 INA_SUFFIX=2026_V2 python ina/ina_coverage_impact.py

# Step 4 — mutation delta: SF (mutation loss ≥80%) per visit
DATASET=crx_2026-04-14 INA_SUFFIX=2026_V2 python ina/ina_mutation_delta.py

# Step 5 — proxy access taxonomy: all leaf property accesses (dangerous + non-dangerous)
DATASET=crx_2026-04-14 INA_SUFFIX=2026_V2 python ina/ina_proxy_access_counts.py

# Step 6 — cross-signal consistency report (reads steps 1–4 JSONs)
DATASET=crx_2026-04-14 INA_SUFFIX=2026_V2 python ina/ina_consistency_report.py

# Step 7 — dropped-row attribution from nginx error log (optional)
DATASET=crx_2026-04-14 INA_SUFFIX=2026_V2 python ina/ina_error_log_analysis.py
```

Step 7 requires `analyzer/https.error.log`.

### INA pipeline — extended analyses

Run after the main pipeline (steps 1–5 must complete first):

```bash
# FD kill/expand severity distribution for strict FD set
DATASET=crx_2026-04-14 INA_SUFFIX=2026_V2 python ina/ina_fd_severity.py

# FD for extensions outside the selector-payload population (non-dangerous property readers)
DATASET=crx_2026-04-14 INA_SUFFIX=2026_V2 python ina/ina_nondangerous_fd.py

# Variable distribution: GBS variable names + dangerous sink selectors
DATASET=crx_2026-04-14 INA_SUFFIX=2026_V2 python ina/ina_variable_analysis.py
```

### INA pipeline — GBS branch

The GBS analysis requires a separate pre-crawl step to identify candidate extensions, then a dedicated attack crawl. Run `extract_gbs_variables.py` **after the baseline GBS trace crawl completes** and **before the GBS attack crawl starts**:

```bash
# Pre-crawl: build GBS candidate list from CS trace log
GBS_PRE_SUFFIX=2026_GBS_PRE DATASET=crx_2026-04-14 python ina/extract_gbs_variables.py
```

This writes the candidate extension list to `crawler/extension_lists/clobber_gbs_attack.json` and creates the `extension_gbs_vars` DB table. Pass the output list to the crawler via `EXTENSION_LIST_FILE`.

After the GBS attack crawl completes:

```bash
# Analyze GBS proxy data: tier classification (dangerous / meaningful / structural)
DATASET=crx_2026-04-14 INA_SUFFIX=2026_V2 python ina/ina_gbs_sinks.py
```

### INA pipeline — taint analysis

Run after the taint crawl completes (separate crawl, different suffix):

```bash
# Dynamic taint: sentinel propagation through dangerous property reads to sinks
DATASET=crx_2026-04-14 TAINT_SUFFIX=2026_TAINT python ina/ina_taint_analysis.py

# Overlap: static taint (DB) vs dynamic taint (above output)
DATASET=crx_2026-04-14 TAINT_SUFFIX=2026_TAINT python ina/taint_overlap.py
```

`taint_overlap.py` also queries the `extension_taint_flows` table populated by the static taint extractor.

### CodeQL static taint analysis

A separate, interprocedural static taint analysis using CodeQL, distinct from the AST-based `static/src/taint_flow_analyzer.py` above. Requires the [CodeQL CLI](https://github.com/github/codeql-cli-binaries) and `static/src/dom_query_extractor.py` to have already populated `extension_dom_queries`.

```bash
python ina/codeql_pipeline/codeql_select_files.py
python ina/codeql_pipeline/codeql_build_databases.py
python ina/codeql_pipeline/codeql_run_queries.py \
    --query ina/codeql_queries/ext_taint_locations_expanded.ql
```

`codeql_select_files.py` selects, per extension, the source files relevant to the DOM-clobbering taint query. `codeql_build_databases.py` builds one CodeQL database per extension. `codeql_run_queries.py` runs the query in `ina/codeql_queries/` against every database and writes the resulting source-to-sink flows to JSON.

### INA output files

Main pipeline — written to `results/ina/{INA_SUFFIX}/`:

| File | Script | Contents |
|---|---|---|
| `ina_hit_rate.json` | `ina_hit_rate.py` | Per-visit hit rate (extensions receiving clobbered elements). |
| `ina_dangerous_sinks.json` | `ina_dangerous_sinks.py` | Per-visit dangerous sink sets and pairwise Jaccard. |
| `ina_coverage_impact.json` | `ina_coverage_impact.py` | Per-visit FD: targeted clobber and GBS branches. |
| `ina_mutation_delta.json` | `ina_mutation_delta.py` | Per-visit SF: targeted clobber and GBS branches. |
| `ina_proxy_access_counts.json` | `ina_proxy_access_counts.py` | Full leaf property access taxonomy (dangerous + non-dangerous). |
| `ina_consistency_report.json` | `ina_consistency_report.py` | Cross-signal consistency summary. |
| `ina_error_log_analysis.json` | `ina_error_log_analysis.py` | Dropped-row attribution and signal impact assessment. |
| `ina_fd_severity.json` | `ina_fd_severity.py` | Kill/expand severity bins for strict FD set. |
| `ina_nondangerous_fd.json` | `ina_nondangerous_fd.py` | FD for non-dangerous property readers. |
| `ina_gbs_sinks.json` | `ina_gbs_sinks.py` | GBS tier classification (dangerous / meaningful / structural). |
| `ina_variable_analysis.json` | `ina_variable_analysis.py` | GBS variable name distribution and selector patterns. |

GBS pre-crawl — written to `results/ina/`:

| File | Script | Contents |
|---|---|---|
| `gbs_variables_summary.json` | `extract_gbs_variables.py` | GBS candidate statistics and top variable names. |

Taint — written to `results/ina/taint/`:

| File | Script | Contents |
|---|---|---|
| `dynamic_taint_summary_{TAINT_SUFFIX}.json` | `ina_taint_analysis.py` | Per-extension taint verdict (CONFIRMED_SINK / DOM_WRITE / READ_ONLY). |
| `taint_overlap_analysis.json` | `taint_overlap.py` | Static vs dynamic taint overlap. |

### Supplementary INA scripts

These do not need to be run as part of the standard pipeline:

| Script | Purpose |
|---|---|
| `clobber_vuln_detector.py` | Static scan for extensions using the window-global coordination pattern that INA SF exploits. Requires `DATASET`. |

---

## Consistency terminology

All analyses use the same three-tier consistency model across 3 visits:

| Term | Meaning |
|---|---|
| **Strict (AND)** | Extension shows the signal in **all 3 visits**. The primary reported number throughout the paper. |
| **Majority (≥2/3)** | Extension shows the signal in at least 2 visits. Reported alongside strict for robustness. |
| **Union (OR)** | Extension shows the signal in at least 1 visit. Upper bound; not used as the primary claim. |

The `pairwise_jaccard` function in both helpers computes all three and reports pairwise Jaccard similarity between visit pairs.

---

## Troubleshooting

**`NameError` or `None` in table names:** A required environment variable was not set. Every suffix variable must be exported before running any script. Check that `DATASET`, `SNA_SUFFIX`, or `INA_SUFFIX` is set in your shell.

**`FileNotFoundError` in consistency_report or error_log_analysis:** The upstream JSON files were not produced. Run the pipeline steps in order, or use `run_all.py`.

**`psycopg2.OperationalError`:** Database credentials are missing or wrong. Verify `~/.env` contains `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS`.

**Coverage data returns 0 rows:** The `scripts` table may not be populated for this dataset. The script classifier returns `undeclared` for unknown scripts, so coverage will still run but WAR/CS/BG breakdown in `sna_component_impact.py` will be inaccurate.
