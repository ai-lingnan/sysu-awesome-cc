#!/usr/bin/env python3
"""
Claude Code Chat Archive Tool
从 ~/.claude/projects/ 提取聊天记录并转换为可读的 Markdown 格式

使用方法:
    python3 archive_chats.py [--full] [--project PROJECT] [--since YYYY-MM-DD]

选项:
    --full              完整归档（包括工具调用详情）
    --project NAME      只归档特定项目
    --since YYYY-MM-DD  只归档指定日期之后的会话
    --output DIR        输出目录（默认 ~/ClaudeCodeArchive，可通过 CC_ARCHIVE_DIR 环境变量覆盖）
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import argparse


def get_default_paths():
    """获取默认路径配置"""
    # Support CC_ARCHIVE_DIR environment variable for portability
    default_archive = os.environ.get("CC_ARCHIVE_DIR", str(Path.home() / "ClaudeCodeArchive"))
    return {
        "claude_dir": Path.home() / ".claude",
        "projects_dir": Path.home() / ".claude" / "projects",
        "archive_dir": Path(default_archive),
    }


def decode_project_path(encoded: str) -> str:
    """将编码的项目路径转换为友好名称"""
    if encoded.startswith("-"):
        encoded = encoded[1:]
    path = encoded.replace("-", "/")
    parts = path.split("/")
    meaningful = [p for p in parts if p and p not in ["Users", "xueheng"]]
    if meaningful:
        return "_".join(meaningful[-3:]) if len(meaningful) > 2 else "_".join(meaningful)
    return encoded


def parse_session_file(filepath: Path) -> dict:
    """解析单个会话文件，提取对话内容"""
    session_data = {
        "messages": [],
        "metadata": {},
        "first_timestamp": None,
        "last_timestamp": None,
        "title": None,
        "slug": None,
    }

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if "slug" in entry and not session_data["slug"]:
                    session_data["slug"] = entry["slug"]

                if "timestamp" in entry:
                    ts = entry["timestamp"]
                    if not session_data["first_timestamp"]:
                        session_data["first_timestamp"] = ts
                    session_data["last_timestamp"] = ts

                # 提取用户消息
                if entry.get("type") == "user" and "message" in entry:
                    msg = entry["message"]
                    if isinstance(msg, dict) and "content" in msg:
                        content = msg["content"]
                        if isinstance(content, str):
                            session_data["messages"].append({
                                "role": "user",
                                "content": content,
                                "timestamp": entry.get("timestamp")
                            })
                        elif isinstance(content, list):
                            text_parts = []
                            for part in content:
                                if isinstance(part, dict) and part.get("type") == "text":
                                    text_parts.append(part.get("text", ""))
                            if text_parts:
                                session_data["messages"].append({
                                    "role": "user",
                                    "content": "\n".join(text_parts),
                                    "timestamp": entry.get("timestamp")
                                })

                # 提取助手消息
                elif "message" in entry and isinstance(entry["message"], dict):
                    msg = entry["message"]
                    if msg.get("role") == "assistant" and "content" in msg:
                        content = msg["content"]
                        text_parts = []
                        tool_uses = []

                        if isinstance(content, list):
                            for part in content:
                                if isinstance(part, dict):
                                    if part.get("type") == "text":
                                        text_parts.append(part.get("text", ""))
                                    elif part.get("type") == "tool_use":
                                        tool_uses.append({
                                            "name": part.get("name"),
                                            "input": part.get("input", {})
                                        })
                        elif isinstance(content, str):
                            text_parts.append(content)

                        if text_parts or tool_uses:
                            session_data["messages"].append({
                                "role": "assistant",
                                "content": "\n".join(text_parts),
                                "tools": tool_uses,
                                "timestamp": entry.get("timestamp")
                            })

    except Exception as e:
        print(f"Error parsing {filepath}: {e}")

    return session_data


def format_session_markdown(session_data: dict, include_tools: bool = False) -> str:
    """将会话数据转换为 Markdown 格式"""
    lines = []

    if session_data["slug"]:
        lines.append(f"# {session_data['slug']}")
    else:
        lines.append("# Chat Session")

    lines.append("")
    lines.append("---")

    if session_data["first_timestamp"]:
        try:
            dt = datetime.fromisoformat(session_data["first_timestamp"].replace("Z", "+00:00"))
            lines.append(f"created: {dt.strftime('%Y-%m-%d %H:%M')}")
        except:
            lines.append(f"created: {session_data['first_timestamp']}")

    if session_data["last_timestamp"]:
        try:
            dt = datetime.fromisoformat(session_data["last_timestamp"].replace("Z", "+00:00"))
            lines.append(f"updated: {dt.strftime('%Y-%m-%d %H:%M')}")
        except:
            pass

    lines.append(f"messages: {len(session_data['messages'])}")
    lines.append("---")
    lines.append("")

    for msg in session_data["messages"]:
        role = msg["role"]
        content = msg["content"]

        if role == "user":
            lines.append("## User")
            lines.append("")
            lines.append(content)
            lines.append("")
        else:
            lines.append("## Assistant")
            lines.append("")
            if content:
                lines.append(content)
            if include_tools and msg.get("tools"):
                lines.append("")
                lines.append("<details>")
                lines.append("<summary>Tool Uses</summary>")
                lines.append("")
                for tool in msg["tools"]:
                    lines.append(f"- **{tool['name']}**")
                lines.append("</details>")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def parse_index_table(filepath: Path, link_column: int = 1) -> dict:
    """
    解析现有索引文件中的表格，返回以文件名为键的条目字典

    Args:
        filepath: 索引文件路径
        link_column: 包含链接的列索引（0-based）

    Returns:
        dict: {filename: raw_table_row}
    """
    entries = {}
    if not filepath.exists():
        return entries

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        for line in content.split("\n"):
            line = line.strip()
            if not line.startswith("|") or line.startswith("|--") or line.startswith("| 日期") or line.startswith("| 项目"):
                continue

            # Extract filename from markdown link [title](path/to/file.md)
            match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', line)
            if match:
                link_path = match.group(2)
                filename = link_path.split("/")[-1]
                entries[filename] = line
    except Exception as e:
        print(f"Warning: Could not parse existing index {filepath}: {e}")

    return entries


def create_project_index(project_name: str, sessions: list, existing_entries: dict = None) -> str:
    """创建项目索引文件，合并现有条目"""
    # Build new entries dict
    new_entries = {}
    for session in sessions:
        date = session.get("date", "Unknown")
        title = session.get("title", "Untitled")
        msg_count = session.get("message_count", 0)
        filename = session.get("filename", "")
        new_entries[filename] = f"| {date} | [{title}](sessions/{filename}) | {msg_count} |"

    # Merge: new entries override existing ones (same file = updated content)
    merged = {}
    if existing_entries:
        merged.update(existing_entries)
    merged.update(new_entries)

    # Sort by date (extract from filename: YYYY-MM-DD_HHMM_slug.md)
    def sort_key(item):
        filename = item[0]
        # Try to extract date from filename
        match = re.match(r'(\d{4}-\d{2}-\d{2})_(\d{4})_', filename)
        if match:
            return match.group(1) + match.group(2)
        return "0000-00-00_0000"

    sorted_entries = sorted(merged.items(), key=sort_key, reverse=True)

    lines = [
        f"# {project_name}",
        "",
        f"共 {len(sorted_entries)} 个会话",
        "",
        "## 会话列表",
        "",
        "| 日期 | 标题 | 消息数 |",
        "|------|------|--------|",
    ]

    for filename, row in sorted_entries:
        lines.append(row)

    return "\n".join(lines)


def archive_all(
    full_mode: bool = False,
    project_filter: str = None,
    since_date: str = None,
    output_dir: str = None
) -> dict:
    """
    执行完整归档

    Returns:
        dict: 归档统计信息
    """
    paths = get_default_paths()
    projects_dir = paths["projects_dir"]
    archive_dir = Path(output_dir) if output_dir else paths["archive_dir"]

    # 确保输出目录存在
    for subdir in ["projects", "timeline", "scripts", "raw"]:
        (archive_dir / subdir).mkdir(parents=True, exist_ok=True)

    if not projects_dir.exists():
        print(f"Projects directory not found: {projects_dir}")
        return {"error": "Projects directory not found"}

    since_dt = None
    if since_date:
        try:
            since_dt = datetime.fromisoformat(since_date)
        except:
            print(f"Invalid date format: {since_date}")
            return {"error": "Invalid date format"}

    projects_data = defaultdict(list)
    timeline_data = defaultdict(list)

    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        project_name = decode_project_path(project_dir.name)

        if project_filter and project_filter.lower() not in project_name.lower():
            continue

        print(f"Processing project: {project_name}")

        project_archive_dir = archive_dir / "projects" / project_name / "sessions"
        project_archive_dir.mkdir(parents=True, exist_ok=True)

        for session_file in project_dir.glob("*.jsonl"):
            if session_file.name.startswith("agent-"):
                continue

            session_data = parse_session_file(session_file)

            if not session_data["messages"]:
                continue

            if since_dt and session_data["first_timestamp"]:
                try:
                    session_dt = datetime.fromisoformat(
                        session_data["first_timestamp"].replace("Z", "+00:00")
                    )
                    if session_dt.replace(tzinfo=None) < since_dt:
                        continue
                except:
                    pass

            if session_data["first_timestamp"]:
                try:
                    dt = datetime.fromisoformat(
                        session_data["first_timestamp"].replace("Z", "+00:00")
                    )
                    date_str = dt.strftime("%Y-%m-%d")
                    time_str = dt.strftime("%H%M")
                except:
                    date_str = "unknown"
                    time_str = "0000"
            else:
                date_str = "unknown"
                time_str = "0000"

            slug = session_data["slug"] or session_file.stem[:8]
            filename = f"{date_str}_{time_str}_{slug}.md"

            md_content = format_session_markdown(session_data, include_tools=full_mode)

            output_path = project_archive_dir / filename
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md_content)

            projects_data[project_name].append({
                "date": date_str,
                "title": slug,
                "message_count": len(session_data["messages"]),
                "filename": filename,
            })

            timeline_data[date_str].append({
                "project": project_name,
                "title": slug,
                "message_count": len(session_data["messages"]),
                "path": f"projects/{project_name}/sessions/{filename}",
            })

        if projects_data[project_name]:
            # Read existing index to merge entries from other machines
            index_path = archive_dir / "projects" / project_name / "_index.md"
            existing_entries = parse_index_table(index_path)
            index_content = create_project_index(project_name, projects_data[project_name], existing_entries)
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(index_content)

    # 创建时间线索引
    for date_str, sessions in timeline_data.items():
        if date_str == "unknown":
            continue
        year_month = date_str[:7]
        timeline_dir = archive_dir / "timeline" / year_month
        timeline_dir.mkdir(parents=True, exist_ok=True)

        timeline_path = timeline_dir / f"{date_str}.md"

        # Build new entries
        new_entries = {}
        for s in sessions:
            filename = s['path'].split("/")[-1]
            new_entries[filename] = f"| {s['project']} | [{s['title']}](../../{s['path']}) | {s['message_count']} |"

        # Merge with existing entries
        existing_entries = parse_index_table(timeline_path)
        merged = {}
        merged.update(existing_entries)
        merged.update(new_entries)

        daily_lines = [
            f"# {date_str}",
            "",
            f"共 {len(merged)} 个会话",
            "",
            "| 项目 | 标题 | 消息数 |",
            "|------|------|--------|",
        ]
        for filename, row in sorted(merged.items()):
            daily_lines.append(row)

        with open(timeline_path, "w", encoding="utf-8") as f:
            f.write("\n".join(daily_lines))

    # 创建主 README - scan full archive directory for accurate counts
    projects_dir_archive = archive_dir / "projects"
    all_projects = {}
    if projects_dir_archive.exists():
        for proj_dir in projects_dir_archive.iterdir():
            if proj_dir.is_dir():
                sessions_dir = proj_dir / "sessions"
                if sessions_dir.exists():
                    session_count = len(list(sessions_dir.glob("*.md")))
                    all_projects[proj_dir.name] = session_count

    total_sessions = sum(all_projects.values())

    # Get Beijing time for timestamp
    beijing_tz = timezone(timedelta(hours=8))
    beijing_time = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M')

    readme = f"""# Claude Code Chat Archive

自动归档生成于: {beijing_time} (北京时间)

## 统计

- 项目数: {len(all_projects)}
- 总会话数: {total_sessions}

## 目录结构

- `projects/` - 按项目分类的会话记录
- `timeline/` - 按日期索引
- `scripts/` - 归档工具
- `raw/` - 原始数据备份（可选）

## 使用

```bash
# 增量归档
python3 scripts/archive_chats.py --since $(date -v-1d +%Y-%m-%d)

# 完整归档
python3 scripts/archive_chats.py --full

# 归档特定项目
python3 scripts/archive_chats.py --project NewNote
```

## 项目列表

"""
    for proj in sorted(all_projects.keys()):
        count = all_projects[proj]
        readme += f"- [{proj}](projects/{proj}/_index.md) ({count} 会话)\n"

    with open(archive_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)

    stats = {
        "project_count": len(all_projects),
        "session_count": total_sessions,
        "output_dir": str(archive_dir),
        "projects": all_projects,
        "this_run": {
            "project_count": len(projects_data),
            "session_count": sum(len(v) for v in projects_data.values()),
        }
    }

    print(f"\n✓ 归档完成!")
    print(f"  本次处理项目: {len(projects_data)}")
    print(f"  归档总项目数: {len(all_projects)}")
    print(f"  归档总会话数: {total_sessions}")
    print(f"  输出目录: {archive_dir}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Archive Claude Code chat sessions")
    parser.add_argument("--full", action="store_true", help="Include tool call details")
    parser.add_argument("--project", type=str, help="Filter by project name")
    parser.add_argument("--since", type=str, help="Only archive sessions since date (YYYY-MM-DD)")
    parser.add_argument("--output", type=str, help="Output directory")

    args = parser.parse_args()

    archive_all(
        full_mode=args.full,
        project_filter=args.project,
        since_date=args.since,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()
