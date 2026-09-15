"""
update_seen_vars.py — Update seenVars in __cs_hook.js from variable_log frequency data.

Queries isolated_variable_log_{SUFFIX} across all extensions and identifies
variable names that appear in more than FREQ_THRESHOLD of the corpus.
These are browser built-ins that post-date the current seenVars snapshot.
Adds them to the seenVars Set in __cs_hook.js.

Run on the server from /root/ext-dos/:
    VAR_LOG_SUFFIX=2026_GBS_PRE DATASET=crx_2026-04-14 python static/src/update_seen_vars.py

After running, re-deploy the hooks:
    DATASET=crx_2026-04-14 python static/src/main.py --copy_hooks_only
    GBS_PRE_SUFFIX=2026_GBS_PRE DATASET=crx_2026-04-14 python static/src/main.py --copy_gbs_hooks
"""
import os, sys, json, re, traceback
from collections import Counter
from pathlib import Path

import psycopg2

SUFFIX    = os.getenv('VAR_LOG_SUFFIX', '2026_GBS_PRE')
DATASET   = os.getenv('DATASET', 'crx_2026-04-14')
DB_HOST   = os.getenv('DB_HOST', '127.0.0.1')
DB_USER   = os.getenv('DB_USER', 'dos_extensions')
DB_NAME   = os.getenv('DB_NAME', 'dos_extensions')
DB_PASS   = os.getenv('DB_PASS', '')

# Variables appearing in more than this fraction of corpus = browser built-in
FREQ_THRESHOLD = 0.50

HOOK_FILES = [
    Path('/root/ext-dos/static/src/hooks/__cs_hook_bkp.js'),
    Path('/root/ext-dos/static/src/hooks/__cs_hook.js'),
]


def get_variable_frequencies():
    """
    Query variable_log and count how many distinct extensions each variable
    name appears in. Returns {varname: count}.
    """
    conn = psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
    )
    cur = conn.cursor()
    table = f"isolated_variable_log_{SUFFIX}"

    print(f"Querying {table} for variable frequency...")
    try:
        cur.execute(
            f"SELECT DISTINCT extension_id, variables FROM {table} WHERE dataset = %s;",
            (DATASET,)
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    print(f"  {len(rows):,} rows loaded")

    # Count distinct extensions per variable name
    freq = Counter()
    n_extensions = len({r[0] for r in rows})

    for ext_id, var_data in rows:
        if not var_data: continue
        if isinstance(var_data, str):
            try: var_data = json.loads(var_data)
            except: continue
        if isinstance(var_data, dict):
            names = set(var_data.keys())
        elif isinstance(var_data, list):
            names = set(var_data)
        else:
            continue
        for name in names:
            freq[name] += 1

    return freq, n_extensions


def get_existing_seen_vars(hook_path: Path) -> set:
    """Parse existing seenVars from hook file."""
    content = hook_path.read_text(encoding='utf-8')
    start = content.find('window.seenVars = new Set([')
    if start == -1:
        raise ValueError(f"seenVars not found in {hook_path}")
    end = content.find(']);', start)
    block = content[start:end]
    return set(re.findall(r'"([^"]+)"', block))


def add_to_seen_vars(hook_path: Path, new_names: set) -> int:
    """
    Add new_names to the seenVars Set in the hook file.
    Inserts them as quoted strings just before the closing ]);
    Returns count of names actually added.
    """
    content = hook_path.read_text(encoding='utf-8')
    existing = get_existing_seen_vars(hook_path)
    to_add = sorted(new_names - existing)
    if not to_add:
        print(f"  {hook_path.name}: nothing to add")
        return 0

    # Find insertion point: just before the ]); that closes seenVars
    start = content.find('window.seenVars = new Set([')
    end = content.find(']);', start)

    # Build insertion string — match surrounding indentation (4 spaces)
    insertion = '\n'.join(f'    "{name}",' for name in to_add) + '\n'

    new_content = content[:end] + insertion + content[end:]
    hook_path.write_text(new_content, encoding='utf-8')
    print(f"  {hook_path.name}: added {len(to_add)} names")
    return len(to_add)


def main():
    print(f"update_seen_vars.py")
    print(f"  Suffix:    {SUFFIX}")
    print(f"  Dataset:   {DATASET}")
    print(f"  Threshold: >{FREQ_THRESHOLD*100:.0f}% of corpus")
    print()

    freq, n_extensions = get_variable_frequencies()
    print(f"  Total extensions in variable_log: {n_extensions:,}")
    print(f"  Unique variable names seen:       {len(freq):,}")
    print()

    # Identify high-frequency names = browser built-ins
    threshold_count = n_extensions * FREQ_THRESHOLD
    browser_globals = {name for name, count in freq.items()
                       if count >= threshold_count
                       and len(name) > 1
                       and not name.startswith('__')}

    print(f"Variables appearing in >{FREQ_THRESHOLD*100:.0f}% of extensions: {len(browser_globals)}")
    print(f"  (these are browser built-ins missing from seenVars)")

    # Get existing seenVars from first hook file
    existing = get_existing_seen_vars(HOOK_FILES[0])
    new_names = browser_globals - existing

    if not new_names:
        print("  seenVars is already up to date — nothing to add")
        return

    print(f"  New names to add to seenVars: {len(new_names)}")
    print(f"  Sample: {sorted(new_names)[:20]}")
    print()

    for hook_path in HOOK_FILES:
        if hook_path.exists():
            add_to_seen_vars(hook_path, new_names)
        else:
            print(f"  SKIP {hook_path} — not found")

    print()
    print(f"Done. seenVars updated with {len(new_names)} new browser globals.")
    print()
    print("Next steps:")
    print("  1. DATASET=crx_2026-04-14 python static/src/main.py --copy_hooks_only")
    print(f"  2. GBS_PRE_SUFFIX={SUFFIX} DATASET=crx_2026-04-14 python static/src/main.py --copy_gbs_hooks")


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
