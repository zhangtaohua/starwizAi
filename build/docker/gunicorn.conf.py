import multiprocessing

bind = "0.0.0.0:5177"
backlog = 4096
timeout = 120

workers = multiprocessing.cpu_count() * 2 + 1
threads = multiprocessing.cpu_count() * 2

daemon = False

# To ensure that gunicorn won't run as a daemon
raw_env = ["PYTHONUNBUFFERED=1"]

# Logging
# accesslog = "-"
# errorlog = "-"
loglevel = "info"

accesslog = "/app/running/storage/logs/gunicorn/access.log"
errorlog = "/app/running/storage/logs/gunicorn/error.log"

pidfile = "/app/running/storage/logs/gunicorn/gunicorn.pid"
SOCKFILE = "/app/running/storage/logs/gunicorn/gunicorn.sock"

# Example of a more detailed logging config
# logconfig_dict = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "formatters": {
#         "generic": {
#             "format": "%(asctime)s [%(process)d] [%(levelname)s] %(message)s",
#             "datefmt": "%Y-%m-%d %H:%M:%S",
#             "class": "logging.Formatter",
#         },
#     },
#     "handlers": {
#         "console": {
#             "class": "logging.StreamHandler",
#             "formatter": "generic",
#         },
#     },
#     "root": {
#         "level": "INFO",
#         "handlers": ["console"],
#     },
# }
