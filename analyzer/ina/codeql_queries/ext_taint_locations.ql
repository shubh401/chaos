/**
 * @name Extension DOM-source to dangerous-sink taint flow — locations only
 * @kind table
 * @id ext/dom-taint-flow-locations
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
    exists(DataFlow::MethodCallNode call, string prop |
      call.getMethodName() = "getAttribute" and
      call.getArgument(0).getStringValue() = prop and
      isDangerousPropName(prop.toLowerCase()) and
      pred = call.getReceiver() and
      succ = call
    )
    or
    exists(DataFlow::PropRead pr |
      isDangerousPropName(pr.getPropertyName()) and
      pred = pr.getBase() and
      succ = pr
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
