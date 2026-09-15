import os, sys, traceback
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ina_helpers import (
    query_table_payload, CRAWL_SUFFIX, N_VISITS,
    save_results, pairwise_jaccard,
)


def collect_by_visit():
    """
    Returns: {visit: {ext_id: {'queries': n, 'hits': n, 'apis': Counter}}}
    A hit is any row where data or proxy_data is non-empty.
    Uses query_table_payload to filter to clobber_payload URL in SQL.
    Only selects columns needed; skips large text fields (stacktrace, caller, etc.).
    """
    rows = query_table_payload(
        'clobber_hook_log',
        'extension_id, visit, api, data, proxy_data',
    )
    result = defaultdict(lambda: defaultdict(lambda: {'queries': 0, 'hits': 0, 'apis': Counter()}))
    for ext_id, visit, api, data, proxy_data in rows:
        result[visit][ext_id]['queries'] += 1
        result[visit][ext_id]['apis'][api] += 1
        if (data and str(data).strip()) or (proxy_data and str(proxy_data).strip()):
            result[visit][ext_id]['hits'] += 1
    return result


def analyze():
    print(f"Loading clobber_hook_log for suffix={CRAWL_SUFFIX}...")
    by_visit = collect_by_visit()

    visits = sorted(by_visit.keys())
    print(f"  Visits found: {visits}  (expected {N_VISITS})")

    # Per-visit summary + per-extension stats
    per_visit = {}
    sets_any_hit = {}
    for v in visits:
        ext_data = by_visit[v]
        any_hit = {e for e, d in ext_data.items() if d['hits'] > 0}
        sets_any_hit[v] = any_hit
        per_visit[v] = {
            'extensions_with_queries': len(ext_data),
            'extensions_with_any_hit': len(any_hit),
            'total_query_rows': sum(d['queries'] for d in ext_data.values()),
            'total_hit_rows': sum(d['hits'] for d in ext_data.values()),
            'per_extension': {
                e: {
                    'queries': d['queries'],
                    'hits': d['hits'],
                    'hit_rate': round(d['hits'] / d['queries'], 4) if d['queries'] else 0,
                }
                for e, d in ext_data.items()
            },
        }
        print(f"  Visit {v}: {len(ext_data):,} extensions with queries, "
              f"{len(any_hit):,} with any hit, "
              f"{per_visit[v]['total_query_rows']:,} total rows")

    # Pairwise consistency
    consistency = pairwise_jaccard(sets_any_hit)
    print(f"\n  Hit-rate consistency across visits (Jaccard on 'any hit' binary):")
    for key, info in consistency.items():
        if key == '_summary':
            continue
        v1, v2 = key
        print(f"    Visit {v1} vs {v2}: Jaccard={info['jaccard']:.4f}  "
              f"(n_a={info['n_a']}, n_b={info['n_b']}, "
              f"∩={info['intersection']}, only_a={info['only_a']}, only_b={info['only_b']})")
    s = consistency['_summary']
    print(f"\n  Union (≥1 visit with hit):   {s['union']:,}")
    print(f"  Majority (≥2 visits with hit): {s['majority_ge2']:,}")
    print(f"  Strict (all {len(visits)} visits with hit):   {s['strict_all']:,}")

    out = {
        'crawl_suffix': CRAWL_SUFFIX,
        'visits': visits,
        'per_visit': per_visit,
        'consistency': {str(k): v for k, v in consistency.items()},
    }
    return out


def main():
    try:
        out = analyze()
        save_results(out, 'ina_hit_rate.json')
    except Exception:
        traceback.print_exc()


if __name__ == '__main__':
    main()
