import http.server
import socketserver
import os

PORT = 8001
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROUTES = {
    "/":                    "/html/index.html",
    "/index.html":          "/html/index.html",
    "/dashboard":           "/html/dashboard.html",
    "/dashboard.html":      "/html/dashboard.html",
    "/landing":             "/html/index.html",
    "/login":               "/html/login.html",
    "/login.html":          "/html/login.html",
    "/register":            "/html/register.html",
    "/register.html":       "/html/register.html",
    "/groups.html":         "/ui-design/pages/groups.html",
    "/topics.html":         "/ui-design/pages/topics.html",
    "/schedules.html":      "/ui-design/pages/schedules.html",
    "/logs.html":           "/ui-design/pages/logs.html",
    "/settings.html":       "/ui-design/pages/settings.html",
    "/profile.html":        "/ui-design/pages/profile.html",
}

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
        path_clean = self.path.split("?")[0]
        if path_clean in ROUTES:
            self.path = ROUTES[path_clean]
        super().do_GET()

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
