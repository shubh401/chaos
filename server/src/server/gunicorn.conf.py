from config import DATASET, META_TEST_TYPE, TEST_TYPE, TABLE_SUFFIX, CRAWL_URL_TYPE

bind = '0.0.0.0:9000'
workers = 10
worker_class = 'gthread'
preload = True
reload = True
daemon = False
threads = 2
timeout = 120
keepalive = 75
pidfile = f'/var/logs/{META_TEST_TYPE}/{TEST_TYPE}/{DATASET[:4]}{TABLE_SUFFIX}_{CRAWL_URL_TYPE}/gunicorn_server.pid'
errorlog  = f'/var/logs/{META_TEST_TYPE}/{TEST_TYPE}/{DATASET[:4]}{TABLE_SUFFIX}_{CRAWL_URL_TYPE}/gunicorn.log'
loglevel = 'info'
capture_output = True
proc_name = 'gunicorn_server'
max_requests = 0
wsgi_app = "server.wsgi"
