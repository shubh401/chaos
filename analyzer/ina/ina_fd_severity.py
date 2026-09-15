import os, sys, json, traceback
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ina_helpers import (
    query_by_url, CRAWL_SUFFIX, N_VISITS,
    URL_FD_BASELINE, URL_FD_TARGETED,
    URL_GBS_BASELINE, URL_GBS_ATTACK,
    save_results,
)
from db_helpers import (
    classify_coverage_scripts, SCRIPT_TYPE_CS, get_connection, DATASET,
)

FD_THRESHOLD   = 0.05
MIN_EXEC_BYTES = 1024

OUT_DIR = Path(__file__).resolve().parent.parent.parent / 'results' / 'ina' / CRAWL_SUFFIX


def coverage_by_url(url_frag):
    """Returns {visit: {ext_id: exec_bytes}} for CS scripts on the given URL."""
    rows = query_by_url('coverage_log', 'extension_id, visit, coverage', url_frag)
    result = defaultdict(dict)
    for ext_id, visit, cov_data in rows:
        if not cov_data: continue
        classified = classify_coverage_scripts(cov_data, ext_id)
        cs_scripts = classified.get(SCRIPT_TYPE_CS, [])
        exec_bytes = sum(s[2] for s in cs_scripts if s[1] > 0)
        if exec_bytes > 0:
            result[visit][ext_id] = exec_bytes
    return result


def compute_deltas(baseline_cov, attack_cov_by_visit, restrict_to=None):
    """
    For each extension in restrict_to, compute average fractional delta:
      delta = (attack_bytes - baseline_bytes) / baseline_bytes
    Negative = killed, positive = expanded.
    Returns {ext_id: avg_delta}.
    """
    baseline = {}
    for visit_map in baseline_cov.values():
        for ext_id, eb in visit_map.items():
            if restrict_to and ext_id not in restrict_to:
                continue
            baseline[ext_id] = max(baseline.get(ext_id, 0), eb)

    visits = sorted(attack_cov_by_visit.keys())
    ext_deltas = defaultdict(list)

    for v in visits:
        attack = attack_cov_by_visit[v]
        for ext_id, b_bytes in baseline.items():
            if b_bytes < MIN_EXEC_BYTES:
                continue
            a_bytes = attack.get(ext_id, 0)
            delta = (a_bytes - b_bytes) / b_bytes
            ext_deltas[ext_id].append(delta)

    return {ext_id: sum(deltas) / len(deltas)
            for ext_id, deltas in ext_deltas.items()
            if len(deltas) == N_VISITS}


def bin_deltas(deltas, strict_set):
    """
    Bin extensions in strict_set by their average delta.
    Returns counts for killed (>50%, 20-50%, 5-20%) and expanded (5-20%, 20-50%, >50%).
    """
    bins = {
        'killed_gt50':    0,
        'killed_20_50':   0,
        'killed_5_20':    0,
        'expanded_5_20':  0,
        'expanded_20_50': 0,
        'expanded_gt50':  0,
        'no_data':        0,
    }
    for ext_id in strict_set:
        if ext_id not in deltas:
            bins['no_data'] += 1
            continue
        d = deltas[ext_id]
        if d < -0.50:
            bins['killed_gt50'] += 1
        elif d < -0.20:
            bins['killed_20_50'] += 1
        elif d < -FD_THRESHOLD:
            bins['killed_5_20'] += 1
        elif d > 0.50:
            bins['expanded_gt50'] += 1
        elif d > 0.20:
            bins['expanded_20_50'] += 1
        elif d > FD_THRESHOLD:
            bins['expanded_5_20'] += 1
        else:
            # delta between -5% and +5% but in strict set — should not happen
            # (strict requires |delta| > 5% in all 3 visits); log as no_data
            bins['no_data'] += 1
    return bins


def main():
    print(f"INA v3 FD Severity Distribution — suffix={CRAWL_SUFFIX}")

    # Load strict FD sets from existing result file
    cov_path = OUT_DIR / 'ina_coverage_impact.json'
    if not cov_path.exists():
        print(f"ERROR: {cov_path} not found — run ina_coverage_impact.py first")
        sys.exit(1)
    cov_data = json.load(open(cov_path))
    targeted_strict = set(cov_data['fd_targeted']['strict_set'])
    gbs_strict      = set(cov_data['fd_gbs']['strict_set'])
    gbs_only        = gbs_strict - targeted_strict
    combined_strict = targeted_strict | gbs_strict
    print(f"  Targeted strict: {len(targeted_strict)}")
    print(f"  GBS strict: {len(gbs_strict)}  (GBS-only new: {len(gbs_only)})")
    print(f"  Combined: {len(combined_strict)}")

    # GBS attack population
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT extension_id FROM extension_gbs_vars WHERE dataset=%s;", (DATASET,))
    gbs_attack_exts = {r[0] for r in cur.fetchall()}
    conn.close()

    # Targeted FD deltas
    print(f"\nLoading targeted baseline ({URL_FD_BASELINE})...")
    fd_baseline = coverage_by_url(URL_FD_BASELINE)
    print(f"Loading targeted attack ({URL_FD_TARGETED})...")
    fd_attack   = coverage_by_url(URL_FD_TARGETED)
    targeted_exts = set()
    for vm in fd_attack.values():
        targeted_exts.update(vm.keys())

    print("Computing targeted deltas...")
    targeted_deltas = compute_deltas(fd_baseline, fd_attack, restrict_to=targeted_exts)

    # GBS FD deltas
    print(f"\nLoading GBS baseline ({URL_GBS_BASELINE})...")
    gbs_baseline = coverage_by_url(URL_GBS_BASELINE)
    print(f"Loading GBS attack ({URL_GBS_ATTACK})...")
    gbs_attack_cov = coverage_by_url(URL_GBS_ATTACK)

    print("Computing GBS deltas...")
    gbs_deltas = compute_deltas(gbs_baseline, gbs_attack_cov, restrict_to=gbs_attack_exts)

    # Merge: GBS-only extensions use gbs_deltas; targeted use targeted_deltas
    combined_deltas = {**targeted_deltas}
    for ext_id in gbs_only:
        if ext_id in gbs_deltas:
            combined_deltas[ext_id] = gbs_deltas[ext_id]

    # Bin results
    targeted_bins = bin_deltas(targeted_deltas, targeted_strict)
    gbs_bins      = bin_deltas(gbs_deltas, gbs_strict)
    combined_bins = bin_deltas(combined_deltas, combined_strict)

    def print_bins(label, strict_n, b):
        print(f"\n  {label} (strict={strict_n})")
        print(f"    Killed >50%:     {b['killed_gt50']:>4}")
        print(f"    Killed 20-50%:   {b['killed_20_50']:>4}")
        print(f"    Killed 5-20%:    {b['killed_5_20']:>4}")
        print(f"    Expanded 5-20%:  {b['expanded_5_20']:>4}")
        print(f"    Expanded 20-50%: {b['expanded_20_50']:>4}")
        print(f"    Expanded >50%:   {b['expanded_gt50']:>4}")
        print(f"    No data:         {b['no_data']:>4}")
        total_k = b['killed_gt50'] + b['killed_20_50'] + b['killed_5_20']
        total_e = b['expanded_5_20'] + b['expanded_20_50'] + b['expanded_gt50']
        print(f"    → Total killed: {total_k}, expanded: {total_e}")

    print_bins("Targeted FD (selector-based)", len(targeted_strict), targeted_bins)
    print_bins("GBS FD", len(gbs_strict), gbs_bins)
    print_bins("Combined FD (targeted + GBS-only)", len(combined_strict), combined_bins)

    out = {
        'crawl_suffix': CRAWL_SUFFIX,
        'fd_targeted': {
            'strict_count': len(targeted_strict),
            'bins': targeted_bins,
        },
        'fd_gbs': {
            'strict_count': len(gbs_strict),
            'gbs_only_count': len(gbs_only),
            'bins': gbs_bins,
        },
        'combined': {
            'strict_count': len(combined_strict),
            'bins': combined_bins,
        },
    }
    out_path = OUT_DIR / 'ina_fd_severity.json'
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
