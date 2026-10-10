import base64
import hmac
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEBUI_URL = os.environ.get("WEBUI_URL", "http://172.30.255.119:30500").rstrip("/")
PORT = int(os.environ.get("PORT", "8088"))
AUTH_USER = os.environ.get("GUI_USER", "")
AUTH_PASS = os.environ.get("GUI_PASSWORD", "")
READ_ONLY = os.environ.get("READ_ONLY", "false").lower() == "true"
ALLOWED_PREFIXES = ("/config/v1/", "/api/subscriber")
INDEX = Path(__file__).with_name("index.html").read_bytes()


class Handler(BaseHTTPRequestHandler):
    server_version = "aether-gui"

    def _authorized(self):
        if not AUTH_USER:
            return True
        header = self.headers.get("Authorization", "")
        if not header.startswith("Basic "):
            return False
        try:
            supplied = base64.b64decode(header[6:]).decode()
        except Exception:
            return False
        return hmac.compare_digest(supplied, f"{AUTH_USER}:{AUTH_PASS}")

    def _send(self, code, body=b"", ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle(self):
        if not self._authorized():
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="aether-gui"')
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if self.command == "GET" and self.path in ("/", "/index.html"):
            return self._send(200, INDEX, "text/html; charset=utf-8")
        if self.path == "/gui/config":
            return self._send(200, b'{"readOnly": %s}' % (b"true" if READ_ONLY else b"false"))

        if not self.path.startswith("/proxy/"):
            return self._send(404, b'{"error": "not found"}')
        target = self.path[len("/proxy"):]
        if not target.startswith(ALLOWED_PREFIXES) or ".." in target:
            return self._send(403, b'{"error": "path not allowed"}')
        if READ_ONLY and self.command != "GET":
            return self._send(403, b'{"error": "read-only mode"}')

        length = int(self.headers.get("Content-Length") or 0)
        data = self.rfile.read(length) if length else None
        req = urllib.request.Request(WEBUI_URL + target, data=data, method=self.command)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                self._send(resp.status, resp.read(), resp.headers.get("Content-Type", "application/json"))
        except urllib.error.HTTPError as e:
            self._send(e.code, e.read(), e.headers.get("Content-Type", "text/plain"))
        except Exception as e:
            self._send(502, ('{"error": "%s"}' % str(e).replace('"', "'")).encode())

    do_GET = do_POST = do_PUT = do_DELETE = _handle


if __name__ == "__main__":
    print(f"listening on :{PORT}, upstream {WEBUI_URL}, read_only={READ_ONLY}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
