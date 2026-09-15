(() => {
  // Save originals BEFORE any modifications
  const _fetch = window.fetch;
  const _stringify = JSON.stringify;
  const _defineProperty = Object.defineProperty;
  const _getOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
  const _keys = Object.keys;
  const _hasOwnProperty = Object.prototype.hasOwnProperty;

  const _seen = new Set();
  let _misc_counter = 0;
  const MAX_MISC = 100;  // cap for Object.keys / hasOwnProperty / toPrimitive

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
    // For property reads/writes: deduplicate on (api, prototype, property)
    if (data && data.prototype !== undefined && data.property !== undefined) {
      const dedupKey = `${api}|${data.prototype}|${data.property}`;
      if (_seen.has(dedupKey)) return;
      _seen.add(dedupKey);
    } else {
      // Object.keys, hasOwnProperty, toPrimitive: use separate counter
      if (_misc_counter++ > MAX_MISC) return;
    }
    try {
      _fetch.call(window, `${location.origin}${window.location.pathname}hook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: _stringify.call(JSON, {
          type: api,
          data,
          extensionId: new URLSearchParams(window.location.search).get('extensionId'),
          visit: new URLSearchParams(window.location.search).get('visit'),
					url: window.location.href,
					contextURL: document.location.href,
        }, _getCircularReplacer()),
      });
    } catch (e) { /* suppress dispatch errors */ }
  }

  // --- 1. Sentinel properties on prototypes ---
  const SENTINEL_KEYS = [
    'config', 'settings', 'options', 'data', 'id', 'key', 'value',
    'name', 'type', 'status', 'result', 'error', 'callback',
    'handler', 'state', 'cache', 'token', 'url', 'response', 'src', 'target', 'params', 'args', 'version', 'path',
  ];

  const PROTOTYPES = [
    [Object.prototype, 'Object.prototype'],
    [Array.prototype, 'Array.prototype'],
    [Set.prototype, 'Set.prototype'],
    [Map.prototype, 'Map.prototype'],
    [Function.prototype, 'Function.prototype'],
    [String.prototype, 'String.prototype'],
    [Number.prototype, 'Number.prototype'],
    [EventTarget.prototype, 'EventTarget.prototype'],
    [EventSource.prototype, 'EventSource.prototype'],
    [Boolean.prototype, 'Boolean.prototype'],
  ];

  for (const [proto, protoName] of PROTOTYPES) {
    for (const key of SENTINEL_KEYS) {
      // Skip if property already exists on this prototype
      if (_hasOwnProperty.call(proto, key)) continue;
      try {
        _defineProperty.call(Object, proto, key, {
          get() {
            dispatch('proto_poison.read', {
              prototype: protoName,
              property: key,
              accessedOn: this?.constructor?.name,
              stacktrace: new Error().stack?.split('\n').slice(1, 5),
            });
            return undefined;
          },
          set(val) {
            dispatch('proto_poison.write', {
              prototype: protoName,
              property: key,
              valueType: typeof val,
              stacktrace: new Error().stack?.split('\n').slice(1, 5),
            });
          },
          configurable: true,
          enumerable: false, // Monitor: non-enumerable, does not poison for-in
        });
      } catch (e) { /* non-configurable property, skip */ }
    }
  }

  // --- 2. Symbol.toPrimitive monitor on Object.prototype ---
  try {
    _defineProperty.call(Object, Object.prototype, Symbol.toPrimitive, {
      value: function (hint) {
        dispatch('proto_poison.toPrimitive', {
          hint,
          constructorName: this?.constructor?.name,
          stacktrace: new Error().stack?.split('\n').slice(1, 5),
        });
        if (hint === 'number') return NaN;
        if (hint === 'string') return Object.prototype.toString.call(this);
        return this.valueOf();
      },
      configurable: true,
      writable: true,
    });
  } catch (e) {}

  // --- 3. Object.keys monitor ---
  Object.keys = function (obj) {
    const result = _keys.call(Object, obj);
    dispatch('proto_poison.Object.keys', {
      keyCount: result.length,
      objectType: obj?.constructor?.name,
      stacktrace: new Error().stack?.split('\n').slice(1, 5),
    });
    return result;
  };

  // --- 4. hasOwnProperty monitor ---
  Object.prototype.hasOwnProperty = function (prop) {
    const result = _hasOwnProperty.call(this, prop);
    if (SENTINEL_KEYS.includes(prop)) {
      dispatch('proto_poison.hasOwnProperty', {
        property: prop,
        result,
        objectType: this?.constructor?.name,
        stacktrace: new Error().stack?.split('\n').slice(1, 5),
      });
    }
    return result;
  };
})();
