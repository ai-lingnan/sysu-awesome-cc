#!/usr/bin/env python3
"""下载一条公开的抖音视频（只用 Python 标准库，Python >= 3.10）。

两条路线，先快后慢：
1. 快速路线：读官方分享页 iesdouyin.com/share/video/<作品ID>/?from_ssr=1 里公开给出的数据，
   核对作品 ID、作者、标题后下载官方播放地址。分享页不给数据时结论为 NEED_BROWSER。
2. 浏览器路线：智能体用浏览器打开分享链接，在页面里运行 douyin_extract.js，
   把返回的 JSON 存成文件交给本脚本（--from-json），或用 --media-url 等参数逐项传入。

用法（<PY> 换成你的 Python：macOS 一般是 python3，Windows 是 py -3）：
  <PY> douyin_save.py "https://v.douyin.com/xxxx/"
  <PY> douyin_save.py "3.84 复制打开抖音，看看【某某的作品】…… https://v.douyin.com/xxxx/ ……"
  <PY> douyin_save.py "<链接>" --from-json douyin_page.json
  <PY> douyin_save.py --media-url "<视频地址>" --author 央视新闻 --title "<标题>" --page-url "<作品页>"
  <PY> douyin_save.py "<链接>" --out 资料                     输出根目录，默认 ./资料

产物：<out>/抖音/<作品ID>_<标题>/video.mp4、source.json
最后一行是结论：
  RESULT: OK <目录>
  RESULT: NEED_BROWSER <原因>    快速路线没拿到数据，改走浏览器路线
  RESULT: NEED_HUMAN <原因>      要登录或要人完成验证
  RESULT: UNSUPPORTED <原因>     图文作品、私密或已删除作品
  RESULT: ERROR <原因>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

for _s in (sys.stdout, sys.stderr):  # Windows 控制台默认 GBK，统一 UTF-8 输出
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1")
REFERER = "https://www.iesdouyin.com/"
DESKTOP_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
CST = timezone(timedelta(hours=8))
ID_PATTERNS = [r"/share/video/(\d{8,})", r"/video/(\d{8,})", r"modal_id=(\d{8,})",
               r"aweme_id=(\d{8,})", r"item_ids=(\d{8,})"]
NOTE_PATTERNS = [r"/share/note/(\d{8,})", r"/note/(\d{8,})", r"/share/slides/(\d{8,})", r"/slides/(\d{8,})"]


class StopError(Exception):
    def __init__(self, kind: str, reason: str):
        super().__init__(reason)
        self.kind, self.reason = kind, reason


def http_get(url: str, *, attempts: int = 4, timeout: int = 30) -> tuple[bytes, str]:
    headers = {"User-Agent": UA, "Referer": REFERER, "Accept-Language": "zh-CN,zh;q=0.9"}
    last = ""
    for i in range(attempts):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
                return r.read(), r.geturl()
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (400, 401, 403, 404, 410):
                break
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
        time.sleep(1.5 * (i + 1))
    raise StopError("ERROR", f"网络请求失败（{last}）：{url[:100]}")


def extract_url(text: str) -> str:
    m = re.search(r"https?://[^\s\"'<>，。；）)]+", text)
    if not m:
        raise StopError("ERROR", "输入里没有找到 http(s) 链接")
    return m.group(0).rstrip(".,;:")


def find_id(url: str) -> tuple[str | None, bool]:
    for p in NOTE_PATTERNS:
        m = re.search(p, url)
        if m:
            return m.group(1), True
    for p in ID_PATTERNS:
        m = re.search(p, url)
        if m:
            return m.group(1), False
    return None, False


def is_waf(page: str) -> bool:
    return "_wafchallengeid" in page or "waf-jschallenge" in page or "__ac_nonce" in page[:5000]


def find_item(obj, aweme_id: str):
    """在 _ROUTER_DATA 里递归找 aweme_id 对得上的作品对象，不依赖固定的键名路径。"""
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            if str(cur.get("aweme_id", "")) == aweme_id and ("desc" in cur or "video" in cur):
                return cur
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return None


def find_filter_reason(obj) -> str:
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            fl = cur.get("filter_list")
            if isinstance(fl, list) and fl:
                f = fl[0] if isinstance(fl[0], dict) else {}
                return str(f.get("notice") or f.get("detail_msg") or f.get("filter_reason") or "")
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return ""


def fetch_item(aweme_id: str) -> tuple[str, dict]:
    url = f"https://www.iesdouyin.com/share/video/{aweme_id}/?from_ssr=1"
    page = ""
    for i in range(2):
        data, _ = http_get(url)
        page = data.decode("utf-8", errors="replace")
        if not is_waf(page):
            break
        time.sleep(3)   # 人机校验页：稍等再取一次，不做校验
    if is_waf(page):
        raise StopError("NEED_BROWSER", "官方分享页返回了人机校验页，改用浏览器打开")
    m = re.search(r"window\._ROUTER_DATA\s*=\s*(\{.*?\})\s*</script>", page, re.S)
    if not m:
        raise StopError("NEED_BROWSER", "官方分享页里没有 window._ROUTER_DATA，改用浏览器打开")
    try:
        root = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        raise StopError("NEED_BROWSER", f"官方分享页数据解析失败（{e}），改用浏览器打开")
    item = find_item(root, aweme_id)
    if not item:
        reason = find_filter_reason(root)
        if reason:
            raise StopError("UNSUPPORTED", f"抖音提示：{reason}（作品可能已删除、设为私密或仅登录可见）")
        raise StopError("NEED_BROWSER", "官方分享页只返回了页面空壳，没有作品数据，改用浏览器打开")
    return url, item


def norm(text: str) -> str:
    return re.sub(r"[\s\W_]+", "", unicodedata.normalize("NFKC", text or "").casefold())


def safe_name(text: str, limit: int = 40) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = re.sub(r"#\S+", " ", text)                   # 去掉话题标签
    text = re.sub(r"[\\/:*?\"<>|\r\n\t@]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" .-_")
    return text[:limit].strip() or "未命名"


def with_ratio(play_url: str, ratio: str) -> str:
    parts = urlsplit(play_url)
    q = dict(parse_qsl(parts.query, keep_blank_values=True))
    q["ratio"] = ratio
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))


def download(url: str, dest: Path, attempts: int = 6, referer: str = REFERER, ua: str = UA) -> str:
    """跟随官方播放地址的跳转下载 MP4，断线自动续传。返回 CDN 主机名。"""
    part = dest.with_name(dest.name + ".part")
    part.unlink(missing_ok=True)
    host, last = "", ""
    for i in range(attempts):
        have = part.stat().st_size if part.exists() else 0
        headers = {"User-Agent": ua, "Referer": referer}
        if have:
            headers["Range"] = f"bytes={have}-"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
                host = urlsplit(r.geturl()).netloc
                mode = "ab" if have and r.status == 206 else "wb"
                with open(part, mode) as f:
                    shutil.copyfileobj(r, f, 1 << 20)
            if part.stat().st_size > 1024:
                part.replace(dest)
                return host
            last = "文件太小"
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code == 416:          # 续传位置越界：重下
                part.unlink(missing_ok=True)
            elif e.code in (403, 404):
                break
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
        time.sleep(2 * (i + 1))
    part.unlink(missing_ok=True)
    raise StopError("ERROR", f"视频下载失败（{last}）")


def mp4_duration(path: Path) -> float | None:
    """读 MP4 的 moov/mvhd 盒子得到时长（秒），不依赖 ffprobe。"""
    import struct
    size_total = path.stat().st_size
    with open(path, "rb") as f:
        pos = 0
        while pos + 8 <= size_total:
            f.seek(pos)
            size, kind = struct.unpack(">I4s", f.read(8))
            head = 8
            if size == 1:
                size, head = struct.unpack(">Q", f.read(8))[0], 16
            elif size == 0:
                size = size_total - pos
            if kind == b"moov":
                end, p = pos + size, pos + head
                while p + 8 <= end:
                    f.seek(p)
                    sz, k = struct.unpack(">I4s", f.read(8))
                    if k == b"mvhd":
                        ver = f.read(1)[0]
                        f.read(3)
                        if ver == 1:
                            f.read(16)
                            scale, dur = struct.unpack(">IQ", f.read(12))
                        else:
                            f.read(8)
                            scale, dur = struct.unpack(">II", f.read(8))
                        return round(dur / scale, 2) if scale else None
                    if sz < 8:
                        break
                    p += sz
                return None
            if size < 8:
                break
            pos += size
    return None


def check_mp4(path: Path) -> dict:
    with open(path, "rb") as f:
        head = f.read(12)
    if head[4:8] != b"ftyp":
        raise StopError("ERROR", "下载到的文件不是 MP4（文件头没有 ftyp）")
    info: dict = {"header": "ftyp " + head[8:12].decode("latin-1", "replace").strip()}
    try:
        info["duration_s_from_file"] = mp4_duration(path)
    except Exception:
        info["duration_s_from_file"] = None
    exe = shutil.which("ffprobe")
    if not exe:
        info["ffprobe"] = "未安装，已跳过编码校验（时长取自 MP4 文件头）"
        return info
    p = subprocess.run([exe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
                       capture_output=True, text=True, timeout=120)
    if p.returncode != 0:
        raise StopError("ERROR", f"ffprobe 读不了这个文件：{p.stderr.strip()[:200]}")
    probe = json.loads(p.stdout)
    v = next((s for s in probe.get("streams", []) if s.get("codec_type") == "video"), None)
    a = next((s for s in probe.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not v:
        raise StopError("ERROR", "文件里没有视频流")
    info.update({"ffprobe": "ok", "duration_s": round(float(probe.get("format", {}).get("duration") or 0), 2),
                 "width": v.get("width"), "height": v.get("height"), "video_codec": v.get("codec_name"),
                 "audio_codec": a.get("codec_name") if a else None})
    return info


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_id(share: str) -> tuple[str, str, str]:
    """返回 (输入里的链接, 跳转后的链接, 作品 ID)。"""
    src = extract_url(share)
    aweme_id, is_note = find_id(src)
    resolved = src
    if not aweme_id:
        _, resolved = http_get(src)          # 短链：跟随跳转拿到作品 ID
        aweme_id, is_note = find_id(resolved)
    if is_note:
        raise StopError("UNSUPPORTED", "这是图文作品，本脚本只下载视频")
    if not aweme_id:
        raise StopError("ERROR", f"没能从链接里找到作品 ID：{resolved[:120]}")
    return src, resolved, aweme_id


def check_identity(author: str, title: str, expect_author: str | None, expect_title: str | None) -> None:
    if expect_author and norm(expect_author) not in norm(author):
        raise StopError("ERROR", f"作者对不上：页面上是“{author}”，期望“{expect_author}”")
    if expect_title and norm(expect_title)[:12] not in norm(title):
        raise StopError("ERROR", f"标题对不上：页面上是“{title[:40]}”")


def finish(folder: Path, dest: Path, meta: dict, page_duration: float | None) -> Path:
    check = check_mp4(dest)
    file_dur = check.get("duration_s") or check.get("duration_s_from_file")
    if file_dur and page_duration and abs(file_dur - page_duration) > 5:
        raise StopError("ERROR", f"时长对不上：页面 {page_duration:.1f} 秒，文件 {file_dur} 秒")
    source = dict(meta)
    source.update({
        "fetched_at": datetime.now(CST).isoformat(timespec="seconds"),
        "duration_s_from_page": page_duration,
        "file": "video.mp4",
        "size_bytes": dest.stat().st_size,
        "sha256": sha256(dest),
        "check": check,
    })
    (folder / "source.json").write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"作者    : {source['author']}")
    print(f"标题    : {source['title']}")
    print(f"发布时间: {source['published_at']}")
    print(f"文件    : {source['size_bytes']/1e6:.1f} MB，SHA-256 {source['sha256'][:16]}…；"
          + (f"时长 {check['duration_s']} 秒，{check['width']}x{check['height']}" if check.get("ffprobe") == "ok"
             else f"时长 {check.get('duration_s_from_file')} 秒；ffprobe {check['ffprobe']}"))
    return folder


def save(share: str, out_root: Path, expect_author: str | None = None, expect_title: str | None = None) -> Path:
    """快速路线：读官方分享页里公开给出的数据。"""
    src, _, aweme_id = resolve_id(share)
    ssr_url, item = fetch_item(aweme_id)
    if item.get("images"):
        raise StopError("UNSUPPORTED", "这是图文作品，本脚本只下载视频")
    status = item.get("status") or {}
    if status.get("is_delete") or status.get("is_private") or status.get("private_status"):
        raise StopError("UNSUPPORTED", "作品已删除或设为私密")
    author = (item.get("author") or {}).get("nickname", "")
    desc = item.get("desc", "")
    check_identity(author, desc, expect_author, expect_title)

    video = item.get("video") or {}
    urls = ((video.get("play_addr") or {}).get("url_list") or [])
    if not urls:
        raise StopError("NEED_BROWSER", "分享页数据里没有播放地址")
    base = urls[0].replace("/playwm/", "/play/")
    w, h = int(video.get("width") or 0), int(video.get("height") or 0)
    ratios = (["1080p", "720p"] if min(w, h) >= 1080 else ["720p"]) if w and h else ["720p"]

    folder = out_root / "抖音" / f"{aweme_id}_{safe_name(desc.strip() or '未命名')}"
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / "video.mp4"
    errors, host, used = [], "", ""
    for ratio in ratios:
        try:
            host = download(with_ratio(base, ratio), dest)
            used = ratio
            break
        except StopError as e:
            errors.append(f"{ratio}: {e.reason}")
    else:
        raise StopError("ERROR", "；".join(errors))
    ct = item.get("create_time")
    duration_ms = video.get("duration")
    meta = {
        "aweme_id": aweme_id,
        "share_url": src,
        "canonical_url": f"https://www.douyin.com/video/{aweme_id}",
        "author": author,
        "title": desc,
        "published_at": datetime.fromtimestamp(ct, CST).isoformat() if isinstance(ct, (int, float)) and ct > 0 else None,
        "method": "share_page",
        "data_source": ssr_url,
        "quality_requested": used,
        "cdn_host": host,
    }
    return finish(folder, dest, meta, round(duration_ms / 1000, 2) if duration_ms else None)


def parse_published(text: str | None) -> str | None:
    if not text:
        return None
    m = re.search(r"(\d{4})[-年/](\d{1,2})[-月/](\d{1,2})日?(?:\s*(\d{1,2}):(\d{2}))?", text)
    if not m:
        return text
    return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                    int(m.group(4) or 0), int(m.group(5) or 0), tzinfo=CST).isoformat()


def save_media(info: dict, out_root: Path, share: str | None = None,
               expect_author: str | None = None, expect_title: str | None = None) -> Path:
    """浏览器路线：页面里读到的视频地址与作者、标题，由本脚本下载并记录。"""
    status = info.get("status", "ok")
    if status == "note":
        raise StopError("UNSUPPORTED", "这是图文作品，本脚本只下载视频")
    if status == "verify":
        raise StopError("NEED_HUMAN", "抖音弹出了验证，请在浏览器里完成验证后再试")
    if status == "login":
        raise StopError("NEED_HUMAN", "这条作品要登录后才能看，本技能只处理公开作品")
    urls = [u for u in (info.get("media_urls") or []) if u and u.startswith("http")]
    if status != "ok" or not urls:
        raise StopError("ERROR", "页面上没有找到视频地址（作品可能已删除、设为私密或页面改版）")
    page_url = info.get("page_url") or ""
    aweme_id = str(info.get("aweme_id") or "") or (find_id(page_url)[0] or "")
    if not aweme_id and share:
        aweme_id = resolve_id(share)[2]
    if not aweme_id:
        raise StopError("ERROR", "没能确定作品 ID，请同时给出 --page-url")
    urls = [u for u in urls if "douyinstatic.com" not in u]      # 排除页面加载动画
    if not urls:
        raise StopError("ERROR", "页面给出的只是加载动画，不是作品视频；等页面加载完再执行一次")
    author, title = (info.get("author") or "").strip(), (info.get("title") or "").strip()
    if not author and not title:
        raise StopError("ERROR", "页面还没加载完（作者、标题都是空的）；等几秒再执行一次")
    check_identity(author, title, expect_author, expect_title)

    folder = out_root / "抖音" / f"{aweme_id}_{safe_name(title or '未命名')}"
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / "video.mp4"
    errors, host = [], ""
    for u in urls:
        try:
            host = download(u, dest, referer="https://www.douyin.com/", ua=info.get("user_agent") or DESKTOP_UA)
            break
        except StopError as e:
            errors.append(f"{urlsplit(u).netloc}: {e.reason}")
    else:
        raise StopError("ERROR", "；".join(errors) + "（视频地址有时效，重新打开页面再取一次）")
    meta = {
        "aweme_id": aweme_id,
        "share_url": extract_url(share) if share else page_url,
        "canonical_url": f"https://www.douyin.com/video/{aweme_id}",
        "author": author,
        "title": title,
        "published_at": parse_published(info.get("published")),
        "method": "browser",
        "page_url": page_url,
        "cdn_host": host,
    }
    d = info.get("duration_s")
    return finish(folder, dest, meta, float(d) if d else None)


def run(share: str, out: str = "资料", expect_author: str | None = None, expect_title: str | None = None,
        media: dict | None = None) -> tuple[str, str]:
    try:
        root = Path(out).expanduser().resolve()
        if media:
            return "OK", str(save_media(media, root, share, expect_author, expect_title))
        return "OK", str(save(share, root, expect_author, expect_title))
    except StopError as e:
        return e.kind, e.reason
    except Exception as e:
        return "ERROR", f"{type(e).__name__}: {e}"


def main() -> int:
    ap = argparse.ArgumentParser(description="下载一条公开的抖音视频")
    ap.add_argument("share", nargs="?", help="抖音链接，或复制来的整段分享文字")
    ap.add_argument("--out", default="资料", help="输出根目录，默认当前目录下的 资料")
    ap.add_argument("--expect-author", help="可选：期望的作者昵称，对不上就停下")
    ap.add_argument("--expect-title", help="可选：期望的标题开头，对不上就停下")
    g = ap.add_argument_group("浏览器路线（快速路线返回 NEED_BROWSER 时用）")
    g.add_argument("--from-json", help="douyin_extract.js 返回的 JSON 存成的文件")
    g.add_argument("--media-url", action="append", help="页面里读到的视频地址，可给多个")
    g.add_argument("--author")
    g.add_argument("--title")
    g.add_argument("--published", help="页面上的发布时间，如 2026-10-11 23:52")
    g.add_argument("--duration", type=float, help="页面上的视频时长（秒）")
    g.add_argument("--page-url", help="浏览器里最终打开的作品页地址")
    a = ap.parse_args()
    media = None
    if a.from_json:
        media = json.loads(Path(a.from_json).read_text(encoding="utf-8-sig"))
        if isinstance(media, str):          # 有的浏览器工具把返回值再包一层 JSON 字符串
            media = json.loads(media)
    elif a.media_url:
        media = {"status": "ok", "media_urls": a.media_url, "author": a.author, "title": a.title,
                 "published": a.published, "duration_s": a.duration, "page_url": a.page_url}
    if not a.share and not media:
        ap.error("需要抖音链接，或 --from-json / --media-url")
    kind, msg = run(a.share or "", a.out, a.expect_author, a.expect_title, media)
    print(f"RESULT: {kind} {msg}")
    return 0 if kind == "OK" else (2 if kind == "NEED_BROWSER" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
