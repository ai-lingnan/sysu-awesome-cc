# Multi-dimensional Deep Analysis

7 domain-specific agents analyze CC interaction patterns in parallel.

**Time Filter**: All agents respect the `[TIME_FILTER]` parameter. Replace with user's time selection before launching.

**Tool Constraints**: Each agent prompt MUST include this prefix:
```
IMPORTANT: Only use Read, Glob, and Grep tools. Do NOT use any browser, web, or network tools.
```

## Agent 1: Skill Development Patterns

```
Analyze Claude Code chat archives [TIME_FILTER] in [ARCHIVE_ROOT]/projects/claude_skill_make/sessions/ to understand skill development patterns:

1. Read 5-8 session files matching the time criteria
2. Identify:
   - What skills were developed
   - The iterative refinement process
   - Common patterns in skill design requests
   - Time investment patterns
3. Return a structured summary of skill development methodology and insights
```

## Agent 2: Knowledge Management Patterns

```
Analyze Claude Code chat archives [TIME_FILTER] in [ARCHIVE_ROOT]/projects/obsidian_NewNote_NewNote/sessions/ and [ARCHIVE_ROOT]/projects/NewNote/sessions/ to understand knowledge management patterns:

1. Read session files matching the time criteria
2. Identify:
   - How the Obsidian vault evolved
   - Types of notes created
   - Linking patterns
   - AI-native note-taking workflows
3. Return a summary of knowledge management methodology
```

## Agent 3: Content Creation Workflow

```
Analyze Claude Code chat archives [TIME_FILTER] in [ARCHIVE_ROOT]/projects/PythonProjects_wechat_blog/sessions/ to understand WeChat article writing workflow:

1. Read session files matching the time criteria
2. Identify:
   - Article creation workflow
   - Research integration patterns
   - Image generation usage
   - Target audience considerations
3. Return a summary of content creation methodology
```

## Agent 4: Teaching Content Patterns

```
Search for teaching-related sessions [TIME_FILTER] in [ARCHIVE_ROOT]/projects/ directories containing "2025", "讲义", or teaching-related terms:

1. Find and read 5-8 teaching-related session files within the time criteria
2. Identify:
   - Types of teaching content created
   - Lecture note generation workflow
   - Course material synthesis methods
   - Multi-source integration patterns (recordings + slides)
3. Return a summary of teaching content creation methodology
```

## Agent 5: Academic Writing Patterns

```
Search for research-related sessions [TIME_FILTER] in [ARCHIVE_ROOT]/projects/ directories containing "Research", "Narratives", "copy_edit", or academic terms:

1. Find and read 5-8 research/academic writing session files within the time criteria
2. Identify:
   - Paper editing workflows
   - Multi-stage editing process
   - Human-in-the-loop decision points
   - Git integration for academic writing
3. Return a summary of academic writing methodology
```

## Agent 6: Prompt Engineering Patterns

```
Search across session files [TIME_FILTER] in [ARCHIVE_ROOT]/projects/ to identify unique prompt engineering patterns:

1. Sample 10-15 sessions within the time criteria across different projects
2. Identify:
   - Common prompt structures
   - Use of path specifications
   - Declarative vs procedural instructions
   - Context provision patterns
   - Human-in-the-loop checkpoints
3. Return a summary of prompt engineering style and best practices
```

## Agent 7: Time & Productivity Patterns

```
Analyze the timeline data [TIME_FILTER] in [ARCHIVE_ROOT]/timeline/ and project modification dates:

1. Read timeline index files within the time criteria
2. Analyze:
   - Project sprint patterns (concentrated work periods)
   - Seasonal/weekly patterns
   - Project switching frequency
   - Long sessions vs short sessions distribution
3. Return insights about work rhythm and productivity patterns
```

## Report Synthesis Template

After all agents complete, synthesize findings into:

```markdown
---
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - type/reflection
  - status/active
  - AI/interaction-analysis
aliases: [CC交互反思, Claude Code使用模式]
---

# Claude Code 多维度分析

> [TIME_SUMMARY_PREFIX] [N] 个会话、[M] 个项目的分析
> 更新于 YYYY-MM-DD

## 一、用户画像
[From prompt engineering agent + overall synthesis]

## 二、交互风格
[From prompt engineering agent]

## 三、任务分布图谱
[From quantitative analysis + all domain agents]

## 四、独特的交互模式
[From all agents - common patterns]

## 五、时间与节奏模式
[From time patterns agent]

## 六、深层洞察
[Synthesis of key insights from all agents]

## 七、项目活跃度
[From quantitative analysis]

## 八、启示与建议
[Actionable recommendations from all agents]

## Related
- [[CC_Insights_YYYYMMDD]]
- [[Personal Profile]]
- [[Research Status]]

## Source
[Data sources and agent contributions]
```

## Output Specification

**File Output**: See `time_filter_guide.md` for naming by time range

**User Summary**:
```
✓ 多维度深度分析完成！报告已保存至 [路径]

[TIME_SUMMARY_PREFIX]:
- 技能开发: [关键发现]
- 知识管理: [关键发现]
- 内容创作: [关键发现]
- 教学内容: [关键发现]
- 学术写作: [关键发现]
- 提示工程: [关键发现]
- 时间模式: [关键发现]

综合洞察: [1-2句核心发现]
建议: [1-2个action items]

详细报告含各领域完整分析。
```
