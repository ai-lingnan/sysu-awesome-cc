---
name: cc-insights
description: This skill should be used when the user asks to "归档聊天记录", "archive my chats", "分析我与CC的交互", "analyze my Claude Code usage", "反思我的CC使用习惯", "生成CC洞察报告", "深度分析CC使用模式", "更新聊天归档", or mentions keywords like "交互日志", "使用模式分析", "CC insights", "deep analysis". Provides automated archiving and deep analysis of Claude Code interaction history.
version: 3.0.0
---

# CC Insights

Automated archiving and deep analysis of Claude Code interaction history.

## Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Archive   │ ──► │   Analyze   │ ──► │  Ask User   │ ──► │   Report    │
│   Chats     │     │   Patterns  │     │  (2 phases) │     │   + Summary │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## Path Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `[ARCHIVE_ROOT]` | Where archives are saved | Run `archive_chats.py` to see output path |
| `<skill_root>` | This skill's directory | Directory containing this SKILL.md |
| `[TIME_FILTER]` | Time range parameter | See `references/time_filter_guide.md` |

## Standard Workflow

```
User: "归档并分析我的CC聊天记录"
```

1. Run `archive_chats.py` to convert JSONL → Markdown (note the output path as `[ARCHIVE_ROOT]`)
2. Run `analyze_patterns.py` to extract patterns
3. **Offer analysis options** via AskUserQuestion (2 phases)

## Post-Archiving Analysis Menu

**After archiving**, offer options using AskUserQuestion in two phases:

### Phase 1: Time Range (Parameter)

Time range is a **parameter**, not an agent set. It filters all subsequent analysis.

| Selection | `[TIME_FILTER]` Value | `[TIME_SUMMARY_PREFIX]` |
|-----------|----------------------|-------------------------|
| 全量分析 (All) | `from all available history` | `基于全部历史数据分析` |
| 近月分析 (30d) | `from the last 30 days only` | `基于近30天数据分析` |
| 本周分析 (7d) | `from the last 7 days only` | `基于近7天数据分析` |

### Phase 2: Analysis Dimensions (Agent Set)

Each dimension launches its own set of agents, all receiving the time filter.

| Selection | Reference File | Agents |
|-----------|----------------|--------|
| 多维度深度分析 | `references/deep_analysis_agents.md` | 7 |
| 人工干预分析 | `references/human_input_analysis.md` | 5 |
| 模式归类 | `references/pattern_grouping.md` | 5 |

### AskUserQuestion Template

```yaml
questions:
  - question: "归档完成！选择时间范围分析？"
    header: "时间范围"
    multiSelect: false
    options:
      - label: "全量分析 (All)"
        description: "分析所有历史交互，总结模式，提出改进建议"
      - label: "近月分析 (30d)"
        description: "分析近30天交互模式和使用习惯"
      - label: "本周分析 (7d)"
        description: "分析近7天交互，适合周度复盘"
  - question: "选择分析维度？"
    header: "分析维度"
    multiSelect: true
    options:
      - label: "多维度深度分析"
        description: "7个领域专项agent并行分析（技能开发、知识管理、内容创作等）"
      - label: "人工干预分析"
        description: "分析首次任务后的用户介入，识别改进点"
      - label: "模式归类"
        description: "识别重复输入，建议创建command/skill/agent"
```

## Required Permissions

Before running this skill, ensure these paths are in `~/.claude/settings.json` under `permissions.allow`:

```json
"permissions": {
  "allow": [
    "Read(~/.claude/skills/cc-insights/**)",
    "Read(~/ClaudeCodeArchive/**)",
    "Read(~/SynologyDrive/ClaudeCodeArchive/**)"
  ]
}
```

## Execution Logic

Based on user selections:

1. **Extract time range** from Phase 1 selection
2. **Read `references/time_filter_guide.md`** to get `[TIME_FILTER]` and `[TIME_SUMMARY_PREFIX]` values
3. **For each selected dimension** in Phase 2:
   - Read the corresponding reference file
   - **Replace `[TIME_FILTER]`** in all agent prompts with the time filter value
   - **Replace `[ARCHIVE_ROOT]`** with the actual archive path
   - Launch all agents in parallel using Task tool with `subagent_type=Explore`
   - **CRITICAL**: Prefix each agent prompt with:
     ```
     IMPORTANT: Only use Read, Glob, and Grep tools. Do NOT use any browser, web, or network tools.
     You have permission to read all files under [ARCHIVE_ROOT].
     ```
4. **Synthesize results** into a single report
5. **Apply output naming** based on time range (see `time_filter_guide.md`)

### Example: User selects "本周分析 (7d)" + "多维度深度分析"

1. `[TIME_FILTER]` = `from the last 7 days only`
2. `[TIME_SUMMARY_PREFIX]` = `基于近7天数据分析`
3. Read `references/deep_analysis_agents.md`
4. For each of the 7 agent prompts, replace `[TIME_FILTER]` with the filter value
5. Launch 7 agents (all filtered to last 7 days)
6. Output file: `CC_Weekly_MultiDim_YYYYMMDD.md`

## Scripts Reference

Scripts are in `scripts/` subdirectory relative to this SKILL.md.

```bash
python3 <skill_root>/scripts/<script_name>.py [OPTIONS]
```

### archive_chats.py

| Option | Description |
|--------|-------------|
| `--full` | Include tool call details |
| `--project NAME` | Filter by project name |
| `--since YYYY-MM-DD` | Archive only after date |
| `--output DIR` | Custom output directory (see script for default) |

### analyze_patterns.py

| Option | Description |
|--------|-------------|
| `--output FILE` | Save JSON to file |
| `--pretty` | Pretty-print JSON |

### generate_insights.py

| Option | Description |
|--------|-------------|
| `--analysis FILE` | Input analysis JSON |
| `--output FILE` | Output Markdown path |

## Additional References

- `references/time_filter_guide.md` - Time parameter values and output naming
- `references/deep_analysis_agents.md` - 7 domain-specific agents
- `references/human_input_analysis.md` - 5 intervention analysis agents
- `references/pattern_grouping.md` - 5 pattern mining agents
- `references/workflow.md` - Automation setup, cron jobs, best practices
