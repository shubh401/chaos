(() => {
    // Save fetch reference immediately — before any extension can override it.
    // This script runs as a PAGE SCRIPT (main world). window.__dispatchHookData
    // is in the ISOLATED WORLD and is NOT visible here. We must use fetch directly.
    const _fetch = window.fetch;
    const _params = new URLSearchParams(window.location.search);
    const _extId  = _params.get('extensionId');
    const _visit  = _params.get('visit');
    const _origin = window.location.origin;
    const _path   = window.location.pathname;

    function _dispatch(api, data) {
        if (!_extId || !_fetch) return;
        try {
            _fetch.call(window, `${_origin}${_path}hook`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({
                    type:        api,
                    data:        data,
                    extensionId: _extId,
                    visit:       _visit,
                    url:         window.location.href,
                    contextURL:  document.location.href,
                }),
            });
        } catch (e) { /* suppress */ }
    }

    const _config  = window.__CLOBBER_TRIGGER_CONFIG || { globals: [], methods: [] };
    const _globals = _config.globals || [];
    const _methods = _config.methods || [];

    function _tryInvoke() {
        const results = {};

        for (const name of _globals) {
            const val  = window[name];
            const type = typeof val;
            results[name] = { type, is_element: val instanceof HTMLElement };

            if (type === 'function') {
                try { val(); } catch (e) { results[name].error = String(e).slice(0, 100); }
            } else if (val && type === 'object' && !(val instanceof HTMLElement)) {
                for (const common of ['toggle', 'show', 'open', 'init', 'start', 'enable', 'activate']) {
                    if (typeof val[common] === 'function') {
                        try { val[common](); } catch (e) {}
                        results[name + '.' + common] = { invoked: true };
                    }
                }
            }
        }

        for (const dotted of _methods) {
            const parts  = dotted.split('.');
            const obj    = parts[0];
            const method = parts.slice(1).join('.');
            try {
                const base = window[obj];
                if (base && typeof base[method] === 'function') {
                    base[method]();
                    results[dotted] = { invoked: true };
                }
            } catch (e) {}
        }

        // Dispatch via direct fetch to /hook — works from main world
        _dispatch('clobber_trigger.invocation', {
            config_globals: _globals,
            config_methods: _methods,
            results:        results,
            timestamp:      performance.now(),
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        setTimeout(_tryInvoke, 300);
        setTimeout(_tryInvoke, 1500);
    });
})();
