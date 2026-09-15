import os
import sys
import traceback
import importlib.util
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ina_helpers import CRAWL_SUFFIX


def run_module(name, path):
    print()
    print(f'{"=" * 72}')
    print(f'  RUNNING: {name}')
    print(f'{"=" * 72}')
    t0 = time.time()
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()
        elapsed = time.time() - t0
        print(f'  [{name}] Done in {elapsed:.1f}s')
        return True
    except Exception:
        traceback.print_exc()
        print(f'  [{name}] FAILED')
        return False


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    print(f'INA Pipeline: suffix={CRAWL_SUFFIX}')
    print(f'Results → results/ina/{CRAWL_SUFFIX}/')

    steps = [
        ('ina_hit_rate',            os.path.join(base, 'ina_hit_rate.py')),
        ('ina_dangerous_sinks',     os.path.join(base, 'ina_dangerous_sinks.py')),
        ('ina_coverage_impact',     os.path.join(base, 'ina_coverage_impact.py')),
        ('ina_mutation_delta',      os.path.join(base, 'ina_mutation_delta.py')),
        ('ina_proxy_access_counts', os.path.join(base, 'ina_proxy_access_counts.py')),
        ('ina_consistency_report',  os.path.join(base, 'ina_consistency_report.py')),
        ('ina_error_log_analysis',  os.path.join(base, 'ina_error_log_analysis.py')),
    ]

    results = {}
    for name, path in steps:
        if not os.path.exists(path):
            print(f'  SKIP {name}: file not found')
            results[name] = 'SKIP'
            continue
        ok = run_module(name, path)
        results[name] = 'OK' if ok else 'FAIL'

    print()
    print('=' * 72)
    print('  PIPELINE SUMMARY')
    print('=' * 72)
    for name, status in results.items():
        print(f'  {status:<6}  {name}')


if __name__ == '__main__':
    main()
