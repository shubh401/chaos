"""
dom_query_extractor.py — Extracts DOM query patterns from extension content scripts.

Runs the Node.js AST parser on each extension's content scripts to identify
DOM query targets (selectors, IDs, attribute names) that can be clobbered.
Results are stored in the extension_dom_queries DB table.

Usage:
    cd static/src && python dom_query_extractor.py
"""
from manifest import get_manifest, get_content_scripts
from files import list_of_files
from collections import defaultdict
from tqdm import tqdm
from config import *

import multiprocessing as mp
import subprocess
import traceback
import psycopg2
import json
import os

WORKERS = 30
DOM_QUERY_EXTRACTOR = "./static/src/helpers/dom_query_extractor.js"


def extract_queries(script_path: str, extension_id: str) -> dict:
    """Run the Node.js DOM query extractor on a single script file."""
    result = {"queries": [], "document_access": [], "property_sinks": [], "bundler_gadgets": []}
    try:
        proc = subprocess.Popen(
            ["node", DOM_QUERY_EXTRACTOR, script_path],
            stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )
        proc.wait(600)
        stdout = proc.stdout.read().decode().strip()
        if stdout:
            result = json.loads(stdout)
    except subprocess.TimeoutExpired:
        pass
    except:
        traceback.print_exc()
    return result


def get_content_script_paths(extension_id: str) -> list:
    """Get absolute paths of content scripts for an extension."""
    paths = []
    try:
        extension_dir = f"{ISOLATED_NAMESPACE_DIR}{extension_id}/"
        if not os.path.exists(extension_dir):
            extension_dir = f"{UNZIPPED_DIR}{extension_id}/"
        if not os.path.exists(extension_dir):
            return paths

        manifest = get_manifest(os.path.join(extension_dir, "manifest.json"), extension_id)
        if not manifest:
            return paths

        file_list = list_of_files(extension_dir, extension_id)
        if not file_list:
            return paths

        scripts = get_content_scripts(manifest, file_list, "content_scripts", "js", extension_id, extension_dir)
        if scripts:
            for script_name in scripts.keys():
                if script_name == "__cs_hook.js":
                    continue
                full_path = os.path.join(extension_dir, script_name)
                if os.path.exists(full_path):
                    paths.append(full_path)
    except:
        traceback.print_exc()
    return paths


def process_extension(extension_id: str) -> tuple:
    """Process a single extension: extract DOM queries from all its content scripts."""
    merged = {"queries": [], "document_access": [], "property_sinks": [], "bundler_gadgets": []}
    try:
        script_paths = get_content_script_paths(extension_id)
        for path in script_paths:
            result = extract_queries(path, extension_id)
            for key in merged:
                merged[key].extend(result.get(key, []))

        # Deduplicate
        seen_queries = set()
        unique_queries = []
        for q in merged["queries"]:
            key = f"{q['method']}:{q['argument']}"
            if key not in seen_queries:
                seen_queries.add(key)
                unique_queries.append(q)
        merged["queries"] = unique_queries

        seen_doc = set()
        unique_doc = []
        for d in merged["document_access"]:
            if d["property"] not in seen_doc:
                seen_doc.add(d["property"])
                unique_doc.append(d)
        merged["document_access"] = unique_doc

    except:
        traceback.print_exc()
    return merged, extension_id


def create_table():
    """Create the extension_dom_queries table if it doesn't exist."""
    try:
        connection = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extension_dom_queries (
                id SERIAL PRIMARY KEY,
                extension_id VARCHAR(256),
                dataset VARCHAR(32) NOT NULL,
                queries JSONB,
                document_access JSONB,
                property_sinks JSONB,
                bundler_gadgets JSONB,
                tstamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS edq_ext ON extension_dom_queries(extension_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS edq_ext_dat ON extension_dom_queries(extension_id, dataset);")
        connection.commit()
        connection.close()
    except:
        traceback.print_exc()


def insert_results(extension_id: str, data: dict):
    """Insert extraction results into the DB."""
    try:
        if not any(data.get(k) for k in ["queries", "document_access", "property_sinks", "bundler_gadgets"]):
            return
        connection = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO extension_dom_queries (extension_id, dataset, queries, document_access, property_sinks, bundler_gadgets)
            VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;
        """, (
            extension_id, DATASET,
            json.dumps(data.get("queries", [])),
            json.dumps(data.get("document_access", [])),
            json.dumps(data.get("property_sinks", [])),
            json.dumps(data.get("bundler_gadgets", [])),
        ))
        connection.commit()
        connection.close()
    except:
        traceback.print_exc()


def main():
    try:
        create_table()

        # Get list of extensions from the isolated namespace directory
        extension_dir = ISOLATED_NAMESPACE_DIR
        if not os.path.exists(extension_dir):
            extension_dir = UNZIPPED_DIR
        extensions = os.listdir(extension_dir)
        extensions = [e for e in extensions if os.path.isdir(os.path.join(extension_dir, e))]

        print(f"Processing {len(extensions)} extensions from {extension_dir}...")

        with_queries = 0
        with mp.Pool(processes=WORKERS, maxtasksperchild=1) as pool:
            for data, ext_id in tqdm(pool.imap_unordered(process_extension, extensions), total=len(extensions)):
                if any(data.get(k) for k in ["queries", "document_access", "property_sinks", "bundler_gadgets"]):
                    insert_results(ext_id, data)
                    with_queries += 1

        print(f"\nDone. {with_queries}/{len(extensions)} extensions have DOM query patterns.")
    except:
        traceback.print_exc()


if __name__ == "__main__":
    main()
