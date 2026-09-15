(() => {
  // Current lifecycle stage — updated on each browser lifecycle event.
  window.__v2_lifecycle_stage = 'document_start';

  // High-resolution monotonic timestamp (ms since navigationStart).
  window.__v2_timestamp = function () {
    return performance.now();
  };

  document.addEventListener('DOMContentLoaded', function () {
    window.__v2_lifecycle_stage = 'DOMContentLoaded';
  });

  window.addEventListener('load', function () {
    window.__v2_lifecycle_stage = 'load';
  });

  window.addEventListener('beforeunload', function () {
    window.__v2_lifecycle_stage = 'beforeunload';
  });
})();
