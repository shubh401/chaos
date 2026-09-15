import os, sys, json, traceback
from pathlib import Path
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ina_helpers import (
    CRAWL_SUFFIX, save_results, pairwise_jaccard,
    load_json,
)

def section(title):
    print(f'\n{"=" * 72}')
    print(f'  {title}')
    print(f'{"=" * 72}')


def load_all():
    data = {}
    for key, fname in [
        ('hit_rate',      'ina_hit_rate.json'),
        ('sinks',         'ina_dangerous_sinks.json'),
        ('coverage',      'ina_coverage_impact.json'),
        ('mutations',     'ina_mutation_delta.json'),
    ]:
        try:
            data[key] = load_json(fname)
            print(f"  Loaded: {fname}")
        except FileNotFoundError:
            print(f"  MISSING: {fname} — run the pipeline first")
            data[key] = None
    return data


def main():
    print(f'INA v2 Consistency Report — crawl suffix: {CRAWL_SUFFIX}')
    print(f'Comparing 3 visits within a single crawl (MAX_VISIT=3)\n')

    data = load_all()

    # -------------------------------------------------------------------------
    # 1. Hit rate stability
    # -------------------------------------------------------------------------
    section('1. HIT RATE STABILITY (clobber_payload URL)')

    if data['hit_rate']:
        hr = data['hit_rate']
        consistency = hr.get('consistency', {})
        summary = consistency.get('_summary', {})
        visits = summary.get('visits', [])
        pv = hr.get('per_visit', {})

        print(f'\n  {"Visit":<8} {"Extensions queried":>20} {"With any hit":>15}')
        print(f'  {"-" * 45}')
        for v in visits:
            d = pv.get(str(v), pv.get(v, {}))
            print(f'  {v:<8} {d.get("extensions_with_queries", "?"):>20,} {d.get("extensions_with_any_hit", "?"):>15,}')

        print(f'\n  Pairwise Jaccard (any hit):')
        for key, info in consistency.items():
            if key == '_summary':
                continue
            try:
                pair = eval(key) if isinstance(key, str) else key
                if isinstance(pair, tuple):
                    print(f'    Visit {pair[0]} vs {pair[1]}: Jaccard={info["jaccard"]:.4f}  '
                          f'(∩={info["intersection"]}, only_a={info["only_a"]}, only_b={info["only_b"]})')
            except Exception:
                pass

        print(f'\n  Union (≥1 visit):    {summary.get("union", "?"):>6,}')
        print(f'  Majority (≥2 visits):{summary.get("majority_ge2", "?"):>6,}')
        print(f'  Strict (all visits): {summary.get("strict_all", "?"):>6,}')

    # -------------------------------------------------------------------------
    # 2. Dangerous sink stability
    # -------------------------------------------------------------------------
    section('2. DANGEROUS SINK STABILITY')

    if data['sinks']:
        sk = data['sinks']
        consistency = sk.get('consistency', {})
        summary = consistency.get('_summary', {})
        visits = summary.get('visits', [])
        pv = sk.get('per_visit_summary', {})

        print(f'\n  {"Visit":<8} {"With any sink":>15}')
        print(f'  {"-" * 25}')
        for v in visits:
            d = pv.get(str(v), pv.get(v, {}))
            print(f'  {v:<8} {d.get("extensions_with_any_sink", "?"):>15,}')

        print(f'\n  Pairwise Jaccard (dangerous sink):')
        for key, info in consistency.items():
            if key == '_summary':
                continue
            try:
                pair = eval(key) if isinstance(key, str) else key
                if isinstance(pair, tuple):
                    print(f'    Visit {pair[0]} vs {pair[1]}: Jaccard={info["jaccard"]:.4f}  '
                          f'(∩={info["intersection"]}, only_a={info["only_a"]}, only_b={info["only_b"]})')
            except Exception:
                pass

        strict_n = summary.get('strict_all', 0)
        majority_n = summary.get('majority_ge2', 0)
        union_n = summary.get('union', 0)
        print(f'\n  Union (≥1 visit):    {union_n:>6,}')
        print(f'  Majority (≥2 visits):{majority_n:>6,}')
        print(f'  Strict (all visits): {strict_n:>6,}')

    # -------------------------------------------------------------------------
    # 3. Silent failure stability
    # -------------------------------------------------------------------------
    section('3. SILENT FAILURE STABILITY')

    if data['mutations']:
        mu = data['mutations']
        sf_strict = mu.get('silent_failure_strict_count', 0)
        sf_union  = mu.get('silent_failure_union_count', 0)
        sf_maj    = mu.get('silent_failure_majority_count', 0)
        pv        = mu.get('per_visit', {})
        print(f'\n  {"Visit":<8} {"Extensions w/ mutations":>25} {"SF count":>10}')
        print(f'  {"-" * 45}')
        for v in sorted(pv.keys()):
            d = pv[v]
            print(f'  {v:<8} {d.get("extensions_with_mutations", "?"):>25,} {d.get("sf_count", "?"):>10,}')
        print(f'\n  Pairwise Jaccard (SF set):')
        cons = mu.get('consistency', {})
        for key, info in cons.items():
            if key == '_summary':
                continue
            try:
                pair = eval(key) if isinstance(key, str) else key
                if isinstance(pair, tuple):
                    print(f'    Visit {pair[0]} vs {pair[1]}: Jaccard={info["jaccard"]:.4f}  '
                          f'(∩={info["intersection"]}, only_a={info["only_a"]}, only_b={info["only_b"]})')
            except Exception:
                pass
        print(f'\n  Union (≥1 visit SF):    {sf_union:,}')
        print(f'  Majority (≥2 visits):   {sf_maj:,}')
        print(f'  Strict (all visits):    {sf_strict:,}')

    # -------------------------------------------------------------------------
    # 4. Coverage stability
    # -------------------------------------------------------------------------
    section('4. COVERAGE STABILITY (coefficient of variation across visits)')

    if data['coverage']:
        cv_data = data['coverage']
        stab = cv_data.get('stability_summary', {})
        print(f'\n  Extensions analyzed: {cv_data.get("extensions_analyzed", "?"):,}')
        print(f'  Stable   (CV < 10%):  {stab.get("stable_cv_lt10pct", "?"):,}')
        print(f'  Moderate (CV 10-30%): {stab.get("moderate_cv_10_30pct", "?"):,}')
        print(f'  Noisy    (CV ≥ 30%):  {stab.get("noisy_cv_ge30pct", "?"):,}')

    # -------------------------------------------------------------------------
    # 5. INA union per visit
    # -------------------------------------------------------------------------
    section('5. INA UNION COUNTS PER VISIT AND TOTALS')

    if data['sinks'] and data['mutations']:
        sk_pv = data['sinks'].get('per_visit_per_extension', {})
        sf_strict_set = set(data['mutations'].get('silent_failure_strict_set', []))

        sink_by_visit = {
            v: set(exts.keys())
            for v, exts in sk_pv.items()
        }
        visits = sorted(sink_by_visit.keys(), key=lambda x: int(x) if str(x).isdigit() else x)

        print(f'\n  {"Visit":<8} {"Sinks":>8} {"SF (strict)":>12} {"Union":>8}')
        print(f'  {"-" * 40}')
        for v in visits:
            sinks_v = sink_by_visit.get(v, set())
            union_v = sinks_v | sf_strict_set
            print(f'  {v:<8} {len(sinks_v):>8,} {len(sf_strict_set):>12,} {len(union_v):>8,}')

        # Strict sink set
        if sink_by_visit:
            all_sink_sets = [sink_by_visit[v] for v in visits]
            strict_sinks = set.intersection(*all_sink_sets) if all_sink_sets else set()
            strict_union = strict_sinks | sf_strict_set
            print(f'\n  Strict sinks (all visits) + SF (strict): {len(strict_sinks):,} + {len(sf_strict_set):,} = {len(strict_union):,}')

    # -------------------------------------------------------------------------
    # 6. Verdict
    # -------------------------------------------------------------------------
    section('6. CONSISTENCY VERDICT')

    print()
    if data['sinks']:
        sk_s = data['sinks'].get('consistency', {}).get('_summary', {})
        strict_sinks = sk_s.get('strict_all', 0)
        union_sinks  = sk_s.get('union', 0)
        ratio = strict_sinks / max(union_sinks, 1)
        status = 'CONSISTENT' if ratio >= 0.80 else 'LOW CONSISTENCY'
        print(f'  {status}  Dangerous sinks strict/union = {strict_sinks:,}/{union_sinks:,} ({ratio:.1%})')

    if data['mutations']:
        sf_strict = data['mutations'].get('silent_failure_strict_count', 0)
        sf_union  = data['mutations'].get('silent_failure_union_count', 0)
        ratio = sf_strict / max(sf_union, 1)
        status = 'CONSISTENT' if ratio >= 0.40 else 'LOW CONSISTENCY'
        print(f'  {status}  SF strict/union = {sf_strict:,}/{sf_union:,} ({ratio:.1%})')
    print()

    # -------------------------------------------------------------------------
    # Save
    # -------------------------------------------------------------------------
    out = {
        'crawl_suffix': CRAWL_SUFFIX,
    }

    if data['sinks']:
        sk_s = data['sinks'].get('consistency', {}).get('_summary', {})
        out['dangerous_sink_summary'] = {
            'per_visit': sk_s.get('per_visit_n', {}),
            'union': sk_s.get('union'),
            'majority_ge2': sk_s.get('majority_ge2'),
            'strict_all': sk_s.get('strict_all'),
        }

    if data['hit_rate']:
        hr_s = data['hit_rate'].get('consistency', {}).get('_summary', {})
        out['hit_rate_summary'] = {
            'per_visit': hr_s.get('per_visit_n', {}),
            'union': hr_s.get('union'),
            'majority_ge2': hr_s.get('majority_ge2'),
            'strict_all': hr_s.get('strict_all'),
        }

    if data['mutations']:
        mu = data['mutations']
        out['silent_failure_summary'] = {
            'strict_count': mu.get('silent_failure_strict_count'),
            'majority_count': mu.get('silent_failure_majority_count'),
            'union_count': mu.get('silent_failure_union_count'),
        }

    save_results(out, 'ina_consistency_report.json')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
