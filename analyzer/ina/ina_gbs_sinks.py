import os, sys, json, traceback
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ina_helpers import (
    query_by_url, CRAWL_SUFFIX, pairwise_jaccard,
    URL_GBS_ATTACK, DANGEROUS_SINKS, save_results,
)

# Properties that indicate a type/identity check — extension is testing what
# the object is rather than using its data. Reading ONLY these does not constitute
# meaningful data flow.
TYPE_GUARD_PROPS = {
    'nodeType', 'tagName', 'nodeName', 'constructor',
    'nodeValue', 'localName', 'namespaceURI',
}

# Properties that indicate the extension is just iterating/traversing the object
# rather than reading meaningful data from it. Included with type guards for the
# "structural-only" exclusion tier.
STRUCTURAL_PROPS = {
    'length', 'forEach', 'map', 'filter', 'reduce',
    'addEventListener', 'removeEventListener',
    'appendChild', 'removeChild', 'contains',
    'parentNode', 'parentElement', 'childNodes', 'children',
    'nextSibling', 'previousSibling', 'firstChild', 'lastChild',
    'ownerDocument', 'getRootNode',
    '0', '1', '2', '3',   # numeric index access on unexpected array-like
}

# Combined set: structural + type-guard — reading only these is not meaningful data flow
NON_MEANINGFUL = TYPE_GUARD_PROPS | STRUCTURAL_PROPS


import re as _re
_GETATTR_RE = _re.compile(r'getAttribute\(["\']([^"\']+)["\']\)', _re.IGNORECASE)

def leaf(ident):
    """
    Extract the accessed property name from a proxy identifier.
    Handles direct access (...querySelector(...).href) and
    getAttribute calls (...getAttribute("href")).
    """
    if not ident: return ''
    # Check getAttribute("prop") — extract argument as the effective property
    m = _GETATTR_RE.search(ident)
    if m:
        return m.group(1).lower()
    tail = ident.rsplit('.', 1)[-1]
    if tail.endswith('()'): tail = tail[:-2]
    if '[' in tail: tail = tail.split('[', 1)[0]
    return tail


def parse_proxy_data(proxy_data):
    if not proxy_data: return []
    if isinstance(proxy_data, str):
        try: proxy_data = json.loads(proxy_data)
        except: return []
    if not isinstance(proxy_data, list): return []
    return [e.get('identifier', '') for e in proxy_data if isinstance(e, dict)]


def has_property_access(ident):
    """True if identifier shows a property read off the clobbered element (depth > root)."""
    if not ident: return False
    stripped = ident[len('window.'):] if ident.startswith('window.') else ident
    return '.' in stripped or '[' in stripped


def classify_extension(idents):
    """
    Given the set of all identifiers accessed by one extension across all visits,
    classify the data flow pattern:
      'dangerous'       — read a known dangerous sink property
      'meaningful_unguarded' — read meaningful property, no type guard present
      'meaningful_guarded'   — read meaningful property AND a type guard property
      'structural_only' — only structural/type-guard properties, no meaningful data
    """
    leaves = {leaf(i) for i in idents if has_property_access(i)}
    if not leaves:
        return 'no_property_access'

    has_dangerous   = bool(leaves & DANGEROUS_SINKS)
    has_type_guard  = bool(leaves & TYPE_GUARD_PROPS)
    has_meaningful  = bool(leaves - NON_MEANINGFUL)   # non-structural, non-type-guard

    if has_dangerous:
        return 'dangerous'
    if has_meaningful and not has_type_guard:
        return 'meaningful_unguarded'
    if has_meaningful and has_type_guard:
        return 'meaningful_guarded'
    return 'structural_only'


def strict_set(by_visit):
    """Intersection of extension sets across all visits.
    by_visit values may be sets (tier_per_visit) or dicts (sinks_by_visit)."""
    result = None
    for v in by_visit.values():
        ext_set = set(v.keys()) if isinstance(v, dict) else set(v)
        result = ext_set if result is None else result & ext_set
    return result or set()


def main():
    print(f"INA v3 GBS Sinks — suffix={CRAWL_SUFFIX}")

    rows = query_by_url('proxy_log', 'extension_id, visit, proxy_data', URL_GBS_ATTACK)
    print(f"  proxy_log rows on GBS attack URL: {len(rows):,}")

    # Collect all identifiers per (extension, visit)
    idents_by_ext_visit = defaultdict(lambda: defaultdict(set))
    # All identifiers ever seen per extension (across all visits) for classification
    all_idents_by_ext = defaultdict(set)

    for ext_id, visit, proxy_data in rows:
        for ident in parse_proxy_data(proxy_data):
            idents_by_ext_visit[ext_id][visit].add(ident)
            all_idents_by_ext[ext_id].add(ident)

    # ── Per-visit population for each tier ───────────────────────────────────
    # For strict AND, an extension must appear in the same tier across all 3 visits.
    # We classify per-extension (using all-visit union of identifiers) since the
    # property access pattern is stable — an extension that checks nodeType does
    # so consistently, not randomly per visit.
    tier_by_ext = {
        ext_id: classify_extension(idents)
        for ext_id, idents in all_idents_by_ext.items()
    }

    # Group extensions by tier
    tiers = defaultdict(set)
    for ext_id, tier in tier_by_ext.items():
        tiers[tier].add(ext_id)

    # Per-visit counts (how many extensions in each tier had proxy data that visit)
    tier_per_visit = defaultdict(lambda: defaultdict(set))
    for ext_id, visit_map in idents_by_ext_visit.items():
        tier = tier_by_ext[ext_id]
        for visit in visit_map:
            tier_per_visit[tier][visit].add(ext_id)

    # Strict: present in all 3 visits within their tier
    tier_strict = {
        tier: strict_set(visit_map)
        for tier, visit_map in tier_per_visit.items()
    }

    # ── Dangerous sink view (Tier 1) — for pairwise Jaccard ──────────────────
    sinks_by_visit = defaultdict(set)
    for ext_id, visit_map in idents_by_ext_visit.items():
        if tier_by_ext[ext_id] == 'dangerous':
            for visit in visit_map:
                sinks_by_visit[visit].add(ext_id)
    sink_consistency = pairwise_jaccard(dict(sinks_by_visit))

    # ── Property frequency across all extensions ──────────────────────────────
    prop_freq = Counter()
    for idents in all_idents_by_ext.values():
        for ident in idents:
            prop_freq[leaf(ident)] += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    t1  = tiers.get('dangerous', set())
    t2  = tiers.get('meaningful_unguarded', set())
    t3  = tiers.get('meaningful_guarded', set())
    t_s = tiers.get('structural_only', set())
    t_n = tiers.get('no_property_access', set())

    t1_strict  = tier_strict.get('dangerous', set())
    t2_strict  = tier_strict.get('meaningful_unguarded', set())
    t3_strict  = tier_strict.get('meaningful_guarded', set())

    # Combined INA GBS flow set (all tiers with confirmed data flow)
    gbs_flow_strict = t1_strict | t2_strict | t3_strict

    out = {
        'crawl_suffix': CRAWL_SUFFIX,
        'total_extensions_with_proxy_data': len(all_idents_by_ext),
        'tier_summary': {
            'tier1_dangerous_sinks': {
                'description': 'Read known dangerous sink property (href/src/action/innerHTML/...)',
                'count_any_visit':   len(t1),
                'count_strict_all3': len(t1_strict),
                'strict_set':        sorted(t1_strict),
                'consistency':       sink_consistency,
            },
            'tier2_meaningful_unguarded': {
                'description': 'Read meaningful property, NO type guard (nodeType/tagName/...) present — no defensive awareness',
                'count_any_visit':   len(t2),
                'count_strict_all3': len(t2_strict),
                'strict_set':        sorted(t2_strict),
            },
            'tier3_meaningful_guarded': {
                'description': 'Read meaningful property AND a type guard — attempted defence but meaningful read still occurred',
                'count_any_visit':   len(t3),
                'count_strict_all3': len(t3_strict),
                'strict_set':        sorted(t3_strict),
            },
            'structural_only': {
                'description': 'Only structural/iteration/type-check properties — disruption confirmed, no meaningful data flow',
                'count_any_visit': len(t_s),
                'any_set':         sorted(t_s),
            },
            'no_property_access': {
                'description': 'Proxy fired but no property access off clobbered element detected',
                'count': len(t_n),
            },
        },
        'gbs_flow_strict_set': sorted(gbs_flow_strict),
        'gbs_flow_strict_count': len(gbs_flow_strict),
        'top_accessed_properties': [
            {'property': p, 'count': n,
             'category': 'dangerous_sink' if p in DANGEROUS_SINKS
                         else 'type_guard' if p in TYPE_GUARD_PROPS
                         else 'structural' if p in STRUCTURAL_PROPS
                         else 'meaningful'}
            for p, n in prop_freq.most_common(25)
        ],
    }
    save_results(out, 'ina_gbs_sinks.json')

    print(f"\n{'─'*60}")
    print(f"  Tier 1 — Dangerous sink reads")
    print(f"    Any visit:    {len(t1):>5,}  |  Strict all-3: {len(t1_strict):>5,}")
    print(f"  Tier 2 — Meaningful, unguarded (no type check)")
    print(f"    Any visit:    {len(t2):>5,}  |  Strict all-3: {len(t2_strict):>5,}")
    print(f"  Tier 3 — Meaningful, guarded (type check present but read still occurred)")
    print(f"    Any visit:    {len(t3):>5,}  |  Strict all-3: {len(t3_strict):>5,}")
    print(f"  Structural only (disruption, no data flow)")
    print(f"    Any visit:    {len(t_s):>5,}")
    print(f"{'─'*60}")
    print(f"\nTop accessed properties:")
    for entry in out['top_accessed_properties'][:15]:
        print(f"  {entry['count']:>5,}  {entry['property']:<30}  [{entry['category']}]")


if __name__ == '__main__':
    try: main()
    except Exception: traceback.print_exc()
