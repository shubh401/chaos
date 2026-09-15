(() => {
  const _fetch = window.fetch;
  const _stringify = JSON.stringify;
  const _defineProperty = Object.defineProperty;
  const _hasOwnProperty = Object.prototype.hasOwnProperty;

  let counter = 0;
  const MAX_DISPATCHES = 10000;

  const _getCircularReplacer = () => {
    const seen = new WeakSet();
    return (key, value) => {
      if (typeof value === 'object' && value !== null) {
        if (seen.has(value)) return '[Circular]';
        seen.add(value);
      }
      return value;
    };
  };

  function dispatch(api, data) {
    if (counter++ > MAX_DISPATCHES) return;
    try {
      _fetch.call(window, `${location.origin}${window.location.pathname}hook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: _stringify.call(JSON, {
          type: api,
          data,
          extensionId: new URLSearchParams(window.location.search).get('extensionId'),
          visit: new URLSearchParams(window.location.search).get('visit'),
        }, _getCircularReplacer()),
      });
    } catch (e) { /* suppress dispatch errors */ }
  }

  // Common global names used by extensions and web analytics
  const GLOBAL_NAMES = [
    'config', 'settings', 'options', 'app', 'api', 'sdk', 'manager',
    'controller', 'service', 'client', 'plugin', 'module', 'adapter',
    '_gaq', '_ga', 'dataLayer', 'ga', 'gtag', 'fbq', 'twq', 'analytics',
    'tracker', 'logger', 'debug', 'utils', 'helpers', 'constants',
    'store', 'state', 'cache', 'registry', 'dispatcher', 'emitter',
    'bus', 'router', 'routes', 'pages', 'views', 'models',
    'user', 'session', 'auth', 'token', 'credentials',
    'request', 'response', 'xhr', 'ajax',
    'observer', 'listener', 'handler', 'callback', 'hooks',
    'queue', 'tasks', 'jobs', 'workers', 'threads',
    'db', 'database', 'storage', 'repo', 'repository',
    'ui', 'dom', 'widgets', 'components',
    'VERSION', 'ENV', 'DEBUG', 'PROD', 'DEV',
    'namespace', 'scope', 'context', 'env', 'environment',
    '__ext', '__extension', '__content', '__background',
    'chrome_ext', 'browser_ext', 'webext',
  ];

  for (const name of GLOBAL_NAMES) {
    // Skip if already defined (non-configurable) or built-in
    if (_hasOwnProperty.call(window, name)) continue;
    try {
      const proxy = new Proxy({}, {
        get(target, prop) {
          dispatch('global_preassign.get', {
            globalName: name,
            property: String(prop),
            stacktrace: new Error().stack?.split('\n').slice(1, 5),
          });
          return target[prop];
        },
        set(target, prop, value) {
          dispatch('global_preassign.set', {
            globalName: name,
            property: String(prop),
            valueType: typeof value,
            stacktrace: new Error().stack?.split('\n').slice(1, 5),
          });
          target[prop] = value;
          return true;
        },
        apply(target, thisArg, args) {
          dispatch('global_preassign.call', {
            globalName: name,
            argCount: args.length,
            stacktrace: new Error().stack?.split('\n').slice(1, 5),
          });
          return undefined;
        },
      });

      _defineProperty.call(Object, window, name, {
        get() { return proxy; },
        set(val) {
          // Allow extension to overwrite (configurable: true)
          dispatch('global_preassign.overwrite', {
            globalName: name,
            newValueType: typeof val,
            stacktrace: new Error().stack?.split('\n').slice(1, 5),
          });
          _defineProperty.call(Object, window, name, {
            value: val,
            writable: true,
            configurable: true,
            enumerable: true,
          });
        },
        configurable: true,
        enumerable: false,
      });
    } catch (e) { /* skip non-configurable globals */ }
  }
})();
