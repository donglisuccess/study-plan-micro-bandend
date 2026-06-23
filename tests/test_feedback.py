import json
import tempfile
import unittest
from pathlib import Path

import database
from server import FeedbackValidationError, validate_feedback_payload


class FeedbackValidationTests(unittest.TestCase):
    def test_normalizes_valid_feedback(self):
        result = validate_feedback_payload(
            {
                "planId": " plan-1 ",
                "options": ["有帮助", "有帮助", " 想要更详细 "],
                "text": " 希望增加练习题 ",
                "createdAt": 1750000000000,
            }
        )

        self.assertEqual(result["planId"], "plan-1")
        self.assertEqual(result["options"], ["有帮助", "想要更详细"])
        self.assertEqual(result["text"], "希望增加练习题")

    def test_requires_option_or_text(self):
        with self.assertRaises(FeedbackValidationError):
            validate_feedback_payload(
                {
                    "planId": "plan-1",
                    "options": [],
                    "text": "   ",
                }
            )

    def test_rejects_text_over_limit(self):
        with self.assertRaises(FeedbackValidationError):
            validate_feedback_payload(
                {
                    "planId": "plan-1",
                    "options": [],
                    "text": "反馈" * 101,
                }
            )


class FeedbackDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = database.DB_PATH
        database.DB_PATH = Path(self.temp_dir.name) / "feedback-test.db"
        database.initialize_database()
        database.save_generated_plan(
            {
                "id": "plan-1",
                "grade": "初一",
                "subject": "数学",
                "level": "一般",
                "goal": "巩固提升",
                "days": 14,
                "dailyTime": "1 小时",
                "items": [],
            }
        )

    def tearDown(self):
        database.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_saves_feedback_for_existing_plan(self):
        result = database.save_plan_feedback(
            "plan-1",
            ["有帮助"],
            "内容很清楚",
            1750000000000,
        )

        with database.get_connection() as connection:
            row = connection.execute(
                """
                SELECT plan_id, options_json, feedback_text, client_created_at
                FROM plan_feedbacks
                WHERE id = ?
                """,
                (result["id"],),
            ).fetchone()

        self.assertEqual(row["plan_id"], "plan-1")
        self.assertEqual(json.loads(row["options_json"]), ["有帮助"])
        self.assertEqual(row["feedback_text"], "内容很清楚")
        self.assertEqual(row["client_created_at"], 1750000000000)

    def test_rejects_unknown_plan(self):
        with self.assertRaises(LookupError):
            database.save_plan_feedback("missing-plan", ["一般"], "", None)


if __name__ == "__main__":
    unittest.main()
