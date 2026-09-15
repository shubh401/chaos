import os, sys, re, traceback
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sna_helpers import CRAWL_SUFFIX, save_results, load_json

ANALYZER_DIR = Path(__file__).resolve().parent.parent.parent
LOG_PATH     = ANALYZER_DIR / 'https.error.log'

PATTERN_REQUEST = re.compile(r'request: \"(?:POST|GET) (/[^\s\"]+)')
PATTERN_REF     = re.compile(r'extensionId=([a-zA-Z0-9]+)&visit=(\d+)')

# SNA endpoints that affect signal integrity
SIGNAL_ENDPOINTS = {
    '/shared/hook':     'hook_log',
    '/shared/coverage': 'coverage_log',
    '/shared/mutation': 'mutation_log',
    '/shared/error':    'errors',
}


def parse_log():
    ext_visit_eps  = defaultdict(lambda: defaultdict(Counter))
    endpoint_visit = defaultdict(Counter)
    total_by_ep    = Counter()

    with open(LOG_PATH) as f:
        for line in f:
            m_req = PATTERN_REQUEST.search(line)
            m_ref = PATTERN_REF.search(line)
            if not m_req or not m_ref:
                continue
            endpoint = '/' + m_req.group(1).lstrip('/').split('?')[0]
            ext_id   = m_ref.group(1)
            visit    = int(m_ref.group(2))

            # Only keep SNA (shared) endpoints
            if not endpoint.startswith('/shared'):
                continue

            ext_visit_eps[ext_id][visit][endpoint] += 1
            endpoint_visit[endpoint][visit]        += 1
            total_by_ep[endpoint]                  += 1

    return ext_visit_eps, endpoint_visit, total_by_ep


def analyze():
    print(f'Parsing {LOG_PATH} for SNA (/shared) entries...')
    ext_visit_eps, endpoint_visit, total_by_ep = parse_log()

    if not total_by_ep:
        print('  No /shared entries found in log — log may be from a different crawl.')
        print('  (INA entries use /isolated prefix; SNA uses /shared prefix)')
        return {
            'crawl_suffix': CRAWL_SUFFIX,
            'log_path': str(LOG_PATH),
            'total_dropped_rows': 0,
            'unique_extensions_affected': 0,
            'note': 'No /shared entries found. Log file may predate the SNA v2 crawl or use a different prefix.',
        }

    visits = sorted({v for vmap in ext_visit_eps.values() for v in vmap})
    total  = sum(total_by_ep.values())
    print(f'  SNA dropped rows: {total:,}')
    print(f'  Unique extensions affected: {len(ext_visit_eps):,}')
    print(f'  Visits in log: {visits}')

    print(f'\n  Endpoint breakdown:')
    for ep, n in total_by_ep.most_common(15):
        print(f'    {ep:<45} {n:>7,}  ', end='')
        for v in visits:
            print(f'  v{v}={endpoint_visit[ep][v]:,}', end='')
        print()

    # Signal-critical drops
    signal_drops = {}
    for ep, sig in SIGNAL_ENDPOINTS.items():
        affected = {e for e, vmap in ext_visit_eps.items()
                    if any(ep in eps_c for eps_c in vmap.values())}
        by_visit = {v: {e for e, vmap in ext_visit_eps.items()
                        if ep in vmap.get(v, {})}
                    for v in visits}
        signal_drops[sig] = {
            'endpoint':    ep,
            'total_drops': total_by_ep.get(ep, 0),
            'unique_extensions_affected': len(affected),
            'by_visit':    {v: len(s) for v, s in by_visit.items()},
        }
        if total_by_ep.get(ep, 0):
            print(f'\n  {sig} ({ep}):')
            print(f'    Total: {total_by_ep[ep]:,}  Extensions: {len(affected):,}')
            for v in visits:
                print(f'    visit {v}: {len(by_visit[v]):,} extensions')

    # Cross-reference with strict affected set
    try:
        report = load_json('sna_consistency_report.json')
        strict_any = set(report.get('strict_any_attack', []))
        cov_drop_exts = {e for e, vmap in ext_visit_eps.items()
                         if any('/shared/coverage' in eps_c for eps_c in vmap.values())}
        print(f'\n  Strict affected set: {len(strict_any):,}')
        print(f'  Coverage drops any visit: {len(cov_drop_exts):,}')
        print(f'  Strict ∩ coverage drops: {len(strict_any & cov_drop_exts):,}')
        strict_with_drops = len(strict_any & cov_drop_exts)
    except FileNotFoundError:
        strict_any = set()
        strict_with_drops = None
        print('  (consistency report not yet available — run sna_consistency_report.py first)')

    out = {
        'crawl_suffix': CRAWL_SUFFIX,
        'log_path': str(LOG_PATH),
        'total_dropped_rows': total,
        'unique_extensions_affected': len(ext_visit_eps),
        'visits': visits,
        'endpoint_totals': dict(total_by_ep.most_common()),
        'signal_drops': signal_drops,
        'strict_analysis': {
            'strict_any_count': len(strict_any),
            'strict_with_coverage_drops': strict_with_drops,
        } if strict_any else {},
        'per_extension_drops': {
            ext_id: {str(v): dict(eps_c) for v, eps_c in vmap.items()}
            for ext_id, vmap in ext_visit_eps.items()
        },
    }
    return out


def main():
    try:
        out = analyze()
        save_results(out, 'sna_error_log_analysis.json')
    except Exception:
        traceback.print_exc()


if __name__ == '__main__':
    main()
