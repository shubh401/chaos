import os, sys, json, traceback, re
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ina_helpers import (
    query_table_payload, CRAWL_SUFFIX, N_VISITS, DANGEROUS_SINKS,
    save_results, pairwise_jaccard,
)

_GETATTR_RE = re.compile(r'getAttribute\(["\']([^"\']+)["\']\)', re.IGNORECASE)


def parse_entries(proxy_data):
    """Parse proxy_data JSONB list → list of identifier strings."""
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


def is_dangerous_sink(ident):
    """
    Return (True, prop_name) if ident accesses a dangerous source property:
      - direct leaf access: ...querySelector(...).href  → tail='href'
      - getAttribute call:  ...getAttribute("href")     → extracted via regex
    Returns (False, '') otherwise.
    """
    if not ident:
        return False, ''
    tail = ident.rsplit('.', 1)[-1]
    if tail.endswith('()'):
        tail = tail[:-2]
    if '[' in tail:
        tail = tail.split('[', 1)[0]
    if tail in DANGEROUS_SINKS:
        return True, tail
    m = _GETATTR_RE.search(ident)
    if m:
        arg = m.group(1).lower()
        if arg in DANGEROUS_SINKS:
            return True, arg
    return False, ''


def collect_sinks_by_visit():
    """
    Returns: {visit: {ext_id: set of dangerous leaf properties accessed}}
    Queries isolated_proxy_log_{CRAWL_SUFFIX}.
    Uses query_table_payload to filter to clobber_payload URL in SQL and
    only fetch extension_id, visit, proxy_data (skips url, context_url, type).
    """
    rows = query_table_payload(
        'proxy_log',
        'extension_id, visit, proxy_data',
    )
    print(f"  proxy_log rows on clobber_payload URL: {len(rows):,}")

    result = defaultdict(lambda: defaultdict(set))
    for ext_id, visit, proxy_data in rows:
        if not proxy_data:
            continue
        for ident in parse_entries(proxy_data):
            dangerous, prop = is_dangerous_sink(ident)
            if dangerous:
                result[visit][ext_id].add(prop)
    return result


def analyze():
    print(f"Loading proxy_log for sink analysis, suffix={CRAWL_SUFFIX}...")
    by_visit = collect_sinks_by_visit()

    visits = sorted(by_visit.keys())
    print(f"  Visits found: {visits}  (expected {N_VISITS})")

    sets_has_sink = {v: set(by_visit[v].keys()) for v in visits}

    per_visit = {}
    for v in visits:
        ext_sinks = by_visit[v]
        has_sink = sets_has_sink[v]
        sink_counts = Counter()
        for sinks in ext_sinks.values():
            sink_counts.update(sinks)
        per_visit[v] = {
            'extensions_with_any_sink': len(has_sink),
            'sink_property_counts': dict(sink_counts.most_common()),
            'per_extension': {e: sorted(list(s)) for e, s in ext_sinks.items()},
        }
        print(f"  Visit {v}: {len(has_sink):,} extensions with dangerous sinks")
        for prop, n in sink_counts.most_common(8):
            print(f"    {prop:<30} {n:>6,} extensions")

    consistency = pairwise_jaccard(sets_has_sink)
    print(f"\n  Dangerous sink consistency across visits:")
    for key, info in consistency.items():
        if key == '_summary':
            continue
        if isinstance(key, tuple):
            v1, v2 = key
            print(f"    Visit {v1} vs {v2}: Jaccard={info['jaccard']:.4f}  "
                  f"(n_a={info['n_a']}, n_b={info['n_b']}, "
                  f"∩={info['intersection']}, only_a={info['only_a']}, only_b={info['only_b']})")
    s = consistency['_summary']
    print(f"\n  Union (≥1 visit with sink):    {s['union']:,}")
    print(f"  Majority (≥2 visits with sink):  {s['majority_ge2']:,}")
    print(f"  Strict (all {len(visits)} visits with sink):    {s['strict_all']:,}")

    out = {
        'crawl_suffix': CRAWL_SUFFIX,
        'visits': visits,
        'per_visit_summary': {
            v: {k: pv[k] for k in ['extensions_with_any_sink', 'sink_property_counts']}
            for v, pv in per_visit.items()
        },
        'per_visit_per_extension': {
            v: pv['per_extension'] for v, pv in per_visit.items()
        },
        'consistency': {str(k): v for k, v in consistency.items()},
    }
    return out


def main():
    try:
        out = analyze()
        save_results(out, 'ina_dangerous_sinks.json')
    except Exception:
        traceback.print_exc()


if __name__ == '__main__':
    main()
