from files import absolute_file_path_from_dir, list_of_files
from multiprocessing.managers import DictProxy, ListProxy
from config import *

from itertools import chain
import jsbeautifier
import retirejs

def grep_invocations(script_path_list: list, target_apis: list, extension_id: str) -> list:
    """
    Searches for invocations of target APIs in the given list of script paths.

    Args:
        script_path_list (list): List of paths to the scripts to be analyzed.
        target_apis (list): List of target APIs to search for in the scripts.
        extension_id (str): The ID of the extension being processed.

    Returns:
        list: A list of APIs found in the scripts.
    """
    invocations = []
    try:
        for script_path in script_path_list:
            if isinstance(script_path, list): script_path = script_path[0]
            parser_process = subprocess.Popen(["node", JS_PARSER, script_path], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            parser_process.wait(600)
            script_data, _ = parser_process.stdout.read().decode().strip().lower(), parser_process.stderr.read().decode()
            if script_data is None or script_data == "":
                return invocations
            for api in target_apis:
                if api.lower() in script_data:
                    invocations.append(api)
    except subprocess.TimeoutExpired as te:
        pass
    except:
        logging.error("[UTILITY] Error in grep_invocations(): " + extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))
    finally:
        return invocations

def merge_scripts(scripts: str, source_dir: str, target_file: str, extension_id: str) -> None:
    """
    Merges multiple scripts into a single target file.

    Args:
        scripts (str): The scripts to be merged.
        source_dir (str): The source directory containing the scripts.
        target_file (str): The name of the target file to write the merged scripts to.
        extension_id (str): The ID of the extension being processed.

    Returns:
        None
    """
    try:
        if scripts:
            if os.path.exists(source_dir + extension_id + "/" + target_file):
                os.remove(source_dir + extension_id + "/" + target_file)
            file_list = list_of_files(source_dir + extension_id, extension_id)
            with open(source_dir + extension_id + "/" + target_file, "w") as nfh:
                for script in scripts:
                    absolute_path = script
                    if script and not script.startswith(source_dir):
                        absolute_path = absolute_file_path_from_dir(file_list, source_dir, extension_id, script, extension_id)
                    if absolute_path != "":
                        data = open(absolute_path, 'r', errors='ignore').read()
                        data = jsbeautifier.beautify(data)
                        nfh.write(data)
                nfh.close()
    except:
        logging.error("[UTILITY] Error in merge_scripts(): " + extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))

def detect_libraries(scripts: list, extension_id: str) -> list:
    """
    Detects and removes known libraries from the list of scripts.

    Args:
        scripts (list): The list of scripts to be analyzed.
        extension_id (str): The ID of the extension being processed.

    Returns:
        list: The list of scripts with known libraries removed.
    """
    try:
        idx = 0
        while True:
            if scripts is None or idx >= len(scripts):
                break
            elif len(retirejs.scan_filename(scripts[idx])) or "jquery" in scripts[idx]:
                del scripts[idx]
            else:
                idx += 1
                continue
    except:
        logging.error("[UTILITY] Error while detecting libraries for script:" + extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))

def filter_wars(war_scripts: dict, cs_hosts: list, manifest_processed_urls: set, has_scripting_perm: bool, extension_id: str) -> dict:
    """
    Filters unnecessary WAR scripts based on the given criteria.

    Args:
        war_scripts (dict): The dictionary of WAR scripts to be filtered.
        cs_hosts (list): The list of content script hosts.
        manifest_processed_urls (set): The set of processed URLs from the manifest.
        has_scripting_perm (bool): Whether the extension has scripting permissions.
        extension_id (str): The ID of the extension being processed.

    Returns:
        dict: The filtered dictionary of WAR scripts.
    """
    wars = deepcopy(war_scripts)
    try:
        if "<all_urls>" in manifest_processed_urls and has_scripting_perm:
            return war_scripts
        if "<all_urls>" in cs_hosts:
            return war_scripts
        # Need to refine the following permissions check
        if ADVANCED_TEST:
            """ If the content scripts has set of permissions H1, and the manifest has set of permissions H2, then there are two cases for WARs with host permissions H3."""
            for script, hosts in wars.items():
                # If H3 is empty then, the WARs are potentially injected either from content scripts or from the manifest.
                if not hosts:
                    continue
                # If H3 is not empty, then H3 maybe a subset of H1 or H2, or it may be not.
                # We only consider the WARs with hosts that are either a subset of H1 or H2, for simplicity.
                elif has_scripting_perm or set(hosts).intersection(manifest_processed_urls):
                    continue
                elif set(hosts).intersection(cs_hosts):
                    continue
                elif "<all_urls>" in manifest_processed_urls or "<all_urls>" in cs_hosts:
                    continue
                elif "activeTab" in manifest_processed_urls or "activeTab" in cs_hosts:
                    continue
                else:
                    del war_scripts[script]
        if not ADVANCED_TEST:
            for script, hosts in wars.items():
                if "unknown" in hosts and script in war_scripts:
                    del war_scripts[script]
    except:
        logging.error("[UTILITY] Error while filtering unnecssary WAR scripts:" + extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))
    return war_scripts

def flatten_chain(list_of_lists: list) -> list:
    """
    Flattens a list of lists into a single list.

    Args:
        list_of_lists (list): The list of lists to be flattened.

    Returns:
        list: The flattened list.
    """
    return list(chain.from_iterable(list_of_lists))

def serialize_object(data):
    """
    Serializes the given data object to a JSON-compatible format.

    Args:
        data: The data object to serialize.

    Returns:
        The serialized data object.
    """
    if isinstance(data, set):
        return list(data)
    elif isinstance(data, defaultdict):
        return dict(data)
    elif isinstance(data, DictProxy):
        return dict(data)
    elif isinstance(data, ListProxy):
        return list(data)
    return data
