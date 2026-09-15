from collections import defaultdict
from dotenv import load_dotenv

import traceback
import logging
import json
import os

if os.path.exists("~/chaos/.env"):
    load_dotenv(dotenv_path="~/chaos/.env")

TEST_TYPE = os.getenv("TEST_TYPE")
META_TEST_TYPE = os.getenv("META_TEST_TYPE")
TEST_BREAKAGE = bool(os.getenv("TEST_BREAKAGE") == "True")
DATASET = os.getenv("DATASET")
EXTENSION_TYPE = os.getenv("EXTENSION_TYPE")
TABLE_SUFFIX = os.getenv("TABLE_SUFFIX")
CRAWL_URL_TYPE = os.getenv("CRAWL_URL_TYPE")

# Database Configuration
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_NAME = os.getenv('DB_NAME')
DB_PASS = os.getenv('DB_PASS')

LOGS = f"/var/logs/{META_TEST_TYPE}/{TEST_TYPE}/{DATASET[:4]}{TABLE_SUFFIX}_{CRAWL_URL_TYPE}"
os.makedirs(LOGS, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    filename=f"{LOGS}/{TEST_TYPE}.log",
    filemode="a+"
)
logging.getLogger("urllib3").setLevel(logging.ERROR)

CONNECTION_INFO = f'hostaddr={DB_HOST} port=5432 dbname={DB_NAME} user={DB_USER} password={DB_PASS} sslmode=disable'

TEST_URL = "testserver.com"
