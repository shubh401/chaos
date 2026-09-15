"""
codeql_select_files.py — Per-extension, per-signal file selection for the CodeQL
corpus-scale taint run.

Reuses db_helpers.py's load_scripts_table()/classify_script() (the SAME classification
logic already used elsewhere in this pipeline, e.g. ina_v3_coverage_impact.py,
sna_v2_recompute_fck_component.py) to select ONLY the signal-relevant on-disk files per
extension:
  - INA: SCRIPT_TYPE_CS only (content scripts — the isolated-world attack surface)
  - SNA: SCRIPT_TYPE_WAR only (main-world-injected scripts — the shared-namespace attack
    surface; SCRIPT_TYPE_INJECTED/SCRIPT_TYPE_EXTERNAL_WAR have no on-disk file path and
    are excluded here, not applicable to a source-file-based CodeQL database)

Deliberately does NOT include BG/WAR files for INA or CS/BG files for SNA — cross-component
data flow (CS -> WAR via postMessage, CS -> BG via chrome.runtime.sendMessage, and the SNA
equivalents) is captured by treating postMessage/sendMessage/sendNativeMessage as SINKS in
the taint query itself (already true in ext_taint.ql's DangerousSink vocabulary — these
calls literally ARE the boundary-crossing event), not by including the receiving
component's file in the same database. This keeps each database small, correctly scoped,
and free of cross-component name-collision risk (the exact problem the hand-rolled
extractor's scope-collision investigation identified) while still detecting when
signal-relevant code hands tainted data across a component boundary.

Output: one JSON per signal — {extension_id: [absolute_file_path, ...]}, skipping
extensions with zero relevant files (nothing to build a database from).

Usage (run from analyzer/):
    DATASET=crx_2026-04-14 python ina/codeql_pipeline/codeql_select_files.py \\
        --signal ina --extension-list crawler/extension_lists/ina_sink_strict_3210.json \\
        --out results/ina/taint/codeql_files_ina.json

    DATASET=crx_2026-04-14 python ina/codeql_pipeline/codeql_select_files.py \\
        --signal sna --extension-list <sna_677_list.json> \\
        --out results/ina/taint/codeql_files_sna.json
"""
import os, sys, json, argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import db_helpers as dbh

NS_DIR_TEMPLATE = '/datasets/{namespace}_namespace/basic/{dataset}/'

SIGNAL_TYPES = {
    'ina': {dbh.SCRIPT_TYPE_CS},
    'sna': {dbh.SCRIPT_TYPE_WAR},
}
SIGNAL_NAMESPACE = {
    'ina': 'isolated',
    'sna': 'shared',
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--signal', required=True, choices=['ina', 'sna'])
    parser.add_argument('--extension-list', required=True,
                         help='JSON with {"extension_ids": [...]}')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()

    dataset = dbh.DATASET
    ns_dir = NS_DIR_TEMPLATE.format(namespace=SIGNAL_NAMESPACE[args.signal], dataset=dataset)
    wanted_types = SIGNAL_TYPES[args.signal]

    ext_ids = set(json.loads(Path(args.extension_list).read_text())['extension_ids'])
    print(f"Signal: {args.signal}  |  Wanted script types: {wanted_types}  |  "
          f"Namespace dir: {ns_dir}")
    print(f"Extension list: {len(ext_ids):,} extensions")

    print("Loading scripts table (this may take a moment on first call)...")
    scripts_map = dbh.load_scripts_table()

    selected = {}
    n_no_scripts_row = 0
    n_no_matching_type = 0
    n_no_file_on_disk = 0
    for ext_id in sorted(ext_ids):
        ext_scripts = scripts_map.get(ext_id, {})
        if not ext_scripts:
            n_no_scripts_row += 1
            continue

        matching_rel_paths = [rel for rel, stype in ext_scripts.items() if stype in wanted_types]
        if not matching_rel_paths:
            n_no_matching_type += 1
            continue

        abs_paths = []
        ext_dir = os.path.join(ns_dir, ext_id)
        for rel in matching_rel_paths:
            abs_path = os.path.join(ext_dir, rel)
            if os.path.exists(abs_path):
                abs_paths.append(abs_path)
        if not abs_paths:
            n_no_file_on_disk += 1
            continue

        selected[ext_id] = abs_paths

    print(f"\nSelected: {len(selected):,} extensions with >=1 relevant, on-disk file")
    print(f"  Skipped — no 'scripts' table row at all: {n_no_scripts_row:,}")
    print(f"  Skipped — no script of type {wanted_types}: {n_no_matching_type:,}")
    print(f"  Skipped — matched type but file missing on disk: {n_no_file_on_disk:,}")
    total_files = sum(len(v) for v in selected.values())
    print(f"  Total files across all selected extensions: {total_files:,}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump({
            'signal': args.signal,
            'dataset': dataset,
            'wanted_script_types': sorted(wanted_types),
            'n_extensions_input': len(ext_ids),
            'n_extensions_selected': len(selected),
            'n_skipped_no_scripts_row': n_no_scripts_row,
            'n_skipped_no_matching_type': n_no_matching_type,
            'n_skipped_file_missing': n_no_file_on_disk,
            'files_by_extension': selected,
        }, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == '__main__':
    main()
