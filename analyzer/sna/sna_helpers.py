import os
import sys
import json
from collections import defaultdict, Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import db_helpers as dbh
from db_helpers import (
    get_connection, DATASET, TEMPLATE_PAIRS,
    classify_coverage_scripts, get_template_from_url,
)

CRAWL_SUFFIX = os.getenv('SNA_SUFFIX')
THRESHOLD    = 0.05   # fraction_code_killed > 5% → affected (mirrors v1)
ATTACKS      = list(TEMPLATE_PAIRS.keys())  # hook, raider, proto_poison, event_swallow, global_preassign


def _results_dir():
    base = Path(__file__).resolve().parent.parent.parent
    d = base / 'results' / 'sna' / CRAWL_SUFFIX
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


def load_coverage_by_visit():
    """
    Query shared_coverage_log_{CRAWL_SUFFIX} and return:
        {visit: {ext_id: {attack: {fraction_code_killed, exec_bytes_baseline,
                                    exec_bytes_break, total_bytes}}}}

    Uses the (dataset, extension_id, visit) index. Pushes template URL filter
    into SQL via LIKE ANY(...) to avoid shipping non-SNA rows over the network.
    Only the 10 SNA template URLs are fetched; all other pages are excluded.
    """
    # Build the set of template filename patterns we need
    templates = set()
    for base_tmpl, break_tmpl in TEMPLATE_PAIRS.values():
        templates.add(base_tmpl)
        templates.add(break_tmpl)
    like_patterns = [f'%{t}%' for t in templates]

    print(f"  Querying shared_coverage_log_{CRAWL_SUFFIX} (filtering to {len(templates)} SNA templates)...")
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        f"SELECT extension_id, visit, url, coverage "
        f"FROM shared_coverage_log_{CRAWL_SUFFIX} "
        f"WHERE dataset = %s AND url LIKE ANY(%s);",
        (DATASET, like_patterns)
    )
    rows = cur.fetchall()
    conn.close()
    print(f"  {len(rows):,} coverage rows loaded")

    # {visit: {ext_id: {template: [{url, total_len, exec_len}]}}}
    raw = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for ext_id, visit, url, coverage_data in rows:
        if not coverage_data or not isinstance(coverage_data, dict):
            continue
        template = get_template_from_url(url)
        if template is None:
            continue
        classified = classify_coverage_scripts(coverage_data, ext_id)
        for stype, scripts in classified.items():
            for script_url, total_len, exec_len, pct in scripts:
                if total_len and total_len > 0:
                    raw[visit][ext_id][template].append({
                        'url':       script_url,
                        'total_len': total_len,
                        'exec_len':  exec_len or 0,
                    })

    visits = sorted(raw.keys())
    print(f"  Visits found: {visits}")

    # Compute fraction_code_killed per visit × extension × attack
    result = {}
    for visit in visits:
        visit_result = {}
        for ext_id, templates in raw[visit].items():
            ext_data = {}
            for attack, (baseline_tmpl, break_tmpl) in TEMPLATE_PAIRS.items():
                baseline = templates.get(baseline_tmpl, [])
                brk      = templates.get(break_tmpl, [])
                if not baseline and not brk:
                    continue

                b_by_url = defaultdict(list)
                for s in baseline:
                    b_by_url[s['url']].append(s)
                k_by_url = defaultdict(list)
                for s in brk:
                    k_by_url[s['url']].append(s)

                all_urls        = set(b_by_url) | set(k_by_url)
                total_bytes     = 0
                total_exec_base = 0
                total_exec_brk  = 0

                for surl in all_urls:
                    b_ents = b_by_url.get(surl, [])
                    k_ents = k_by_url.get(surl, [])
                    tlen   = (b_ents or k_ents)[0]['total_len']
                    total_bytes     += tlen
                    total_exec_base += sum(e['exec_len'] for e in b_ents) / len(b_ents) if b_ents else 0.0
                    total_exec_brk  += sum(e['exec_len'] for e in k_ents) / len(k_ents) if k_ents else 0.0

                if total_bytes == 0:
                    continue

                frac = (total_exec_base - total_exec_brk) / total_bytes
                ext_data[attack] = {
                    'fraction_code_killed': round(frac, 6),
                    'exec_bytes_baseline':  round(total_exec_base),
                    'exec_bytes_break':     round(total_exec_brk),
                    'total_bytes':          int(total_bytes),
                }

            if ext_data:
                visit_result[ext_id] = ext_data
        result[visit] = visit_result
        print(f"    Visit {visit}: {len(visit_result):,} extensions with coverage data")

    return result


def affected_set(visit_data):
    """Return set of ext_ids affected (fraction_code_killed > THRESHOLD for any attack)."""
    return {e for e, atks in visit_data.items()
            if any(d.get('fraction_code_killed', 0) > THRESHOLD for d in atks.values())}


def affected_set_per_attack(visit_data):
    """Return {attack: set of affected ext_ids} for one visit."""
    result = {atk: set() for atk in ATTACKS}
    for ext_id, atks in visit_data.items():
        for atk, d in atks.items():
            if d.get('fraction_code_killed', 0) > THRESHOLD:
                result[atk].add(ext_id)
    return result


def jaccard(a, b):
    if not a and not b:
        return 1.0
    u = a | b
    return len(a & b) / len(u) if u else 0.0


def pairwise_jaccard(sets_by_visit):
    """
    Given {visit: set}, return pairwise stats + strict/majority/union summary.
    Mirrors INA v2 helper exactly.
    """
    visits = sorted(sets_by_visit.keys())
    out    = {}
    for i, v1 in enumerate(visits):
        for v2 in visits[i+1:]:
            s1, s2 = sets_by_visit[v1], sets_by_visit[v2]
            out[(v1, v2)] = {
                'visit_a': v1, 'visit_b': v2,
                'n_a': len(s1), 'n_b': len(s2),
                'intersection': len(s1 & s2),
                'union': len(s1 | s2),
                'only_a': len(s1 - s2),
                'only_b': len(s2 - s1),
                'jaccard': round(jaccard(s1, s2), 4),
            }
    all_sets  = [sets_by_visit[v] for v in visits]
    strict    = set.intersection(*all_sets) if all_sets else set()
    union_all = set.union(*all_sets) if all_sets else set()
    counts    = Counter()
    for s in all_sets:
        counts.update(s)
    majority = {e for e, c in counts.items() if c >= 2}
    out['_summary'] = {
        'visits': visits,
        'per_visit_n': {v: len(sets_by_visit[v]) for v in visits},
        'union': len(union_all),
        'majority_ge2': len(majority),
        'strict_all': len(strict),
    }
    return out
