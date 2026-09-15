from typing import Iterator, Optional, Tuple
from collections import defaultdict
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

import traceback
import argparse
import logging
import psutil
import shutil
import time
import json
import sys
import os

if os.path.exists("~/chaos/.env"):
    load_dotenv(dotenv_path="~/chaos/.env")

# Crawl Configuration constants
WORKERS = 1
VISIT_ID = 1
MAX_VISIT = 1
MULTI_TEST_COUNT = 1
DATASET = os.getenv("DATASET")
META_TEST_TYPE = os.getenv("META_TEST_TYPE")
TEST_TYPE = os.getenv("TEST_TYPE")
TABLE_SUFFIX = os.getenv("TABLE_SUFFIX")

# Test pages for different attack compoenents (shared and isolated).
CRAWL_URL_TYPE = os.getenv("CRAWL_URL_TYPE")
CRAWL_URLS = json.loads(open(Path(__file__).resolve().parents[1] / 'crawl_urls.json').read())
TEST_URLS = CRAWL_URLS.get(TEST_TYPE, {}).get(CRAWL_URL_TYPE)

# Process Monitoring
MINUTE = 60
CRAWL_TIMEOUT = int(5 * MINUTE)
INSPECTION_INTERVAL = int(1 * MINUTE)
TERMINATOR = int(2.5 * MINUTE)
VIPER = int(3 * MINUTE)
IS_MULTI_VISIT = True

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

# Database Configuration
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_NAME = os.getenv('DB_NAME')
DB_PASS = os.getenv('DB_PASS')

CONNECTION_INFO = f'hostaddr={DB_HOST} port=5432 dbname={DB_NAME} user={DB_USER} password={DB_PASS} sslmode=disable'

# Logging Configuration
LOGS = f"~/chaos/crawler/logs/{META_TEST_TYPE}/{TEST_TYPE}/{DATASET[:4]}{TABLE_SUFFIX}_{CRAWL_URL_TYPE}/"
if os.path.exists(LOGS): shutil.rmtree(LOGS)
os.makedirs(f"{LOGS}screenshots/", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    filename=f"{LOGS}{TEST_TYPE}_crawler.log",
    filemode="a+"
)

ADVANCED_TEST = bool(os.getenv("ADVANCED_TEST") == "True")
DIR_EXTENSION = os.getenv("DIR_EXTENSION")

MOUNT_PATH = "/mnt/extensions/"
USER_DATA_DIR = os.getenv("USER_DATA_DIR", "/tmp/chaos/chromiumDataDir/")
os.makedirs(USER_DATA_DIR, exist_ok=True)

TMPFS_COMMAND = ["mount", "-t", "tmpfs", "-o", "size=10g", "tmpfs", USER_DATA_DIR]
UNMOUNT_COMMAND = ["umount", f"{USER_DATA_DIR}"]

EXTENSIONS = os.listdir(f"{MOUNT_PATH}{DIR_EXTENSION}/{DATASET}/")
