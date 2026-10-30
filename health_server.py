"""Minimal HTTP health endpoint required by Render Web Services."""
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

log = logging.getLogger(__name__)
_server = None

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/health", "/healthz"):
            self.send_error(404)
            return
        payload = json.dumps({"status": "ok", "service": "queen-2"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        log.info("health: " + fmt, *args)

def start_health_server():
    global _server
    if _server is not None:
        return _server
    port = int(os.getenv("PORT", "10000"))
    _server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    Thread(target=_server.serve_forever, name="health-server", daemon=True).start()
    log.info("Health server listening on 0.0.0.0:%s", port)
    return _server
