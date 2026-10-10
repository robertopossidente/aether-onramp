import base64
import hmac
import json
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
SWAGGER_UI = b"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Aether SD-Core API</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.onload = () => SwaggerUIBundle({
      url: "/openapi.json",
      dom_id: "#swagger-ui",
      deepLinking: true
    });
  </script>
</body>
</html>"""

ERROR_RESPONSE = {
    "description": "Erro retornado pelo WebUI",
    "content": {
        "application/json": {
            "schema": {"$ref": "#/components/schemas/Error"}
        }
    },
}
JSON_OBJECT = {"$ref": "#/components/schemas/JsonObject"}


def _operation(summary, response_schema, method="get"):
    operation = {
        "summary": summary,
        "responses": {
            "200": {
                "description": "Operação concluída",
                "content": {
                    "application/json": {"schema": response_schema}
                },
            },
            "default": ERROR_RESPONSE,
        },
    }
    if method == "post":
        operation["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {"schema": JSON_OBJECT}
            },
        }
    return operation


def _item_path(parameter, label, tag):
    get = {**_operation(f"Consulta {label}", JSON_OBJECT), "tags": [tag]}
    post = {
        **_operation(f"Cria ou atualiza {label}", JSON_OBJECT, "post"),
        "tags": [tag],
    }
    delete = {
        **_operation(
            f"Exclui {label}",
            {"type": "object", "additionalProperties": True},
            "delete",
        ),
        "tags": [tag],
    }
    return {
        "parameters": [{
            "name": parameter,
            "in": "path",
            "required": True,
            "description": label,
            "schema": {"type": "string"},
        }],
        "get": get,
        "post": post,
        "delete": delete,
    }


OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "Aether SD-Core WebUI API",
        "version": "1.0.0",
        "description": (
            "API do WebUI do SD-Core encaminhada pelo proxy desta GUI. "
            "As estruturas dos objetos dependem da versão/configuração do SD-Core."
        ),
    },
    "servers": [{"url": "/proxy", "description": "Proxy da GUI"}],
    "tags": [
        {"name": "Network slices"},
        {"name": "Device groups"},
        {"name": "Assinantes"},
        {"name": "Inventário"},
    ],
    "paths": {
        "/config/v1/network-slice": {
            "get": {
                **_operation(
                    "Lista os identificadores de network slices",
                    {"type": "array", "items": {"type": "string"}},
                ),
                "tags": ["Network slices"],
            }
        },
        "/config/v1/network-slice/{name}": {
            **_item_path("name", "network slice", "Network slices"),
        },
        "/config/v1/device-group": {
            "get": {
                **_operation(
                    "Lista os identificadores de device groups",
                    {"type": "array", "items": {"type": "string"}},
                ),
                "tags": ["Device groups"],
            }
        },
        "/config/v1/device-group/{name}": {
            **_item_path("name", "device group", "Device groups"),
        },
        "/api/subscriber": {
            "get": {
                **_operation(
                    "Lista os assinantes",
                    {"type": "array", "items": JSON_OBJECT},
                ),
                "tags": ["Assinantes"],
            }
        },
        "/api/subscriber/{ueId}": {
            **_item_path("ueId", "ID do assinante", "Assinantes"),
        },
        "/config/v1/inventory/gnb": {
            "get": {
                **_operation(
                    "Lista os gNBs conhecidos",
                    {"type": "array", "items": JSON_OBJECT},
                ),
                "tags": ["Inventário"],
            }
        },
        "/config/v1/inventory/upf": {
            "get": {
                **_operation(
                    "Lista os UPFs conhecidos",
                    {"type": "array", "items": JSON_OBJECT},
                ),
                "tags": ["Inventário"],
            }
        },
    },
    "components": {
        "schemas": {
            "JsonObject": {
                "type": "object",
                "description": "Objeto JSON conforme o modelo do SD-Core.",
                "additionalProperties": True,
            },
            "Error": {
                "type": "object",
                "additionalProperties": True,
                "description": "Resposta de erro da API upstream.",
            },
        }
    },
}


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
        if self.command == "GET" and self.path in ("/docs", "/docs/", "/swagger"):
            return self._send(200, SWAGGER_UI, "text/html; charset=utf-8")
        if self.command == "GET" and self.path == "/openapi.json":
            body = json.dumps(OPENAPI_SPEC, ensure_ascii=False).encode()
            return self._send(200, body, "application/json; charset=utf-8")
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
