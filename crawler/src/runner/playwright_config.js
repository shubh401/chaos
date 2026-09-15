require('dotenv').config({path: `~/chaos/.env`})

let DATASET = process.env.DATASET;
let TEST_TYPE = process.env.TEST_TYPE;
let META_TEST_TYPE = process.env.META_TEST_TYPE;
let TABLE_SUFFIX = process.env.TABLE_SUFFIX;
let CRAWL_URL_TYPE = process.env.CRAWL_URL_TYPE;
let IGNORE_SCRIPT_NAMES = new Set([
    "mutation.js", "sparkmd5.js", "mutation_hashes.js",
    "hook.js", "hook_break.js", "raider.js", "raider_ui.js", "raider_break.js",
    "lifecycle_tracker.js", "v2_dispatch.js",
    "proto_poison.js", "proto_poison_break.js",
    "promise_poison.js", "promise_poison_break.js",
    "event_swallow.js", "event_swallow_break.js",
    "eval_poison.js", "eval_poison_break.js",
    "mo.js", "hook_ui.js", "hook_helper.js",
    "raider_simple_ui.js", "mutation_ui.js", "clobber_ui.js",
    "ads.js", "ads_hooked.js",
]);

let MAX_RETRIES = 3;
let TMP_DIR = "/mnt/extensions/";
let USER_DATA_DIR = process.env.USER_DATA_DIR;
let REMOTE_URL = `http://testserver.com:9000/${TEST_TYPE}/`;
let DEBUG = (process.env.DEBUG).toLowerCase() === "true" ? true : false;
let LOG_DIR = `~/chaos/crawler/logs/${META_TEST_TYPE}/${TEST_TYPE}/${DATASET.substring(0,4)}${TABLE_SUFFIX}_${CRAWL_URL_TYPE}/`;
let HTML_DIR = `~/chaos/crawler/html/${META_TEST_TYPE}/${TEST_TYPE}/${DATASET.substring(0,4)}${TABLE_SUFFIX}_${CRAWL_URL_TYPE}/`;

let ADVANCED_TEST, EXTENSION_DIR, DIR_EXTENSION;
ADVANCED_TEST = (process.env.ADVANCED_TEST).toLowerCase() === "true" ? true : false;
DIR_EXTENSION = process.env.DIR_EXTENSION;
EXTENSION_DIR = `${TMP_DIR}${DIR_EXTENSION}/${DATASET}/`;

let CRAWL_TIMEOUT = 30000
let NAVIGATION_TIMEOUT = 30000
let WAIT_TIMEOUT = 6000
let VIEWPORT_SIZE = { "width": 1920, "height": 1080 }

let CHROME_LAUNCH_ARGS = {
    headless: false,
    timeout: 30000,
    ignoreHTTPSErrors: true,
    "args": [
        '--headless=new',
        '--no-sandbox',
        '--no-zygote',
        '--no-first-run',
        '--start-maximized',
        '--disable-infobars',
        '--disable-dev-shm-usage',
        '--disable-setuid-sandbox',
        '--ignore-certificate-errors',
        '--disable-software-rasterizer',
        '--allow-running-insecure-content',
        '--ignore-certificate-errors-spki-list',
        '--enable-logging=stderr',
        `--unsafely-treat-insecure-origin-as-secure=http://testserver.com:9000/${TEST_TYPE}/`,
        '--disable-gpu',
        '--allow-future-manifest-version',
        '--allow-legacy-extension-manifests',
    ]
};

module.exports = {
    DEBUG,
    TABLE_SUFFIX,
    DATASET,
    LOG_DIR,
    HTML_DIR,
    META_TEST_TYPE,
    REMOTE_URL,
    IGNORE_SCRIPT_NAMES,
    IS_MULTI_VISIT,
    TEST_TYPE,
    VIEWPORT_SIZE,
    MAX_RETRIES,
    CRAWL_TIMEOUT,
    USER_DATA_DIR,
    NAVIGATION_TIMEOUT,
    WAIT_TIMEOUT,
    TMP_DIR,
    EXTENSION_DIR,
    CHROME_LAUNCH_ARGS,
}
