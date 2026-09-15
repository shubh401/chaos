from django.http import HttpRequest, HttpResponse, FileResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET
from django.shortcuts import render
from django.conf import settings
from server.db import *
from config import *

@require_GET
@cache_control(max_age=60 * 60 * 24 * 365, immutable=True, public=True)
def favicon(request: HttpRequest) -> FileResponse:
    """
    Handles the request for the favicon.ico file.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        FileResponse: The response containing the favicon.ico file.
    """
    if not request: return response
    favicon_path = os.path.join(settings.STATIC_ROOT, 'img', 'favicon.ico')
    response = FileResponse(open(favicon_path, 'rb'))
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD"
    response["Access-Control-Allow-Headers"] = "Authorization, Origin, X-Requested-With, Content-Type, Accept"
    return response

def csp_endpoint(request: HttpRequest) -> HttpResponse:
    """
    Handles the request for the Content Security Policy (CSP) endpoint.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The response indicating the status of the CSP endpoint.
    """
    response = HttpResponse()
    try:
        if request == None:
            response.content = "Invalid/Empty Request!"
            return response
        parsed_data = parse_request_data(request)
        if not parsed_data or not isinstance(parsed_data, dict):
            response.content = "Invalid/Empty Request!"
            return response
        response.content = store_csp_logs(parsed_data)
    except:
        logging.error("Exception occurred in csp_endpoint(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        response.content = "Error!"
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD"
    response["Access-Control-Allow-Headers"] = "Authorization, Origin, X-Requested-With, Content-Type, Accept"    
    return response

def scripts(request: HttpRequest) -> HttpResponse:
    """
    Handles the request for JavaScript files.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        FileResponse: The response containing the requested JavaScript file.
    """
    response = HttpResponse()
    try:
        if request == None:
            response.content = "Invalid/Empty Request!"
        else:
            if request.GET["name"] == "extension_id_placeholder.js":
                response.content = ""
            else:
                script_path = os.path.join(settings.STATIC_ROOT, 'scripts', request.GET["name"])
                response = FileResponse(open(script_path, 'rb'))    
            response["Content-Type"] = "application/javascript"
    except:
        logging.error("Exception occurred in scripts(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        response.content = "Error!"  
    return response

def images(request: HttpRequest) -> FileResponse:
    """
    Handles the request for image files.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        FileResponse: The response containing the requested image file.
    """
    response = HttpResponse()
    try:
        if request == None:
            response.content = "Invalid/Empty Request!"
        else:
            image_path = os.path.join(settings.STATIC_ROOT, 'img', request.GET["name"])
            response = FileResponse(open(image_path, 'rb'))    
            response["Content-Type"] = "image/jpeg"
    except:
        logging.error("Exception occurred in images(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        response.content = "Error!"
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD"
    response["Access-Control-Allow-Headers"] = "Authorization, Origin, X-Requested-With, Content-Type, Accept"    
    return response

def media(request: HttpRequest) -> FileResponse:
    """
    Handles the request for media files.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        FileResponse: The response containing the requested media file.
    """
    response = HttpResponse()
    try:
        if request == None:
            response.content = "Invalid/Empty Request!"
        else:
            media_path = os.path.join(settings.STATIC_ROOT, 'media', request.GET["name"])
            response = FileResponse(open(media_path, 'rb'))
            response['Content-Disposition'] = 'inline; filename=%s' % request.GET["name"]
    except:
        logging.error("Exception occurred in media(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        response.content = "Error"   
    return response

def parse_request_data(request: HttpRequest) -> dict:
    """
    Parses the request data from the HTTP request object.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        dict: The parsed request data.
    """
    data = None
    try:
        data = json.loads(str(request.body.decode('utf-8', errors='ignore').replace("\x00", "").replace("\u0000", "")))
    except:
        try:
            data = json.loads(str(request.body.decode('utf-32', errors='ignore').replace("\x00", "").replace("\u0000", "")))
        except:
            try:
                data = json.loads(str(request.body.decode('utf-8-bom', errors='ignore').replace("\x00", "").replace("\u0000", "")))
            except:
                pass
    return data

def error_logs(request: HttpRequest) -> HttpResponse:
    """
    Handles the request for error logs.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The response indicating the status of the error logs request.
    """
    response = HttpResponse()
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD"
    response["Access-Control-Allow-Headers"] = "Authorization, Origin, X-Requested-With, Content-Type, Accept"  
    try:
        parsed_data = parse_request_data(request)
        if not parsed_data: response.content = 'Error!'
        else: response.content = store_error_logs(parsed_data)
    except:
        logging.error("Exception occurred in error_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        response.content = "Error"
    return response

def hook_logs(request: HttpRequest) -> HttpResponse:
    """
    Handles the request for hook logs.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The response indicating the status of the hook logs request.
    """
    response = HttpResponse()
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD"
    response["Access-Control-Allow-Headers"] = "Authorization, Origin, X-Requested-With, Content-Type, Accept"  
    try:
        if request == None:
            response.content = "Invalid/Empty Request!"
            return response
        parsed_data = parse_request_data(request)
        if not parsed_data or not isinstance(parsed_data, dict):
            response.content = "Invalid/Empty Request!"
            return response
        response.content = store_invocation_logs(parsed_data)
    except:
        logging.error("Exception occurred in hook_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        response.content = "Error" 
    return response

def clobber_logs(request: HttpRequest) -> HttpResponse:
    """
    Handles the request for hook logs.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The response indicating the status of the hook logs request.
    """
    response = HttpResponse()
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD"
    response["Access-Control-Allow-Headers"] = "Authorization, Origin, X-Requested-With, Content-Type, Accept"  
    try:
        if request == None:
            response.content = "Invalid/Empty Request!"
            return response
        parsed_data = parse_request_data(request)
        if not parsed_data or not isinstance(parsed_data, dict):
            response.content = "Invalid/Empty Request!"
            return response
        response.content = store_clobber_logs(parsed_data)
    except:
        logging.error("Exception occurred in clobber_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        response.content = "Error" 
    return response

def mutation_logs(request: HttpRequest) -> HttpResponse:
    """
    Handles the request for mutation logs.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The response indicating the status of the mutation logs request.
    """
    response = HttpResponse()
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD"
    response["Access-Control-Allow-Headers"] = "Authorization, Origin, X-Requested-With, Content-Type, Accept"  
    try:
        if request == None:
            response.content = "Invalid/Empty Request!"
            return response
        parsed_data = parse_request_data(request)
        if not parsed_data or not isinstance(parsed_data, dict):
            response.content = "Invalid/Empty Request!"
            return response
        response.content = store_mutation_logs(parsed_data)
    except:
        logging.error("Exception occurred in mutation_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        response.content = "Error"
    return response

def poll_logs(request: HttpRequest) -> HttpResponse:
    """
    Handles the request for poll logs.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The response indicating the status of the poll logs request.
    """
    response = HttpResponse()
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD"
    response["Access-Control-Allow-Headers"] = "Authorization, Origin, X-Requested-With, Content-Type, Accept"  
    try:
        if not request:
            response.content = "Invalid/Empty Request!"
            return response
        parsed_data = parse_request_data(request)
        if not parsed_data or not isinstance(parsed_data, dict) or not parsed_data.get("type"):
            response.content = "Invalid/Empty Request!"
            return response
        if parsed_data.get("type", "") == "cookies": response.content = store_cookie_logs(parsed_data)
        elif parsed_data.get("type", "") == "idb": response.content = store_idb_logs(parsed_data)
        elif parsed_data.get("type", "") == "message": response.content = store_message_logs(parsed_data)
        elif parsed_data.get("type", "") in ("local", "session"): response.content = store_storage_logs(parsed_data)
        elif parsed_data.get("type", "") == "variable": response.content = store_variable_logs(parsed_data)
        elif parsed_data.get("type", "") == "cs_trace": response.content = store_cs_trace_logs(parsed_data)
    except:
        logging.error("Exception occurred in poll_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        response.content = "Error"
    return response

def coverage_logs(request: HttpRequest) -> HttpResponse:
    """
    Handles the request for coverage logs.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The response indicating the status of the coverage logs request.
    """
    response = HttpResponse()
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD"
    response["Access-Control-Allow-Headers"] = "Authorization, Origin, X-Requested-With, Content-Type, Accept"  
    try:
        if not request:
            response.content = "Invalid/Empty Request!"
            return response
        parsed_data = parse_request_data(request)
        if not parsed_data or not isinstance(parsed_data, dict):
            response.content = "Invalid/Empty Request!"
            return response
        response.content = store_coverage_logs(parsed_data)
    except:
        logging.error("Exception occurred in coverage_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        response.content = "Error"
    return response

def proxy_logs(request: HttpRequest) -> HttpResponse:
    """
    Handles the request for proxy logs.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The response indicating the status of the proxy logs request.
    """
    response = HttpResponse()
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD"
    response["Access-Control-Allow-Headers"] = "Authorization, Origin, X-Requested-With, Content-Type, Accept"  
    try:
        if not request:
            response.content = "Invalid/Empty Request!"
            return response
        parsed_data = parse_request_data(request)
        if not parsed_data or not isinstance(parsed_data, dict):
            response.content = "Invalid/Empty Request!"
            return response
        response.content = store_proxy_logs(parsed_data)
    except:
        logging.error("Exception occurred in proxy_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        response.content = "Error"
    return response

def preassign_script(request: HttpRequest) -> HttpResponse:
    """
    Dynamically generates a per-extension global pre-assignment break script.

    Queries extension_vars (static analysis) and variable_log (dynamic observation)
    for the given extensionId, then generates JS that locks those globals with
    Object.defineProperty (configurable: false, getters throw).

    Returns synchronous JavaScript — loaded via <script src> in the template,
    so it blocks parsing and executes before the extension's content script.
    """
    response = HttpResponse()
    response["Content-Type"] = "application/javascript"
    response["Access-Control-Allow-Origin"] = "*"
    try:
        extension_id = request.GET.get("extensionId", "")
        if not extension_id:
            response.content = "// No extensionId provided"
            return response

        variables = get_extension_variables(extension_id)
        if not variables:
            response.content = "// No variables found for extension: %s" % extension_id
            return response

        vars_json = json.dumps(variables)
        response.content = """// Auto-generated global pre-assignment break script for: %s
(() => {
  const _fetch = window.fetch;
  const _stringify = JSON.stringify;
  const _defineProperty = Object.defineProperty;

  let counter = 0;
  const MAX = 5000;

  function dispatch(api, data) {
    if (counter++ > MAX) return;
    try {
      _fetch.call(window, location.origin + window.location.pathname + 'hook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: _stringify.call(JSON, {
          type: api, data: data,
          extensionId: new URLSearchParams(window.location.search).get('extensionId'),
          visit: new URLSearchParams(window.location.search).get('visit'),
        }),
      });
    } catch (e) {}
  }

  const VARS = %s;

  for (const varName of VARS) {
    if (varName in window) continue;
    try {
      _defineProperty.call(Object, window, varName, {
        get() {
          dispatch('global_preassign_break.access', { variable: varName });
          throw new Error('Global variable access denied: ' + varName);
        },
        set() {
          dispatch('global_preassign_break.assign', { variable: varName });
          throw new Error('Global variable assignment denied: ' + varName);
        },
        configurable: false,
        enumerable: true,
      });
    } catch (e) {}
  }
})();
""" % (extension_id, vars_json)
    except:
        logging.error("Exception occurred in preassign_script(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        response.content = "// Error generating script"
    return response

def gbs_trace_script(request: HttpRequest) -> HttpResponse:
    """
    Dynamically generates a per-extension GBS trace script.

    Reads variable names observed in the pre-crawl variable_log (suffix from
    GBS_PRE_SUFFIX env var, default 2026_GBS_PRE) and generates JavaScript that
    installs transparent defineProperty hooks for those names at document_start.

    Unlike preassign_script (which throws), these hooks are non-destructive:
    getters and setters still work normally — they only record the access order
    (get/set sequence) and dispatch a cs_trace event via __dispatchPollData.

    The script is deployed as a content script (via manifest injection), so it
    runs in the isolated world at document_start — before the extension's own CS.
    When the extension later reads window.X in a DOMContentLoaded callback, the
    hook is already installed and records the access order.

    Returns synchronous JavaScript — written to __gbs_trace.js in the extension
    directory and referenced directly in manifest.json.
    """
    response = HttpResponse()
    response["Content-Type"] = "application/javascript"
    response["Access-Control-Allow-Origin"] = "*"
    try:
        extension_id = request.GET.get("extensionId", "")
        pre_suffix   = request.GET.get("preSuffix", os.getenv("GBS_PRE_SUFFIX", "2026_GBS_PRE"))
        if not extension_id:
            response.content = "// No extensionId provided"
            return response

        variables = get_gbs_trace_variables(extension_id, pre_suffix)
        if not variables:
            response.content = "// No variables found for extension: %s" % extension_id
            return response

        vars_json = json.dumps(variables)
        response.content = """// Auto-generated GBS trace script for: %s
// Installs transparent defineProperty hooks for known CS globals.
// Records get/set access order; dispatches cs_trace via __dispatchPollData.
(() => {
  const _defineProperty = Object.defineProperty;
  const _hasOwn = Object.prototype.hasOwnProperty;

  const _traces = {};
  const _values = {};

  function _hook(name) {
    if (_hasOwn.call(window, name)) return;
    try {
      _defineProperty.call(Object, window, name, {
        configurable: true,
        enumerable:   true,
        get() {
          if (!_traces[name]) _traces[name] = [];
          _traces[name].push('get');
          return _values[name];
        },
        set(v) {
          if (!_traces[name]) _traces[name] = [];
          _traces[name].push('set');
          _values[name] = v;
        },
      });
    } catch (_) {}
  }

  const VARS = %s;
  for (const name of VARS) { _hook(name); }

  document.addEventListener('DOMContentLoaded', function () {
    const formatted = {};
    for (const [name, ops] of Object.entries(_traces)) {
      if (ops.length > 0) formatted[name] = ops.join(' - ');
    }
    if (Object.keys(formatted).length > 0 &&
        typeof window.__dispatchPollData === 'function') {
      window.__dispatchPollData('cs_trace', {
        traces: formatted,
        stage:  'gbs-trace',
      });
    }
  });
})();
""" % (extension_id, vars_json)
    except:
        logging.error("Exception occurred in gbs_trace_script(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        response.content = "// Error generating script"
    return response


# ---------------------------------------------------------------------------
# Honey body extraction for clobber_payload
#
# The clobber_payload endpoint used to return a near-empty page (<body><%s>
# <h1>New Test Page</h1></body>). That gives content scripts no realistic DOM
# surface: password managers never see a form, translators never see a <p
# lang=...>, ad blockers never see an ad slot. Extensions early-return when
# their anchor selectors find nothing, so coverage delta between pass 1
# (empty payload) and pass 2 (real payload) is near zero for most of the
# population. See INA_FINDINGS_v1.md for the concrete numbers.
#
# Fix: extract the rich honey <body> from isolated/templates/isolated/
# clobber_proxy.html (login form, multi-lang paragraphs, images, semantic
# nav, shopping sections) and PREPEND the per-extension attacker payload
# inside it. Prepending (not appending) is the realistic DOM-clobbering
# threat model — attacker-controlled user content sits at the TOP of a
# legitimate page (comments, forum posts, markdown injections). When IDs
# collide, first-in-document-order wins getElementById, so the attacker
# element wins — exactly the real-world scenario.
#
# Body is read once on first use and cached in-process.
# ---------------------------------------------------------------------------
_HONEY_BODY_CACHE = {'html': None}


def _load_honey_body():
    """Return the inner HTML of <body>...</body> from clobber_proxy.html.

    Cached after the first read. On any failure (template missing, no <body>
    tags) we fall back to an empty string so the endpoint still serves a
    functional page — the per-extension attacker payload still loads.
    """
    if _HONEY_BODY_CACHE['html'] is not None:
        return _HONEY_BODY_CACHE['html']
    try:
        path = os.path.join(
            settings.BASE_DIR,
            'isolated', 'templates', 'isolated', 'clobber_proxy.html',
        )
        with open(path, 'r', encoding='utf-8') as fh:
            html = fh.read()
        lo = html.lower()
        start = lo.find('<body')
        if start < 0:
            _HONEY_BODY_CACHE['html'] = ''
            return ''
        start = html.find('>', start)
        if start < 0:
            _HONEY_BODY_CACHE['html'] = ''
            return ''
        start += 1
        end = lo.rfind('</body>')
        if end < 0 or end <= start:
            _HONEY_BODY_CACHE['html'] = ''
            return ''
        body_inner = html[start:end]
        # Strip any <script> tags from the honey body — the clobber_payload
        # endpoint loads its own instrumentation scripts via <head>; we don't
        # want honey-page scripts (lifecycle_tracker, mutation, etc.) running
        # twice. A simple regex strip is fine here: the honey body has only
        # a couple of <script> tags and no tricky nesting.
        import re
        body_inner = re.sub(
            r'<script\b[^>]*>.*?</script\s*>', '', body_inner,
            flags=re.IGNORECASE | re.DOTALL,
        )
        _HONEY_BODY_CACHE['html'] = body_inner
        return body_inner
    except Exception:
        logging.error("_load_honey_body: %s\n" % "-".join(traceback.format_exc().split("\n")))
        _HONEY_BODY_CACHE['html'] = ''
        return ''


def clobber_payload(request: HttpRequest) -> HttpResponse:
    """
    Dynamically generates a per-extension DOM clobbering page.

    Queries extension_clobber_payloads for the given extensionId and returns
    an HTML page that:
      1. Loads instrumentation scripts (lifecycle_tracker, sparkmd5,
         mutation_hashes, mutation, v2_dispatch) in <head>
      2. PREPENDS the per-extension attacker payload into <body>
      3. Follows the attacker payload with the honey body extracted from
         isolated/templates/isolated/clobber_proxy.html (login form,
         multi-lang article text, nav, semantic sections — the realistic
         DOM surface content scripts expect to find on a real page)

    Why prepend the attacker payload rather than append: getElementById /
    first-match selectors return the first element in document order, so
    prepending gives the attacker element priority on collisions — the
    canonical DOM-clobbering scenario. See INA_FINDINGS_v1.md §7.
    """
    response = HttpResponse()
    response["Content-Type"] = "text/html"
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD"
    response["Access-Control-Allow-Headers"] = "Authorization, Origin, X-Requested-With, Content-Type, Accept"
    try:
        # Dispatch type=trigger to the coordination-trigger variant
        if request.GET.get("type") == "trigger":
            return clobber_trigger_payload(request)

        # type=baseline: serve honey body only — no per-extension clobber elements.
        # Used as the within-suffix FD/SF baseline visit. The extension sees the
        # same realistic page structure as the attack visit, but without any
        # attacker-injected elements in <head>. This eliminates cross-crawl noise
        # and makes baseline/attack directly comparable within the same suffix.
        if request.GET.get("type") == "baseline":
            honey_body = _load_honey_body()
            response.content = """<html>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ShopIt.com</title>
  <script src="./scripts?name=lifecycle_tracker.js"></script>
  <script src="./scripts?name=sparkmd5.js"></script>
  <script src="./scripts?name=mutation_hashes.js"></script>
  <script src="./scripts?name=mutation.js"></script>
  <script src="./scripts?name=v2_dispatch.js"></script>
</head>
<body>
  <!-- Baseline: honey body only, no attacker payload -->
  %s
</body>
</html>""" % honey_body
            return response

        extension_id = request.GET.get("extensionId", "")
        if not extension_id:
            response.content = "<html><body><h1>No extensionId</h1></body></html>"
            return response

        payload_html = get_clobber_payload(extension_id)
        if not payload_html:
            payload_html = "<!-- No clobber payload found for this extension -->"

        honey_body = _load_honey_body()

        response.content = """<html>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ShopIt.com</title>
  <script src="./scripts?name=lifecycle_tracker.js"></script>
  <script src="./scripts?name=sparkmd5.js"></script>
  <script src="./scripts?name=mutation_hashes.js"></script>
  <script src="./scripts?name=mutation.js"></script>
  <script src="./scripts?name=v2_dispatch.js"></script>
</head>
<body>
  <!-- BEGIN attacker payload (prepended for first-in-DOM-order priority) -->
  %s
  <!-- END attacker payload -->
  <!-- BEGIN honey body (from clobber_proxy.html) -->
  %s
  <!-- END honey body -->
</body>
</html>""" % (payload_html, honey_body)
    except:
        logging.error("Exception occurred in clobber_payload(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        response.content = "<html><body><h1>Error</h1></body></html>"
    return response


# ─────────────────────────────────────────────────────────────────────────────
# executeScript-coordination trigger crawl (v2, isolated namespace only)
# All code below is NEW — nothing above is modified.
# ─────────────────────────────────────────────────────────────────────────────

def get_clobber_globals(extension_id: str) -> dict:
    """
    Retrieve the per-extension coordination globals from extension_clobber_globals.
    Returns {'globals': [...], 'methods': [...], 'typeof_guards': [...]}
    or empty dict if none found.
    """
    try:
        with CONNECTION_POOL.connection() as connection:
            cursor = connection.execute(
                "SELECT globals_json FROM extension_clobber_globals "
                "WHERE extension_id = %s AND dataset = %s LIMIT 1;",
                (extension_id, DATASET)
            )
            row = cursor.fetchone()
            if row and row[0]:
                val = row[0]
                if isinstance(val, str):
                    return json.loads(val)
                return val if isinstance(val, dict) else {}
    except:
        logging.error("[DB] get_clobber_globals: %s" % "-".join(traceback.format_exc().split("\n")))
    return {}


def clobber_trigger_payload(request: HttpRequest) -> HttpResponse:
    """
    Variant of clobber_payload for the executeScript-coordination trigger crawl.

    Identical to clobber_payload EXCEPT it also:
      1. Loads static/scripts/v2/clobber_trigger.js
      2. Injects window.__CLOBBER_TRIGGER_CONFIG = {globals, methods} from
         the extension_clobber_globals table so the trigger script knows
         which window.X names to call for this specific extension.

    This tests the executeScript-coordination attack surface: the page
    pre-clobbers window.X (via the clobber payload), then clobber_trigger.js
    invokes window.X() — if clobbered it silently fails, if genuine it fires
    the extension UI. Mutations signal whether the globals were accessible.

    Served at: /isolated/clobber_payload/?type=trigger&extensionId=<id>
    The existing clobber_payload view dispatches here when type=trigger.
    """
    response = HttpResponse()
    response["Content-Type"] = "text/html"
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD"
    response["Access-Control-Allow-Headers"] = "Authorization, Origin, X-Requested-With, Content-Type, Accept"
    try:
        extension_id = request.GET.get("extensionId", "")
        if not extension_id:
            response.content = "<html><body><h1>No extensionId</h1></body></html>"
            return response

        globals_config = get_clobber_globals(extension_id)
        honey_body     = _load_honey_body()
        config_json    = json.dumps(globals_config)

        # Build a trigger-specific clobber payload from the coordination globals.
        # The INA extension_clobber_payloads targets DOM-query selectors, which is
        # the WRONG attack surface here. The trigger vulnerability relies on BARE
        # PROPERTY ACCESS (window.X), which requires native DOM clobbering via
        # matching id/name attributes — not querySelector targets.
        # We generate one <a id="X"> element per exported global so that
        # window.X resolves to an HTMLElement before the CS dedup guard runs.
        trigger_globals = globals_config.get('globals', [])
        trigger_payload_parts = []
        for g in trigger_globals:
            # <a id="X"> clobbers window.X via id-based native clobbering
            trigger_payload_parts.append(f'<a id="{g}" style="display:none"></a>')
            # <form name="X"> covers form-collection access patterns
            trigger_payload_parts.append(f'<form name="{g}" style="display:none"></form>')
        trigger_payload = '\n  '.join(trigger_payload_parts) if trigger_payload_parts \
                          else '<!-- No coordination globals to clobber -->'

        response.content = """<html>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ShopIt.com</title>
  <script>window.__CLOBBER_TRIGGER_CONFIG = %s;</script>
  <!-- Trigger clobber payload: one <a id="X"> per exported coordination global.
       Injected in <head> so id/name elements are in the DOM BEFORE any content
       script runs. The CS dedup guard sees window.X = HTMLElement (truthy) and
       skips initialisation — replicating an attacker-controlled page. -->
  %s
  <script src="./scripts?name=lifecycle_tracker.js"></script>
  <script src="./scripts?name=sparkmd5.js"></script>
  <script src="./scripts?name=mutation_hashes.js"></script>
  <script src="./scripts?name=mutation.js"></script>
  <script src="./scripts?name=v2/clobber_trigger.js"></script>
  <script src="./scripts?name=v2_dispatch.js"></script>
</head>
<body>
  %s
</body>
</html>""" % (config_json, trigger_payload, honey_body)
    except:
        logging.error("Exception in clobber_trigger_payload(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        response.content = "<html><body><h1>Error</h1></body></html>"
    return response


def clobber_gbs_payload(request: HttpRequest) -> HttpResponse:
    """
    Per-extension GBS (getter-before-setter) clobber attack page.

    Injects one <a id="V" name="V"> element per GBS variable in <head> so
    elements exist in the DOM before any CS runs at document_start. Also
    includes the honey body so content-triggered extensions activate and
    can show SF/FD/proxy-sink signal — same realistic DOM surface as the
    targeted clobber attack page.

    The GBS elements in <head> are what differ from the baseline:
    they clobber window.V via named property resolution when the extension's
    CS reads window.V in a DOMContentLoaded callback.

    Served at: /isolated/clobber_gbs_payload/?extensionId=<id>
    Returns honey body only (no GBS elements) when extension_gbs_vars is empty.
    """
    response = HttpResponse()
    response["Content-Type"] = "text/html"
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD"
    response["Access-Control-Allow-Headers"] = "Authorization, Origin, X-Requested-With, Content-Type, Accept"
    try:
        extension_id = request.GET.get("extensionId", "")
        if not extension_id:
            response.content = "<html><body><h1>No extensionId</h1></body></html>"
            return response

        gbs_vars   = get_gbs_variables(extension_id)
        honey_body = _load_honey_body()

        payload_parts = []
        for v in gbs_vars:
            payload_parts.append(f'<a id="{v}" name="{v}" style="display:none"></a>')
        gbs_payload = '\n  '.join(payload_parts) if payload_parts \
                      else '<!-- No GBS variables recorded for this extension -->'

        response.content = """<html>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ShopIt.com</title>
  <!-- GBS clobber payload: one <a id="V"> per getter-before-setter variable.
       In <head> so elements exist before any CS runs at document_start. -->
  %s
  <script src="./scripts?name=lifecycle_tracker.js"></script>
  <script src="./scripts?name=sparkmd5.js"></script>
  <script src="./scripts?name=mutation_hashes.js"></script>
  <script src="./scripts?name=mutation.js"></script>
  <script src="./scripts?name=v2_dispatch.js"></script>
</head>
<body>
  %s
</body>
</html>""" % (gbs_payload, honey_body)
    except:
        logging.error("Exception in clobber_gbs_payload(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        response.content = "<html><body><h1>Error</h1></body></html>"
    return response
