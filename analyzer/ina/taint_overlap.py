import os, sys, json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import db_helpers as dbh

DATASET  = dbh.DATASET
OUT_DIR  = Path(__file__).resolve().parent.parent.parent / 'results' / 'ina' / 'taint'

def q(sql, *params):
    conn = dbh.get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(sql, params or None)
        return cur.fetchall()
    finally:
        conn.close()


def main():
    # Load dynamic confirmed set (123)
    suffix = os.getenv('TAINT_SUFFIX')
    taint2_path = OUT_DIR / f'dynamic_taint_summary_{suffix}.json'
    if not taint2_path.exists():
        print(f'ERROR: {taint2_path} not found')
        sys.exit(1)

    d2 = json.load(open(taint2_path))
    dynamic_confirmed = set(d2['strict']['combined_confirmed_set'])
    print(f'Dynamic confirmed set (taint2): {len(dynamic_confirmed)}')

    # Load static confirmed set from DB.
    # The DB was populated by the FIRST extractor run (before context-qualified
    # disambiguation). The updated extractor renamed ambiguous sinks:
    #   set → chrome.storage.set  or  set(unverified)
    #   assign → location.assign  or  assign(unverified)
    #   replace → location.replace or replace(unverified)
    #   create → chrome.tabs.create or create(unverified)
    #   update → chrome.tabs.update or update(unverified)
    #   open → XMLHttpRequest.open  or  open(unverified)
    # The DB also has pre-disambiguation names (no suffix).
    # We filter to ONLY the sinks that the updated extractor treats as
    # unambiguously verified — matching the 313 count in static_taint_summary.json.
    VERIFIED_SINKS = (
        # Network
        'fetch', 'send', 'sendBeacon',
        # Messaging
        'sendMessage', 'postMessage', 'sendNativeMessage',
        # Storage
        'setItem',
        # Eval-class
        'eval', 'write', 'writeln', 'setTimeout', 'setInterval',
        # DOM write (assignment targets)
        'innerHTML', 'outerHTML', 'textContent', 'innerText',
        'src', 'href', 'action', 'data',
        # Context-qualified (renamed by updated extractor)
        'location.assign', 'location.replace',
        'chrome.tabs.create', 'chrome.tabs.update',
        'chrome.storage.set', 'chrome.storage.local.set',
        'chrome.storage.sync.set',
        'XMLHttpRequest.open', 'open',
        'WebSocket',
    )
    placeholders = ','.join(['%s'] * len(VERIFIED_SINKS))
    rows = q(
        f"""SELECT DISTINCT extension_id
            FROM extension_taint_flows,
                 jsonb_array_elements(flows) AS flow
            WHERE dataset=%s
              AND flow->>'sink' IN ({placeholders});""",
        DATASET, *VERIFIED_SINKS
    )
    static_confirmed = {r[0] for r in rows}
    print(f'  (filtered to {len(VERIFIED_SINKS)} verified sink names matching updated extractor)')

    # Also compute narrow set: function call sinks only (no DOM property assignments)
    # DOM property assignments: innerHTML, outerHTML, textContent, innerText, src,
    # href, action, data — these are valid but weaker than function call sinks
    DOM_PROP_SINKS = {'innerHTML','outerHTML','textContent','innerText',
                      'src','href','action','data'}
    NARROW_SINKS = [s for s in VERIFIED_SINKS if s not in DOM_PROP_SINKS]
    narrow_ph = ','.join(['%s'] * len(NARROW_SINKS))
    narrow_rows = q(
        f"""SELECT DISTINCT extension_id
            FROM extension_taint_flows,
                 jsonb_array_elements(flows) AS flow
            WHERE dataset=%s
              AND flow->>'sink' IN ({narrow_ph});""",
        DATASET, *NARROW_SINKS
    )
    static_narrow = {r[0] for r in narrow_rows}
    print(f'  Narrow (function call sinks only, excl. DOM prop assignments): {len(static_narrow)}')

    # Show what's actually in the filtered set
    sink_dist = q(
        f"""SELECT flow->>'sink' AS sink, COUNT(DISTINCT extension_id)
            FROM extension_taint_flows,
                 jsonb_array_elements(flows) AS flow
            WHERE dataset=%s
              AND flow->>'sink' IN ({placeholders})
            GROUP BY 1 ORDER BY 2 DESC;""",
        DATASET, *VERIFIED_SINKS
    )
    print('  Verified sink distribution:')
    for sink, n in (sink_dist or []):
        print(f'    {int(n):>5}  {sink}')
    print(f'Static confirmed set (DB):      {len(static_confirmed)}')

    # Compute relationships — broad static (569)
    both        = dynamic_confirmed & static_confirmed
    dyn_only    = dynamic_confirmed - static_confirmed
    static_only = static_confirmed - dynamic_confirmed
    union       = dynamic_confirmed | static_confirmed

    # Compute relationships — narrow static (function call sinks only)
    both_n       = dynamic_confirmed & static_narrow
    dyn_only_n   = dynamic_confirmed - static_narrow
    static_only_n = static_narrow - dynamic_confirmed
    union_n      = dynamic_confirmed | static_narrow

    print()
    print('── Overlap analysis (broad static — includes DOM prop assignments) ──')
    print(f'  Both static AND dynamic:    {len(both):>5,}')
    print(f'  Dynamic only (not static):  {len(dyn_only):>5,}  ← dynamic found what static missed')
    print(f'  Static only (not dynamic):  {len(static_only):>5,}  ← static found what dynamic missed')
    print(f'  Union:                      {len(union):>5,}  ← total with any taint evidence')

    print()
    print('── Overlap analysis (narrow static — function call sinks only) ──')
    print(f'  Narrow static count:        {len(static_narrow):>5,}')
    print(f'  Both static AND dynamic:    {len(both_n):>5,}')
    print(f'  Dynamic only (not static):  {len(dyn_only_n):>5,}')
    print(f'  Static only (not dynamic):  {len(static_only_n):>5,}')
    print(f'  Union:                      {len(union_n):>5,}')

    # Load corrected 3,210 sink set
    sink_list_path = (Path(__file__).resolve().parent.parent.parent.parent /
                      'crawler' / 'extension_lists' / 'ina_sink_strict_3210.json')
    sink_3210 = set()
    if sink_list_path.exists():
        sink_3210 = set(json.load(open(sink_list_path))['extension_ids'])

    n_sink = len(sink_3210) if sink_3210 else 3210
    print()
    print(f'Relationship to {n_sink:,} exposure set (corrected, getAttribute-aware):')
    print(f'  {n_sink:,}  dangerous source property accessed (proxy signal)')
    print(f'  ├──  {len(union):>5,}  any taint evidence — broad (static DOM-prop OR dynamic)')
    print(f'  ├──  {len(union_n):>5,}  any taint evidence — narrow (function call sinks)')
    print(f'  ├──  {len(dynamic_confirmed):>5,}  dynamic confirmed (strict, instrumentation-clean)')
    print(f'  ├──    {len(both_n):>3,}  confirmed by BOTH narrow static + dynamic (strongest)')
    no_taint = (len(sink_3210 - dynamic_confirmed - static_confirmed)
                if sink_3210 else n_sink - len(union))
    print(f'  └──  {no_taint:>5,}  no taint evidence by either method')

    # read-only: accessed dangerous property but no sink reached
    if sink_3210:
        read_only = sink_3210 - dynamic_confirmed
        static_in_readonly = static_confirmed & read_only
        print()
        print(f'Read-only (dangerous property accessed, no dynamic sink reached): {len(read_only):,}')
        print(f'  {len(static_in_readonly):,} of those have static code paths')
        print(f'  → Likely: flow requires user interaction, or goes to unmonitored sink')

    out = {
        'dynamic_confirmed': len(dynamic_confirmed),
        'static_confirmed':  len(static_confirmed),
        'both':              len(both),
        'dynamic_only':      len(dyn_only),
        'static_only':       len(static_only),
        'union':             len(union),
        'dynamic_only_set':  sorted(dyn_only),
        'both_set':          sorted(both),
    }
    out_path = OUT_DIR / 'taint_overlap_analysis.json'
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f'\nSaved: {out_path}')


if __name__ == '__main__':
    main()
