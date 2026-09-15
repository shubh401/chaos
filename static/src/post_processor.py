from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from files import copy_extension_dir, copy_file
from utility import serialize_object
from manifest import get_manifest
from config import *

import hashlib

def handle_other_data(data: list, file_name: str) -> None:
    """
    Handles the given data by writing it to a JSON file.

    Args:
        data (list): The data to be written to the file.
        file_name (str): The name of the file (without extension) to write the data to.

    Returns:
        None
    """
    try:
        if data:
            with open(f"{LOGS}{file_name}.json", "w", encoding="utf-8-sig") as fh:
                json.dump(data, fh, indent = 4, default=serialize_object)
    except:
        logging.error("[POST-PROCESSOR] Error while handling header analysis data" + ", ".join(traceback.format_exc().split("\n")))

def inject_into_manifest(extension_id: str) -> None:
    """
    Injects hook configuration as content script into the manifest file of the specified extension.

    Args:
        extension_id (str): The ID of the extension whose manifest file will be modified.

    Returns:
        None
    """
    try:
        manifest = get_manifest(f"{ISOLATED_NAMESPACE_DIR}{extension_id}/manifest.json", extension_id)
        if manifest.get('content_scripts', []):
            manifest['content_scripts'].insert(0, HOOK_CONFIG)
        else:
            manifest['content_scripts'] = [HOOK_CONFIG]
        with open(f"{ISOLATED_NAMESPACE_DIR}{extension_id}/manifest.json", "w", encoding="utf-8-sig") as fh:
            json.dump(manifest, fh, indent=4)
    except:
        logging.error("[POST-PROCESSOR] Error in inject_into_manifest for extension_id: " + extension_id + " : " + ", ".join(traceback.format_exc().split("\n")))

def instrument_extension_with_hooks(extension_id: str) -> None:
    """
    Instruments the specified extension with hooks by copying the hook file and injecting it into the manifest.

    Args:
        extension_id (str): The ID of the extension to be instrumented.

    Returns:
        None
    """
    try:
        copy_file(CS_HOOK_PATH, os.path.join(ISOLATED_NAMESPACE_DIR, extension_id, CS_HOOK_NAME))
        inject_into_manifest(extension_id)
    except:
        logging.error("[POSTPROCESSOR] Error in instrument_extension_with_hooks(): " + extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))

def normalize_url(url):
    try:
        parsed = urlparse(url)
        sorted_query = urlencode(sorted(parse_qsl(parsed.query)))
        normalized = parsed._replace(
            scheme=parsed.scheme.lower(),
            netloc=parsed.netloc.lower(),
            path=parsed.path.rstrip('/'),
            query=sorted_query
        )
        return urlunparse(normalized)
    except:
        logging.error("[POST-PROCESSOR] Error in normalize_url for URL: " + url + " : " + ", ".join(traceback.format_exc().split("\n")))

def consistent_hash(urls):
    try:
        normalized_urls = [normalize_url(u) for u in urls]
        sorted_urls = sorted(normalized_urls)
        serialized = json.dumps(sorted_urls, separators=(',', ':'))
        return hashlib.sha256(serialized.encode()).hexdigest()
    except:
        logging.error("[POST-PROCESSOR] Error in consistent_hash for URLs: " + ", ".join(urls) + " : " + ", ".join(traceback.format_exc().split("\n")))

def aggregate_host_hashes(hosts: list, extension_id: str, host_type: str) -> set:
    try:
        host_hash = consistent_hash(hosts)
        if host_hash in HOSTS_DICT:
            HOSTS_DICT[host_hash].add((extension_id, host_type))
        else:
            HOSTS_DICT[host_hash] = set((extension_id, host_type))
    except:
        logging.error("[POST-PROCESSOR] Error in aggregate_host_hashes: " + ", ".join(traceback.format_exc().split("\n")))

def update_background_urls(manifest: str, extension_id: str) -> None:
    """
    Updates the URLs in the background script of the specified extension.

    Args:
        manifest (str): The path to the manifest file to be updated.
        extension_id (str): The ID of the extension whose manifest will be updated.

    Returns:
        None
    """
    try:
        if manifest.get("manifest_version", 2) == 2:
            if manifest.get("permissions"):
                manifest["permissions"] = HOST_SUBSTITUTE + manifest["permissions"]
            else:
                manifest["permissions"] = HOST_SUBSTITUTE
        elif manifest.get("manifest_version", 3) == 3:
            if manifest.get("host_permissions"):
                manifest["host_permissions"] = HOST_SUBSTITUTE + manifest["host_permissions"]
            else:
                manifest["host_permissions"] = HOST_SUBSTITUTE
    except:
        logging.error("[POST-PROCESSOR] Error in update_background_urls for extension_id: " + extension_id + " : " + ", ".join(traceback.format_exc().split("\n")))

def update_content_script_urls(manifest: dict, extension_id: str, main_world_only: bool = False) -> None:
    """
    Updates the URLs in the content scripts of the specified extension.

    Args:
        manifest (dict): The manifest dictionary to be updated.
        extension_id (str): The ID of the extension whose manifest will be updated.

    Returns:
        None
    """
    try:
        if manifest.get("content_scripts", []):
            if main_world_only:
                for script in manifest["content_scripts"]:
                    if "matches" in script and script.get("world", "ISOLATED") == "MAIN":
                        script["matches"] = HOST_SUBSTITUTE + script["matches"]
                    elif "matches" not in script:
                        script["matches"] = HOST_SUBSTITUTE
            else:
                for script in manifest["content_scripts"]:
                    if "matches" in script:
                        script["matches"] = HOST_SUBSTITUTE + script["matches"]
                    else:
                        script["matches"] = HOST_SUBSTITUTE
    except:
        logging.error("[POST-PROCESSOR] Error in update_content_script_urls for extension_id: " + extension_id + " : " + ", ".join(traceback.format_exc().split("\n")))

def update_war_urls(manifest: dict, extension_id: str, war_scripts: list, main_world_scripts: list) -> None:
    """
    Updates the URLs in the web accessible resources of the specified extension.

    Args:
        manifest (dict): The manifest dictionary to be updated.
        extension_id (str): The ID of the extension whose manifest will be updated.
        war_scripts (list): The list of web accessible resources to be updated.

    Returns:
        None
    """
    try:
        if manifest.get("web_accessible_resources", []):
            for resource in manifest["web_accessible_resources"]:
                if isinstance(resource, str):
                    continue
                elif isinstance(resource, dict):
                    for res in resource.get("resources", []):
                        if res in war_scripts:
                            resource.get("matches", []).extend(HOST_SUBSTITUTE)
                            break
                else:
                    continue
        if main_world_scripts:
            update_content_script_urls(manifest, extension_id, main_world_only=True)
    except:
        logging.error("[POST-PROCESSOR] Error in update_war_urls for extension_id: " + extension_id + " : " + ", ".join(traceback.format_exc().split("\n")))

def overwrite_manifest(manifest: dict, extension_dir: str, extension_id: str) -> None:  
    """
    Overwrites the manifest file with the updated manifest dictionary.

    Args:
        manifest (dict): The manifest dictionary to be written to the file.
        manifest_path (str): The path to the manifest file to be overwritten.
        extension_id (str): The ID of the extension whose manifest will be overwritten.

    Returns:
        None
    """
    try:
        with open(f"{extension_dir}{extension_id}/manifest.json", "w", encoding="utf-8-sig") as fh:
            json.dump(manifest, fh, indent=4)
    except:
        logging.error("[POST-PROCESSOR] Error in overwrite_manifest for extension_id: " + extension_id + " : " + ", ".join(traceback.format_exc().split("\n")))

def update_manifest_urls(manifest: dict, component_type: str, extension_id: str, war_scripts: list = [], main_world_scripts: list = []) -> None:
    """
    Updates the URLs in the manifest file of the specified extension.

    Args:
        manifest (dict): The manifest dictionary to be updated.
        extension_id (str): The ID of the extension whose manifest will be updated.

    Returns:
        None
    """
    try:
        if component_type in ["bg", "scripting"]:
            update_background_urls(manifest, extension_id)
        elif component_type == "cs":
            update_content_script_urls(manifest, extension_id)
        elif component_type == "war":
            update_war_urls(manifest, extension_id, war_scripts, main_world_scripts)
        
    except:
        logging.error("[POST-PROCESSOR] Error in update_manifest_urls for extension_id: " + extension_id + " : " + ", ".join(traceback.format_exc().split("\n")))

def post_process(manifest_content: dict, hosts: list, extension_id: str, pp_type: str, war_scripts: list = [], main_world_scripts: list = []) -> None:
    """
    Post-processes the specified extension based on the given type the extension may be vulnerable to.

    Args:
        extension_id (str): The ID of the extension to be post-processed.
        pp_type (str): The type of post-processing to be performed. Can be "scripting", "war", or "cs".

    Returns:
        None
    """
    try:
        if pp_type == "scripting":
            copy_extension_dir(UNZIPPED_DIR, SHARED_NAMESPACE_DIR, extension_id)
            copy_extension_dir(UNZIPPED_DIR, ISOLATED_NAMESPACE_DIR, extension_id)
            instrument_extension_with_hooks(extension_id)
            if ADVANCED_TEST:
                update_manifest_urls(manifest_content, "bg", extension_id)
                overwrite_manifest(manifest_content, SHARED_NAMESPACE_DIR, extension_id)
                overwrite_manifest(manifest_content, ISOLATED_NAMESPACE_DIR, extension_id)
        elif pp_type == "war":
            copy_extension_dir(UNZIPPED_DIR, SHARED_NAMESPACE_DIR, extension_id)
            if ADVANCED_TEST:
                update_manifest_urls(manifest_content, "war", extension_id, war_scripts, main_world_scripts)
                overwrite_manifest(manifest_content, SHARED_NAMESPACE_DIR, extension_id)
        elif pp_type == "cs":
            copy_extension_dir(UNZIPPED_DIR, ISOLATED_NAMESPACE_DIR, extension_id)
            instrument_extension_with_hooks(extension_id)
            if ADVANCED_TEST:
                update_manifest_urls(manifest_content, "cs", extension_id)
                overwrite_manifest(manifest_content, ISOLATED_NAMESPACE_DIR, extension_id)
        if ADVANCED_TEST and len(hosts):
            aggregate_host_hashes(hosts, extension_id, pp_type)
    except:
        logging.error("[POSTPROCESSOR] Error in post_process(): for extension_id: " + extension_id + " : " + ", ".join(traceback.format_exc().split("\n")))
    return manifest_content

def log_data(invocations: dict, cookies: list, scripting: list, webRequest: list, war_dyn_urls: list) -> None:
    """
    Logs the given data by writing it to JSON files.

    Args:
        invocations (dict): The invocations data to be logged.
        cookies (list): The cookies data to be logged.
        scripting (list): The scripting data to be logged.
        webRequest (list): The webRequest data to be logged.
        war_dyn_urls (list): The war dynamic URLs data to be logged.

    Returns:
        None
    """
    try:
        print("Post-processing data storage in progress, please do not terminate the program!")
        if invocations:
            with open(f"{LOGS}invocations.json", "w", encoding="utf-8-sig") as fh:
                json.dump(invocations, fh, indent = 4, default = serialize_object)
        handle_other_data(cookies, "cookies_perm")
        handle_other_data(scripting, "scripting_perm")
        handle_other_data(webRequest, "webRequest_perm")
        handle_other_data(war_dyn_urls, "war_dyn_urls")
        
        if HOSTS_DICT:
            with open(os.path.join(LOGS, "host_hashes.json"), "w") as fh:
                json.dump(HOSTS_DICT, fh, indent=4, default=serialize_object)
    except:
        logging.error("[POST-PROCESSOR] Error while logging data" + ", ".join(traceback.format_exc().split("\n")))
