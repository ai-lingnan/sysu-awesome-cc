#!/usr/bin/env python3
"""把一篇公开的微信公众号文章存成本地 Markdown + 图片（只用 Python 标准库，Python >= 3.10）。

用法（<PY> 换成你的 Python：macOS 一般是 python3，Windows 是 py 或 python）：
  <PY> wechat_save.py "https://mp.weixin.qq.com/s/xxxx"
  <PY> wechat_save.py "<链接>" --out 资料              输出根目录，默认 ./资料
  <PY> wechat_save.py "<链接>" --from-html page.html   脚本取不到页面时，用浏览器存下来的 HTML 继续

产物：<out>/公众号/<发布日期>_<标题>/article.md、images/、source.json
最后一行是结论：
  RESULT: OK <目录>
  RESULT: NEED_BROWSER <原因>     脚本拿不到正文，改用浏览器读页面后走 --from-html
  RESULT: UNAVAILABLE <原因>      文章已删除、违规屏蔽或链接无效，浏览器也打不开
  RESULT: ERROR <原因>
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

for _s in (sys.stdout, sys.stderr):  # Windows 控制台默认 GBK，统一 UTF-8 输出
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
REFERER = "https://mp.weixin.qq.com/"
CST = timezone(timedelta(hours=8))
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "source", "track", "wbr", "param"}
BLOCK = {"p", "div", "section", "article", "header", "footer", "figure", "figcaption",
         "blockquote", "ul", "ol", "li", "table", "tr", "h1", "h2", "h3", "h4", "h5", "h6",
         "pre", "hr", "center"}
VIDEO_TAGS = {"iframe", "video", "mpvideosnap", "mp-common-videosnap", "mpvideo",
              "mp-common-video", "mp-video"}
SKIP_TAGS = {"script", "style", "noscript", "svg", "mp-common-profile", "mpprofile",
             "mp-miniprogram", "mpvoice", "mp-common-mpaudio", "qqmusic", "mpcps",
             "mp-common-product", "button", "input", "textarea", "select"}
VIDEO_MARK = "[原文此处嵌入视频]"


class StopError(Exception):
    def __init__(self, kind: str, reason: str):
        super().__init__(reason)
        self.kind, self.reason = kind, reason


# ---------------------------------------------------------------- 网络
def http_get(url: str, *, referer: str | None = None, attempts: int = 4, timeout: int = 30) -> tuple[bytes, str, str]:
    """返回 (内容, 最终 URL, Content-Type)。网络抖动自动重试。"""
    headers = {"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"}
    if referer:
        headers["Referer"] = referer
    last = ""
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read(), r.geturl(), r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (400, 401, 403, 404, 410):
                break
        except Exception as e:  # 超时、连接重置、SSL 抖动
            last = f"{type(e).__name__}: {e}"
        time.sleep(1.5 * (i + 1))
    raise StopError("ERROR", f"下载失败（{last}）：{url[:120]}")


def sniff_image(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:2] == b"BM":
        return "bmp"
    if data[4:12] in (b"ftypavif", b"ftypavis"):
        return "avif"
    head = data[:300].lstrip().lower()
    if head.startswith(b"<svg") or (head.startswith(b"<?xml") and b"<svg" in data[:1000].lower()):
        return "svg"
    return None


# ---------------------------------------------------------------- 页面检查与元数据
BLOCKED_MARKERS = ["环境异常", "完成验证后即可继续访问", "secitptpage/verify", "wappoc_appmsgcaptcha",
                   "请输入验证码", "操作频繁"]
GONE_MARKERS = {"该内容已被发布者删除": "文章已被发布者删除",
                "此内容因违规无法查看": "文章因违规被屏蔽",
                "此内容被投诉且经审核涉嫌侵权": "文章因侵权投诉被屏蔽",
                "该公众号已迁移": "公众号已迁移，旧链接失效",
                "此帐号已被屏蔽": "公众号已被屏蔽",
                "此帐号已自主注销": "公众号已注销",
                "链接已过期": "链接已过期（搜狗等搜索结果里的临时链接几小时后失效）"}


def check_page(page: str) -> None:
    if 'id="js_content"' in page or "id='js_content'" in page:
        return
    for k, v in GONE_MARKERS.items():
        if k in page:
            raise StopError("UNAVAILABLE", v)
    for k in BLOCKED_MARKERS:
        if k in page:
            raise StopError("NEED_BROWSER", f"微信返回了验证页（“{k}”），脚本不做验证")
    if "参数错误" in page:
        raise StopError("UNAVAILABLE", "微信提示“参数错误”，链接不完整或已失效")
    raise StopError("NEED_BROWSER", "页面里没有正文区域 #js_content（可能是图片/视频消息或页面改版）")


def js_str(page: str, name: str) -> str:
    pats = [rf"var\s+{name}\s*=\s*htmlDecode\(\s*\"((?:[^\"\\]|\\.)*)\"",
            rf"var\s+{name}\s*=\s*'((?:[^'\\]|\\.)*)'",
            rf"var\s+{name}\s*=\s*\"((?:[^\"\\]|\\.)*)\"",
            rf"\b{name}\s*:\s*'((?:[^'\\]|\\.)*)'",
            rf"\b{name}\s*:\s*\"((?:[^\"\\]|\\.)*)\""]
    for p in pats:
        m = re.search(p, page)
        if m and m.group(1).strip():
            v = m.group(1)
            v = re.sub(r"\\x([0-9a-fA-F]{2})", lambda x: chr(int(x.group(1), 16)), v)
            v = v.replace("\\'", "'").replace('\\"', '"').replace("\\/", "/")
            return html.unescape(html.unescape(v)).strip()
    return ""


def meta(page: str, key: str) -> str:
    m = re.search(rf'<meta[^>]+(?:property|name)="{re.escape(key)}"[^>]+content="([^"]*)"', page)
    return html.unescape(m.group(1)).strip() if m else ""


def tag_text(page: str, elem_id: str) -> str:
    m = re.search(rf'id="{elem_id}"[^>]*>(.*?)</', page, re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))).strip() if m else ""


def extract_meta(page: str, url: str) -> dict:
    title = js_str(page, "msg_title") or meta(page, "og:title") or tag_text(page, "activity-name")
    if not title:
        m = re.search(r'class="js_title_inner"[^>]*>(.*?)</span>', page, re.S)
        title = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
    account = js_str(page, "nickname") or tag_text(page, "js_name")
    author = meta(page, "author") or meta(page, "og:article:author")
    if author == account or author.startswith(account + "微信"):
        author = author if author != account else ""
    published = None
    m = re.search(r"\bct\s*=\s*['\"](\d{10})['\"]", page)
    if m:
        published = datetime.fromtimestamp(int(m.group(1)), CST)
    else:
        s = js_str(page, "createTime") or js_str(page, "create_time")
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                published = datetime.strptime(s, fmt).replace(tzinfo=CST)
                break
            except ValueError:
                pass
    if not published:
        t = tag_text(page, "publish_time")
        m = re.search(r"(\d{4})(?:年|-)(\d{1,2})(?:月|-)(\d{1,2})日?(?:\s*(\d{1,2}):(\d{2}))?", t)
        if m:
            published = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                                 int(m.group(4) or 0), int(m.group(5) or 0), tzinfo=CST)
    def var(name: str, pat: str) -> str:
        m = re.search(rf"var\s+{name}\s*=\s*[\"']({pat})[\"']", page)
        return m.group(1) if m else ""
    biz, mid = var("biz", r"[A-Za-z0-9+/=]+"), var("mid", r"\d+")
    idx, sn = var("idx", r"\d+"), var("sn", r"[0-9a-f]{16,}")
    permanent = ""
    if biz and mid and idx and sn:
        permanent = f"https://mp.weixin.qq.com/s?__biz={biz}&mid={mid}&idx={idx}&sn={sn}"
    elif "__biz=" in url and "sn=" in url:
        q = dict(re.findall(r"[?&](__biz|mid|idx|sn)=([^&#]+)", url))
        if len(q) == 4:
            permanent = "https://mp.weixin.qq.com/s?" + "&".join(f"{k}={q[k]}" for k in ("__biz", "mid", "idx", "sn"))
    elif "/s/" in url and "src=" not in url:
        permanent = url.split("?")[0].split("#")[0]
    return {"title": title, "account": account, "author": author,
            "published": published, "permanent_url": permanent,
            "source_url_in_article": js_str(page, "msg_source_url")}


# ---------------------------------------------------------------- 正文转 Markdown
def clean_url(u: str) -> str:
    u = html.unescape(u.strip())
    if u.startswith("//"):
        u = "https:" + u
    return u.split("#")[0]


class ContentParser(HTMLParser):
    """只解析 #js_content 子树，转成 Markdown；视频播放器等节点整段跳过。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.root_depth: int | None = None   # js_content 所在的栈深度
        self.skip_depth: int | None = None
        self.out: list[str] = []
        self.images: list[str] = []
        self.videos = 0
        self.inline_stack: list[tuple[str, int]] = []  # (标记, 起始位置)
        self.table: list[list[str]] | None = None
        self.cell: list[str] | None = None
        self.link_href: list[str | None] = []
        self.list_stack: list[list] = []  # [类型, 计数]
        self.pre = 0
        self.done = False

    # 输出工具
    def emit(self, s: str) -> None:
        if self.cell is not None:
            self.cell.append(s)
        else:
            self.out.append(s)

    def block(self) -> None:
        if self.cell is not None:
            self.cell.append(" ")
        else:
            self.out.append("\n\n")

    def is_video(self, tag: str, a: dict) -> bool:
        cls = a.get("class", "") or ""
        if tag in VIDEO_TAGS:
            return True
        if "data-mpvid" in a or "data-vidtype" in a:
            return True
        return any(k in cls for k in ("video_iframe", "js_tx_video_container", "mp_video",
                                      "wx_video", "video_player", "js_video", "txp_"))

    def handle_starttag(self, tag: str, attrs) -> None:
        if self.done:
            return
        a = {k: (v or "") for k, v in attrs}
        if self.root_depth is None:
            if a.get("id") == "js_content":
                self.root_depth = len(self.stack)
            if tag not in VOID:
                self.stack.append(tag)
            return
        if self.skip_depth is not None:
            if tag not in VOID:
                self.stack.append(tag)
            return
        if tag in SKIP_TAGS or self.is_video(tag, a) or "display:none" in a.get("style", "").replace(" ", ""):
            if self.is_video(tag, a):
                self.videos += 1
                self.block()
                self.emit(VIDEO_MARK)
                self.block()
            if tag not in VOID:
                self.skip_depth = len(self.stack)
                self.stack.append(tag)
            return
        if tag == "img":
            src = a.get("data-src") or a.get("src") or ""
            if src and not src.startswith("data:"):
                self.images.append(clean_url(src))
                self.emit(f"\n\n<<IMG{len(self.images)}>>\n\n" if self.cell is None else f" <<IMG{len(self.images)}>> ")
            return
        if tag == "br":
            self.emit("\n" if self.cell is None else " ")
            return
        if tag == "hr":
            self.block(); self.emit("---"); self.block()
            return
        self.stack.append(tag)
        if tag == "table":
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.table.append([])
        elif tag in ("td", "th") and self.table is not None:
            self.cell = []
        elif tag in BLOCK:
            self.block()
            if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                self.emit("#" * min(int(tag[1]) + 1, 6) + " ")
            elif tag == "blockquote":
                self.emit("> ")
            elif tag in ("ul", "ol"):
                self.list_stack.append([tag, 0])
            elif tag == "li":
                if self.list_stack and self.list_stack[-1][0] == "ol":
                    self.list_stack[-1][1] += 1
                    self.emit(f"{self.list_stack[-1][1]}. ")
                else:
                    self.emit("- ")
            elif tag == "pre":
                self.pre += 1
                self.emit("```txt\n")
        elif tag in ("strong", "b"):
            self.inline_stack.append(("**", len(self.out)))
            self.emit("\x00B")
        elif tag == "a":
            href = a.get("href", "")
            self.link_href.append(href if href.startswith("http") else None)
            self.emit("\x00A")

    def handle_endtag(self, tag: str) -> None:
        if self.done or tag in VOID:
            return
        if tag not in self.stack:
            return
        while self.stack:
            t = self.stack.pop()
            depth = len(self.stack)
            if self.skip_depth is not None:
                if depth == self.skip_depth:
                    self.skip_depth = None
                if t == tag:
                    return
                continue
            if self.root_depth is not None and depth == self.root_depth:
                self.done = True
                return
            if self.root_depth is not None:
                self.close(t)
            if t == tag:
                return

    def close(self, t: str) -> None:
        if t in ("td", "th") and self.cell is not None and self.table is not None:
            txt = re.sub(r"\s+", " ", "".join(self.cell)).replace("|", "\\|").strip()
            txt = txt.replace("\x00B", "").replace("\x00b", "").replace("\x00A", "").replace("\x00a", "")
            if self.table:
                self.table[-1].append(txt)
            self.cell = None
        elif t == "table" and self.table is not None:
            rows = [r for r in self.table if any(c.strip() for c in r)]
            self.table = None
            if rows:
                n = max(len(r) for r in rows)
                rows = [r + [""] * (n - len(r)) for r in rows]
                lines = ["| " + " | ".join(rows[0]) + " |", "|" + " --- |" * n]
                lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
                self.block(); self.emit("\n".join(lines)); self.block()
        elif t in ("strong", "b"):
            self.emit("\x00b")
        elif t == "a":
            href = self.link_href.pop() if self.link_href else None
            self.emit(f"\x00a{href or ''}\x00")
        elif t in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
            self.block()
        elif t == "pre":
            self.pre = max(0, self.pre - 1)
            self.emit("\n```")
            self.block()
        elif t in BLOCK:
            self.block()

    def handle_data(self, data: str) -> None:
        if self.done or self.root_depth is None or self.skip_depth is not None:
            return
        if self.pre:
            self.emit(data)
            return
        data = data.replace("​", "").replace("﻿", "").replace("\xa0", " ")
        data = re.sub(r"[ \t\r\n]+", " ", data)
        if data:
            self.emit(data)


def finish_markdown(raw: str) -> str:
    # 粗体：内容为空就去掉标记
    raw = re.sub(r"\x00B(\s*)\x00b", r"\1", raw)
    def bold(m):
        inner = m.group(2)
        if not inner.strip() or re.fullmatch(r"\s*(<<IMG\d+>>\s*)+", inner) or "\n\n" in inner:
            return m.group(1) + inner + m.group(3)
        return f"{m.group(1)}**{inner}**{m.group(3)}"
    raw = re.sub(r"\x00B(\s*)(.*?)(\s*)\x00b", bold, raw, flags=re.S)
    raw = raw.replace("\x00B", "").replace("\x00b", "")
    # 链接：有 http 地址才写成 Markdown 链接
    def link(m):
        text, href = m.group(1), m.group(2)
        return f"[{text.strip()}]({href})" if href and text.strip() and "<<IMG" not in text else text
    raw = re.sub(r"\x00A(.*?)\x00a(.*?)\x00", link, raw, flags=re.S)
    raw = raw.replace("\x00A", "")
    lines = []
    for line in raw.split("\n"):
        line = line.rstrip()
        if line.strip() in ("", ">", "-", "#", "##", "###"):
            line = ""
        lines.append(line.lstrip(" ") if not line.startswith("    ") else line)
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    # 去掉连续重复的视频占位
    text = re.sub(rf"(\[原文此处嵌入视频\]\s*){{2,}}", VIDEO_MARK + "\n\n", text)
    return text + "\n"


# ---------------------------------------------------------------- 主流程
def safe_name(text: str, limit: int = 40) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\\/:*?\"<>|\r\n\t#]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" .-_")
    return text[:limit].strip() or "未命名"


def save(url: str, out_root: Path, from_html: Path | None = None) -> Path:
    if from_html:
        page = from_html.read_text(encoding="utf-8-sig", errors="replace").strip()
        if page.startswith('"'):            # 有的浏览器工具把返回值包成 JSON 字符串
            page = json.loads(page)
        final_url, method = url, "browser_html"
    else:
        data, final_url, _ = http_get(url, referer=REFERER)
        page = data.decode("utf-8", errors="replace")
        method = "urllib"
    check_page(page)
    info = extract_meta(page, url)
    p = ContentParser()
    p.feed(page)
    if p.root_depth is None:
        raise StopError("NEED_BROWSER", "没有解析到 #js_content")
    body = finish_markdown("".join(p.out))

    date = info["published"].strftime("%Y-%m-%d") if info["published"] else datetime.now(CST).strftime("%Y-%m-%d")
    folder = out_root / "公众号" / f"{date}_{safe_name(info['title'] or '未命名')}"
    img_dir = folder / "images"
    if img_dir.exists():
        shutil.rmtree(img_dir)
    img_dir.mkdir(parents=True, exist_ok=True)

    # 按正文顺序下载，同一张图只存一份
    url_to_file: dict[str, str] = {}
    failed: list[str] = []
    n = 0
    for u in p.images:
        if u in url_to_file or u in failed:
            continue
        try:
            data, _, _ = http_get(u, referer=REFERER, attempts=4)
            ext = sniff_image(data)
            if not ext:
                raise StopError("ERROR", "返回的不是图片")
        except StopError:
            failed.append(u)
            continue
        n += 1
        name = f"{n:02d}.{ext}"
        (img_dir / name).write_bytes(data)
        url_to_file[u] = name

    def img_ref(m):
        u = p.images[int(m.group(1)) - 1]
        if u in url_to_file:
            return f"![图{url_to_file[u].split('.')[0]}](images/{url_to_file[u]})"
        return f"[图片下载失败，原图链接]({u})"
    body = re.sub(r"<<IMG(\d+)>>", img_ref, body)

    head = [f"# {info['title'] or '未命名'}", ""]
    meta_line = [f"公众号：{info['account'] or '未知'}"]
    if info["author"]:
        meta_line.append(f"作者：{info['author']}")
    if info["published"]:
        meta_line.append(f"发布时间：{info['published'].strftime('%Y-%m-%d %H:%M')}")
    head.append("> " + "｜".join(meta_line))
    head.append(f"> 原文链接：{info['permanent_url'] or url}")
    head += ["", "---", "", ""]
    md = "\n".join(head) + body
    (folder / "article.md").write_text(md, encoding="utf-8")

    plain = re.sub(r"!\[[^\]]*\]\([^)]*\)|\[[^\]]*\]\([^)]*\)|[#>*|\-`]", "", body)
    fetched = datetime.now(CST)
    source = {
        "url": url,
        "permanent_url": info["permanent_url"],
        "title": info["title"],
        "account": info["account"],
        "author": info["author"],
        "published_at": info["published"].isoformat() if info["published"] else None,
        "fetched_at": fetched.isoformat(timespec="seconds"),
        "image_count": len(url_to_file),
        "image_refs_in_article": len(re.findall(r"!\[图\d+\]\(images/", body)),
        "images_failed": failed,
        "embedded_videos_not_saved": p.videos,
        "text_chars": len(re.sub(r"\s", "", plain)),
        "method": method,
    }
    if info["source_url_in_article"]:
        source["original_source_link"] = info["source_url_in_article"]
    (folder / "source.json").write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")
    if source["text_chars"] < 20 and not url_to_file:
        raise StopError("NEED_BROWSER", "正文几乎为空（可能是图片消息或页面改版）")
    print(f"标题    : {source['title']}")
    print(f"公众号  : {source['account']}" + (f"（作者 {source['author']}）" if source["author"] else ""))
    print(f"发布时间: {source['published_at']}")
    print(f"正文字数: {source['text_chars']}；图片 {source['image_count']} 张"
          + (f"，{len(failed)} 张下载失败" if failed else "")
          + (f"；原文嵌入视频 {p.videos} 处未下载" if p.videos else ""))
    return folder


def run(url: str, out: str = "资料", from_html: str | None = None) -> tuple[str, str]:
    """供 save.py 调用：返回 (结论, 目录或原因)。"""
    try:
        if "mp.weixin.qq.com" not in url:
            raise StopError("ERROR", "不是 mp.weixin.qq.com 的文章链接")
        folder = save(url, Path(out).expanduser().resolve(), Path(from_html) if from_html else None)
        return "OK", str(folder)
    except StopError as e:
        return e.kind, e.reason
    except Exception as e:  # 兜底，避免打印长堆栈吓到使用者
        return "ERROR", f"{type(e).__name__}: {e}"


def extract_url(text: str) -> str:
    m = re.search(r"https?://mp\.weixin\.qq\.com/[^\s\"'<>，。；）)]+", text)
    return m.group(0) if m else text.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="保存一篇公开的微信公众号文章")
    ap.add_argument("url", help="文章链接，或含链接的分享文字")
    ap.add_argument("--out", default="资料", help="输出根目录，默认当前目录下的 资料")
    ap.add_argument("--from-html", help="浏览器存下来的页面 HTML（脚本取不到页面时用）")
    a = ap.parse_args()
    kind, msg = run(extract_url(a.url), a.out, a.from_html)
    print(f"RESULT: {kind} {msg}")
    return 0 if kind == "OK" else (2 if kind == "NEED_BROWSER" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
