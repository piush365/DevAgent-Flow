bind = "0.0.0.0:5000"
workers = 2
worker_class = "sync"
# Streaming responses can take a while; keep this generous
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
