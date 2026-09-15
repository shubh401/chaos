(() => {
  const _fetch = window.fetch;
  const _stringify = JSON.stringify;
  const _PromiseThen = Promise.prototype.then;
  const _PromiseCatch = Promise.prototype.catch;
  const _PromiseFinally = Promise.prototype.finally;
  const _PromiseResolve = Promise.resolve;
  const _PromiseReject = Promise.reject;
  const _PromiseAll = Promise.all;
  const _PromiseAllSettled = Promise.allSettled;
  const _PromiseRace = Promise.race;
  const _PromiseAny = Promise.any;

  let counter = 0;
  const MAX = 10000;

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
      // Use saved .then to avoid recursion
      _PromiseThen.call(p, function () {}, function () {});
    } catch (e) {}
  }

  Promise.prototype.then = function (onFulfilled, onRejected) {
    dispatch('promise.then', {
      hasFulfilled: typeof onFulfilled === 'function',
      hasRejected: typeof onRejected === 'function',
      stacktrace: new Error().stack?.split('\n').slice(1, 5),
    });
    return _PromiseThen.call(this, onFulfilled, onRejected);
  };

  Promise.prototype.catch = function (onRejected) {
    dispatch('promise.catch', {
      hasHandler: typeof onRejected === 'function',
      stacktrace: new Error().stack?.split('\n').slice(1, 5),
    });
    return _PromiseCatch.call(this, onRejected);
  };

  Promise.prototype.finally = function (onFinally) {
    dispatch('promise.finally', {
      hasHandler: typeof onFinally === 'function',
      stacktrace: new Error().stack?.split('\n').slice(1, 5),
    });
    return _PromiseFinally.call(this, onFinally);
  };

  Promise.resolve = function (value) {
    dispatch('Promise.resolve', { valueType: typeof value });
    return _PromiseResolve.call(Promise, value);
  };

  Promise.reject = function (reason) {
    dispatch('Promise.reject', { reasonType: typeof reason });
    return _PromiseReject.call(Promise, reason);
  };

  Promise.all = function (iterable) {
    dispatch('Promise.all', { stacktrace: new Error().stack?.split('\n').slice(1, 5) });
    return _PromiseAll.call(Promise, iterable);
  };

  Promise.allSettled = function (iterable) {
    dispatch('Promise.allSettled', { stacktrace: new Error().stack?.split('\n').slice(1, 5) });
    return _PromiseAllSettled.call(Promise, iterable);
  };

  Promise.race = function (iterable) {
    dispatch('Promise.race', { stacktrace: new Error().stack?.split('\n').slice(1, 5) });
    return _PromiseRace.call(Promise, iterable);
  };

  if (typeof _PromiseAny === 'function') {
    Promise.any = function (iterable) {
      dispatch('Promise.any', { stacktrace: new Error().stack?.split('\n').slice(1, 5) });
      return _PromiseAny.call(Promise, iterable);
    };
  }
})();
