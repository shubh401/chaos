from urllib.parse import urlparse, parse_qs
from psycopg_pool import ConnectionPool
from config import *

import hashlib
import re as _re

# Load seenVars from __cs_hook.js at import time.
# Filters variable_log data so that browser built-ins captured before the
# seenVars snapshot was updated are excluded from GBS trace hook targets.
def _load_seen_vars_from_hook() -> set:
    try:
        import os as _os
        # Hook file is at static/src/hooks/ relative to repo root
        hook_path = _os.path.join(
            _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))),
            'static', 'src', 'hooks', '__cs_hook.js'
        )
        content = open(hook_path, 'r', encoding='utf-8').read()
        start = content.find('window.seenVars = new Set([')
        end   = content.find(']);', start)
        if start == -1 or end == -1:
            return set()
        return set(_re.findall(r'"([^"]+)"', content[start:end]))
    except Exception:
        return set()

_HOOK_SEEN_VARS = _load_seen_vars_from_hook()

CONNECTION_POOL = ConnectionPool(conninfo=CONNECTION_INFO, min_size=5, max_size=10, timeout=30)

def store_error_logs(data: dict) -> str:
    """
    Stores error logs into the database.

    Args:
        data (dict): A dictionary containing the error log details. Expected keys are:
            - "extensionId" (str): The ID of the extension.
            - "error" (dict): The error details.
            - "type" (str): The type of the error.
            - "visit" (str): The visit identifier.
            - "source" (str): The source of the error.
            - "url" (str): The URL associated with the error log.
            - "contextURL" (str): The context URL associated with the error log.

    Returns:
        str: "Ok!" if the log is stored successfully or if the extension ID is not provided or is 'None'.
             "Error!" if an exception occurs during the process.
    """
    try:
        extension_id = str(data.get("extensionId"))
        if not extension_id or extension_id == 'None': return "Ok!"
        
        error = json.dumps(data.get("error"))
        error_type = str(data.get("type"))
        visit = str(data.get("visit"))
        source = str(data.get("source"))
        url = data.get("url", "")
        context_url = data.get("contextURL", "")
        client_ts = data.get("__v2_client_ts")
        lifecycle_stage = data.get("__v2_lifecycle_stage")

        query = f"INSERT INTO {TEST_TYPE}_errors_{TABLE_SUFFIX} (extension_id, url, context_url, error_type, source, dataset, error, visit, client_ts, lifecycle_stage) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;"
        with CONNECTION_POOL.connection() as connection:
            connection.execute(query, (extension_id, url, context_url, error_type, source, DATASET, error, visit, client_ts, lifecycle_stage))
        return "Ok!"
    except:
        logging.error("[DB] Exception occurred in log_error(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        return "Error!"
    
def store_invocation_logs(hook_data: dict) -> str:
    """
    Stores invocation logs based on the provided prototype data.

    Args:
        hook_data (dict): A dictionary containing the prototype data. Expected keys include:
            - "type" (str): The type of the prototype data.
            - "data" (dict): The data associated with the prototype.
            - "extensionId" (str): The ID of the extension.
            - "url" (str): The URL associated with the prototype.
            - "contextURL" (str): The context URL associated with the prototype.
            - "visit" (str): The visit identifier.

    Returns:
        str: "Ok!" if the logs are stored successfully, "Error!" if an exception occurs.
    """
    try:
        if hook_data.get("type", "") == "variable" and hook_data.get("data", None):
            return store_variable_logs(hook_data)
        
        extension_id = str(hook_data.get("extensionId", None))
        if not extension_id or extension_id == 'None': return "Ok!"
        
        url = str(hook_data.get("url"))
        context_url = str(hook_data.get("contextURL"))
        api = str(hook_data.get("type"))
        visit = str(hook_data.get("visit"))
        
        data, arguments, caller, caller_data, caller_name, stacktrace = None, None, None, None, None, None
        if hook_data.get("data"):
            if api in ('cookies', 'localStorage', 'sessionStorage'):
                api = hook_data.get("data").get("type")
            data = json.dumps(hook_data.get("data").get("dis"))
            arguments = json.dumps(hook_data.get("data").get("arguments"))
            caller = json.dumps(hook_data.get("data").get("caller"))
            caller_data = json.dumps(hook_data.get("data").get("callerData"))
            caller_name = json.dumps(hook_data.get("data").get("callerName"))
            stacktrace = json.dumps(hook_data.get("data").get("stacktrace"))
        
        client_ts = hook_data.get("data", {}).get("__v2_client_ts") if hook_data.get("data") else None
        lifecycle_stage = hook_data.get("data", {}).get("__v2_lifecycle_stage") if hook_data.get("data") else None

        arguments_md5 = "%s_%s" % (api, hashlib.md5(str(arguments).encode()).hexdigest())
        arguments_data_md5 = "%s_%s_%s" % (
            api, hashlib.md5(str(arguments).encode()).hexdigest(), hashlib.md5(str(data).encode()).hexdigest())
        caller_data_md5 = "%s_%s" % (api, hashlib.md5(str(caller_data).encode()).hexdigest())
        stack_trace_md5 = "%s_%s" % (api, hashlib.md5(str(stacktrace).encode()).hexdigest())

        query = f"""INSERT INTO {TEST_TYPE}_hook_log_{TABLE_SUFFIX}
        (extension_id, url, context_url, api, data, arguments, caller, caller_name, caller_data, stacktrace, stack_trace_md5, arguments_md5, arguments_data_md5, caller_data_md5, dataset, visit, client_ts, lifecycle_stage)
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;"""
        with CONNECTION_POOL.connection() as connection:
            connection.execute(query, (extension_id, url, context_url, api, data, arguments, caller, caller_name, caller_data, stacktrace, stack_trace_md5, arguments_md5, arguments_data_md5, caller_data_md5,
            DATASET, visit, client_ts, lifecycle_stage))
        return "Ok!"
    except:
        logging.error("[DB] Exception occurred in store_invocation_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        return "Error!"

def store_clobber_logs(clobber_data: dict) -> str:
    """
    Stores clobber proxy logs based on the provided prototype data.

    Args:
        hook_data (dict): A dictionary containing the prototype data. Expected keys include:
            - "type" (str): The type of the prototype data.
            - "data" (dict): The data associated with the prototype.
            - "extensionId" (str): The ID of the extension.
            - "url" (str): The URL associated with the prototype.
            - "contextURL" (str): The context URL associated with the prototype.
            - "visit" (str): The visit identifier.

    Returns:
        str: "Ok!" if the logs are stored successfully, "Error!" if an exception occurs.
    """
    try:
        if clobber_data.get("type", "") == "variable" and clobber_data.get("data", None):
            return store_variable_logs(clobber_data)
        
        extension_id = str(clobber_data.get("extensionId", None))
        if not extension_id or extension_id == 'None': return "Ok!"
        
        url = str(clobber_data.get("url"))
        context_url = str(clobber_data.get("contextURL"))
        api = str(clobber_data.get("type"))
        visit = str(clobber_data.get("visit"))
        
        data, proxy_data, arguments, caller, caller_data, caller_name, stacktrace = None, None, None, None, None, None, None
        if clobber_data.get("data"):
            if api in ('cookies', 'localStorage', 'sessionStorage'):
                api = clobber_data.get("data").get("type")
            data = json.dumps(clobber_data.get("data").get("dis"))
            proxy_data = json.dumps(clobber_data.get("data").get("proxyData"))
            arguments = json.dumps(clobber_data.get("data").get("arguments"))
            caller = json.dumps(clobber_data.get("data").get("caller"))
            caller_data = json.dumps(clobber_data.get("data").get("callerData"))
            caller_name = json.dumps(clobber_data.get("data").get("callerName"))
            stacktrace = json.dumps(clobber_data.get("data").get("stacktrace"))
        
        arguments_md5 = "%s_%s" % (api, hashlib.md5(str(arguments).encode()).hexdigest())
        arguments_data_md5 = "%s_%s_%s" % (
            api, hashlib.md5(str(arguments).encode()).hexdigest(), hashlib.md5(str(data).encode()).hexdigest())
        caller_data_md5 = "%s_%s" % (api, hashlib.md5(str(caller_data).encode()).hexdigest())
        stack_trace_md5 = "%s_%s" % (api, hashlib.md5(str(stacktrace).encode()).hexdigest())
        
        query = f"""INSERT INTO {TEST_TYPE}_clobber_hook_log_{TABLE_SUFFIX}
        (extension_id, url, context_url, api, data, proxy_data, arguments, caller, caller_name, caller_data, stacktrace, stack_trace_md5, arguments_md5, arguments_data_md5, caller_data_md5, dataset, visit) 
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;"""
        with CONNECTION_POOL.connection() as connection:
            connection.execute(query, (extension_id, url, context_url, api, data, proxy_data, arguments, caller, caller_name, caller_data, stacktrace, stack_trace_md5, arguments_md5, arguments_data_md5, caller_data_md5,
            DATASET, visit))
        return "Ok!"
    except:
        logging.error("[DB] Exception occurred in store_clobber_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        return "Error!"

def store_variable_logs(variable_data: dict) -> str:
    """
    Stores variable logs into the database.

    Args:
        variable_data (dict): A dictionary containing the variable log details. Expected keys are:
            - "extensionId" (str): The ID of the extension.
            - "stage" (str): The stage of the variable log.
            - "url" (str): The URL associated with the variable log.
            - "contextURL" (str): The context URL associated with the variable log.
            - "visit" (str): The visit identifier.
            - "data" (dict): The data associated with the variable log, including "variables".

    Returns:
        str: "Ok!" if the log is stored successfully or if the extension ID is not provided or is 'None'.
             "Error!" if an exception occurs during the process.
    """
    try:
        extension_id = str(variable_data.get("extensionId", None))
        if not extension_id or extension_id == 'None': return "Ok!"
        
        stage, url, context_url, variables = None, None, None, None
        stage = variable_data.get("data", {}).get("stage")
        url = str(variable_data.get("url"))
        context_url = str(variable_data.get("contextURL"))
        visit = str(variable_data.get("visit"))
        
        variables = variable_data.get("data", {})
        if isinstance(variables, str): variables = json.loads(variables)
        if isinstance(variables, dict): variables = variables.get("variables")
        if not variables: return "Ok!"
        
        client_ts = variable_data.get("data", {}).get("__v2_client_ts") if isinstance(variable_data.get("data"), dict) else None
        lifecycle_stage = variable_data.get("data", {}).get("__v2_lifecycle_stage") if isinstance(variable_data.get("data"), dict) else None

        query = f"INSERT INTO {TEST_TYPE}_variable_log_{TABLE_SUFFIX} (extension_id, variables, dataset, visit, stage, url, context_url, client_ts, lifecycle_stage) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"
        with CONNECTION_POOL.connection() as connection:
            connection.execute(query, (extension_id, json.dumps(variables), DATASET, visit, stage, url, context_url, client_ts, lifecycle_stage))
        return "Ok!"
    except:
        logging.error("[DB] Exception occurred in store_variable_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        return "Error!"

def store_cs_trace_logs(trace_data: dict) -> str:
    try:
        extension_id = str(trace_data.get("extensionId", None))
        if not extension_id or extension_id == 'None': return "Ok!"
        url         = str(trace_data.get("url"))
        context_url = str(trace_data.get("contextURL"))
        visit       = str(trace_data.get("visit"))
        data        = trace_data.get("data", {})
        if isinstance(data, str):
            try: data = json.loads(data)
            except: return "Ok!"
        traces = data.get("traces") if isinstance(data, dict) else None
        if not traces: return "Ok!"
        query = f"INSERT INTO {TEST_TYPE}_cs_trace_log_{TABLE_SUFFIX} (extension_id, traces, dataset, visit, url, context_url) VALUES(%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"
        with CONNECTION_POOL.connection() as connection:
            connection.execute(query, (extension_id, json.dumps(traces), DATASET, visit, url, context_url))
        return "Ok!"
    except:
        logging.error("[DB] Exception occurred in store_cs_trace_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        return "Error!"

def store_mutation_logs(mutation_data: dict) -> str:
    """
    Stores mutation logs into the database.

    Args:
        mutation_data (dict): A dictionary containing the mutation log details. Expected keys are:
            - "extensionId" (str): The ID of the extension.
            - "type" (str): The type of the mutation.
            - "url" (str): The URL associated with the mutation.
            - "contextURL" (str): The context URL associated with the mutation.
            - "visit" (str): The visit identifier.
            - "data" (dict): The data associated with the mutation, including "addedNodes", "removedNodes", "target", etc.

    Returns:
        str: "Ok!" if the log is stored successfully or if the extension ID is not provided or is 'None'.
             "Error!" if an exception occurs during the process.
    """
    try:
        extension_id = str(mutation_data.get("extensionId", None))
        if not extension_id or extension_id == 'None': return "Ok!"
        api = str(mutation_data.get("type"))
        url = str(mutation_data.get("url"))
        context_url = str(mutation_data.get("contextURL"))
        visit = str(mutation_data.get("visit"))
        
        client_ts = mutation_data.get("__v2_client_ts")
        lifecycle_stage = mutation_data.get("__v2_lifecycle_stage")

        added_nodes, removed_nodes, target, type, attribute_name, attribute_namespace, old_value, next_sibling, previous_sibling, data_digest = None, None, None, None, None, None, None, None, None, None

        if mutation_data.get("data"):
            data = mutation_data.get("data", {})
            data_digest = hashlib.md5(json.dumps(data).encode()).hexdigest()
            added_nodes = json.dumps(data.get("addedNodes"))
            removed_nodes = json.dumps(data.get("removedNodes"))
            target = json.dumps(data.get("target"))
            type = json.dumps(data.get("type"))
            attribute_name = json.dumps(data.get("attributeName"))
            attribute_namespace = json.dumps(data.get("attributeNamespace"))
            old_value = json.dumps(data.get("oldValue"))
            next_sibling = json.dumps(data.get("nextSibling"))
            previous_sibling = json.dumps(data.get("previousSibling"))
            # Fallback: extract v2 fields from data sub-object if not at top level
            if client_ts is None:
                client_ts = data.get("__v2_client_ts")
            if lifecycle_stage is None:
                lifecycle_stage = data.get("__v2_lifecycle_stage")

        query = f"INSERT INTO {TEST_TYPE}_mutation_log_{TABLE_SUFFIX} (extension_id, url, context_url, api, added_nodes, removed_nodes, target, type, attribute_name, attribute_namespace, old_value, next_sibling, previous_sibling, data_digest, dataset, visit, client_ts, lifecycle_stage) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;"
        with CONNECTION_POOL.connection() as connection:
            connection.execute(query, (extension_id, url, context_url, api, added_nodes, removed_nodes, target, type, attribute_name, attribute_namespace, old_value, next_sibling, previous_sibling, data_digest, DATASET, visit, client_ts, lifecycle_stage))
        return "Ok!"
    except:
        logging.error("[DB] Exception occurred in store_mutation_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        return "Error!"

def store_cookie_logs(cookie_data: dict) -> str:
    """
    Stores cookie logs into the database.

    Args:
        cookie_data (dict): A dictionary containing the cookie log details. Expected keys are:
            - "extensionId" (str): The ID of the extension.
            - "stage" (str): The stage of the cookie log.
            - "url" (str): The URL associated with the cookie log.
            - "contextURL" (str): The context URL associated with the cookie log.
            - "visit" (str): The visit identifier.
            - "data" (dict): The data associated with the cookie log.

    Returns:
        str: "Ok!" if the log is stored successfully or if the extension ID is not provided or is 'None'.
             "Error!" if an exception occurs during the process.
    """
    try:
        extension_id = str(cookie_data.get("extensionId"))
        stage, url, context_url = None, None, None
        if cookie_data.get("stage", None):
            stage = cookie_data.get("stage")
        else:
            stage = cookie_data.get("data", {}).get("stage")
        url = cookie_data.get("url")
        context_url = cookie_data.get("contextURL")
        visit = cookie_data.get("visit")
        
        client_ts = cookie_data.get("data", {}).get("__v2_client_ts") if isinstance(cookie_data.get("data"), dict) else None
        lifecycle_stage = cookie_data.get("data", {}).get("__v2_lifecycle_stage") if isinstance(cookie_data.get("data"), dict) else None

        query = f"INSERT INTO {TEST_TYPE}_cookies_log_{TABLE_SUFFIX} (extension_id, type, data, dataset, visit, stage, url, context_url, client_ts, lifecycle_stage) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"
        with CONNECTION_POOL.connection() as connection:
            connection.execute(query, (extension_id, "poll", json.dumps(cookie_data.get("data")), DATASET, visit, stage, url, context_url, client_ts, lifecycle_stage))
        return "Ok!"
    except:
        logging.error("[DB] Exception occurred in store_cookie_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        return "Error!"

def store_message_logs(message_data: dict) -> str:
    """
    Stores message logs into the database.

    Args:
        message_data (dict): A dictionary containing the message log details. Expected keys are:
            - "extensionId" (str): The ID of the extension.
            - "stage" (str): The stage of the message log.
            - "url" (str): The URL associated with the message log.
            - "contextURL" (str): The context URL associated with the message log.
            - "visit" (str): The visit identifier.
            - "message" (str): The message content.
            - "source" (str): The source of the message.
            - "target" (str): The target of the message.
            - "origin" (str): The origin of the message.

    Returns:
        str: "Ok!" if the log is stored successfully or if the extension ID is not provided or is 'None'.
             "Error!" if an exception occurs during the process.
    """
    try:
        extension_id = str(message_data.get("extensionId"))
        stage = message_data.get("data", {}).get("stage")
        url = message_data.get("url")
        context_url = message_data.get("contextURL")
        visit = message_data.get("visit")
        message = message_data.get("data", {}).get("message")
        source = message_data.get("data", {}).get("source")
        target = message_data.get("data", {}).get("target")
        origin = message_data.get("data", {}).get("origin")
        client_ts = message_data.get("data", {}).get("__v2_client_ts") if isinstance(message_data.get("data"), dict) else None
        lifecycle_stage_val = message_data.get("data", {}).get("__v2_lifecycle_stage") if isinstance(message_data.get("data"), dict) else None
        data = {"source": source, "target": target, "origin": origin}
        query = f"INSERT INTO {TEST_TYPE}_message_log_{TABLE_SUFFIX} (extension_id, message, data, dataset, visit, stage, url, context_url, client_ts, lifecycle_stage) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"
        with CONNECTION_POOL.connection() as connection:
            connection.execute(query, (extension_id, json.dumps(message), json.dumps(data), DATASET, visit, stage, url, context_url, client_ts, lifecycle_stage_val))
        return "Ok!"
    except:
        logging.error("[DB] Exception occurred in store_message_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        return "Error!"
 
def store_storage_logs(storage_data: dict) -> str:
    """
    Stores storage logs into the database.

    Args:
        storage_data (dict): A dictionary containing the storage log details. Expected keys are:
            - "extensionId" (str): The ID of the extension.
            - "stage" (str): The stage of the storage log.
            - "url" (str): The URL associated with the storage log.
            - "contextURL" (str): The context URL associated with the storage log.
            - "visit" (str): The visit identifier.
            - "type" (str): The type of the storage.
            - "data" (dict): The data associated with the storage log.

    Returns:
        str: "Ok!" if the log is stored successfully or if the extension ID is not provided or is 'None'.
             "Error!" if an exception occurs during the process.
    """
    try:
        extension_id = str(storage_data.get("extensionId"))
        stage = storage_data.get("data", {}).get("stage")
        url = storage_data.get("url")
        context_url = storage_data.get("contextURL")
        visit = storage_data.get("visit")
        client_ts = storage_data.get("data", {}).get("__v2_client_ts") if isinstance(storage_data.get("data"), dict) else None
        lifecycle_stage = storage_data.get("data", {}).get("__v2_lifecycle_stage") if isinstance(storage_data.get("data"), dict) else None

        query = f"INSERT INTO {TEST_TYPE}_storage_log_{TABLE_SUFFIX} (extension_id, storage, type, data, dataset, visit, stage, url, context_url, client_ts, lifecycle_stage) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"
        with CONNECTION_POOL.connection() as connection:
            connection.execute(query, (extension_id, json.dumps(storage_data.get("type")), "poll", json.dumps(storage_data.get("data")), DATASET, visit, stage, url, context_url, client_ts, lifecycle_stage))
        return "Ok!"
    except:
        logging.error("[DB] Exception occurred in store_storage_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        return "Error!"

def store_idb_logs(idb_data: dict) -> str:
    """
    Stores IndexedDB (IDB) logs into the database.

    Args:
        idb_data (dict): A dictionary containing the IDB log details. Expected keys are:
            - "extensionId" (str): The ID of the extension.
            - "stage" (str): The stage of the IDB log.
            - "url" (str): The URL associated with the IDB log.
            - "contextURL" (str): The context URL associated with the IDB log.
            - "visit" (str): The visit identifier.
            - "property" (dict): The property details of the IDB log.
            - "arguments" (dict): The arguments associated with the IDB log.
            - "results" (dict): The results of the IDB log.

    Returns:
        str: "Ok!" if the log is stored successfully or if the extension ID is not provided or is 'None'.
             "Error!" if an exception occurs during the process.
    """
    try:
        extension_id = str(idb_data.get("extensionId"))
        stage = idb_data.get("stage")
        url = idb_data.get("url")
        context_url = idb_data.get("contextURL")
        visit = idb_data.get("visit")
        property = json.dumps(idb_data.get("property"))
        arguments = json.dumps(idb_data.get("arguments"))
        results = json.dumps(idb_data.get("results")) if idb_data.get("results") else json.dumps(idb_data.get("data", ""))
        
        client_ts = idb_data.get("data", {}).get("__v2_client_ts") if isinstance(idb_data.get("data"), dict) else None
        lifecycle_stage = idb_data.get("data", {}).get("__v2_lifecycle_stage") if isinstance(idb_data.get("data"), dict) else None

        query = f"INSERT INTO {TEST_TYPE}_idb_log_{TABLE_SUFFIX} (extension_id, property, arguments, results, dataset, visit, stage, url, context_url, client_ts, lifecycle_stage) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"
        with CONNECTION_POOL.connection() as connection:
            connection.execute(query, (extension_id, property, arguments, results, DATASET, visit, stage, url, context_url, client_ts, lifecycle_stage))
        return "Ok!"
    except:
        logging.error("[DB] Exception occurred in store_idb_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        return "Error!"

def store_coverage_logs(coverage_data: dict) -> str:
    """
    Stores coverage logs into the database.

    Args:
        coverage_data (dict): A dictionary containing the coverage log details. Expected keys are:
            - "extensionId" (str): The ID of the extension.
            - "url" (str): The URL associated with the coverage log.
            - "visit" (str): The visit identifier.
            - "coverage" (dict): The coverage data.

    Returns:
        str: "Ok" if the log is stored successfully or if the extension ID is not provided or is 'None'.
             "Error!" if an exception occurs during the process.
    """
    try:
        extension_id = str(coverage_data.get("extensionId"))
        url = coverage_data.get("url")
        visit = coverage_data.get("visit")
        coverage = json.dumps(coverage_data.get("coverage"))
        query = f"INSERT INTO {TEST_TYPE}_coverage_log_{TABLE_SUFFIX} (extension_id, url, coverage, dataset, visit) VALUES(%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"
        with CONNECTION_POOL.connection() as connection:
            connection.execute(query, (extension_id, url, coverage, DATASET, visit))
        return "Ok"
    except:
        logging.error("[DB] Exception occurred in store_coverage_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        return "Error!"

def store_proxy_logs(proxy_data: dict) -> str:
    """
    Stores proxy logs into the database.

    Args:
        proxy_data (dict): A dictionary containing the proxy log details. Expected keys are:
            - "extensionId" (str): The ID of the extension.
            - "url" (str): The URL associated with the proxy log.
            - "contextURL" (str): The context URL associated with the proxy log.
            - "visit" (str): The visit identifier.
            - "type" (str): The type associated with the proxy log.
            - "proxy_data" (dict): The proxy data.

    Returns:
        str: "Ok" if the log is stored successfully or if the extension ID is not provided or is 'None'.
             "Error!" if an exception occurs during the process.
    """
    try:
        extension_id = str(proxy_data.get("extensionId"))
        url = proxy_data.get("url")
        context_url = proxy_data.get("contextURL")
        visit = proxy_data.get("visit")
        type = proxy_data.get("type")
        proxy_data = json.dumps(proxy_data.get("data"))

        query = f"INSERT INTO {TEST_TYPE}_proxy_log_{TABLE_SUFFIX} (extension_id, url, context_url, type, proxy_data, dataset, visit) VALUES(%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"
        with CONNECTION_POOL.connection() as connection:
            connection.execute(query, (extension_id, url, context_url, type, proxy_data, DATASET, visit))
        return "Ok"
    except:
        logging.error("[DB] Exception occurred in store_proxy_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        return "Error!"

def store_csp_logs(csp_report: dict) -> str:
    try:
        csp_report = csp_report.get("csp-report", {})
        url = csp_report.get("source-file", "")
        context_url = csp_report.get("document-uri", "")
        parsed_url = urlparse(context_url)
        extension_id = parse_qs(parsed_url.query).get('extensionId', [None])[0]
        if not extension_id: return "Ok"
        visit = parse_qs(parsed_url.query)['visit'][0]
        query = f"INSERT INTO {TEST_TYPE}_csp_log_{TABLE_SUFFIX} (extension_id, url, context_url, csp_report, dataset, visit) VALUES(%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"
        with CONNECTION_POOL.connection() as connection:
            connection.execute(query, (extension_id, url, context_url, json.dumps(csp_report), DATASET, visit))
        return "Ok"
    except:
        logging.error("[DB] Exception occurred in store_csp_logs(): %s\n" % "-".join(traceback.format_exc().split("\n")))
        return "Error!"


# Variables to skip when generating pre-assignment scripts
_PREASSIGN_SKIP_VARS = {
    '__v2_lifecycle_stage', '__v2_timestamp', '__preassign_dispatch',
    '__preassign_defineProperty', '__dispatchHookData', '__dispatchPollData',
    '__dispatchMutationData', '__dispatchErrorLog', '__exposedErrorLogger',
    '__getCircularReplacer', '__knownHashes', '__fetch', '__stringify',
    'SparkMD5', '__playwright__binding__', '__pwInitScripts',
}

def get_extension_variables(extension_id: str) -> list:
    """
    Queries both extension_vars (static analysis) and variable_log (dynamic observation)
    for a given extension_id. Returns a deduplicated list of variable names.
    """
    variables = set()
    try:
        with CONNECTION_POOL.connection() as connection:
            # Source 1: Static analysis (extension_vars table)
            try:
                cursor = connection.execute(
                    "SELECT variables FROM extension_vars WHERE extension_id = %s AND dataset = %s;",
                    (extension_id, DATASET)
                )
                for row in cursor.fetchall():
                    if row[0]:
                        var_data = row[0]
                        if isinstance(var_data, list):
                            variables.update(var_data)
                        elif isinstance(var_data, dict):
                            variables.update(var_data.keys())
            except:
                logging.error("[DB] get_extension_variables (static): %s" % "-".join(traceback.format_exc().split("\n")))

            # Source 2: Dynamic observation (variable_log table)
            try:
                variable_table = f"{TEST_TYPE}_variable_log_{TABLE_SUFFIX}"
                cursor = connection.execute(
                    f"SELECT variables FROM {variable_table} WHERE extension_id = %s AND dataset = %s;",
                    (extension_id, DATASET)
                )
                for row in cursor.fetchall():
                    if row[0]:
                        var_data = row[0]
                        if isinstance(var_data, str):
                            try:
                                var_data = json.loads(var_data)
                            except:
                                continue
                        if isinstance(var_data, dict):
                            variables.update(var_data.keys())
                        elif isinstance(var_data, list):
                            variables.update(var_data)
            except:
                logging.error("[DB] get_extension_variables (dynamic): %s" % "-".join(traceback.format_exc().split("\n")))
    except:
        logging.error("[DB] get_extension_variables: %s" % "-".join(traceback.format_exc().split("\n")))

    # Filter out instrumentation vars and short names
    return sorted([v for v in variables if v not in _PREASSIGN_SKIP_VARS and len(v) > 1 and not v.startswith('__')])


def get_clobber_payload(extension_id: str) -> str:
    """
    Retrieves the pre-generated DOM clobbering HTML payload for an extension.
    Returns the payload_html string, or empty string if none exists.
    """
    try:
        with CONNECTION_POOL.connection() as connection:
            cursor = connection.execute(
                "SELECT payload_html FROM extension_clobber_payloads WHERE extension_id = %s AND dataset = %s LIMIT 1;",
                (extension_id, DATASET)
            )
            row = cursor.fetchone()
            if row and row[0]:
                return row[0]
    except:
        logging.error("[DB] get_clobber_payload: %s" % "-".join(traceback.format_exc().split("\n")))
    return ""


def get_gbs_trace_variables(extension_id: str, pre_suffix: str) -> list:
    """
    Returns variable names observed in the pre-crawl variable_log for the given
    extension, to be used as the GBS trace hook target list.

    Reads isolated_variable_log_{pre_suffix}. Note: seenVars in __cs_hook.js
    must be kept current (run update_seen_vars.py) so that browser built-ins
    that post-date the seenVars snapshot are excluded from variable_log before
    reaching this function.
    """
    variables = set()
    try:
        with CONNECTION_POOL.connection() as connection:
            table = f"isolated_variable_log_{pre_suffix}"
            cursor = connection.execute(
                f"SELECT variables FROM {table} WHERE extension_id = %s AND dataset = %s;",
                (extension_id, DATASET)
            )
            for row in cursor.fetchall():
                if not row[0]: continue
                var_data = row[0]
                if isinstance(var_data, str):
                    try: var_data = json.loads(var_data)
                    except: continue
                if isinstance(var_data, dict):
                    variables.update(var_data.keys())
                elif isinstance(var_data, list):
                    variables.update(var_data)
    except:
        logging.error("[DB] get_gbs_trace_variables: %s" % "-".join(traceback.format_exc().split("\n")))
    return sorted([v for v in variables
                   if v not in _PREASSIGN_SKIP_VARS
                   and v not in _HOOK_SEEN_VARS
                   and len(v) > 1
                   and not v.startswith('__')])


def get_gbs_variables(extension_id: str) -> list:
    try:
        with CONNECTION_POOL.connection() as connection:
            cursor = connection.execute(
                "SELECT var_names FROM extension_gbs_vars WHERE extension_id = %s AND dataset = %s LIMIT 1;",
                (extension_id, DATASET)
            )
            row = cursor.fetchone()
            if row and row[0]:
                data = row[0]
                if isinstance(data, list): return data
                if isinstance(data, str):
                    try: return json.loads(data)
                    except: pass
    except:
        logging.error("[DB] get_gbs_variables: %s" % "-".join(traceback.format_exc().split("\n")))
    return []


