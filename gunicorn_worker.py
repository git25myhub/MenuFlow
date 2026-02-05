"""
Custom GeventWebSocket worker that excludes SSL from monkey patching.

Gevent's SSL patch causes RecursionError when requests/urllib3 make HTTPS calls
(e.g. SendGrid API) on Python 3.6+. Excluding ssl from patching fixes this while
keeping socket/threading patches for WebSocket support.
See: https://github.com/gevent/gevent/issues/903
"""
import socket

from gevent import monkey
from geventwebsocket.gunicorn.workers import GeventWebSocketWorker


class GeventWebSocketWorkerNoSSL(GeventWebSocketWorker):
    """GeventWebSocketWorker with SSL excluded from monkey patching."""

    def patch(self):
        monkey.patch_all(ssl=False)
        sockets = []
        for s in self.sockets:
            sockets.append(socket.socket(s.FAMILY, socket.SOCK_STREAM, fileno=s.sock.detach()))
        self.sockets = sockets
