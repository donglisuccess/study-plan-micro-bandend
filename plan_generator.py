import random
import re
import uuid
from datetime import datetime, timezone


GRADE_ALIASES = {
    "小学五年级": "五年级",
    "小学六年级": "六年级",
}

VALID_GRADES = ("五年级", "六年级", "初一", "初二", "初三", "高一", "高二")
VALID_SUBJECTS = ("数学", "语文", "英语", "物理", "化学", "生物", "政治", "历史")
VALID_LEVELS = ("基础较弱", "一般", "较好")
VALID_GOALS = ("补基础", "巩固提升", "预习新课", "补基础 + 预习")
PRIMARY_GRADES = ("五年级", "六年级")
PRIMARY_SUBJECTS = ("数学", "语文", "英语")

DAILY_MINUTES = {
    "30 分钟": 30,
    "1 小时": 60,
    "1.5 小时": 90,
    "2 小时": 120,
}

SUBJECT_MODULES = {
    "数学": {
        "primary": ["数的运算", "分数与小数", "简易方程", "应用题", "图形与面积", "统计与可能性"],
        "middle": ["有理数与整式", "方程与不等式", "函数基础", "三角形与四边形", "几何证明", "数据统计"],
        "high": ["集合与函数", "基本初等函数", "三角函数", "数列", "立体几何", "概率统计"],
    },
    "语文": {
        "primary": ["字词与病句", "课内阅读", "记叙文阅读", "古诗文积累", "段落表达", "习作审题"],
        "middle": ["现代文阅读", "文言文基础", "古诗词鉴赏", "名著阅读", "语言运用", "记叙文写作"],
        "high": ["论述类文本", "文学类文本", "文言文阅读", "古诗词鉴赏", "语言文字运用", "议论文写作"],
    },
    "英语": {
        "primary": ["核心单词", "自然拼读", "基础句型", "听力跟读", "短文阅读", "书面表达"],
        "middle": ["词汇短语", "时态语法", "阅读理解", "完形填空", "听说训练", "作文表达"],
        "high": ["核心词汇", "句法结构", "阅读理解", "完形填空", "语法填空", "应用文写作"],
    },
    "物理": {
        "middle": ["机械运动", "声现象", "光现象", "质量与密度", "力与运动", "功和机械能"],
        "high": ["运动学", "相互作用", "牛顿运动定律", "曲线运动", "机械能", "实验与测量"],
    },
    "化学": {
        "middle": ["物质构成", "化学用语", "空气和氧气", "水和溶液", "化学方程式", "酸碱盐基础"],
        "high": ["物质的量", "离子反应", "氧化还原反应", "元素化合物", "反应原理", "有机化学基础"],
    },
    "生物": {
        "middle": ["细胞结构", "生物分类", "植物生理", "人体生理", "遗传与变异", "生态系统"],
        "high": ["细胞代谢", "遗传规律", "稳态与调节", "生物与环境", "生物技术", "实验探究"],
    },
    "政治": {
        "middle": ["成长与心理", "道德与法治", "权利与义务", "国家制度", "国情与发展", "时事理解"],
        "high": ["中国特色社会主义", "经济与社会", "政治与法治", "哲学与文化", "逻辑与思维", "时事分析"],
    },
    "历史": {
        "middle": ["中国古代史", "中国近代史", "中国现代史", "世界古代史", "世界近代史", "世界现代史"],
        "high": ["中外历史纲要", "制度演变", "经济与社会生活", "文化交流传播", "战争与和平", "史料分析"],
    },
}

SUBJECT_TASKS = {
    "数学": {
        "diagnostic": ["完成一组覆盖本学期重点的基础题", "标出计算、概念和应用题中最薄弱的 2 类", "整理 3 道最有代表性的错题"],
        "base": ["回看课本例题，梳理{topic}的定义、公式和适用条件", "完成{count}道{topic}基础题，按“会做、犹豫、不会”分类", "选 1 道错题写清错误步骤和正确解法", "口头讲解 1 道典型题的解题思路"],
        "practice": ["归纳{topic}的 2 类常见题型和解题入口", "完成{count}道分层练习，检查步骤和单位", "重做 2 道同类错题并比较两次思路", "尝试 1 道综合题，卡住时只看第一步提示"],
        "preview": ["阅读新课{topic}，圈出定义、公式和例题条件", "照着例题完成 3 到 5 道入门题", "把新知识与已经学过的内容画成联系图", "记录 2 个暂时不理解的问题，开学后重点听"],
    },
    "语文": {
        "diagnostic": ["完成一组字词、病句和阅读小测", "检查阅读题中概括、赏析和作用题的失分情况", "翻看近期作文，找出内容和表达各 1 个问题"],
        "base": ["复习{topic}的答题方法和常用表达", "完成 1 组基础练习，答案必须在原文中找依据", "积累 5 个好词句或 2 个作文素材", "用 3 句话复述今天阅读内容的主旨"],
        "practice": ["完成 1 篇{topic}练习并圈出关键句", "对照答案补全“依据、分析、结论”三步", "把 1 道失分题改写成完整规范答案", "围绕同一主题写一个 150 字片段"],
        "preview": ["预读{topic}相关篇目，标出生词和不理解的句子", "概括段落大意并写出文章结构", "查找作者或时代背景，整理 3 条信息", "仿写一个有细节、有感受的短段落"],
    },
    "英语": {
        "diagnostic": ["完成词汇、语法和短文阅读小测", "统计单词、句型和阅读三类错误数量", "朗读一段课文并记录卡顿位置"],
        "base": ["复习{topic}中的核心词汇和句型", "完成{count}个词句练习并订正拼写", "跟读课文或音频 10 分钟，模仿重音和停顿", "用今天的词汇造 5 个与生活有关的句子"],
        "practice": ["完成 1 组{topic}练习并标出依据", "整理 5 个易错词组或语法点", "精读 1 篇短文，概括每段中心句", "写 6 到 8 句话的小短文并自行检查"],
        "preview": ["预习{topic}的新单词、短语和重点句型", "听读新课内容 2 遍并标出听不清的位置", "用新句型完成 5 个替换练习", "不看课本复述 3 句新课重点表达"],
    },
    "物理": {
        "diagnostic": ["完成概念、计算和实验题各一组", "检查公式选择、单位换算和受力分析中的问题", "整理 2 个生活现象并尝试用物理知识解释"],
        "base": ["梳理{topic}的概念、公式、单位和适用条件", "完成{count}道基础题，计算题写全已知量和公式", "画出 1 张过程图、受力图或光路图", "用生活中的例子解释今天的物理规律"],
        "practice": ["完成{topic}的 1 组分层练习", "对 2 道错题检查对象、过程和单位", "完成 1 道实验题，写清自变量和因变量", "尝试用两种方法分析 1 道综合题"],
        "preview": ["阅读{topic}新课并记录关键物理量", "观察或设计 1 个简单实验，预测实验现象", "完成 3 道新课概念判断题", "整理公式中各物理量的含义和单位"],
    },
    "化学": {
        "diagnostic": ["完成化学用语、概念和实验现象小测", "检查元素符号、化学式和方程式的书写错误", "整理 3 个容易混淆的物质或反应"],
        "base": ["梳理{topic}的核心概念和常见物质", "完成 1 组化学用语或基础概念练习", "整理 3 个反应的条件、现象和结论", "规范书写并配平 3 到 5 个化学方程式"],
        "practice": ["完成{topic}的 1 组分层练习", "对照实验装置说明每个步骤的目的", "整理 2 道错题涉及的知识链", "完成 1 道计算或推断题并写出依据"],
        "preview": ["预习{topic}并圈出新物质、新概念和新反应", "写出 3 个关键化学用语并说明含义", "阅读 1 个新课实验，预测现象和结论", "把新知识与已学物质关系画成转化图"],
    },
    "生物": {
        "diagnostic": ["完成概念、识图和实验探究小测", "检查结构与功能、过程与条件的混淆点", "列出最不熟悉的 3 个生物学概念"],
        "base": ["梳理{topic}中的结构、功能和过程", "完成 1 组概念辨析或识图练习", "画 1 张结构图或过程图并补全标注", "用自己的话解释 3 个核心概念"],
        "practice": ["完成{topic}的图表或材料分析练习", "整理实验的目的、变量、步骤和结论", "把 2 道错题改成正确的判断并说明理由", "用知识网络串联今天的 4 个关键词"],
        "preview": ["阅读{topic}新课并标出结构和过程关键词", "观察教材图示，按顺序讲述变化过程", "提出 2 个可以通过实验验证的问题", "把新旧知识整理成一张对比表"],
    },
    "政治": {
        "diagnostic": ["完成基础观点和材料分析小测", "检查观点记忆、材料对应和表达完整性", "整理 3 个不会用教材观点解释的生活情境"],
        "base": ["理解{topic}的 3 个核心观点和关键词", "为每个观点匹配 1 个生活或社会例子", "完成 2 道选择题并说明排除理由", "用“观点 + 材料 + 结论”回答 1 道简答题"],
        "practice": ["完成{topic}的 2 道材料分析题", "圈出材料中的主体、行为和结果", "补全答案中缺少的教材观点", "结合近期新闻写一段 100 字分析"],
        "preview": ["预读{topic}框题并圈出 3 个核心观点", "用自己的话解释标题之间的关系", "寻找 1 个与新课相关的时事案例", "列出 2 个预习后仍想追问的问题"],
    },
    "历史": {
        "diagnostic": ["完成时间、人物、事件和材料题小测", "检查时间线、因果关系和历史影响的薄弱点", "整理 3 个容易混淆的历史事件"],
        "base": ["梳理{topic}的时间、人物、事件和影响", "完成一条包含 5 个节点的时间线", "阅读 1 段史料并提取出处、观点和信息", "用“背景、过程、影响”复述 1 个事件"],
        "practice": ["完成{topic}的 2 道材料分析题", "比较 2 个事件的相同点和不同点", "把 1 道错题放回时间线重新定位", "围绕一个主题整理中外历史联系"],
        "preview": ["预读{topic}并标记时间、地点和主要人物", "制作新课的时间轴或事件关系图", "阅读 1 则相关史料并写出有效信息", "提出 2 个关于事件原因或影响的问题"],
    },
}

GENERAL_TIPS = (
    "先保证正确率，再逐步提高速度。",
    "遇到不会的内容先标记，集中在最后处理。",
    "完成后让孩子用自己的话复述今天的重点。",
    "错题不只改答案，还要写清错误原因。",
    "今天只和昨天的自己比较，稳定完成最重要。",
    "学习结束后用 5 分钟整理桌面和明日材料。",
)


class PlanValidationError(ValueError):
    pass


def _parse_days(value):
    matched = re.search(r"\d+", str(value or ""))
    days = int(matched.group()) if matched else 0
    if days not in (14, 21, 30, 45):
        raise PlanValidationError("计划天数不支持")
    return days


def _get_stage(grade):
    if grade in PRIMARY_GRADES:
        return "primary"
    if grade.startswith("高"):
        return "high"
    return "middle"


def _task_limit(minutes):
    if minutes <= 30:
        return 2
    if minutes <= 60:
        return 3
    return 4


def _practice_count(minutes, level):
    base = {30: 6, 60: 10, 90: 14, 120: 18}[minutes]
    if level == "基础较弱":
        return max(5, base - 2)
    if level == "较好":
        return base + 2
    return base


def _fill_tasks(templates, topic, count, limit, rng):
    selected = list(templates)
    rng.shuffle(selected)
    return [
        template.format(topic=topic, count=count)
        for template in selected[:limit]
    ]


def _build_summary(grade, subject, level, goal, days, daily_time):
    level_text = {
        "基础较弱": "前半程会放慢节奏，优先补齐概念、基础方法和常见错误。",
        "一般": "计划会在基础复习和专题练习之间保持平衡，帮助知识形成体系。",
        "较好": "基础复习会更加精炼，并增加综合运用和表达输出。",
    }[level]
    goal_text = {
        "补基础": "全程以查漏补缺和错题回炉为主，不盲目追求难度。",
        "巩固提升": "在稳定基础题正确率后，逐步加入分层练习和综合任务。",
        "预习新课": "先保持旧知识不断档，再在后半程建立新课的初步框架。",
        "补基础 + 预习": "前半程集中补基础，后半程自然过渡到新课预习。",
    }[goal]
    return (
        f"这是一份面向{grade}{subject}的 {days} 天计划，每天建议学习{daily_time}。"
        f"{level_text}{goal_text}每 7 天安排一次复盘，家长可根据完成质量适当增减题量。"
    )


def _build_focus(subject, goal):
    focus_parts = [f"{subject}核心知识", "基础方法", "错题整理"]
    if "预习" in goal:
        focus_parts.append("新课预习")
    if goal == "巩固提升":
        focus_parts.append("综合运用")
    return " + ".join(focus_parts)


def _build_review_item(day, minutes, week_index, final_day):
    title = "计划总结与成果验收" if final_day else f"第 {week_index} 周复盘"
    tasks = [
        "整理本周错题，按知识点和错因分类",
        "重做 5 道代表性错题，确认能够独立完成",
        "用一页纸画出本周知识结构或时间线",
        "和家长一起记录完成率，并确定下周最需要加强的 2 个内容",
    ][:_task_limit(minutes)]
    return {
        "title": title,
        "tasks": tasks,
        "tip": "复盘不是重复抄答案，而是确认哪些内容已经真正掌握。",
    }


def generate_study_plan(options):
    if not isinstance(options, dict):
        raise PlanValidationError("请求参数格式不正确")

    grade = GRADE_ALIASES.get(str(options.get("grade", "")).strip(), str(options.get("grade", "")).strip())
    subject = str(options.get("subject", "")).strip()
    level = str(options.get("level", "")).strip()
    goal = str(options.get("goal", "")).strip()
    daily_time = str(options.get("dailyTime", "")).strip()
    days = _parse_days(options.get("days"))

    if grade not in VALID_GRADES:
        raise PlanValidationError("请选择正确的年级")
    if subject not in VALID_SUBJECTS:
        raise PlanValidationError("请选择正确的薄弱科目")
    if grade in PRIMARY_GRADES and subject not in PRIMARY_SUBJECTS:
        raise PlanValidationError("五年级和六年级暂不支持该科目")
    if level not in VALID_LEVELS:
        raise PlanValidationError("请选择正确的当前基础")
    if goal not in VALID_GOALS:
        raise PlanValidationError("请选择正确的学习目标")
    if daily_time not in DAILY_MINUTES:
        raise PlanValidationError("请选择正确的每日学习时间")

    minutes = DAILY_MINUTES[daily_time]
    stage = _get_stage(grade)
    modules = SUBJECT_MODULES[subject].get(stage) or SUBJECT_MODULES[subject]["middle"]
    profile = SUBJECT_TASKS[subject]
    plan_id = f"plan_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    rng = random.Random(plan_id)
    topic_offset = rng.randrange(len(modules))
    task_limit = _task_limit(minutes)
    practice_count = _practice_count(minutes, level)

    base_ratio = {
        "基础较弱": 0.56,
        "一般": 0.40,
        "较好": 0.28,
    }[level]
    if goal == "补基础":
        base_ratio = max(base_ratio, 0.62)
    elif goal == "补基础 + 预习":
        base_ratio = max(base_ratio, 0.50)

    items = []
    for day in range(1, days + 1):
        progress = day / days
        final_day = day == days

        if day == 1:
            item = {
                "title": "学习基础诊断",
                "tasks": profile["diagnostic"][:task_limit],
                "tip": "诊断的目的不是打分，而是找到接下来最值得投入时间的地方。",
            }
        elif day % 7 == 0 or final_day:
            item = _build_review_item(day, minutes, (day + 6) // 7, final_day)
        else:
            topic = modules[(topic_offset + day - 2) % len(modules)]
            if progress <= base_ratio:
                phase = "base"
                title = f"基础梳理：{topic}"
            elif "预习" in goal and progress >= 0.68:
                phase = "preview"
                title = f"新课预习：{topic}"
            else:
                phase = "practice"
                title = f"专题巩固：{topic}"

            item = {
                "title": title,
                "tasks": _fill_tasks(
                    profile[phase],
                    topic,
                    practice_count,
                    task_limit,
                    rng,
                ),
                "tip": rng.choice(GENERAL_TIPS),
            }

        items.append(
            {
                "day": day,
                "title": item["title"],
                "tasks": item["tasks"],
                "duration": f"{minutes} 分钟",
                "tip": item["tip"],
                "completed": False,
            }
        )

    return {
        "id": plan_id,
        "grade": grade,
        "subject": subject,
        "level": level,
        "goal": goal,
        "days": days,
        "dailyTime": daily_time,
        "summary": _build_summary(grade, subject, level, goal, days, daily_time),
        "focus": _build_focus(subject, goal),
        "items": items,
        "generatedBy": "rule_template_v1",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
