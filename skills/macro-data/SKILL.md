---
name: macro-data
description: "Use when 查中国或国际宏观/财经数据（GDP、CPI、PMI、社融、利率等）。按 2026-09 实测模板取数。"
tags: [economics, data]
platforms: [macos]
---

# 宏观/财经数据取数（2026-09 实测版）

所有模板均来自 2026-09-21 对十个数据源的逐一真实拉取测试。**只按本 skill 的模板取数；模板失效时按第 5 节/第四节铁律里的发现流程重新探路，不要编造数据。**

## 一、路由表（先选源再动手）

| 需求 | 首选 | 备用 / 核验 |
|---|---|---|
| 中国宏观（GDP/CPI/PMI/社融/M2/LPR/利率/汇率） | AKShare（快、免 token） | 国家统计局新 API 核验（权威一手） |
| 中国宏观「引用级」数字 | 国家统计局新 API | AKShare 交叉核对 |
| 国际跨国宏观面板（GDP/通胀/财政/就业/汇率） | DBnomics（93 机构一站式） | 各机构原生 API |
| World Bank WDI 年度数据 | wbgapi / WB 原生 API（5/5，别走 DBnomics） | — |
| IMF 年度宏观 + WEO 预测 | IMF DataMapper API | 高频 IFS 才降级 DBnomics |
| 美国宏观深度（含 ALFRED vintage） | FRED（fredgraph.csv 免 key 兜底） | Alpha Vantage 免费宏观端点 |
| A 股/板块行情 | AKShare（新浪源稳，东财源会抖） | cn-financial-mcp（42 工具免 key，财报工具有排序 bug 勿用「最近」口径） |
| 欧美个股/行情 | yfinance / OpenBB | Alpha Vantage |

## 二、统一 Python 环境

统一用 conda 具名环境 `macro-data`（Python 3.11；**禁止建 venv/virtualenv**）：

```bash
conda create -n macro-data python=3.11 -y      # 首次
PY="$(conda info --base)/envs/macro-data/bin/python"
$PY -c "import akshare"                         # 验证可用
```

缺包：`$PY -m pip install akshare dbnomics wbgapi fredapi pandas -i https://pypi.org/simple`（wbgapi 在清华镜像缺包，必须用官方 PyPI）。单建一个环境而不是装进日常共用的环境——akshare 的依赖较重，容易冲掉其他项目钉住的版本。

## 三、各源调用模板

### 1. AKShare（中国宏观/行情首选，免 token）

```bash
$PY - <<'EOF'
import io, contextlib, akshare as ak
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):   # 抑制 tqdm（走 stderr）
    df = ak.macro_china_gdp()          # 或 macro_china_pmi / macro_china_lpr / macro_china_shrzgm(社融)
print(df.head(3).to_string())
EOF
```

- 常用：`macro_china_gdp`、`macro_china_pmi`、`macro_china_lpr`、`macro_china_shrzgm`、`stock_zh_index_daily("sh000001")`
- **坑**：`macro_china_cpi_monthly` / `macro_usa_cpi_monthly` 走金十源，**滞后约一年**——查最新 CPI 改用统计局接口（见第 5 节）或 `macro_china_cpi_yearly`
- **坑**：个股东财源 `stock_zh_a_hist` 会 ConnectionError，用新浪源 `stock_zh_a_daily(symbol="sh600519")` 替代
- 发现接口：`[x for x in dir(ak) if x.startswith('macro_china')]`

### 2. DBnomics（国际宏观默认源，免 key）

```bash
# IMF WEO 中国实际 GDP 增速（注意版本化数据集 WEO:2025-04）
curl -s "https://api.db.nomics.world/v22/series/IMF/WEO:2025-04/CHN.NGDP_RPCH?observations=1"
```

```bash
$PY - <<'EOF'
import dbnomics
df = dbnomics.fetch_series(provider_code="IMF", dataset_code="WEO:2025-04", series_code="CHN.NGDP_RPCH")
assert not df.empty, "空表！检查序列 ID / 数据集版本"
print(df.tail(3))
EOF
```

- **坑**：`fetch_series("IMF/WEO:2025-04/CHN.NGDP_RPCH")` 单字符串形式对带冒号数据集**静默返回空表**，必须用显式参数 + 检查 `df.empty`
- **坑**：镜像索引滞后差异大（实测 WB 滞后 2 年、Eurostat 8 个月、IMF WEO 仅到 2025-04 期）；时效敏感先查 `curl -s https://api.db.nomics.world/v22/last-updates`
- 发现序列四步法：`/v22/providers` → `/v22/datasets/{provider}` → `/v22/series/{provider}/{dataset}?q=关键词`（数据集内搜索实测有效）→ 拉数据；全局 series 搜索无效

### 3. World Bank（wbgapi，5/5）

```bash
$PY - <<'EOF'
import wbgapi as wb
print(wb.series.info(q='GDP growth'))                       # 客户端关键词搜索指标代码
print(wb.data.DataFrame('FP.CPI.TOTL.ZG', 'CHN', time=range(2020,2025)))
EOF
```

免 key。指标代码语义化（NY.GDP.MKTP.CD、FP.CPI.TOTL.ZG），大多可直接猜对。年度数据滞后约 1.5 年属正常。

### 4. FRED（美国宏观金标准）

免 key 兜底（单序列）：
```bash
curl -s "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDP" | tail -3
curl -s "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL" | tail -3
```
- **坑**：多序列混合频率（`id=GDP,CPIAUCSL`）返回 ZIP 而非 CSV；单序列或同频率才直接给 CSV
- 若环境变量或本地配置里已有 `FRED_API_KEY`（检查但不要打印到日志），改用 fredapi：`Fred(api_key=...).get_series('GDP')`；官方 API 限速 120 req/min
- 经济史/预测评估研究用 ALFRED vintage（`get_series_as_of_date`）避免前视偏差

### 5. 国家统计局新 API（中国数据权威核验源）

**旧 easyquery.htm（dbcode=hgyd/hgnd、A010101 那套）2026-03 起全路径 403 废止，网上旧教程全部失效。** 新接口免鉴权/免 cookie：

```bash
BASE="https://data.stats.gov.cn/dg/website/publicrelease/web/external"
# 中文关键词搜索（英文关键词会触发服务端异常页！）
curl -s "$BASE/query?search=居民消费价格&pagenum=1&pageSize=5"
# 取数（POST）
curl -s -X POST "$BASE/stream/esData" -H "Content-Type: application/json" -d '{
  "cid":"<叶子cid>", "indicatorIds":["<指标UUID>"],
  "das":[{"text":"全国","value":"000000000000"}],
  "dts":["202601MM-202608MM"], "showType":"1"}'
```

已实测可用的常用 cid/indicatorId（CPI 同比、GDP 当季、M2 同比）见 `references/common-series.md`，直接复用避免每次遍历。时间编码：月 `202608MM`、季 `202602SS`、年 `2025YY`。未发布月份返回空字符串。辅助脚本：`scripts/nbs_fetch.py`（封装搜索+取数，系统 python3 即可运行）。
- **坑**：搜索端点 `pageSize` 必须 ≤5，≥10 必触发服务端异常 HTML 页；Python urllib 须显式带 UA（脚本已处理）；服务端偶发异常页，需重试

### 6. IMF DataMapper（年度宏观 + 预测，免 key）

```bash
curl -s "https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH"   # 注意 /CHN 过滤不生效，返回全部国家，客户端取 ['values']['NGDP_RPCH']['CHN']
```
- 常用指标：NGDP_RPCH（实际GDP增速）、PCPIPCH（CPI）、NGDPD（GDP美元）、GGXWDG_NGDP（政府债务/GDP）；`/indicators` 一次拉全 132 个
- IMF 新旧 SDMX 端点 2026-09 实测均不可用（502/超时）；要 IFS 月度高频数据降级走 DBnomics `IMF/IFS`

## 四、铁律

1. **取到数先看最新一期日期**是否符合发布节奏（月更 CPI T+10 天左右、季 GDP、年度 WDI 滞后 1.5 年）；明显滞后的源要在交付时说明。
2. 论文/公开稿件引用的关键数字，**用统计局（中国）或 FRED/官方源（国际）核验**，AKShare/DBnomics 是二手镜像。
3. 空表、空字符串、NaN 都要显式检查并如实报告，禁止把「没取到」写成数字。
4. 所有源均无 SLA：批量抓取限速 ≤2 req/s（统计局）/ ≤100 req/min（FRED），带指数退避重试。
5. 接口静默变更时有发生（统计局端点曾悄悄改名）；模板 4xx/5xx 时先查对应测试报告的发现流程重新探路，并把新端点 patch 回本 skill。