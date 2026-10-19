#!/usr/bin/env python3
"""macro-data 环境检查 / 按需安装 / 冒烟测试（macOS、Windows、Linux 通用，只用标准库）。

用法（<PY> 换成你要检查的 Python：macOS 一般是 python3，Windows 是 py 或 python）：
  <PY> check_env.py              只检查，不改动任何东西（默认）
  <PY> check_env.py --install    只装缺的必需包（先清华镜像，失败再阿里云镜像）；已装的不重装
  <PY> check_env.py --install --optional   连同国际数据源的可选包一起装
  <PY> check_env.py --smoke      冒烟测试：统计局取一条 M2、AKShare 取一条 PMI

本脚本兼容 Python 3.8+，这样版本太旧时也能跑起来并告诉你要升级。
"""
import importlib.util, os, platform, shutil, struct, subprocess, sys, sysconfig, time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):          # Windows 控制台默认 GBK，统一 UTF-8 输出
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

MIN_PY = (3, 11)                             # akshare 当前版本要求 Python >= 3.11
REQUIRED = ["akshare"]                       # pandas、requests 等由 akshare 自动带上
OPTIONAL = ["dbnomics", "wbgapi", "fredapi"] # 只在查国际数据时才需要
MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"
BACKUP = "https://mirrors.aliyun.com/pypi/simple/"  # 国内备用镜像；本课按国内网络环境，不回退到境外官方源


def pkg_version(name):
    if importlib.util.find_spec(name) is None:
        return None
    try:
        from importlib.metadata import version
        return version(name)
    except Exception:
        return "已安装"


def pip_ok():
    r = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, text=True)
    return r.returncode == 0, (r.stdout or r.stderr).strip()


def env_kind():
    if (Path(sys.prefix) / "conda-meta").exists():
        return "conda 环境（%s）" % Path(sys.prefix).name
    if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        return "虚拟环境"
    return "系统 Python"


def externally_managed():
    # Homebrew 等发行版的 Python 带这个标记，pip 会拒绝直接安装（PEP 668）
    return (Path(sysconfig.get_paths()["stdlib"]) / "EXTERNALLY-MANAGED").exists()


def need_user_flag():
    purelib = sysconfig.get_paths()["purelib"]
    return env_kind() == "系统 Python" and not os.access(purelib, os.W_OK)


def conda_info():
    exe = shutil.which("conda")
    if not exe:
        return None, None
    try:
        base = subprocess.run([exe, "info", "--base"], capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:
        return exe, None
    return exe, base


def check():
    print("== macro-data 环境检查 ==")
    print("操作系统    :", platform.system(), platform.release(), platform.machine())
    print("Python 路径 :", sys.executable)
    ver = sys.version_info
    ver_ok = ver[:2] >= MIN_PY
    print("Python 版本 : %d.%d.%d  %s" % (ver[0], ver[1], ver[2],
          "OK" if ver_ok else "太旧，需要 >= %d.%d" % MIN_PY))
    bits = struct.calcsize("P") * 8
    print("Python 位数 : %d 位%s" % (bits, "" if bits == 64 else "  !! 需要 64 位 Python，32 位装不上 akshare 的依赖"))
    print("环境类型    :", env_kind())
    ok, msg = pip_ok()
    print("pip         :", msg if ok else "不可用 -> 先运行 <PY> -m ensurepip --upgrade")
    exe, base = conda_info()
    if exe:
        envdir = Path(base) / "envs" / "macro-data" if base else None
        has_env = bool(envdir and envdir.exists())
        print("conda       : 有（%s）；macro-data 环境%s" % (exe, "已存在" if has_env else "不存在"))
    else:
        print("conda       : 未检测到（用系统 Python + pip 即可，不必装 conda）")
    missing = []
    for name in REQUIRED:
        v = pkg_version(name)
        print("必需包 %-9s: %s" % (name, v or "缺"))
        if not v:
            missing.append(name)
    for name in OPTIONAL:
        print("可选包 %-9s: %s" % (name, pkg_version(name) or "未装（查国际数据时再装）"))
    em = externally_managed()
    if em:
        print("!! 这个 Python 是 Homebrew/系统托管的（EXTERNALLY-MANAGED），pip 会拒绝安装；"
              "改用 python.org 安装包装的 Python 或 conda 环境")
    print("安装位置    :", sysconfig.get_paths()["purelib"] + ("（无写权限，将加 --user 装到用户目录）" if need_user_flag() else ""))
    if not ver_ok:
        print("STATUS: PYTHON_TOO_OLD")
    elif not ok:
        print("STATUS: NO_PIP")
    elif em and missing:
        print("STATUS: EXTERNALLY_MANAGED")
    elif missing:
        print("STATUS: MISSING " + " ".join(missing))
    else:
        print("STATUS: READY")
    return ver_ok, ok, missing


def pip_install(pkgs):
    base = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check"]
    if need_user_flag():
        base.append("--user")
    for index in (MIRROR, BACKUP):
        print(">> pip install %s  (源: %s)" % (" ".join(pkgs), index), flush=True)
        r = subprocess.run(base + pkgs + ["-i", index, "--timeout", "60"])
        if r.returncode == 0:
            return True
        print("!! 这个源安装失败，换下一个源重试", flush=True)
    return False


def install(with_optional):
    ver_ok, ok, missing = check()
    if not ver_ok or not ok:
        print("先解决上面的 Python 版本或 pip 问题，再安装包。")
        return 1
    if externally_managed() and missing:
        print("这个 Python 不允许 pip 安装，停止。")
        return 1
    todo = missing + ([p for p in OPTIONAL if not pkg_version(p)] if with_optional else [])
    if not todo:
        print("没有需要安装的包，已跳过（不重装）。")
        return 0
    if not pip_install(todo):
        print("STATUS: INSTALL_FAILED（见上方 pip 报错，按 SKILL.md 的常见报错表处理）")
        return 1
    importlib.invalidate_caches()
    print("安装完成，复查：")
    return 0 if check()[2] == [] else 1


def smoke():
    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    sys.dont_write_bytecode = True           # 不在 skill 目录里留 __pycache__
    ok_all = True
    # 1) 国家统计局：M2 同比（单一叶子，1999 至今），取最近 6 个月
    try:
        import nbs_fetch
        t = time.localtime()
        y, m = t.tm_year, t.tm_mon
        y0, m0 = (y, m - 5) if m > 5 else (y - 1, m + 7)
        dts = "%d%02dMM-%d%02dMM" % (y0, m0, y, m)
        rows = nbs_fetch.data("82130c6621a745cda3d64b090e733383", "e03f2232631f41cd9d754a7d7feb4a81", dts, quiet=True)
        got = [r for r in rows if r[2]]      # 接口按时间倒序返回，got[0] 是最新一期
        if got:
            print("[统计局] OK  M2 同比 %s = %s%s（区间 %s，共 %d 期有值）" % (got[0][0], got[0][2], got[0][3], dts, len(got)))
        else:
            ok_all = False
            print("[统计局] 失败：返回为空（区间 %s）" % dts)
    except Exception as e:
        ok_all = False
        print("[统计局] 失败：%s: %s" % (type(e).__name__, e))
    # 2) AKShare：中国官方制造业 PMI
    try:
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            import akshare as ak
            df = ak.macro_china_pmi()
        if df is None or df.empty:
            ok_all = False
            print("[AKShare] 失败：返回空表")
        else:
            row = df.iloc[0]
            print("[AKShare] OK  akshare %s，macro_china_pmi 共 %d 行，第一行：%s" % (
                getattr(ak, "__version__", "?"), len(df), " | ".join(str(x) for x in row.tolist()[:3])))
    except Exception as e:
        ok_all = False
        print("[AKShare] 失败：%s: %s" % (type(e).__name__, e))
    print("SMOKE: " + ("PASS" if ok_all else "FAIL"))
    return 0 if ok_all else 1


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--smoke" in args:
        sys.exit(smoke())
    if "--install" in args:
        sys.exit(install("--optional" in args))
    check()
