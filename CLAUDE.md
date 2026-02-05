## Project Overview

This is a collection of Claude Code plugins (agents, commands, skills) maintained by faculty and students at Sun Yat-sen University Lingnan College.

## Repository Structure

- **agents/**: Subagent definitions (Task tool `subagent_type` targets)

- **commands/**: Slash commands (`/command-name`)

- **skills/**: Skills with supporting scripts and references

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