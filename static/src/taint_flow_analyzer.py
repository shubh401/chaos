"""
taint_flow_analyzer.py — Static taint flow analysis for INA dangerous sink extensions.

Runs taint_flow_extractor.js on each content script of every extension in the
v2 dangerous sink strict set (1,556 extensions). Looks for direct flows from
DOM query results through dangerous properties to output sinks.

Outputs:
  - DB table extension_taint_flows (extension_id, dataset, flows JSONB)
  - crawler/extension_lists/ina_sink_strict_1556.json  (for dynamic taint crawl)
  - results/ina/taint/static_taint_summary.json

Run from /root/ext-dos/:
    DATASET=crx_2026-04-14 python static/src/taint_flow_analyzer.py

Optional — limit to a subset for testing:
    DATASET=crx_2026-04-14 LIMIT=50 python static/src/taint_flow_analyzer.py
"""
import os, sys, json, subprocess, traceback
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm
import multiprocessing as mp
import psycopg2
from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parents[2]
HELPERS_DIR = Path(__file__).resolve().parent / 'helpers'
EXTRACTOR   = str(HELPERS_DIR / 'taint_flow_extractor.js')
LIST_DIR    = BASE_DIR / 'crawler' / 'extension_lists'
OUT_DIR     = BASE_DIR / 'analyzer' / 'results' / 'ina' / 'taint'
LIST_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Manifest helpers — must be importable from static/src/
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from manifest import get_manifest
    from manifest import get_content_scripts as _manifest_get_cs
    from files import list_of_files
    _MANIFEST_OK = True
except ImportError as _e:
    print(f'WARNING: could not import manifest helpers: {_e}')
    _MANIFEST_OK = False

# ── Config ────────────────────────────────────────────────────────────────────
for _env in [str(BASE_DIR / '.env'), '/root/ext-dos/.env']:
    if os.path.exists(_env):
        load_dotenv(dotenv_path=_env)
        break

DATASET  = os.getenv('DATASET', 'crx_2026-04-14')
DB_HOST  = os.getenv('DB_HOST', '127.0.0.1')
DB_NAME  = os.getenv('DB_NAME', 'dos_extensions')
DB_USER  = os.getenv('DB_USER', 'dos_extensions')
DB_PASS  = os.getenv('DB_PASS', '')
V2_SUFFIX = os.getenv('INA_V2_SUFFIX', '2026_04_23')
WORKERS  = int(os.getenv('WORKERS', '20'))
LIMIT    = int(os.getenv('LIMIT', '0'))   # 0 = no limit
EXTENSION_LIST = os.getenv('EXTENSION_LIST', '')  # override extension list JSON path

NS_DIR = f'/datasets/isolated_namespace/basic/{DATASET}/'

WORKERS_NODE = 30   # parallel Node.js processes


def get_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME,
                            user=DB_USER, password=DB_PASS)


def load_sink_strict_set() -> set:
    """
    Load the v2 dangerous sink strict set (1,556).
    Tries local results JSON first (authoritative, already computed),
    falls back to DB query if not found.
    """
    # Primary: load from pre-computed results file
    results_path = (
        BASE_DIR / 'analyzer' / 'results' / 'ina' / 'v2' / V2_SUFFIX
        / 'ina_v2_dangerous_sinks.json'
    )
    if results_path.exists():
        try:
            data = json.loads(results_path.read_text())
            pv = data.get('per_visit_per_extension', {})
            if pv:
                strict = (
                    set(pv.get('1', {}).keys()) &
                    set(pv.get('2', {}).keys()) &
                    set(pv.get('3', {}).keys())
                )
                print(f"  v2 dangerous sink strict set (from local results): {len(strict):,}")
                return strict
        except Exception as e:
            print(f"  WARNING: could not read local results: {e}")

    # Fallback: query DB
    print(f"  Local results not found — querying DB...")
    conn = get_connection()
    cur  = conn.cursor()
    tbl  = f'isolated_proxy_log_{V2_SUFFIX}'
    try:
        cur.execute(
            f"SELECT DISTINCT extension_id, visit FROM {tbl} "
            f"WHERE dataset=%s AND proxy_data IS NOT NULL AND proxy_data::text != 'null';",
            (DATASET,)
        )
        rows = cur.fetchall()
    except Exception as e:
        print(f"  WARNING: could not query {tbl}: {e}")
        rows = []
    finally:
        conn.close()

    visits = defaultdict(set)
    for ext_id, visit in rows:
        visits[int(visit)].add(ext_id)
    if not visits:
        return set()
    strict = set.intersection(*visits.values())
    print(f"  v2 dangerous sink strict set (from DB {tbl}): {len(strict):,}")
    return strict


def get_content_scripts(ext_id: str) -> list:
    """Return absolute paths of content script JS files for this extension."""
    if not _MANIFEST_OK:
        return []
    ext_dir = os.path.join(NS_DIR, ext_id)
    if not os.path.isdir(ext_dir):
        return []
    manifest_path = os.path.join(ext_dir, 'manifest.json')
    if not os.path.exists(manifest_path):
        return []
    try:
        m  = get_manifest(manifest_path, ext_id)
        if not m:
            return []
        fl = list_of_files(ext_dir, ext_id)
        scripts = _manifest_get_cs(m, fl, 'content_scripts', 'js', ext_id, ext_dir)
        if not scripts:
            return []
        skip = {'__cs_hook.js', '__gbs_trace.js', '__cs_hook_taint.js'}
        return [
            os.path.join(ext_dir, name)
            for name in scripts.keys()
            if name not in skip and os.path.exists(os.path.join(ext_dir, name))
        ]
    except Exception:
        return []


def run_extractor(script_path: str) -> dict:
    """Run taint_flow_extractor.js on one script, return parsed result."""
    empty = {'flows': [], 'sources': 0, 'tainted_reads': 0}
    try:
        proc = subprocess.run(
            ['node', EXTRACTOR, script_path],
            capture_output=True, text=True, timeout=30
        )
        if proc.stdout.strip():
            return json.loads(proc.stdout.strip())
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass
    return empty


def process_extension(ext_id: str) -> tuple:
    """Analyze all content scripts for one extension. Returns (ext_id, merged_result)."""
    scripts = get_content_scripts(ext_id)
    merged = {'flows': [], 'sources': 0, 'tainted_reads': 0, 'scripts_analyzed': len(scripts)}
    for script_path in scripts:
        r = run_extractor(script_path)
        merged['flows'].extend(r.get('flows', []))
        merged['sources']       += r.get('sources', 0)
        merged['tainted_reads'] += r.get('tainted_reads', 0)
    # Deduplicate flows by (type, sink, line)
    seen = set()
    unique_flows = []
    for f in merged['flows']:
        key = (f.get('type'), f.get('sink'), f.get('line'))
        if key not in seen:
            seen.add(key)
            unique_flows.append(f)
    merged['flows'] = unique_flows
    return ext_id, merged


def create_table():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS extension_taint_flows (
            id           SERIAL PRIMARY KEY,
            extension_id VARCHAR(256),
            dataset      VARCHAR(32) NOT NULL,
            flows        JSONB,
            sources      INT DEFAULT 0,
            tainted_reads INT DEFAULT 0,
            scripts_analyzed INT DEFAULT 0,
            tstamp       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS etf_ext_dat
        ON extension_taint_flows(extension_id, dataset);
    """)
    conn.commit()
    conn.close()


def insert_results(ext_id: str, data: dict):
    if not data.get('flows') and data.get('sources', 0) == 0:
        return
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO extension_taint_flows
                (extension_id, dataset, flows, sources, tainted_reads, scripts_analyzed)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (extension_id, dataset) DO UPDATE SET
                flows=EXCLUDED.flows, sources=EXCLUDED.sources,
                tainted_reads=EXCLUDED.tainted_reads,
                scripts_analyzed=EXCLUDED.scripts_analyzed,
                tstamp=CURRENT_TIMESTAMP;
        """, (
            ext_id, DATASET,
            json.dumps(data['flows']),
            data['sources'], data['tainted_reads'], data['scripts_analyzed']
        ))
        conn.commit()
        conn.close()
    except Exception:
        traceback.print_exc()


def main():
    print(f"Static taint flow analysis — dataset={DATASET}")
    print(f"  Extractor: {EXTRACTOR}")
    print()

    # ── Load extension set ────────────────────────────────────────────────────
    if EXTENSION_LIST:
        print(f"Loading extension list from {EXTENSION_LIST} ...")
        try:
            data = json.loads(Path(EXTENSION_LIST).read_text())
            sink_exts = set(data['extension_ids'])
            print(f"  Loaded {len(sink_exts):,} extensions from override list")
        except Exception as e:
            print(f"ERROR: Could not read EXTENSION_LIST={EXTENSION_LIST}: {e}")
            sys.exit(1)
    else:
        print("Loading v2 dangerous sink strict set...")
        sink_exts = load_sink_strict_set()
        if not sink_exts:
            print("ERROR: Could not load sink strict set from DB. Check V2_SUFFIX env var.")
            sys.exit(1)

    # Filter to extensions on disk
    on_disk = {e for e in sink_exts if os.path.isdir(os.path.join(NS_DIR, e))}
    missing = sink_exts - on_disk
    if missing:
        print(f"  WARNING: {len(missing)} extensions not on disk — skipping")
    print(f"  On disk: {len(on_disk):,}")

    ext_list = sorted(on_disk)
    if LIMIT:
        ext_list = ext_list[:LIMIT]
        print(f"  Limited to {LIMIT} extensions (LIMIT env var)")
    print()

    # ── Sanity check: verify manifest parsing works on first extension ────────
    sample_id = ext_list[0] if ext_list else None
    if sample_id:
        scripts = get_content_scripts(sample_id)
        if not scripts:
            print(f"WARNING: get_content_scripts returned empty for {sample_id}")
            print(f"  NS_DIR:        {NS_DIR}")
            print(f"  _MANIFEST_OK:  {_MANIFEST_OK}")
            ext_dir = os.path.join(NS_DIR, sample_id)
            print(f"  ext_dir exists:{os.path.isdir(ext_dir)}")
            mpath = os.path.join(ext_dir, 'manifest.json')
            print(f"  manifest:      {os.path.exists(mpath)}")
            if os.path.exists(mpath):
                m = json.load(open(mpath))
                cs = m.get('content_scripts', [])
                print(f"  content_scripts entries: {len(cs)}")
                if cs:
                    print(f"  first entry: {cs[0]}")
            print()
        else:
            print(f"Sanity check OK: {sample_id} → {len(scripts)} content script(s)")
            r = run_extractor(scripts[0])
            print(f"  Extractor test: sources={r['sources']} flows={len(r['flows'])}")
            print()

    # ── Write extension list JSON (for dynamic taint crawl) ──────────────────
    list_path = LIST_DIR / 'ina_sink_strict_1556.json'
    with open(list_path, 'w') as f:
        json.dump({
            'crawl_type':    'clobber_taint',
            'dataset':       DATASET,
            'count':         len(on_disk),
            'source':        f'v2 dangerous sink strict set (isolated_proxy_log_{V2_SUFFIX})',
            'extension_ids': sorted(on_disk),
        }, f, indent=2)
    print(f"Extension list → {list_path}  ({len(on_disk):,} extensions)")
    print()

    # ── Run static analysis ───────────────────────────────────────────────────
    create_table()
    print(f"Running static analysis ({WORKERS_NODE} workers)...")

    with_flows     = 0
    with_sources   = 0
    total_flows    = 0
    sink_counts    = defaultdict(int)
    prop_counts    = defaultdict(int)
    flow_type_counts = defaultdict(int)

    with mp.Pool(processes=WORKERS_NODE, maxtasksperchild=1) as pool:
        for ext_id, data in tqdm(
            pool.imap_unordered(process_extension, ext_list),
            total=len(ext_list)
        ):
            if data['sources'] > 0:
                with_sources += 1
            if data['flows']:
                with_flows += 1
                total_flows += len(data['flows'])
                for flow in data['flows']:
                    sink_counts[flow.get('sink', 'unknown')] += 1
                    prop_counts[flow.get('property', flow.get('var_name', '?'))] += 1
                    flow_type_counts[flow.get('type', '?')] += 1
                insert_results(ext_id, data)

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print('=' * 65)
    print(f'  Extensions analyzed:          {len(ext_list):>6,}')
    print(f'  With DOM query sources:       {with_sources:>6,}')
    print(f'  With confirmed taint flows:   {with_flows:>6,}')
    print(f'  Total flow instances:         {total_flows:>6,}')
    print()
    print('  Top sinks reached:')
    for sink, n in sorted(sink_counts.items(), key=lambda x: -x[1])[:15]:
        print(f'    {n:>5,}  {sink}')
    print()
    print('  Flow types:')
    for ft, n in sorted(flow_type_counts.items(), key=lambda x: -x[1]):
        print(f'    {n:>5,}  {ft}')
    print('=' * 65)

    summary = {
        'dataset':              DATASET,
        'v2_suffix':            V2_SUFFIX,
        'extensions_analyzed':  len(ext_list),
        'with_dom_sources':     with_sources,
        'with_taint_flows':     with_flows,
        'total_flows':          total_flows,
        'sink_counts':          dict(sorted(sink_counts.items(), key=lambda x: -x[1])),
        'flow_type_counts':     dict(flow_type_counts),
        'extension_list_file':  str(list_path),
    }
    out_path = OUT_DIR / 'static_taint_summary.json'
    with open(out_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary → {out_path}")
    print()
    print("Next: run dynamic taint crawl on these extensions:")
    print(f"  TEST_TYPE=isolated CRAWL_URL_TYPE=clobber_taint \\")
    print(f"  TABLE_SUFFIX=2026_v3_taint DIR_EXTENSION=basic \\")
    print(f"  EXTENSION_LIST_FILE={list_path} \\")
    print(f"  MAX_VISIT=3 WORKERS=20 python crawler/src/crawler.py")


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
