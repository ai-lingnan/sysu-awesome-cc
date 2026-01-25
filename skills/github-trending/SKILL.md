---
name: github-trending
description: 获取 GitHub 热门项目信息。当用户说"获取 github trending"、"今日/本周/本月热门项目"、"github 上有什么热门"时使用。
---

# GitHub Trending

获取 GitHub 热门项目列表和仓库 README。

## 使用方法

### 获取热门项目

```bash
# 默认：今日热门（所有语言）
python ~/.claude/skills/github-trending/scripts/github_trending.py

# 指定时间范围
python ~/.claude/skills/github-trending/scripts/github_trending.py trending --since weekly
python ~/.claude/skills/github-trending/scripts/github_trending.py trending --since monthly

# 指定语言
python ~/.claude/skills/github-trending/scripts/github_trending.py trending --language python
python ~/.claude/skills/github-trending/scripts/github_trending.py trending --since weekly --language rust
```

### 获取仓库 README

```bash
python ~/.claude/skills/github-trending/scripts/github_trending.py readme owner/repo-name
```

## 参数说明

| 参数 | 可选值 | 默认值 |
|------|--------|--------|
| `--since` | daily, weekly, monthly | daily |
| `--language` | python, javascript, go, rust 等 | 空（所有语言） |

## 执行流程

1. 运行脚本获取热门项目列表
2. 向用户展示结果
3. 如用户对某个项目感兴趣，获取其 README
