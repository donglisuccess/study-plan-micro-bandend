import os
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "study_plan.db"
DB_PATH = Path(os.environ.get("STUDY_PLAN_DB_PATH", DEFAULT_DB_PATH))

CATEGORIES = ("grades", "subjects", "levels", "goals", "days", "dailyTimes")

OPTION_SEEDS = {
    "grades": ["五年级", "六年级", "初一", "初二", "初三", "高一", "高二"],
    "subjects": ["数学", "语文", "英语", "物理", "化学", "生物", "政治", "历史"],
    "levels": ["基础较弱", "一般", "较好"],
    "goals": ["补基础", "巩固提升", "预习新课", "补基础 + 预习"],
    "days": ["14 天", "21 天", "30 天", "45 天"],
    "dailyTimes": ["30 分钟", "1 小时", "1.5 小时", "2 小时"],
}

DEFAULT_OPTIONS = {
    "days": "30 天",
    "dailyTimes": "1 小时",
}


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS basic_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                value TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_default INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, value)
            )
            """
        )

        for category, values in OPTION_SEEDS.items():
            for sort_order, value in enumerate(values):
                is_default = int(DEFAULT_OPTIONS.get(category) == value)
                connection.execute(
                    """
                    INSERT INTO basic_options (
                        category,
                        value,
                        sort_order,
                        is_default
                    )
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(category, value) DO UPDATE SET
                        sort_order = excluded.sort_order,
                        is_default = excluded.is_default,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (category, value, sort_order, is_default),
                )


def get_basic_options():
    result = {category: [] for category in CATEGORIES}
    defaults = {}

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT category, value, is_default
            FROM basic_options
            ORDER BY category, sort_order, id
            """
        ).fetchall()

    for row in rows:
        category = row["category"]
        if category not in result:
            continue
        result[category].append(row["value"])
        if row["is_default"]:
            defaults[category] = row["value"]

    result["defaults"] = defaults
    return result
