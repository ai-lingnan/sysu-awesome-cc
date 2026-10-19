---
name: deepseek-web
description: "Use when 要联网查最新数据、新闻、官方公告，或读某个网页的正文。用 DeepSeek 官方 Search／Fetch 接口（与 DeepSeek 对话 API 同一个 Key），国内网络可用；先搜索找出处，再读原文核对数字，回答附链接和发布日期。"
platforms: [macos, windows]
tags: [web, search]
---

# DeepSeek 联网搜索与读网页

用 DeepSeek 官方的两个接口：

- **Search**（`https://api.deepseek.com/v1/tools/search`）：按关键词返回标题、链接、摘要、发布时间、权威度。
- **Fetch**（`https://api.deepseek.com/v1/tools/fetch`）：给一个网址，返回标题和 Markdown 正文。

两个接口与 DeepSeek 对话 API 用同一个 Key，国内网络直连可用。本技能是课程自建的，DeepSeek 没有发布官方技能；脚本 `scripts/ds_web.py` 只用 Python 标准库。

## 第 0 步：检查 Key（每个会话第一次用之前）

```bash
python3 "<SKILL_DIR>/scripts/ds_web.py" check        # Windows：py "<SKILL_DIR>\scripts\ds_web.py" check
```

它用 DeepSeek 的余额接口验证 Key，不计费。第一行是结论：

- `KEY_OK`：可以用，直接往下做。
- `KEY_MISSING` 或 `KEY_INVALID`：把脚本打印的引导原样转告用户，然后停下等用户配好。引导内容是：到 https://platform.deepseek.com/api_keys 用手机号登录、创建 API Key、确认账户有余额；再由用户本人在终端运行 `ds_web.py setup` 粘贴 Key（输入不显示），脚本验证后写进本机环境变量；最后重启 Claude Code 或 WorkBuddy。不要让用户把 Key 发给你，也不要替用户运行 setup。
- `NO_BALANCE`：告诉用户 Key 有效但余额不足，充值后继续。

用户说配好了，再运行一次 `check`，`KEY_OK` 再开始任务。

## 先判断用户要什么

- 问一个最新的数（CPI、利率、政策发布日期等）：先 `search` 找出处，再 `fetch` 打开原文核对，回答给数字、原文链接、发布日期。
- 给了一个网址，要读或要总结：直接 `fetch`，存成 Markdown，再按用户要求总结或摘数。
- 要找一类资料：`search` 多给几条，按来源权威度和日期排好，列给用户。

按最合理的理解直接做，不追问。回答里写清每个数字来自哪个链接。

## 运行命令

`<SKILL_DIR>` 换成本技能所在文件夹。

macOS：

```bash
python3 "<SKILL_DIR>/scripts/ds_web.py" search "国家统计局 居民消费价格 最新" --count 5 --out search.json
python3 "<SKILL_DIR>/scripts/ds_web.py" fetch "https://www.stats.gov.cn/sj/zxfb/..." --out page.md
```

Windows（PowerShell）：

```powershell
py "<SKILL_DIR>\scripts\ds_web.py" search "国家统计局 居民消费价格 最新" --count 5 --out search.json
py "<SKILL_DIR>\scripts\ds_web.py" fetch "https://www.stats.gov.cn/sj/zxfb/..." --out page.md
```

没有 `py` 就用 `python`。

- `search` 支持搜索语法：`site:stats.gov.cn`、`after:2026-09-01`、`lang:zh`、`"精确短语"`。
- `--out` 把结果存进当前项目；屏幕上只打印摘要。
- 脚本对临时失败自动重试两次（Fetch 第一次偶尔返回“取不到可用内容”，重试通常就好）。

## 怎样用结果

1. 从 `search` 结果里挑权威来源：政府网站、官方机构优先，`authority` 越高越可靠；记下标题、链接、日期。
2. 对选中的链接 `fetch`，在正文里找到那个数字再下结论，不凭摘要回答。
3. 政府网站的“最新发布”列表页是动态加载的，`fetch` 只能取到页脚；改为 `fetch` 具体那篇发布稿的网址（从 `search` 结果里拿）。

## 配置 Key 的细节（setup 做了什么）

`setup` 先用余额接口验证 Key，能用才保存：

- macOS：`launchctl setenv DEEPSEEK_API_KEY`，并在 `~/Library/LaunchAgents/` 放一个只有本人可读的启动项，重启电脑后自动恢复。
- Windows：`setx DEEPSEEK_API_KEY`，写进用户环境变量。

已经在 CC Switch 里配了 DeepSeek 的，也要跑一次 `setup`：CC Switch 只把 Key 交给 Claude Code 调模型，技能脚本读的是环境变量。

## 常见报错

| 报错 | 原因 | 处理 |
| --- | --- | --- |
| `KEY_MISSING` | 环境变量没配，或配了没重启客户端 | 按第 0 步引导用户运行 `setup`，重启客户端 |
| `HTTP 401 Key 无效` | Key 抄错或已删除 | 在 DeepSeek 开放平台重新生成 |
| `HTTP 402 账户余额不足` | 余额用完 | 充值后再试 |
| `HTTP 404 取不到可用内容` | 网页打不开或是动态页 | 换具体文章的网址；仍不行就用浏览器工具打开 |
| `HTTP 429` | 每个账号每秒最多 5 次 | 脚本已自动等待重试；批量时放慢 |
| `网络错误` | 断网或代理干扰 | 国内网络直连即可，关掉全局代理再试 |

## 费用

按成功请求计费，Search、Fetch 各约每千次 5 元（以 DeepSeek 官方文档为准）；读回的正文交给模型总结时，模型 Token 另计。
