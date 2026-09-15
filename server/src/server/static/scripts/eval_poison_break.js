(() => {
  const _fetch = window.fetch;
  const _stringify = JSON.stringify;
  const _Function = window.Function;
  const _setTimeout = window.setTimeout;
  const _setInterval = window.setInterval;

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

  // --- eval throws ---
  window.eval = function () {
    dispatch('eval_poison_break.eval', {
      stacktrace: new Error().stack?.split('\n').slice(1, 5),
    });
    throw new Error('eval is disabled by page security policy');
  };

  // --- Function constructor throws ---
  window.Function = function () {
    dispatch('eval_poison_break.Function', {
      stacktrace: new Error().stack?.split('\n').slice(1, 5),
    });
    throw new Error('Function constructor is disabled');
  };
  window.Function.prototype = _Function.prototype;

  // --- setTimeout with string: silent no-op ---
  window.setTimeout = function (handler, delay, ...args) {
    if (typeof handler === 'string') {
      dispatch('eval_poison_break.setTimeout_string', {
        codeSnippet: handler.slice(0, 200),
      });
      return 0; // fake timer ID
    }
    return _setTimeout.call(window, handler, delay, ...args);
  };

  // --- setInterval with string: silent no-op ---
  window.setInterval = function (handler, delay, ...args) {
    if (typeof handler === 'string') {
      dispatch('eval_poison_break.setInterval_string', {
        codeSnippet: handler.slice(0, 200),
      });
      return 0;
    }
    return _setInterval.call(window, handler, delay, ...args);
  };
})();
