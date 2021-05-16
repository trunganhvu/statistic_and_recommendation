# import multiprocessing

bind = "127.0.0.1:8000"
# workers = multiprocessing.cpu_count() * 2 + 1
workers = 2

# Error log - records Gunicorn server goings-on
errorlog = "/var/log/gunicorn.error.log"
# Whether to send Django output to the error log
capture_output = True
# How verbose the Gunicorn error logs should be
loglevel = "info"
