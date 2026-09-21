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

## Pre-commit Sanitization Check（提交前脱敏检查）

新增或更新 agent / command / skill 时，提交前检查内容与附带文件里有没有不该公开的信息。
本仓库是公开仓库，推上去的东西会留在 git 历史里。

**要清理的**：

- 服务器与网络：公网/内网 IP、主机名、SSH 用户名与端口、内部域名、NAS 或 VPS 地址
- 凭据：密码、API key、token、私钥、`.env`、证书文件、数据库连接串、cookie / session
- 个人电脑专有路径：`/Users/<用户名>/...`、Synology Drive 等同步盘目录、本机 conda 环境绝对路径
- 个人信息：邮箱、手机号、工号学号、他人姓名
- 附带产物：脚本里写死的凭据、日志、缓存、截图和测试数据里的敏感内容

**怎么改**：

- 真实值换占位符（`<YOUR_SERVER_IP>`、`$API_KEY`、`~/path/to/project`），在 README 或 SKILL.md 里说明怎么填
- 凭据从环境变量或本地配置文件读，配置文件不进仓库，写进 `.gitignore`
- 路径用相对路径或 `~`，不写具体用户名

**提交前扫一遍**：

```bash
git diff --cached | grep -inE '(password|passwd|secret|token|api[_-]?key|private[_-]?key|ssh-rsa|BEGIN [A-Z ]*PRIVATE KEY|/Users/[a-z]|[0-9]{1,3}(\.[0-9]{1,3}){3})'
```

**已经推上去了**：先改密钥、换密码、吊销 token，再清理文件。从当前文件里删掉不等于没泄露——
历史记录和已有的 clone、fork 里还在。
