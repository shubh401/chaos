(() => {
  const _fetch = window.fetch;
  const _stringify = JSON.stringify;
  const _Promise = Promise;
  const _PromiseThen = Promise.prototype.then;
  const _PromiseReject = Promise.reject;

  let counter = 0;
  const MAX = 5000;

  // Dispatch using saved originals to avoid self-poisoning
  function dispatch(api, data) {
    if (counter++ > MAX) return;
    try {
      const p = _fetch.call(window, `${location.origin}${window.location.pathname}hook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: _stringify.call(JSON, {
          type: api, data,
          extensionId: new URLSearchParams(window.location.search).get('extensionId'),
          visit: new URLSearchParams(window.location.search).get('visit'),
        }),
      });
      _PromiseThen.call(p, function () {}, function () {});
    } catch (e) {}
  }

  // .then() — chain stalls silently (never resolves)
  Promise.prototype.then = function (onFulfilled, onRejected) {
    dispatch('promise_break.then', {
      stacktrace: new Error().stack?.split('\n').slice(1, 5),
    });
    return new _Promise(function () {}); // never settles
  };

  // .catch() — always fires with poisoned error
  Promise.prototype.catch = function (onRejected) {
    dispatch('promise_break.catch', {
      stacktrace: new Error().stack?.split('\n').slice(1, 5),
    });
    if (typeof onRejected === 'function') {
      try { onRejected(new Error('Promise chain poisoned')); } catch (e) {}
    }
    return new _Promise(function () {});
  };

  // .finally() — never fires
  Promise.prototype.finally = function () {
    dispatch('promise_break.finally', {});
    return new _Promise(function () {});
  };

  // Promise.resolve — returns a rejected Promise
  Promise.resolve = function () {
    dispatch('promise_break.resolve', {});
    return _PromiseReject.call(_Promise, new Error('Promise.resolve poisoned'));
  };

  // Promise.reject — still rejects but .catch is already broken so it cascades
  Promise.reject = function (reason) {
    dispatch('promise_break.reject', {});
    return _PromiseReject.call(_Promise, reason || new Error('Promise.reject poisoned'));
  };

  // Promise.all — never settles
  Promise.all = function () {
    dispatch('promise_break.all', {});
    return new _Promise(function () {});
  };

  // Promise.allSettled — never settles
  Promise.allSettled = function () {
    dispatch('promise_break.allSettled', {});
    return new _Promise(function () {});
  };

  // Promise.race — never settles
  Promise.race = function () {
    dispatch('promise_break.race', {});
    return new _Promise(function () {});
  };

  // Promise.any — always rejects
  if (typeof Promise.any === 'function') {
    Promise.any = function () {
      dispatch('promise_break.any', {});
      return _PromiseReject.call(_Promise, new AggregateError([], 'Promise.any poisoned'));
    };
  }
})();
