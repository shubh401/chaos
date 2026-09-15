(() => {
    const _nonce = Math.random().toString(36).slice(2, 6);

    const DANGEROUS_SINKS = new Set([
        'src', 'href', 'action', 'formaction', 'innerHTML', 'outerHTML',
        'srcdoc', 'data', 'value', 'textContent', 'location',
        'setAttribute', 'insertAdjacentHTML', 'innerText', 'text',
    ]);

    function sentinel(prop) {
        return `__TAINT_${prop}_${_nonce}__`;
    }

    // ── Install Layer 1: override __makeProxy ─────────────────────────────────
    // Retry until __cs_hook.js has defined __makeProxy (document_start race)
    function _install() {
        if (typeof window.__makeProxy !== 'function') {
            setTimeout(_install, 20);
            return;
        }
        if (window.__clobberTaintInstalled) return;
        window.__clobberTaintInstalled = true;

        const _origMakeProxy = window.__makeProxy;

        window.__makeProxy = function(obj, identifier, appliedOperations, arg_map, isRealValue, proxy_id) {
            const base = _origMakeProxy.apply(this, arguments);

            return new Proxy(base, {
                get(target, key) {
                    const val = Reflect.get(target, key);

                    if (typeof key !== 'string') return val;

                    // Intercept dangerous property reads
                    if (DANGEROUS_SINKS.has(key)
                            && key !== 'setAttribute'
                            && key !== 'insertAdjacentHTML') {
                        const s = sentinel(key);

                        // Dispatch taint.read — wrap in {dis:...} so store_clobber_logs
                        // stores the payload in the `data` column (reads data.dis)
                        if (typeof window.__dispatchHookData === 'function') {
                            window.__dispatchHookData('taint.read', {
                                dis: {
                                    property:   key,
                                    identifier: identifier,
                                    sentinel:   s,
                                    nonce:      _nonce,
                                },
                            });
                        }
                        return s;
                    }

                    // Wrap setAttribute to taint URL-class attribute values
                    if (key === 'setAttribute') {
                        return function(attrName, attrValue) {
                            const URL_ATTRS = new Set([
                                'src','href','action','formaction','srcdoc','data',
                                'ping','poster','manifest','codebase',
                            ]);
                            if (URL_ATTRS.has(attrName)) {
                                const s = sentinel(attrName);
                                if (typeof window.__dispatchHookData === 'function') {
                                    window.__dispatchHookData('taint.read', {
                                        dis: {
                                            property:   'setAttribute:' + attrName,
                                            identifier: identifier,
                                            sentinel:   s,
                                            nonce:      _nonce,
                                        },
                                    });
                                }
                                return val.call(target.__get_real_obj || target, attrName, s);
                            }
                            return val.call(target.__get_real_obj || target, attrName, attrValue);
                        };
                    }

                    // Wrap insertAdjacentHTML
                    if (key === 'insertAdjacentHTML') {
                        return function(pos, html) {
                            const s = sentinel('insertAdjacentHTML');
                            if (typeof window.__dispatchHookData === 'function') {
                                window.__dispatchHookData('taint.read', {
                                    dis: {
                                        property:   'insertAdjacentHTML',
                                        identifier: identifier,
                                        sentinel:   s,
                                        nonce:      _nonce,
                                    },
                                });
                            }
                            return val.call(target.__get_real_obj || target, pos, s);
                        };
                    }

                    return val;
                }
            });
        };

        // Log installation so we can confirm it ran
        if (typeof window.__dispatchHookData === 'function') {
            window.__dispatchHookData('taint.installed', {
                dis: { nonce: _nonce, version: '2026-04-26' },
            });
        }
    }

    // Install immediately or after a short delay
    if (typeof window.__makeProxy === 'function') {
        _install();
    } else {
        setTimeout(_install, 20);
        document.addEventListener('DOMContentLoaded', _install);
    }
})();
