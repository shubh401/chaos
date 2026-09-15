import os, sys, json, traceback
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ina_helpers import (
    query_by_url, CRAWL_SUFFIX, N_VISITS, pairwise_jaccard,
    URL_FD_BASELINE, URL_FD_TARGETED,
    URL_GBS_BASELINE, URL_GBS_ATTACK,
    save_results,
)
from db_helpers import (
    classify_coverage_scripts, SCRIPT_TYPE_CS, get_connection, DATASET,
)

FD_THRESHOLD   = 0.05
MIN_EXEC_BYTES = 1024


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


def fd_analysis(baseline_cov, attack_cov_by_visit, label, restrict_to=None):
    """
    Compute FD for one attack URL against its corresponding baseline.

    restrict_to: optional set of extension IDs — only these are considered.
                 Critical for GBS FD: baseline URL is shared with Crawl 1 (53K
                 extensions), so without restriction the GBS FD would compare
                 1,323 attacked extensions against a 53K-extension baseline,
                 inflating the FD count massively.
    """
    baseline = {}
    for visit_map in baseline_cov.values():
        for ext_id, eb in visit_map.items():
            if restrict_to and ext_id not in restrict_to:
                continue
            baseline[ext_id] = max(baseline.get(ext_id, 0), eb)

    visits = sorted(attack_cov_by_visit.keys())
    fd_by_visit = {}
    for v in visits:
        attack = attack_cov_by_visit[v]
        fd_set = set()
        for ext_id, b_bytes in baseline.items():
            if b_bytes < MIN_EXEC_BYTES: continue
            a_bytes = attack.get(ext_id, 0)
            if (b_bytes - a_bytes) / b_bytes > FD_THRESHOLD:
                fd_set.add(ext_id)
        fd_by_visit[v] = fd_set

    consistency = pairwise_jaccard(fd_by_visit)
    strict = fd_by_visit[visits[0]].copy() if visits else set()
    for s in list(fd_by_visit.values())[1:]:
        strict &= s

    return {
        'label':        label,
        'per_visit':    {v: len(fd_by_visit[v]) for v in visits},
        'consistency':  consistency,
        'strict_count': len(strict),
        'strict_set':   sorted(strict),
    }


def main():
    print(f"INA v3 Coverage Impact — suffix={CRAWL_SUFFIX}")
    print()

    # ── Load population sets for scoping ──────────────────────────────────
    # Targeted FD: restrict to extensions that have a clobber payload AND
    # appear in the attack coverage (have_targeted_rows). Using attack coverage
    # keys as restrict_to ensures we only score extensions that were actually attacked.
    # GBS FD: restrict to the 1,323 extension_gbs_vars population.
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT extension_id FROM extension_gbs_vars WHERE dataset=%s;", (DATASET,))
    gbs_attack_exts = {r[0] for r in cur.fetchall()}
    conn.close()
    print(f"GBS attack population: {len(gbs_attack_exts):,} extensions")

    # ── FD Targeted (Crawl 1) ──────────────────────────────────────────────
    print(f"\nLoading targeted baseline coverage ({URL_FD_BASELINE})...")
    fd_baseline = coverage_by_url(URL_FD_BASELINE)
    print(f"  Baseline visits: {sorted(fd_baseline.keys())}")

    print(f"Loading targeted attack coverage ({URL_FD_TARGETED})...")
    fd_attack = coverage_by_url(URL_FD_TARGETED)

    # Targeted FD: scope baseline to extensions that actually appear in the attack
    # coverage — avoids scoring extensions that were never given a targeted payload
    targeted_exts = set()
    for visit_map in fd_attack.values():
        targeted_exts.update(visit_map.keys())
    print(f"  Targeted attack population: {len(targeted_exts):,} extensions")

    print("Computing FD — targeted clobber (scoped to attacked extensions)...")
    fd_targeted = fd_analysis(fd_baseline, fd_attack, 'selector-based clobber (targeted)',
                              restrict_to=targeted_exts)

    # ── FD GBS (Crawl 2 baseline + Crawl 3 attack) ────────────────────────
    print(f"\nLoading GBS baseline coverage ({URL_GBS_BASELINE}, scoped to GBS population)...")
    gbs_baseline = coverage_by_url(URL_GBS_BASELINE)
    print(f"  GBS baseline visits: {sorted(gbs_baseline.keys())}")

    print(f"Loading GBS attack coverage ({URL_GBS_ATTACK})...")
    gbs_attack_cov = coverage_by_url(URL_GBS_ATTACK)

    print("Computing FD — GBS clobber (scoped to GBS attack population)...")
    fd_gbs = fd_analysis(gbs_baseline, gbs_attack_cov, 'GBS clobber',
                         restrict_to=gbs_attack_exts)

    targeted_strict = set(fd_targeted['strict_set'])
    gbs_strict      = set(fd_gbs['strict_set'])
    gbs_new         = gbs_strict - targeted_strict


    out = {
        'crawl_suffix':   CRAWL_SUFFIX,
        'fd_threshold':   FD_THRESHOLD,
        'min_exec_bytes': MIN_EXEC_BYTES,
        'fd_targeted':    fd_targeted,
        'fd_gbs':         fd_gbs,
        'incremental': {
            'gbs_only_strict': len(gbs_new),
            'gbs_only_set':    sorted(gbs_new),
        },
        'note': (
            f'v3 self-contained. '
            f'Targeted FD: {URL_FD_BASELINE} vs {URL_FD_TARGETED} (Crawl 1). '
            f'GBS FD: {URL_GBS_BASELINE} (Crawl 2) vs {URL_GBS_ATTACK} (Crawl 3).'
        ),
    }
    save_results(out, 'ina_coverage_impact.json')

    print(f"\nFD targeted strict: {fd_targeted['strict_count']}")
    print(f"FD GBS strict:      {fd_gbs['strict_count']}")
    print(f"GBS-only new:       {len(gbs_new)}")


if __name__ == '__main__':
    try: main()
    except Exception: traceback.print_exc()
