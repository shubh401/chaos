import os, sys, traceback
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sna_helpers import (
    CRAWL_SUFFIX, THRESHOLD, ATTACKS,
    pairwise_jaccard, save_results, load_json,
)

ATK_LABEL = {
    'hook':             'API Overwrites',
    'global_preassign': 'Variable Pollution',
    'event_swallow':    'Event Poisoning',
    'raider':           'State Cleanup',
    'proto_poison':     'Prototype Poisoning',
}


def section(title):
    print(f'\n{"=" * 72}')
    print(f'  {title}')
    print(f'{"=" * 72}')


def delta_str(old, new):
    if old is None or new is None:
        return 'N/A'
    d = new - old
    sign = '+' if d >= 0 else ''
    return f'{sign}{d:,}'


def main():
    print(f'SNA v2 Consistency Report — crawl suffix: {CRAWL_SUFFIX}')
    print(f'Comparing 3 visits within a single crawl (MAX_VISIT=3)\n')

    try:
        impact = load_json('sna_execution_impact.json')
    except FileNotFoundError:
        print('ERROR: sna_execution_impact.json not found — run sna_execution_impact.py first.')
        return

    visits  = impact['visits']
    pv_data = impact['per_visit_per_extension']

    # Reconstruct per-attack affected sets per visit
    # {attack: {visit: set of ext_ids}}
    atk_sets_by_visit = {atk: {} for atk in ATTACKS}
    for v in visits:
        vdata = pv_data[str(v)]
        for atk in ATTACKS:
            atk_sets_by_visit[atk][v] = {
                ext_id for ext_id, ext_data in vdata.items()
                if ext_data.get(atk, {}).get('fraction_code_killed', 0) > THRESHOLD
            }

    # Any-attack affected set per visit
    any_atk_by_visit = {
        v: set().union(*[atk_sets_by_visit[atk][v] for atk in ATTACKS])
        for v in visits
    }

    # ── 1. Per-visit affected counts ─────────────────────────────────────────
    section('1. PER-VISIT AFFECTED COUNTS')
    print(f'\n  {"Attack":<22}', end='')
    for v in visits: print(f'  visit{v}:>8', end='')
    print(f'  {"strict":>8}  {"majority":>9}  {"union":>7}')
    print(f'  {"-"*22}', end='')
    for _ in visits: print(f'  {"--------":>8}', end='')
    print(f'  {"--------":>8}  {"---------":>9}  {"-------":>7}')

    per_attack_results = {}
    for atk in ATTACKS:
        cons = pairwise_jaccard(atk_sets_by_visit[atk])
        s    = cons['_summary']
        per_attack_results[atk] = {'consistency': cons, 'strict_set': None}

        print(f'  {ATK_LABEL[atk]:<22}', end='')
        for v in visits:
            print(f'  {s["per_visit_n"][v]:>8,}', end='')
        print(f'  {s["strict_all"]:>8,}  {s["majority_ge2"]:>9,}  {s["union"]:>7,}')

    # Any attack
    any_cons = pairwise_jaccard(any_atk_by_visit)
    s_any    = any_cons['_summary']
    print(f'  {"Any attack":<22}', end='')
    for v in visits:
        print(f'  {s_any["per_visit_n"][v]:>8,}', end='')
    print(f'  {s_any["strict_all"]:>8,}  {s_any["majority_ge2"]:>9,}  {s_any["union"]:>7,}')

    # ── 2. Pairwise Jaccard per attack ────────────────────────────────────────
    section('2. PAIRWISE JACCARD PER ATTACK')
    for atk in ATTACKS:
        cons = pairwise_jaccard(atk_sets_by_visit[atk])
        print(f'\n  {ATK_LABEL[atk]}:')
        for key, info in cons.items():
            if key == '_summary': continue
            v1, v2 = key
            print(f'    Visit {v1} vs {v2}: Jaccard={info["jaccard"]:.4f}  '
                  f'(n_a={info["n_a"]}, n_b={info["n_b"]}, '
                  f'∩={info["intersection"]}, only_a={info["only_a"]}, only_b={info["only_b"]})')

    print(f'\n  Any attack:')
    for key, info in any_cons.items():
        if key == '_summary': continue
        v1, v2 = key
        print(f'    Visit {v1} vs {v2}: Jaccard={info["jaccard"]:.4f}  '
              f'(n_a={info["n_a"]}, n_b={info["n_b"]}, ∩={info["intersection"]})')

    # ── 3. Kill severity for strict set ──────────────────────────────────────
    section('3. KILL SEVERITY — STRICT SET (all 3 visits)')

    # Build strict set per attack
    strict_per_atk = {}
    for atk in ATTACKS:
        sets = [atk_sets_by_visit[atk][v] for v in visits]
        strict_per_atk[atk] = set.intersection(*sets)

    strict_any = set.union(*strict_per_atk.values())

    print(f'\n  {"Attack":<22} {"n":>6}  {">80%":>6}  {"50-80%":>7}  {"20-50%":>7}  {"5-20%":>6}')
    print(f'  {"-"*22} {"------":>6}  {"------":>6}  {"-------":>7}  {"-------":>7}  {"------":>6}')

    severity_out = {}
    for atk in ATTACKS:
        strict_exts = strict_per_atk[atk]
        buckets     = {'>80': 0, '50-80': 0, '20-50': 0, '5-20': 0}
        # Use median fraction_code_killed across visits for each strict extension
        for ext_id in strict_exts:
            fracs = [pv_data[str(v)].get(ext_id, {}).get(atk, {}).get('fraction_code_killed', 0)
                     for v in visits]
            median_fck = sorted(fracs)[len(fracs)//2]
            if   median_fck > 0.80: buckets['>80']   += 1
            elif median_fck > 0.50: buckets['50-80'] += 1
            elif median_fck > 0.20: buckets['20-50'] += 1
            elif median_fck > 0.05: buckets['5-20']  += 1
        print(f'  {ATK_LABEL[atk]:<22} {len(strict_exts):>6,}  '
              f'{buckets[">80"]:>6}  {buckets["50-80"]:>7}  '
              f'{buckets["20-50"]:>7}  {buckets["5-20"]:>6}')
        severity_out[atk] = buckets

    # Overall (deduplicated strict any-attack set)
    overall_buckets = {'>80': 0, '50-80': 0, '20-50': 0, '5-20': 0}
    for ext_id in strict_any:
        # max fraction killed across attacks (worst-case)
        max_fck = 0
        for atk in ATTACKS:
            fracs = [pv_data[str(v)].get(ext_id, {}).get(atk, {}).get('fraction_code_killed', 0)
                     for v in visits]
            max_fck = max(max_fck, sorted(fracs)[len(fracs)//2])
        if   max_fck > 0.80: overall_buckets['>80']   += 1
        elif max_fck > 0.50: overall_buckets['50-80'] += 1
        elif max_fck > 0.20: overall_buckets['20-50'] += 1
        elif max_fck > 0.05: overall_buckets['5-20']  += 1
    print(f'  {"Overall":<22} {len(strict_any):>6,}  '
          f'{overall_buckets[">80"]:>6}  {overall_buckets["50-80"]:>7}  '
          f'{overall_buckets["20-50"]:>7}  {overall_buckets["5-20"]:>6}')

    # ── 4. Verdict ────────────────────────────────────────────────────────────
    section('4. CONSISTENCY VERDICT')
    total_strict = len(strict_any)
    print(f'\n  Total affected (strict, any attack): {total_strict:,}')
    print()
    for atk in ATTACKS:
        s = pairwise_jaccard(atk_sets_by_visit[atk])['_summary']
        strict_n = s['strict_all']
        union_n  = s['union']
        ratio = strict_n / max(union_n, 1)
        status = 'CONSISTENT' if ratio >= 0.80 else 'LOW CONSISTENCY'
        print(f'  {status}  {ATK_LABEL[atk]:<22}  strict={strict_n:,}  union={union_n:,}  ({ratio:.1%})')

    # ── Save ──────────────────────────────────────────────────────────────────
    out = {
        'crawl_suffix': CRAWL_SUFFIX,
        'threshold':    THRESHOLD,
        'visits':       visits,
        'per_attack_consistency': {
            atk: {str(k): v for k, v in pairwise_jaccard(atk_sets_by_visit[atk]).items()}
            for atk in ATTACKS
        },
        'any_attack_consistency': {str(k): v for k, v in any_cons.items()},
        'strict_sets': {
            atk: sorted(list(s)) for atk, s in strict_per_atk.items()
        },
        'strict_any_attack': sorted(list(strict_any)),
        'kill_severity_strict': {
            **severity_out,
            'overall': overall_buckets,
        },
    }
    save_results(out, 'sna_consistency_report.json')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
