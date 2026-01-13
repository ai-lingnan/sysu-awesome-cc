# Human Input Analysis

Analyze WHY the user needed to intervene after the initial task request. Identify systematic improvement opportunities for skills, workflows, agents, and commands.

**Time Filter**: All agents respect the `[TIME_FILTER]` parameter. Replace with user's time selection before launching.

**Tool Constraints**: Each agent prompt MUST include this prefix:
```
IMPORTANT: Only use Read, Glob, and Grep tools. Do NOT use any browser, web, or network tools.
```

## Critical Focus

**Only analyze inputs AFTER the first task request in each session** - the first input is expected; subsequent inputs reveal improvement opportunities.

## Parallel Agents (5)

Launch these agents simultaneously using Task tool with `subagent_type=Explore`:

### Agent 1: Intervention Categorizer
```
Analyze human inputs [TIME_FILTER] (excluding first input per session) in [ARCHIVE_ROOT]/projects/:

1. Sample 30+ sessions with multiple user inputs within the time criteria
2. Categorize each post-first intervention:
   - Correction (Claude did wrong thing)
   - Clarification (Claude misunderstood)
   - Direction change (user changed mind)
   - Approval request (Claude asked, user answered)
   - Additional context (user provided more info)
   - Bug report (something broke)
3. Return categorized inventory with frequencies
```

### Agent 2: Skill Improvement Analyzer
```
From intervention patterns [TIME_FILTER], identify skill improvements:

1. Find interventions caused by skill limitations within the time criteria
2. Identify:
   - Skills that need better defaults
   - Skills missing important features
   - Skills that should ask more/fewer questions
   - New skills that could prevent interventions
3. Return skill improvement recommendations with priority
```

### Agent 3: Workflow Gap Analyzer
```
Identify workflow gaps [TIME_FILTER] from intervention patterns:

1. Find interventions caused by workflow issues within the time criteria
2. Identify:
   - Missing intermediate steps
   - Wrong sequence of operations
   - Missing validation checkpoints
   - Workflows that should be skills/commands
3. Return workflow improvement recommendations
```

### Agent 4: Command/Agent Opportunity Finder
```
Identify opportunities for new commands or agents [TIME_FILTER]:

1. Find repeated intervention patterns within the time criteria
2. Identify:
   - Sequences that could be single commands
   - Complex tasks that need specialized agents
   - Repeated context provisions that could be automated
3. Return command/agent creation recommendations with templates
```

### Agent 5: Root Cause Synthesizer
```
Synthesize root causes of interventions [TIME_FILTER]:

1. Review all intervention categories within the time criteria
2. Identify systemic issues:
   - Context provision problems
   - Instruction clarity issues
   - Tool limitation patterns
   - Expectation mismatches
3. Return root cause analysis with systemic fixes
```

## Output Specification

**File Output**: See `time_filter_guide.md` for naming by time range

**Report Structure**:
- Intervention Category Distribution
- Top 10 Intervention Patterns
- Skill Improvements (Prioritized)
- Workflow Improvements
- New Command/Agent Proposals
- Systemic Root Causes
- Action Plan

**User Summary**:
```
✓ 人工干预分析完成！报告已保存至 [路径]

[TIME_SUMMARY_PREFIX] 干预模式分布：
- 纠正类: [X]%  | 澄清类: [Y]%  | 补充信息: [Z]%

Top 3 改进机会：
1. [Skill/Workflow名]: [简述问题和建议]
2. [Skill/Workflow名]: [简述问题和建议]
3. [新增建议]: [简述内容]

详细报告含 [N] 个干预模式分析，[M] 条改进建议。
```
