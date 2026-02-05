import os
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
workers = 1
threads = 1
timeout = 120 
# Use a WebSocket-capable worker for Flask-SocketIO (gevent + gevent-websocket).
# Custom worker excludes SSL from gevent monkey patching to avoid RecursionError
# when requests makes HTTPS calls (e.g. SendGrid). See gunicorn_worker.py.
worker_class = 'gunicorn_worker.GeventWebSocketWorkerNoSSL'
preload_app = False