(() => {
  const _ts = window.__v2_timestamp || (() => performance.now());
  const _stage = () => window.__v2_lifecycle_stage || 'unknown';

  // --- __dispatchHookData (defined by hook.js / hook_break.js / hook_logger.js) ---
  // Injects v2 fields into the `data` sub-object before the original serializes it.
  if (typeof window.__dispatchHookData === 'function') {
    const _origHook = window.__dispatchHookData;
    window.__dispatchHookData = async function (api, data) {
      if (data && typeof data === 'object') {
        data.__v2_client_ts = _ts();
        data.__v2_lifecycle_stage = _stage();
      }
      return _origHook.call(this, api, data);
    };
  }

  // --- __dispatchPollData ---
  // hook.js defines:  __dispatchPollData(data, stage)  — data is an object, stage is a string
  // raider.js defines: __dispatchPollData(type, data)  — type is a string, data is an object
  // We use ...args and inject into whichever argument is the data object.
  if (typeof window.__dispatchPollData === 'function') {
    const _origPoll = window.__dispatchPollData;
    window.__dispatchPollData = async function (...args) {
      for (let i = 0; i < args.length; i++) {
        if (args[i] && typeof args[i] === 'object') {
          args[i].__v2_client_ts = _ts();
          args[i].__v2_lifecycle_stage = _stage();
          break;
        }
      }
      return _origPoll.apply(this, args);
    };
  }

  // --- __dispatchMutationData (defined by mutation.js) ---
  // The original constructs the full POST payload internally, so we replace it entirely.
  // We add __v2_client_ts and __v2_lifecycle_stage as top-level fields AND inside the
  // data object (so they survive into the added_nodes JSONB column on the server).
  if (typeof window.__dispatchMutationData === 'function') {
    window.__dispatchMutationData = async function (data) {
      const client_ts = _ts();
      const lifecycle_stage = _stage();

      if (data && typeof data === 'object') {
        data.__v2_client_ts = client_ts;
        data.__v2_lifecycle_stage = lifecycle_stage;
      }

      let parsed_data;
      try {
        parsed_data = JSON.stringify(
          {
            type: 'mutation',
            data,
            extensionId: new URLSearchParams(window.location.search).get('extensionId'),
            url: window.location.href,
            contextURL: document.location.href,
            visit: new URLSearchParams(window.location.search).get('visit'),
            __v2_client_ts: client_ts,
            __v2_lifecycle_stage: lifecycle_stage,
          },
          window.__getCircularReplacer()
        );
        fetch(`${location.origin}${window.location.pathname}mutation`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: parsed_data,
        });
      } catch (e) {
        if (typeof window.__dispatchErrorLog === 'function') {
          window.__dispatchErrorLog({
            type: window.top.location.search,
            source: '__dispatchMutationData',
            error: { stack: e.stack, message: e.message, name: e.name },
            url: window.location.href,
            contextURL: document.location.href,
            extensionId: new URLSearchParams(window.location.search).get('extensionId'),
            visit: new URLSearchParams(window.location.search).get('visit'),
          });
        }
      }
    };
  }

  // --- __dispatchErrorLog (defined by mutation.js / raider.js) ---
  if (typeof window.__dispatchErrorLog === 'function') {
    const _origError = window.__dispatchErrorLog;
    window.__dispatchErrorLog = async function (data) {
      if (data && typeof data === 'object') {
        data.__v2_client_ts = _ts();
        data.__v2_lifecycle_stage = _stage();
      }
      return _origError.call(this, data);
    };
  }

  // --- __exposedErrorLogger (defined by hook.js / hook_logger.js) ---
  if (typeof window.__exposedErrorLogger === 'function') {
    const _origExposed = window.__exposedErrorLogger;
    window.__exposedErrorLogger = function (data) {
      if (data && typeof data === 'object') {
        data.__v2_client_ts = _ts();
        data.__v2_lifecycle_stage = _stage();
      }
      return _origExposed.call(this, data);
    };
  }
})();
