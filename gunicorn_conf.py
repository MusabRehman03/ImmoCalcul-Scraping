from multiprocessing import cpu_count

# Socket path
bind = 'unix:/home/bots/modules/SC-ImmoCalcul/gunicorn.sock'

# Worker options
workers = cpu_count() + 1
worker_class = 'uvicorn.workers.UvicornWorker'

# Logging options
loglevel = 'debug'
accesslog = '/home/bots/modules/SC-ImmoCalcul/access_log'
errorlog = '/home/bots/modules/SC-ImmoCalcul/error_log'

