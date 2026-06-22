import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from database import get_basic_options, initialize_database, save_generated_plan
from plan_generator import PlanValidationError, generate_study_plan


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

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/study-plans/generate":
            try:
                options = self.read_json_body()
                plan = generate_study_plan(options)
                save_generated_plan(plan)
            except PlanValidationError as error:
                self.send_json(400, {"code": 4001, "message": str(error)})
                return
            except ValueError as error:
                self.send_json(400, {"code": 4000, "message": str(error)})
                return
            except Exception as error:
                print(f"[study-plan-api] generate failed: {error}")
                self.send_json(500, {"code": 5000, "message": "生成计划失败，请稍后重试"})
                return

            self.send_json(
                200,
                {
                    "code": 0,
                    "message": "success",
                    "data": plan,
                },
            )
            return

        self.send_json(404, {"code": 404, "message": "not found"})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_common_headers()
        self.end_headers()

    def read_json_body(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("请求长度不正确") from error

        if content_length <= 0:
            raise ValueError("请求内容不能为空")
        if content_length > 64 * 1024:
            raise ValueError("请求内容过大")

        try:
            return json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("请求内容不是有效的 JSON") from error

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
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, message_format, *args):
        print("[study-plan-api] " + message_format % args)


def run():
    initialize_database()
    server = ThreadingHTTPServer((HOST, PORT), ApiHandler)
    print(f"Study plan API is running at http://127.0.0.1:{PORT}")
    print("GET /api/basic-options")
    print("POST /api/study-plans/generate")
    server.serve_forever()


if __name__ == "__main__":
    run()
