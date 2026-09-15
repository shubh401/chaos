import os, sys, traceback
import numpy as np
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sna_helpers import (
    CRAWL_SUFFIX, THRESHOLD, ATTACKS,
    load_coverage_by_visit, affected_set_per_attack,
    save_results,
)


def analyze():
    print(f"Loading coverage data for suffix={CRAWL_SUFFIX}...")
    by_visit = load_coverage_by_visit()
    visits   = sorted(by_visit.keys())

    per_visit_summary = {}
    for v in visits:
        vdata   = by_visit[v]
        aff_per = affected_set_per_attack(vdata)
        buckets = {'>80': 0, '50-80': 0, '20-50': 0, '5-20': 0}
        for ext_data in vdata.values():
            for atk, d in ext_data.items():
                fck = d.get('fraction_code_killed', 0)
                if   fck > 0.80: buckets['>80']   += 1
                elif fck > 0.50: buckets['50-80'] += 1
                elif fck > 0.20: buckets['20-50'] += 1
                elif fck > 0.05: buckets['5-20']  += 1

        print(f"\n  Visit {v}: {len(vdata):,} extensions")
        for atk in ATTACKS:
            print(f"    {atk:<20}: {len(aff_per[atk]):,} affected (>{THRESHOLD*100:.0f}% kill)")

        per_visit_summary[v] = {
            'extensions_with_data': len(vdata),
            'affected_per_attack':  {atk: len(s) for atk, s in aff_per.items()},
            'affected_any':         sum(1 for vd in vdata.values()
                                        if any(d.get('fraction_code_killed',0) > THRESHOLD
                                               for d in vd.values())),
            'kill_severity_buckets': buckets,
        }

    out = {
        'crawl_suffix': CRAWL_SUFFIX,
        'threshold':    THRESHOLD,
        'visits':       visits,
        'per_visit_summary': per_visit_summary,
        'per_visit_per_extension': {
            str(v): {
                ext_id: {
                    atk: {
                        'fraction_code_killed': d['fraction_code_killed'],
                        'total_bytes':          d['total_bytes'],
                    }
                    for atk, d in ext_data.items()
                }
                for ext_id, ext_data in vdata.items()
            }
            for v, vdata in by_visit.items()
        },
        'note': (
            f'v2: single table shared_coverage_log_{CRAWL_SUFFIX} with {len(visits)} visits. '
            'fraction_code_killed = (exec_baseline - exec_break) / total_bytes per visit. '
            'Each visit independently compares baseline vs break template for each attack.'
        ),
    }
    return out


def main():
    try:
        out = analyze()
        save_results(out, 'sna_execution_impact.json')
    except Exception:
        traceback.print_exc()


if __name__ == '__main__':
    main()
