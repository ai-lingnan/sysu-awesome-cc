---
name: macro-data
description: "Use when 查中国或国际宏观/财经数据（GDP、CPI、PMI、社融、利率等）。按 2026-09 实测模板取数；首次使用先检查环境，按 macOS/Windows 引导安装 Python 与 AKShare。"
tags: [economics, data]
---

# 宏观/财经数据取数（2026-09 实测版）

所有模板均来自 2026-09-21 对十个数据源的逐一真实拉取测试。**只按本 skill 的模板取数；模板失效时按第 5 节/第四节铁律里的发现流程重新探路，不要编造数据。**

## 〇、首次使用：环境检查与安装

每个会话第一次取数前先做第 1 步检查（环境已就绪时几秒钟完成，直接去第一节）。使用者可能是没装过 Python、不熟悉终端的本科生：命令由你来执行；需要用户自己动手的地方（双击安装包、勾选框、改系统设置）一步一步说清点哪里；每一步用一句大白话告诉用户在做什么。下文 `<SKILL_DIR>` 指本 SKILL.md 所在目录，`<PY>` 指要用的 Python 解释器。

**最小依赖**（2026-09-27 按代码核实）：

| 用途 | 需要装什么 | 说明 |
|---|---|---|
| 国家统计局（`scripts/nbs_fetch.py`） | Python 3 | 只用标准库，不装任何包 |
| AKShare（中国宏观、行情） | Python ≥ 3.11 + `akshare` | pandas、requests、lxml 等由 pip 自动带上；课程练习只需这一项 |
| 国际源（第三节 2–4） | `dbnomics`、`wbgapi`、`fredapi` | 可选，查国际数据时再装 |

conda 不是必需：已有 conda 的用 conda 具名环境，没有的用系统 Python 加 pip。**不建 venv/virtualenv。** Python 推荐 3.12 或 3.13（3.11–3.14 均可）。

### 第 1 步：检查（只读，不改任何东西）

先找到一个 Python：

- macOS：`python3 --version`；有 conda 的再看 `conda env list` 里有没有 `macro-data` 环境，有就用 `"$(conda info --base)/envs/macro-data/bin/python"`
- Windows（PowerShell）：依次试 `py --version`、`python --version`、`where.exe python`；有 conda 的看 `conda env list`，`macro-data` 环境的解释器是 `"$(conda info --base)\envs\macro-data\python.exe"`
- 一个都没有，或版本低于 3.11，就去第 3 步装 Python

再运行检查脚本：`<PY> "<SKILL_DIR>/scripts/check_env.py"`。它打印操作系统、Python 路径与版本、pip、conda、各包是否已装、包会装到哪里，最后一行是结论：

| 最后一行 | 下一步 |
|---|---|
| `STATUS: READY` | 环境可用，不需要安装。首次使用跑一次第 4 步冒烟测试，之后直接取数 |
| `STATUS: MISSING akshare` | 第 2 步征得同意，再第 3 步装包 |
| `STATUS: PYTHON_TOO_OLD` | 第 2 步征得同意，再第 3 步装 Python |
| `STATUS: NO_PIP` | 征得同意后运行 `<PY> -m ensurepip --upgrade` |
| `STATUS: EXTERNALLY_MANAGED` | 这是 Homebrew/系统托管的 Python，不能 pip 安装；改用 python.org 安装包或 conda 环境 |

记下检查结果里的「Python 路径」，后文所有 `$PY` / `<PY>` 都用这个完整路径，保证装包和运行用的是同一个 Python。

### 第 2 步：先说明，得到同意再安装

动手安装前，用一段话告诉用户：要装什么（名称和版本，例如“Python 3.13”“akshare 及其依赖共 27 个包，下载约 50 MB”）、装到哪里（检查结果里的「安装位置」，或 conda 环境路径）、从哪里下载（清华镜像，失败再用 PyPI 官方源）、大约要几分钟。**得到用户明确同意后再执行。** 检查结果里已经装好的不重装、不升级；用户不同意就停下，把下面的手动步骤告诉他。

### 第 3 步：安装（缺什么装什么）

**macOS**

1. 已有 conda，且没有 `macro-data` 环境：`conda create -n macro-data python=3.12 -y`，之后 `PY="$(conda info --base)/envs/macro-data/bin/python"`
2. 没有 conda，缺 Python 或版本低于 3.11：让用户打开 https://www.python.org/downloads/macos/ ，下载 3.13 的 “macOS 64-bit universal2 installer”（.pkg），双击按默认选项装完；**再到「应用程序 → Python 3.13」双击 `Install Certificates.command`**（不做这步，取数会报 SSL 证书错误）。然后新开一个终端窗口，`python3 --version` 应显示 3.13。不要用 Homebrew 的 Python（pip 会拒绝安装），也不要用系统自带的 `/usr/bin/python3`（3.9，太旧；首次运行还会弹窗要求装“命令行开发者工具”）
3. 装包：`<PY> "<SKILL_DIR>/scripts/check_env.py" --install`。脚本只装缺的包，先用清华镜像，失败自动换官方源；没有写权限时自动加 `--user` 装到用户目录。等价的手动命令：`<PY> -m pip install akshare -i https://pypi.tuna.tsinghua.edu.cn/simple`，失败再把 `-i` 换成 `https://pypi.org/simple`

**Windows（PowerShell）**

1. 已有 Anaconda/Miniconda，且没有 `macro-data` 环境：`conda create -n macro-data python=3.12 -y`，之后 `$PY = "$(conda info --base)\envs\macro-data\python.exe"`，用 `& $PY ...` 调用（不必 `conda activate`）
2. 没有 conda，缺 Python 或版本低于 3.11，二选一：
   - winget：`winget install -e --id Python.Python.3.13 --scope user`（官方安装包，装到用户目录，自动加入 PATH，不需要管理员）
   - 官网：让用户打开 https://www.python.org/downloads/windows/ ，下载 3.13 的 “Windows installer (64-bit)”，双击后**先勾选第一页底部的 “Add python.exe to PATH”**，再点 “Install Now”。如果下载到的是 “Python install manager”，也可以用：装完在新窗口运行 `py install 3.13`
3. 装完**关闭所有 PowerShell、VS Code 和 Claude Code 窗口再重新打开**，PATH 只对新窗口生效
4. 分清 `python` 和 `py`：`py` 是 Python 启动器，按注册表找已装的 Python，不依赖 PATH，官网安装包默认会装上；`python` 按 PATH 找，找不到时会落到 Microsoft Store 的占位符。`python3` 在 Windows 上多数情况是占位符（只有 Python install manager 附带一个兼容别名），不要依赖它。拿到完整路径最稳：`$PY = (py -3 -c "import sys; print(sys.executable)")`（旧式启动器和新的 install manager 都支持 `py -3`），之后一律 `& $PY ...`
5. Microsoft Store 占位符的样子：`python` 输出 “Python was not found; run without arguments to install from the Microsoft Store...”，或者直接弹出商店；`where.exe python` 第一行是 `...\AppData\Local\Microsoft\WindowsApps\python.exe`。解决：改用 `py`；或让用户打开「设置 → 应用 → 高级应用设置 → 应用执行别名」，关掉“应用安装程序 python.exe / python3.exe”两项。例外：用 Python install manager 或 Microsoft Store 装的 Python，WindowsApps 里的 `python.exe` 就是正式入口，只要 `python --version` 能输出版本号就不要关
6. 装包：`& $PY "<SKILL_DIR>\scripts\check_env.py" --install`，行为同 macOS

国际源可选包：`<PY> "<SKILL_DIR>/scripts/check_env.py" --install --optional`（同样先征得同意）。

### 第 4 步：冒烟测试

`<PY> "<SKILL_DIR>/scripts/check_env.py" --smoke`：从统计局取最近几个月的 M2 同比、从 AKShare 取官方制造业 PMI，各打印一行。最后一行 `SMOKE: PASS` 即环境可用；`FAIL` 按下表排查。2026-09-27 macOS 实测输出：

```txt
[统计局] OK  M2 同比 2026年7月 = 7.7%（区间 202604MM-202609MM，共 4 期有值）
[AKShare] OK  akshare 1.18.97，macro_china_pmi 共 224 行，第一行：2026年08月份 | 49.8 | 0.8097166
SMOKE: PASS
```

### 常见报错

| 现象 | 原因 | 解决 |
|---|---|---|
| `python` / `py` 不是内部或外部命令；`command not found` | 没装 Python，或 PATH 没生效 | 关掉终端和编辑器重开；Windows 改用 `py`；仍不行就重装并勾选 “Add python.exe to PATH” |
| `Python was not found; run without arguments to install from the Microsoft Store` | Windows 的 Store 占位符 | 见上文 Windows 第 5 条 |
| `pip` 不是命令 | pip 的 Scripts 目录不在 PATH | 不直接敲 `pip`，一律用 `<PY> -m pip` |
| `No matching distribution found for akshare`，或提示 `Requires-Python >=3.11` | Python 版本太旧 | 装 Python 3.12/3.13 后重跑检查 |
| Windows 上装 `mini-racer` 失败、要求编译器或 `Microsoft Visual C++ 14.0 is required` | 装的是 32 位 Python（mini-racer 没有 32 位安装包） | 看检查脚本的「Python 位数」一行；卸掉后重装 “Windows installer (64-bit)” |
| `ModuleNotFoundError: No module named 'akshare'`，但刚装过 | 装进了另一个 Python | 装包和运行用同一个 `<PY>` 完整路径；以检查脚本打印的「Python 路径」为准 |
| pip `ReadTimeoutError`、`ConnectionError`、`ProxyError` | 网络不通或代理干扰 | 脚本已按“清华镜像 → 官方源”自动重试；开着 VPN/代理的，把全局模式改成规则模式或暂时关闭；校园网先确认已登录 |
| 取数时 `ProxyError`、`RemoteDisconnected`、超时 | 代理把国内网站绕到境外 | 统计局和 AKShare 都是国内源，直连最稳：关掉全局代理；清掉代理环境变量（macOS `unset HTTP_PROXY HTTPS_PROXY`，PowerShell `Remove-Item Env:HTTP_PROXY, Env:HTTPS_PROXY -ErrorAction SilentlyContinue`） |
| `SSL: CERTIFICATE_VERIFY_FAILED` | macOS：python.org 版 Python 没装证书；Windows：杀毒软件或公司网络拦截 HTTPS | macOS 双击「应用程序 → Python 3.x → Install Certificates.command」；Windows 暂时关闭杀毒软件的 HTTPS 扫描或换网络。只有 pip 装包可临时加 `--trusted-host pypi.tuna.tsinghua.edu.cn`，取数不要关证书校验 |
| `SSLEOFError`、`SSLError` 偶发 | 代理或服务器抖动 | 关代理后重试 |
| `[WinError 5] 拒绝访问`、`Permission denied`、`Consider using the --user option` | 往系统目录装包没有权限 | 检查脚本会自动加 `--user`；手动安装时加 `--user`。不要用管理员 PowerShell 或 `sudo pip` |
| `error: externally-managed-environment` | Homebrew 或系统托管的 Python | 改用 python.org 安装包或 conda 环境；不要加 `--break-system-packages` |
| PowerShell 提示“禁止运行脚本”（`conda activate` 时） | PowerShell 执行策略 | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`；或不 activate，直接用 `python.exe` 完整路径 |
| `UnicodeEncodeError: 'gbk' codec`、中文乱码 | Windows 控制台默认 GBK 编码 | 先设 `$env:PYTHONUTF8=1`（PowerShell）或 `export PYTHONUTF8=1`（Git Bash） |

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

解释器记作 `$PY`，取第〇节检查脚本打印的「Python 路径」。已有 conda 的用具名环境 `macro-data`（Python 3.11 及以上）；没有 conda 的用系统 Python + pip，不必为此装 conda。**禁止建 venv/virtualenv。**

```bash
# macOS / Linux（有 conda）
conda create -n macro-data python=3.12 -y      # 首次；环境已存在就跳过
PY="$(conda info --base)/envs/macro-data/bin/python"
$PY -c "import akshare"                         # 验证可用
```

```powershell
# Windows PowerShell
$PY = "$(conda info --base)\envs\macro-data\python.exe"      # 有 conda
$PY = (py -3 -c "import sys; print(sys.executable)")          # 没有 conda
& $PY -c "import akshare"                                     # 验证可用
```

缺包：`$PY -m pip install akshare dbnomics wbgapi fredapi pandas -i https://pypi.org/simple`（wbgapi 在清华镜像缺包，必须用官方 PyPI；2026-09-27 复查清华镜像已有 wbgapi 1.0.14，镜像失败时仍走官方源）。只装当前任务要用的包，课程练习只需 akshare，推荐用第〇节的 `check_env.py --install`（先镜像后官方源、已装的跳过）。有 conda 的单建一个环境而不是装进日常共用的环境——akshare 的依赖较重，容易冲掉其他项目钉住的版本。

## 三、各源调用模板

下面的模板按 bash 写。Windows 上：Claude Code 装了 Git for Windows 时 Bash 工具就是 Git Bash，`$PY - <<'EOF'` 写法可以照用（`$PY` 用正斜杠路径，如 `C:/Users/<用户名>/AppData/Local/Programs/Python/Python313/python.exe`）；在 PowerShell 里没有 heredoc，把代码存成 `.py` 文件再 `& $PY 文件.py`，`curl` 要写成 `curl.exe`，`| tail -3` 改成 `| Select-Object -Last 3`。

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

已实测可用的常用 cid/indicatorId（CPI 同比、GDP 当季、M2 同比）见 `references/common-series.md`，直接复用避免每次遍历。时间编码：月 `202608MM`、季 `202602SS`、年 `2025YY`。未发布月份返回空字符串。辅助脚本：`scripts/nbs_fetch.py`（封装搜索+取数，只用标准库，任何 Python 3 都能运行：macOS `python3`、Windows `py`，或直接用 `$PY`）。
- **坑**：搜索端点 `pageSize` 必须 ≤5，≥10 必触发服务端异常 HTML 页；Python urllib 须显式带 UA（脚本已处理）；服务端偶发异常页，需重试
- **坑**：`esData` 按时间倒序返回（第一行是区间内最新一期，含未发布的空值期），取“最新值”要跳过空值后取第一条

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