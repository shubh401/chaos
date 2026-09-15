VERSION = '2026-04-26-final'
import os
import re
import sys
import json
import traceback
import multiprocessing as mp
from pathlib import Path
from collections import defaultdict

ANALYZER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(ANALYZER_DIR)   # ~/chaos/
STATIC_SRC   = os.path.join(PROJECT_ROOT, 'static', 'src')

sys.path.insert(0, ANALYZER_DIR)
sys.path.insert(0, STATIC_SRC)

import db_helpers as dbh
from db_helpers import (
    DATASET, get_connection,
    SCRIPT_TYPE_CS, SCRIPT_TYPE_BG, SCRIPT_TYPE_WAR, SCRIPT_TYPE_UNDECLARED,
    INSTRUMENTATION_SCRIPTS,
)

# static/src utilities for manifest-based fallback.
# config.py uses relative paths anchored at the project root (~/chaos/), so we
# temporarily chdir there before importing, then restore the original directory.
_STATIC_SRC_AVAILABLE = False
_orig_cwd = os.getcwd()
try:
    os.chdir(PROJECT_ROOT)
    from manifest import get_manifest, get_content_scripts, get_background_scripts
    from files import list_of_files, absolute_file_path_from_dir, script_src_from_html
    _STATIC_SRC_AVAILABLE = True
except Exception:
    pass
finally:
    os.chdir(_orig_cwd)

WORKERS          = int(os.getenv('WORKERS', 40))
MAX_SCRIPT_BYTES = 2 * 1024 * 1024   # skip scripts > 2MB
OUT_PATH = Path(__file__).resolve().parent.parent / 'results' / 'ina' / 'clobber_vuln_scan.json'

# Extension files on the server — full absolute paths are in the scripts table.
# Bare filenames (undeclared scripts without a full path) are resolved relative
# to this base: /datasets/unzipped/{DATASET}/{ext_id}/
EXT_BASE = Path(os.getenv('EXT_DIR', f'/datasets/isolated_namespace/basic/{dbh.DATASET}'))

# Standard browser window properties — not interesting as clobber targets
SAFE_WINDOW_PROPS = {
    'location','history','navigator','document','screen','performance',
    'console','fetch','setTimeout','setInterval','clearTimeout','clearInterval',
    'requestAnimationFrame','cancelAnimationFrame','addEventListener',
    'removeEventListener','dispatchEvent','postMessage','open','close',
    'focus','blur','alert','confirm','prompt','print','stop',
    'getComputedStyle','getSelection','matchMedia','scrollTo','scrollBy',
    'scroll','resizeTo','resizeBy','moveTo','moveBy','atob','btoa',
    'crypto','indexedDB','caches','localStorage','sessionStorage',
    'speechSynthesis','visualViewport','customElements','devicePixelRatio',
    'innerWidth','innerHeight','outerWidth','outerHeight',
    'pageXOffset','pageYOffset','screenX','screenY','scrollX','scrollY',
    'orientation','frameElement','frames','parent','top','opener',
    'self','window','name','status','closed','length','origin',
    'crossOriginIsolated','isSecureContext','trustedTypes','scheduler',
    'onload','onerror','onbeforeunload','onunload','onhashchange','onpopstate',
    'onmessage','onmessageerror','onstorage','onoffline','ononline',
    'onresize','onscroll','chrome','browser',
    'Promise','Symbol','Proxy','Reflect','WeakMap','WeakSet','Map','Set',
    'Object','Array','Function','String','Number','Boolean','Date',
    'RegExp','Error','JSON','Math','parseInt','parseFloat',
    'isNaN','isFinite','eval','undefined','NaN','Infinity','globalThis',
    # Very common generic names unlikely to be coordination globals
    'log','warn','error','info','debug','trace',
    'onerror','onload','onunload','onbeforeunload',
    # Our instrumentation
    '__makeProxy','__isProxy','__logProxyToServer','__dispatchHookData',
    '__dispatchErrorLog','__dispatchPollData','__getCircularReplacer',
    '__resCounter','__counter','seenVars','__pollStorage','__fetch',
    '__stringify','__atob','__btoa','SparkMD5',
}

# ── Patterns ──────────────────────────────────────────────────────────────────

# window.X = <non-null non-falsy> (content script exports)
RE_WIN_WRITE = re.compile(
    r'\bwindow\.([a-zA-Z_$][a-zA-Z0-9_$]*)\s*='
    r'\s*(?!null\b|undefined\b|false\b|0\b|[\'\"]\s*[\'\"])',
    re.MULTILINE
)
# typeof window.X === 'function' guard
RE_TYPEOF_WIN_FN = re.compile(
    r'typeof\s+window\.([a-zA-Z_$][a-zA-Z0-9_$]*)\s*===?\s*[\'"]function[\'"]',
    re.MULTILINE
)
# window.X.method() — reading an exported instance's method
RE_WIN_INSTANCE_READ = re.compile(
    r'\bwindow\.([a-zA-Z_$][a-zA-Z0-9_$]*)\.([a-zA-Z_$][a-zA-Z0-9_$]*)',
    re.MULTILINE
)
# window.X (bare read — for simpler typeof checks and && guards)
RE_WIN_BARE_READ = re.compile(
    r'\bwindow\.([a-zA-Z_$][a-zA-Z0-9_$]*)\b',
    re.MULTILINE
)
# executeScript call — full form (unminified)
RE_EXECUTE_SCRIPT = re.compile(
    r'(?:chrome|browser)\.(?:scripting|tabs)\.executeScript\s*\(',
    re.MULTILINE
)
# executeScript in minified bundles: variable.executeScript( or .executeScript(
# Filtered to MV3-style with func:/function: argument to reduce false positives
RE_EXECUTE_SCRIPT_MINIFIED = re.compile(
    r'\.executeScript\s*\(',
    re.MULTILINE
)
# chrome.tabs.executeScript (MV2 style, also minified as variable.tabs.executeScript)
RE_EXECUTE_SCRIPT_TABS = re.compile(
    r'\.tabs\.executeScript\s*\(',
    re.MULTILINE
)


def _resolve_path(ext_id, raw_path):
    """
    Resolve a scripts-table path to an absolute filesystem path.

    The scripts table may store paths with a stale base directory
    (e.g. /datasets/unzipped/...) that differs from the actual mount
    point (/datasets/isolated_namespace/basic/...). We remap by extracting
    the relative part after {dataset}/{ext_id}/ and re-rooting it under
    EXT_BASE/{ext_id}/.

    Cases:
      Absolute with correct base  → use as-is if it exists, else remap
      Absolute with wrong base    → extract relative suffix, remap under EXT_BASE
      Bare filename               → resolve as EXT_BASE/{ext_id}/{filename}
    """
    if not raw_path:
        return None
    p = Path(raw_path)
    if p.is_absolute():
        # Fast path: file exists at the stored path
        if os.path.exists(str(p)):
            return str(p)
        # Remap: find the relative part after the extension_id directory
        # e.g. /datasets/unzipped/{DATASET}/extid/scripts/foo.js
        #   -> scripts/foo.js -> EXT_BASE/extid/scripts/foo.js
        parts = p.parts
        if ext_id in parts:
            idx      = list(parts).index(ext_id)
            rel_tail = Path(*parts[idx + 1:]) if idx + 1 < len(parts) else Path(p.name)
        else:
            rel_tail = Path(p.name)
        return str(EXT_BASE / ext_id / rel_tail)
    # Bare filename
    return str(EXT_BASE / ext_id / raw_path)


def _scripts_from_manifest(ext_id):
    """
    Fallback: derive typed script paths from the extension manifest using the
    static/src utilities (get_manifest, get_content_scripts, get_background_scripts,
    list_of_files, absolute_file_path_from_dir).

    Falls back to a simple manifest.json reader when static/src is unavailable.
    Returns {role: [abs_path, ...]} or {} if manifest is unreadable.
    """
    source_dir = str(EXT_BASE) + '/'          # static/src expects trailing slash
    manifest_path = os.path.join(source_dir, ext_id, 'manifest.json')

    if not os.path.exists(manifest_path):
        return {}

    scripts = defaultdict(set)

    if _STATIC_SRC_AVAILABLE:
        _cwd = os.getcwd()
        try:
            os.chdir(PROJECT_ROOT)
            manifest = get_manifest(manifest_path, ext_id)
            if not manifest:
                return {}
            file_list = list_of_files(source_dir, ext_id)

            def resolve(rel_path):
                """Resolve rel_path to an existing absolute path."""
                # Try absolute_file_path_from_dir first (handles wildcards etc.)
                abs_path = absolute_file_path_from_dir(
                    file_list, source_dir, ext_id, rel_path, ext_id)
                if abs_path and os.path.exists(abs_path):
                    return abs_path
                # Direct construction: strip leading slash, join with ext dir
                rel_clean = rel_path.lstrip('/')
                direct = os.path.join(source_dir, ext_id, rel_clean)
                if os.path.exists(direct):
                    return direct
                return None

            # Content scripts (isolated world)
            cs_map = get_content_scripts(
                manifest, file_list, 'content_scripts', 'js',
                source_dir, ext_id, extended_war_check=False,
            )
            for rel_path in cs_map:
                abs_path = resolve(rel_path)
                if abs_path:
                    scripts['cs'].add(abs_path)

            # WAR scripts (MAIN world content scripts)
            war_map = get_content_scripts(
                manifest, file_list, 'content_scripts', 'js',
                source_dir, ext_id, extended_war_check=True,
            )
            for rel_path in war_map:
                abs_path = resolve(rel_path)
                if abs_path:
                    scripts['war'].add(abs_path)

            # Background / service worker scripts
            for rel_path in get_background_scripts(manifest, ext_id):
                abs_path = resolve(rel_path)
                if abs_path and abs_path.endswith('.js'):
                    scripts['bg'].add(abs_path)
                elif abs_path and abs_path.endswith('.html'):
                    # HTML popup — extract script tags
                    for src in script_src_from_html(abs_path, ext_id):
                        abs_src = resolve(src)
                        if abs_src:
                            scripts['bg'].add(abs_src)
                elif not abs_path:
                    # Try treating rel_path as HTML popup directly
                    html_path = os.path.join(source_dir, ext_id, rel_path.lstrip('/'))
                    if os.path.exists(html_path) and html_path.endswith('.html'):
                        for src in script_src_from_html(html_path, ext_id):
                            abs_src = resolve(src)
                            if abs_src:
                                scripts['bg'].add(abs_src)
        except Exception:
            traceback.print_exc()
        finally:
            os.chdir(_cwd)
    else:
        # Minimal fallback without static/src
        try:
            with open(manifest_path, errors='replace') as f:
                manifest = json.load(f)
        except Exception:
            return {}
        ext_dir = Path(source_dir) / ext_id
        mv = manifest.get('manifest_version', 2)
        for cs_entry in manifest.get('content_scripts', []):
            for js in cs_entry.get('js', []):
                p = ext_dir / js
                if p.exists(): scripts['cs'].add(str(p))
        bg = manifest.get('background', {})
        for key in ('service_worker', 'page') + (('scripts',) if mv == 2 else ()):
            val = bg.get(key)
            if isinstance(val, str):
                p = ext_dir / val
                if p.exists(): scripts['bg'].add(str(p))
            elif isinstance(val, list):
                for s in val:
                    p = ext_dir / s
                    if p.exists(): scripts['bg'].add(str(p))

    return {role: sorted(paths) for role, paths in scripts.items() if paths}


def _load_scripts_by_type(ext_ids=None):
    """
    Query the scripts table and return:
      {ext_id: {'cs': [path,...], 'bg': [path,...], 'war': [path,...]}}

    For extensions not in the scripts table (sparse coverage), fall back to
    parsing the manifest directly from EXT_BASE/{ext_id}/manifest.json.

    ext_ids: optional set of extension IDs to restrict the query (for targeted scans).
             If None, loads all extensions in the dataset.
    """
    import time
    print(f"Loading scripts table for dataset={DATASET}  base={EXT_BASE}...")
    sys.stdout.flush()
    t0 = time.time()
    conn = get_connection()
    cur  = conn.cursor()

    # Diagnose available datasets on first run
    cur.execute("SELECT DISTINCT dataset FROM scripts ORDER BY dataset;")
    available = [r[0] for r in cur.fetchall()]
    print(f"  Datasets in scripts table: {available}")
    sys.stdout.flush()
    if DATASET not in available:
        print(f"  WARNING: '{DATASET}' not found — check DATASET env var.")
        sys.stdout.flush()

    print(f"  Querying scripts table... ", end='', flush=True)
    if ext_ids:
        placeholders = ','.join(['%s'] * len(ext_ids))
        cur.execute(
            f"SELECT extension_id, path, type FROM scripts "
            f"WHERE dataset = %s AND extension_id IN ({placeholders});",
            (DATASET, *ext_ids)
        )
    else:
        cur.execute(
            "SELECT extension_id, path, type FROM scripts WHERE dataset = %s;",
            (DATASET,)
        )
    print(f"query done ({time.time()-t0:.1f}s), fetching rows... ", end='', flush=True)
    rows = cur.fetchall()
    conn.close()
    print(f"{len(rows):,} rows ({time.time()-t0:.1f}s total)")

    raw = defaultdict(lambda: defaultdict(set))
    for ext_id, path, stype in rows:
        if not ext_id or not path:
            continue
        stype    = stype or SCRIPT_TYPE_UNDECLARED
        resolved = _resolve_path(ext_id, path)
        if not resolved:
            continue
        if stype in (SCRIPT_TYPE_CS, SCRIPT_TYPE_UNDECLARED):
            raw[ext_id]['cs'].add(resolved)
        elif stype == SCRIPT_TYPE_BG:
            raw[ext_id]['bg'].add(resolved)
        elif stype == SCRIPT_TYPE_WAR:
            raw[ext_id]['war'].add(resolved)

    result = {}
    for ext_id, roles in raw.items():
        result[ext_id] = {role: sorted(paths) for role, paths in roles.items()}

    # Merge manifest fallback for all resolved extensions:
    # The scripts table may be incomplete (e.g. lists AI helper files as CS but
    # misses content.js). Always merge manifest-derived paths on top of DB paths
    # so we don't miss the primary CS file that exports coordination globals.
    # For extensions entirely absent from DB, manifest is the only source.
    target_set = set(ext_ids) if ext_ids else set(result.keys())
    missing_from_db = (set(ext_ids) - set(result.keys())) if ext_ids else set()

    n_target = len(target_set)
    print(f"  Merging manifest data for {n_target:,} extensions...", flush=True)
    t_merge = time.time()
    for n_done, ext_id in enumerate(sorted(target_set)):
        if n_done > 0 and n_done % 10000 == 0:
            print(f"    {n_done:,}/{n_target:,} merged ({time.time()-t_merge:.0f}s)...", flush=True)
        fb = _scripts_from_manifest(ext_id)
        if not fb:
            continue
        if ext_id not in result:
            result[ext_id] = fb
        else:
            # Merge: add manifest paths not already in DB result
            for role, paths in fb.items():
                existing = set(result[ext_id].get(role, []))
                new_paths = [p for p in paths if p not in existing]
                if new_paths:
                    result[ext_id][role] = sorted(existing | set(new_paths))
    print(f"  Manifest merge done ({time.time()-t_merge:.1f}s)", flush=True)

    has_cs_and_bg = sum(1 for v in result.values() if 'cs' in v and 'bg' in v)
    print(f"  {len(result):,} extensions with any scripts")
    print(f"  {has_cs_and_bg:,} with both CS and BG scripts (primary scan targets)")
    return result


def _read_script(path):
    try:
        if not os.path.exists(path):
            return None
        if os.path.getsize(path) > MAX_SCRIPT_BYTES:
            return None
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception:
        return None


def _find_and_read(path):
    """
    Read a script file. If the path doesn't exist, try to find a file with
    the same basename anywhere under EXT_BASE/{ext_id}/.
    Handles the case where the DB stores a bare filename without a full path.
    """
    src = _read_script(path)
    if src is not None:
        return src
    # Try to find by basename under the extension directory
    basename = os.path.basename(path)
    if not basename or not basename.endswith('.js'):
        return None
    # Extract ext_id from path: EXT_BASE / ext_id / ...
    try:
        rel = os.path.relpath(path, str(EXT_BASE))
        ext_id = rel.split(os.sep)[0]
        ext_dir = EXT_BASE / ext_id
        for root, _, files in os.walk(str(ext_dir)):
            if basename in files:
                candidate = os.path.join(root, basename)
                src = _read_script(candidate)
                if src is not None:
                    return src
    except Exception:
        pass
    return None


def _extract_window_writes(src):
    """Return set of non-safe names written to window."""
    found = set()
    for m in RE_WIN_WRITE.finditer(src):
        name = m.group(1)
        if name not in SAFE_WINDOW_PROPS:
            found.add(name)
    return found


def _extract_window_reads(src):
    """Return (reads, typeof_guards, instance_reads) sets from a script."""
    reads   = set()
    guards  = set()
    methods = set()
    for m in RE_TYPEOF_WIN_FN.finditer(src):
        name = m.group(1)
        if name not in SAFE_WINDOW_PROPS:
            guards.add(name)
            reads.add(name)
    for m in RE_WIN_INSTANCE_READ.finditer(src):
        name = m.group(1)
        if name not in SAFE_WINDOW_PROPS:
            methods.add(f'{name}.{m.group(2)}')
            reads.add(name)
    # Also plain window.X references (excluding writes)
    for m in RE_WIN_BARE_READ.finditer(src):
        name = m.group(1)
        if name not in SAFE_WINDOW_PROPS:
            reads.add(name)
    return reads, guards, methods


def _is_instrumentation(path):
    return os.path.basename(path) in INSTRUMENTATION_SCRIPTS


def analyse_extension(args):
    ext_id, script_map = args
    cs_paths  = [p for p in script_map.get('cs', []) + script_map.get('war', [])
                 if not _is_instrumentation(p)]
    bg_paths  = [p for p in script_map.get('bg', []) + script_map.get('war', [])
                 if not _is_instrumentation(p)]


    # ── A. CS scripts: find window.X writes ───────────────────────────────────
    cs_writes       = set()
    cs_typeof_guards = set()

    for path in cs_paths:
        src = _find_and_read(path)
        if not src:
            continue
        cs_writes |= _extract_window_writes(src)
        _, guards, _ = _extract_window_reads(src)
        cs_typeof_guards |= guards

    # ── B. BG scripts: find executeScript + window.X reads ────────────────────
    bg_has_execute_script = False
    bg_reads        = set()
    bg_writes       = set()
    bg_typeof_guards = set()
    bg_methods      = set()

    for path in bg_paths:
        src = _find_and_read(path)
        if not src:
            continue
        if (RE_EXECUTE_SCRIPT.search(src)
                or RE_EXECUTE_SCRIPT_TABS.search(src)
                or RE_EXECUTE_SCRIPT_MINIFIED.search(src)):
            bg_has_execute_script = True
        reads, guards, methods = _extract_window_reads(src)
        bg_reads        |= {n for n in reads   if n not in SAFE_WINDOW_PROPS}
        bg_typeof_guards |= {n for n in guards if n not in SAFE_WINDOW_PROPS}
        bg_methods      |= methods
        # Track what BG writes to window — exclude these from cross-reference
        # to avoid flagging BG-internal globals (e.g. window.PreloadManager in bg.js)
        bg_writes |= _extract_window_writes(src)

    # ── C. Cross-reference ─────────────────────────────────────────────────────
    # exported_and_read: CS wrote it AND BG reads it.
    # We do NOT exclude BG-written globals here: BG fallback code often writes
    # window.X = new MyClass() as a recovery path when it can't find the CS
    # instance — that write is itself evidence of the coordination pattern.
    exported_and_read = cs_writes & bg_reads
    guarded           = exported_and_read & (bg_typeof_guards | cs_typeof_guards)

    # ── Scoring ────────────────────────────────────────────────────────────────
    # Quality filter: for HIGH/MEDIUM, require at least one exported global to
    # appear in typeof_guards OR instance_methods — these are the strongest
    # evidence that the BG is specifically checking the CS-exported type.
    # This eliminates false positives where BG and CS both happen to use the
    # same common window.X name (e.g. window.log, window.PreloadManager) without
    # actually coordinating through it.
    high_quality = exported_and_read & (guarded | {m.split('.')[0] for m in bg_methods})

    if high_quality and guarded:
        risk = 'HIGH'    # typeof guard is the clearest minification-resistant signal
    elif high_quality and bg_has_execute_script:
        risk = 'HIGH'    # explicit executeScript + high-quality cross-read
    elif high_quality:
        risk = 'MEDIUM'  # high-quality cross-read; executeScript likely in minified bundle
    elif exported_and_read and bg_has_execute_script:
        risk = 'LOW'     # cross-read but weaker evidence + executeScript present
    elif cs_writes and bg_has_execute_script:
        risk = 'LOW'     # executeScript present but no confirmed cross-read
    elif cs_writes:
        risk = 'INFO'    # globals exported; no BG reads or executeScript detected
    else:
        return ext_id, None

    return ext_id, {
        'ext_id':               ext_id,
        'risk':                 risk,
        'cs_window_writes':     sorted(cs_writes),
        'bg_window_reads':      sorted(bg_reads),
        'exported_and_read':    sorted(exported_and_read),
        'high_quality':         sorted(high_quality),
        'typeof_guards':        sorted(guarded),
        'has_execute_script':   bg_has_execute_script,
        'instance_methods':     sorted(bg_methods),
        'n_cs_scripts':         len(cs_paths),
        'n_bg_scripts':         len(bg_paths),
        'cs_paths':             cs_paths,
        'bg_paths':             bg_paths,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--ids', nargs='*', default=None,
                        help='Specific extension IDs to scan (default: all)')
    args = parser.parse_args()

    target_ids = set(args.ids) if args.ids else None
    script_map = _load_scripts_by_type(ext_ids=target_ids)

    # For full scan: also sweep extensions present on disk but absent from scripts table
    if not target_ids and EXT_BASE.exists():
        disk_exts = set(os.listdir(EXT_BASE))
        db_exts   = set(script_map.keys())
        uncovered = disk_exts - db_exts
        if uncovered:
            print(f"  {len(uncovered):,} extensions on disk not in scripts table — manifest fallback...", flush=True)
            import time as _t
            t_disk = _t.time()
            added = 0
            for n_done, ext_id in enumerate(sorted(uncovered)):
                if n_done > 0 and n_done % 5000 == 0:
                    print(f"    disk fallback: {n_done:,}/{len(uncovered):,} ({_t.time()-t_disk:.0f}s)...", flush=True)
                fb = _scripts_from_manifest(ext_id)
                if fb and 'cs' in fb:
                    script_map[ext_id] = fb
                    added += 1
            print(f"  Disk fallback done: added {added:,} extensions ({_t.time()-t_disk:.1f}s)")

    candidates = [(ext_id, sm) for ext_id, sm in script_map.items() if 'cs' in sm]
    if target_ids:
        missing = target_ids - set(script_map.keys())
        if missing:
            print(f"  WARNING: {len(missing)} requested IDs not resolved: {sorted(missing)}")
    print(f"\nScanning {len(candidates):,} extensions with content scripts...  [version={VERSION}]", flush=True)
    results = {}
    verbose = len(candidates) <= 20   # print per-extension detail for small scans
    with mp.Pool(processes=WORKERS, maxtasksperchild=10) as pool:
        for i, (ext_id, result) in enumerate(
                pool.imap_unordered(analyse_extension, candidates, chunksize=100)):
            if i % 2000 == 0:
                high_med = sum(1 for r in results.values() if r['risk'] in ('HIGH','MEDIUM'))
                print(f"  {i:,}/{len(candidates):,} — HIGH/MEDIUM: {high_med:,}")
            if result:
                results[ext_id] = result
                if verbose:
                    print(f"\n  {ext_id}  risk={result['risk']}")
                    cs_names = [Path(p).name for p in result['cs_paths']]
                    print(f"    cs_paths ({len(cs_names)}): {cs_names[:6]}{'...' if len(cs_names)>6 else ''}")
                    print(f"    bg_paths : {[Path(p).name for p in result['bg_paths'][:4]]}")
                    # Show high_quality globals first in cs_writes so they're visible in truncation
                    hq = set(result.get('high_quality', []))
                    cs_w = sorted(result['cs_window_writes'], key=lambda x: (x not in hq, x))
                    print(f"    cs_writes: {cs_w[:8]}{'...' if len(cs_w)>8 else ''}")
                    print(f"    bg_reads : {result['bg_window_reads'][:8]}")
                    print(f"    high_quality   : {result.get('high_quality', '?')}")
                    print(f"    exported+read  : {result['exported_and_read']}")
                    print(f"    typeof_guards  : {result['typeof_guards']}")
                    print(f"    instance_methods: {result['instance_methods'][:4]}")
                    print(f"    has_executeScript: {result['has_execute_script']}")
            elif verbose:
                print(f"\n  {ext_id}  NO SIGNAL (no cs_writes or below threshold)")

    # ── Summary ────────────────────────────────────────────────────────────────
    from collections import Counter
    by_risk = Counter(r['risk'] for r in results.values())

    print(f'\n{"="*60}')
    print(f'  CLOBBER VULNERABILITY SCAN — {DATASET}')
    print(f'{"="*60}')
    print(f'  Extensions scanned:   {len(candidates):,}')
    for risk in ('HIGH', 'MEDIUM', 'LOW', 'INFO'):
        print(f'  {risk:<8}: {by_risk[risk]:,}')

    # Cross-reference with known SF strict set
    try:
        v2_path = Path(__file__).resolve().parent.parent / \
                  'results' / 'ina' / os.getenv('INA_SUFFIX', '') / 'ina_mutation_delta.json'
        sf_strict = set(json.load(open(v2_path)).get('silent_failure_strict_set', []))
        sf_hits   = {e: results[e] for e in sf_strict if e in results}
        print(f'\n  Known SF strict ({len(sf_strict)}) found in scan: {len(sf_hits)}')
        for ext_id, r in sorted(sf_hits.items(), key=lambda x: x[1]['risk']):
            print(f'    {ext_id}  risk={r["risk"]}  high_quality={r.get("high_quality", r["exported_and_read"])[:4]}')
        sf_missed = sf_strict - set(results.keys())
        if sf_missed:
            print(f'  SF not in scan — retrying with manifest fallback: {len(sf_missed)}')
            retry_results = {}
            for ext_id in sorted(sf_missed):
                fb = _scripts_from_manifest(ext_id)
                if not fb or 'cs' not in fb:
                    print(f'    {ext_id}: no scripts found via manifest fallback')
                    continue
                _, r = analyse_extension((ext_id, fb))
                if r:
                    retry_results[ext_id] = r
                    results[ext_id] = r
                    print(f'    {ext_id}: risk={r["risk"]}  exported+read={r["exported_and_read"][:4]}')
                else:
                    print(f'    {ext_id}: no signal detected via manifest fallback')
            if retry_results:
                by_risk.update(Counter(r['risk'] for r in retry_results.values()))
                print(f'  Retry added: {len(retry_results)} results')
    except Exception:
        traceback.print_exc()

    # Top HIGH risk — sort and display by high_quality (the filtered set)
    high = sorted([r for r in results.values() if r['risk'] == 'HIGH'],
                  key=lambda x: -len(x.get('high_quality', x['exported_and_read'])))
    print(f'\n  Top 20 HIGH risk (by high-quality coordination globals):')
    print(f'  {"Extension":<35} {"high_quality":<45} {"guards"}')
    for r in high[:20]:
        hq = r.get('high_quality', r['exported_and_read'])
        print(f'  {r["ext_id"]:<35} {str(hq[:4]):<45} {r["typeof_guards"][:3]}')

    # Save
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output = {
        'dataset':       DATASET,
        'total_scanned': len(candidates),
        'summary':       dict(by_risk),
        'results':       results,
    }
    with open(OUT_PATH, 'w') as f:
        json.dump(output, f, indent=2)
    print(f'\nSaved: {OUT_PATH}')


if __name__ == '__main__':
    main()
