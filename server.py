import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from database import get_basic_options, initialize_database


HOST = os.environ.get("STUDY_PLAN_API_HOST", "0.0.0.0")
PORT = int(os.environ.get("STUDY_PLAN_API_PORT", "5000"))


class ApiHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/health":
            self.send_json(200, {"code": 0, "message": "ok"})
            return

        if path == "/api/basic-options":
            self.send_json(
                200,
                {
                    "code": 0,
                    "message": "success",
                    "data": get_basic_options(),
                },
            )
            return

        self.send_json(404, {"code": 404, "message": "not found"})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_common_headers()
        self.end_headers()

    def send_json(self, status_code, payload):
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_common_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_common_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, message_format, *args):
        print("[study-plan-api] " + message_format % args)


def run():
    initialize_database()
    server = ThreadingHTTPServer((HOST, PORT), ApiHandler)
    print(f"Study plan API is running at http://127.0.0.1:{PORT}")
    print("GET /api/basic-options")
    server.serve_forever()


if __name__ == "__main__":
    run()
