"""
copy_taint_hooks.py — Deploy __cs_hook_taint.js to a specific set of extensions.

Copies __cs_hook_taint.js (which includes the extended sink hooks for taint
tracking) to each extension in the provided list, replacing the standard
__cs_hook.js. The standard hook can be restored afterward with
--copy_hooks_only via main.py.

Run from /root/ext-dos/:
    DATASET=crx_2026-04-14 \\
    EXTENSION_LIST=crawler/extension_lists/ina_sink_strict_1556.json \\
    python static/src/copy_taint_hooks.py

After the taint crawl completes, restore the standard hook:
    DATASET=crx_2026-04-14 python static/src/main.py --copy_hooks_only
"""
import os, sys, json, shutil, traceback
from pathlib import Path
from tqdm import tqdm

BASE_DIR   = Path(__file__).resolve().parents[2]
HOOKS_DIR  = Path(__file__).resolve().parent / 'hooks'
DATASET    = os.getenv('DATASET', 'crx_2026-04-14')
NS_DIR     = f'/datasets/isolated_namespace/basic/{DATASET}/'
LIST_FILE  = os.getenv(
    'EXTENSION_LIST',
    str(BASE_DIR / 'crawler' / 'extension_lists' / 'ina_sink_strict_1556.json')
)

TAINT_HOOK_SRC  = str(HOOKS_DIR / '__cs_hook_taint.js')
TARGET_NAME     = '__cs_hook.js'   # replaces the standard hook in the ext dir


def main():
    print(f"Deploying taint hook to extensions")
    print(f"  Source:     {TAINT_HOOK_SRC}")
    print(f"  Target:     {TARGET_NAME}")
    print(f"  List:       {LIST_FILE}")
    print(f"  NS_DIR:     {NS_DIR}")
    print()

    if not os.path.exists(TAINT_HOOK_SRC):
        print(f"ERROR: taint hook not found at {TAINT_HOOK_SRC}")
        sys.exit(1)

    # Load extension list
    if not os.path.exists(LIST_FILE):
        print(f"ERROR: extension list not found at {LIST_FILE}")
        sys.exit(1)

    data = json.load(open(LIST_FILE))
    if isinstance(data, list):
        ext_ids = data
    else:
        ext_ids = data.get('extension_ids', [])
    print(f"  Extensions in list: {len(ext_ids):,}")

    # Filter to those on disk
    on_disk = [e for e in ext_ids if os.path.isdir(os.path.join(NS_DIR, e))]
    missing = len(ext_ids) - len(on_disk)
    if missing:
        print(f"  WARNING: {missing} not on disk — skipping")
    print(f"  On disk: {len(on_disk):,}")
    print()

    deployed = 0
    failed   = 0

    with tqdm(total=len(on_disk), desc='Copying taint hook') as pbar:
        for ext_id in on_disk:
            target = os.path.join(NS_DIR, ext_id, TARGET_NAME)
            try:
                shutil.copy2(TAINT_HOOK_SRC, target)
                deployed += 1
            except Exception:
                traceback.print_exc()
                failed += 1
            pbar.update(1)

    print()
    print(f"Deployed: {deployed:,}  |  Failed: {failed:,}")
    print()
    print("After the taint crawl completes, restore the standard hook with:")
    print("  DATASET={} python static/src/main.py --copy_hooks_only".format(DATASET))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
