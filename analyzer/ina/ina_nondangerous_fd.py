import os, sys, json, traceback
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ina_helpers import (
    query_by_url, CRAWL_SUFFIX, N_VISITS,
    URL_FD_BASELINE, URL_FD_TARGETED,
    save_results,
)
from db_helpers import (
    classify_coverage_scripts, SCRIPT_TYPE_CS, get_connection, DATASET,
)

FD_THRESHOLD   = 0.05
MIN_EXEC_BYTES = 1024

# Dangerous source properties — same as DANGEROUS_SINKS in ina_helpers
DANGEROUS_SOURCES = {
    'src', 'href', 'action', 'formaction', 'innerHTML', 'outerHTML',
    'srcdoc', 'data', 'value', 'textContent', 'location',
    'setAttribute', 'insertAdjacentHTML',
}

OUT_DIR = Path(__file__).resolve().parent.parent.parent / 'results' / 'ina' / CRAWL_SUFFIX


import re as _re
_GETATTR_RE = _re.compile(r'getAttribute\(["\']([^"\']+)["\']\)', _re.IGNORECASE)


def is_dangerous_ident(ident):
    """
    Return True if the identifier accesses a dangerous source property, either:
      - direct property access: ...querySelector(...).href
      - getAttribute with a dangerous argument: ...getAttribute("href")
    """
    if not ident:
        return False
    ident = str(ident)
    # Check direct leaf property
    tail = ident.rsplit('.', 1)[-1]
    if tail.endswith('()'):
        tail = tail[:-2]
    if '[' in tail:
        tail = tail.split('[', 1)[0]
    if tail in DANGEROUS_SOURCES:
        return True
    # Check getAttribute("dangerous_prop") argument
    m = _GETATTR_RE.search(ident)
    if m and m.group(1).lower() in DANGEROUS_SOURCES:
        return True
    return False


def get_proxy_extension_sets():
    """
    From the proxy log on the targeted attack URL, return:
      - dangerous_set: extensions that accessed at least one dangerous source property
        (via direct property access OR getAttribute with a dangerous argument)
      - nondangerous_set: extensions that accessed the clobbered element but ONLY
                          non-dangerous properties
    """
    conn = get_connection()
    cur  = conn.cursor()
    tbl  = f"isolated_proxy_log_{CRAWL_SUFFIX}"
    cur.execute(
        f"SELECT extension_id, proxy_data FROM {tbl} "
        f"WHERE dataset=%s AND url LIKE %s;",
        (DATASET, f'%{URL_FD_TARGETED}%')
    )
    rows = cur.fetchall()
    conn.close()

    dangerous_set    = set()
    nondangerous_set = set()

    for ext_id, proxy_data in rows:
        if not proxy_data or not ext_id:
            continue
        if isinstance(proxy_data, str):
            try:
                proxy_data = json.loads(proxy_data)
            except Exception:
                continue
        if not isinstance(proxy_data, list):
            continue
        hit_dangerous = False
        for entry in proxy_data:
            if not isinstance(entry, dict):
                continue
            ident = entry.get('identifier')
            if ident and is_dangerous_ident(ident):
                hit_dangerous = True
                break
        if hit_dangerous:
            dangerous_set.add(ext_id)
        else:
            nondangerous_set.add(ext_id)

    return dangerous_set, nondangerous_set


def coverage_by_url(url_frag, restrict_to=None):
    """Returns {visit: {ext_id: exec_bytes}} for CS scripts on the given URL."""
    rows = query_by_url('coverage_log', 'extension_id, visit, coverage', url_frag)
    result = defaultdict(dict)
    for ext_id, visit, cov_data in rows:
        if restrict_to and ext_id not in restrict_to:
            continue
        if not cov_data:
            continue
        classified = classify_coverage_scripts(cov_data, ext_id)
        cs_scripts = classified.get(SCRIPT_TYPE_CS, [])
        exec_bytes = sum(s[2] for s in cs_scripts if s[1] > 0)
        if exec_bytes > 0:
            result[visit][ext_id] = exec_bytes
    return result


def compute_fd(baseline_cov, attack_cov, restrict_to):
    """
    Strict 3-visit AND FD computation for restrict_to population.
    Each visit's attack is compared against that same visit's baseline,
    not a max-across-visits reference, to avoid cross-visit inflation.
    """
    visits = sorted(set(baseline_cov.keys()) & set(attack_cov.keys()))
    fd_by_visit = {}
    n_evaluated = set()
    for v in visits:
        b_map = baseline_cov[v]
        a_map = attack_cov[v]
        fd_set = set()
        for ext_id, b_bytes in b_map.items():
            if ext_id not in restrict_to:
                continue
            if b_bytes < MIN_EXEC_BYTES:
                continue
            n_evaluated.add(ext_id)
            a_bytes = a_map.get(ext_id, 0)
            if (b_bytes - a_bytes) / b_bytes > FD_THRESHOLD:
                fd_set.add(ext_id)
        fd_by_visit[v] = fd_set

    print(f"  Extensions evaluated in coverage (have CS bytes >= {MIN_EXEC_BYTES}): {len(n_evaluated)}")
    for v, s in sorted(fd_by_visit.items()):
        print(f"  Visit {v} FD count: {len(s)}")

    if len(fd_by_visit) < N_VISITS:
        return set()

    visit_list = sorted(fd_by_visit.keys())
    # Pairwise intersections to diagnose why strict AND may be empty
    for i in range(len(visit_list)):
        for j in range(i+1, len(visit_list)):
            va, vb = visit_list[i], visit_list[j]
            overlap = fd_by_visit[va] & fd_by_visit[vb]
            print(f"  Intersection visit {va} ∩ visit {vb}: {len(overlap)}")
            if overlap:
                print(f"    Sample: {list(overlap)[:3]}")

    strict = set.intersection(*fd_by_visit.values())
    print(f"  Sample visit-1 FD ext: {list(fd_by_visit[visit_list[0]])[:2]}")
    print(f"  Same ext in visit-2? {list(fd_by_visit[visit_list[0]])[:1][0] in fd_by_visit[visit_list[1]] if fd_by_visit[visit_list[0]] else 'N/A'}")
    return strict


def main():
    print(f"INA v3 Non-Dangerous FD — suffix={CRAWL_SUFFIX}")

    # Load existing FD strict set (518 selector-based)
    cov_path = OUT_DIR / 'ina_coverage_impact.json'
    if not cov_path.exists():
        print(f"ERROR: {cov_path} not found — run ina_coverage_impact.py first")
        sys.exit(1)
    existing_fd = set(json.load(open(cov_path))['fd_targeted']['strict_set'])
    print(f"  Existing FD strict set: {len(existing_fd)}")

    # Load dangerous source 3,210 set (corrected: getAttribute-aware)
    sink_path = Path(__file__).resolve().parent.parent.parent.parent / \
                'crawler' / 'extension_lists' / 'ina_sink_strict_3210.json'
    dangerous_3210 = set(json.load(open(sink_path))['extension_ids'])
    print(f"  Dangerous source strict set (3,210): {len(dangerous_3210)}")

    # Get proxy-based sets from targeted attack visits
    print("\nQuerying proxy log for property access sets...")
    dangerous_proxy, nondangerous_proxy = get_proxy_extension_sets()
    print(f"  Extensions with dangerous source access (proxy): {len(dangerous_proxy)}")
    print(f"  Extensions with non-dangerous access only:       {len(nondangerous_proxy)}")

    # Target: non-dangerous proxy set, excluding existing FD set
    target = nondangerous_proxy - existing_fd
    print(f"  Target (non-dangerous, not already in FD set):   {len(target)}")


    # Load coverage data restricted to target population
    print("\nLoading coverage data...")
    baseline_cov = coverage_by_url(URL_FD_BASELINE, restrict_to=target)
    attack_cov   = coverage_by_url(URL_FD_TARGETED, restrict_to=target)
    print(f"  Extensions with baseline coverage: {sum(len(v) for v in baseline_cov.values())}")
    print(f"  Extensions with attack coverage:   {sum(len(v) for v in attack_cov.values())}")

    # Compute FD
    print("\nComputing FD...")
    fd_strict = compute_fd(baseline_cov, attack_cov, restrict_to=target)
    print(f"  Non-dangerous FD strict (3-visit AND, >5%): {len(fd_strict)}")

    # Overlap with existing sets
    overlap_existing = fd_strict & existing_fd
    overlap_dangerous = fd_strict & dangerous_3210
    print(f"  Overlap with existing FD 518: {len(overlap_existing)}")
    print(f"  Overlap with dangerous source 3210: {len(overlap_dangerous)}")

    out = {
        'crawl_suffix': CRAWL_SUFFIX,
        'description': 'FD for extensions with non-dangerous proxy access only, not in existing FD set',
        'proxy_dangerous_count': len(dangerous_proxy),
        'proxy_nondangerous_count': len(nondangerous_proxy),
        'target_count': len(target),
        'fd_strict_count': len(fd_strict),
        'fd_strict_set': sorted(fd_strict),
        'overlap_with_existing_fd': len(overlap_existing),
        'overlap_with_dangerous_3210': len(overlap_dangerous),
    }
    out_path = OUT_DIR / 'ina_nondangerous_fd.json'
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
