(() => {
  const _fetch = window.fetch;
  const _stringify = JSON.stringify;
  const _defineProperty = Object.defineProperty;
  const _hasOwnProperty = Object.prototype.hasOwnProperty;

  let counter = 0;
  const MAX_DISPATCHES = 10000;

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
        }),
      });
    } catch (e) { /* suppress dispatch errors */ }
  }

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
    if (_hasOwnProperty.call(window, name)) continue;
    try {
      _defineProperty.call(Object, window, name, {
        get() {
          dispatch('global_preassign_break.get', {
            globalName: name,
            stacktrace: new Error().stack?.split('\n').slice(1, 5),
          });
          throw new TypeError(
            `Cannot read property '${name}': blocked by page-level pre-assignment`
          );
        },
        set(val) {
          dispatch('global_preassign_break.set_attempt', {
            globalName: name,
            valueType: typeof val,
            stacktrace: new Error().stack?.split('\n').slice(1, 5),
          });
          throw new TypeError(
            `Cannot assign to read-only property '${name}' of object '#<Window>'`
          );
        },
        configurable: false, // Break: extension cannot redefine or delete
        enumerable: false,
      });
    } catch (e) { /* skip non-configurable globals */ }
  }
})();
