from post_processor import log_data
from processor import Processor
from manifest import get_manifest
from files import copy_file
from tqdm import tqdm
from config import *

import argparse
import psycopg2
import re
import sys

# Load seenVars from the hook file at import time.
# Used to filter variable_log data: any name already in seenVars is a browser
# built-in, not an extension global — even if it was captured in variable_log
# before the seenVars snapshot was updated.
def _load_seen_vars() -> set:
    try:
        hook_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'hooks', '__cs_hook.js')
        content = open(hook_path, 'r', encoding='utf-8').read()
        start = content.find('window.seenVars = new Set([')
        end   = content.find(']);', start)
        if start == -1 or end == -1:
            return set()
        return set(re.findall(r'"([^"]+)"', content[start:end]))
    except Exception:
        return set()

_SEEN_VARS = _load_seen_vars()

def start(extension_id) -> Tuple[dict, list, bool, str]:
    """
    Starts the processing of the given extension.

    Args:
        extension_id (str): The ID of the extension to be processed.

    Returns:
        Tuple[dict, list, bool, str]: A tuple containing the invocations, permission bits, dynamic URL flag, and extension ID.
    """
    try:
        extension_instance = Processor(extension_id)
        return extension_instance.start_processing()
    except:
        logging.error(f"[PROCESSOR] Error while instantiating processor for extension - {extension_id} - ", "; ".join(traceback.format_exc().split("\n")))
    return tuple([None]*4)

def initialize_dir() -> None:
    """
    Initializes the necessary directories for processing.
    """
    try:
        os.makedirs(UNZIPPED_DIR, exist_ok=True)
        if os.path.exists(SHARED_NAMESPACE_DIR): shutil.rmtree(SHARED_NAMESPACE_DIR)
        os.makedirs(SHARED_NAMESPACE_DIR)
        if os.path.exists(ISOLATED_NAMESPACE_DIR): shutil.rmtree(ISOLATED_NAMESPACE_DIR)
        os.makedirs(ISOLATED_NAMESPACE_DIR)
    except:
        logging.error("[PROCESSOR] Error while initializing directories - ", "; ".join(traceback.format_exc().split("\n")))

def parse_args() -> Optional[argparse.Namespace]:
    """
    Parses command-line arguments.

    Returns:
        Optional[argparse.Namespace]: The parsed arguments.
    """
    args = None
    try:
        parser = argparse.ArgumentParser(description='E-DoS: Static Filtering of Browser Extensions')
        parser._action_groups.pop()
        optional_args = parser.add_argument_group('Optional arguments')
        optional_args.add_argument("-f", "--full_analysis", help="Perform full static pre-filtering of downloaded extensions.", required=False, default=True)
        optional_args.add_argument("-ho", "--copy_hooks_only", help="Only copy the new/updated hook script to the pre-categorized extensions.", required=False, default=False)
        optional_args.add_argument("-gbs", "--copy_gbs_hooks", help="Generate and inject per-extension GBS trace scripts. Requires GBS_PRE_SUFFIX env var.", required=False, default=False)
        optional_args.add_argument("-rgbs", "--remove_gbs_hooks", help="Remove __gbs_trace.js and manifest entries from all extensions. Run before Crawl 1.", required=False, default=False)
        optional_args.add_argument("-rcs", "--remove_cs_hook", help="Remove __cs_hook.js and its manifest entry from all extensions, for a true hook-free baseline crawl. Run --copy_hooks_only afterward to restore.", required=False, default=False)
        optional_args.add_argument("-p", "--hook_path", help="The path of the hook script to be copied", required=False)
        optional_args.add_argument("-a", "--advanced_tests", help="Run tests for advanced threat models.", required=False)
        args = parser.parse_args()
    except:
        logging.error("[ARCHIVES] Error while parsing arguments - " + "; ".join(traceback.format_exc().split("\n")))
        sys.exit(1)
    finally:
        return args

def copy_hooks_only() -> None:
    """
    Copies the hook script to the pre-categorized extensions.
    """
    try:
        total_extensions = os.listdir(ISOLATED_NAMESPACE_DIR)
        with tqdm (total=len(total_extensions)) as pbar:
            for extension in total_extensions:
                if os.path.exists(os.path.join(ISOLATED_NAMESPACE_DIR, extension, CS_HOOK_NAME)):
                    os.remove(os.path.join(ISOLATED_NAMESPACE_DIR, extension, CS_HOOK_NAME))
                if os.path.exists(os.path.join(ISOLATED_NAMESPACE_DIR, extension, "__cs_hooks.js")):
                    os.remove(os.path.join(ISOLATED_NAMESPACE_DIR, extension, "__cs_hooks.js"))
                copy_file(CS_HOOK_PATH, os.path.join(ISOLATED_NAMESPACE_DIR, extension, CS_HOOK_NAME))
                pbar.update(1)
    except:
        logging.error("[PROCESSOR] Error at copy_hooks_only() - " + "; ".join(traceback.format_exc().split("\n")))

def remove_gbs_hooks() -> None:
    """
    Remove __gbs_trace.js from all extension directories and strip its entry
    from each manifest. Run before Crawl 1 so GBS trace hooks don't fire
    during the FD/SF crawl (they would write stale traces to cs_trace_log).
    After Crawl 1, re-run copy_gbs_hooks to deploy fresh per-extension hooks
    using the richer variable_log data collected during the crawl.

    Run with:
        DATASET=crx_2026-04-14 python static/src/main.py --remove_gbs_hooks
    """
    GBS_NAME = "__gbs_trace.js"
    logging.info(f"[GBS] Removing GBS trace hooks from {ISOLATED_NAMESPACE_DIR}")

    total_extensions = os.listdir(ISOLATED_NAMESPACE_DIR)
    removed_js = 0
    removed_manifest = 0

    with tqdm(total=len(total_extensions), desc="Remove GBS hooks") as pbar:
        for extension_id in total_extensions:
            ext_dir = os.path.join(ISOLATED_NAMESPACE_DIR, extension_id)
            if not os.path.isdir(ext_dir):
                pbar.update(1)
                continue

            # Remove JS file
            gbs_path = os.path.join(ext_dir, GBS_NAME)
            if os.path.exists(gbs_path):
                os.remove(gbs_path)
                removed_js += 1

            # Strip manifest entry
            manifest_path = os.path.join(ext_dir, 'manifest.json')
            try:
                m = get_manifest(manifest_path, extension_id)
                if m:
                    existing = m.get('content_scripts', [])
                    cleaned = [e for e in existing
                               if not (isinstance(e, dict) and GBS_NAME in e.get('js', []))]
                    if len(cleaned) < len(existing):
                        m['content_scripts'] = cleaned
                        with open(manifest_path, 'w', encoding='utf-8-sig') as fh:
                            json.dump(m, fh, indent=4)
                        removed_manifest += 1
            except Exception:
                logging.error(f"[GBS] Error cleaning manifest for {extension_id}: "
                              + "; ".join(traceback.format_exc().split("\n")))
            pbar.update(1)

    logging.info(f"[GBS] Removed {removed_js} JS files, {removed_manifest} manifest entries")
    print(f"GBS hooks removed: {removed_js} JS files, {removed_manifest} manifest entries")


def remove_cs_hook() -> None:
    """
    Remove __cs_hook.js from ALL extension directories and strip its entry from
    each manifest — for a TRUE hook-free baseline crawl (no injected instrumentation
    of any kind; CDP coverage collection is independent of this file, see
    crawler/src/runner/crx_runner.js's Profiler.* calls, so coverage measurement
    still works with the hook fully absent).

    Mirrors remove_gbs_hooks() exactly, targeting CS_HOOK_NAME instead of the GBS
    trace file. Uses the SAME list-membership manifest filter
    (`CS_HOOK_NAME in e.get('js', [])`) as remove_gbs_hooks(), not a full-dict
    equality check — this is the pattern already proven to work reliably in this
    codebase.

    IMPORTANT: this affects ALL extensions in ISOLATED_NAMESPACE_DIR, not a scoped
    subset. Run the hook-free crawl immediately after, then run --copy_hooks_only
    to restore __cs_hook.js before any other crawl depends on it being present.

    Run with:
        DATASET=crx_2026-04-14 python static/src/main.py --remove_cs_hook
    """
    logging.info(f"[CS_HOOK] Removing __cs_hook.js from {ISOLATED_NAMESPACE_DIR}")

    total_extensions = os.listdir(ISOLATED_NAMESPACE_DIR)
    removed_js = 0
    removed_manifest = 0

    with tqdm(total=len(total_extensions), desc="Remove __cs_hook.js") as pbar:
        for extension_id in total_extensions:
            ext_dir = os.path.join(ISOLATED_NAMESPACE_DIR, extension_id)
            if not os.path.isdir(ext_dir):
                pbar.update(1)
                continue

            hook_path = os.path.join(ext_dir, CS_HOOK_NAME)
            if os.path.exists(hook_path):
                os.remove(hook_path)
                removed_js += 1

            manifest_path = os.path.join(ext_dir, 'manifest.json')
            try:
                m = get_manifest(manifest_path, extension_id)
                if m:
                    existing = m.get('content_scripts', [])
                    cleaned = [e for e in existing
                               if not (isinstance(e, dict) and CS_HOOK_NAME in e.get('js', []))]
                    if len(cleaned) < len(existing):
                        m['content_scripts'] = cleaned
                        with open(manifest_path, 'w', encoding='utf-8-sig') as fh:
                            json.dump(m, fh, indent=4)
                        removed_manifest += 1
            except Exception:
                logging.error(f"[CS_HOOK] Error cleaning manifest for {extension_id}: "
                              + "; ".join(traceback.format_exc().split("\n")))
            pbar.update(1)

    logging.info(f"[CS_HOOK] Removed {removed_js} JS files, {removed_manifest} manifest entries")
    print(f"__cs_hook.js removed: {removed_js} JS files, {removed_manifest} manifest entries")


GBS_TRACE_NAME = "__gbs_trace.js"
GBS_TRACE_CONFIG = {
    "matches": ["<all_urls>"],
    "run_at": "document_start",
    "js": [GBS_TRACE_NAME]
}


def _get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, database=DB_NAME,
        user=DB_USER, password=DB_PASS
    )


def _get_gbs_trace_vars(cursor, extension_id: str, pre_suffix: str) -> list:
    """
    Fetch variable names for GBS trace hooks for this extension.

    Queries isolated_variable_log from multiple suffixes in priority order
    and unions the results. This handles two failure modes:

      1. Pre-crawl (mutation_simple) missed the extension: extensions that only
         activate on rich page content produce no variable_log rows on a bare page.
      2. Crawl 1 (honey body) captured them: after Crawl 1, variable_log_2026_v3
         has richer data for content-triggered extensions.

    Suffixes queried (in addition to pre_suffix):
      - GBS_EXTRA_SUFFIX env var (e.g. 2026_v3 after Crawl 1 finishes)

    All results are filtered by _SEEN_VARS (browser built-ins excluded).
    """
    skip = {
        '__v2_lifecycle_stage', '__v2_timestamp', '__preassign_dispatch',
        '__preassign_defineProperty', '__dispatchHookData', '__dispatchPollData',
        '__dispatchMutationData', '__dispatchErrorLog', '__exposedErrorLogger',
        '__getCircularReplacer', '__knownHashes', '__fetch', '__stringify',
        'SparkMD5', '__playwright__binding__', '__pwInitScripts',
    }

    # Build list of suffixes to query — pre_suffix first, then any extras
    suffixes = [pre_suffix]
    extra = os.getenv('GBS_EXTRA_SUFFIX', '')
    if extra and extra != pre_suffix:
        suffixes.append(extra)

    variables = set()
    for suffix in suffixes:
        table = f"isolated_variable_log_{suffix}"
        try:
            cursor.execute(
                f"SELECT variables FROM {table} WHERE extension_id = %s AND dataset = %s;",
                (extension_id, DATASET)
            )
            for (var_data,) in cursor.fetchall():
                if not var_data: continue
                if isinstance(var_data, str):
                    try: var_data = json.loads(var_data)
                    except: continue
                if isinstance(var_data, dict): variables.update(var_data.keys())
                elif isinstance(var_data, list): variables.update(var_data)
        except Exception:
            pass  # table may not exist yet for extra suffix

    return sorted([v for v in variables
                   if v not in skip
                   and v not in _SEEN_VARS
                   and len(v) > 1
                   and not v.startswith('__')])


def _write_gbs_trace_js(ext_dir: str, variables: list) -> None:
    """
    Write __gbs_trace.js to the extension directory.
    Contains transparent defineProperty hooks for the given variable names.
    """
    vars_json = json.dumps(variables)
    script = """// Auto-generated GBS trace script — do not edit manually.
// Installs transparent defineProperty hooks for known CS globals.
// get/set access order is dispatched via __dispatchPollData('cs_trace', ...).
(() => {
  const _defineProperty = Object.defineProperty;
  const _hasOwn = Object.prototype.hasOwnProperty;
  const _traces = {};
  const _values = {};

  function _hook(name) {
    if (_hasOwn.call(window, name)) return;
    try {
      _defineProperty.call(Object, window, name, {
        configurable: true,
        enumerable:   true,
        get() {
          if (!_traces[name]) _traces[name] = [];
          _traces[name].push('get');
          return _values[name];
        },
        set(v) {
          if (!_traces[name]) _traces[name] = [];
          _traces[name].push('set');
          _values[name] = v;
        },
      });
    } catch (_) {}
  }

  const VARS = %s;
  for (const name of VARS) { _hook(name); }

  // Dispatch at three points to catch all run_at values:
  //   document_start CS reads globals sync -> captured at DOMContentLoaded
  //   document_idle/document_end CS reads after DCL -> captured at load/beforeunload
  let _sent = false;
  function _dispatch(stage) {
    if (_sent) return;
    const formatted = {};
    for (const [name, ops] of Object.entries(_traces)) {
      if (ops.length > 0) formatted[name] = ops.join(' - ');
    }
    if (Object.keys(formatted).length > 0 &&
        typeof window.__dispatchPollData === 'function') {
      window.__dispatchPollData('cs_trace', { traces: formatted, stage: 'gbs-trace-' + stage });
      _sent = true;
    }
  }
  document.addEventListener('DOMContentLoaded', function() { _dispatch('dcl'); });
  window.addEventListener('load',               function() { _dispatch('load'); });
  window.addEventListener('beforeunload',       function() { _dispatch('unload'); });
})();
""" % vars_json
    with open(os.path.join(ext_dir, GBS_TRACE_NAME), 'w', encoding='utf-8') as fh:
        fh.write(script)


def _inject_gbs_trace_into_manifest(ext_dir: str, extension_id: str) -> None:
    """
    Add GBS_TRACE_CONFIG as the first content_scripts entry in the manifest.
    Idempotent and self-healing: removes any duplicate __gbs_trace.js entries
    before inserting exactly one at position 0.
    """
    manifest_path = os.path.join(ext_dir, 'manifest.json')
    manifest = get_manifest(manifest_path, extension_id)
    if not manifest: return

    existing_cs = manifest.get('content_scripts', [])

    # Remove ALL existing __gbs_trace.js entries (handles duplicates from prior runs)
    cleaned_cs = [
        entry for entry in existing_cs
        if not (isinstance(entry, dict) and GBS_TRACE_NAME in entry.get('js', []))
    ]

    # Insert exactly one entry at position 0 (before __cs_hook.js)
    manifest['content_scripts'] = [GBS_TRACE_CONFIG] + cleaned_cs

    with open(manifest_path, 'w', encoding='utf-8-sig') as fh:
        json.dump(manifest, fh, indent=4)


def copy_gbs_hooks_only() -> None:
    """
    Generates and deploys per-extension GBS trace scripts.

    For each extension in ISOLATED_NAMESPACE_DIR:
      1. Queries isolated_variable_log_{GBS_PRE_SUFFIX} for known variable names.
      2. Generates a per-extension __gbs_trace.js with transparent defineProperty hooks.
      3. Writes __gbs_trace.js to the extension directory.
      4. Injects {"js": ["__gbs_trace.js"], "run_at": "document_start"} as the FIRST
         content_scripts entry in manifest.json (before __cs_hook.js).

    Run with:
        GBS_PRE_SUFFIX=2026_GBS_PRE DATASET=crx_2026-04-14 python static/src/main.py --copy_gbs_hooks
    """
    pre_suffix = os.getenv('GBS_PRE_SUFFIX', '2026_GBS_PRE')
    logging.info(f"[GBS] Deploying GBS trace hooks. Pre-suffix: {pre_suffix}, Dir: {ISOLATED_NAMESPACE_DIR}")

    try:
        conn   = _get_db_connection()
        cursor = conn.cursor()
    except Exception:
        logging.error("[GBS] DB connection failed: " + "; ".join(traceback.format_exc().split("\n")))
        return

    total_extensions = os.listdir(ISOLATED_NAMESPACE_DIR)
    skipped = 0
    deployed = 0

    with tqdm(total=len(total_extensions), desc="GBS hooks") as pbar:
        for extension_id in total_extensions:
            ext_dir = os.path.join(ISOLATED_NAMESPACE_DIR, extension_id)
            if not os.path.isdir(ext_dir):
                pbar.update(1)
                continue
            try:
                variables = _get_gbs_trace_vars(cursor, extension_id, pre_suffix)
                if not variables:
                    skipped += 1
                    pbar.update(1)
                    continue
                _write_gbs_trace_js(ext_dir, variables)
                _inject_gbs_trace_into_manifest(ext_dir, extension_id)
                deployed += 1
            except Exception:
                logging.error(f"[GBS] Error for {extension_id}: " + "; ".join(traceback.format_exc().split("\n")))
            pbar.update(1)

    conn.close()
    logging.info(f"[GBS] Done. Deployed: {deployed}, Skipped (no vars): {skipped}")
    print(f"GBS hooks deployed: {deployed}  |  Skipped (no variable data): {skipped}")


def full_analysis() -> None:
    """
    Performs a full static pre-filtering analysis of downloaded extensions.
    """
    invocations, scripting, cookies, webRequest = defaultdict(), [], [], []
    dyn_urls, total_extensions = [], []
    try:
        total_extensions = os.listdir(EXTENSION_DIR)
        if ADVANCED_TEST:
            basic_extensions = os.listdir(SHARED_NAMESPACE_DIR.replace("advanced", "basic"))
            basic_extensions.extend(os.listdir(ISOLATED_NAMESPACE_DIR.replace("advanced", "basic")))
            basic_extensions = [ext + ".crx" for ext in basic_extensions]
            total_extensions = list(set(total_extensions) - set(basic_extensions))
            # total_extensions = ['lmnnddcnmjighabhoaedndimldgmbjch', 'bopacbllopffibflgfgamplgcaoabnmj']
        if len(total_extensions):
            logging.info("Static analysis started!")
            initialize_dir()
            
            with mp.Pool(processes=WORKERS, maxtasksperchild=1) as pool:
                for (ext_invocations, perm_bits, is_dynamic_url_found, extension_id) in tqdm(pool.imap_unordered(start, total_extensions), total=len(total_extensions)):
                    if ext_invocations: invocations[extension_id] = ext_invocations
                    if perm_bits[0]: cookies.append(extension_id)
                    if perm_bits[1]: scripting.append(extension_id)
                    if perm_bits[2]: webRequest.append(extension_id)
                    if is_dynamic_url_found: dyn_urls.append(extension_id)
                    continue
            
            log_data(invocations, cookies, scripting, webRequest, dyn_urls)
            logging.info("Analysis completed!")
    except:
        logging.error("[PROCESSOR] Error at full_analysis() - " + "; ".join(traceback.format_exc().split("\n")))

def init() -> None:
    """
    Initializes the processing based on the parsed arguments.
    """
    global CS_HOOK_PATH, ADVANCED_TEST
    try:
        args = parse_args()
        if args.hook_path: CS_HOOK_PATH = args.hook_path.strip()
        if args.advanced_tests: ADVANCED_TEST = bool(args.advanced_tests.strip())
        if args.copy_hooks_only: copy_hooks_only()
        elif args.copy_gbs_hooks: copy_gbs_hooks_only()
        elif args.remove_gbs_hooks: remove_gbs_hooks()
        elif args.remove_cs_hook: remove_cs_hook()
        elif args.full_analysis: full_analysis()
    except:
        logging.error("[PROCESSOR] Error at init() :( - " + "; ".join(traceback.format_exc().split("\n")))

if __name__ == '__main__':
    init()
