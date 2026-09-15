# Static Analysis

Pre-crawl pipeline that processes raw Chrome extension CRX files, selects which extensions qualify for SNA and INA crawls, instruments selected extensions with hook scripts, and populates the DB tables that the server and analyzer depend on.

All scripts run from the **repository root** (`chaos/`), not from inside `static/`.

---

## What it does

1. **Unpacks** each CRX file into a per-extension directory.
2. **Reads the manifest** and discards apps, themes, and extensions without content scripts or relevant permissions.
3. **Classifies** each surviving extension into one or more crawl populations:
   - **Shared namespace** (`SHARED_NAMESPACE_DIR`) — extensions with `scripting`/`tabs` permission + `<all_urls>` host permission, or WAR-injecting extensions. Target for SNA crawls.
   - **Isolated namespace** (`ISOLATED_NAMESPACE_DIR`) — extensions with content scripts matching `<all_urls>`. Target for INA crawls.
4. **Instruments** isolated-namespace extensions: copies `__cs_hook.js` into each extension directory and injects it as the first `content_scripts` entry (`run_at: document_start`, `matches: <all_urls>`).
5. **Patches manifests** (advanced mode) to add the test-server URL to `host_permissions` / `content_scripts.matches` / `web_accessible_resources.matches`.
6. **Logs** invocations and permission bits to JSON files in `static/logs/`.

Separate entry points handle supplementary tasks: DOM query extraction, static taint analysis, GBS hook deployment, and `seenVars` maintenance.

---

## Prerequisites

### Python dependencies

Install all Python dependencies from the repository root using `uv`:

```bash
uv sync
```

### Node.js dependencies

From the repository root:

```bash
npm install
```

This installs `acorn-loose`, `escodegen`, `unzip-crx-3`, and all other packages listed in the root `package.json`.

### Environment file

`config.py` loads `~/chaos/.env`. The file must contain at minimum:

```
DB_HOST=<postgres-host>
DB_NAME=chaos
DB_USER=<your-user>
DB_PASS=<your-password>
DATASET_TS=2026-04-14
```

`DATASET` is derived as `crx_{DATASET_TS}`, so setting `DATASET_TS=2026-04-14` gives `DATASET=crx_2026-04-14`.

### Input data

Raw CRX files must be at `/datasets/crx_{DATASET_TS}/` (one `.crx` file per extension ID).

### Database tables

`dom_query_extractor.py` and `taint_flow_analyzer.py` create their own tables on first run. All other tables (`extension_clobber_payloads`, `extension_vars`, `extension_gbs_vars`) are expected to already exist or to be populated by external tooling before the crawl.

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `DATASET_TS` | yes | Date portion of the dataset name (e.g. `2026-04-14`). `DATASET` = `crx_{DATASET_TS}`. |
| `DATASET` | `dom_query_extractor.py`, `taint_flow_analyzer.py`, `update_seen_vars.py` | Full dataset name (e.g. `crx_2026-04-14`). Used directly in these scripts; not consumed by `config.py`. |
| `DIR_EXTENSION` | no | Subdirectory under the namespace dirs (default: `basic`). Set to `advanced` for advanced-mode runs. |
| `ADVANCED_TEST` | no | `True` to enable advanced-test mode (patches manifest URLs, includes activeTab). Default: `False`. |
| `GBS_PRE_SUFFIX` | `--copy_gbs_hooks` | Table suffix for the GBS pre-crawl `variable_log` (e.g. `2026_GBS_PRE`). |
| `GBS_EXTRA_SUFFIX` | `--copy_gbs_hooks` | Optional additional `variable_log` suffix to union with `GBS_PRE_SUFFIX` (e.g. the INA main crawl suffix). |
| `INA_V2_SUFFIX` | `taint_flow_analyzer.py` | Suffix of the INA proxy_log to use as the dangerous-sink strict set seed (default: `2026_04_23`). |
| `EXTENSION_LIST` | `taint_flow_analyzer.py` | Override path: JSON file with `extension_ids` list. Skips the DB sink-set query. |

All DB credentials (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS`) are read from `~/chaos/.env`.

---

## Directory layout

```
static/
├── package.json               # Node dependencies: acorn-loose, escodegen, unzip-crx-3
├── pyproject.toml
└── src/
    ├── config.py              # All constants: paths, API lists, JS blacklists, logging
    ├── main.py                # Entry point: full_analysis, copy_hooks_only, copy_gbs_hooks, remove_gbs_hooks
    ├── processor.py           # Per-extension analysis: extract → manifest → permissions → scripts → post-process
    ├── post_processor.py      # Copy extension dirs, instrument hooks, patch manifest URLs, log results
    ├── manifest.py            # Manifest parsing: permissions, content scripts, WARs, background scripts
    ├── extractor.py           # CRX unpacking via Node.js unpack_crx.js
    ├── files.py               # File listing, path resolution, directory copying
    ├── utility.py             # grep_invocations, filter_wars, URL helpers
    ├── urls.py                # Host permission URL preprocessing and normalization
    ├── enums.py               # Script (CS/BG/WAR) and Sink type enums
    ├── dom_query_extractor.py # Standalone: extracts DOM query patterns → extension_dom_queries table
    ├── taint_flow_analyzer.py # Standalone: static taint analysis → extension_taint_flows table
    ├── copy_taint_hooks.py    # Standalone: deploys __cs_hook_taint.js to a target extension list
    ├── update_seen_vars.py    # Standalone: updates seenVars in __cs_hook.js from variable_log
    ├── hooks/
    │   ├── __cs_hook.js       # INA content-script hook (injected into every isolated-namespace extension)
    │   └── __cs_hook_taint.js # Taint-instrumented variant of the CS hook
    └── helpers/
        ├── unpack_crx.js          # Node.js: unpacks a .crx file using unzip-crx-3
        ├── js_parser.js           # Node.js: acorn-loose AST parser, shared by other helpers
        ├── dom_query_extractor.js # Node.js: walks AST for DOM query patterns and document access
        ├── taint_flow_extractor.js # Node.js: walks AST for taint flows from DOM sources to sinks
        ├── content_script_definition.json  # Hook injection config: matches=<all_urls>, run_at=document_start
        └── api_permissions.json   # Canonical Chrome extension API permission name list
```

Output directories (created automatically):

```
/datasets/unzipped/crx_{DATASET_TS}/          # Unpacked extension files
/datasets/shared_namespace/{DIR_EXTENSION}/crx_{DATASET_TS}/    # SNA crawl population
/datasets/isolated_namespace/{DIR_EXTENSION}/crx_{DATASET_TS}/  # INA crawl population
static/logs/crx_{DATASET_TS}/{DIR_EXTENSION}/  # Per-run JSON logs
```

---

## Running the full analysis

The full analysis unpacks all CRX files, classifies extensions, copies them to the namespace directories, and instruments INA candidates with the CS hook. Run from the repository root:

```bash
DATASET_TS=2026-04-14 python static/src/main.py
```

Or equivalently (the `--full_analysis` flag is the default):

```bash
DATASET_TS=2026-04-14 python static/src/main.py --full_analysis
```

This processes all `.crx` files in `/datasets/crx_2026-04-14/` in parallel (`WORKERS=1` by default in `config.py` — increase for production runs) and writes:

- `/datasets/unzipped/crx_2026-04-14/<ext_id>/` — unpacked files for every extension
- `/datasets/shared_namespace/basic/crx_2026-04-14/<ext_id>/` — SNA candidates
- `/datasets/isolated_namespace/basic/crx_2026-04-14/<ext_id>/` — INA candidates, with `__cs_hook.js` injected
- `static/logs/crx_2026-04-14/basic/invocations.json` — API invocations found per extension
- `static/logs/crx_2026-04-14/basic/cookies_perm.json` — extensions with `cookies` permission
- `static/logs/crx_2026-04-14/basic/scripting_perm.json` — extensions with `scripting`/`tabs` permission
- `static/logs/crx_2026-04-14/basic/webRequest_perm.json` — extensions with `webRequest` permission
- `static/logs/crx_2026-04-14/basic/war_dyn_urls.json` — extensions with dynamic WAR URLs

### Increasing parallelism

Edit `WORKERS` in `static/src/config.py` before running. A value of 20–40 is typical for a machine with ≥16 cores. The pool uses `maxtasksperchild=1` to prevent memory accumulation across extensions.

---

## Per-extension processing pipeline

Each extension goes through `Processor.start_processing()`:

1. **Extract** (`extractor.py`): calls `node helpers/unpack_crx.js` to unzip the CRX into `UNZIPPED_DIR`.
2. **Read manifest**: parses `manifest.json`. Extensions missing a manifest, or typed as `app` or `theme`, are dropped.
3. **Permissions**: extracts host permissions and API permissions (MV2 and MV3 handled separately). Normalises host permission URLs.
4. **Permission bits**: sets three boolean flags — `has_cookies`, `has_scripting`, `has_webRequest`.
5. **Background scripts**: if `has_scripting`, greps background scripts for `executeScript`, `registerContentScripts`, `cookies.*`, and `webRequest` APIs.
6. **Content scripts**: resolves CS script paths, checks if any match `<all_urls>`, greps for `INTERACTION_APIS` (DOM query methods, storage, messaging, etc.).
7. **Web accessible resources**: resolves WAR paths, greps for `INTERACTION_APIS`, checks if matches include `<all_urls>`.
8. **Post-process** (`post_processor.py`): copies the extension to the appropriate namespace directory based on what qualifies:
   - `scripting` qualification → both `SHARED_NAMESPACE_DIR` and `ISOLATED_NAMESPACE_DIR`; hook injected into isolated copy
   - `cs` qualification → `ISOLATED_NAMESPACE_DIR` only; hook injected
   - `war` qualification → `SHARED_NAMESPACE_DIR` only

### Qualification rules (basic mode)

| Qualification | Condition |
|---|---|
| `scripting` | `has_scripting` AND `<all_urls>` in host permissions |
| `cs` | extension has content scripts AND `<all_urls>` in CS matches |
| `war` | extension has WARs AND (`<all_urls>` in CS matches OR in host permissions) |

In `ADVANCED_TEST=True` mode, the host-permission check is relaxed and any host permission qualifies.

### Hook injection

For every extension placed in `ISOLATED_NAMESPACE_DIR`, `post_processor.inject_into_manifest` inserts:

```json
{
  "matches": ["<all_urls>"],
  "run_at": "document_start",
  "js": ["__cs_hook.js"]
}
```

as the first entry in `content_scripts`, and copies `__cs_hook.js` into the extension directory. This ensures the hook runs before all extension content scripts on every page visit.

---

## Hook management

### Updating the CS hook only

After modifying `__cs_hook.js` (e.g. adding new APIs or updating `seenVars`), re-deploy the hook to all already-categorised isolated-namespace extensions without re-running the full analysis:

```bash
DATASET_TS=2026-04-14 python static/src/main.py --copy_hooks_only
```

This overwrites `__cs_hook.js` in every extension directory under `ISOLATED_NAMESPACE_DIR` without touching manifests or other files.

### Updating `seenVars` in the CS hook

`seenVars` is a Set in `__cs_hook.js` listing known browser built-in globals. Any name in this set is excluded from the `variable_log` — it is treated as a browser API, not an extension global. After a crawl, new browser globals may appear in `variable_log` that were not in `seenVars`. Update the set:

```bash
DATASET_TS=2026_GBS_PRE DATASET=crx_2026-04-14 python static/src/update_seen_vars.py
```

This queries `isolated_variable_log_{DATASET_TS}`, identifies variable names appearing in more than 50% of extensions (frequency threshold for "this is a browser built-in"), and appends any new names to the `seenVars` Set in `hooks/__cs_hook.js`. After updating, redeploy:

```bash
DATASET_TS=2026-04-14 python static/src/main.py --copy_hooks_only
```

---

## GBS hook management

GBS trace hooks (`__gbs_trace.js`) record the get/set access order of window globals in content scripts. They are deployed **between** the GBS pre-crawl and the GBS attack crawl, and **removed** before the INA main crawl.

### Full GBS sequence

**Before INA main crawl (Crawl 1) — remove GBS hooks if present:**

```bash
DATASET_TS=2026-04-14 python static/src/main.py --remove_gbs_hooks
```

Removes `__gbs_trace.js` from every extension directory in `ISOLATED_NAMESPACE_DIR` and strips its `content_scripts` entry from each manifest. Safe to run even if no GBS hooks have been deployed yet.

**After GBS pre-crawl — deploy per-extension GBS hooks:**

```bash
GBS_PRE_SUFFIX=2026_GBS_PRE DATASET_TS=2026-04-14 python static/src/main.py --copy_gbs_hooks
```

For each extension in `ISOLATED_NAMESPACE_DIR`, queries `isolated_variable_log_{GBS_PRE_SUFFIX}` for observed variable names, generates a per-extension `__gbs_trace.js` with transparent `defineProperty` hooks for those variables, and injects it as the **first** `content_scripts` entry (before `__cs_hook.js`, so it runs first at `document_start`).

To also union variable names from a richer crawl (e.g. the INA main crawl whose honey body activates more extensions):

```bash
GBS_PRE_SUFFIX=2026_GBS_PRE GBS_EXTRA_SUFFIX=2026_V3 DATASET_TS=2026-04-14 python static/src/main.py --copy_gbs_hooks
```

Output: prints `GBS hooks deployed: N  |  Skipped (no variable data): M`.

---

## DOM query extraction

Extracts DOM query patterns (selectors, attribute names, property sinks, bundler gadgets) from content scripts and writes them to the `extension_dom_queries` DB table. This table feeds the CodeQL static taint analysis (`analyzer/ina/codeql_pipeline/`).

```bash
DATASET_TS=2026-04-14 python static/src/dom_query_extractor.py
```

**Reads from:** `ISOLATED_NAMESPACE_DIR` (falls back to `UNZIPPED_DIR` if not present).

**Writes to:** `extension_dom_queries` table — created automatically on first run.

Each extension's content scripts are parsed by `helpers/dom_query_extractor.js` (acorn-loose AST walker). The extractor identifies:

| Field | Contents |
|---|---|
| `queries` | `{method, argument, type}` — calls to `getElementById`, `querySelector`, `getAttribute`, etc. with their string arguments |
| `document_access` | Bare `document.X` / `window.X` property accesses (non-standard names only) |
| `property_sinks` | Property writes on query results (e.g. `.src =`, `.innerHTML =`) |
| `bundler_gadgets` | Bundler-injected global access patterns |

---

## Static taint analysis

Runs after the INA dangerous-sink set is established (requires `ina_dangerous_sinks.json` or the `isolated_proxy_log` table from a prior crawl). Identifies content scripts with direct data-flow paths from DOM query sources to network/storage/DOM sinks.

```bash
DATASET=crx_2026-04-14 INA_V2_SUFFIX=2026_V3 python static/src/taint_flow_analyzer.py
```

**Extension set**: by default loads the dangerous-sink strict set from `analyzer/results/ina/{INA_V2_SUFFIX}/ina_dangerous_sinks.json` (falls back to DB query of `isolated_proxy_log_{INA_V2_SUFFIX}`). Override with a JSON file:

```bash
DATASET=crx_2026-04-14 EXTENSION_LIST=crawler/extension_lists/my_list.json python static/src/taint_flow_analyzer.py
```

**What it detects** (via `helpers/taint_flow_extractor.js`):

1. **Source**: `getElementById` / `querySelector` / `querySelectorAll` call whose result is stored in a variable.
2. **Tainted read**: a dangerous property (`.href`, `.src`, `.action`, `.innerHTML`, etc.) read off a source variable.
3. **Sink**: the tainted value flows into `fetch`, `XMLHttpRequest`, `location.href`, `postMessage`, `chrome.*`, `eval`, or a DOM insertion call.

**Writes to:**
- `extension_taint_flows` table — created automatically on first run. Used by `analyzer/ina/taint_overlap.py`.
- `analyzer/results/ina/taint/static_taint_summary.json` — summary statistics.
- `crawler/extension_lists/ina_sink_strict_1556.json` — extension list for the dynamic taint crawl.

---

## Output files

### `static/logs/crx_{DATASET_TS}/{DIR_EXTENSION}/`

| File | Contents |
|---|---|
| `static_analyzer.log` | Per-extension processing log |
| `invocations.json` | `{extension_id: {script_type: [matched_api_strings]}}` for every extension with any API match |
| `cookies_perm.json` | List of extension IDs with `cookies` permission |
| `scripting_perm.json` | List of extension IDs with `scripting` or `tabs` permission |
| `webRequest_perm.json` | List of extension IDs with `webRequest`-family permission |
| `war_dyn_urls.json` | List of extension IDs with dynamic WAR URL patterns |
| `host_hashes.json` | Advanced mode only: SHA-256 hashes of normalised host-permission URL sets, grouped by extension |

### DB tables created or populated

| Table | Populated by | Contents |
|---|---|---|
| `extension_dom_queries` | `dom_query_extractor.py` | Per-extension DOM selector patterns, bare property accesses, property sinks, bundler gadgets |
| `extension_taint_flows` | `taint_flow_analyzer.py` | Per-extension static taint flows from DOM sources to sinks |

The following tables are **read** by the server at crawl time and must be populated by external tooling (static clobber payload generator, not included in this component):

| Table | Read by server endpoint | Contents |
|---|---|---|
| `extension_clobber_payloads` | `clobber_payload` | Per-extension HTML clobber payload injected into the attack page |
| `extension_vars` | `preassign_script` | Per-extension window global names for the SNA global_preassign attack |
| `extension_gbs_vars` | `clobber_gbs_payload`, `gbs_trace_script` | Per-extension GBS variable names, populated by `extract_gbs_variables.py` in the analyzer |

---

## Typical run order (before each crawl)

### SNA and INA main crawl

```bash
# 1. Full static analysis
DATASET_TS=2026-04-14 python static/src/main.py

# 2. DOM query extraction (required for INA bare-access follow-up)
DATASET=crx_2026-04-14 python static/src/dom_query_extractor.py
```

The crawler can then start against `SHARED_NAMESPACE_DIR` (SNA) and `ISOLATED_NAMESPACE_DIR` (INA).

### Before the GBS pre-crawl

```bash
# Remove any stale GBS hooks from a previous run
DATASET_TS=2026-04-14 python static/src/main.py --remove_gbs_hooks
```

### After the GBS pre-crawl, before the GBS attack crawl

```bash
# Optionally update seenVars first
DATASET_TS=2026_GBS_PRE DATASET=crx_2026-04-14 python static/src/update_seen_vars.py

# Redeploy updated CS hook
DATASET_TS=2026-04-14 python static/src/main.py --copy_hooks_only

# Deploy per-extension GBS trace hooks
GBS_PRE_SUFFIX=2026_GBS_PRE DATASET_TS=2026-04-14 python static/src/main.py --copy_gbs_hooks
```

Then run `analyzer/ina/extract_gbs_variables.py` to populate `extension_gbs_vars`, and start the GBS attack crawl.

### After INA main crawl, before taint crawl

```bash
# Static taint analysis on the dangerous-sink strict set
DATASET=crx_2026-04-14 INA_V2_SUFFIX=2026_V3 python static/src/taint_flow_analyzer.py
```

Then start the dynamic taint crawl using the extension list written to `crawler/extension_lists/ina_sink_strict_1556.json`.

---

## Troubleshooting

**`DATASET_TS` is `None` and `DATASET` crashes in `config.py`:** `config.py` is imported at startup and builds `DATASET = f"crx_{DATASET_TS}"`. If `DATASET_TS` is unset, `DATASET` becomes `"crx_None"` and the log/output paths are wrong. Always export `DATASET_TS` before running `main.py`.

**`No module named 'config'`:** Scripts in `static/src/` import each other by name. They must be run with `python static/src/<script>.py` from the repository root, not from inside `static/src/`.

**`node: command not found`:** Node.js is not on `$PATH`. Install it and ensure `npm install` has been run from the repository root.

**`unzip-crx-3: Cannot unpack`:** The CRX file is malformed, an MV3-style ZIP without the CRX header, or a Chrome App. The extractor will log a warning and the extension will be skipped.

**`extension_dom_queries` missing when running the analyzer:** `dom_query_extractor.py` was not run for this dataset. Run it before any bare-access or DOM query analysis in the analyzer.

**`seenVars` is stale — GBS trace picks up browser globals:** Run `update_seen_vars.py` against the current `variable_log` suffix, then redeploy hooks with `--copy_hooks_only` and re-deploy GBS hooks with `--copy_gbs_hooks`.

**Extensions in `ISOLATED_NAMESPACE_DIR` have duplicate `__gbs_trace.js` manifest entries:** `--copy_gbs_hooks` is idempotent — it strips all existing `__gbs_trace.js` entries before inserting one at position 0. Re-running it will self-heal any duplicates.
