from config import *

import psycopg2

def create_test_tables() -> bool:
    """
    Creates the necessary test tables in the database if they do not already exist.
    
    Returns:
        bool: True if the tables were created successfully, False otherwise.
    """
    try:
        connection = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cursor = connection.cursor()
        cursor.execute("START TRANSACTION;")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {TEST_TYPE}_storage_log_{TABLE_SUFFIX} (id SERIAL PRIMARY KEY, extension_id VARCHAR(256), storage TEXT, type VARCHAR(32), data JSONB, dataset VARCHAR(32) NOT NULL, visit SMALLINT, stage VARCHAR(16), url VARCHAR(1024), context_url VARCHAR(1024), client_ts DOUBLE PRECISION, lifecycle_stage VARCHAR(32), tstamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {TEST_TYPE}_cookies_log_{TABLE_SUFFIX} (id SERIAL PRIMARY KEY, extension_id VARCHAR(256), type VARCHAR(32), data JSONB, dataset VARCHAR(32) NOT NULL, visit SMALLINT, stage VARCHAR(16), url VARCHAR(1024), context_url VARCHAR(1024), client_ts DOUBLE PRECISION, lifecycle_stage VARCHAR(32), tstamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {TEST_TYPE}_idb_log_{TABLE_SUFFIX} (id SERIAL PRIMARY KEY, extension_id VARCHAR(256), property VARCHAR(32), arguments JSONB, results JSONB, dataset VARCHAR(32) NOT NULL, visit SMALLINT, stage VARCHAR(16), url VARCHAR(1024), context_url VARCHAR(1024), client_ts DOUBLE PRECISION, lifecycle_stage VARCHAR(32), tstamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {TEST_TYPE}_message_log_{TABLE_SUFFIX} (id SERIAL PRIMARY KEY, extension_id VARCHAR(256), message TEXT, data JSONB, dataset VARCHAR(32) NOT NULL, visit SMALLINT, stage VARCHAR(16), url VARCHAR(1024), context_url VARCHAR(1024), client_ts DOUBLE PRECISION, lifecycle_stage VARCHAR(32), tstamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {TEST_TYPE}_variable_log_{TABLE_SUFFIX} (id SERIAL PRIMARY KEY, extension_id VARCHAR(256), variables TEXT, dataset VARCHAR(32) NOT NULL, visit SMALLINT, stage VARCHAR(32), url VARCHAR(1024), context_url VARCHAR(1024), client_ts DOUBLE PRECISION, lifecycle_stage VARCHAR(32), tstamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {TEST_TYPE}_mutation_log_{TABLE_SUFFIX} (id SERIAL PRIMARY KEY, api VARCHAR(64), extension_id VARCHAR(256), url VARCHAR(1024), context_url VARCHAR(1024), added_nodes JSONB, removed_nodes JSONB, target TEXT NOT NULL, type TEXT NOT NULL, attribute_name TEXT, attribute_namespace TEXT, old_value TEXT, next_sibling TEXT, previous_sibling TEXT, data_digest VARCHAR(32) NOT NULL, dataset VARCHAR(32) NOT NULL, visit SMALLINT, client_ts DOUBLE PRECISION, lifecycle_stage VARCHAR(32), tstamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {TEST_TYPE}_hook_log_{TABLE_SUFFIX} (id SERIAL PRIMARY KEY, extension_id VARCHAR(256), url VARCHAR(1024), context_url VARCHAR(1024), api VARCHAR(256), arguments TEXT, data TEXT, caller TEXT, caller_name TEXT, caller_data TEXT, stacktrace TEXT, stack_trace_md5 varchar(256), arguments_md5 varchar(256), arguments_data_md5 varchar(256), caller_data_md5 varchar(256), dataset VARCHAR(32) NOT NULL, visit SMALLINT, client_ts DOUBLE PRECISION, lifecycle_stage VARCHAR(32), tstamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {TEST_TYPE}_errors_{TABLE_SUFFIX} (id SERIAL PRIMARY KEY, extension_id VARCHAR(256), url VARCHAR(1024), context_url VARCHAR(1024), dataset VARCHAR(32) NOT NULL, error TEXT, error_type VARCHAR(1024), source VARCHAR(256), visit SMALLINT DEFAULT 0, client_ts DOUBLE PRECISION, lifecycle_stage VARCHAR(32), tstamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);")
        # cursor.execute(f"CREATE TABLE IF NOT EXISTS {TEST_TYPE}_extension_counter_{TABLE_SUFFIX} (id SERIAL PRIMARY KEY, extension_id VARCHAR(256), dataset VARCHAR(32) NOT NULL, other_extensions JSONB, visit SMALLINT DEFAULT 0, tstamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {TEST_TYPE}_coverage_log_{TABLE_SUFFIX} (id SERIAL PRIMARY KEY, extension_id VARCHAR(256), url VARCHAR(1024), coverage JSONB, dataset VARCHAR(32) NOT NULL, visit SMALLINT DEFAULT 0, tstamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);")
        # cursor.execute(f"CREATE TABLE IF NOT EXISTS {TEST_TYPE}_state_log_{TABLE_SUFFIX} (id SERIAL PRIMARY KEY, extension_id VARCHAR(256), url VARCHAR(1024), context_url VARCHAR(1024), dataset VARCHAR(32) NOT NULL, api VARCHAR(512), state VARCHAR(128), visit SMALLINT DEFAULT 0, tstamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {TEST_TYPE}_proxy_log_{TABLE_SUFFIX} (id SERIAL PRIMARY KEY, extension_id VARCHAR(256), url VARCHAR(1024), context_url VARCHAR(1024), dataset VARCHAR(32) NOT NULL, type VARCHAR(512), proxy_data JSONB, visit SMALLINT DEFAULT 0, tstamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {TEST_TYPE}_csp_log_{TABLE_SUFFIX} (id SERIAL PRIMARY KEY, extension_id VARCHAR(256), url VARCHAR(1024), context_url VARCHAR(1024), csp_report JSONB, dataset VARCHAR(32) NOT NULL, visit SMALLINT DEFAULT 0, tstamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);")
        
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {TEST_TYPE}_test_extensions (id SERIAL PRIMARY KEY, extension_id VARCHAR(256), test_urls JSONB, test_status SMALLINT DEFAULT 0, retried SMALLINT DEFAULT 0, dataset VARCHAR(32) NOT NULL, visit SMALLINT DEFAULT 0, tstamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);")
            
        if TEST_TYPE == 'isolated':
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {TEST_TYPE}_clobber_hook_log_{TABLE_SUFFIX} (id SERIAL PRIMARY KEY, extension_id VARCHAR(256), url VARCHAR(1024), context_url VARCHAR(1024), api VARCHAR(256), arguments TEXT, data TEXT, proxy_data TEXT, caller TEXT, caller_name TEXT, caller_data TEXT, stacktrace TEXT, stack_trace_md5 varchar(256), arguments_md5 varchar(256), arguments_data_md5 varchar(256), caller_data_md5 varchar(256), dataset VARCHAR(32) NOT NULL, visit SMALLINT, tstamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);")
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {TEST_TYPE}_cs_trace_log_{TABLE_SUFFIX} (id SERIAL PRIMARY KEY, extension_id VARCHAR(256), traces JSONB, dataset VARCHAR(32) NOT NULL, visit SMALLINT, url VARCHAR(1024), context_url VARCHAR(1024), tstamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);")

        cursor.execute(f"CREATE INDEX IF NOT EXISTS {TEST_TYPE}_proto_store_dat_idx_{TABLE_SUFFIX} ON {TEST_TYPE}_hook_log_{TABLE_SUFFIX}(dataset);")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {TEST_TYPE}_proto_store_dat_vis_ext_idx_{TABLE_SUFFIX} ON {TEST_TYPE}_hook_log_{TABLE_SUFFIX}(dataset, visit, extension_id);")
        if TEST_TYPE == 'isolated':
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {TEST_TYPE}_clob_store_dat_idx_{TABLE_SUFFIX} ON {TEST_TYPE}_clobber_hook_log_{TABLE_SUFFIX}(dataset);")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {TEST_TYPE}_clob_store_dat_vis_ext_idx_{TABLE_SUFFIX} ON {TEST_TYPE}_clobber_hook_log_{TABLE_SUFFIX}(dataset, visit, extension_id);")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {TEST_TYPE}_cs_trace_dat_vis_ext_idx_{TABLE_SUFFIX} ON {TEST_TYPE}_cs_trace_log_{TABLE_SUFFIX}(dataset, extension_id, visit);")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {TEST_TYPE}_mut_store_dat_idx_{TABLE_SUFFIX} ON {TEST_TYPE}_mutation_log_{TABLE_SUFFIX}(dataset);")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {TEST_TYPE}_mut_store_dat_vis_ext_idx_{TABLE_SUFFIX} ON {TEST_TYPE}_mutation_log_{TABLE_SUFFIX}(dataset, visit, extension_id);")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {TEST_TYPE}_test_ext_fetch ON {TEST_TYPE}_test_extensions(dataset, test_status);")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {TEST_TYPE}_test_ext_update ON {TEST_TYPE}_test_extensions(dataset, extension_id);")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {TEST_TYPE}_test_ext_reset ON {TEST_TYPE}_test_extensions(dataset);")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {TEST_TYPE}_err_idx ON {TEST_TYPE}_errors_{TABLE_SUFFIX}(dataset, extension_id);")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {TEST_TYPE}_err_vis_idx ON {TEST_TYPE}_errors_{TABLE_SUFFIX}(dataset, extension_id, visit);")
        # cursor.execute(f"CREATE INDEX IF NOT EXISTS {TEST_TYPE}_state_idx ON {TEST_TYPE}_state_log_{TABLE_SUFFIX}(dataset, extension_id, visit);")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {TEST_TYPE}_proxy_idx ON {TEST_TYPE}_proxy_log_{TABLE_SUFFIX}(dataset, extension_id, visit);")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {TEST_TYPE}_coverage_idx ON {TEST_TYPE}_coverage_log_{TABLE_SUFFIX}(dataset, extension_id, visit);")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {TEST_TYPE}_csp_idx ON {TEST_TYPE}_csp_log_{TABLE_SUFFIX}(dataset, extension_id);")
        cursor.execute(f"DELETE FROM {TEST_TYPE}_test_extensions WHERE dataset = '{DATASET}';")
        cursor.execute("COMMIT;")
        connection.close()
        return True
    except:
        logging.error(f"[EXTENSION MANAGER] Error while seting-up the DB for {TEST_TYPE} test crawl (create_{TEST_TYPE}_test_tables()): %s" % "; ".join(str(traceback.format_exc()).split("\n")))
    return False

def update_extension(extension_id: str, status: str) -> None:
    """
    Updates the status of a specific extension in the database.
    
    Args:
        extension_id (str): The ID of the extension to update.
        status (str): The new status to set for the extension.
    """
    try:
        connection = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cursor = connection.cursor()
        update_query = f""" UPDATE {TEST_TYPE}_test_extensions SET "test_status" = {status} WHERE dataset = '{DATASET}' AND "extension_id" = '{extension_id}'; """
        cursor.execute(""" START TRANSACTION; """)
        cursor.execute(update_query)
        cursor.execute("COMMIT;")
        connection.close()
    except:
        logging.error("[EXTENSION MANAGER] Error while updating extension status in DB (update_extension()): %s" % "; ".join(str(traceback.format_exc()).split("\n")))

def get_new_extension() -> list:
    """
    Retrieves a new extension from the database that has not been tested yet.
    
    Returns:
        list: A list containing the extension ID, test URLs, and retry count.
    """
    result = []
    try:
        connection = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cursor = connection.cursor()
        query = f""" SELECT "extension_id", "test_urls" FROM {TEST_TYPE}_test_extensions WHERE dataset = '{DATASET}' AND "test_status" = 0 ORDER BY "id" LIMIT 1 FOR UPDATE; """
        cursor.execute(""" START TRANSACTION; """)
        cursor.execute(query)
        result = cursor.fetchone()
        if result is not None and len(result):
            update_query = f""" UPDATE {TEST_TYPE}_test_extensions SET "test_status" = 1 WHERE dataset = '{DATASET}' AND "extension_id" = '{result[0]}'; """
            cursor.execute(update_query)
        cursor.execute("COMMIT;")
        connection.commit()
        connection.close()
    except:
        logging.error("[EXTENSION MANAGER] Error while getting new extension from DB (get_new_extension()): %s" % "; ".join(str(traceback.format_exc()).split("\n")))     
    return result
   
def update_visit_id(curr_id) -> None:
    """
    Updates the visit ID for various logs in the database.
    
    Args:
        curr_id (int): The current visit ID to set.
    """
    try:
        connection = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cursor = connection.cursor()
        for data_type in ("storage", "cookies", "message", "idb"):
            update_query = f""" UPDATE {TEST_TYPE}_{data_type}_log_{TABLE_SUFFIX} SET visit = {curr_id} WHERE dataset = '{DATASET}' AND (visit = -1 OR visit = 0); """
            cursor.execute(update_query)
        connection.commit()
        connection.close()
    except:
        logging.error("[EXTENSION MANAGER] Error while updating extensions visit id in DB (update_visit_id()): %s" % "; ".join(str(traceback.format_exc()).split("\n")))

def update_extensions() -> None:
    """
    Resets the test status of all extensions in the database for the current dataset.
    """
    try:
        connection = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cursor = connection.cursor()
        update_query = f""" UPDATE {TEST_TYPE}_test_extensions SET test_status = 0 WHERE dataset = '{DATASET}'; """
        cursor.execute(update_query)
        connection.commit()
        connection.close()
    except:
        logging.error("[EXTENSION MANAGER] Error while updating extensions status in DB (update_extension()): %s" % "; ".join(str(traceback.format_exc()).split("\n")))

def insert_extensions() -> bool:
    """
    Inserts new extensions into the database for testing.
    
    Returns:
        bool: True if the extensions were inserted successfully, False otherwise.
    """
    params = []
    try:
        for extension_id in EXTENSIONS:
            params.append((extension_id, json.dumps(TEST_URLS), DATASET))
        connection = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cursor = connection.cursor()
        insert_query = f""" INSERT INTO {TEST_TYPE}_test_extensions (extension_id, test_urls, dataset) VALUES(%s,%s,%s); """
        cursor.executemany(insert_query, tuple(params))
        connection.commit()
        connection.close()
        return True
    except:
        logging.error("[EXTENSION MANAGER] Error while inserting extensions status in DB (update_extension()): %s" % "; ".join(str(traceback.format_exc()).split("\n")))
    return False

def insert_multi_test_extensions(map_data) -> bool:
    """
    Inserts new multi-test extensions into the database for testing.
    
    Args:
        map_data (dict): A dictionary mapping extension IDs to other extensions.
    
    Returns:
        bool: True if the extensions were inserted successfully, False otherwise.
    """
    params = []
    try:
        for extension_id, others in map_data.items():
            params.append((extension_id, json.dumps(others), json.dumps(TEST_URLS), DATASET))
        connection = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cursor = connection.cursor()
        insert_query = f""" INSERT INTO {TEST_TYPE}_test_extensions (extension_id, others, test_urls, dataset) VALUES(%s,%s,%s,%s); """
        cursor.executemany(insert_query, tuple(params))
        connection.commit()
        connection.close()
        return True
    except:
        logging.error("[EXTENSION MANAGER] Error while inserting multi test extensions status in DB (update_extension()): %s" % "; ".join(str(traceback.format_exc()).split("\n")))
    return False
