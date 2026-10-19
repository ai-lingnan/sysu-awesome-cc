---
name: media-save
description: "把公开的微信公众号文章和抖音视频存到本地。用户给出 mp.weixin.qq.com 文章链接，或 v.douyin.com / douyin.com 视频链接（含整段分享文字）时使用：公众号存成 Markdown + 图片，抖音存成 MP4，并记录出处。"
platforms: [macos, windows]
tags: [wechat, douyin, archive]
---

# 公众号文章与抖音视频存档

## 先判断用户要什么

用户给一个或几个链接就够了，按最合理的理解直接做，不追问：

| 用户的话 | 做什么 |
|---|---|
| 只给链接，或说“存一下”“下载” | 存档，结尾报产物位置 |
| “这篇讲了什么”“帮我总结” | 先存档，再读 `article.md` 给要点 |
| “把数据／表格摘出来” | 先存档，再从 `article.md` 提取，整理成表格 |
| 视频“讲了什么”“要文字稿” | 先存档，再说明本技能不转文字，可把 `video.mp4` 交给课程里的语音转写工具 |

保存位置固定为当前项目下的 `资料/公众号/` 和 `资料/抖音/`，不让用户选。脚本自动从页面取作者、标题、发布时间并核对，网络抖动自动重试。一次给多个链接就一次传给 `save.py`，最后汇总。

## 按链接分平台

| 链接里的域名 | 平台 | 脚本 |
|---|---|---|
| `mp.weixin.qq.com` | 公众号 | `scripts/wechat_save.py` |
| `v.douyin.com`、`douyin.com`、`iesdouyin.com` | 抖音 | `scripts/douyin_save.py` |
| 其他（B 站、小红书、视频号等） | 不支持 | 告诉用户本技能只处理公众号和抖音，停下 |

`scripts/save.py` 按域名自动分派，平时只用它。

## 运行命令

下文 `<SKILL_DIR>` 指本 SKILL.md 所在目录，`<PY>` 指 Python 3.10 及以上的解释器。脚本只用标准库，不装任何包。在用户的项目目录里运行（产物写到运行目录下的 `资料/`）。

macOS：

```bash
python3 --version            # 3.10 及以上即可，<PY> 就写 python3
python3 "<SKILL_DIR>/scripts/save.py" "<链接或整段分享文字>" ["<链接2>" ...]
```

Windows（PowerShell）：

```powershell
py -3 --version              # 3.10 及以上即可，<PY> 就写 py -3
$env:PYTHONUTF8 = 1          # 避免控制台中文乱码
py -3 "<SKILL_DIR>\scripts\save.py" "<链接或整段分享文字>" ["<链接2>" ...]
```

链接里有 `&`，整段加引号。没有 Python 或版本低于 3.10：macOS 从 https://www.python.org/downloads/macos/ 装 3.13 并运行 `Install Certificates.command`；Windows 运行 `winget install -e --id Python.Python.3.13 --scope user`，装完重开终端。

每个链接输出一行 `RESULT: <结论> <目录或原因>`，按结论处理：

| 结论 | 处理 |
|---|---|
| `OK` | 完成，读该目录下的 `source.json` 做验收 |
| `NEED_BROWSER` | 不请示，改用浏览器读取：公众号见“脚本取不到时：用浏览器读”，抖音见“浏览器路线” |
| `NEED_HUMAN` | 要登录或要人完成验证：用一句话告诉用户要做什么，停下 |
| `UNAVAILABLE` | 文章已删除、被屏蔽或链接无效，告诉用户原因 |
| `UNSUPPORTED` | 图文作品、私密作品或不支持的平台，告诉用户原因 |
| `ERROR` | 按下方常见报错处理；网络类错误等一分钟重跑一次 |

## 公众号

产物：`资料/公众号/<发布日期>_<标题>/`

- `article.md`：标题、公众号、作者、发布时间、原文链接，然后是正文。图片写成 `![图01](images/01.jpg)`，原文嵌入视频的位置写 `[原文此处嵌入视频]`（视频本身不下载）
- `images/`：按正文顺序编号 `01`、`02`……，扩展名按文件头判定的真实格式（jpg / png / gif / webp）
- `source.json`：`url`、`permanent_url`、`title`、`account`、`author`、`published_at`、`fetched_at`、`image_count`、`images_failed`、`embedded_videos_not_saved`、`text_chars`、`method`

验收：

1. `source.json` 里 `image_count` 等于 `image_refs_in_article`，`images_failed` 为空
2. 打开 `article.md`，标题、公众号名与原文一致，正文从头到尾连贯，没有“播放、倍速、全屏”之类播放器文字
3. 字数 `text_chars` 与原文篇幅相称（以图为主的海报类文章字数少属正常）

### 脚本取不到时：用浏览器读

结论是 `NEED_BROWSER` 时直接走这条路，不先问用户：

1. 用客户端自带的浏览器工具打开原链接
2. 在页面里执行 `scripts/browser_extract.js` 的全部内容，返回一段精简 HTML
3. 返回值以 `NO_JS_CONTENT` 开头、内容是“环境异常／完成验证”：停下，告诉用户“请在浏览器里打开这篇文章，点‘去验证’完成验证后告诉我”，用户回复后从第 1 步重来
4. 否则把返回的 HTML 原样存成临时文件（如 `资料/公众号/page.html`），运行：

```bash
<PY> "<SKILL_DIR>/scripts/wechat_save.py" "<原链接>" --from-html "资料/公众号/page.html"
```

成功后删掉临时文件。产物与直接抓取相同，`source.json` 的 `method` 为 `browser_html`。

### 常见报错

| 现象 | 原因 | 处理 |
|---|---|---|
| `NEED_BROWSER 微信返回了验证页` | 微信对脚本访问弹了验证，带 `__biz=` 但缺 `chksm=` 参数的长链接常见 | 走上面的浏览器路线；或请用户在微信里“复制链接”拿 `mp.weixin.qq.com/s/...` 短链再试 |
| `UNAVAILABLE 链接已过期` | 搜狗等搜索结果里的临时链接（含 `src=11&timestamp=`）几小时后失效 | 改用文章页的正式链接 |
| `UNAVAILABLE 参数错误` | 链接复制不全 | 让用户重新复制完整链接 |
| `images_failed` 不为空 | 个别图片下载超时 | 重跑一次（同一目录覆盖写入）；仍失败的图在正文里保留原图链接 |
| `SSL: CERTIFICATE_VERIFY_FAILED` | macOS 的 python.org 版 Python 没装证书 | 运行「应用程序 → Python 3.x → Install Certificates.command」 |
| `ProxyError`、连接超时 | 代理把国内网站绕到境外 | 关掉全局代理或改规则模式；清掉 `HTTP_PROXY`、`HTTPS_PROXY` 环境变量 |
| 中文乱码、`UnicodeEncodeError` | Windows 控制台 GBK 编码 | 先运行 `$env:PYTHONUTF8 = 1` |

## 抖音

两条路线，先快后慢，中间不请示：

1. 快速路线：`save.py` 先读抖音官方分享页 `https://www.iesdouyin.com/share/video/<作品ID>/?from_ssr=1` 里公开给出的数据，核对作品 ID、作者、标题后下载。分享页不给数据时结论是 `NEED_BROWSER`（2026-10 实测多数作品如此）。
2. 浏览器路线：用客户端自带的浏览器工具（WorkBuddy 内置浏览器、Playwright MCP、Playwright CLI、agent-browser 任选其一）：
   1. 打开用户给的分享链接（短链会自动跳到作品页），等页面渲染出视频
   2. 在页面里执行 `scripts/douyin_extract.js` 的全部内容。它最多等 15 秒，返回一段 JSON：`status`、`aweme_id`、`author`、`title`、`published`、`duration_s`、`media_urls`（`<video>` 的 currentSrc／source，或页面加载过的 douyinvod.com 媒体请求，只取这条作品的）
   3. 按 `status` 处理：`ok` 往下走；`verify` 停下，告诉用户“抖音要求验证，请在浏览器里完成验证后告诉我”；`login` 停下，告诉用户这条作品要登录才能看、本技能只处理公开作品；`note` 告诉用户这是图文作品；`no_video` 刷新页面再执行一次，仍没有就按 `ERROR` 报给用户
   4. 把返回的 JSON 原样存成临时文件（如 `资料/抖音/page.json`），运行下面的命令下载并写 `source.json`；成功后删掉临时文件

```bash
<PY> "<SKILL_DIR>/scripts/douyin_save.py" "<分享链接>" --from-json "资料/抖音/page.json"
```

也可以不存文件，逐项传参：`<PY> "<SKILL_DIR>/scripts/douyin_save.py" --media-url "<视频地址>" --author "<作者>" --title "<标题>" --published "<发布时间>" --page-url "<作品页地址>"`（`--media-url` 可给多个，依次尝试）。

以 agent-browser 为例（macOS 终端）：

```bash
agent-browser open "<分享链接>"
agent-browser eval --stdin < "<SKILL_DIR>/scripts/douyin_extract.js" > 资料/抖音/page.json
python3 "<SKILL_DIR>/scripts/douyin_save.py" "<分享链接>" --from-json 资料/抖音/page.json
```

Windows PowerShell 没有 `<` 重定向，第二行写成 `Get-Content "<SKILL_DIR>\scripts\douyin_extract.js" -Raw | agent-browser eval --stdin | Out-File -Encoding utf8 资料\抖音\page.json`。浏览器工具把返回值包成带引号的 JSON 字符串也没关系，脚本会自动解开。

产物：`资料/抖音/<作品ID>_<标题>/`

- `video.mp4`
- `source.json`：`aweme_id`、`share_url`、`canonical_url`、`author`、`title`、`published_at`、`fetched_at`、`duration_s_from_page`、`size_bytes`、`sha256`、`method`（`share_page` 或 `browser`）、`check`

`check` 里有 MP4 文件头和从文件头读出的时长 `duration_s_from_file`；电脑上有 `ffprobe` 时还有分辨率与编码。文件时长与页面时长相差超过 5 秒就报错停下。可选参数 `--expect-author "央视新闻"`：作者对不上就停下。

验收：

1. 双击 `video.mp4` 能播放，画面与分享卡片一致
2. `source.json` 的 `author`、`title` 与分享文字里的作者、标题对得上
3. `duration_s_from_file` 与页面时长接近，`size_bytes` 大于 0，`sha256` 是 64 位十六进制

### 常见报错

| 现象 | 原因 | 处理 |
|---|---|---|
| `NEED_BROWSER 官方分享页只返回了页面空壳` | 抖音把作品数据改由浏览器加载，分享页不再直接给出 | 走浏览器路线 |
| `NEED_BROWSER 官方分享页返回了人机校验页` | 短时间请求多了 | 走浏览器路线 |
| `douyin_extract.js` 返回 `verify` | 浏览器里弹出滑块等验证 | 请用户在浏览器里完成验证，再执行一次脚本 |
| `UNSUPPORTED 这是图文作品` | 链接指向图文（`/note/`） | 告诉用户本技能只下载视频 |
| `UNSUPPORTED 作品已删除或设为私密` | 作品不公开 | 告诉用户原因 |
| `ERROR 作者对不上` | 短链跳到了别的作品 | 请用户从原视频重新复制分享链接 |
| `ERROR 视频下载失败（HTTP 403）` | 视频地址有时效，过期了 | 重新打开页面、再执行一次 `douyin_extract.js` |
| `ERROR 时长对不上` | 拿到的是别的视频（例如推荐流里的下一条） | 重新打开作品页再取一次 |
| `ERROR 下载到的文件不是 MP4` | 拿到的是错误页 | 重新取地址再下 |

## 结尾

用一句话告诉用户做了什么、产物在哪，例如：“已存好《……》（统计微讯，2026-09-15），正文 2807 字、图片 1 张，在 `资料/公众号/2026-09-15_……/`。”多个链接时列一张简表：链接、结论、目录或原因。
