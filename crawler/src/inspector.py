from dotenv import load_dotenv
from proc import *

import traceback
import psutil
import time
import proc
import os

if os.path.exists("~/chaos/.env"):
    load_dotenv(dotenv_path="~/chaos/.env")
TEST_TYPE = os.getenv("TEST_TYPE")

def terminate_crawler() -> None:
    """
    Terminates all crawler processes.
    """
    try:
        for process in psutil.process_iter():
            cmdline = ' '.join(process.cmdline())
            if "xdg" in cmdline or "firefox" in cmdline or "local-chromium" in cmdline or "ms-playwright" in cmdline:
                process.terminate()
    except:
        print("[INSPECTOR] Error in terminate_crawler(): " + '; '.join(str(traceback.format_exc()).split('\n')))

def inspect_running_processes() -> bool:
    """
    Inspects running processes and terminates or kills them based on certain conditions.
    Also checks CPU load and terminates crawler processes if the load is too high.

    Returns:
        bool: True if the inspection was successful, False otherwise.
    """
    try:
        for process in psutil.process_iter():
            try: process_info = process.as_dict(attrs=['pid', 'name', 'cpu_percent', 'cmdline'])
            except: continue
            try:
                cmdline = ' '.join(process.cmdline())
                if "xdg" in cmdline or "firefox" in cmdline or "local-chromium" in cmdline or "ms-playwright" in cmdline:
                    curr_time = proc.current_time() - process.create_time()
                    if curr_time > int(PREDEFINED_ENV_VALUES[f"{TEST_TYPE.upper()}_TEST_VIPER"]) or process.status() == psutil.STATUS_ZOMBIE:
                        print("Killing %s running for %s seconds." % (process_info['pid'], str(int(curr_time))))
                        process.kill()
                    elif (proc.current_time() - process.create_time()) > int(PREDEFINED_ENV_VALUES[f"{TEST_TYPE.upper()}_TEST_TERMINATOR"]) or process.status() == psutil.STATUS_ZOMBIE:
                        print("Gracefully terminating %s running for %s seconds." % (process_info['pid'], str(int(curr_time))))
                        process.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except:
                print("[INSPECTOR] Error in inspect_running_processes(): " + '; '.join(str(traceback.format_exc()).split('\n')))
                continue
        if not proc.check_cpu_load():
            terminate_crawler()
            print("[INSPECTOR] CPU load too high! Crawling instances terminated gracefully.\n\n")
        return True
    except:
        print("[INSPECTOR] Error in inspect_running_processes(): " + '; '.join(str(traceback.format_exc()).split('\n')))
    return False

if __name__ == "__main__":
    interval = PREDEFINED_ENV_VALUES[f"{TEST_TYPE.upper()}_TEST_INSPECTOR"]
    print(f"[INSPECTOR] Scheduling load manager now on every {str(interval)} seconds now.\n\n")
    while inspect_running_processes():
        time.sleep(interval)
