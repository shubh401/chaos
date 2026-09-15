from config import *
from db import *

import multiprocessing as mp
import subprocess
import random
import string
import shutil
import proc

def terminate() -> None:
    """
    Terminates all crawler processes.
    """
    try:
        process_list = proc.get_running_processes()
        for process in process_list:
            cmdline = ' '.join(process.cmdline())
            if "xdg" in cmdline or "firefox" in cmdline or "local-chromium" in cmdline or "ms-playwright" in cmdline:
                process.terminate()
    except:
        logging.error("[CRAWLER] Error in terminate(): " + '; '.join(str(traceback.format_exc()).split('\n')))

def clean_tmp() -> None:
    """
    Cleans up temporary files and directories.
    """
    try:
        if os.path.exists("~/chaos/cleanup_tmp.sh"):
            subprocess.run(["bash", "~/chaos/cleanup_tmp.sh"])
        subprocess.run(["pkill", "Xvfb"])
        subprocess.run(["rm", "-rf", USER_DATA_DIR])
        subprocess.run(["rm", "-rf", "/tmp/playwright-*"])
        subprocess.run(["rm", "-rf", "/tmp/xvfb_*"])
        subprocess.run(["rm", "-rf", "/tmp/.X*-lock"])
        subprocess.run(["rm", "-rf", "/tmp/.tX*"])
        subprocess.run(["rm", "-rf", f"{USER_DATA_DIR}xvfb-err.log"])
        subprocess.run(["rm", "-rf", f"{USER_DATA_DIR}xvfb.auth"])
        subprocess.run(["rm", "-rf", "/tmp/.org.chromium.*"])
    except:
        logging.error("[CRAWLER] Error in clean_tmp(): " + '; '.join(str(traceback.format_exc()).split('\n')))

def setup_ramdisk_space() -> None:
    """
    Sets up the RAM disk space.
    """
    try:
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        process = subprocess.Popen(TMPFS_COMMAND, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc_error = process.stderr.read().decode().strip()
        process.wait()
        if proc_error:
            logging.error("Error while mounting ramdisk: " + '; '.join(proc_error.split("\n")))
            sys.exit(1)
        logging.info("[CRAWLER] RAM disk space setup successfully!\n")
    except:
        logging.error("[CRAWLER] Error in setup_ramdisk_space(): " + '; '.join(str(traceback.format_exc()).split('\n')))
        sys.exit(1)

def remove_ramdisk_space() -> None:
    """
    Removes the RAM disk space.
    """
    try:
        process = subprocess.Popen(UNMOUNT_COMMAND, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc_error = process.stderr.read().decode().strip()
        if proc_error:
            logging.error("Error while unmounting ramdisk: " + '; '.join(proc_error.split("\n")))
            sys.exit(1)
        logging.info("[CRAWLER] RAM disk space removed successfully!\n")
    except:
        logging.error("[CRAWLER] Error in remove_ramdisk_space(): " + '; '.join(str(traceback.format_exc()).split('\n')))

def setup() -> bool:
    """
    Sets up the database for the crawl.

    Returns:
        bool: True if the setup was successful, False otherwise.
    """
    try:
        if create_test_tables() and insert_extensions():
            logging.info("[CONTROLLER] Database setup successfully for the crawl!\n")
            return True
        logging.error("[CONTROLLER] Couldn't successfully store the extensions for analysis (setup())")
    except:
        logging.error("[CONTROLLER] Error in setup(): " + '; '.join(str(traceback.format_exc()).split('\n')))
    return False

def crawl(extension_id: str, visit: int, idx: int, url: str) -> int:
    """
    Executes the crawling process for a single extension.

    Args:
        extension_id (str): The ID of the extension to crawl.
        idx (int): The index of the worker.
        url (str): The URL to crawl.

    Returns:
        int: The result of the crawl.
    """
    process = None
    try:
        random_string = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=10))
        process = subprocess.Popen(["xvfb-run", "-a", "-f", f"{USER_DATA_DIR}xvfb.auth", "-e", f"{USER_DATA_DIR}xvfb-err.log", "-s", "-screen 0 1920x1080x24", "node", f"{DATASET[0:3]}_runner.js", json.dumps({"id": extension_id, "port": idx, "url": url, "visit": visit, "uid": random_string})], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=Path(__file__).parent / 'runner')
        process.wait(CRAWL_TIMEOUT)
        err, output = process.stderr.read().decode().strip(), process.stdout.read().decode().strip()
        if err != "" or "ERROR" in output[:100]:
            logging.error("[CONTROLLER] Error at runtime: (start_crawl())): %s - %s - %s" % (str(idx+1), output, err))
            return -1
    except subprocess.TimeoutExpired:
        if process: process.kill()
        logging.error("[CONTROLLER] Timeout error while crawling for %s.\n" % (extension_id))
        return -1
    except:
        if process: process.kill()
        logging.error("[CONTROLLER] Unhandled exception while crawling for %s - %s" % (extension_id, "; ".join(traceback.format_exc().split('\n'))))
        return -1
    return 2

def start_crawl(idx: int) -> None:
    """
    Starts the crawling process for a single extension.

    Args:
        idx (int): The index of the worker.
    """
    try:
        while True:
            time.sleep(0.5)
            extension_data = get_new_extension()
            if extension_data is None:
                logging.warning("[CONTROLLER] No new extension_id retrieved from DB. Worker %s suspended.\n" % str(idx+1))
                break
            result = defaultdict(int)
            for url in extension_data[1]:
                visit_counter = 0
                while visit_counter < MAX_VISIT:
                    res = crawl(extension_data[0], visit_counter+1, idx, url)
                    result[res] += 1
                    visit_counter += 1
            if result.get(2) and result.get(2) > len(extension_data[1])//2:
                update_extension(extension_data[0], 2)
            else: update_extension(extension_data[0], -1)
    except:
        logging.error("[CONTROLLER] Error while creating crawling instance for - %s" % "; ".join(traceback.format_exc().split('\n')))

def init_crawler() -> None:
    """
    Initializes the crawler with the specified number of workers.

    Args:
        workers (int): The number of workers to initialize.
    """
    try:
        pool = mp.Pool(processes=WORKERS)
        pool.map(start_crawl, range(0, WORKERS))
    except:
        logging.error("[CONTROLLER] Error in init(): " + '; '.join(str(traceback.format_exc()).split('\n')))
 
def init_server() -> None:
    """
    Initializes the crawling server.
    """
    try:
        process = subprocess.Popen(["docker-compose", "--env-file", f"~/chaos/.env", "up", "--build", "-d"], cwd=f"~/chaos/server")
        process.wait(timeout=600)
        if process.returncode != 0:
            logging.error("[CONTROLLER] Error while starting crawling server: " + process.stderr.read().decode().strip())
            sys.exit(1)
        logging.info("[CONTROLLER] Crawling server started successfully!\n")
    except:
        logging.error("Error while starting crawling server: " + '; '.join(str(traceback.format_exc()).split('\n')))
        sys.exit(1)

if __name__ == '__main__':
    try:
        if not proc.check_cpu_load():
            sys.exit(0)
        
        if not setup(): sys.exit(1)
        setup_ramdisk_space()
        init_server()
        init_crawler()
        terminate()
        clean_tmp()
    except KeyboardInterrupt: logging.warning("Crawl interrupted!")
    except: logging.error("Error in init: " + '; '.join(str(traceback.format_exc()).split('\n')))
    finally:
        subprocess.run(["docker-compose", "down"], cwd='./server')
        subprocess.run(["pkill", "gunicorn"])
        subprocess.run(["pkill", "Xvfb"])
        clean_tmp()
        sys.exit(0)
