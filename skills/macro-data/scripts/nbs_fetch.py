#!/usr/bin/env python3
"""国家统计局新 API 取数辅助（2026-09 实测版，旧 easyquery 已废止）。

只用 Python 标准库，macOS / Windows / Linux 通用。

用法（macOS 用 python3，Windows 用 python 或 py；也可以换成检查脚本给出的解释器完整路径）：
  python3 nbs_fetch.py search <中文关键词>
  python3 nbs_fetch.py data <cid> <indicatorId> <dts>
    dts 示例：202601MM-202608MM（月）/ 202501SS-202602SS（季）/ 2020YY-2025YY（年）
"""
import json, sys, time, urllib.request, urllib.parse

BASE = "https://data.stats.gov.cn/dg/website/publicrelease/web/external"
AREA = [{"text": "全国", "value": "000000000000"}]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

# Windows 控制台默认 GBK 编码，打印中文或特殊字符可能报 UnicodeEncodeError；统一改成 UTF-8 输出
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

def _get(url):
    # 服务端对 Python-urllib 默认 UA 不稳定（实测全败），必须显式带 UA；偶发异常 HTML 页，重试 3 次
    for attempt in range(3):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode("utf-8", "replace")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            print(f"!! 第{attempt+1}次非JSON，前120字节: {raw[:120]!r}", file=sys.stderr)
            time.sleep(1 + attempt)
    print("!! 返回非 JSON（重试 3 次均失败）；检查关键词是否为中文，或服务端维护中", file=sys.stderr)
    sys.exit(2)

def search(kw):
    # 注意：pageSize>=10 会触发服务端异常 HTML 页（2026-09 实测），必须用 <=5
    res = _get(f"{BASE}/query?search={urllib.parse.quote(kw)}&pagenum=1&pageSize=5")
    # 实测结构：{"data": {"types": [...], "data": [...]}}；偶发返回服务端异常 HTML 页，重试即可
    items = res.get("data")
    if isinstance(items, dict):
        items = items.get("data") or items.get("list") or []
    for item in items or []:
        print(json.dumps({k: item.get(k) for k in ("show_name", "dt_name", "value", "indic_id", "i", "treeinfo_globalid") if k in item}, ensure_ascii=False))

def data(cid, indicator_id, dts, quiet=False):
    """取数并逐行打印；返回 [(期别, 指标名, 值或空串, 单位), ...]，未发布月份值为空串。"""
    body = json.dumps({
        "cid": cid, "indicatorIds": [indicator_id], "das": AREA,
        "dts": [dts], "showType": "1",
    }).encode()
    req = urllib.request.Request(f"{BASE}/stream/esData", data=body,
                                 headers={"Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        res = json.loads(r.read().decode("utf-8", "replace"))
    rows = []
    for row in res.get("data", []):
        for v in row.get("values", []):
            rows.append((row.get("name", row.get("code")), v.get("i_showname", "").strip(),
                         v.get("value") or "", v.get("du_name", "")))
    if not quiet:
        for name, show, val, unit in rows:
            print(f"{name}\t{show}\t{val or '（未发布）'} {unit}")
    return rows

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "search":
        search(sys.argv[2])
    elif len(sys.argv) >= 5 and sys.argv[1] == "data":
        data(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(__doc__)
        sys.exit(1)
