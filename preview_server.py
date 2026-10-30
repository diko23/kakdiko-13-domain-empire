import argparse
import http.server
import json
import socketserver
from pathlib import Path
from urllib.parse import urlparse

from build_monorepo import DIST_DIR, MANIFEST_PATH, build_all


class MultiDomainRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/domains":
            manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            payload = {
                "status": "ok",
                "count": len(manifest["domains"]),
                "domains": [
                    {
                        "domain": d["domain"],
                        "brand_name": d["brand_name"],
                        "tier": d["tier"],
                        "tool": d["tool"]["title"],
                        "price_idr": d["acquisition"]["price_idr"],
                        "preview_url": f"/{d['domain']}/",
                    }
                    for d in manifest["domains"]
                ],
            }
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Support Host-header routing just like Cloudflare worker.js
        host = (self.headers.get("Host") or "").lower().split(":")[0]
        if host.startswith("www."):
            host = host[4:]

        if (DIST_DIR / host).is_dir() and not parsed.path.startswith(f"/{host}/"):
            self.path = f"/{host}{parsed.path}"
        elif parsed.path in ("/", "/index.html"):
            self.path = "/command-center/index.html"

        return super().do_GET()


def run_server(port: int = 8080):
    if not DIST_DIR.exists():
        build_all()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), MultiDomainRequestHandler) as httpd:
        print(f"[OK] 13-Domain Empire Server running at http://127.0.0.1:{port}/")
        print(f"    Command Center : http://127.0.0.1:{port}/")
        print(f"    API Endpoint   : http://127.0.0.1:{port}/api/domains")
        httpd.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local Multi-Domain Preview Server")
    parser.add_argument("--port", type=int, default=8080, help="Port number (default: 8080)")
    args = parser.parse_args()
    run_server(args.port)
