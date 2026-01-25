## Project Overview

This is a collection of Claude Code plugins (agents, commands, skills) maintained by faculty and students at Sun Yat-sen University Lingnan College.

## Repository Structure

- **agents/**: Subagent definitions (Task tool `subagent_type` targets)
  - `paper-reviewer.md` - Economics paper referee reports
  - `web-researcher.md` - Structured web research with source verification

- **commands/**: Slash commands (`/command-name`)
  - `multi-agent.md` - Multi-agent orchestration with context protection

- **skills/**: Skills with supporting scripts and references
  - `fetch4ai/` - Web content extraction via crawl4ai
  - `md-to-docx/` - Markdown to Word conversion with Chinese formatting
  - `mineru-pdf-converter/` - PDF to Markdown via MinerU cloud API
  - `marp-slides-creator/` - Presentation creation with themed templates
  - `cc-insights/` - Chat history analysis and archiving
  - `chat-history-summarizer/` - Session documentation export
  - `chinese-quote-converter/` - English to Chinese quotation mark conversion
  - `web-research/` - Multi-agent research workflow

## Plugin Component Patterns

### Agent Definition (agents/*.md)
```yaml
---
name: agent-name
description: |
  When to use this agent...
model: opus  # optional: sonnet, opus, haiku
---
# Agent instructions...
```

### Command Definition (commands/*.md)
```yaml
---
description: What the command does
argument-hint: [expected-args]
---
Instructions using $ARGUMENTS placeholder...
```

### Skill Definition (skills/*/SKILL.md)
```yaml
---
name: skill-name
description: Trigger phrases for this skill...
version: x.y.z
allowed-tools: Bash, Read, Write
---
# Skill instructions and usage examples...
```

## Development
- Update @README.md and this @CLAUDE.md whenever a new plugin/command/skill is added.
- Do not add Claude/Claude Code/Claude models as a contributor in git commits.