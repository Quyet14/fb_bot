import http.server
import socketserver
import os

PORT = 8001
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.path = "/html/index.html"
        super().do_GET()

with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    print(f"Serving UI at http://127.0.0.1:{PORT}")
    httpd.serve_forever()
