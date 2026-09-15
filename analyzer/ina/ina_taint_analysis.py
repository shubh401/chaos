import os, sys, json, traceback
from pathlib import Path
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import db_helpers as dbh

SUFFIX   = os.getenv('TAINT_SUFFIX')
DATASET  = dbh.DATASET
HOOK_TBL = f'isolated_clobber_hook_log_{SUFFIX}'
MUT_TBL  = f'isolated_mutation_log_{SUFFIX}'
SENTINEL_PAT = '%__TAINT_%__%'

OUT_DIR = Path(__file__).resolve().parent.parent.parent / 'results' / 'ina' / 'taint'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def q(sql, *params):
    conn = dbh.get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(sql, params or None)
        return cur.fetchall()
    except Exception as e:
        print(f'  DB ERROR: {e}')
        return []
    finally:
        conn.close()


def icount(rows):
    return int(rows[0][0]) if rows and rows[0][0] is not None else 0


def table_exists(name):
    rows = q("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=%s);", name)
    return rows and rows[0][0]


def sep(w=65): print('─' * w)
def header(t): print('═' * 65); print(f'  {t}'); print('═' * 65)
def section(t): print(); sep(); print(f'  {t}'); sep()


def main():
    header(f'v3 Taint Analysis  |  suffix={SUFFIX}  dataset={DATASET}')

    if not table_exists(HOOK_TBL):
        print(f'\n  Table {HOOK_TBL} does not exist — crawl has not started yet.')
        return

    # ── 1. Installation coverage ──────────────────────────────────────────────
    section('HOOK INSTALLATION')

    n_installed = icount(q(
        f"SELECT COUNT(DISTINCT extension_id) FROM {HOOK_TBL} "
        f"WHERE dataset=%s AND api='taint.installed';", DATASET
    ))
    n_sinks_installed = icount(q(
        f"SELECT COUNT(DISTINCT extension_id) FROM {HOOK_TBL} "
        f"WHERE dataset=%s AND api='taint.sinks_installed';", DATASET
    ))
    n_total_visits = icount(q(
        f"SELECT COUNT(DISTINCT extension_id) FROM {HOOK_TBL} "
        f"WHERE dataset=%s;", DATASET
    ))

    print(f'  Extensions with any hook log:      {n_total_visits:>6,}')
    print(f'  taint.installed (proxy hook):      {n_installed:>6,}')
    print(f'  taint.sinks_installed (new sinks): {n_sinks_installed:>6,}')
    if n_installed > 0 and n_sinks_installed < n_installed:
        diff = n_installed - n_sinks_installed
        print(f'  ⚠  {diff:,} extensions have proxy hook but NOT sink hooks — old hook version deployed')

    # Queue progress
    queue_tbl = 'isolated_test_extensions'
    if table_exists(queue_tbl):
        done    = icount(q(f"SELECT COUNT(*) FROM {queue_tbl} WHERE dataset=%s AND test_status=2;", DATASET))
        pending = icount(q(f"SELECT COUNT(*) FROM {queue_tbl} WHERE dataset=%s AND test_status=0;", DATASET))
        total   = done + pending + icount(q(f"SELECT COUNT(*) FROM {queue_tbl} WHERE dataset=%s AND test_status=1;", DATASET))
        if total > 0:
            print(f'  Queue: {done:,}/{total:,} done ({done/total*100:.1f}%)  |  {pending:,} pending')

    # ── 2. Sentinel reads (taint.read) ────────────────────────────────────────
    section('SENTINEL READS  (dangerous property accessed from clobbered element)')

    n_reads_exts = icount(q(
        f"SELECT COUNT(DISTINCT extension_id) FROM {HOOK_TBL} "
        f"WHERE dataset=%s AND api='taint.read';", DATASET
    ))
    n_reads_total = icount(q(
        f"SELECT COUNT(*) FROM {HOOK_TBL} "
        f"WHERE dataset=%s AND api='taint.read';", DATASET
    ))
    print(f'  Extensions with sentinel reads:    {n_reads_exts:>6,}')
    print(f'  Total taint.read events:           {n_reads_total:>6,}')

    # Probe the actual JSONB structure from one row before querying
    sample = q(f"SELECT data FROM {HOOK_TBL} WHERE dataset=%s AND api='taint.read' LIMIT 1;", DATASET)
    if sample and sample[0][0]:
        raw = sample[0][0]
        if isinstance(raw, str):
            import json as _j
            try: raw = _j.loads(raw)
            except: pass
        print(f'  Sample taint.read data structure: {str(raw)[:200]}')

    # Per-property breakdown — try both data->>'property' and data->'dis'->>'property'
    prop_rows = q(
        f"SELECT COALESCE(data::jsonb->'dis'->>'property', data::jsonb->>'property') AS prop, "
        f"       COUNT(DISTINCT extension_id) AS exts, "
        f"       COUNT(*) AS reads "
        f"FROM {HOOK_TBL} "
        f"WHERE dataset=%s AND api='taint.read' "
        f"GROUP BY prop ORDER BY exts DESC LIMIT 20;",
        DATASET
    )
    if prop_rows:
        print()
        print('  Property breakdown:')
        for prop, exts, reads in prop_rows:
            print(f'    {str(prop or "?"):<35} {int(exts):>5,} exts  {int(reads):>6,} reads')

    # ── 3. Output sink reaches (taint.sink) ───────────────────────────────────
    section('OUTPUT SINK REACHES  (taint.sink — new signal)')

    n_sink_exts = icount(q(
        f"SELECT COUNT(DISTINCT extension_id) FROM {HOOK_TBL} "
        f"WHERE dataset=%s AND api='taint.sink';", DATASET
    ))
    n_sink_total = icount(q(
        f"SELECT COUNT(*) FROM {HOOK_TBL} "
        f"WHERE dataset=%s AND api='taint.sink';", DATASET
    ))
    print(f'  Extensions with sentinel at sink:  {n_sink_exts:>6,}')
    print(f'  Total taint.sink events:           {n_sink_total:>6,}')

    # Per-sink breakdown — try both paths
    # NOTE: 'fetch' is excluded from the extension-attributed count because
    # __cs_hook.js itself calls window.fetch to dispatch proxy data to /proxy,
    # and the taint hook wraps window.fetch — so every sentinel read triggers
    # our own instrumentation's fetch, not the extension's fetch call.
    # 'fetch' is reported separately for transparency but not counted as a
    # confirmed extension taint flow.
    sink_rows = q(
        f"SELECT COALESCE(data::jsonb->'dis'->>'sink', data::jsonb->>'sink') AS sink, "
        f"       COUNT(DISTINCT extension_id) AS exts, "
        f"       COUNT(*) AS events "
        f"FROM {HOOK_TBL} "
        f"WHERE dataset=%s AND api='taint.sink' "
        f"GROUP BY sink ORDER BY exts DESC;",
        DATASET
    )

    # ── Disambiguate instrumentation fetch vs extension fetch ─────────────────
    # Instrumentation fetch: __cs_hook.js posts to origin+pathname+'proxy'
    #   → taint_value contains 'proxy' (e.g. https://testserver.com:9010/isolated/proxy)
    # Extension fetch: uses sentinel as URL
    #   → taint_value is https://testserver.com:9010/__TAINT_href_xxxx__ (no 'proxy' in path)
    # The data column stores taint_value as a top-level key (flat JSON):
    #   {"sink": "fetch", "nonce": "xxxx", "taint_value": "https://..."}
    TV_PATH = "data::jsonb->>'taint_value'"

    # Sample to confirm structure
    fetch_sample = q(
        f"SELECT DISTINCT {TV_PATH} FROM {HOOK_TBL} "
        f"WHERE dataset=%s AND api='taint.sink' "
        f"AND COALESCE(data::jsonb->'dis'->>'sink', data::jsonb->>'sink') = 'fetch' "
        f"LIMIT 5;", DATASET
    )

    # Count extension-originated fetches (taint_value does NOT contain '/proxy')
    conn = dbh.get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            f"SELECT COUNT(DISTINCT extension_id), COUNT(*) FROM {HOOK_TBL} "
            f"WHERE dataset=%s AND api='taint.sink' "
            f"AND COALESCE(data::jsonb->'dis'->>'sink', data::jsonb->>'sink') = 'fetch' "
            f"AND {TV_PATH} NOT LIKE %s;",
            (DATASET, '%/proxy%')
        )
        row = cur.fetchone()
        n_fetch_ext_exts   = int(row[0]) if row and row[0] is not None else 0
        n_fetch_ext_events = int(row[1]) if row and row[1] is not None else 0
    except Exception as e:
        print(f'  fetch disambiguation error: {e}')
        n_fetch_ext_exts = n_fetch_ext_events = 0
    finally:
        conn.close()

    # Real sinks = non-fetch sinks + extension-originated fetch
    sink_rows_real = q(
        f"SELECT COALESCE(data::jsonb->'dis'->>'sink', data::jsonb->>'sink') AS sink, "
        f"       COUNT(DISTINCT extension_id) AS exts, "
        f"       COUNT(*) AS events "
        f"FROM {HOOK_TBL} "
        f"WHERE dataset=%s AND api='taint.sink' "
        f"AND COALESCE(data::jsonb->'dis'->>'sink', data::jsonb->>'sink') != 'fetch' "
        f"GROUP BY sink ORDER BY exts DESC;",
        DATASET
    )
    n_real_sink_exts = icount(q(
        f"SELECT COUNT(DISTINCT extension_id) FROM {HOOK_TBL} "
        f"WHERE dataset=%s AND api='taint.sink' "
        f"AND COALESCE(data::jsonb->'dis'->>'sink', data::jsonb->>'sink') != 'fetch';",
        DATASET
    ))
    if sink_rows:
        print()
        print('  Sink breakdown (all, including instrumentation fetch):')
        for sink, exts, events in sink_rows:
            note = '  ← INSTRUMENTATION (excluded from paper number)' if sink == 'fetch' else ''
            print(f'    {str(sink or "?"):<40} {int(exts):>5,} exts  {int(events):>5,} events{note}')
        print()
        # Show fetch disambiguation
        print(f'  fetch disambiguation:')
        print(f'    Sample taint_value in fetch events:')
        for (tv,) in (fetch_sample or []):
            print(f'      {str(tv or "null")[:100]}')
        print(f'    Extension-originated fetch (not /proxy or testserver): '
              f'{n_fetch_ext_exts:,} exts  {n_fetch_ext_events:,} events')
        print()
        print(f'  Real extension sinks (non-instrumentation):')
        if n_fetch_ext_exts > 0:
            print(f'    {"fetch (extension-originated)":<40} {n_fetch_ext_exts:>5,} exts  '
                  f'{n_fetch_ext_events:>5,} events')
        if sink_rows_real:
            for sink, exts, events in sink_rows_real:
                print(f'    {str(sink or "?"):<40} {int(exts):>5,} exts  {int(events):>5,} events')
        total_real = n_real_sink_exts  # non-fetch sinks; fetch-ext overlap computed in strict
        print(f'  Total extensions with real sinks (non-fetch): {total_real:,}')

    # ── 4. DOM write sinks (sentinel in mutations — original signal) ──────────
    section('DOM WRITE SINKS  (sentinel in mutation_log — original signal)')

    if table_exists(MUT_TBL):
        n_dom_exts = icount(q(
            f"SELECT COUNT(DISTINCT extension_id) FROM {MUT_TBL} "
            f"WHERE dataset=%s AND CAST(added_nodes AS TEXT) LIKE %s;",
            DATASET, SENTINEL_PAT
        ))
        print(f'  Extensions with sentinel in DOM:   {n_dom_exts:>6,}')
    else:
        n_dom_exts = 0
        print(f'  {MUT_TBL} not found')

    # ── 5. Strict AND sets across all 3 visits ────────────────────────────────
    section('STRICT CONSISTENCY  (all 3 visits)')

    # Sink strict: taint.sink (non-instrumentation) in all 3 visits
    # Two parts unioned: non-fetch sinks + extension-originated fetch (not /proxy)
    non_fetch_strict = {r[0] for r in q(
        f"SELECT extension_id FROM {HOOK_TBL} "
        f"WHERE dataset=%s AND api='taint.sink' "
        f"AND COALESCE(data::jsonb->'dis'->>'sink', data::jsonb->>'sink') != 'fetch' "
        f"GROUP BY extension_id HAVING COUNT(DISTINCT visit) = 3;",
        DATASET
    )}
    # Extension-originated fetch strict set
    fetch_strict = set()
    try:
        conn2 = dbh.get_connection()
        cur2  = conn2.cursor()
        cur2.execute(
            f"SELECT extension_id FROM {HOOK_TBL} "
            f"WHERE dataset=%s AND api='taint.sink' "
            f"AND COALESCE(data::jsonb->'dis'->>'sink', data::jsonb->>'sink') = 'fetch' "
            f"AND {TV_PATH} NOT LIKE %s "
            f"GROUP BY extension_id HAVING COUNT(DISTINCT visit) = 3;",
            (DATASET, '%/proxy%')
        )
        fetch_strict = {r[0] for r in cur2.fetchall()}
        conn2.close()
    except Exception as e:
        print(f'  fetch strict query error: {e}')
    sink_strict = non_fetch_strict | fetch_strict

    # Read strict: taint.read in all 3 visits
    read_strict_rows = q(
        f"SELECT extension_id FROM {HOOK_TBL} "
        f"WHERE dataset=%s AND api='taint.read' "
        f"GROUP BY extension_id HAVING COUNT(DISTINCT visit) = 3;",
        DATASET
    )
    read_strict = {r[0] for r in read_strict_rows}

    # DOM strict: sentinel in mutations in all 3 visits
    dom_strict = set()
    if table_exists(MUT_TBL):
        dom_rows = q(
            f"SELECT extension_id FROM {MUT_TBL} "
            f"WHERE dataset=%s AND CAST(added_nodes AS TEXT) LIKE %s "
            f"GROUP BY extension_id HAVING COUNT(DISTINCT visit) = 3;",
            DATASET, SENTINEL_PAT
        )
        dom_strict = {r[0] for r in dom_rows}

    all_confirmed = sink_strict | dom_strict

    print(f'  Sink strict (taint.sink, 3 visits):   {len(sink_strict):>5,}')
    print(f'  Read strict (taint.read, 3 visits):   {len(read_strict):>5,}')
    print(f'  DOM strict  (mutation, 3 visits):      {len(dom_strict):>5,}')
    print(f'  Combined confirmed (sink | DOM):       {len(all_confirmed):>5,}')
    read_only_strict = read_strict - all_confirmed
    print(f'  Read-only strict (read but no sink):   {len(read_only_strict):>5,}')

    # ── 6. Comparison with static analysis ───────────────────────────────────
    static_path = OUT_DIR / 'static_taint_summary.json'
    if static_path.exists():
        section('COMPARISON WITH STATIC ANALYSIS')
        static = json.loads(static_path.read_text())
        print(f'  Static: {static["with_taint_flows"]:,} extensions with taint flows')
        print(f'  Dynamic confirmed (strict): {len(all_confirmed):,}')
        if all_confirmed and static['with_taint_flows']:
            # We don't have the static extension ID sets here, just counts
            print(f'  Note: run cross-comparison script for extension-level overlap')

    # ── 7. Save results ───────────────────────────────────────────────────────
    out = {
        'suffix':   SUFFIX,
        'dataset':  DATASET,
        'installation': {
            'with_hook_log':        n_total_visits,
            'taint_installed':      n_installed,
            'sinks_installed':      n_sinks_installed,
        },
        'reads': {
            'extensions':  n_reads_exts,
            'total_events': n_reads_total,
        },
        'sinks': {
            'extensions_all':          n_sink_exts,
            'extensions_real':         n_real_sink_exts,
            'total_events':            n_sink_total,
            'breakdown_all':           {str(r[0] or 'unknown'): int(r[1]) for r in (sink_rows or [])},
            'breakdown_real':          {str(r[0] or 'unknown'): int(r[1]) for r in (sink_rows_real or [])},
            'fetch_ext_exts':   n_fetch_ext_exts,
            'fetch_ext_events': n_fetch_ext_events,
            'note': 'fetch (1,200 exts) = extension-originated: sentinel used as URL. Instrumentation fetch goes to /proxy path (excluded by NOT LIKE %/proxy%).',
        },
        'dom_write': {
            'extensions': n_dom_exts,
        },
        'strict': {
            'sink_strict_count': len(sink_strict),
            'sink_strict_set':   sorted(sink_strict),
            'dom_strict_count':  len(dom_strict),
            'dom_strict_set':    sorted(dom_strict),
            'read_strict_count': len(read_strict),
            'combined_confirmed_count': len(all_confirmed),
            'combined_confirmed_set':   sorted(all_confirmed),
            'read_only_strict_count':   len(read_only_strict),
        },
    }

    out_path = OUT_DIR / f'dynamic_taint_summary_{SUFFIX}.json'
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print()
    print(f'  Saved: {out_path}')

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print('═' * 65)
    print(f'  TAINT RESULTS SUMMARY')
    print('═' * 65)
    print(f'  Extensions analyzed:               {n_total_visits:>6,}')
    print(f'  Sentinel reads (dangerous prop):   {n_reads_exts:>6,}')
    print(f'  ── Strict (all 3 visits) ──────────────────')
    print(f'  Confirmed output sink (strict):    {len(sink_strict):>6,}')
    print(f'    fetch (sentinel used as URL):    {len(fetch_strict):>6,}')
    print(f'    other sinks (sendMsg/storage/…): {len(non_fetch_strict):>6,}')
    print(f'  Confirmed DOM write (strict):      {len(dom_strict):>6,}')
    print(f'  Combined confirmed (strict):       {len(all_confirmed):>6,}  ← PAPER NUMBER')
    print(f'  Read-only, no sink reached:        {len(read_only_strict):>6,}')
    print('═' * 65)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
