# 常用序列 ID 速查（2026-09-21 实测有效）

## 国家统计局新 API（cid / indicatorId 均为 UUID，直接复用）

BASE = `https://data.stats.gov.cn/dg/website/publicrelease/web/external`，取数 POST `$BASE/stream/esData`，全国地区码 `000000000000`。

| 指标 | 频率 code | cid | indicatorId | 备注 |
|---|---|---|---|---|
| CPI 同比（上年同月=100） | 月度 1 | `5c7452825c7c4dcba391db5ca7f335c5`（2026- 分片） | `53180dfb9c14411ba4b762307c85920c` | 长序列另有 (2021-2025)/(2016-2020)/(-2015) 分片 cid，需树遍历拼接 |
| GDP 当季值（亿元，现价） | 季度 2 | `28d936104e304aa191e338eb82b6dc09` | `d22612f09aeb4241bc557ef0ac61b3ba` | 国民经济核算 → 国内生产总值(现价) |
| M2 同比（%） | 月度 1 | `82130c6621a745cda3d64b090e733383` | `e03f2232631f41cd9d754a7d7feb4a81` | 1999 至今单一叶子，未分片 |

树根：月度 `fc982599aa684be7969d7b90b1bd0e84`（code=1）、季度 `a94b8b7365a94874968cabbe392cf679`（code=2）。
树遍历：GET `$BASE/new/queryIndexTreeAsync?pid=<父节点>&code=<1/2/3>` → 叶子后 GET `$BASE/new/queryIndicatorsByCid?cid=<cid>`。
搜索（仅中文关键词）：GET `$BASE/query?search=<中文指标名>&pagenum=1&pageSize=5`。

## DBnomics 三段式 ID（provider/dataset/series）

| 指标 | ID |
|---|---|
| IMF WEO 中国实际 GDP 增速 | `IMF/WEO:2025-04/CHN.NGDP_RPCH`（取最新 WEO 版本号先查 `/v22/datasets/IMF`） |
| WB WDI 中国 CPI 年通胀 | `WB/WDI/A-FP.CPI.TOTL.ZG-CHN`（镜像滞后，优先 wbgapi） |
| Eurostat 欧元区 HICP 年率（月） | `Eurostat/prc_hicp_manr/M.RCH_A.CP00.EA20` |

## FRED 常用 series_id

GDP（名义，季）、GDPC1（实际）、CPIAUCSL（CPI 月）、UNRATE（失业率）、FEDFUNDS（联邦基金利率）、DGS10（10 年期国债收益率）、DEXCHUS（人民币兑美元）。

## IMF DataMapper 常用指标

NGDP_RPCH（实际 GDP 增速）、PCPIPCH（CPI 年通胀）、NGDPD（GDP 现价美元）、NGDPDPC（人均 GDP 美元）、GGXWDG_NGDP（政府总债务/GDP）、BCA_NGDPD（经常账户/GDP）、LUR（失业率）。

## World Bank 常用指标代码

NY.GDP.MKTP.CD（GDP 现价美元）、NY.GDP.MKTP.KD.ZG（GDP 增速）、FP.CPI.TOTL.ZG（CPI 通胀）、SL.UEM.TOTL.ZS（失业率）、NE.EXP.GNFS.ZS（出口占 GDP）、FS.AST.PRVT.GD.ZS（私人信贷/GDP）。
