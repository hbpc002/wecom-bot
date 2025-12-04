# Gunicorn configuration file

# Server socket
bind = "0.0.0.0:5000"

# Worker processes
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "wecom-bot"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Environment
raw_env = [
    "PYTHONUNBUFFERED=1",
]
