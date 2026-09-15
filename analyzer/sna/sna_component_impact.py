import os, sys, json, traceback
import numpy as np
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import db_helpers as dbh
from db_helpers import (
    DATASET, TEMPLATE_PAIRS, get_connection,
    classify_coverage_scripts, get_template_from_url,
    SCRIPT_TYPE_CS, SCRIPT_TYPE_WAR, SCRIPT_TYPE_BG,
    SCRIPT_TYPE_UNDECLARED, SCRIPT_TYPE_INJECTED,
)
from sna_helpers import CRAWL_SUFFIX, THRESHOLD

COMPONENT_GROUPS = {
    'war': {SCRIPT_TYPE_WAR, SCRIPT_TYPE_INJECTED},
    'cs':  {SCRIPT_TYPE_CS, SCRIPT_TYPE_UNDECLARED},
    'bg':  {SCRIPT_TYPE_BG},
}

# Which components are DIRECTLY targeted by each attack.
# Apples-to-apples: WAR kill severity uses WAR fck, CS uses CS fck, etc.
# event_swallow swallows events at window/document (main world) AND fires in
# isolated world listeners -> both WAR and CS are direct targets.
# raider clears storage that both WAR and CS read -> both direct.
ATTACK_DIRECT_COMPONENTS = {
    'hook':             {'war'},           # main-world API corruption
    'global_preassign': {'war'},           # pre-assigns window.X in main world
    'event_swallow':    {'war', 'cs'},     # events bridge both worlds directly
    'raider':           {'war', 'cs'},     # storage read by both worlds directly
    'proto_poison':     {'war', 'cs'},     # prototype chain shared across all worlds
}

ATTACKS = list(TEMPLATE_PAIRS.keys())
ATK_LABEL = {
    'hook':             'API Overwrites',
    'global_preassign': 'Variable Pollution',
    'event_swallow':    'Event Poisoning',
    'raider':           'State Cleanup',
    'proto_poison':     'Prototype Poisoning',
}


def load_coverage_by_visit_and_type():
    """
    Query shared_coverage_log and return:
      {visit: {ext_id: {template: {component: {script_url: (total, exec)}}}}}

    component is one of 'war', 'cs', 'bg'.
    """
    templates = set()
    for base_tmpl, break_tmpl in TEMPLATE_PAIRS.values():
        templates.add(base_tmpl)
        templates.add(break_tmpl)
    like_patterns = [f'%{t}%' for t in templates]

    print(f"  Querying shared_coverage_log_{CRAWL_SUFFIX} ...")
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        f"SELECT extension_id, visit, url, coverage "
        f"FROM shared_coverage_log_{CRAWL_SUFFIX} "
        f"WHERE dataset = %s AND url LIKE ANY(%s);",
        (DATASET, like_patterns)
    )
    rows = cur.fetchall()
    conn.close()
    print(f"  {len(rows):,} coverage rows")

    # {visit: {ext_id: {template: {component: {script_url: [(total, exec)]}}}}}
    raw = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))))

    for ext_id, visit, url, cov in rows:
        if not cov or not isinstance(cov, dict):
            continue
        template = get_template_from_url(url)
        classified = classify_coverage_scripts(cov, ext_id)
        for stype, scripts in classified.items():
            # Map to component group
            component = None
            for grp, types in COMPONENT_GROUPS.items():
                if stype in types:
                    component = grp
                    break
            if component is None:
                continue
            for script_url, total_len, exec_len, pct in scripts:
                if total_len and total_len > 0:
                    raw[visit][ext_id][template][component][script_url].append(
                        (total_len, exec_len or 0)
                    )

    visits = sorted(raw.keys())
    print(f"  Visits: {visits}")
    return dict(raw), visits


def compute_component_fck(raw, visits):
    """
    For each visit × extension × attack × component, compute fraction_code_killed
    using ONLY that component's bytes as denominator (apples-to-apples).
    Returns {visit: {ext_id: {attack: {component: fck}}}}
    """
    result = {}
    for visit in visits:
        visit_result = {}
        for ext_id, templates in raw[visit].items():
            ext_data = {}
            for attack, (baseline_tmpl, break_tmpl) in TEMPLATE_PAIRS.items():
                attack_data = {}
                for component in COMPONENT_GROUPS:
                    base_scripts = templates.get(baseline_tmpl, {}).get(component, {})
                    brk_scripts  = templates.get(break_tmpl, {}).get(component, {})
                    if not base_scripts and not brk_scripts:
                        continue

                    all_urls        = set(base_scripts) | set(brk_scripts)
                    total_bytes     = 0
                    total_exec_base = 0
                    total_exec_brk  = 0

                    for surl in all_urls:
                        b_entries = base_scripts.get(surl, [])
                        k_entries = brk_scripts.get(surl, [])
                        tlen = (b_entries or k_entries)[0][0]
                        total_bytes     += tlen
                        total_exec_base += (sum(e[1] for e in b_entries) / len(b_entries)
                                            if b_entries else 0.0)
                        total_exec_brk  += (sum(e[1] for e in k_entries) / len(k_entries)
                                            if k_entries else 0.0)

                    if total_bytes == 0:
                        continue
                    # Denominator = this component's bytes ONLY — apples-to-apples
                    fck = (total_exec_base - total_exec_brk) / total_bytes
                    attack_data[component] = round(fck, 6)

                if attack_data:
                    ext_data[attack] = attack_data
            if ext_data:
                visit_result[ext_id] = ext_data
        result[visit] = visit_result
        print(f"    Visit {visit}: {len(visit_result):,} extensions with component data")
    return result


def component_kill_severity(fck_by_visit, visits, component, attack, strict_set):
    """
    Compute kill severity buckets for a strict set of extensions using
    COMPONENT-SPECIFIC fck (same denominator across all rows being compared).

    strict_set: extensions that pass THRESHOLD in this component for this attack
                in ALL 3 visits.
    Returns {'>80': n, '50-80': n, '20-50': n, '5-20': n}
    """
    buckets = {'>80': 0, '50-80': 0, '20-50': 0, '5-20': 0}
    for ext_id in strict_set:
        visit_fcks = [
            fck_by_visit[v].get(ext_id, {}).get(attack, {}).get(component, 0)
            for v in visits
        ]
        median_fck = sorted(visit_fcks)[len(visit_fcks) // 2]
        if   median_fck > 0.80: buckets['>80']   += 1
        elif median_fck > 0.50: buckets['50-80'] += 1
        elif median_fck > 0.20: buckets['20-50'] += 1
        elif median_fck > 0.05: buckets['5-20']  += 1
    return buckets


def analyze():
    print(f"Loading coverage data for suffix={CRAWL_SUFFIX} ...")
    raw, visits = load_coverage_by_visit_and_type()

    print(f"\nComputing per-component, per-visit fraction_code_killed ...")
    fck_by_visit = compute_component_fck(raw, visits)

    # For each component × attack, compute strict affected set (all 3 visits)
    print(f"\nComputing strict affected sets per component ...")

    per_component_strict = {}
    per_component_pervisit = {}

    for component in COMPONENT_GROUPS:
        comp_strict = {}
        comp_pv     = {}
        for attack in ATTACKS:
            per_visit_sets = [
                {e for e, d in fck_by_visit[v].items()
                 if d.get(attack, {}).get(component, 0) > THRESHOLD}
                for v in visits
            ]
            strict  = set.intersection(*per_visit_sets) if per_visit_sets else set()
            union   = set.union(*per_visit_sets) if per_visit_sets else set()
            majority = {e for e in union
                        if sum(1 for s in per_visit_sets if e in s) >= 2}
            comp_strict[attack] = strict
            comp_pv[attack] = {
                'strict':   len(strict),
                'majority': len(majority),
                'union':    len(union),
                'per_visit': [len(s) for s in per_visit_sets],
            }
        per_component_strict[component] = comp_strict
        per_component_pervisit[component] = comp_pv

    # Print summary
    print(f"\n{'='*70}")
    print(f"  SNA v2 COMPONENT IMPACT — {CRAWL_SUFFIX}")
    print(f"{'='*70}")
    print(f"\n  {'Attack':<22}", end='')
    for comp in COMPONENT_GROUPS:
        print(f"  {comp.upper():>8} strict", end='')
    print(f"  {'COMBINED':>10}")
    print(f"  {'-'*22}", end='')
    for _ in COMPONENT_GROUPS:
        print(f"  {'----------':>14}", end='')
    print(f"  {'----------':>10}")

    # Load combined strict for comparison
    from sna_helpers import load_coverage_by_visit
    combined_pv = load_coverage_by_visit()
    combined_visits = sorted(combined_pv.keys())
    combined_strict = {}
    for attack in ATTACKS:
        per_v = [{e for e,d in combined_pv[v].items()
                  if d.get(attack,{}).get('fraction_code_killed',0) > THRESHOLD}
                 for v in combined_visits]
        combined_strict[attack] = len(set.intersection(*per_v))

    for attack in ATTACKS:
        print(f"  {ATK_LABEL[attack]:<22}", end='')
        for comp in COMPONENT_GROUPS:
            n = len(per_component_strict[comp][attack])
            print(f"  {n:>14,}", end='')
        print(f"  {combined_strict[attack]:>10,}")

    # ── Kill severity: apples-to-apples per component ─────────────────────────
    # Each row uses COMPONENT-SPECIFIC fck (WAR fck for WAR rows, CS fck for CS)
    # so kill magnitudes are directly comparable across attacks within each component.
    # Also shows direct vs indirect effect per attack (corrected classification).
    kill_sev = {}  # {component: {attack: buckets}}
    for comp in COMPONENT_GROUPS:
        kill_sev[comp] = {}
        for attack in ATTACKS:
            strict_set = per_component_strict[comp][attack]
            kill_sev[comp][attack] = component_kill_severity(
                fck_by_visit, visits, comp, attack, strict_set
            )

    print(f"\n  {'='*80}")
    print(f"  KILL SEVERITY — COMPONENT-SPECIFIC FCK (apples-to-apples)")
    print(f"  Each row uses ONLY that component's bytes as denominator.")
    print(f"  direct/indirect per attack:")
    print(f"    hook/global_preassign: WAR=direct, CS=indirect")
    print(f"    event_swallow/raider:  WAR=direct, CS=direct (both worlds)")
    print(f"    proto_poison:          WAR=direct, CS=direct (shared prototype)")
    print(f"  {'='*80}")
    print()

    for comp in ['war', 'cs', 'bg']:
        comp_label = comp.upper()
        print(f"  --- {comp_label} scripts ---")
        print(f"  {'Attack':<22}  {'Effect':<10}  {'n':>5}  {'>80%':>6}  {'50-80%':>7}  {'20-50%':>7}  {'5-20%':>6}")
        for attack in ATTACKS:
            strict_set = per_component_strict[comp][attack]
            if not strict_set:
                continue
            b      = kill_sev[comp][attack]
            effect = 'direct' if comp in ATTACK_DIRECT_COMPONENTS[attack] else 'indirect'
            n      = len(strict_set)
            print(f"  {ATK_LABEL[attack]:<22}  {effect:<10}  {n:>5}  "
                  f"{b['>80']:>6}  {b['50-80']:>7}  {b['20-50']:>7}  {b['5-20']:>6}")
        print()

    # Cross-world simultaneous kill
    print(f"  --- Cross-world (WAR ∩ CS both strict) ---")
    for attack in ATTACKS:
        war_s = per_component_strict['war'][attack]
        cs_s  = per_component_strict['cs'][attack]
        cross = len(war_s & cs_s)
        if cross > 0:
            print(f"  {ATK_LABEL[attack]:<22}  WAR∩CS={cross:>4}  (killed in both worlds simultaneously)")

    # Overall dedup
    # Load consistency report for the deduplicated strict_any_attack set
    _results_dir = Path(__file__).resolve().parent.parent.parent / \
                   'results' / 'sna' / CRAWL_SUFFIX
    _cr_path = _results_dir / 'sna_consistency_report.json'
    _cr = json.load(open(_cr_path)) if _cr_path.exists() else {}
    strict_any = set(_cr.get('strict_any_attack', []))
    if not strict_any:
        # Compute from component strict sets
        for comp in COMPONENT_GROUPS:
            for attack in ATTACKS:
                strict_any |= per_component_strict[comp][attack]
    # Use combined fck for overall summary
    from sna_helpers import load_coverage_by_visit
    combined_pv = load_coverage_by_visit()
    combined_visits = sorted(combined_pv.keys())
    ov_buckets = {'>80':0,'50-80':0,'20-50':0,'5-20':0}
    for ext_id in strict_any:
        max_m = 0
        for attack in ATTACKS:
            vals = [combined_pv[v].get(ext_id,{}).get(attack,{}).get('fraction_code_killed',0)
                    for v in combined_visits]
            max_m = max(max_m, sorted(vals)[len(vals)//2])
        if   max_m > 0.80: ov_buckets['>80']   += 1
        elif max_m > 0.50: ov_buckets['50-80'] += 1
        elif max_m > 0.20: ov_buckets['20-50'] += 1
        elif max_m > 0.05: ov_buckets['5-20']  += 1
    print(f"\n  {'Overall (dedup strict)':<22}  {'':10}  {len(strict_any):>5}  "
          f"{ov_buckets['>80']:>6}  {ov_buckets['50-80']:>7}  {ov_buckets['20-50']:>7}  {ov_buckets['5-20']:>6}")

    # WAR vs CS ratio analysis (kept for reference)
    v1_ratios = {'hook':1.5, 'global_preassign':1.3, 'event_swallow':0.5,
                 'raider':0.6, 'proto_poison':0.8}
    print(f"\n  WAR/CS ratio (strict) — scale of direct vs cross-world effect:")
    print(f"  {'Attack':<22}  {'WAR':>6}  {'CS':>6}  {'Ratio':>6}  {'v1':>5}")
    for attack in ATTACKS:
        war_n = len(per_component_strict['war'][attack])
        cs_n  = len(per_component_strict['cs'][attack])
        ratio = war_n / cs_n if cs_n > 0 else 0
        v1r   = v1_ratios[attack]
        direction = '↑' if ratio > v1r * 1.1 else ('↓' if ratio < v1r * 0.9 else '~')
        print(f"  {ATK_LABEL[attack]:<22}  {war_n:>6}  {cs_n:>6}  {ratio:>6.1f}  {v1r:>5.1f}{direction}")

    # Attack-appropriate denominator: refined strict counts using only
    # the script type the attack is designed to affect.
    # hook / global_preassign → WAR (main world, directly corrupted)
    # event_swallow / raider  → CS  (isolated world, indirectly affected)
    # proto_poison            → ALL (prototype chain shared across all worlds)
    ATTACK_DENOMINATOR = {
        'hook':             'war',
        'global_preassign': 'war',
        'event_swallow':    'cs',
        'raider':           'cs',
        'proto_poison':     None,   # None = use combined (all scripts)
    }

    print(f"\n  {'='*70}")
    print(f"  ATTACK-APPROPRIATE DENOMINATOR (primary recommended metric)")
    print(f"  {'='*70}")
    print(f"  Rationale: only count kill in the script type the attack targets.")
    print(f"  hook/global_preassign → WAR scripts (main world targets)")
    print(f"  event_swallow/raider  → CS scripts (isolated world targets)")
    print(f"  proto_poison          → ALL scripts (shared prototype chain)")
    print()
    print(f"  {'Attack':<22}  {'Target':>6}  {'Refined strict':>14}  {'Combined strict':>16}  {'Δ':>5}")
    for attack in ATTACKS:
        target_comp = ATTACK_DENOMINATOR[attack]
        if target_comp is None:
            refined_n = combined_strict[attack]
            target_lbl = 'ALL'
        else:
            refined_n = len(per_component_strict[target_comp][attack])
            target_lbl = target_comp.upper()
        delta = refined_n - combined_strict[attack]
        sign  = '+' if delta > 0 else ''
        print(f"  {ATK_LABEL[attack]:<22}  {target_lbl:>6}  {refined_n:>14,}  {combined_strict[attack]:>16,}  {sign}{delta:>4}")

    # BG impact (small population but high severity)
    bg_total = sum(len(per_component_strict['bg'][a]) for a in ATTACKS)
    if bg_total > 0:
        print(f"\n  BG/service worker impact (small but high severity when present):")
        for attack in ATTACKS:
            n = len(per_component_strict['bg'][attack])
            if n > 0:
                bg_fracs = []
                for v in visits:
                    for ext_id, d in fck_by_visit[v].items():
                        if d.get(attack, {}).get('bg', 0) > THRESHOLD:
                            bg_fracs.append(d[attack]['bg'])
                med = np.median(bg_fracs) * 100 if bg_fracs else 0
                print(f"    {ATK_LABEL[attack]:<22}: {n} extensions  median_fck={med:.1f}%")

    # Per-extension component fck: median across visits, for strict set only
    # Stored so downstream analysis can use component-specific fck directly
    per_ext_component_fck = {}
    for comp in COMPONENT_GROUPS:
        per_ext_component_fck[comp] = {}
        for attack in ATTACKS:
            strict_set = per_component_strict[comp][attack]
            per_ext_component_fck[comp][attack] = {
                ext_id: round(sorted(
                    [fck_by_visit[v].get(ext_id, {}).get(attack, {}).get(comp, 0)
                     for v in visits]
                )[len(visits) // 2], 6)
                for ext_id in strict_set
            }

    # Build output
    out = {
        'crawl_suffix': CRAWL_SUFFIX,
        'threshold': THRESHOLD,
        'visits': visits,
        'attack_direct_components': {k: sorted(v) for k, v in ATTACK_DIRECT_COMPONENTS.items()},
        'per_component': {
            comp: {
                attack: {
                    'strict':     len(per_component_strict[comp][attack]),
                    'strict_set': sorted(per_component_strict[comp][attack]),
                    'kill_severity_component_fck': kill_sev[comp][attack],
                    'is_direct':  comp in ATTACK_DIRECT_COMPONENTS[attack],
                    **per_component_pervisit[comp][attack],
                }
                for attack in ATTACKS
            }
            for comp in COMPONENT_GROUPS
        },
        'per_ext_component_fck': per_ext_component_fck,
        'attack_appropriate': {
            attack: {
                'target_component': ATTACK_DENOMINATOR[attack] or 'all',
                'strict': (len(per_component_strict[ATTACK_DENOMINATOR[attack]][attack])
                           if ATTACK_DENOMINATOR[attack] else combined_strict[attack]),
                'combined_strict': combined_strict[attack],
                'reasoning': (
                    'WAR = main world, directly corrupted by main-world API/global attacks'
                    if ATTACK_DENOMINATOR[attack] == 'war' else
                    'CS = isolated world, target of event/storage attacks'
                    if ATTACK_DENOMINATOR[attack] == 'cs' else
                    'ALL = prototype chain shared across all JS worlds'
                ),
            }
            for attack in ATTACKS
        },
        'war_cs_ratio': {
            attack: {
                'war_strict': len(per_component_strict['war'][attack]),
                'cs_strict':  len(per_component_strict['cs'][attack]),
                'ratio': round(len(per_component_strict['war'][attack]) /
                               max(len(per_component_strict['cs'][attack]), 1), 3),
                'v1_ratio': v1_ratios[attack],
            }
            for attack in ATTACKS
        },
        'note': (
            'WAR = scripts in MAIN world (directly affected by SNA). '
            'CS = isolated world scripts (indirectly affected via DOM/events). '
            'ratio > 1 means WAR more affected than CS (confirms direct attack). '
            'ratio < 1 means CS more affected (indicates cross-world propagation).'
        ),
    }
    return out


def main():
    try:
        out = analyze()
        results_dir = Path(__file__).resolve().parent.parent.parent / \
                      'results' / 'sna' / CRAWL_SUFFIX
        results_dir.mkdir(parents=True, exist_ok=True)
        out_path = results_dir / 'sna_component_impact.json'
        with open(out_path, 'w') as f:
            json.dump(out, f, indent=2)
        print(f"\nSaved: {out_path}")
    except Exception:
        traceback.print_exc()


if __name__ == '__main__':
    main()
