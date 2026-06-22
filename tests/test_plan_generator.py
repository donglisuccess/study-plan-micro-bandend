import unittest

from plan_generator import PlanValidationError, generate_study_plan


class PlanGeneratorTests(unittest.TestCase):
    def test_generates_supported_subjects(self):
        cases = [
            ("五年级", "数学"),
            ("六年级", "语文"),
            ("初一", "英语"),
            ("初二", "物理"),
            ("初三", "化学"),
            ("高一", "生物"),
            ("高一", "政治"),
            ("高二", "历史"),
        ]

        for grade, subject in cases:
            with self.subTest(grade=grade, subject=subject):
                plan = generate_study_plan(
                    {
                        "grade": grade,
                        "subject": subject,
                        "level": "一般",
                        "goal": "补基础 + 预习",
                        "days": "21 天",
                        "dailyTime": "1.5 小时",
                    }
                )

                self.assertEqual(len(plan["items"]), 21)
                self.assertEqual(plan["generatedBy"], "rule_template_v1")
                self.assertTrue(
                    any(item["title"].startswith("新课预习") for item in plan["items"])
                )
                self.assertEqual(plan["items"][-1]["title"], "计划总结与成果验收")

    def test_task_count_matches_daily_time(self):
        short_plan = generate_study_plan(
            {
                "grade": "初一",
                "subject": "数学",
                "level": "基础较弱",
                "goal": "补基础",
                "days": "14 天",
                "dailyTime": "30 分钟",
            }
        )
        long_plan = generate_study_plan(
            {
                "grade": "高一",
                "subject": "物理",
                "level": "较好",
                "goal": "巩固提升",
                "days": "14 天",
                "dailyTime": "2 小时",
            }
        )

        self.assertTrue(all(len(item["tasks"]) == 2 for item in short_plan["items"]))
        self.assertTrue(all(2 <= len(item["tasks"]) <= 4 for item in long_plan["items"]))

    def test_primary_grade_rejects_secondary_subject(self):
        with self.assertRaises(PlanValidationError):
            generate_study_plan(
                {
                    "grade": "五年级",
                    "subject": "物理",
                    "level": "一般",
                    "goal": "补基础",
                    "days": "14 天",
                    "dailyTime": "1 小时",
                }
            )


if __name__ == "__main__":
    unittest.main()
