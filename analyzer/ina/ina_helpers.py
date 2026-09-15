import os, sys, json
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import db_helpers as dbh
from db_helpers import get_connection, DATASET

CRAWL_SUFFIX = os.getenv('INA_SUFFIX')
TEST_TYPE    = 'isolated'
N_VISITS     = 3

# ── URL fragments — must be unique across all log table rows ─────────────
# Crawl 1: FD/SF targeted clobber
URL_FD_BASELINE = 'type=baseline'    # honey body only (no clobber)
URL_FD_TARGETED = 'type=targeted'    # honey body + per-ext selector payload

# Crawl 2: GBS trace collection — uses honey body baseline (same as FD/SF targeted)
# Honey body activates content-triggered GBS extensions so baseline mutations > 0.
# __gbs_trace.js fires regardless of page content so traces are still collected.
URL_GBS_TRACE    = 'type=baseline'    # honey body only (reuses FD baseline URL)

# Crawl 3: GBS attack
URL_GBS_ATTACK   = 'clobber_gbs_payload'  # honey body + <a id="V"> in head

# GBS SF/FD: compare Crawl 2 baseline (honey body, no clobber) vs Crawl 3 attack
URL_GBS_BASELINE = URL_GBS_TRACE     # type=baseline rows = GBS baseline

DANGEROUS_SINKS = {
    'src', 'href', 'action', 'formaction', 'innerHTML', 'outerHTML',
    'srcdoc', 'data', 'value', 'textContent', 'location',
    'setAttribute', 'insertAdjacentHTML',
}

# SF thresholds — same as v1/v2
MIN_BASELINE_MUTATIONS   = 10
FRACTION_LOST_THRESHOLD  = 0.80


def _table(table_type):
    return f"{TEST_TYPE}_{table_type}_{CRAWL_SUFFIX}"


def _results_dir():
    base = Path(__file__).resolve().parent.parent.parent
    d = base / 'results' / 'ina' / CRAWL_SUFFIX
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_results(data, filename):
    path = _results_dir() / filename
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved: {path}")


def load_json(filename):
    path = _results_dir() / filename
    with open(path) as f:
        return json.load(f)


CLOBBER_PAYLOAD_URL_FRAG = 'clobber_payload'


def query_table_payload(table_type, columns):
    """Query only clobber_payload rows, filtering URL server-side."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        f"SELECT {columns} FROM {_table(table_type)} "
        f"WHERE dataset = %s AND url LIKE %s;",
        (DATASET, f'%{CLOBBER_PAYLOAD_URL_FRAG}%')
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def query_by_url(table_type, columns, url_frag):
    """Query a log table filtering to rows whose URL contains url_frag."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        f"SELECT {columns} FROM {_table(table_type)} "
        f"WHERE dataset = %s AND url LIKE %s;",
        (DATASET, f'%{url_frag}%')
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def pairwise_jaccard(sets_by_visit):
    """Compute pairwise Jaccard similarity across visits. Returns empty summary if no data."""
    visits = sorted(sets_by_visit.keys())
    out = {}
    if not visits:
        out['_summary'] = {'visits': [], 'per_visit_n': {}, 'union': 0, 'majority_ge2': 0, 'strict_all': 0}
        return out
    for i, va in enumerate(visits):
        for vb in visits[i+1:]:
            a, b = sets_by_visit[va], sets_by_visit[vb]
            inter = len(a & b)
            union = len(a | b)
            out[str((va, vb))] = {
                'visit_a': va, 'visit_b': vb,
                'n_a': len(a), 'n_b': len(b),
                'intersection': inter, 'union': union,
                'only_a': len(a - b), 'only_b': len(b - a),
                'jaccard': round(inter / union, 4) if union else 1.0,
            }
    all_sets = [sets_by_visit[v] for v in visits]
    strict = all_sets[0].copy()
    for s in all_sets[1:]:
        strict &= s
    union_all = set()
    for s in all_sets:
        union_all |= s
    majority = set()
    for ext in union_all:
        if sum(1 for s in all_sets if ext in s) >= (len(all_sets) + 1) // 2:
            majority.add(ext)
    out['_summary'] = {
        'visits':       visits,
        'per_visit_n':  {v: len(sets_by_visit[v]) for v in visits},
        'union':        len(union_all),
        'majority_ge2': len(majority),
        'strict_all':   len(strict),
    }
    return out
