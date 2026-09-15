from typing import Iterator, Tuple

import traceback
import psutil
import time

MINUTE = 60
CRAWL_TIMEOUT = int(5 * MINUTE)
INSPECTION_INTERVAL = int(1 * MINUTE)
TERMINATOR = int(2.5 * MINUTE)
VIPER = int(3 * MINUTE)

PREDEFINED_ENV_VALUES = {
    "SHARED_TEST_INSPECTOR" : INSPECTION_INTERVAL,
    "SHARED_TEST_TERMINATOR": TERMINATOR,
    "SHARED_TEST_VIPER": VIPER,
    "ISOLATED_TEST_INSPECTOR" : INSPECTION_INTERVAL,
    "ISOLATED_TEST_TERMINATOR": TERMINATOR,
    "ISOLATED_TEST_VIPER": VIPER,
    "CPU_THRESHOLD": 90,
    "DEPTH": 0
}

def load_average() -> Tuple[float, float, float]:
    """
    Retrieves the system load average over the last 1, 5, and 15 minutes.

    Returns:
        Tuple[float, float, float]: The load averages for the last 1, 5, and 15 minutes.
    """
    return psutil.getloadavg()

def cpu_percentage() -> float:
    """
    Retrieves the current system-wide CPU utilization as a percentage.

    Returns:
        float: The current CPU utilization percentage.
    """
    return psutil.cpu_percent()

def virtual_memory() -> float:
    """
    Retrieves the percentage of used virtual memory.

    Returns:
        float: The percentage of used virtual memory.
    """
    return psutil.virtual_memory()[2]

def get_running_processes() -> Iterator[psutil.Process]:
    """
    Retrieves an iterator for all running processes.

    Returns:
        Iterator[psutil.Process]: An iterator for all running processes.
    """
    return psutil.process_iter()

def get_process(pid: int) -> psutil.Process:
    """
    Retrieves a process by its PID.

    Args:
        pid (int): The PID of the process to retrieve.

    Returns:
        psutil.Process: The process with the specified PID.
    """
    try:
        return psutil.Process(pid)
    except:
        print("[PROCESS MANAGER] Error in get_process() - " + '; '.join(str(traceback.format_exc()).split('\n')))

def process_create_time(pid: int) -> float:
    """
    Retrieves the creation time of a process.

    Args:
        pid (int): The PID of the process.

    Returns:
        float: The creation time of the process.
    """
    try:
        proc = get_process(pid)
        return proc.create_time()
    except:
        print("[PROCESS MANAGER] Error in process_create_time() - " + '; '.join(str(traceback.format_exc()).split('\n')))

def current_time() -> float:
    """
    Retrieves the current system time.

    Returns:
        float: The current system time.
    """
    return time.time()

def is_crawler_process(pid: int) -> bool:
    """
    Checks if a process is a crawler process.

    Args:
        pid (int): The PID of the process to check.

    Returns:
        bool: True if the process is a crawler process, False otherwise.
    """
    try:
        proc = get_process(pid)
        if proc.status() == 'running':
            if proc.name() == "":
                return True
    except:
        print("[PROCESS MANAGER] Error in is_crawler_process() - " + '; '.join(str(traceback.format_exc()).split('\n')))
    return False

def check_cpu_load() -> bool:
    """
    Checks if the CPU load is within acceptable limits.

    Returns:
        bool: True if the CPU load is within acceptable limits, False otherwise.
    """
    try:
        if int(cpu_percentage()) > int(PREDEFINED_ENV_VALUES["CPU_THRESHOLD"]):
            load = load_average()
            if load[1] < 192 and load[2] < 192:
                print("[CONTROLLER] CPU Load is over %s percent at the moment" % str(PREDEFINED_ENV_VALUES["CPU_THRESHOLD"]))
                return True
        else:
            return True
    except:
        print("[CONTROLLER] Error in check_cpu_load(): %s" + '; '.join(str(traceback.format_exc()).split('\n')))
    return False

def kill_process(pid: int) -> None:
    """
    Kills a process by its PID.

    Args:
        pid (int): The PID of the process to kill.
    """
    try:
        proc = get_process(pid)
        if proc.status() == 'running':
            proc.kill()
    except:
        print("[PROCESS MANAGER] Error in kill_process() - " + '; '.join(str(traceback.format_exc()).split('\n')))

def terminate_process(pid: int) -> None:
    """
    Terminates a process by its PID.

    Args:
        pid (int): The PID of the process to terminate.
    """
    try:
        proc = get_process(pid)
        if proc.status() == 'running':
            proc.terminate()
    except:
        print("[PROCESS MANAGER] Error in terminate_process() - " + '; '.join(str(traceback.format_exc()).split('\n')))
