import os, sys, json, traceback
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import db_helpers as dbh

SUFFIX   = os.getenv('GBS_PRE_SUFFIX')
DATASET  = dbh.DATASET
OUT_DIR  = Path(__file__).resolve().parent.parent.parent / 'results' / 'ina'
OUT_DIR.mkdir(parents=True, exist_ok=True)

LIBRARY_FREQ_THRESHOLD = 0.30

# Minimum variable name length; skip __-prefixed instrumentation names
MIN_NAME_LEN = 3

BASELINE_URL_FRAG = 'type=baseline'   # honey body baseline (clobber_payload&type=baseline)


def load_traces():
    """
    Returns {extension_id: {visit: {varName: trace_string}}}
    Only rows from the baseline URL (mutation_simple) are loaded.
    """
    conn = dbh.get_connection()
    cur  = conn.cursor()
    tbl  = f"isolated_cs_trace_log_{SUFFIX}"
    cur.execute(
        f"SELECT extension_id, visit, traces FROM {tbl} "
        f"WHERE dataset = %s AND url LIKE %s;",
        (DATASET, f'%{BASELINE_URL_FRAG}%')
    )
    rows = cur.fetchall()
    conn.close()
    print(f"  Loaded {len(rows):,} trace rows from {tbl} (baseline URL only)")

    result = defaultdict(lambda: defaultdict(dict))
    for ext_id, visit, traces in rows:
        if not traces: continue
        if isinstance(traces, str):
            try: traces = json.loads(traces)
            except: continue
        if not isinstance(traces, dict): continue
        result[ext_id][visit] = traces
    return result


def is_gbs(trace_str: str) -> bool:
    """True if the trace string starts with 'get'."""
    return isinstance(trace_str, str) and trace_str.strip().startswith('get')


def extract_candidates(traces_by_ext):
    """
    For each extension, collect variables that show GBS in ANY visit (OR union).
    Strict AND filtering is deferred to post-crawl analysis where all visit data
    is available — applying AND here would discard extensions where GBS fired in
    1-2 visits due to timing races or page load variation.
    Returns {extension_id: [varname, ...]}
    """
    result = {}
    for ext_id, visit_map in traces_by_ext.items():
        if not visit_map: continue
        # Union: variable appears as GBS in at least one recorded visit
        gbs_any = set()
        for visit, trace_dict in visit_map.items():
            for name, trace in trace_dict.items():
                if is_gbs(trace) and len(name) >= MIN_NAME_LEN and not name.startswith('__'):
                    gbs_any.add(name)
        if gbs_any:
            result[ext_id] = sorted(gbs_any)
    return result


def flag_library_globals(candidates, n_extensions):
    """
    Returns set of variable names that appear in more than LIBRARY_FREQ_THRESHOLD
    of all extensions — likely library globals.
    """
    freq = defaultdict(int)
    for vars_list in candidates.values():
        for v in vars_list:
            freq[v] += 1
    threshold = n_extensions * LIBRARY_FREQ_THRESHOLD
    return {v for v, count in freq.items() if count > threshold}


def write_db(candidates):
    """Write/overwrite extension_gbs_vars table."""
    conn = dbh.get_connection()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS extension_gbs_vars (
            id           SERIAL PRIMARY KEY,
            extension_id VARCHAR(256),
            dataset      VARCHAR(32) NOT NULL,
            var_names    JSONB,
            tstamp       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS extension_gbs_vars_ext_dat
        ON extension_gbs_vars(extension_id, dataset);
    """)
    cur.execute("DELETE FROM extension_gbs_vars WHERE dataset = %s;", (DATASET,))
    rows = [(ext_id, DATASET, json.dumps(vars_list))
            for ext_id, vars_list in candidates.items()]
    from psycopg2.extras import execute_values
    execute_values(cur,
        "INSERT INTO extension_gbs_vars (extension_id, dataset, var_names) VALUES %s "
        "ON CONFLICT (extension_id, dataset) DO UPDATE SET var_names = EXCLUDED.var_names;",
        rows
    )
    conn.commit()
    conn.close()
    print(f"  Wrote {len(rows):,} rows to extension_gbs_vars")


def main():
    print(f"GBS variable extraction — suffix={SUFFIX}, dataset={DATASET}")
    print()

    print("Loading traces...")
    traces = load_traces()
    print(f"  Extensions with any trace data: {len(traces):,}")

    print("Extracting strict GBS candidates...")
    candidates = extract_candidates(traces)
    print(f"  Extensions with >=1 GBS variable: {len(candidates):,}")

    library_globals = flag_library_globals(candidates, len(traces))
    print(f"  Library globals (>{LIBRARY_FREQ_THRESHOLD*100:.0f}% corpus frequency): "
          f"{len(library_globals)} — {sorted(library_globals)[:10]}...")

    total_vars = sum(len(v) for v in candidates.values())
    print(f"  Total GBS variables across corpus: {total_vars:,}")
    print(f"  Mean per extension: {total_vars/max(len(candidates),1):.1f}")

    print("Writing to extension_gbs_vars...")
    write_db(candidates)

    summary = {
        'suffix':            SUFFIX,
        'dataset':           DATASET,
        'baseline_url_frag': BASELINE_URL_FRAG,
        'extensions_with_traces':    len(traces),
        'extensions_with_gbs':       len(candidates),
        'total_gbs_vars':            total_vars,
        'library_globals_flagged':   sorted(library_globals),
        'library_freq_threshold':    LIBRARY_FREQ_THRESHOLD,
        'top_gbs_vars': [],  # computed below
    }
    freq = defaultdict(int)
    for vars_list in candidates.values():
        for v in vars_list:
            freq[v] += 1
    summary['top_gbs_vars'] = sorted(freq.items(), key=lambda x: -x[1])[:20]

    out_path = OUT_DIR / 'gbs_variables_summary.json'
    with open(out_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"  Summary → {out_path}")
    print()
    print(f"Done. {len(candidates):,} extensions have GBS variables ready for the attack crawl.")

    # Write extension list file for GBS attack crawl (used via EXTENSION_LIST_FILE env var)
    list_dir = Path(__file__).resolve().parent.parent.parent.parent / 'crawler' / 'extension_lists'
    list_dir.mkdir(parents=True, exist_ok=True)
    list_path = list_dir / 'clobber_gbs_attack.json'
    list_out = {
        'crawl_type':    'clobber_gbs_attack',
        'dataset':       DATASET,
        'count':         len(candidates),
        'source':        f'extension_gbs_vars — confirmed GBS candidates from {SUFFIX} traces',
        'extension_ids': sorted(candidates),
    }
    with open(list_path, 'w') as f:
        json.dump(list_out, f, indent=2)
    print(f"  Extension list → {list_path}  ({len(candidates):,} extensions)")
    print()
    print("Next step (GBS attack crawl):")
    ina_suffix = os.getenv('INA_SUFFIX', 'INA_SUFFIX')
    print(f"  TEST_TYPE=isolated CRAWL_URL_TYPE=clobber_gbs_attack \\")
    print(f"  TABLE_SUFFIX={ina_suffix} DIR_EXTENSION=basic \\")
    print(f"  EXTENSION_LIST_FILE={list_path} \\")
    print(f"  MAX_VISIT=3 WORKERS=60 python crawler/main.py")


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
