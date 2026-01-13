---
name: chat-history-summarizer
description: Extract and summarize Claude Code chat history into structured documentation. Use when the user asks to export, summarize, or document a conversation session, extract prompts and actions from chat logs, or create a record of what was accomplished in a session.
---

# Chat History Summarizer

## Overview

This skill extracts user prompts and Claude's actions from Claude Code conversation logs, generating a concise, structured summary document. It's useful for:

- Documenting what was accomplished in a session
- Creating a record for future reference or handoff
- Reviewing methodology and approach taken
- Learning from past interactions

## Prerequisites

Install the claude-conversation-extractor tool:

```bash
pip install claude-conversation-extractor
```

## Workflow

### Step 1: List Available Sessions

```bash
claude-extract --list
```

This shows all available sessions with:
- Session ID
- Project folder
- Modification date
- Message count
- Size
- Preview of first message

### Step 2: Search for Specific Session (Optional)

```bash
claude-extract --search "keyword"
```

Search by keyword to find relevant sessions.

### Step 3: Export the Session

```bash
# Basic export
claude-extract --extract <session_number>

# Detailed export (includes tool outputs)
claude-extract --extract <session_number> --detailed

# Export as HTML
claude-extract --format html --extract <session_number>
```

Default output location: `~/Desktop/Claude logs/`

### Step 4: Generate Summary

Read the exported file and create a structured summary with:

1. **Session Metadata**
   - Session ID
   - Date
   - Total message count

2. **User Inputs & Claude Actions** (organized by interaction rounds)
   - Each user prompt (quoted)
   - Concise summary of Claude's actions (tools used, files created/modified)

3. **Generated Files List** (if applicable)
   - File paths and descriptions

4. **Tool Usage Statistics** (optional)
   - Tools used and frequency

5. **Key Outcomes** (optional)
   - Main deliverables or conclusions

## Output Template

```markdown
# [Session Title/Topic]

**Session ID:** [id]
**Date:** [date]
**Total Messages:** [count]

---

## User Inputs & Claude Actions Summary

### Round 1: [Brief Title]

**User Input:**
> [Exact user prompt, quoted]

**Claude Actions:**
1. [Action 1 - tool used, brief description]
2. [Action 2 - tool used, brief description]
3. [Files created/modified if any]

---

### Round 2: [Brief Title]
...

---

## Generated Files

| File | Path | Description |
|------|------|-------------|
| [name] | [path] | [brief description] |

---

## Tool Usage Statistics

| Tool | Count | Purpose |
|------|-------|---------|
| [tool] | [n] | [main use] |

---

*Summary extracted from conversation log on [current date]*
```

## Key Principles

1. **Quote user inputs exactly** - Preserve the user's original wording
2. **Be concise on Claude actions** - Focus on what was done, not how
3. **Group by interaction rounds** - Each user input starts a new round
4. **Highlight key deliverables** - Files created, reports generated, etc.
5. **Skip warmup/system messages** - Only include substantive exchanges

## Extracting from Raw Logs

When reading exported markdown files:

1. Look for `## 👤 User` markers to identify user inputs
2. Look for `## 🤖 Claude` markers for Claude responses
3. Look for `🔧 Using tool:` to identify tool usage
4. Ignore:
   - System reminders (`<system-reminder>`)
   - Warmup messages
   - Agent internal messages
   - Tool input/output details (unless specifically relevant)

## Example Search Patterns

```bash
# Find user messages
grep -n "## 👤 User" exported-log.md

# Find tool usage
grep -n "🔧 Using tool:" exported-log.md

# Find Write operations (files created)
grep -n "Using tool: Write" exported-log.md
```

## Tips

- For very long sessions, focus on key milestones rather than every exchange
- Group related exchanges into logical "rounds" even if interrupted
- Note when context was compacted or session was continued
- Include any user choices/preferences that shaped the outcome
