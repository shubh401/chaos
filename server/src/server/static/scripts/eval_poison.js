(() => {
  const _fetch = window.fetch;
  const _stringify = JSON.stringify;
  const _eval = window.eval;
  const _Function = window.Function;
  const _setTimeout = window.setTimeout;
  const _setInterval = window.setInterval;

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

  // --- eval ---
  window.eval = function (code) {
    dispatch('eval_poison.eval', {
      codeLength: typeof code === 'string' ? code.length : 0,
      codeSnippet: typeof code === 'string' ? code.slice(0, 200) : String(code).slice(0, 200),
      stacktrace: new Error().stack?.split('\n').slice(1, 5),
    });
    return _eval.call(window, code);
  };

  // --- Function constructor ---
  window.Function = new Proxy(_Function, {
    construct(target, args, newTarget) {
      dispatch('eval_poison.Function_construct', {
        argCount: args.length,
        bodySnippet: args.length > 0 ? String(args[args.length - 1]).slice(0, 200) : '',
        stacktrace: new Error().stack?.split('\n').slice(1, 5),
      });
      return Reflect.construct(target, args, newTarget);
    },
    apply(target, thisArg, args) {
      dispatch('eval_poison.Function_apply', {
        argCount: args.length,
        bodySnippet: args.length > 0 ? String(args[args.length - 1]).slice(0, 200) : '',
        stacktrace: new Error().stack?.split('\n').slice(1, 5),
      });
      return Reflect.apply(target, thisArg, args);
    },
  });
  window.Function.prototype = _Function.prototype;

  // --- setTimeout with string argument ---
  window.setTimeout = function (handler, delay, ...args) {
    if (typeof handler === 'string') {
      dispatch('eval_poison.setTimeout_string', {
        codeSnippet: handler.slice(0, 200),
        delay,
        stacktrace: new Error().stack?.split('\n').slice(1, 5),
      });
    }
    return _setTimeout.call(window, handler, delay, ...args);
  };

  // --- setInterval with string argument ---
  window.setInterval = function (handler, delay, ...args) {
    if (typeof handler === 'string') {
      dispatch('eval_poison.setInterval_string', {
        codeSnippet: handler.slice(0, 200),
        delay,
        stacktrace: new Error().stack?.split('\n').slice(1, 5),
      });
    }
    return _setInterval.call(window, handler, delay, ...args);
  };

  // --- AsyncFunction constructor ---
  try {
    const _AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
    Object.getPrototypeOf(async function () {}).constructor = new Proxy(_AsyncFunction, {
      construct(target, args) {
        dispatch('eval_poison.AsyncFunction', {
          bodySnippet: args.length > 0 ? String(args[args.length - 1]).slice(0, 200) : '',
          stacktrace: new Error().stack?.split('\n').slice(1, 5),
        });
        return Reflect.construct(target, args);
      },
      apply(target, thisArg, args) {
        dispatch('eval_poison.AsyncFunction_apply', {
          bodySnippet: args.length > 0 ? String(args[args.length - 1]).slice(0, 200) : '',
        });
        return Reflect.apply(target, thisArg, args);
      },
    });
  } catch (e) {}
})();
