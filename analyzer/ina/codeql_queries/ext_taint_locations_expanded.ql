/**
 * @name Extension DOM-source to dangerous-sink taint flow — EXPANDED vocabulary
 * @description Extends ext_taint_locations.ql's source/sink vocabulary to cover the
 *              four categories Rev1 flagged as a completeness gap (confirmed absent from
 *              the current vocabulary in TAINT_SCOPE_COLLISION_FINDINGS.md / REVIEW.md
 *              Cluster D): EventTarget-based reads, XPath, node traversal, Shadow DOM.
 *              Kept as a SEPARATE query file (not a modification of ext_taint_locations.ql)
 *              so the already-validated, corpus-run narrow-vocabulary result stays intact
 *              and citable, and so this gives a direct before/after comparison — run
 *              against the SAME already-built databases (databases are source-code
 *              extractions, not query-specific, so no rebuild is needed).
 * @kind table
 * @id ext/dom-taint-flow-locations-expanded
 */

import javascript

// ── Original vocabulary (unchanged from ext_taint_locations.ql) ──────────────────────
class DomQuerySource extends DataFlow::CallNode {
  DomQuerySource() {
    exists(string m |
      m = ["getElementById", "querySelector", "querySelectorAll",
           "getElementsByClassName", "getElementsByTagName", "getElementsByName",
           "closest", "matches"] and
      this.getCalleeName() = m
    )
  }
}

// ── NEW: XPath source — document.evaluate(...) call itself is not yet the tainted
//    value; its RESULT properties (singleNodeValue/stringValue/numberValue/
//    iterateNext()) are — modeled as an additional flow step below, matching the
//    getAttribute() pattern already validated this session. ──────────────────────────
class XPathEvaluateCall extends DataFlow::CallNode {
  XPathEvaluateCall() { this.getCalleeName() = "evaluate" }
}

// ── NEW: Shadow DOM source — el.attachShadow(...) returns a new ShadowRoot anchored
//    to a (possibly already-tainted) host element; el.shadowRoot reads an existing one.
//    Modeled as: attachShadow()'s return value is itself a fresh, query-capable root
//    (not tainted on its own — DomQuerySource already covers querySelector calls made
//    ON it, once shadowRoot/attachShadow's result flows as a normal DataFlow::Node); the
//    .shadowRoot READ is the one that needs an explicit flow step, since it's a property
//    read on a (potentially tainted) host, not a fresh top-level source. ─────────────
predicate isShadowDomPropName(string p) { p = ["shadowRoot"] }

// ── NEW: EventTarget-based read — el.addEventListener("x", e => ... e.target ...);
//    e.target/e.currentTarget yields a DOM element the extension did not explicitly
//    query for, but which is nonetheless attacker-influenceable (the element the
//    attacker's page caused the event to fire on). Modeled as a SOURCE (like
//    DomQuerySource), not a flow step, since there is no "receiver" to propagate
//    taint FROM — the event object itself is the origin. ──────────────────────────────
predicate isEventTargetPropName(string p) { p = ["target", "currentTarget"] }

// ── NEW: node-traversal properties — reading these off an ALREADY-tainted node yields
//    another (still attacker-influenceable) node; modeled as a flow step, same shape as
//    isDangerousPropName's PropRead branch, but semantically distinct (these yield
//    NODES to traverse further, not final string VALUES to sink directly — kept in a
//    separate predicate rather than merged into isDangerousPropName for that reason,
//    even though the CodeQL modeling is mechanically identical). ──────────────────────
predicate isTraversalPropName(string p) {
  p = ["parentNode", "parentElement", "nextSibling", "previousSibling",
       "firstChild", "lastChild", "childNodes", "nextElementSibling",
       "previousElementSibling", "firstElementChild", "lastElementChild"]
}

// ── Original dangerous-property vocabulary (unchanged) ───────────────────────────────
predicate isDangerousPropName(string p) {
  p = ["src", "href", "action", "formaction", "innerHTML", "outerHTML",
       "srcdoc", "data", "value", "textContent", "innerText", "text",
       "location", "name", "id", "className", "dataset"]
}

// ── NEW: XPathResult accessor properties/methods — reading these off a tainted
//    XPathResult yields the actual attacker-influenceable value/node. ─────────────────
predicate isXPathResultAccessorName(string p) {
  p = ["singleNodeValue", "stringValue", "numberValue", "booleanValue"]
}

class DangerousSink extends DataFlow::CallNode {
  DangerousSink() {
    exists(string m |
      m = ["fetch", "send", "sendBeacon", "postMessage", "sendMessage",
           "sendNativeMessage", "setItem", "eval", "write", "writeln",
           "setTimeout", "setInterval"] and
      this.getCalleeName() = m
    )
  }
}

module Config implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node src) {
    src = any(DomQuerySource s).getASuccessor*()
    or
    exists(DataFlow::PropRead pr | isEventTargetPropName(pr.getPropertyName()) and src = pr)
  }

  predicate isSink(DataFlow::Node sink) {
    exists(DangerousSink dsink | sink = dsink.getAnArgument())
    or
    exists(DangerousSink dsink, DataFlow::ObjectLiteralNode obj |
      obj = dsink.getAnArgument() and
      sink = obj.getAPropertyWrite().getRhs()
    )
  }

  predicate isAdditionalFlowStep(DataFlow::Node pred, DataFlow::Node succ) {
    // el.getAttribute("href") — original, unchanged
    exists(DataFlow::MethodCallNode call, string prop |
      call.getMethodName() = "getAttribute" and
      call.getArgument(0).getStringValue() = prop and
      isDangerousPropName(prop.toLowerCase()) and
      pred = call.getReceiver() and
      succ = call
    )
    or
    // el.href / el.src / etc. — original, unchanged
    exists(DataFlow::PropRead pr |
      isDangerousPropName(pr.getPropertyName()) and
      pred = pr.getBase() and
      succ = pr
    )
    or
    // NEW — node traversal: el.parentNode / el.nextSibling / etc. on a tainted node
    exists(DataFlow::PropRead pr |
      isTraversalPropName(pr.getPropertyName()) and
      pred = pr.getBase() and
      succ = pr
    )
    or
    // NEW — Shadow DOM: el.shadowRoot on a tainted host element
    exists(DataFlow::PropRead pr |
      isShadowDomPropName(pr.getPropertyName()) and
      pred = pr.getBase() and
      succ = pr
    )
    or
    // NEW — XPath: document.evaluate(...) call's tainted-ness comes from whatever
    // node/string was passed as the CONTEXT NODE argument (arg index 1) being tainted —
    // i.e. document.evaluate(expr, contextNode, ...) where contextNode is tainted taints
    // the evaluate() result itself.
    exists(XPathEvaluateCall call |
      pred = call.getArgument(1) and
      succ = call
    )
    or
    // NEW — XPath result accessors: xpathResult.singleNodeValue / .stringValue / etc.
    // on a tainted XPathResult (the evaluate() call itself, per the step above)
    exists(DataFlow::PropRead pr |
      isXPathResultAccessorName(pr.getPropertyName()) and
      pred = pr.getBase() and
      succ = pr
    )
    or
    // NEW — XPath iteration: xpathResult.iterateNext() on a tainted XPathResult
    exists(DataFlow::MethodCallNode call |
      call.getMethodName() = "iterateNext" and
      pred = call.getReceiver() and
      succ = call
    )
  }
}

module Flow = TaintTracking::Global<Config>;

from DataFlow::Node source, DataFlow::Node sink
where
  Flow::flow(source, sink) and
  Config::isSink(sink)
select source.getFile().getBaseName(), source.getLocation().getStartLine(), source.toString(),
       sink.getFile().getBaseName(), sink.getLocation().getStartLine(), sink.toString()
