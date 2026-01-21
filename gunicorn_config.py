import os
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
workers = 1
threads = 1
timeout = 120 
# Use a WebSocket-capable worker for Flask-SocketIO (gevent + gevent-websocket)
worker_class = 'geventwebsocket.gunicorn.workers.GeventWebSocketWorker'
preload_app = False