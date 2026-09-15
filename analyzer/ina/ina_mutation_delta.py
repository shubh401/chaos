import os, sys, json, traceback
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ina_helpers import (
    query_by_url, CRAWL_SUFFIX, N_VISITS, pairwise_jaccard,
    URL_FD_BASELINE, URL_FD_TARGETED,
    URL_GBS_BASELINE, URL_GBS_ATTACK,
    MIN_BASELINE_MUTATIONS, FRACTION_LOST_THRESHOLD,
    save_results,
)


def counts_from_url(url_frag):
    """Return {visit: Counter{ext_id: mutation_count}} for the given URL fragment."""
    rows = query_by_url('mutation_log', 'extension_id, visit', url_frag)
    result = defaultdict(Counter)
    for ext_id, visit in rows:
        result[visit][ext_id] += 1
    return result


def sf_analysis(baseline_counts, attack_counts_by_visit, label, restrict_to=None):
    """
    Compute SF for one attack URL against its corresponding baseline.

    restrict_to: optional set of extension IDs — only these are considered.
                 Used for GBS to scope to the 1,323 Crawl 3 extensions only,
                 avoiding the 53K Crawl 1 baseline polluting GBS SF numbers.

    SF is bidirectional: both suppression (fewer mutations — init skipped) and
    amplification (more mutations — error/retry paths) count as disruption,
    since both confirm the GBS clobber changed the extension's behavior.
    """
    # Use max count across baseline visits as the denominator
    baseline = {}
    for visit_counter in baseline_counts.values():
        for ext_id, count in visit_counter.items():
            if restrict_to and ext_id not in restrict_to:
                continue
            baseline[ext_id] = max(baseline.get(ext_id, 0), count)

    visits = sorted(attack_counts_by_visit.keys())
    sf_by_visit = {}
    for v in visits:
        attack = attack_counts_by_visit[v]
        sf_set = set()
        for ext_id, b_count in baseline.items():
            if b_count < MIN_BASELINE_MUTATIONS: continue
            a_count = attack.get(ext_id, 0)
            # Bidirectional: |baseline - attack| / baseline > threshold
            frac = abs(b_count - a_count) / b_count
            if frac > FRACTION_LOST_THRESHOLD:
                sf_set.add(ext_id)
        sf_by_visit[v] = sf_set

    consistency = pairwise_jaccard(sf_by_visit)
    strict = sf_by_visit[visits[0]].copy() if visits else set()
    for s in list(sf_by_visit.values())[1:]:
        strict &= s

    return {
        'label':        label,
        'per_visit':    {v: len(sf_by_visit[v]) for v in visits},
        'consistency':  consistency,
        'strict_count': len(strict),
        'strict_set':   sorted(strict),
    }


def main():
    print(f"INA v3 Mutation Delta — suffix={CRAWL_SUFFIX}")
    print()

    # ── SF Targeted (Crawl 1: type=baseline vs type=targeted) ─────────────
    print(f"Loading FD/SF targeted baseline ({URL_FD_BASELINE})...")
    fd_baseline = counts_from_url(URL_FD_BASELINE)
    n_fd_base = len(set().union(*[c.keys() for c in fd_baseline.values()])) if fd_baseline else 0
    print(f"  Extensions with baseline mutations: {n_fd_base:,}")

    print(f"Loading FD/SF targeted attack ({URL_FD_TARGETED})...")
    fd_attack = counts_from_url(URL_FD_TARGETED)

    print("Computing SF — targeted clobber...")
    sf_targeted = sf_analysis(fd_baseline, fd_attack, 'selector-based clobber (targeted)')

    # ── SF GBS (Crawl 2 baseline: type=baseline vs Crawl 3 attack: clobber_gbs_payload) ──
    # IMPORTANT: baseline URL is 'type=baseline' which has 53K extensions from Crawl 1.
    # Must restrict to only the 1,323 Crawl 3 attack extensions so we compare apples
    # to apples — GBS SF only applies to extensions that were actually attacked.
    print(f"\nLoading GBS attack extensions from extension_gbs_vars...")
    from db_helpers import get_connection, DATASET as _DS
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT extension_id FROM extension_gbs_vars WHERE dataset=%s;", (_DS,))
    gbs_attack_exts = {r[0] for r in cur.fetchall()}
    conn.close()
    print(f"  GBS attack population: {len(gbs_attack_exts):,} extensions")

    print(f"Loading GBS baseline ({URL_GBS_BASELINE}, scoped to GBS attack population)...")
    gbs_baseline = counts_from_url(URL_GBS_BASELINE)
    n_gbs_base = len({
        ext_id for c in gbs_baseline.values()
        for ext_id in c if ext_id in gbs_attack_exts
    })
    print(f"  Extensions with GBS baseline mutations: {n_gbs_base:,}")

    print(f"Loading GBS attack ({URL_GBS_ATTACK})...")
    gbs_attack = counts_from_url(URL_GBS_ATTACK)

    print("Computing SF — GBS clobber (bidirectional, scoped to GBS attack population)...")
    sf_gbs = sf_analysis(gbs_baseline, gbs_attack, 'GBS clobber', restrict_to=gbs_attack_exts)

    # Incremental: GBS SF not already caught by targeted SF
    targeted_strict = set(sf_targeted['strict_set'])
    gbs_strict      = set(sf_gbs['strict_set'])
    gbs_new         = gbs_strict - targeted_strict

    out = {
        'crawl_suffix': CRAWL_SUFFIX,
        'thresholds': {
            'min_baseline_mutations':  MIN_BASELINE_MUTATIONS,
            'fraction_lost_threshold': FRACTION_LOST_THRESHOLD,
        },
        'sf_targeted': sf_targeted,
        'sf_gbs':      sf_gbs,
        'incremental': {
            'gbs_only_strict': len(gbs_new),
            'gbs_only_set':    sorted(gbs_new),
            'note': 'GBS SF not already captured by targeted clobber SF',
        },
        'note': (
            f'v3 self-contained. '
            f'Targeted SF: {URL_FD_BASELINE} vs {URL_FD_TARGETED} (Crawl 1, ~19K extensions). '
            f'GBS SF: {URL_GBS_BASELINE} (Crawl 2) vs {URL_GBS_ATTACK} (Crawl 3, GBS candidates).'
        ),
    }
    save_results(out, 'ina_mutation_delta.json')

    print(f"\nSF targeted strict: {sf_targeted['strict_count']}")
    print(f"SF GBS strict:      {sf_gbs['strict_count']}")
    print(f"GBS-only new:       {len(gbs_new)}")


if __name__ == '__main__':
    try: main()
    except Exception: traceback.print_exc()
