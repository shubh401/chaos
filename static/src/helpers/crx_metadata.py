from collections import defaultdict
from bs4 import BeautifulSoup
from tqdm import tqdm

import multiprocessing as mp
import traceback
import requests
import logging
import urllib3
import time
import json
import os

WORKERS = 100
DATE = "2025-11-13"
DATASET = f"crx_{DATE}"
LOGS = f"./static/logs/{DATASET}/"
# Specify path to file list of extensions
EXTENSIONS = []
for ext in os.listdir(f"/datasets/{DATASET}/"):
    EXTENSIONS.append(ext[:-4])

SESSION = requests.Session()
SESSION.headers.update(
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    }
)
CWS_URL_TEMPLATE = "https://chromewebstore.google.com/detail/sui-wallet/"

os.makedirs(LOGS, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    filename=f"{LOGS}metadata_extractor.log",
    filemode="a+"
)
logging.getLogger("urllib3").setLevel(logging.INFO)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    return data

def extract_data(extension_id: str):
    """
    Extracts metadata for the given extension from the Chrome Web Store.

    Args:
        extension_id (str): The ID of the extension to extract metadata for.

    Returns:
        Tuple: A tuple containing the number of users, rating, parent category, category, and email.
    """
    users, rating, parent_category, category, email = None, None, "", "", None
    try:
        response = SESSION.get(CWS_URL_TEMPLATE + extension_id)
        if not response: return users, rating, category, email
        soup = BeautifulSoup(response.content, 'html.parser')
        if soup.find('span', {'class' :'Vq0ZA'}) is not None:
            rating = soup.find('span', {'class' :'Vq0ZA'}).text
        if soup.find('div', {'class' :'AxYQf'}) is not None:
            email = soup.find('div', {'class' :'AxYQf'}).text
        if soup.find('a', {'class' :'gqpEIe FjUAcd'}) is not None:
            parent_category = soup.find('a', {'class' :'gqpEIe FjUAcd'}).text
        if soup.find('a', {'class' :'gqpEIe bgp7Ye'}) is not None:
            category = soup.find('a', {'class' :'gqpEIe bgp7Ye'}).text
        if soup.find('div', {'class' :'F9iKBc'}):
            if parent_category + category != "": 
                try:
                    users = soup.find('div', {'class' :'F9iKBc'}).text.split(parent_category + category)[1].split()[0]
                except:
                    users = '0'
            else:
                try:
                    users = soup.find('div', {'class' :'F9iKBc'}).text.split()[0]
                except:
                    users = '0'
    except:
        logging.error(f"[CRX METADATA] Error in extract_data() for extension - {extension_id}: %s" % "; ".join(str(traceback.format_exc()).split("\n")))
    return users, rating, parent_category, category, email

def start(extension_id: str):
    """
    Starts the metadata extraction process for the given extension.

    Args:
        extension_id (str): The ID of the extension to extract metadata for.

    Returns:
        Tuple: A tuple containing the extension ID, number of users, rating, parent category, category, and email.
    """
    user, rating, parent_category, category, email = None, None, None, None, None
    try:
        user, rating, parent_category, category, email = extract_data(extension_id)
    except:
        logging.error(f"[CRX METADATA] Error in start() for extension - {extension_id}: %s" % "; ".join(str(traceback.format_exc()).split("\n")))
    return (extension_id, user, rating, parent_category, category, email)

def main():
    """
    Main function to extract metadata for all extensions and save it to a JSON file.
    """
    extension_metadata = defaultdict(lambda: defaultdict())
    try:
        if not EXTENSIONS: return
        elif os.path.exists(f"crx_metadata.json"): return

        with mp.Pool(processes=WORKERS) as pool:
            for (extension_id, user, rating, parent_category, category, email) in tqdm(pool.imap_unordered(start, EXTENSIONS), total=len(EXTENSIONS)):
                extension_metadata[extension_id]["user"] = user
                extension_metadata[extension_id]["rating"] = rating
                extension_metadata[extension_id]["parent_category"] = parent_category
                extension_metadata[extension_id]["category"] = category
                extension_metadata[extension_id]["email"] = email

        if extension_metadata:
            with open(f"{LOGS}crx_metadata.json", "w") as fh:
                json.dump(extension_metadata, fh, indent=4, default=serialize_object)
    except:
        logging.error(f"[CRX METADATA] Error in main(): %s" % "; ".join(str(traceback.format_exc()).split("\n")))

if __name__ == '__main__':
    main()