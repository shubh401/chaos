import os, sys, json, traceback
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ina_helpers import (
    query_table_payload, CRAWL_SUFFIX, DANGEROUS_SINKS,
    save_results,
)

TOP_N = 30   # non-dangerous properties to report


def parse_entries(proxy_data):
    if not proxy_data:
        return []
    if isinstance(proxy_data, str):
        try:
            proxy_data = json.loads(proxy_data)
        except Exception:
            return []
    if not isinstance(proxy_data, list):
        return []
    out = []
    for entry in proxy_data:
        if isinstance(entry, dict):
            ident = entry.get('identifier')
            if ident:
                out.append(str(ident))
    return out


def leaf(ident):
    if not ident:
        return ''
    tail = ident.rsplit('.', 1)[-1]
    if tail.endswith('()'):
        tail = tail[:-2]
    if '[' in tail:
        tail = tail.split('[', 1)[0]
    return tail


def analyze():
    print(f"Loading proxy_log for suffix={CRAWL_SUFFIX} (all visits)...")
    rows = query_table_payload(
        'proxy_log',
        'extension_id, visit, proxy_data',
    )
    print(f"  Rows on clobber_payload URL: {len(rows):,}")

    leaf_counts    = Counter()   # all leaf properties (raw)
    visit_counts   = Counter()   # rows per visit
    ext_set        = set()
    total_idents   = 0
    dangerous_ext_set = defaultdict(set)

    for ext_id, visit, proxy_data in rows:
        if not proxy_data:
            continue
        visit_counts[visit] += 1
        ext_set.add(ext_id)
        for ident in parse_entries(proxy_data):
            total_idents += 1
            lf = leaf(ident)
            leaf_counts[lf] += 1
            if lf in DANGEROUS_SINKS:
                dangerous_ext_set[lf].add(ext_id)

    print(f"  Extensions with any proxy access: {len(ext_set):,}")
    print(f"  Total identifier records:         {total_idents:,}")
    print(f"  Rows per visit: {dict(sorted(visit_counts.items()))}")

    # Split dangerous vs non-dangerous
    dangerous_counts    = {k: v for k, v in leaf_counts.items() if k in DANGEROUS_SINKS}
    non_dangerous_counts = {k: v for k, v in leaf_counts.items() if k not in DANGEROUS_SINKS}

    total_dangerous    = sum(dangerous_counts.values())
    total_non_dangerous = sum(non_dangerous_counts.values())
    total_all          = sum(leaf_counts.values())

    print(f"\n  Total leaf accesses:      {total_all:,}")
    print(f"  Non-dangerous accesses:   {total_non_dangerous:,}  ({100*total_non_dangerous/total_all:.1f}%)")
    print(f"  Dangerous sink accesses:  {total_dangerous:,}  ({100*total_dangerous/total_all:.1f}%)")

    print(f"\n  Top {TOP_N} non-dangerous properties:")
    print(f"  {'Property':<35} {'Accesses':>10}")
    top_non_dangerous = Counter(non_dangerous_counts).most_common(TOP_N)
    for prop, n in top_non_dangerous:
        print(f"  {prop:<35} {n:>10,}")

    print(f"\n  Dangerous sink property accesses:")
    for prop, n in sorted(dangerous_counts.items(), key=lambda x: -x[1]):
        n_exts = len(dangerous_ext_set[prop])
        print(f"  {prop:<35} {n:>10,} accesses  ({n_exts} extensions)")

    out = {
        'crawl_suffix': CRAWL_SUFFIX,
        'rows_on_payload': len(rows),
        'extensions_with_accesses': len(ext_set),
        'total_identifier_records': total_idents,
        'rows_per_visit': {int(v): n for v, n in visit_counts.items()},
        'totals': {
            'all_accesses': total_all,
            'non_dangerous': total_non_dangerous,
            'dangerous': total_dangerous,
            'non_dangerous_pct': round(100 * total_non_dangerous / total_all, 1) if total_all else 0,
        },
        'top_non_dangerous': [
            {'property': prop, 'accesses': n}
            for prop, n in top_non_dangerous
        ],
        'dangerous_sink_accesses': {
            prop: {'accesses': n, 'extensions': len(dangerous_ext_set[prop])}
            for prop, n in sorted(dangerous_counts.items(), key=lambda x: -x[1])
        },
        'all_leaf_counts': dict(Counter(leaf_counts).most_common(100)),
        'note': (
            f'Aggregated across all {len(visit_counts)} visits of {CRAWL_SUFFIX}. '
            'Each visit delivers the same clobber payload; counts reflect total '
            'accesses across the full crawl, not per-visit averages. '
            'Non-dangerous accesses confirm proxy coverage and validate that '
            'dangerous sinks are a conservative lower bound on attacker influence.'
        ),
    }
    return out


def main():
    try:
        out = analyze()
        save_results(out, 'ina_proxy_access_counts.json')
    except Exception:
        traceback.print_exc()


if __name__ == '__main__':
    main()
