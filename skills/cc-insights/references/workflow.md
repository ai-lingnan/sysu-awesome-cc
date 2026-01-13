# CC Insights 详细工作流程

本文档提供完整的归档和分析工作流程指南。

## 完整工作流程

### 阶段 1：归档聊天记录

```bash
# Set skill root (adjust to your installation path)
SKILL_ROOT=~/.claude/skills/cc-insights

# 1.1 完整归档（首次使用）
python3 $SKILL_ROOT/scripts/archive_chats.py --full

# 1.2 增量归档（日常使用）
python3 $SKILL_ROOT/scripts/archive_chats.py --since $(date -v-7d +%Y-%m-%d)

# 1.3 特定项目归档
python3 $SKILL_ROOT/scripts/archive_chats.py --project NewNote
```

输出目录结构：
```
[ARCHIVE_ROOT]/
├── README.md                    # 主索引
├── projects/                    # 按项目分类
│   ├── [project_name]/
│   │   ├── _index.md           # 项目索引
│   │   └── sessions/           # 会话记录
├── timeline/                    # 按日期索引
│   └── YYYY-MM/
│       └── YYYY-MM-DD.md
└── scripts/                     # 工具脚本
```

### 阶段 2：分析交互模式

```bash
# 2.1 生成分析数据
python3 $SKILL_ROOT/scripts/analyze_patterns.py --output /tmp/analysis.json --pretty

# 2.2 查看分析结果
cat /tmp/analysis.json | python3 -m json.tool
```

分析维度：
- **时间分布**: 每小时输入次数，识别高峰时段
- **项目活跃度**: Top 20 项目及其输入次数
- **提问特征**: 平均/最大/最小词数
- **Skills 使用**: 已安装 Skills 列表

### 阶段 3：生成洞察报告

```bash
# 3.1 基于分析数据生成报告
python3 $SKILL_ROOT/scripts/generate_insights.py \
    --analysis /tmp/analysis.json \
    --output [YOUR_OUTPUT_PATH]/CC_Insights_$(date +%Y%m%d).md

# 3.2 直接生成（自动运行分析）
python3 $SKILL_ROOT/scripts/generate_insights.py \
    --output ~/path/to/output.md
```

## 自动化设置

### Cron Job 配置

```bash
# 编辑 crontab
crontab -e

# Set SKILL_ROOT to your installation path in crontab
# 添加以下行（每日凌晨 2 点自动归档）
0 2 * * * python3 [SKILL_ROOT]/scripts/archive_chats.py --since $(date -v-1d +\%Y-\%m-\%d)

# 每周日生成周报
0 3 * * 0 python3 [SKILL_ROOT]/scripts/generate_insights.py --output ~/Reports/weekly_$(date +\%Y\%m\%d).md
```

### 快捷命令

在 `~/.zshrc` 或 `~/.bashrc` 中添加：

```bash
# Set your skill installation path
export CC_INSIGHTS_ROOT=~/.claude/skills/cc-insights

# CC Insights 快捷命令
alias cc-archive="python3 $CC_INSIGHTS_ROOT/scripts/archive_chats.py"
alias cc-analyze="python3 $CC_INSIGHTS_ROOT/scripts/analyze_patterns.py"
alias cc-report="python3 $CC_INSIGHTS_ROOT/scripts/generate_insights.py"

# 一键完整流程
cc-insights() {
    echo "Step 1: Archiving..."
    cc-archive --since $(date -v-7d +%Y-%m-%d)
    echo "Step 2: Analyzing..."
    cc-analyze --output /tmp/cc_analysis.json
    echo "Step 3: Generating report..."
    cc-report --analysis /tmp/cc_analysis.json --output "$1"
    echo "Done! Report saved to: $1"
}
```

## 分析指标说明

### 时间分布指标

| 指标 | 说明 | 用途 |
|------|------|------|
| peak_hours | 输入最多的 3 个小时 | 识别深度工作时段 |
| hour_distribution | 每小时输入次数 | 了解工作节奏 |
| active_days | 有输入的天数 | 评估使用频率 |

### 项目活跃度指标

| 指标 | 说明 | 用途 |
|------|------|------|
| project_activity | 各项目输入次数 | 识别重点项目 |
| main_sessions | 主会话数 | 评估项目深度 |
| size_mb | 项目存储大小 | 管理存储空间 |

### 提问特征指标

| 指标 | 说明 | 参考值 |
|------|------|--------|
| average | 平均提问词数 | 10-20 为简洁 |
| max | 最长提问词数 | >500 可能需拆分 |

## 报告定制

### 输出目录配置

修改脚本中的默认路径：

```python
# archive_chats.py
def get_default_paths():
    return {
        "archive_dir": Path.home() / "YourPath" / "ClaudeCodeArchive",
        # 修改为你的首选路径
    }
```

### 报告模板定制

编辑 `generate_insights.py` 中的 `generate_insights_report()` 函数，可自定义：
- 报告标题和格式
- 分析维度
- 建议内容
- 标签和元数据

## 故障排除

### 常见问题

**Q: 归档脚本报错 "Projects directory not found"**
A: 检查 `~/.claude/projects/` 是否存在，确认 Claude Code 已使用过

**Q: 分析脚本无输出**
A: 检查 `~/.claude/history.jsonl` 是否存在

**Q: 报告中数据显示 N/A**
A: 运行分析脚本时添加 `--pretty` 查看详细错误

### 调试模式

```bash
# 查看原始数据
head -5 ~/.claude/history.jsonl | python3 -m json.tool

# 检查项目结构
ls -la ~/.claude/projects/ | head -20
```
