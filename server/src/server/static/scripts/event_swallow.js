(() => {
  const _fetch = window.fetch;
  const _stringify = JSON.stringify;
  const _addEventListener = EventTarget.prototype.addEventListener;

  let counter = 0;
  const MAX = 10000;

  function dispatch(api, data) {
    if (counter++ > MAX) return;
    try {
      _fetch.call(window, `${location.origin}${window.location.pathname}hook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: _stringify.call(JSON, {
          type: api, data,
          extensionId: new URLSearchParams(window.location.search).get('extensionId'),
          visit: new URLSearchParams(window.location.search).get('visit'),
        }),
      });
    } catch (e) {}
  }

  // Events that extensions commonly listen for
  const CRITICAL_EVENTS = [
    'click', 'dblclick', 'mousedown', 'mouseup', 'mousemove',
    'mouseover', 'mouseout', 'mouseenter', 'mouseleave',
    'keydown', 'keyup', 'keypress',
    'input', 'change', 'submit', 'focus', 'blur',
    'touchstart', 'touchend', 'touchmove',
    'contextmenu', 'wheel', 'scroll',
    'message', 'messageerror',
    'copy', 'cut', 'paste',
    'visibilitychange', 'pageshow', 'pagehide',
    'online', 'offline',
    'drag', 'dragstart', 'dragend', 'dragover', 'drop',
  ];

  // Register capturing-phase listeners that LOG but do not block
  for (const eventName of CRITICAL_EVENTS) {
    _addEventListener.call(window, eventName, function (event) {
      dispatch('event_swallow.window', {
        eventName,
        target: event.target?.nodeName || 'unknown',
        isTrusted: event.isTrusted,
        phase: event.eventPhase,
      });
    }, true);

    _addEventListener.call(document, eventName, function (event) {
      dispatch('event_swallow.document', {
        eventName,
        target: event.target?.nodeName || 'unknown',
        isTrusted: event.isTrusted,
        phase: event.eventPhase,
      });
    }, true);
  }

  // Monitor addEventListener calls to see what extensions listen for
  EventTarget.prototype.addEventListener = function (type, listener, options) {
    dispatch('event_swallow.addEventListener', {
      eventType: type,
      targetName: this?.constructor?.name || this?.nodeName || 'unknown',
      useCapture: typeof options === 'boolean' ? options : options?.capture,
      stacktrace: new Error().stack?.split('\n').slice(1, 5),
    });
    return _addEventListener.call(this, type, listener, options);
  };
})();
