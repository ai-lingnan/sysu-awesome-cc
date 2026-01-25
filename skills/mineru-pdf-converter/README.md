# 📄 MinerU PDF 转换器

> 使用 MinerU 云端 API 将 PDF 转换为高质量 Markdown 的 Claude Code 技能

## 🎯 功能简介

- 将 PDF 转换为 Markdown，保留公式、表格、图片
- 支持本地文件和 URL
- 自动处理大文件（>600 页自动拆分）

## 🔑 配置 API Token

### 第一步：注册 MinerU 账号

1. 访问 [mineru.net](https://mineru.net)
2. 注册并登录账号

### 第二步：获取 API Token

1. 登录后进入个人中心/开发者设置
2. 找到 API Token 或 Access Token
3. 复制你的 Token

### 第三步：填写 Token

打开以下文件：

```
~/.claude/skills/mineru-pdf-converter/references/mineru-token.md
```

将 `YOUR_TOKEN_HERE` 替换为你的实际 Token：

```markdown
# MinerU API Token

Store your MinerU API token in the code block below.

## Token

​```text
eyJhbGciOiJIUzI1NiIsInR5cCI6...你的实际Token...
​```
```

> ⚠️ **注意**：Token 会过期，如果遇到 401 错误，需要重新获取并更新。

## 🚀 如何使用

配置好 Token 后，在 Claude Code 中直接说：

- "用 MinerU 转换这个 PDF：/path/to/file.pdf"
- "PDF转Markdown：/path/to/document.pdf"
- "/mineru /path/to/paper.pdf"
- "转换 PDF https://example.com/paper.pdf"

Claude Code 会自动调用此技能完成转换。

## 📊 API 配额

- 每天 2000 页（高优先级）
- 超出后仍可使用，但处理速度较慢

## ❓ 常见问题

| 问题 | 解决方案 |
| ---- | -------- |
| 401 认证失败 | Token 过期，重新获取并更新 |
| 转换超时 | 文件较大，稍后重试 |
| 429 频率限制 | 今日配额用完，明天再试 |

---

Made with ❤️ for Claude Code
