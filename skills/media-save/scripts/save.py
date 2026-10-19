#!/usr/bin/env python3
"""media-save 入口：按链接自动分派到公众号或抖音脚本，可一次给多个链接（只用标准库，Python >= 3.10）。

用法（<PY> 换成你的 Python：macOS 一般是 python3，Windows 是 py 或 python）：
  <PY> save.py "https://mp.weixin.qq.com/s/xxxx"
  <PY> save.py "https://v.douyin.com/xxxx/" "https://mp.weixin.qq.com/s/yyyy"
  <PY> save.py "<整段分享文字，里面可以有多个链接>"
  <PY> save.py "<链接>" --out 资料          输出根目录，默认当前目录下的 资料

每个链接打印一行 RESULT，最后打印汇总表。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

if sys.version_info < (3, 10):
    print("RESULT: ERROR 需要 Python 3.10 或更高版本，当前是 %d.%d" % sys.version_info[:2])
    raise SystemExit(1)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import douyin_save  # noqa: E402
import wechat_save  # noqa: E402

URL_RE = re.compile(r"https?://[^\s\"'<>，。；）)]+")


def platform_of(url: str) -> str | None:
    host = url.split("/")[2].lower() if url.count("/") >= 2 else ""
    if host == "mp.weixin.qq.com":
        return "公众号"
    if host.endswith("douyin.com") or host.endswith("iesdouyin.com"):
        return "抖音"
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="把公开的微信公众号文章和抖音视频存到本地")
    ap.add_argument("inputs", nargs="+", help="链接或含链接的分享文字，可多个")
    ap.add_argument("--out", default="资料", help="输出根目录，默认当前目录下的 资料")
    a = ap.parse_args()

    urls: list[str] = []
    for text in a.inputs:
        found = [u.rstrip(".,;:") for u in URL_RE.findall(text)]
        urls.extend(found or [text.strip()])
    seen, todo = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            todo.append(u)

    results = []
    for i, url in enumerate(todo, 1):
        plat = platform_of(url)
        print(f"\n[{i}/{len(todo)}] {plat or '未知平台'}  {url}")
        if plat == "公众号":
            kind, msg = wechat_save.run(url, a.out)
        elif plat == "抖音":
            kind, msg = douyin_save.run(url, a.out)
        else:
            kind, msg = "UNSUPPORTED", "只支持 mp.weixin.qq.com（公众号）和 douyin.com / iesdouyin.com（抖音）链接"
        print(f"RESULT: {kind} {msg}")
        results.append((plat or "-", url, kind, msg))

    if len(results) > 1:
        print("\n== 汇总 ==")
        for plat, url, kind, msg in results:
            print(f"{kind:<15} {plat:<4} {msg if kind == 'OK' else url + '  ' + msg}")
    ok = sum(1 for r in results if r[2] == "OK")
    print(f"SUMMARY: {ok}/{len(results)} OK")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
