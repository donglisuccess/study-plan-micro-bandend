import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from database import (
    get_basic_options,
    initialize_database,
    save_generated_plan,
    save_plan_feedback,
)
from plan_generator import PlanValidationError, generate_study_plan


HOST = os.environ.get("STUDY_PLAN_API_HOST", "0.0.0.0")
PORT = int(os.environ.get("STUDY_PLAN_API_PORT", "5000"))
MAX_FEEDBACK_OPTIONS = 10
MAX_FEEDBACK_OPTION_LENGTH = 30
MAX_FEEDBACK_TEXT_LENGTH = 200


class FeedbackValidationError(ValueError):
    pass


def validate_feedback_payload(payload):
    if not isinstance(payload, dict):
        raise FeedbackValidationError("请求内容格式不正确")

    plan_id = payload.get("planId")
    if not isinstance(plan_id, str) or not plan_id.strip():
        raise FeedbackValidationError("计划 ID 不能为空")
    plan_id = plan_id.strip()
    if len(plan_id) > 100:
        raise FeedbackValidationError("计划 ID 过长")

    raw_options = payload.get("options", [])
    if not isinstance(raw_options, list):
        raise FeedbackValidationError("反馈标签格式不正确")
    if len(raw_options) > MAX_FEEDBACK_OPTIONS:
        raise FeedbackValidationError("反馈标签数量过多")

    options = []
    for raw_option in raw_options:
        if not isinstance(raw_option, str):
            raise FeedbackValidationError("反馈标签格式不正确")
        option = raw_option.strip()
        if not option:
            continue
        if len(option) > MAX_FEEDBACK_OPTION_LENGTH:
            raise FeedbackValidationError("反馈标签内容过长")
        if option not in options:
            options.append(option)

    raw_text = payload.get("text", "")
    if not isinstance(raw_text, str):
        raise FeedbackValidationError("反馈内容格式不正确")
    text = raw_text.strip()
    if len(text) > MAX_FEEDBACK_TEXT_LENGTH:
        raise FeedbackValidationError("反馈内容不能超过 200 字")
    if not options and not text:
        raise FeedbackValidationError("请选择反馈标签或填写反馈内容")

    client_created_at = payload.get("createdAt")
    if client_created_at is not None:
        if isinstance(client_created_at, bool) or not isinstance(client_created_at, (int, float)):
            raise FeedbackValidationError("提交时间格式不正确")
        client_created_at = int(client_created_at)

    return {
        "planId": plan_id,
        "options": options,
        "text": text,
        "createdAt": client_created_at,
    }


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

        if path == "/api/study-plans/feedback":
            try:
                feedback = validate_feedback_payload(self.read_json_body())
                saved_feedback = save_plan_feedback(
                    feedback["planId"],
                    feedback["options"],
                    feedback["text"],
                    feedback["createdAt"],
                )
            except FeedbackValidationError as error:
                self.send_json(400, {"code": 4002, "message": str(error)})
                return
            except LookupError as error:
                self.send_json(404, {"code": 4041, "message": str(error)})
                return
            except ValueError as error:
                self.send_json(400, {"code": 4000, "message": str(error)})
                return
            except Exception as error:
                print(f"[study-plan-api] feedback failed: {error}")
                self.send_json(500, {"code": 5001, "message": "提交反馈失败，请稍后重试"})
                return

            self.send_json(
                201,
                {
                    "code": 0,
                    "message": "success",
                    "data": saved_feedback,
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
    print("POST /api/study-plans/feedback")
    server.serve_forever()


if __name__ == "__main__":
    run()
