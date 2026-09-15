import os
import sys
import traceback
import importlib.util
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sna_helpers import CRAWL_SUFFIX


def run_module(name, path):
    print()
    print(f'{"=" * 72}')
    print(f'  RUNNING: {name}')
    print(f'{"=" * 72}')
    t0 = time.time()
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()
        print(f'  [{name}] Done in {time.time() - t0:.1f}s')
        return True
    except Exception:
        traceback.print_exc()
        print(f'  [{name}] FAILED')
        return False


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    print(f'SNA Pipeline: suffix={CRAWL_SUFFIX}')
    print(f'Results → results/sna/{CRAWL_SUFFIX}/')

    steps = [
        ('sna_execution_impact',   os.path.join(base, 'sna_execution_impact.py')),
        ('sna_consistency_report', os.path.join(base, 'sna_consistency_report.py')),
        ('sna_component_impact',   os.path.join(base, 'sna_component_impact.py')),
        ('sna_error_log_analysis', os.path.join(base, 'sna_error_log_analysis.py')),
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
