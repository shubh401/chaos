/**
 * taint_flow_extractor.js — Static taint flow analysis for INA dangerous sink extensions.
 *
 * For a given content script, walks the AST to find:
 *   1. SOURCE: getElementById / querySelector / querySelectorAll calls whose
 *      result is stored in a variable (or used inline).
 *   2. PROPERTY READ: .href / .src / .action / .innerHTML / etc. accessed on
 *      the source result variable.
 *   3. SINK: the read value (or the variable holding it) flows into a dangerous
 *      output sink — fetch, XHR, location, postMessage, chrome.*, eval, etc.
 *
 * Detection strategy: variable-name tracking.
 *   - Track variables assigned from DOM queries (source set).
 *   - Track variables assigned from dangerous property reads on source vars (tainted set).
 *   - Flag any call/assignment where a tainted variable appears as argument.
 *
 * This is intentionally conservative (may miss indirect flows through object
 * properties, closures, or dynamic keys) but has zero false negatives for the
 * common direct-use pattern:
 *   const el = document.getElementById("X");
 *   fetch(el.href);
 *
 * Usage: node taint_flow_extractor.js <script_path>
 * Output: JSON to stdout — { flows: [...], sources: N, tainted_reads: N }
 */

const fs   = require('fs');
const path = require('path');
// Resolve acorn-loose from the static/ package (same as dom_query_extractor.js)
const acorn = require('acorn-loose');

// ── Source DOM query methods ──────────────────────────────────────────────────
const DOM_SOURCES = new Set([
    'getElementById', 'querySelector', 'querySelectorAll',
    'getElementsByClassName', 'getElementsByTagName', 'getElementsByName',
    'closest', 'matches',
]);

// ── Dangerous properties that carry attacker-controlled values ────────────────
const DANGEROUS_PROPS = new Set([
    'src', 'href', 'action', 'formaction', 'innerHTML', 'outerHTML',
    'srcdoc', 'data', 'value', 'textContent', 'innerText', 'text',
    'location', 'name', 'id', 'className', 'dataset',
]);

// ── Output sinks — unambiguous function/method names ─────────────────────────
// These match regardless of the caller object because no legitimate non-sink
// API uses these names in a content script context.
const SINK_FUNCTIONS_UNAMBIGUOUS = new Set([
    'fetch', 'send', 'sendBeacon',          // network
    'postMessage', 'sendMessage',            // messaging
    'sendNativeMessage',                     // chrome native
    'setItem',                               // web storage
    'eval', 'write', 'writeln',             // eval-class
    'setTimeout', 'setInterval',             // string-form eval
]);

// ── Context-qualified sinks ───────────────────────────────────────────────────
// These method names are only sinks when called on specific receiver objects.
// Format: methodName → Set of receiver object name substrings that confirm sink.
// If the receiver is unknown/complex, we still flag but mark as 'unverified'.
const SINK_FUNCTIONS_QUALIFIED = {
    // location.assign / location.replace (NOT Object.assign / String.replace)
    'assign':  { receivers: new Set(['location']),                   sink: 'location.assign'  },
    'replace': { receivers: new Set(['location']),                   sink: 'location.replace' },
    // chrome.tabs.create / chrome.tabs.update
    'create':  { receivers: new Set(['tabs', 'chrome.tabs']),        sink: 'chrome.tabs.create' },
    'update':  { receivers: new Set(['tabs', 'chrome.tabs']),        sink: 'chrome.tabs.update' },
    // chrome.storage.*.set / Map.set (both are sinks, Map.set less severe)
    'set':     { receivers: new Set(['local', 'sync', 'session', 'storage', 'chrome.storage']),
                                                                     sink: 'chrome.storage.set' },
    // XHR.open / window.open / indexedDB.open
    'open':    { receivers: new Set(['location', 'window', 'db', 'indexedDB', 'idb']),
                                                                     sink: 'open'              },
};

// ── Sink assignment targets (left-hand side of assignments) ──────────────────
const SINK_ASSIGNMENTS = new Set([
    'href', 'src', 'action', 'formaction', 'srcdoc', 'data',
    'innerHTML', 'outerHTML', 'textContent', 'innerText',
    'location',
]);

const results = {
    flows:         [],   // confirmed source→prop→sink flows
    sources:       0,    // number of DOM query call sites found
    tainted_reads: 0,    // number of dangerous property reads on source vars
};

// ── AST walker ────────────────────────────────────────────────────────────────
function walk(node, visitor, parent) {
    if (!node || typeof node !== 'object') return;
    if (node.type) visitor(node, parent);
    for (const key of Object.keys(node)) {
        const child = node[key];
        if (Array.isArray(child)) {
            for (const item of child) {
                if (item && typeof item === 'object' && item.type)
                    walk(item, visitor, node);
            }
        } else if (child && typeof child === 'object' && child.type) {
            walk(child, visitor, node);
        }
    }
}

function getName(node) {
    if (!node) return null;
    if (node.type === 'Identifier') return node.name;
    if (node.type === 'MemberExpression' && !node.computed && node.property?.type === 'Identifier')
        return node.property.name;
    return null;
}

function getStringArg(node) {
    if (!node) return null;
    if (node.type === 'Literal' && typeof node.value === 'string') return node.value;
    if (node.type === 'TemplateLiteral' && node.quasis?.length === 1)
        return node.quasis[0].value?.cooked || null;
    return null;
}

function isDOMQuery(node) {
    // document.getElementById(...) / el.querySelector(...)
    if (node.type !== 'CallExpression') return false;
    const callee = node.callee;
    if (callee.type !== 'MemberExpression') return false;
    const method = getName(callee.property);
    return DOM_SOURCES.has(method);
}

// el.getAttribute("href") where el ∈ sourceVars and arg ∈ DANGEROUS_PROPS
function getDangerousGetAttr(node, sourceVars) {
    if (node.type !== 'CallExpression') return null;
    const callee = node.callee;
    if (callee.type !== 'MemberExpression') return null;
    if (getName(callee.property) !== 'getAttribute') return null;
    const objName = getName(callee.object);
    if (!objName || !sourceVars.has(objName)) return null;
    const arg = node.arguments?.[0];
    const prop = arg ? getStringArg(arg) : null;
    if (!prop || !DANGEROUS_PROPS.has(prop.toLowerCase())) return null;
    return { objName, prop: prop.toLowerCase() };
}

function analyze(code) {
    let ast;
    try {
        ast = acorn.parse(code, {
            allowImportExportEverywhere: true,
            allowAwaitOutsideFunction:   true,
            allowReturnOutsideFunction:  true,
            allowHashBang:               true,
            allowReserved:               true,
            locations:                   true,
        });
    } catch(e) {
        return;  // unparseable — skip silently
    }

    // Sets of variable names
    const sourceVars  = new Set();  // assigned from DOM queries
    const taintedVars = new Set();  // assigned from dangerous prop reads on sourceVars

    // Pass 1: collect source variables (DOM query results)
    walk(ast, (node) => {
        // var/let/const x = document.getElementById(...)
        if (node.type === 'VariableDeclarator' && node.init && isDOMQuery(node.init)) {
            results.sources++;
            const name = getName(node.id);
            if (name) sourceVars.add(name);
        }
        // x = document.querySelector(...)
        if (node.type === 'AssignmentExpression' && isDOMQuery(node.right)) {
            results.sources++;
            const name = getName(node.left);
            if (name) sourceVars.add(name);
        }
    });

    // Pass 2: collect tainted variables (dangerous prop reads on source vars)
    walk(ast, (node) => {
        // var/let/const url = el.href  (where el is a sourceVar)
        if (node.type === 'VariableDeclarator' && node.init?.type === 'MemberExpression') {
            const objName = getName(node.init.object);
            const prop    = getName(node.init.property);
            if (objName && sourceVars.has(objName) && DANGEROUS_PROPS.has(prop)) {
                results.tainted_reads++;
                const lhs = getName(node.id);
                if (lhs) taintedVars.add(lhs);
            }
        }
        // x = el.src
        if (node.type === 'AssignmentExpression' && node.right?.type === 'MemberExpression') {
            const objName = getName(node.right.object);
            const prop    = getName(node.right.property);
            if (objName && sourceVars.has(objName) && DANGEROUS_PROPS.has(prop)) {
                results.tainted_reads++;
                const lhs = getName(node.left);
                if (lhs) taintedVars.add(lhs);
            }
        }
        // var/let/const url = el.getAttribute("href")
        if (node.type === 'VariableDeclarator' && node.init?.type === 'CallExpression') {
            const ga = getDangerousGetAttr(node.init, sourceVars);
            if (ga) {
                results.tainted_reads++;
                const lhs = getName(node.id);
                if (lhs) taintedVars.add(lhs);
            }
        }
        // x = el.getAttribute("href")
        if (node.type === 'AssignmentExpression' && node.right?.type === 'CallExpression') {
            const ga = getDangerousGetAttr(node.right, sourceVars);
            if (ga) {
                results.tainted_reads++;
                const lhs = getName(node.left);
                if (lhs) taintedVars.add(lhs);
            }
        }
    });

    // Pass 3: find sinks where tainted vars or inline prop reads appear
    walk(ast, (node) => {
        // ── Call expression sinks: fetch(url), xhr.open(m, url), postMessage(data) ──
        if (node.type === 'CallExpression') {
            const fnName = getName(node.callee);
            if (!fnName) return;

            // Resolve sink name — unambiguous or qualified
            let resolvedSink = null;
            if (SINK_FUNCTIONS_UNAMBIGUOUS.has(fnName)) {
                resolvedSink = fnName;
            } else if (SINK_FUNCTIONS_QUALIFIED[fnName]) {
                const q = SINK_FUNCTIONS_QUALIFIED[fnName];
                // Get receiver name to check context
                const receiver = node.callee?.type === 'MemberExpression'
                    ? (getName(node.callee.object) || '').toLowerCase()
                    : '';
                const matched = [...q.receivers].some(r => receiver.includes(r));
                resolvedSink = matched ? q.sink : (fnName + '(unverified)');
            }
            if (!resolvedSink) return;
            const fnName_orig = fnName;
            // shadow fnName with resolvedSink for reporting
            const sinkLabel = resolvedSink;

            // Check each argument
            node.arguments.forEach((arg, idx) => {
                // Direct tainted var: fetch(taintedUrl)
                if (arg.type === 'Identifier' && taintedVars.has(arg.name)) {
                    results.flows.push({
                        type:     'call_arg',
                        sink:     sinkLabel,
                        arg_idx:  idx,
                        var_name: arg.name,
                        line:     node.loc?.start?.line,
                    });
                }
                // Inline prop read: fetch(el.href)
                if (arg.type === 'MemberExpression') {
                    const objName = getName(arg.object);
                    const prop    = getName(arg.property);
                    if (objName && sourceVars.has(objName) && DANGEROUS_PROPS.has(prop)) {
                        results.tainted_reads++;
                        results.flows.push({
                            type:     'inline_call_arg',
                            sink:     sinkLabel,
                            arg_idx:  idx,
                            source:   objName,
                            property: prop,
                            line:     node.loc?.start?.line,
                        });
                    }
                }
                // Inline getAttribute read: fetch(el.getAttribute("href"))
                if (arg.type === 'CallExpression') {
                    const ga = getDangerousGetAttr(arg, sourceVars);
                    if (ga) {
                        results.tainted_reads++;
                        results.flows.push({
                            type:     'inline_call_arg_getattr',
                            sink:     sinkLabel,
                            arg_idx:  idx,
                            source:   ga.objName,
                            property: ga.prop,
                            line:     node.loc?.start?.line,
                        });
                    }
                }
                // Object literal with tainted values: fetch(url, {body: taintedVal})
                if (arg.type === 'ObjectExpression') {
                    arg.properties?.forEach(p => {
                        const val = p.value;
                        if (val?.type === 'Identifier' && taintedVars.has(val.name)) {
                            results.flows.push({
                                type:     'call_arg_object',
                                sink:     sinkLabel,
                                key:      getName(p.key),
                                var_name: val.name,
                                line:     node.loc?.start?.line,
                            });
                        }
                    });
                }
            });
        }

        // ── Assignment sinks: window.location = tainted, el.src = tainted ──
        if (node.type === 'AssignmentExpression') {
            const lhsProp = getName(node.left);
            if (!lhsProp || !SINK_ASSIGNMENTS.has(lhsProp)) return;

            const rhs = node.right;
            // taintedVar assigned to sink property
            if (rhs.type === 'Identifier' && taintedVars.has(rhs.name)) {
                results.flows.push({
                    type:     'assignment',
                    sink:     lhsProp,
                    var_name: rhs.name,
                    line:     node.loc?.start?.line,
                });
            }
            // inline prop read assigned to sink: el2.src = el.href
            if (rhs.type === 'MemberExpression') {
                const objName = getName(rhs.object);
                const prop    = getName(rhs.property);
                if (objName && sourceVars.has(objName) && DANGEROUS_PROPS.has(prop)) {
                    results.tainted_reads++;
                    results.flows.push({
                        type:     'inline_assignment',
                        sink:     lhsProp,
                        source:   objName,
                        property: prop,
                        line:     node.loc?.start?.line,
                    });
                }
            }
            // inline getAttribute assigned to sink: el2.src = el.getAttribute("href")
            if (rhs.type === 'CallExpression') {
                const ga = getDangerousGetAttr(rhs, sourceVars);
                if (ga) {
                    results.tainted_reads++;
                    results.flows.push({
                        type:     'inline_assignment_getattr',
                        sink:     lhsProp,
                        source:   ga.objName,
                        property: ga.prop,
                        line:     node.loc?.start?.line,
                    });
                }
            }
        }

        // ── new WebSocket(taintedUrl) ──
        if (node.type === 'NewExpression') {
            const ctor = getName(node.callee);
            if (ctor === 'WebSocket' && node.arguments?.length > 0) {
                const arg = node.arguments[0];
                if (arg.type === 'Identifier' && taintedVars.has(arg.name)) {
                    results.flows.push({
                        type:     'constructor',
                        sink:     'WebSocket',
                        var_name: arg.name,
                        line:     node.loc?.start?.line,
                    });
                }
                if (arg.type === 'MemberExpression') {
                    const objName = getName(arg.object);
                    const prop    = getName(arg.property);
                    if (objName && sourceVars.has(objName) && DANGEROUS_PROPS.has(prop)) {
                        results.tainted_reads++;
                        results.flows.push({
                            type:     'inline_constructor',
                            sink:     'WebSocket',
                            source:   objName,
                            property: prop,
                            line:     node.loc?.start?.line,
                        });
                    }
                }
                if (arg.type === 'CallExpression') {
                    const ga = getDangerousGetAttr(arg, sourceVars);
                    if (ga) {
                        results.tainted_reads++;
                        results.flows.push({
                            type:     'inline_constructor_getattr',
                            sink:     'WebSocket',
                            source:   ga.objName,
                            property: ga.prop,
                            line:     node.loc?.start?.line,
                        });
                    }
                }
            }
        }
    });
}

function main(filePath) {
    try {
        const code = fs.readFileSync(filePath, 'utf-8');
        analyze(code);
        console.log(JSON.stringify(results));
    } catch(e) {
        console.error(e.message);
        console.log(JSON.stringify(results));
    }
}

if (process.argv.length > 2) {
    main(process.argv[2]);
}
