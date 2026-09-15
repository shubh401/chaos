import os, sys, json, re
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import db_helpers as dbh

SUFFIX  = os.getenv('INA_SUFFIX')
DATASET = dbh.DATASET
OUT_DIR = Path(__file__).resolve().parent.parent.parent / 'results' / 'ina'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Known bundler/framework global patterns ───────────────────────────────────
# These are window.X names that are artifacts of build tools, not app logic.
# Extensions using these guards are following a bundler template, not deliberately
# designing a namespace — which makes them more vulnerable (less intentional).
BUNDLER_PATTERNS = [
    # Webpack
    re.compile(r'^webpackChunk'),
    re.compile(r'^__webpack_'),
    re.compile(r'^webpackJsonp'),
    # RequireJS / AMD
    re.compile(r'^require$'),
    re.compile(r'^define$'),
    re.compile(r'^requirejs$'),
    # jQuery / Zepto
    re.compile(r'^jQuery$'),
    re.compile(r'^\$$'),
    re.compile(r'^Zepto$'),
    # Angular
    re.compile(r'^angular$'),
    re.compile(r'^ng[A-Z]'),
    # React / Redux
    re.compile(r'^React$'),
    re.compile(r'^ReactDOM$'),
    re.compile(r'^Redux$'),
    # Generic module patterns
    re.compile(r'^module$'),
    re.compile(r'^exports$'),
    re.compile(r'^global$'),
]

# Generic namespace patterns (app-level, not bundler — still a structural smell)
GENERIC_NAMESPACE_PATTERNS = [
    re.compile(r'^app$', re.I),
    re.compile(r'^config$', re.I),
    re.compile(r'^settings$', re.I),
    re.compile(r'^options$', re.I),
    re.compile(r'^globals?$', re.I),
    re.compile(r'^namespace$', re.I),
    re.compile(r'^utils?$', re.I),
    re.compile(r'^helpers?$', re.I),
    re.compile(r'^core$', re.I),
    re.compile(r'^main$', re.I),
    re.compile(r'^init$', re.I),
    re.compile(r'^state$', re.I),
    re.compile(r'^store$', re.I),
    re.compile(r'^data$', re.I),
    re.compile(r'^cache$', re.I),
]


def classify_var(name):
    for pat in BUNDLER_PATTERNS:
        if pat.search(name):
            return 'bundler'
    for pat in GENERIC_NAMESPACE_PATTERNS:
        if pat.search(name):
            return 'generic_namespace'
    # Extension-specific: camelCase or PascalCase with meaningful prefix
    if re.match(r'^[A-Z][a-zA-Z0-9]{3,}$', name):
        return 'extension_specific_pascal'
    if re.match(r'^[a-z][a-zA-Z0-9]{3,}[A-Z][a-zA-Z0-9]*$', name):
        return 'extension_specific_camel'
    if len(name) <= 3:
        return 'short_ambiguous'
    return 'extension_specific'


def q(sql, *params):
    conn = dbh.get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(sql, params or None)
        return cur.fetchall()
    except Exception as e:
        print(f'  DB ERROR: {e}')
        return []
    finally:
        conn.close()


def sep(w=65): print('─' * w)
def section(t): print(); sep(); print(f'  {t}'); sep()


# ─────────────────────────────────────────────────────────────────────────────
# Analysis A — GBS variable distribution
# ─────────────────────────────────────────────────────────────────────────────

def analyze_gbs_variables():
    section('A. GBS VARIABLE DISTRIBUTION')

    rows = q(
        "SELECT extension_id, var_names FROM extension_gbs_vars WHERE dataset=%s;",
        DATASET
    )
    if not rows:
        print('  extension_gbs_vars is empty or not found')
        return {}

    print(f'  Extensions in extension_gbs_vars: {len(rows):,}')

    var_freq      = Counter()   # how many extensions use each variable name
    ext_var_count = Counter()   # how many variables per extension
    category_ext  = defaultdict(set)  # category -> set of extension_ids
    all_vars_by_ext = {}

    for ext_id, var_names in rows:
        if not var_names: continue
        if isinstance(var_names, str):
            try: var_names = json.loads(var_names)
            except: continue
        if not isinstance(var_names, list): continue

        all_vars_by_ext[ext_id] = var_names
        ext_var_count[ext_id] = len(var_names)

        for v in var_names:
            var_freq[v] += 1
            cat = classify_var(v)
            category_ext[cat].add(ext_id)

    print(f'  Total unique variable names: {len(var_freq):,}')
    print(f'  Total variable instances:    {sum(var_freq.values()):,}')
    print(f'  Mean vars per extension:     {sum(ext_var_count.values())/max(len(ext_var_count),1):.1f}')
    print()

    # Category breakdown
    print('  Classification:')
    for cat in ['bundler', 'generic_namespace', 'extension_specific_pascal',
                'extension_specific_camel', 'extension_specific', 'short_ambiguous']:
        n = len(category_ext.get(cat, set()))
        pct = n / len(rows) * 100 if rows else 0
        print(f'    {cat:<35} {n:>5,} extensions ({pct:.1f}%)')

    bundler_exts = category_ext.get('bundler', set())
    print()
    print(f'  Bundler-artifact extensions: {len(bundler_exts):,} ({len(bundler_exts)/len(rows)*100:.1f}%)')
    print(f'  Note: these extensions use webpack/require/jQuery globals — ')
    print(f'  the GBS guard is from a bundler template, not intentional app design.')

    # Top variable names
    print()
    print('  Top 30 variable names (by corpus frequency):')
    for var, n in var_freq.most_common(30):
        cat = classify_var(var)
        print(f'    {n:>5,}  {var:<40} [{cat}]')

    # Bundler-specific top vars
    bundler_vars = [(v, n) for v, n in var_freq.most_common()
                   if classify_var(v) == 'bundler']
    if bundler_vars:
        print()
        print('  Bundler artifact variables (top 10):')
        for var, n in bundler_vars[:10]:
            print(f'    {n:>5,}  {var}')

    # Shared variables (appear in many extensions — cross-extension pattern)
    print()
    print('  Variables shared across ≥10 extensions (cross-extension pattern):')
    shared = [(v, n) for v, n in var_freq.most_common() if n >= 10]
    for var, n in shared[:20]:
        cat = classify_var(var)
        print(f'    {n:>5,}  {var:<40} [{cat}]')

    # Per-variable extension ID sets for the top shared variables
    var_ext_map = defaultdict(set)
    for ext_id, var_names in all_vars_by_ext.items():
        for v in var_names:
            var_ext_map[v].add(ext_id)

    # 5-element payload coverage
    payload_5_vars = ['jQuery', '_sentryDebugIds', 'saveAs', 'webpackJsonp', '_babelPolyfill']
    payload_5_exts = set()
    for v in payload_5_vars:
        payload_5_exts |= var_ext_map.get(v, set())

    print()
    print(f'  5-element payload coverage: {len(payload_5_exts):,} extensions')
    for v in payload_5_vars:
        n = len(var_ext_map.get(v, set()))
        print(f'    {n:>5}  {v}')

    return {
        'total_extensions':   len(rows),
        'total_unique_vars':  len(var_freq),
        'top_vars':           var_freq.most_common(50),
        'category_counts':    {cat: len(exts) for cat, exts in category_ext.items()},
        'bundler_extensions': sorted(bundler_exts),
        'bundler_var_names':  [v for v, _ in bundler_vars[:20]],
        'shared_vars_ge10':   [(v, n) for v, n in var_freq.most_common() if n >= 10],
        # Per-variable extension ID sets for top shared vars
        'var_extension_ids': {
            v: sorted(var_ext_map[v])
            for v, _ in var_freq.most_common(30)
            if len(var_ext_map[v]) >= 5
        },
        # Multi-variable payload coverage sets
        'payload_5_element': {
            'vars':       payload_5_vars,
            'extensions': sorted(payload_5_exts),
            'count':      len(payload_5_exts),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Analysis B — Dangerous sink selector distribution
# ─────────────────────────────────────────────────────────────────────────────

def parse_proxy_entry(entry):
    """
    Extract (method, selector, property) from a proxy_data entry.
    The identifier field format from __cs_hook.js __makeProxy is:
      querySelector(".selector").property
      querySelector(".selector")("arg")
      getElementById("id").property
      getElementsByTagName("tag").N.property
    No 'Document.' prefix — that was added only in the analysis regex, not the hook.
    """
    if not isinstance(entry, dict):
        return None, None, None

    # Try direct identifier field first
    ident = entry.get('identifier', '')

    # Also check ops chain for old_identifier (proxied sub-property)
    if not ident and entry.get('ops'):
        ops = entry['ops']
        if isinstance(ops, list) and ops:
            ident = ops[0].get('old_identifier', '')

    if not ident:
        return None, None, None

    # Match: querySelector(".selector") or getElementById("id") etc.
    # Format: methodName("arg") OR methodName("arg").N for collections
    METHOD_RE = re.compile(
        r'(querySelector(?:All)?|getElementById|getElementsBy(?:TagName|ClassName|Name))'
        r'\("([^"]+)"\)'
    )
    m = METHOD_RE.search(ident)
    method   = m.group(1) if m else None
    selector = m.group(2) if m else None

    # Extract the terminal property (last .propName before end or before next call)
    # e.g. querySelector(".x").href  → href
    #      querySelector(".x").getAttribute("href")  → getAttribute("href")
    PROP_RE = re.compile(
        r'\.(href|src|action|formaction|innerHTML|outerHTML|insertAdjacentHTML'
        r'|textContent|innerText|value|location|data|setAttribute|name|id'
        r'|className|title|alt|srcdoc|poster)'
        r'(?:\(|$|\.)'
    )
    pm = PROP_RE.search(ident)
    prop = pm.group(1) if pm else None

    return method, selector, prop


def analyze_sink_selectors():
    section('B. DANGEROUS SINK SELECTOR DISTRIBUTION')

    # Sample raw proxy_data to confirm format before full query
    sample = q(
        f"SELECT proxy_data FROM isolated_proxy_log_{SUFFIX} "
        "WHERE dataset=%s AND proxy_data IS NOT NULL AND proxy_data::text != 'null' "
        "LIMIT 3;",
        DATASET
    )
    print('  Sample proxy_data entries (format probe):')
    for (pd,) in sample[:2]:
        if isinstance(pd, str):
            try: pd = json.loads(pd)
            except: pass
        if isinstance(pd, list) and pd:
            print(f'    Entry 0: {str(pd[0])[:150]}')

    rows = q(
        "SELECT extension_id, proxy_data "
        f"FROM isolated_proxy_log_{SUFFIX} "
        "WHERE dataset=%s AND proxy_data IS NOT NULL AND proxy_data::text != 'null' "
        "LIMIT 300000;",
        DATASET
    )
    print(f'  proxy_log rows loaded: {len(rows):,}')

    selector_freq  = Counter()
    method_freq    = Counter()
    prop_freq      = Counter()
    selector_prop  = defaultdict(Counter)
    sel_ext_freq   = defaultdict(set)
    parsed_count   = 0

    for ext_id, proxy_data in rows:
        if not proxy_data: continue
        if isinstance(proxy_data, str):
            try: proxy_data = json.loads(proxy_data)
            except: continue
        if not isinstance(proxy_data, list): continue

        for entry in proxy_data:
            method, selector, prop = parse_proxy_entry(entry)
            if method:
                method_freq[method] += 1
                parsed_count += 1
            if selector:
                selector_freq[selector] += 1
                sel_ext_freq[selector].add(ext_id)
            if prop:
                prop_freq[prop] += 1
            if selector and prop:
                selector_prop[selector][prop] += 1

    print(f'  Parsed entries with method: {parsed_count:,}')
    print()

    if parsed_count == 0:
        # Fallback: use the per_visit_per_extension data from v2 sinks JSON
        # which has property names per extension — less granular but still useful
        print('  WARNING: no identifiers parsed — proxy_data format differs from expected.')
        print('  Falling back to v2 dangerous sinks property breakdown.')
        import pathlib
        v2_path = pathlib.Path(__file__).resolve().parent.parent.parent / \
                  'results' / 'ina' / (SUFFIX or '') / 'ina_dangerous_sinks.json'
        if v2_path.exists():
            v2 = json.loads(v2_path.read_text())
            pv = v2['per_visit_per_extension']
            for visit_data in pv.values():
                for ext_id, props in visit_data.items():
                    for p in (props if isinstance(props, list) else props.keys()):
                        prop_freq[p] += 1
            print('  Property distribution from strict sink set:')
            for p, n in prop_freq.most_common():
                print(f'    {n:>6,}  {p}')
        return {'note': 'proxy identifier parsing failed — check format', 'prop_freq': dict(prop_freq)}

    print('  DOM query method distribution:')
    for method, n in method_freq.most_common():
        print(f'    {n:>8,}  {method}')

    print()
    print('  Top 30 selector strings (most clobbered):')
    for sel, n in selector_freq.most_common(30):
        top_prop = selector_prop[sel].most_common(1)
        top_p = top_prop[0][0] if top_prop else '?'
        print(f'    {n:>6,}  {sel:<50} → .{top_p}')

    id_selectors   = [(s, n) for s, n in selector_freq.items() if s.startswith('#')]
    cls_selectors  = [(s, n) for s, n in selector_freq.items() if s.startswith('.')]
    attr_selectors = [(s, n) for s, n in selector_freq.items() if s.startswith('[')]
    tag_selectors  = [(s, n) for s, n in selector_freq.items()
                     if not any(s.startswith(c) for c in '#.[')]

    print()
    print('  Selector type distribution:')
    print(f'    ID (#):          {len(id_selectors):>5,} unique  {sum(n for _,n in id_selectors):>8,} accesses')
    print(f'    Class (.):       {len(cls_selectors):>5,} unique  {sum(n for _,n in cls_selectors):>8,} accesses')
    print(f'    Attribute ([):   {len(attr_selectors):>5,} unique  {sum(n for _,n in attr_selectors):>8,} accesses')
    print(f'    Tag/compound:    {len(tag_selectors):>5,} unique  {sum(n for _,n in tag_selectors):>8,} accesses')

    print()
    print('  Selectors shared across most extensions (cross-extension attack surface):')
    cross_ext = sorted(sel_ext_freq.items(), key=lambda x: -len(x[1]))
    for sel, exts in cross_ext[:20]:
        top_prop = selector_prop[sel].most_common(1)
        top_p = top_prop[0][0] if top_prop else '?'
        print(f'    {len(exts):>5,} exts  {sel:<50} → .{top_p}')

    # 8-element payload coverage (GBS + selector combined)
    # These are the selector-side elements; GBS side is handled in Part A
    payload_8_selectors = ['a', 'img', 'script', 'input', 'video', 'body', '*', 'iframe']
    payload_8_exts = set()
    for sel in payload_8_selectors:
        payload_8_exts |= sel_ext_freq.get(sel, set())

    print()
    print(f'  8-element selector payload coverage: {len(payload_8_exts):,} extensions')
    for sel in payload_8_selectors:
        n = len(sel_ext_freq.get(sel, set()))
        print(f'    {n:>5}  querySelector("{sel}")')

    return {
        'method_freq': dict(method_freq.most_common()),
        'top_selectors': selector_freq.most_common(50),
        'prop_freq': dict(prop_freq.most_common()),
        'cross_extension_selectors': [(s, len(e)) for s, e in cross_ext[:30]],
        'selector_type_counts': {
            'id': len(id_selectors), 'class': len(cls_selectors),
            'attribute': len(attr_selectors), 'tag_compound': len(tag_selectors),
        },
        # Per-selector extension ID sets for cross-extension analysis
        'selector_extension_ids': {
            sel: sorted(sel_ext_freq[sel])
            for sel in ['*', 'a', 'img', 'script', 'input', 'video',
                        'body', 'head', 'iframe', 'link', 'title', 'form']
            if sel in sel_ext_freq
        },
        'payload_8_element': {
            'selectors':  payload_8_selectors,
            'extensions': sorted(payload_8_exts),
            'count':      len(payload_8_exts),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print(f'INA v3 Variable Analysis — suffix={SUFFIX}  dataset={DATASET}')

    gbs_results  = analyze_gbs_variables()
    sink_results = analyze_sink_selectors()

    out = {
        'suffix':  SUFFIX,
        'dataset': DATASET,
        'gbs_variables':   gbs_results,
        'sink_selectors':  sink_results,
    }

    out_path = OUT_DIR / 'ina_variable_analysis.json'
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print(f'Saved: {out_path}')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
