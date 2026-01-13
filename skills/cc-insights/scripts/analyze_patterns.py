#!/usr/bin/env python3
"""
Claude Code 交互模式分析工具
分析用户与 Claude Code 的交互模式：时间分布、项目活跃度、任务类型等

使用方法:
    python3 analyze_patterns.py [--output FILE]

输出:
    JSON 格式的分析结果，可被 generate_insights.py 使用
"""

import os
import json
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
import argparse


def get_default_paths():
    """获取默认路径配置"""
    return {
        "claude_dir": Path.home() / ".claude",
        "history_file": Path.home() / ".claude" / "history.jsonl",
        "projects_dir": Path.home() / ".claude" / "projects",
    }


def analyze_history(history_file: Path) -> dict:
    """分析 history.jsonl 文件"""
    projects = Counter()
    hours = Counter()
    dates = Counter()
    word_counts = []
    total_inputs = 0

    if not history_file.exists():
        return {"error": "History file not found"}

    with open(history_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
                total_inputs += 1

                # 项目统计
                if "project" in d:
                    project_name = d["project"].split("/")[-1]
                    projects[project_name] += 1

                # 时间统计
                if "timestamp" in d:
                    ts = d["timestamp"]
                    # timestamp 是毫秒级
                    dt = datetime.fromtimestamp(ts / 1000)
                    hours[dt.hour] += 1
                    dates[dt.strftime("%Y-%m-%d")] += 1

                # 提问长度统计
                if "display" in d and d["display"]:
                    word_count = len(d["display"].split())
                    word_counts.append(word_count)

            except (json.JSONDecodeError, KeyError, TypeError):
                continue

    # 计算统计指标
    avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
    max_words = max(word_counts) if word_counts else 0
    min_words = min(word_counts) if word_counts else 0

    # 时段分布（按比例）
    hour_distribution = {}
    total_hour_count = sum(hours.values())
    for h in range(24):
        count = hours.get(h, 0)
        percentage = (count / total_hour_count * 100) if total_hour_count > 0 else 0
        hour_distribution[h] = {
            "count": count,
            "percentage": round(percentage, 1)
        }

    # 识别高峰时段
    peak_hours = sorted(hours.items(), key=lambda x: x[1], reverse=True)[:3]

    # 日活跃度
    active_days = len(dates)
    avg_inputs_per_day = total_inputs / active_days if active_days > 0 else 0

    return {
        "total_inputs": total_inputs,
        "project_activity": dict(projects.most_common(20)),
        "hour_distribution": hour_distribution,
        "peak_hours": [{"hour": h, "count": c} for h, c in peak_hours],
        "active_days": active_days,
        "avg_inputs_per_day": round(avg_inputs_per_day, 1),
        "prompt_length": {
            "average": round(avg_words, 1),
            "max": max_words,
            "min": min_words,
            "total_prompts": len(word_counts)
        },
        "date_range": {
            "first": min(dates.keys()) if dates else None,
            "last": max(dates.keys()) if dates else None,
        }
    }


def analyze_projects(projects_dir: Path) -> dict:
    """分析项目目录结构"""
    if not projects_dir.exists():
        return {"error": "Projects directory not found"}

    project_stats = {}
    total_sessions = 0
    total_size = 0

    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        project_name = project_dir.name
        sessions = list(project_dir.glob("*.jsonl"))
        main_sessions = [s for s in sessions if not s.name.startswith("agent-")]
        agent_sessions = [s for s in sessions if s.name.startswith("agent-")]

        project_size = sum(f.stat().st_size for f in sessions)
        total_size += project_size
        total_sessions += len(main_sessions)

        # 分析会话消息数
        message_counts = []
        for session_file in main_sessions[:10]:  # 采样前10个
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    message_counts.append(len(lines))
            except:
                pass

        avg_messages = sum(message_counts) / len(message_counts) if message_counts else 0

        project_stats[project_name] = {
            "main_sessions": len(main_sessions),
            "agent_sessions": len(agent_sessions),
            "size_mb": round(project_size / 1024 / 1024, 2),
            "avg_messages_per_session": round(avg_messages, 1)
        }

    # 按会话数排序
    sorted_projects = sorted(
        project_stats.items(),
        key=lambda x: x[1]["main_sessions"],
        reverse=True
    )

    return {
        "total_projects": len(project_stats),
        "total_sessions": total_sessions,
        "total_size_mb": round(total_size / 1024 / 1024, 2),
        "projects": dict(sorted_projects[:20]),  # Top 20
        "project_size_distribution": {
            "large": len([p for p, s in project_stats.items() if s["size_mb"] > 1]),
            "medium": len([p for p, s in project_stats.items() if 0.1 <= s["size_mb"] <= 1]),
            "small": len([p for p, s in project_stats.items() if s["size_mb"] < 0.1]),
        }
    }


def analyze_skills(skills_dir: Path) -> dict:
    """分析已安装的 Skills"""
    if not skills_dir.exists():
        return {"installed": 0, "skills": []}

    skills = []
    for item in skills_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            skill_md = item / "SKILL.md"
            has_skill_md = skill_md.exists()

            # 检查子目录
            has_scripts = (item / "scripts").exists()
            has_references = (item / "references").exists()
            has_assets = (item / "assets").exists()

            skills.append({
                "name": item.name,
                "has_skill_md": has_skill_md,
                "has_scripts": has_scripts,
                "has_references": has_references,
                "has_assets": has_assets,
            })

    return {
        "installed": len(skills),
        "skills": skills
    }


def generate_analysis_report() -> dict:
    """生成完整分析报告"""
    paths = get_default_paths()

    report = {
        "generated_at": datetime.now().isoformat(),
        "history_analysis": analyze_history(paths["history_file"]),
        "project_analysis": analyze_projects(paths["projects_dir"]),
        "skills_analysis": analyze_skills(paths["claude_dir"] / "skills"),
    }

    # 计算综合指标
    history = report["history_analysis"]
    projects = report["project_analysis"]

    if "error" not in history and "error" not in projects:
        report["summary"] = {
            "total_inputs": history.get("total_inputs", 0),
            "total_sessions": projects.get("total_sessions", 0),
            "total_projects": projects.get("total_projects", 0),
            "avg_inputs_per_day": history.get("avg_inputs_per_day", 0),
            "peak_hours": history.get("peak_hours", []),
            "top_projects": list(history.get("project_activity", {}).keys())[:5],
            "storage_mb": projects.get("total_size_mb", 0),
        }

    return report


def main():
    parser = argparse.ArgumentParser(description="Analyze Claude Code interaction patterns")
    parser.add_argument("--output", type=str, help="Output JSON file path")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON")

    args = parser.parse_args()

    report = generate_analysis_report()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2 if args.pretty else None)
        print(f"Analysis saved to: {args.output}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
