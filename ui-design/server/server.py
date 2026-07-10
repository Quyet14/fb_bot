import http.server
import socketserver
import os
import urllib.error
import urllib.request

PORT = 8001
BACKEND = os.getenv("FBBOT_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")



ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROUTES = {
    "/":                          "/html/index.html",
    "/index.html":                "/html/index.html",
    "/dashboard":                 "/html/dashboard.html",
    "/dashboard.html":            "/html/dashboard.html",
    "/landing":                   "/html/index.html",
    "/login":                     "/html/login.html",
    "/login.html":                "/html/login.html",
    "/register":                  "/html/register.html",
    "/register.html":             "/html/register.html",
    "/groups":                    "/pages/groups.html",
    "/groups.html":               "/pages/groups.html",
    "/topics":                    "/pages/topics.html",
    "/topics.html":               "/pages/topics.html",
    "/schedules":                 "/pages/schedules.html",
    "/schedules.html":            "/pages/schedules.html",
    "/fanpage-schedules":         "/pages/fanpage-schedules.html",
    "/fanpage-schedules.html":    "/pages/fanpage-schedules.html",
    "/logs":                      "/pages/logs.html",
    "/logs.html":                 "/pages/logs.html",
    "/settings":                  "/pages/settings.html",
    "/settings.html":             "/pages/settings.html",
    "/profile":                   "/pages/profile.html",
    "/profile.html":              "/pages/profile.html",
}

# Map extension -> Content-Type với charset
MIME_MAP = {
    ".html": "text/html; charset=utf-8",
    ".css":  "text/css; charset=utf-8",
    ".js":   "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".svg":  "image/svg+xml",
    ".ico":  "image/x-icon",
}

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        if self._proxy_to_backend():
            return
        path_clean = self.path.split("?")[0]
        if path_clean != "/":
            path_clean = path_clean.rstrip("/")
        if path_clean in ROUTES:
            self.path = ROUTES[path_clean]
        super().do_GET()

    def do_POST(self):
        if not self._proxy_to_backend():
            self.send_error(404)

    def do_PUT(self):
        if not self._proxy_to_backend():
            self.send_error(404)

    def do_DELETE(self):
        if not self._proxy_to_backend():
            self.send_error(404)

    def do_OPTIONS(self):
        if self.path.startswith("/api/") or self.path.startswith("/uploads/images/"):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Authorization,Content-Type")
            self.end_headers()
            return
        self.send_error(404)

    def _proxy_to_backend(self):
        if self.path.startswith("/api/"):
            target_path = self.path[4:] or "/"
        elif self.path.startswith("/uploads/images/"):
            target_path = self.path
        else:
            return False

        body = None
        if self.command in {"POST", "PUT", "PATCH"}:
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else None

        headers = {
            key: value for key, value in self.headers.items()
            if key.lower() not in {"host", "content-length", "connection", "accept-encoding"}
        }
        req = urllib.request.Request(f"{BACKEND}{target_path}", data=body, headers=headers, method=self.command)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = resp.read()
                self.send_response(resp.status)
                for key, value in resp.headers.items():
                    if key.lower() not in {"transfer-encoding", "connection", "content-encoding"}:
                        self.send_header(key, value)
                self.end_headers()
                self.wfile.write(payload)
        except urllib.error.HTTPError as e:
            payload = e.read()
            self.send_response(e.code)
            for key, value in e.headers.items():
                if key.lower() not in {"transfer-encoding", "connection", "content-encoding"}:
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(payload)
        except Exception as e:
            msg = f"Backend proxy error: {e}".encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
        return True

    def guess_type(self, path):
        _, ext = os.path.splitext(str(path))
        if ext.lower() in MIME_MAP:
            return MIME_MAP[ext.lower()]
        return super().guess_type(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma",        "no-cache")
        self.send_header("Expires",       "0")
        super().end_headers()

    def log_message(self, format, *args):
        status = args[1] if len(args) > 1 else "?"
        print(f"  [{status}] {args[0]}")

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    httpd.allow_reuse_address = True
    import socket
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"\n{'='*52}")
    print(f"  FB Bot Console — Dev Server")
    print(f"  Local     : http://127.0.0.1:{PORT}/")
    print(f"  Network   : http://{local_ip}:{PORT}/")
    print(f"  Landing   : http://{local_ip}:{PORT}/landing")
    print(f"  Chia se link nay cho nguoi khac: http://{local_ip}:{PORT}/")
    print(f"  Ctrl+C to stop")
    print(f"{'='*52}\n")
    httpd.serve_forever()
