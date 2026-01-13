# Pattern Grouping Analysis

Identify repeated user inputs that could be consolidated into reusable commands, skills, or agents.

**Time Filter**: All agents respect the `[TIME_FILTER]` parameter. Replace with user's time selection before launching.

**Tool Constraints**: Each agent prompt MUST include this prefix:
```
IMPORTANT: Only use Read, Glob, and Grep tools. Do NOT use any browser, web, or network tools.
```

## Parallel Agents (5)

Launch these agents simultaneously using Task tool with `subagent_type=Explore`:

### Agent 1: Exact Pattern Finder
```
Search archives [TIME_FILTER] for near-exact repeated inputs:

1. Extract all user inputs from sessions within the time criteria
2. Find inputs that are:
   - Exact duplicates
   - Slight variations (same intent)
   - Template-like patterns
3. Return grouped patterns with frequency counts
```

### Agent 2: Semantic Pattern Finder
```
Search archives [TIME_FILTER] for semantically similar inputs:

1. Sample user inputs within the time criteria across projects
2. Group by semantic intent:
   - File operations (create, edit, move)
   - Git operations (commit, push, PR)
   - Analysis requests
   - Generation requests
   - Review/improve requests
3. Return semantic pattern groups
```

### Agent 3: Command Candidate Generator
```
Generate command candidates from patterns [TIME_FILTER]:

1. For each high-frequency pattern within the time criteria
2. Design:
   - Command name and syntax
   - Arguments needed
   - Expected behavior
   - Frontmatter template
3. Return command specification drafts
```

### Agent 4: Skill Candidate Generator
```
Generate skill candidates from complex patterns [TIME_FILTER]:

1. For patterns within the time criteria involving:
   - Multi-step workflows
   - Domain expertise
   - Repeated context needs
2. Design:
   - Skill scope and purpose
   - Resources needed (scripts, references)
   - Trigger conditions
3. Return skill specification drafts
```

### Agent 5: Agent Candidate Generator
```
Generate agent candidates from autonomous patterns [TIME_FILTER]:

1. For patterns within the time criteria that:
   - Require exploration
   - Need parallel processing
   - Involve research tasks
2. Design:
   - Agent type and purpose
   - Tools needed
   - System prompt outline
3. Return agent specification drafts
```

## Output Specification

**File Output**: See `time_filter_guide.md` for naming by time range

**Report Structure**:
- Pattern Frequency Report
- Top 20 Repeatable Patterns
- Command Candidates (Ready to Create)
- Skill Candidates (Ready to Create)
- Agent Candidates (Ready to Create)
- Priority Creation Roadmap

**User Summary**:
```
✓ 模式归类分析完成！报告已保存至 [路径]

[TIME_SUMMARY_PREFIX] 发现可复用模式：
- 高频模式: [N] 个 (出现 5+ 次)
- 中频模式: [M] 个 (出现 3-4 次)

推荐创建：
- Commands: [数量] 个候选 (e.g., [示例命令名])
- Skills: [数量] 个候选 (e.g., [示例skill名])
- Agents: [数量] 个候选 (e.g., [示例agent名])

优先创建: [Top 1推荐及简要理由]
```
