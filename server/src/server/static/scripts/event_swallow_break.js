(() => {
  const _fetch = window.fetch;
  const _stringify = JSON.stringify;
  const _addEventListener = EventTarget.prototype.addEventListener;
  const _dispatchEvent = EventTarget.prototype.dispatchEvent;
  const _removeEventListener = EventTarget.prototype.removeEventListener;

  let counter = 0;
  const MAX = 5000;

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

  // Events to swallow — excludes lifecycle events needed by our infrastructure
  const SWALLOW_EVENTS = [
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
    'readystatechange',
  ];

  // Swallow events in capturing phase
  for (const eventName of SWALLOW_EVENTS) {
    _addEventListener.call(window, eventName, function (event) {
      dispatch('event_swallow_break.swallowed', { eventName });
      event.stopImmediatePropagation();
      event.preventDefault();
    }, true);

    _addEventListener.call(document, eventName, function (event) {
      event.stopImmediatePropagation();
      event.preventDefault();
    }, true);
  }

  // Override addEventListener — extension registrations become no-ops
  EventTarget.prototype.addEventListener = function (type, listener, options) {
    // Allow our own scripts to register normally
    const stack = new Error().stack || '';
    if (stack.includes('lifecycle_tracker') || stack.includes('v2_dispatch') ||
        stack.includes('event_swallow') || stack.includes('mutation.js')) {
      return _addEventListener.call(this, type, listener, options);
    }
    dispatch('event_swallow_break.blocked_addEventListener', {
      eventType: type,
      targetName: this?.constructor?.name || this?.nodeName || 'unknown',
    });
    // Register a no-op instead of the actual listener
    return _addEventListener.call(this, type, function () {}, options);
  };

  // Override removeEventListener — no-op
  EventTarget.prototype.removeEventListener = function () {
    return undefined;
  };

  // Override dispatchEvent — custom events fail
  EventTarget.prototype.dispatchEvent = function (event) {
    dispatch('event_swallow_break.blocked_dispatchEvent', {
      eventType: event?.type,
    });
    return false;
  };
})();
