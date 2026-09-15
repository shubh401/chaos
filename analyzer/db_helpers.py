from collections import defaultdict
from dotenv import load_dotenv

import traceback
import psycopg2
import json
import os

# Load .env from project root
for env_path in ['~/chaos/.env', os.path.expanduser('~/chaos/.env')]:
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
        break

DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DATASET = os.getenv('DATASET')
TEST_TYPE = os.getenv('TEST_TYPE', 'shared')
TABLE_SUFFIX = os.getenv('TABLE_SUFFIX')

# Break vs non-break template identifiers
BREAK_TEMPLATES = {
    'hook_simple_break.html',
    'raider_simple_break.html',
    'mutation_simple_break.html',
    'proto_poison_simple_break.html',
    'event_swallow_simple_break.html',
    'global_preassign_simple_break.html',
}

# Template pairs: (monitor/baseline, break)
TEMPLATE_PAIRS = {
    'hook': ('hook_simple.html', 'hook_simple_break.html'),
    'raider': ('raider_simple.html', 'raider_simple_break.html'),
    'proto_poison': ('proto_poison_simple.html', 'proto_poison_simple_break.html'),
    'event_swallow': ('event_swallow_simple.html', 'event_swallow_simple_break.html'),
    'global_preassign': ('mutation_simple.html', 'global_preassign_simple_break.html'),
}

# Our instrumentation scripts to exclude from coverage analysis
INSTRUMENTATION_SCRIPTS = {
    'mutation.js', 'sparkmd5.js', 'mutation_hashes.js',
    'hook.js', 'hook_break.js', 'raider.js', 'raider_ui.js', 'raider_break.js',
    'lifecycle_tracker.js', 'v2_dispatch.js',
    'proto_poison.js', 'proto_poison_break.js',
    'promise_poison.js', 'promise_poison_break.js',
    'event_swallow.js', 'event_swallow_break.js',
    'eval_poison.js', 'eval_poison_break.js',
    'mo.js', 'hook_ui.js', 'hook_helper.js',
    'raider_simple_ui.js', 'mutation_ui.js', 'clobber_ui.js',
    'ads.js', 'ads_hooked.js', '__cs_hook.js',
}

PREASSIGN_SKIP_VARS = {
    # Instrumentation globals
    '__v2_lifecycle_stage', '__v2_timestamp', '__preassign_dispatch',
    '__preassign_defineProperty', '__dispatchHookData', '__dispatchPollData',
    '__dispatchMutationData', '__dispatchErrorLog', '__exposedErrorLogger',
    '__getCircularReplacer', '__knownHashes', '__fetch', '__stringify',
    '__extractNodeInfo', '__processNodeList', '__processMutationTarget',
    '__processMutationRecord',
    'SparkMD5', '__playwright__binding__', '__pwInitScripts', 'attrs',
    # Browser-native globals (Chrome version skew)
    'IDBRecord', 'Temporal', 'crashReport', 'AudioPlaybackStats',
    'ClipboardChangeEvent', 'CrashReportContext', 'DigitalCredential',
    'SpeechRecognitionPhrase', 'XRCompositionLayer', 'XRProjectionLayer',
    'XRCubeLayer', 'XRCylinderLayer', 'XREquirectLayer', 'XRLayerEvent',
    'XRQuadLayer', 'XRSubImage', 'XRWebGLSubImage', 'XRPlane', 'XRPlaneSet',
    'XRVisibilityMaskChangeEvent', 'AnimationTrigger', 'CSSPseudoElement',
    'HTMLGeolocationElement', 'InterestEvent', 'NavigationPrecommitController',
    'Origin', 'PerformanceTimingConfidence', 'TimelineTrigger',
    'TimelineTriggerRange', 'TimelineTriggerRangeList',
}

# Script type constants
SCRIPT_TYPE_WAR = 'war'
SCRIPT_TYPE_CS = 'cs'
SCRIPT_TYPE_BG = 'bg'
SCRIPT_TYPE_UNDECLARED = 'undeclared'
SCRIPT_TYPE_INJECTED = 'injected'       # blob: or no-src programmatic injection
SCRIPT_TYPE_EXTERNAL_WAR = 'external_war'  # non-extension https:// URLs loaded by extension


def get_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)


def table_name(table_type):
    return f"{TEST_TYPE}_{table_type}_{TABLE_SUFFIX}"


def query_table(table_type, columns="*", where_extra="", params=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = f"SELECT {columns} FROM {table_name(table_type)} WHERE dataset = %s {where_extra};"
    cursor.execute(query, (DATASET,) + (params or ()))
    result = cursor.fetchall()
    conn.close()
    return result


def is_break_url(url):
    return any(bt in url for bt in BREAK_TEMPLATES)


def group_by_extension_and_condition(rows, ext_idx=0, url_idx=1):
    grouped = defaultdict(lambda: defaultdict(list))
    for row in rows:
        ext_id = row[ext_idx]
        condition = 'break' if is_break_url(row[url_idx]) else 'normal'
        grouped[ext_id][condition].append(row)
    return grouped


def extract_v2_fields(json_text):
    try:
        if not json_text or '__v2_client_ts' not in str(json_text):
            return (None, None)
        data = json.loads(json_text) if isinstance(json_text, str) else json_text
        if isinstance(data, dict):
            return (data.get('__v2_client_ts'), data.get('__v2_lifecycle_stage'))
    except:
        pass
    return (None, None)


def serialize_object(data):
    if isinstance(data, set):
        return list(data)
    elif isinstance(data, defaultdict):
        return dict(data)
    elif isinstance(data, float) and (data != data):
        return None
    return data


def save_results(data, filename):
    results_dir = os.path.join(os.path.dirname(__file__), 'results', TABLE_SUFFIX)
    os.makedirs(results_dir, exist_ok=True)
    filepath = os.path.join(results_dir, filename)
    with open(filepath, 'w') as fh:
        json.dump(data, fh, indent=4, default=serialize_object)
    print(f"Saved: {filepath}")


# ---------------------------------------------------------------------------
# Script classification for coverage analysis
# ---------------------------------------------------------------------------

_scripts_cache = None

def load_scripts_table():
    """
    Load the scripts table from ext-prometheus into a lookup structure.
    Returns dict: {extension_id: {relative_path: resolved_type}}

    Paths are normalized: full paths → relative from extension root,
    undeclared short names kept as-is for endswith matching.

    Dual-listing resolution: if a script is listed as both 'cs' and 'war',
    it's classified as 'war' for SNA analysis since the MAIN world is the
    attack surface. The content script entry means it CAN run as CS, but
    the WAR entry means it's also injected into the page — where SNA attacks
    directly affect it.
    """
    global _scripts_cache
    if _scripts_cache is not None:
        return _scripts_cache

    # First pass: collect ALL types per (extension_id, rel_path)
    raw = defaultdict(lambda: defaultdict(set))
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT extension_id, path, type FROM scripts WHERE dataset = %s;",
            (DATASET,)
        )
        for ext_id, path, stype in cursor.fetchall():
            if not path or not ext_id:
                continue
            # Normalize full paths: extract relative path after extension_id/
            if ext_id in path:
                idx = path.index(ext_id)
                rel_path = path[idx + len(ext_id):].lstrip('/')
            else:
                rel_path = path
            raw[ext_id][rel_path].add(stype or SCRIPT_TYPE_UNDECLARED)
        conn.close()
    except:
        traceback.print_exc()

    # Second pass: resolve dual-listings
    # Priority: war > cs > bg > undeclared
    # If a script is both cs+war, classify as war (it runs in MAIN world)
    TYPE_PRIORITY = {SCRIPT_TYPE_WAR: 0, SCRIPT_TYPE_CS: 1, SCRIPT_TYPE_BG: 2, SCRIPT_TYPE_UNDECLARED: 3}

    _scripts_cache = defaultdict(dict)
    for ext_id, paths in raw.items():
        for rel_path, types in paths.items():
            if len(types) == 1:
                _scripts_cache[ext_id][rel_path] = list(types)[0]
            else:
                # Resolve by priority: war wins over cs
                resolved = min(types, key=lambda t: TYPE_PRIORITY.get(t, 99))
                _scripts_cache[ext_id][rel_path] = resolved

    return _scripts_cache


def is_instrumentation_script(script_url):
    """Check if a script URL belongs to our test instrumentation."""
    if not script_url:
        return True
    # Our test server scripts
    if 'testserver.com' in script_url:
        return True
    # Check by filename
    filename = script_url.rsplit('/', 1)[-1].split('?')[0]
    if filename in INSTRUMENTATION_SCRIPTS:
        return True
    return False


def classify_script(script_url, extension_id):
    """
    Classify a script URL from coverage data into a component type.

    Returns one of: 'war', 'cs', 'bg', 'undeclared', 'injected', 'external_war', or None (skip).
    """
    if not script_url:
        return None

    # Skip our instrumentation
    if is_instrumentation_script(script_url):
        return None

    # chrome-extension:// URLs — extension's own scripts
    if script_url.startswith('chrome-extension://'):
        # Strip chrome-extension://{extension_id}/
        # URL format: chrome-extension://abcdef123/path/to/script.js
        stripped = script_url[len('chrome-extension://'):]
        # stripped = "abcdef123/path/to/script.js"
        parts = stripped.split('/', 1)
        if len(parts) < 2:
            return SCRIPT_TYPE_UNDECLARED
        rel_path = parts[1]

        # Look up in scripts table
        scripts_map = load_scripts_table()
        ext_scripts = scripts_map.get(extension_id, {})

        # Direct match
        if rel_path in ext_scripts:
            return ext_scripts[rel_path]

        # endswith match for undeclared/short-name entries
        for known_path, stype in ext_scripts.items():
            if rel_path.endswith(known_path) or known_path.endswith(rel_path):
                return stype

        return SCRIPT_TYPE_UNDECLARED

    # blob: or data: URLs — programmatically injected scripts
    if script_url.startswith('blob:') or script_url.startswith('data:'):
        return SCRIPT_TYPE_INJECTED

    # Empty or about: — dynamically created (e.g., document.appendChild script without src)
    if not script_url or script_url.startswith('about:'):
        return SCRIPT_TYPE_INJECTED

    # Other https:// URLs — third-party scripts injected by the extension
    if script_url.startswith('http://') or script_url.startswith('https://'):
        return SCRIPT_TYPE_EXTERNAL_WAR

    return SCRIPT_TYPE_UNDECLARED


def classify_coverage_scripts(coverage_data, extension_id):
    """
    Classify all scripts in a coverage JSONB entry.

    Args:
        coverage_data: dict mapping script_url → [totalLen, execLen, percentage]
        extension_id: the extension being analyzed

    Returns:
        dict mapping script_type → list of (script_url, totalLen, execLen, percentage)
    """
    classified = defaultdict(list)
    if not coverage_data or not isinstance(coverage_data, dict):
        return classified

    for script_url, metrics in coverage_data.items():
        if not isinstance(metrics, list) or len(metrics) < 3:
            continue
        stype = classify_script(script_url, extension_id)
        if stype is None:
            continue  # skip instrumentation
        classified[stype].append((script_url, metrics[0], metrics[1], metrics[2]))

    return classified


def get_template_from_url(url):
    """Extract template name from a crawl URL."""
    if 'template=' in url:
        return url.split('template=')[1].split('&')[0]
    return url
