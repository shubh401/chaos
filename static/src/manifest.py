from files import absolute_file_path_from_dir, script_src_from_html
from jsoncomment import JsonComment
from config import *

import jstyleson
import jsmin
import ast

def get_manifest(manifest_path: str, extension_id: str) -> Optional[dict]:
    """
    Retrieves and parses the manifest file for the given extension.

    Args:
        manifest_path (str): The path to the manifest file.
        extension_id (str): The ID of the extension being processed.

    Returns:
        Optional[dict]: The parsed manifest data, or None if there was an error.
    """
    manifest_data = None
    try:
        if not os.path.exists(manifest_path):
            logging.warning("[MANIFEST] Serious issues in manifest for extension: " + extension_id)
            return None
        try:
            manifest = open(manifest_path, "r", encoding='utf-8-sig').read()
        except:
            manifest = open(manifest_path, "rb").read()
        if manifest is not None and manifest != "":
            try:
                manifest_data = json.loads(manifest)
            except:
                try:
                    manifest_data = ast.literal_eval(manifest)
                except:
                    try:
                        json_comment = JsonComment()
                        manifest_data = json_comment.loads(manifest)
                    except:
                        try:
                            manifest_data= jstyleson.loads(manifest)
                        except:
                            try:
                                minified = jsmin(manifest)
                                manifest_data = json.loads(minified)
                            except:
                                try:
                                    manifest = open(manifest_path, "r", encoding='utf-8-sig', errors='ignore').read()
                                    manifest_data = json.loads(manifest)
                                except:
                                    logging.warning("[MANIFEST] Serious issues in manifest for extension: " + extension_id)
                                    return None
    except:
        logging.error("[MANIFEST] Error while parsing the manifest for extension: " + extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))
    finally:
        return manifest_data

def get_action_popups(manifest: str, extension_id: str) -> list:
    """
    Extracts action popups from the manifest.

    Args:
        manifest (str): The manifest content.
        extension_id (str): The ID of the extension being processed.

    Returns:
        list: A list of action popups.
    """
    action_popups = []
    try:
        if manifest.get("page_action") and isinstance(manifest["page_action"], dict):
            popups = manifest["page_action"].get("default_popup")
            if isinstance(popups, str): action_popups.append(popups)
            elif isinstance(popups, list): action_popups.extend(popups)
        if manifest.get("browser_action") and isinstance(manifest["browser_action"], dict):
            popups = manifest["browser_action"].get("default_popup")
            if isinstance(popups, str): action_popups.append(popups)
            elif isinstance(popups, list): action_popups.extend(popups)
        if manifest.get("action") and isinstance(manifest["action"], dict):
            popups = manifest["action"].get("default_popup")
            if isinstance(popups, str): action_popups.append(popups)
            elif isinstance(popups, list): action_popups.extend(popups)
    except:
        logging.error("[MANIFEST] Error while extracting action popups from the manifest for extension: " + extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))
    finally:
        return action_popups

def get_background_scripts(manifest_content: dict, extension_id: str) -> list:
    """
    Extracts background scripts from the manifest.

    Args:
        manifest_content (dict): The manifest content.
        extension_id (str): The ID of the extension being processed.

    Returns:
        list: A list of background scripts.
    """
    bg_scripts = []
    try:
        if manifest_content:
            if "background" in manifest_content.keys():
                if type(manifest_content["background"]) is str:
                    bg_scripts.extend(manifest_content["background"])
                    return bg_scripts
                elif type(manifest_content["background"]) is list:
                    for entry in manifest_content["background"]:
                        if isinstance(entry, str): bg_scripts.append(entry)
                        elif isinstance(entry, dict):
                            for key, value in entry.items():
                                if key in ["scripts", "page", "service_worker"]:
                                     bg_scripts.extend(value)
                elif type(manifest_content["background"]) is dict:
                    if "scripts" in manifest_content["background"].keys():
                        if type(manifest_content["background"]["scripts"]) is list:
                            bg_scripts.extend(manifest_content["background"]["scripts"])
                        elif type(manifest_content["background"]["scripts"]) is str:
                            bg_scripts.append(manifest_content["background"]["scripts"])
                    if "page" in manifest_content["background"].keys():
                        if type(manifest_content["background"]["page"]) is list:
                            bg_scripts.extend(manifest_content["background"]["page"])
                        elif type(manifest_content["background"]["page"]) is str:
                            bg_scripts.append(manifest_content["background"]["page"])
                    if "service_worker" in manifest_content["background"].keys():
                        if type(manifest_content["background"]["service_worker"]) is list:
                            bg_scripts.extend(manifest_content["background"]["service_worker"])
                        elif type(manifest_content["background"]["service_worker"]) is str:
                            bg_scripts.append(manifest_content["background"]["service_worker"])
            action_popups = get_action_popups(manifest_content, extension_id)
            if action_popups: bg_scripts.extend(action_popups)
    except:
        logging.error("[MANIFEST] Error while extracting background scripts from the manifest for extension: " + extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))
    finally:
        return bg_scripts

def get_content_scripts(manifest_content: dict, file_list: str, key: str, sub_key: str, source_dir: str, extension_id: str, extended_war_check: bool = False) -> dict:
    """
    Extracts content scripts from the manifest.

    Args:
        manifest_content (dict): The manifest content.
        file_list (str): The list of files.
        key (str): The key to look for in the manifest.
        sub_key (str): The sub-key to look for in the manifest.
        source_dir (str): The source directory path.
        extension_id (str): The ID of the extension being processed.
        extended_war_check (bool): Enables extended WAR check (MAIN world scripts). Defaults to False.

    Returns:
        dict: A dictionary of content scripts and their matches.
    """
    content_scripts = defaultdict(list)
    try:
        prerequisites = [manifest_content, manifest_content.get(key, None) and isinstance(manifest_content[key], list)]
        if all(prerequisites):
            for entry in manifest_content[key]:
                if isinstance(entry, dict) and entry.get(sub_key, None) and entry.get("matches", None):
                    for res in entry.get(sub_key):
                        if isinstance(res, str) and ".js" in res and ".json" not in res:
                            if extended_war_check:
                                if entry.get("world", "ISOLATED") == "MAIN":
                                    content_scripts[res].extend(entry.get("matches"))
                            else:
                                content_scripts[res].extend(entry.get("matches"))
                elif not extended_war_check and isinstance(entry, str) and ".js" in entry and ".json" not in entry:
                    content_scripts[entry].extend(["<all_urls>"])
                elif not extended_war_check and isinstance(entry, str) and (".htm" in entry):
                    html_path = absolute_file_path_from_dir(file_list, source_dir, extension_id, entry, extension_id)
                    html_script_src = script_src_from_html(html_path, extension_id)
                    if html_script_src:
                        for script in html_script_src:
                            content_scripts[script].extend(["<all_urls>"])  
    except:
        logging.error("[MANIFEST] Error while extracting content scripts from the manifest for extension: " + extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))
    finally:
        return content_scripts

def get_resources(manifest_content: dict, file_list: str, key: str, sub_key: str, source_dir: str, extension_id: str) -> Tuple[dict, bool]:
    """
    Extracts resources from the manifest.

    Args:
        manifest_content (dict): The manifest content.
        file_list (str): The list of files.
        key (str): The key to look for in the manifest.
        sub_key (str): The sub-key to look for in the manifest.
        source_dir (str): The source directory path.
        extension_id (str): The ID of the extension being processed.

    Returns:
        Tuple[dict, bool]: A tuple containing the resources and a flag indicating if dynamic URLs were found.
    """
    resources = defaultdict(list)
    is_dynamic_url_found = False
    try:
        prerequisites = [manifest_content, manifest_content.get(key, None) and isinstance(manifest_content[key], list)]
        if all(prerequisites):
            for entry in manifest_content.get(key):
                if isinstance(entry, dict) and entry.get(sub_key, None) and entry.get("matches", None):
                    for res in entry.get(sub_key):
                        if isinstance(res, str) and ".js" in res and ".json" not in res:
                            resources[res].extend(entry["matches"])
                        elif isinstance(res, str) and ".htm" in res:
                            html_path = absolute_file_path_from_dir(file_list, source_dir, extension_id, res, extension_id)
                            html_script_src = script_src_from_html(html_path, extension_id)
                            if html_script_src:
                                for script in html_script_src:
                                    resources[script].extend(entry.get("matches"))
                    if "use_dynamic_url" in entry.keys() and entry["use_dynamic_url"]:
                        is_dynamic_url_found = True
                elif isinstance(entry, str) and ".js" in entry and ".json" not in entry: resources[entry].extend(["unknown"])
                elif isinstance(entry, str) and ".htm" in entry:
                    html_path = absolute_file_path_from_dir(file_list, source_dir, extension_id, entry, extension_id)
                    html_script_src = script_src_from_html(html_path, extension_id)
                    if html_script_src:
                        for script in html_script_src: resources[script].extend(["unknown"])
    except:
        logging.error("[MANIFEST] Error while extracting wars from the manifest for extension: " + extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))
    finally:
        return resources, is_dynamic_url_found

def has_api_permissions(api_permissions: set, required_permissions: list, extension_id: str) -> bool:
    """
    Checks if the extension has the required API permissions.

    Args:
        api_permissions (set): The set of API permissions.
        required_permissions (list): The list of required permissions.
        extension_id (str): The ID of the extension being processed.

    Returns:
        bool: True if the extension has the required permissions, False otherwise.
    """
    try:
        if any([perm in api_permissions for perm in required_permissions]):
            return True
        else: return False
    except:
        logging.error("[MANIFEST] Error while checking for relevant permissions for extension: " + extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))

def check_and_update_permissions(manifest_content: dict, perm: str, mandate_key: str, extension_id: str, perm_substitute: str = None, opt_key: str = None) -> dict:
    """
    Checks and updates the permissions in the manifest.

    Args:
        manifest_content (dict): The manifest content.
        perm (str): The permission to check and update.
        mandate_key (str): The key for mandatory permissions.
        extension_id (str): The ID of the extension being processed.
        perm_substitute (str, optional): The substitute permission. Defaults to None.
        opt_key (str, optional): The key for optional permissions. Defaults to None.

    Returns:
        dict: The updated manifest content.
    """
    try:
        """ If there is a permission that needs to be removed (from the optional configurations), we first remove it from the list of permissions.
        """
        if opt_key and manifest_content.get(opt_key):
            manifest_content[opt_key].remove(perm)
        
        """ We then add the permission or its substitute to the list of mandatory permissions.
        """ 
        perm = perm_substitute if perm_substitute else perm
        if manifest_content.get(mandate_key, None) and perm not in manifest_content.get(mandate_key, []):
            manifest_content[mandate_key].append(perm)
        else:
            manifest_content[mandate_key] = [perm]
    except:
        logging.error("[MANIFEST] Error while updating permissions in the manifest for extension: " + extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))
    finally:
        return manifest_content
    
def manifest_v2_permissions(manifest_content: dict, extension_id: str) -> Tuple[list, set]:
    """
    Extracts permissions from a manifest for a version 2 extension.

    Args:
        manifest_content (dict): The manifest content.
        extension_id (str): The ID of the extension being processed.

    Returns:
        Tuple[list, set]: A tuple containing the host permissions and API permissions.
    """
    host_permissions, api_permissions, total_permissions = [], [], []
    try:
        if not manifest_content: return [], []
        if manifest_content.get("permissions", None) and isinstance(manifest_content["permissions"], list):
            total_permissions.extend(manifest_content.get("permissions"))
        
        """ The following check is for the new `optional_host_permissions` applicable only to ADVANCED TESTS. Ideally, the first condition should never be met, given that the `optional_host_permissions` is a MV3 construct, and not available to MV2 extensions.
        """
        if ADVANCED_TEST and "optional_permissions" in manifest_content.keys() and type(manifest_content["optional_permissions"]) is list:
            total_permissions.extend(manifest_content["optional_permissions"])
            
        """ Given that host and API permissions could be mixed in the permissions list, we need to separate them out. We remove all the known API permissions from the total permissions list, and then extract the host permissions from the remaining list.
        """
        if isinstance(total_permissions, list):
            for idx in range(0, len(total_permissions)):
                """ Some permissions have further granular configurations in the form of key-value pairs. We need to extract the keys from them.
                """
                if isinstance(total_permissions[idx], dict):
                    total_permissions[idx] = list(total_permissions[idx].keys())[0]
            
            host_permissions = list(set(total_permissions) - set(API_PERMISSIONS))
        api_permissions = list(set(total_permissions) - set(host_permissions))
    except:
        logging.error("[MANIFEST] Error while extracting permissions from manifest of MV2 extension: " + extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))
    finally:
        return host_permissions, set(api_permissions)

def manifest_v3_permissions(manifest_content: dict, extension_id: str) -> Tuple[list, set]:
    """
    Extracts permissions from a manifest for a version 3 extension.

    Args:
        manifest_content (dict): The manifest content.
        extension_id (str): The ID of the extension being processed.

    Returns:
        Tuple[list, set]: A tuple containing the host permissions and API permissions.
    """
    host_permissions, api_permissions, total_permissions = [], [], []
    try:
        if not manifest_content: return [], []
        """ Ideally, the `permissions` key should only contain API permissions and the `host_permissions` key should only contain host permissions. However, we account for the edge case where the permissions are mixed.
        """
        if "host_permissions" in manifest_content.keys() and type(manifest_content["host_permissions"]) is list:
            total_permissions.extend(manifest_content["host_permissions"])
        if "permissions" in manifest_content.keys() and type(manifest_content["permissions"]) is list:
            total_permissions.extend(manifest_content["permissions"])
        """ The following checks are for the new `optional_permissions` and the `optional_host_permissions` applicable only to ADVANCED TESTS.
        """
        if ADVANCED_TEST and "optional_host_permissions" in manifest_content.keys() and type(manifest_content["optional_host_permissions"]) is list:
            total_permissions.extend(manifest_content["optional_host_permissions"])
        if ADVANCED_TEST and "optional_permissions" in manifest_content.keys() and type(manifest_content["optional_permissions"]) is list:
            total_permissions.extend(manifest_content["optional_permissions"])
        
        if isinstance(total_permissions, list):
            for idx in range(0, len(total_permissions)):
                """ Some permissions have further granular configurations in the form of key-value pairs. We need to extract the keys from them.
                """
                if isinstance(total_permissions[idx], dict):
                    total_permissions[idx] = list(total_permissions[idx].keys())[0]
            host_permissions = list(set(total_permissions) - set(API_PERMISSIONS))
        api_permissions = list(set(total_permissions) - set(host_permissions))
    except:
        logging.error("[MANIFEST] Error while extracting permissions from manifest of MV3 extension: " + extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))
    finally:
        return host_permissions, set(api_permissions)

def update_host_permissions(manifest_content: dict, key: str, sub_key: str, extension_id: str) -> dict:
    """
    Updates the host permissions in the manifest.

    Args:
        manifest_content (dict): The manifest content.
        key (str): The key to look for in the manifest.
        sub_key (str): The sub-key to look for in the manifest.
        extension_id (str): The ID of the extension being processed.

    Returns:
        dict: The updated manifest content.
    """
    try:
        prerequisites = [manifest_content, key in manifest_content.keys() and type(manifest_content[key]) == list]
        if not all(prerequisites): return
        for entry in manifest_content[key]:
            if isinstance(entry, dict) and sub_key in entry.keys() and "matches" in entry.keys():
                for idx in range(0, len(entry["matches"])):
                    if "https" in entry["matches"][idx]:
                        url = entry["matches"][idx].replace('https', 'http')
                        entry["matches"].append(url)
                    # elif "activeTab" == entry["matches"][idx]:
                    #     entry["matches"][idx] = entry["matches"][idx].replace("activeTab", "*://*.testserver.com:9000/*")
    except:
        logging.error("[MANIFEST] Error while updating host permissions in the manifest for extension: " + extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))

def update_api_permissions(manifest_content: dict, key: str, extension_id: str) -> dict:
    """
    Updates the API permissions in the manifest.

    Args:
        manifest_content (dict): The manifest content.
        key (str): The key to look for in the manifest.
        extension_id (str): The ID of the extension being processed.

    Returns:
        dict: The updated manifest content.
    """
    try:
        if key in manifest_content:
            for idx in range(0,len(manifest_content[key])):
                if "https" in manifest_content[key][idx]:
                    manifest_content[key].append(manifest_content[key][idx].replace("https", "http"))
                # elif "activeTab" == manifest_content[key][idx]:
                #     if manifest_content["manifest_version"] < 3:
                #         manifest_content[key][idx] = manifest_content[key][idx].replace("activeTab", "*://*.testserver.com:9000/*")
                #     elif "host_permissions" in manifest_content.keys():
                #         manifest_content["host_permissions"].append("*://*.testserver.com:9000/*")
                #     else:
                #         manifest_content["host_permissions"] = ["*://*.testserver.com:9000/*"]
        if key == "host_permissions" and manifest_content["manifest_version"] == 3:
            if "optional_host_permissions" in manifest_content:
                for url in manifest_content["optional_host_permissions"]:
                    new_url = url
                    if "https" in url:
                        new_url = url.replace("https", "http")
                    # elif "activeTab" == url:
                    #     new_url = url.replace("activeTab", "*://.testserver.com:9000/*")
                    if "host_permissions" not in manifest_content.keys():
                        manifest_content["host_permissions"] = list(set([url, new_url]))
                    manifest_content["host_permissions"].extend(list(set([url, new_url])))
            # if "optional_permissions" in manifest_content:
            #     if "activeTab" in manifest_content["optional_permissions"]:
            #         if "host_permissions" not in manifest_content.keys(): manifest_content["host_permissions"] = ["*://*.testserver.com:9000/*"]
            #         else: manifest_content["host_permissions"].append("*://*.testserver.com:9000/*")
    except:
        logging.error("[MANIFEST] Error while updating api permissions in the manifest for extension: " + extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))
