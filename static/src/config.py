from collections import defaultdict
from typing import Tuple, Optional
from dotenv import load_dotenv
from copy import deepcopy
from enums import Script

import multiprocessing as mp
import subprocess
import traceback
import logging
import shutil
import json
import os

load_dotenv(dotenv_path="~/chaos/.env")

# Configuration constants
WORKERS = 1
DATASET_TS = os.getenv("DATASET_TS")
EXTENSION_TYPE = os.getenv("EXTENSION_TYPE", "chrome")
DATASET = f"crx_{DATASET_TS}"

EXTENSION_DIR = f"/datasets/{DATASET}/"
UNZIPPED_DIR = f"/datasets/unzipped/{DATASET}/"
API_PERMISSIONS = json.loads(open("./static/src/helpers/api_permissions.json", "r").read())

CS_HOOK_NAME = "__cs_hook.js"
CS_HOOK_PATH = f"./static/src/hooks/{CS_HOOK_NAME}"
HOOK_DATA = open(CS_HOOK_PATH, 'r').read()
HOOK_CONFIG = json.load(open("./static/src/helpers/content_script_definition.json", "r"))

SCRIPT_INJECTION_APIS = ["registerContentScripts", "updateContentScripts", "executeScript"]
COOKIE_APIS = ["cookies.get", "cookies.getall", "cookies.getallcookiestores", "cookies.remove", "cookies.set", "cookies.onchanged"]

INTERACTION_APIS = ["document.cookie", "indexedDB", "idb", "localStorage.setItem", "localStorage.getItem", "localStorage[", "localStorage.", "sessionStorage.", "sessionStorage.setItem", "sessionStorage.getItem", "sessionStorage[", "window.addEventListener", "addEventListener", "window.postMessage", "postMessage", "createElement('script')", 'createElement("script")', 'createElement(', "getElementById", "getElementByClassName", "getElementByName", "getElementByTagName", "getElementByTagNameNS", "hasAttribute(", "hasAttributes(", "hasAttributeNS(", "append", "appendChild", "insertAdjacentElement", "insertAdjacentHTML", "attachShadow", "removeAttribute", "removeAttributeNode", "removeAttributeNS", "replaceChildren", "setAttribute", "setAttributeNode", "setAttributeNodeNS" "insertBefore", "insertAdjacentHTML", "setHTMLUnsafe", "toggleAttribute", "write", "writeln"]

HEADER_APIS = ["onBeforeSendHeaders", "onHeadersReceived", "updateDynamicRules", "updateStaticRules"]

MAX_JS_SIZE = 30000000
JS_BLACKLISTS = ["node_modules", 'jquery', 'angular', 'fontawesome', 'bootstrap', "react-dom", "socker.io", "vue", "jsencrypt", "mathjs", "sugar", "react", "lodash", "unidecode", "scc1t2", "ace-builds/src/theme-", "ace-builds/src/snippets/", "ace/src/theme-", "ace/src/snippets/", "ace/theme-", "ace/snippets/", "languages/", "locales/", "/ptk/packages/"]

TEST_URL = "https://testserver.com:9000/*"
HOST_SUBSTITUTE = ["*://testserver.com:9000/*", "*://testserver.com:9010/*"]
CRX_UNPACKER = "./static/src/helpers/unpack_crx.js"
JS_PARSER = "./static/src/helpers/js_parser.js"

DIR_EXTENSION = os.getenv("DIR_EXTENSION", "basic")
ADVANCED_TEST = bool(os.getenv("ADVANCED_TEST", "False") == "True")
SHARED_NAMESPACE_DIR = f"/datasets/shared_namespace/{DIR_EXTENSION}/{DATASET}/"
ISOLATED_NAMESPACE_DIR = f"/datasets/isolated_namespace/{DIR_EXTENSION}/{DATASET}/"

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_NAME = os.getenv('DB_NAME')
DB_PASS = os.getenv('DB_PASS')

# Setup logging
LOGS = f"./static/logs/{DATASET}/{DIR_EXTENSION}/"
if os.path.exists(LOGS): shutil.rmtree(LOGS)
os.makedirs(LOGS, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    filename=f"{LOGS}/static_analyzer.log",
    filemode="a+"
)
logging.getLogger("urllib3").setLevel(logging.ERROR)

MANAGER = mp.Manager()
HOSTS_DICT = MANAGER.dict()

