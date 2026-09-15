const { chromium } = require('playwright');
const config = require("./playwright_config.js");
const { appendFileSync, existsSync, rmSync } = require("fs");
const XMLHttpRequest = require('xmlhttprequest').XMLHttpRequest;

let EXTENSION_ID;
let VISIT;
let UID;
let URL;

/**
 * Injects initialization scripts (hooks) into the given context.
 *
 * @param {Object} context - The context in which to inject the hooks.
 * @param {Function} context.addInitScript - Function to add an initialization script to the context.
 * @throws Will throw an error if the script injection fails.
 */
async function injectHooks(context) {
  try {
    await context.addInitScript({
      path: '../hooks/hook_logger.js'
    });
  } catch (e) {
    logError(`Error while injecting hooks for: ${EXTENSION_ID} - ${e.message}\n`, e);
  }
}

/**
 * Logs an error message and sends it to the server.
 *
 * @param {string} err - The error message to log.
 * @param {Error} errObj - The error object containing the stack trace.
 */
function logError(err, errObj) {
  try {
    appendFileSync(`${config.LOG_DIR}runner.log`, `${err}\n`);
    if (!errObj) return;
    let data = JSON.stringify({
      "source": "runner",
      "EXTENSION_ID": EXTENSION_ID,
      "visit": VISIT,
      "url": URL,
      "contextURL": URL,
      "error": {"stack": errObj.stack, "message": errObj.message, "name": errObj.name}
    });
    let xmlHTTPRequest = new XMLHttpRequest();
    xmlHTTPRequest.onreadystatechange = function () {
      if (xmlHTTPRequest.readyState === 4) {
        if (xmlHTTPRequest.status >= 300) {
          console.error("Error, status code = " + xmlHTTPRequest.status);
        }
      }
    };
    xmlHTTPRequest.open("POST", `${config.REMOTE_URL}error`, true);
    xmlHTTPRequest.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xmlHTTPRequest.send(data);
  } catch (e) {
    console.error(e);
  }
}

/**
 * Logs the coverage data by sending it to the remote server.
 *
 * @param {Object} coverageData - The coverage data to be logged.
 * @returns {Promise<void>} - A promise that resolves when the logging is complete.
 * @throws {Error} - Throws an error if there is an issue with the logging process.
 */
async function logCoverage(coverageData) {
  try {
    let data = JSON.stringify({
      "extensionId": EXTENSION_ID,
      "visit": VISIT,
      "url": URL,
      "coverage": coverageData
    });
    let xmlHTTPRequest = new XMLHttpRequest();
    xmlHTTPRequest.onreadystatechange = function () {
      if (xmlHTTPRequest.readyState === 4) {
        if (xmlHTTPRequest.status >= 300) {
          console.error("Error, status code = " + xmlHTTPRequest.status);
        }
      }
    };
    xmlHTTPRequest.open("POST", `${config.REMOTE_URL}coverage`, true);
    xmlHTTPRequest.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xmlHTTPRequest.send(data);
  } catch (e) {
    console.error(e);
  }
}

/**
 * Calculates the code coverage for a given set of scripts.
 *
 * @param {Object} jsonData - The JSON data containing the result of scripts.
 * @param {Array} jsonData.result - An array of script objects.
 * @param {string} jsonData.result[].url - The URL of the script.
 * @param {Array} jsonData.result[].functions - An array of function objects within the script.
 * @param {Array} jsonData.result[].functions[].ranges - An array of range objects within the function.
 * @param {number} jsonData.result[].functions[].ranges[].startOffset - The start offset of the range.
 * @param {number} jsonData.result[].functions[].ranges[].endOffset - The end offset of the range.
 * @param {number} jsonData.result[].functions[].ranges[].count - The execution count of the range.
 * @returns {Promise<Object>} A promise that resolves to an object mapping script URLs to an array containing the total length, executed length, and coverage percentage.
 */
async function calculateCoverage(jsonData) {
  const resultMap = {};

  for (const script of jsonData.result) {
      const scriptURL = script.url;
      let scriptName = scriptURL.split('=').length > 1 ? scriptURL.split('=')[1]: '';
      if (config.IGNORE_SCRIPT_NAMES.has(scriptName)) {
          continue;
      }
      let totalLength = 0;
      const nonExecutedIntervals = [];

      // Determine total length and collect non-executed intervals
      for (const func of script.functions) {
          for (const range of func.ranges) {
              totalLength = Math.max(totalLength, range.endOffset);
              if (range.count === 0) {
                  nonExecutedIntervals.push([range.startOffset, range.endOffset]);
              }
          }
      }

      // Merge overlapping intervals
      const mergedIntervals = mergeIntervals(nonExecutedIntervals);

      // Subtract non-executed lengths from total length
      let executedLength = totalLength;
      for (const [start, end] of mergedIntervals) {
          executedLength -= (end - start);
      }

      // Calculate coverage percentage
      const coveragePercentage = totalLength > 0 ? (executedLength / totalLength) * 100 : 0;
      resultMap[scriptURL] = [totalLength, executedLength, coveragePercentage];
  }

  return resultMap;
}

/**
 * Merges overlapping intervals.
 *
 * Given a collection of intervals, this function merges all overlapping intervals.
 *
 * @param {number[][]} intervals - An array of intervals, where each interval is represented as a two-element array [start, end].
 * @returns {number[][]} - A new array of merged intervals.
 */
function mergeIntervals(intervals) {
  // Sort intervals based on the start position
  intervals.sort((a, b) => a[0] - b[0]);
  const merged = [];
  for (const [currentStart, currentEnd] of intervals) {
      if (!merged.length || merged[merged.length - 1][1] < currentStart) {
          merged.push([currentStart, currentEnd]);  // No overlap
      } else {
          // There is overlap, extend the current interval
          merged[merged.length - 1][1] = Math.max(merged[merged.length - 1][1], currentEnd);
      }
  }
  return merged;
}

/**
 * Gets a new page handle from the browser context.
 *
 * @param {object} context - The browser context.
 * @returns {Promise<object>} The page handle.
 */
async function getPageHandle(context) {
  try {
    if (context === undefined) {
      console.error(`Browser instance is dead!`);
      logError(`Browser instance is dead for extension: ${EXTENSION_ID}.\n`);
      process.exit(1);
    }
    let page = await context.newPage();
    page.setDefaultNavigationTimeout(config.NAVIGATION_TIMEOUT);
    await page.setViewportSize(config.VIEWPORT_SIZE);
    return page;
  } catch (e) {
    logError(`Error while getting fresh page handle for: ${EXTENSION_ID} - ${e.message}\n`, e);
  }
}

/**
 * Manages code coverage operations using the Chrome DevTools Protocol (CDP) session.
 *
 * @param {object} cdpSession - The CDP session object used to communicate with the browser.
 * @param {string} operation - The operation to perform. Can be "start" to start coverage,
 *                             "coverage" to take coverage, or "coverage-stop" to stop coverage.
 * @returns {Promise<void>} - A promise that resolves when the operation is complete.
 * @throws {Error} - Throws an error if there is an issue with the CDP session or coverage operations.
 */
async function codeCoverage(cdpSession, operation) {
  try {
    if (operation === "start") {
      await cdpSession.send('Profiler.enable');
      await cdpSession.send('Profiler.startPreciseCoverage', {'detailed': true});
    } else if (operation.startsWith("coverage")) {
      let coverageData = await cdpSession.send('Profiler.takePreciseCoverage');
      let coverageMap = await calculateCoverage(coverageData);
      await logCoverage(coverageMap);
      if (operation.endsWith("stop")) {
        await cdpSession.send('Profiler.stopPreciseCoverage');
        await cdpSession.send('Profiler.disable');
      }
    }
  } catch (e) {
    logError(`Error while getting code coverage for: ${EXTENSION_ID} - ${e.message}\n`, e);
  }
}

/**
 * Navigates the browser to the specified URL and waits for a specified timeout.
 *
 * @param {object} context - The browser context.
 * @param {string} url - The URL to navigate to.
 */
async function browse(context, url) {
  let page, cdpSession;
  try {
    page = await getPageHandle(context);
    cdpSession = await context.newCDPSession(page);
    await codeCoverage(cdpSession, "start");
    await page.goto(url, {
      waitUntil: 'load',
      timeout: config.CRAWL_TIMEOUT,
    });
    console.log(`${page.url()}`);
    await codeCoverage(cdpSession, "coverage&stop");
    await page.waitForTimeout(config.WAIT_TIMEOUT);
    try {
      if (config.META_TEST_TYPE === "advanced" && config.TEST_TYPE === "isolated") {
      let pageHTML = await page.content();
      if (pageHTML && pageHTML !== "") {
         appendFileSync(`${config.HTML_DIR}${EXTENSION_ID}_${VISIT}.html`, `${pageHTML}\n`);
      }
    }
    } catch (e) {
      logError(`Error while writing HTML content for: ${EXTENSION_ID} - ${e.message}\n`, e);
    }
    try {
      await page.goto("about:blank", {
        waitUntil: 'domcontentloaded',
        timeout: 1000,
      });
    } catch (e) {}
    await Promise.race([page?.close(), page?.close(), page?.close(), page?.close(), page?.close(), page?.close()]);
  } catch (e) {
    throw new Error(e);
  }
}

/**
 * Detects installed extensions in the browser.
 *
 * @param {object} browser - The browser instance.
 * @returns {Promise<boolean>} True if extensions are detected, False otherwise.
 */
async function detectExtension(browser) {
  try {
    let page = await browser.newPage();
    await page.goto('chrome://extensions', {
      waitUntil: 'domcontentloaded',
      timeout: 5000,
    });
    // await page.screenshot({ path: `${config.LOG_DIR}screenshots/${EXTENSION_ID}_${UID}.png`, fullPage: true });
    const extensions = await page.evaluateHandle(() => [...document.querySelectorAll('body > extensions-manager')[0]
      .shadowRoot.querySelector('#items-list')
      .shadowRoot.querySelectorAll('extensions-item')
    ].map(elem => elem.id));
    let extensionsList = await extensions.jsonValue();
    await Promise.race([page?.close(), page?.close(), page?.close()]);
    if (extensionsList.length > 0) {
      return true;
    } else{
      logError(`Warning: No extensions detected for: ${config.EXTENSION_DIR}${EXTENSION_ID}.`);
      return false;
    }
  } catch (e) {
    logError(`Error while detecting installed extensions while testing for: ${EXTENSION_ID} - ${e.message}\n`, e);
  }
}

/**
 * Gets a browser handle with the specified extensions and settings.
 *
 * @returns {Promise<object>} The browser context.
 */
async function getBrowserHandle() {
  try {
    let launchArgs = config.CHROME_LAUNCH_ARGS;
    launchArgs["args"].push(`--disable-extensions-except=${config.EXTENSION_DIR}${EXTENSION_ID}/,`)
    launchArgs["args"].push(`--load-extension=${config.EXTENSION_DIR}${EXTENSION_ID}/,`)
    let context = await chromium
      .launchPersistentContext(`${config.USER_DATA_DIR}${EXTENSION_ID}_${UID}`, launchArgs)
      .catch(e => logError(`Error while instantiating browser : ${e.toString()}.`));
    if (context === undefined || !await detectExtension(context)) {
      await context?.close();
      return;
    }
    
    if (!URL.includes("testserver.com")) {
      await injectHooks(context);
    }
    return context;
  } catch (e) {
    logError(`Error while instantiating browser handle for extension: ${EXTENSION_ID}: ${e.message}.\n`, e);
  }
}

/**
 * Executes the crawling process for the specified extension and URLs.
 */
async function executeCrawl() {
  let context;
  let retrial = 0;
  try {
    while (true) {
      try {
        context = await getBrowserHandle();
        if (!context) throw Error(`Context could not be created successfully for extension: ${EXTENSION_ID}`)
        await context?.close();
        context = null;
        context = await getBrowserHandle();
        if (!context) throw Error(`Context could not be created successfully for second time for extension: ${EXTENSION_ID}`)
        if (URL.includes("testserver.com")) {
          await browse(context, `${URL}&extensionId=${EXTENSION_ID}&visit=${VISIT}`);
        }
        else {
          await browse(context, URL);
        }
        await context?.close();
        break;
      } catch (e) {
        if (context) await context?.close();
        if (retrial < config.MAX_RETRIES) {
          retrial += 1;
          continue;
        } else {
          logError(`Error: Couldn't succesfully visit for extension: ${EXTENSION_ID} - ${e.message}.`, e);
        };
      }
      break;
    }
    if (existsSync(`${config.USER_DATA_DIR}${EXTENSION_ID}_${UID}`)) {
      rmSync(`${config.USER_DATA_DIR}${EXTENSION_ID}_${UID}`, {
        recursive: true,
        force: true
      });
    }
  } catch (e) {
    if (existsSync(`${config.USER_DATA_DIR}${EXTENSION_ID}_${UID}`)) {
      rmSync(`${config.USER_DATA_DIR}${EXTENSION_ID}_${UID}`, {
        recursive: true,
        force: true
      });
    }
    logError(`Error while executing crawl for extension: ${EXTENSION_ID} - ${e.message}\n`, e);
  }
}

/**
 * Parses command-line arguments and sets global variables.
 */
async function parseArguments() {
  if (process.argv.length !== 1) {
    let extension = JSON.parse(process.argv[2]);
    if (extension === undefined || Object.keys(extension).length < 4) {
      logError("Invalid arguments passed, could not be parsed!");
      process.exit(1);
    }
    EXTENSION_ID = extension.id;
    VISIT = extension.visit;
    URL = extension.url;
    UID = extension.uid;
  } else {
    logError("Invalid arguments passed!");
    process.exit(1);
  }
}

/**
 * Initializes the crawling process by parsing arguments and executing the crawl.
 */
async function init() {
  if (config.DEBUG) {
    EXTENSION_ID = "jmohbogdcndleclcgnmjnfmghegbdfma";
    URL = "http://testserver.com:9000/shared/?template=hook.html";
    VISIT = "1";
    UID = "testrandom";
  } else {
    await parseArguments();
  }
  await executeCrawl();
  if (existsSync(`${config.USER_DATA_DIR}${EXTENSION_ID}_${UID}`)) {
    rmSync(`${config.USER_DATA_DIR}${EXTENSION_ID}_${UID}`, {
      recursive: true,
      force: true
    });
  }
  process.exit(0);
}

process.on('unhandledRejection', (e, p) => {
  void(0);
});

process.setMaxListeners(0);

init();