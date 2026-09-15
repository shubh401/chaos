/**
 * @name Extension DOM-source to dangerous-sink taint flow
 * @description Custom source/sink query mirroring taint_flow_extractor.js's vocabulary:
 *              DOM query results reaching network/messaging/eval sinks via a dangerous
 *              property read.
 * @kind path-problem
 * @problem.severity warning
 * @id ext/dom-taint-flow
 */

import javascript

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

// Dangerous DOM properties whose value derives from (and should be treated as tainted
// given) a tainted receiver — mirrors DANGEROUS_PROPS in taint_flow_extractor.js. CodeQL's
// default JS taint model has no built-in knowledge that Element.getAttribute() or these
// property reads preserve taint from receiver to result, so this must be modeled explicitly.
predicate isDangerousPropName(string p) {
  p = ["src", "href", "action", "formaction", "innerHTML", "outerHTML",
       "srcdoc", "data", "value", "textContent", "innerText", "text",
       "location", "name", "id", "className", "dataset"]
}

module Config implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node src) { src = any(DomQuerySource s).getASuccessor*() }

  predicate isSink(DataFlow::Node sink) {
    exists(DangerousSink dsink | sink = dsink.getAnArgument())
    or
    exists(DangerousSink dsink, DataFlow::ObjectLiteralNode obj |
      obj = dsink.getAnArgument() and
      sink = obj.getAPropertyWrite().getRhs()
    )
  }

  predicate isAdditionalFlowStep(DataFlow::Node pred, DataFlow::Node succ) {
    // el.getAttribute("href") — receiver tainted, result tainted, IF the accessed
    // property name is in our dangerous-property list.
    exists(DataFlow::MethodCallNode call, string prop |
      call.getMethodName() = "getAttribute" and
      call.getArgument(0).getStringValue() = prop and
      isDangerousPropName(prop.toLowerCase()) and
      pred = call.getReceiver() and
      succ = call
    )
    or
    // el.href / el.src / etc. — a direct property READ (not a write) on a tainted
    // receiver, where the property name is dangerous.
    exists(DataFlow::PropRead pr |
      isDangerousPropName(pr.getPropertyName()) and
      pred = pr.getBase() and
      succ = pr
    )
  }
}

module Flow = TaintTracking::Global<Config>;
import Flow::PathGraph

from Flow::PathNode source, Flow::PathNode sink
where Flow::flowPath(source, sink)
select sink.getNode(), source, sink, "Taint flow from DOM source to dangerous sink."
