(() => {
  const _fetch = window.fetch;
  const _stringify = JSON.stringify;
  const _defineProperty = Object.defineProperty;
  const _hasOwnProperty = Object.prototype.hasOwnProperty;

  const _seen = new Set();
  let _misc_counter = 0;
  const MAX_MISC = 50;

  function dispatch(api, data) {
    if (data && data.prototype !== undefined && data.property !== undefined) {
      const dedupKey = `${api}|${data.prototype}|${data.property}`;
      if (_seen.has(dedupKey)) return;
      _seen.add(dedupKey);
    } else {
      if (_misc_counter++ > MAX_MISC) return;
    }
    try {
      _fetch.call(window, `${location.origin}${window.location.pathname}hook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: _stringify.call(JSON, {
          type: api, data,
          extensionId: new URLSearchParams(window.location.search).get('extensionId'),
          visit: new URLSearchParams(window.location.search).get('visit'),
					url: window.location.href,
					contextURL: document.location.href,
        }),
      });
    } catch (e) {}
  }

  // --- 1. Sentinel properties: enumerable + non-configurable + throwing ---
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
      if (_hasOwnProperty.call(proto, key)) continue;
      try {
        _defineProperty.call(Object, proto, key, {
          get() {
            dispatch('proto_poison_break.read', {
              prototype: protoName, property: key,
            });
            throw new Error(`Prototype pollution: ${protoName}.${key} access denied`);
          },
          set() {
            throw new Error(`Prototype pollution: ${protoName}.${key} write denied`);
          },
          configurable: false, // Cannot be removed by extension
          enumerable: true,    // Poisons for...in loops
        });
      } catch (e) {}
    }
  }

  // --- 2. Corrupt toJSON on Object.prototype (breaks JSON.stringify on any object) ---
  try {
    _defineProperty.call(Object, Object.prototype, 'toJSON', {
      value: function () {
        throw new Error('toJSON poisoned');
      },
      configurable: false,
      writable: false,
    });
  } catch (e) {}

  // --- 3. Corrupt valueOf and toString ---
  try {
    const _origValueOf = Object.prototype.valueOf;
    Object.prototype.valueOf = function () {
      // Allow primitives to still work
      if (this === null || this === undefined) return this;
      if (typeof this !== 'object' && typeof this !== 'function') {
        return _origValueOf.call(this);
      }
      throw new Error('valueOf poisoned');
    };
  } catch (e) {}

  try {
    Object.prototype.toString = function () {
      throw new Error('toString poisoned');
    };
  } catch (e) {}

  // --- 4. Symbol.toPrimitive — returns wrong types ---
  try {
    _defineProperty.call(Object, Object.prototype, Symbol.toPrimitive, {
      value: function (hint) {
        if (hint === 'number') return 'not_a_number'; // causes NaN cascades
        if (hint === 'string') return 42;             // wrong type
        return null;
      },
      configurable: false,
    });
  } catch (e) {}

  // --- 5. Symbol.iterator — makes all objects "iterable" with garbage ---
  try {
    _defineProperty.call(Object, Object.prototype, Symbol.iterator, {
      value: function* () {
        yield '__poisoned__';
      },
      configurable: false,
    });
  } catch (e) {}

  // --- 6. hasOwnProperty always returns true ---
  try {
    Object.prototype.hasOwnProperty = function () {
      return true;
    };
  } catch (e) {}
})();
