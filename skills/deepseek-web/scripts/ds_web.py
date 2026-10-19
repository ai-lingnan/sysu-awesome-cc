#!/usr/bin/env python3
"""DeepSeek Search / Fetch API client (standard library only; works on macOS and Windows).

  python ds_web.py search "query" [--count 5] [--content] [--out results.json]
  python ds_web.py fetch  "https://..." [--out page.md]
  python ds_web.py check            # 查 Key 是否已配置、是否有效、余额（免费接口，不计费）
  python ds_web.py setup            # 用户本人在终端运行：粘贴 Key（不回显），写进本机环境变量

The API key is read from the DEEPSEEK_API_KEY environment variable and is never printed.
"""
import argparse, getpass, json, os, subprocess, sys, time, urllib.error, urllib.request

BASE = "https://api.deepseek.com/v1/tools/"


def get_key():
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key and sys.platform == "darwin":
        # macOS: a key set with `launchctl setenv` only reaches apps started afterwards;
        # read it from the launchd session instead of asking the user to restart the agent app.
        import subprocess
        try:
            key = subprocess.run(["/bin/launchctl", "getenv", "DEEPSEEK_API_KEY"],
                                 capture_output=True, text=True, timeout=5).stdout.strip()
        except Exception:
            key = ""
    return key


APPLY_URL = "https://platform.deepseek.com/api_keys"
GUIDE = (
    "还没有可用的 DeepSeek Key。请按下面两步配置（Key 只由你本人粘贴，不要发给智能体）：\n"
    f"  1. 打开 {APPLY_URL} ，用手机号登录 DeepSeek 开放平台，点“创建 API Key”，复制下来；账户需要有余额。\n"
    "  2. 在终端运行本脚本的 setup 子命令，按提示粘贴 Key：\n"
    "       macOS：python3 \"<本技能目录>/scripts/ds_web.py\" setup\n"
    "       Windows：py \"<本技能目录>\\scripts\\ds_web.py\" setup\n"
    "  配好后重启 Claude Code 或 WorkBuddy，再让智能体继续。"
)


def balance(key):
    """GET /user/balance：免费接口，用来验证 Key 并读余额。返回 (状态, 说明)。"""
    req = urllib.request.Request("https://api.deepseek.com/user/balance",
                                 headers={"Authorization": "Bearer " + key, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return ("KEY_INVALID", f"HTTP {e.code}：Key 无效或已删除") if e.code in (401, 403) else ("ERROR", f"HTTP {e.code}")
    except (urllib.error.URLError, TimeoutError) as e:
        return "ERROR", f"网络错误：{e}"
    infos = d.get("balance_infos") or [{}]
    total = ", ".join(f"{i.get('total_balance')} {i.get('currency')}" for i in infos if i)
    if not d.get("is_available"):
        return "NO_BALANCE", f"Key 有效，但余额不足（{total}），请到开放平台充值"
    return "KEY_OK", f"Key 有效，余额 {total}"


def persist_key(key):
    """把 Key 写进本机环境变量，新启动的程序都能读到。"""
    if sys.platform == "win32":
        subprocess.run(["setx", "DEEPSEEK_API_KEY", key], check=True, capture_output=True)
        return "已写入 Windows 用户环境变量 DEEPSEEK_API_KEY。请关掉所有终端、Claude Code 和 WorkBuddy 后重新打开。"
    if sys.platform == "darwin":
        subprocess.run(["/bin/launchctl", "setenv", "DEEPSEEK_API_KEY", key], check=True)
        # 登录后自动再设一次，重启电脑也不丢
        agents = os.path.expanduser("~/Library/LaunchAgents")
        os.makedirs(agents, exist_ok=True)
        plist = os.path.join(agents, "top.lingnan.deepseek-key.plist")
        with open(plist, "w", encoding="utf-8") as fh:
            fh.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                     '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
                     '<plist version="1.0"><dict><key>Label</key><string>top.lingnan.deepseek-key</string>'
                     '<key>ProgramArguments</key><array><string>/bin/launchctl</string><string>setenv</string>'
                     f'<string>DEEPSEEK_API_KEY</string><string>{key}</string></array>'
                     '<key>RunAtLoad</key><true/></dict></plist>\n')
        os.chmod(plist, 0o600)
        return "已写入 macOS 环境变量（重启电脑后自动恢复）。请退出并重新打开 Claude Code 或 WorkBuddy。"
    return "当前系统请手动设置环境变量 DEEPSEEK_API_KEY。"


def check():
    key = get_key()
    if not key:
        print("KEY_MISSING")
        print(GUIDE)
        return 1
    status, msg = balance(key)
    print(status)
    print(msg)
    if status == "KEY_INVALID":
        print(GUIDE)
    return 0 if status == "KEY_OK" else 1


def setup():
    print(f"在 {APPLY_URL} 创建 API Key 后，粘贴到下面（输入时不显示）：")
    key = getpass.getpass("DeepSeek API Key: ").strip()
    if not key:
        sys.exit("没有输入 Key，已退出。")
    status, msg = balance(key)
    print(msg)
    if status in ("KEY_INVALID",):
        sys.exit("这个 Key 用不了，没有保存。请回开放平台检查后重试。")
    print(persist_key(key))
    return 0


def call(endpoint, body, attempts=3):
    key = get_key()
    if not key:
        print("KEY_MISSING"); print(GUIDE); sys.exit(1)
    req = urllib.request.Request(
        BASE + endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    hints = {401: "Key 无效", 402: "账户余额不足", 403: "被策略拦截",
             404: "取不到可用内容", 429: "请求太快，稍后再试"}
    for i in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # Fetch 第一次常返回 404 failed to fetch URL，重试即可；429 与 5xx 也等一会再试
            if e.code in (404, 429, 500, 502, 503, 504) and i < attempts - 1:
                time.sleep(2 * (i + 1))
                continue
            sys.exit(f"HTTP {e.code} {hints.get(e.code, '')}".strip())
        except (urllib.error.URLError, TimeoutError) as e:
            if i < attempts - 1:
                time.sleep(2 * (i + 1))
                continue
            sys.exit(f"网络错误：{e}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--count", type=int, default=5)
    s.add_argument("--content", action="store_true"); s.add_argument("--out")
    f = sub.add_parser("fetch"); f.add_argument("url"); f.add_argument("--out")
    sub.add_parser("check"); sub.add_parser("setup")
    a = ap.parse_args()
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    if a.cmd == "check":
        sys.exit(check())
    if a.cmd == "setup":
        sys.exit(setup())
    if a.cmd == "search":
        data = call("search", {"query": a.query, "count": a.count, "need_content": a.content})
        res = data.get("results", [])
        if a.out:
            with open(a.out, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
        print(f"{len(res)} results")
        for i, r in enumerate(res, 1):
            print(f"[{i}] {r.get('title')}\n    {r.get('url')}\n    date={r.get('date')} authority={r.get('authority')} "
                  f"score={r.get('rerank_score')}\n    {(r.get('snippet') or '')[:160]}")
    else:
        data = call("fetch", {"url": a.url})
        text = f"# {data.get('title', '')}\n\nSource: {a.url}\n\n{data.get('content', '')}"
        if a.out:
            with open(a.out, "w", encoding="utf-8") as fh:
                fh.write(text)
        print(f"title: {data.get('title')}\nchars: {len(data.get('content', ''))}")
        print((data.get("content") or "")[:1200])


if __name__ == "__main__":
    main()
