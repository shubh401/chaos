from files import absolute_path_of_scripts, list_of_files
from utility import grep_invocations, filter_wars
from post_processor import post_process
from extractor import extract_package
from urls import preprocess_urls
from utility import flatten_chain
from manifest import *

class Processor:
    def __init__(self, extension_id: str) -> None:
        """
        Initializes the Processor instance with the given extension ID.

        Args:
            extension_id (str): The ID of the extension to be processed.
        """
        self.extension_id = extension_id
        self.invocations = defaultdict()
        self.processed_host_perms = set()
        self.has_scripting_perm = False
        self.is_ns_test_required = False
        self.is_dynamic_url_found = False
        self.perm_bits = [False, False, False]
        self.host_perms, self.api_perms = [], []
        self.bg_absolute_paths, self.bg_filtered_scripts = defaultdict(), []
        self.war_absolute_paths, self.war_filtered_scripts = defaultdict(), []
        self.processed_cs_urls, self.processed_war_urls = defaultdict(), defaultdict()
        self.cs_absolute_paths, self.cs_filtered_scripts, self.cs_hosts = defaultdict(), [], []
        
    def extract_extension(self) -> bool:
        """
        Extracts the extension package to the unzipped directory.

        Returns:
            bool: True if the extraction was successful, False otherwise.
        """
        try:
            if extract_package(EXTENSION_DIR, UNZIPPED_DIR, self.extension_id):
                if '.' in self.extension_id: self.extension_id = self.extension_id[:-4]
                self.file_list = list_of_files(UNZIPPED_DIR, self.extension_id)
                return True
        except:
            logging.error("[PROCESSOR] Error in extract_extension(): " + self.extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))
        return False

    def read_manifest(self) -> bool:
        """
        Reads and parses the manifest file of the extension.

        Returns:
            bool: True if the manifest was read successfully, False otherwise.
        """
        try:
            self.manifest_content = get_manifest(UNZIPPED_DIR + self.extension_id + "/manifest.json", self.extension_id)
            if not self.manifest_content or "app" in self.manifest_content.keys() or "theme" in self.manifest_content.keys():
                return False
            return True
        except:
            logging.error("[PROCESSOR] Error in read_manifest(): " + self.extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))
            return False

    def extension_permissions(self) -> None:
        """
        Extracts and processes the API and host permissions from the manifest file.
        """
        try:
            if "manifest_version" not in self.manifest_content.keys() or self.manifest_content["manifest_version"] == 2:
                self.host_perms, self.api_perms = manifest_v2_permissions(self.manifest_content, self.extension_id)
            else:
                self.host_perms, self.api_perms = manifest_v3_permissions(self.manifest_content, self.extension_id)
            manifest_url_dict = preprocess_urls(self.host_perms, self.extension_id)
            self.processed_host_perms = set(manifest_url_dict.values())
        except:
            logging.error("[PROCESSOR] Error in extension_permissions(): " + self.extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))

    def check_api_permissions(self) -> None:
        """
        Checks the presence of API permissions of the extension.
        """
        try:
            if not self.api_perms and not self.host_perms: return
            has_cookies_perm = has_api_permissions(self.api_perms, ["cookies"], self.extension_id)
            if ADVANCED_TEST:
                has_scripting_perm = has_api_permissions(self.api_perms.union(set(self.host_perms)), ["scripting", "tabs", "activeTab"], self.extension_id)
            else:
                has_scripting_perm = has_api_permissions(self.api_perms, ["scripting", "tabs"], self.extension_id)
            has_webRequest_perm = has_api_permissions(self.api_perms, ["webRequest", "webRequestBlocking", "webRequestAuthProvider", "declarativeNetRequest", "declarativeNetRequestWithHostAccess", "declarativeNetRequestFeedback"], self.extension_id)
            self.perm_bits = [has_cookies_perm, has_scripting_perm, has_webRequest_perm]
        except:
            logging.error("[PROCESSOR] Error in check_api_permissions(): " + self.extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))

    def qualifies_for_tests(self, test_type: str) -> bool:
        """
        Determines if the extension qualifies for the specified tests.

        Args:
            test_type (str): The type of test to check for qualification.

        Returns:
            bool: True if the extension qualifies for the tests, False otherwise.
        """
        try:
            """ We only select those extensions with `scripting` permission which also has `<all_urls>` in their `host_permissions` for the basic test. For the advanced tests, the host_permissions does not matter since we inject our own endpoint in the manifest anyways.
            """
            if test_type == "scripting":
                # Can restrict the checks further to only `scripting` permission bits.
                if self.perm_bits[1] and (ADVANCED_TEST or "<all_urls>" in self.processed_host_perms):
                    return True
            elif test_type == "cs" and self.cs_absolute_paths:
                if self.cs_hosts and (ADVANCED_TEST or "<all_urls>" in self.processed_cs_urls.values()):
                    return True
            elif test_type == "war" and self.war_absolute_paths:
                if "<all_urls>" in self.processed_cs_urls.values() or "<all_urls>" in self.processed_host_perms:
                    return True
                elif ADVANCED_TEST and len(self.processed_war_urls.values()) > 0:
                    return True
        except:
            logging.error("[PROCESSOR] Error in qualifies_for_tests(): " + self.extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))
        return False

    def handle_background_scripts(self) -> None:
        """
        Handles the background scripts of the extension.
        Checks if the extension qualifies for background script tests,
        processes the background scripts, and checks for invocations of specified APIs.
        """
        apis = []
        try:
            if not self.qualifies_for_tests("scripting"): return
            self.bg_scripts = get_background_scripts(self.manifest_content, self.extension_id)
            for script in self.bg_scripts:
                    bg_absolute_path, filtered = absolute_path_of_scripts([script], self.file_list, UNZIPPED_DIR, self.extension_id)
                    if bg_absolute_path:
                        if script.endswith("htm") or script.endswith("html"):
                            for scr in bg_absolute_path:
                                self.bg_absolute_paths[scr] = scr
                        else: self.bg_absolute_paths[script] = bg_absolute_path
                    elif filtered: self.bg_filtered_scripts.extend(filtered)
            
            if self.perm_bits[0]: apis.extend(COOKIE_APIS)
            if self.perm_bits[1]: apis.extend(SCRIPT_INJECTION_APIS)
            if self.perm_bits[2]: apis.extend(HEADER_APIS)
            if apis: self.check_invocations(list(self.bg_absolute_paths.keys()), apis, "bg")
        except:
            logging.error("[PROCESSOR] Error in handle_background_scripts(): " + self.extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))

    def handle_content_scripts(self) -> None:
        """
        Handles the content scripts of the extension.
        Processes the content scripts and checks if they qualify for basic or advanced tests.
        """
        try:
            self.cs_scripts = get_content_scripts(self.manifest_content, self.file_list, "content_scripts", "js", self.extension_id, UNZIPPED_DIR)
            if not self.cs_scripts: return
            self.cs_hosts = flatten_chain(self.cs_scripts.values())
            self.processed_cs_urls = preprocess_urls(self.cs_hosts, self.extension_id)
            if ADVANCED_TEST or "<all_urls>" in self.processed_cs_urls.values():
                self.cs_absolute_paths, self.cs_filtered_scripts = self.analyze_scripts(self.cs_scripts, "cs")
        except:
            logging.error("[PROCESSOR] Error in handle_content_scripts(): " + self.extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))

    def handle_wars(self) -> None:
        """
        Handles the web accessible resources (WARs) of the extension.
        Processes the WARs and checks if they qualify for namespace tests.
        """
        try:
            self.war_scripts, self.is_dynamic_url_found = get_resources(self.manifest_content, self.file_list, "web_accessible_resources", "resources", self.extension_id, UNZIPPED_DIR)
            self.main_world_scripts = get_content_scripts(self.manifest_content, self.file_list, "content_scripts", "js", UNZIPPED_DIR, self.extension_id, True)
            
            if self.main_world_scripts:
                for script, matches in self.main_world_scripts.items():
                    self.war_scripts[script].extend(matches)
            
            if self.war_scripts:
                self.war_scripts = filter_wars(self.war_scripts, self.cs_hosts, self.processed_host_perms, self.perm_bits[1], self.extension_id)
                if self.war_scripts:
                    self.is_ns_test_required = True
                    self.processed_war_urls = preprocess_urls(flatten_chain(self.war_scripts.values()), self.extension_id)
                    self.war_absolute_paths, self.war_filtered_scripts = self.analyze_scripts(self.war_scripts, "war")
        except:
            logging.error("[PROCESSOR] Error in handle_wars(): " + self.extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))

    def analyze_scripts(self, scripts: dict, script_type: str = "") -> Tuple[dict, list]:
        """
        Analyzes the given scripts and checks for invocations of specified APIs.

        Args:
            scripts (dict): The scripts to be analyzed.
            script_type (str, optional): The type of scripts being analyzed. Defaults to "".

        Returns:
            Tuple[dict, list]: A tuple containing the absolute paths of the scripts and the filtered scripts.
        """
        absolute_paths, filtered_scripts = defaultdict(), []
        try:
            for script, hosts in scripts.items():
                # The next line is redundant, need to remove this later!
                processed_hosts_dict = preprocess_urls(hosts, self.extension_id)
                script_absolute_path, filtered = absolute_path_of_scripts([script], self.file_list, UNZIPPED_DIR, self.extension_id)
                if script_absolute_path and (ADVANCED_TEST or "<all_urls>" in processed_hosts_dict.values() or "unknown" in processed_hosts_dict.values()):
                    absolute_paths[script] = script_absolute_path
                elif filtered: filtered_scripts.extend(filtered)
            
            if absolute_paths:
                self.check_invocations(list(absolute_paths.keys()), INTERACTION_APIS, script_type)
        except:
            logging.error("[PROCESSOR] Error in analyze_scripts(): " + self.extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))
        finally:
            return absolute_paths, filtered_scripts

    def check_invocations(self, script_paths: list, apis: list, script_type: str) -> None:
        """
        Checks for invocations of specified APIs in the given script paths.

        Args:
            script_paths (list): The paths of the scripts to be checked.
            apis (list): The APIs to check for invocations.
            script_type (str): The type of scripts being checked.
        """
        try:
            invocations = grep_invocations(script_paths, apis, self.extension_id)
            if invocations:
                self.invocations[script_type] = invocations
        except:
            logging.error("[PROCESSOR] Error in check_invocations(): " + self.extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))

    def start_processing(self) -> Tuple[dict, list, bool, str]:
        """
        Starts the processing of the extension.
        Extracts the extension, reads the manifest, processes permissions,
        handles background scripts, content scripts, and web accessible resources,
        and post-processes the selected extensions.

        Returns:
            Tuple[dict, list, bool, str]: A tuple containing the invocations, permission bits,
            dynamic URL found flag, and the extension ID.
        """
        try:
            """ We first extract the extension, and then, its metadata.
            """
            if self.extract_extension() and self.read_manifest():
                self.extension_permissions()
                self.check_api_permissions()
            
                """ We only check for background script related invocations if the extension has scripting permissions.
                """
                if self.perm_bits[1]: self.handle_background_scripts()
                self.handle_content_scripts()
                self.handle_wars()
            
                """ We now post-processs the selected extensions based on the extracted bits and the class of attcaks they may be vulnerable to.
                """
                QUAL_BIT = False
                if self.qualifies_for_tests("scripting"):
                    self.manifest_content = post_process(self.manifest_content, self.processed_host_perms, self.extension_id, "scripting")
                    QUAL_BIT = True
                
                if ADVANCED_TEST or not QUAL_BIT:
                    if self.qualifies_for_tests("cs"):
                        self.manifest_content = post_process(self.manifest_content, self.processed_cs_urls.values(), self.extension_id, "cs")
                    if self.qualifies_for_tests("war"):
                        self.manifest_content = post_process(self.manifest_content, self.processed_war_urls.values(), self.extension_id, "war", self.war_scripts.keys(), self.main_world_scripts.keys())
                    elif "<all_urls>" in self.processed_host_perms and self.manifest_content.get("devtools_page", None):
                        self.manifest_content = post_process(self.manifest_content, self.processed_war_urls.values(), self.extension_id, "war")
        except:
            logging.error("[PROCESSOR] Error in start_processing(): " + self.extension_id + " - " + ", ".join(traceback.format_exc().split("\n")))
        finally:
            return self.invocations, self.perm_bits, self.is_dynamic_url_found, self.extension_id
