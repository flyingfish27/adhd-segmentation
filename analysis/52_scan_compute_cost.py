# -*- coding: utf-8 -*-
# =============================================================================
# 52_scan_compute_cost.py  —  "把参数扫开、把特征加多"要花多少算力的成本探针
# =============================================================================
# 这是什么(给未来任何一个不了解本项目的人):
#   这个文件【不是】生产管线的一部分,不产生任何特征、不写任何文件、不进 features.csv。
#   它是一只【探针(probe)】——在真实数据上把几个数字摊开,供人拍板,跑完只在终端打印。
#   "探针"是本项目里一类脚本的固定叫法(见 analysis/32_、33_、50_、51_),含义=探索性、
#   只读、只打印、结论供人决策,不参与生产链路。
#
# 只读:仅读 data/ 下的原始腕表文件 + figures/subject_audit.csv(24 人名单)。不写盘。
#   符合本项目 data/ 只读约定(有 PreToolUse 钩子强制)。
#
# 它给哪些决策供数:
#
#   探针 1 —— 滑窗扫描的算力与列数成本   → 供 TASK-108 / ISSUE-115
#     背景:特征脚本 analysis/42_features_full.py 里那族"时间结构"特征(活动段/静止段
#       时长、每分钟活动↔静止切换次数等),算法是先把动作强度信号按【滑动窗口】聚合,
#       再卡阈值二值化,最后统计各段时长。它有 4 个参数:窗长 win_s、步长 step_s、
#       阈值百分位 pct、短段上限 short_s。目前阈值已扫 9 档(第 177 行 PCTS),
#       但窗长/步长/短段是写死的单值(第 179 行 TS_WIN_S,TS_STEP_S,TS_SHORT_S = 10,5,10)。
#     问题:若把窗长/步长也扩成 5 组扫描,要多花多少时间、特征表要多出多少列?
#     算法:直接调用生产代码里的 time_structure() 本尊(import 进来,不复制一份),
#       对 5 组窗配置各计时;列数按各指标对哪些参数敏感来推算。
#     注意:本探针计的是【特征提取】那一步的时间。真正的大头在下游 A 轨的置换检验,
#       那部分不读信号,由 analysis/53_stat_budget_probes.py 的探针 1 估算。
#
#   探针 2 —— 尚未实现的那几类特征算不算得动   → 供 TASK-10
#     背景:TASK-10 列了 7 大类"完全没算"的特征,其中第 1 类(非线性/复杂度)含
#       DFA、样本熵、排列熵、Hurst、RQA、LZ 复杂度等。这些算法的复杂度差别极大,
#       有的是线性时间、有的是平方时间——在单人 7 万多个采样点上,后者可能根本跑不动。
#     算法:对能直接算的(DFA/排列熵/自相关/LZ)实测单人耗时;对平方复杂度的样本熵,
#       在小规模上实测再按 O(N²) 外推;对 RQA 直接算它的递归矩阵要占多少内存。
#     用途:让"补哪几类特征"这个决定建立在实测成本上,而不是"感觉能跑"。
#
# 【本探针不做自相关衰减时间尺度】——那件事已由 analysis/50_temporal_design_probes.py
#   的探针 1 完成,快照在 analysis/probe_outputs/autocorr_timescale.md(未截断信号、
#   无滞后上限)。本文件不重复测,以免出现两份讲同一个量的快照。
#
# 复现:
#   ADHD_ROOT=<有 data/ 的仓库根> .venv/bin/python analysis/52_scan_compute_cost.py
# =============================================================================
import os, sys, time, math, pathlib, importlib.util
import numpy as np, pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path(os.environ.get("ADHD_ROOT", HERE.parent)).resolve()
if not (ROOT / "data").is_dir():
    sys.exit(f"找不到 {ROOT}/data —— 请把环境变量 ADHD_ROOT 指向有 data/ 的主检出。")

# 把生产脚本 import 进来,直接用它的 load_T / time_structure 本尊计时。
# 42_features_full.py 的主循环收在 __main__ 保护里,import 不会触发它跑全量特征提取。
_spec = importlib.util.spec_from_file_location("f42", HERE / "42_features_full.py")
f42 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(f42)

def banner(title, *notes):
    print("\n" + "#" * 80)
    print(f"# {title}")
    for n in notes:
        print(f"#   {n}")
    print("#" * 80)

# ---------- 取一个被试的信号当计时样本 ----------
AUD = pd.read_csv(ROOT / "figures/subject_audit.csv")
SUBJ = sorted(AUD[(AUD.status == "usable") &
                  (AUD["_T"].astype(str).str.lower() == "yes")].subject.tolist())
assert len(SUBJ) == 24, f"可用被试应为 24 人,实得 {len(SUBJ)}"
BENCH_SUBJ = "H45"                      # 固定用同一人,让不同次运行可比
df, fs, t, n_full = f42.load_T(ROOT / f"data/{BENCH_SUBJ}_T.csv")
ua = df[f42.USER_ACC].astype(float).to_numpy()
mag = np.linalg.norm(ua, axis=1)
N = len(mag)

print(f"计时样本被试 = {BENCH_SUBJ}   信号点数 N = {N:,}   采样率 fs = {fs:.3f} Hz"
      f"   时长 = {N/fs/60:.2f} 分钟")
print(f"(N 已按 42_features_full.py 的 N_TRUNC={f42.N_TRUNC} 截断,与 features.csv 口径一致)")
print(f"全体被试数 = {len(SUBJ)}")

# =============================================================================
# 探针 1  滑窗扫描的算力与列数成本
# =============================================================================
GRID = [(0.5, 0.25), (1, 0.5), (2, 1), (5, 2.5), (10, 5)]   # ISSUE-115 裁定的 5 组
PCTS = f42.PCTS
# 2026-07-26(TASK-108 落地后)改:42_features_full.py 里的 TS_WIN_S/TS_STEP_S 两个单值常量
#   已被 TS_WINS(5 组窗配置的元组)取代,这里改从 TS_WINS 的最后一组取"改动前的现状值 (10,5)"。
#   ⚠️ 本脚本探针1 的既有快照 analysis/probe_outputs/scan_window_cost.md 是【TASK-108 之前】
#      的产物,其"现状 = 单组窗配置"的表述描述的是那时的状态;重跑本脚本不会改变结论
#      (它测的是各窗配置的单次调用耗时),只是"现状"一词此后指扫描本身。
CUR_WIN, CUR_STEP = f42.TS_WINS[-1]
CUR_SHORT = f42.TS_SHORT_S

banner("探针1  滑窗扫描的算力与列数成本(供 TASK-108 / ISSUE-115)",
       f"现状:窗长/步长写死为 ({CUR_WIN}, {CUR_STEP}) 秒,短段上限 {CUR_SHORT} 秒"
       f"(42_features_full.py:179)",
       f"拟扫:{len(GRID)} 组窗配置 {GRID} 秒,阈值沿用 {len(PCTS)} 档 {PCTS}",
       "下表 t_call = 生产函数 time_structure() 单人单次调用耗时")

rows = []
for w, s in GRID:
    t0 = time.time()
    r = f42.time_structure(mag, t, fs, win_s=w, step_s=s, pct=50, short_s=CUR_SHORT)
    dt = time.time() - t0
    nwin = int((N - int(w * fs)) / int(s * fs))
    rows.append(dict(win_s=w, step_s=s, n_windows=nwin, t_call_s=round(dt, 4),
                     全体秒=round(dt * len(PCTS) * len(SUBJ), 1),
                     act_bout_median=r["act_bout_median"], n_bouts=r["n_bouts"]))
cost = pd.DataFrame(rows)
print()
print(cost.to_string(index=False))
print()
print(f"  合计特征提取增量 ≈ {cost['全体秒'].sum():.0f} 秒"
      f"({len(GRID)} 组窗配置 × {len(PCTS)} 档阈值 × {len(SUBJ)} 人)")
print(f"  现状(单组窗配置)耗时 ≈ "
      f"{cost.loc[cost.win_s == CUR_WIN, '全体秒'].iloc[0]:.1f} 秒")

# ---- 列数推算 ----
# time_structure() 返回的键里,随 pct 变的有 6 个;within_win_sd 只随窗配置变;
# mag_median/dur_min/n_bouts 不进特征表(它们是诊断量)。
N_PCT_DEP = 6          # switch_per_min, act_bout_median, stl_bout_median,
                       # act_bout_cv, stl_bout_cv, frac_act_short
N_WIN_DEP = 1          # within_win_sd
N_PATH_B  = 5          # 路径B(逐采样点法 f_tstruct)的 5 个指标,不受窗参数影响
cur_cols = pd.read_csv(ROOT / "analysis/features.csv").shape[1] - 1
pathA_cur = N_PCT_DEP * len(PCTS) + N_WIN_DEP
pathA_new = (N_PCT_DEP * len(PCTS) + N_WIN_DEP) * len(GRID)
print()
print("  --- 特征表列数推算 ---")
print(f"  路径A(滑窗法)每组窗配置 = {N_PCT_DEP} 个随阈值变的指标 × {len(PCTS)} 档"
      f" + {N_WIN_DEP} 个只随窗变的 = {pathA_cur} 列")
print(f"  现状 路径A = {pathA_cur} 列(1 组窗配置)  ->  扫描后 = {pathA_new} 列"
      f"({len(GRID)} 组)")
print(f"  路径B(逐采样点法)= {N_PATH_B} × {len(PCTS)} = {N_PATH_B*len(PCTS)} 列(不受窗参数影响)")
print(f"  features.csv 现有总列数(实测)= {cur_cols}")
print(f"  扫描后总列数 = {cur_cols} - {pathA_cur} + {pathA_new} = {cur_cols - pathA_cur + pathA_new}")

# ---- 耦合约束:段时长分辨率 ----
print()
print("  --- 耦合约束:活动段时长的分辨率 = 步长 ---")
print("  依据 42_features_full.py:155  durs = np.diff(edges) * step_s")
print("  即段时长按构造必为 step_s 的整数倍,故任何小于 step_s 的 short_s 取值都不可分辨。")
_fas = {}
for w, s in GRID:
    r = f42.time_structure(mag, t, fs, win_s=w, step_s=s, pct=50, short_s=CUR_SHORT)
    n_levels = int(CUR_SHORT / s)
    _fas[(w, s)] = r["frac_act_short"]
    print(f"    win={w:4}s step={s:5}s -> 段时长分辨率 {s:5} 秒;"
          f"short_s={CUR_SHORT} 秒 覆盖 {n_levels:3d} 个可分辨档位;"
          f"frac_act_short={r['frac_act_short']:.4f}")
_coarse, _fine = int(CUR_SHORT / GRID[-1][1]), int(CUR_SHORT / GRID[0][1])
print(f"  -> 同一列 frac_act_short:最粗设定(step={GRID[-1][1]}s)下只有 {_coarse} 个可分辨档位,"
      f"最细设定(step={GRID[0][1]}s)下有 {_fine} 个,相差 {_fine//_coarse} 倍。")
print(f"     其数值随设定单调变化(实测 {_fas[GRID[-1]]:.4f} -> {_fas[GRID[0]]:.4f}),"
      f"跨设定横向比较该列时须知情。")

# =============================================================================
# 探针 2  尚未实现的特征大类算不算得动
# =============================================================================
banner("探针2  TASK-10 待补特征大类的算力可行性",
       f"单人 N = {N:,} 点;全体 {len(SUBJ)} 人",
       "线性/近线性复杂度的直接实测;平方复杂度的小规模实测 + O(N²) 外推")

def dfa(x):
    """去趋势波动分析:返回标度指数 alpha。O(N log N) 量级。"""
    y = np.cumsum(x - x.mean())
    scales = np.unique(np.logspace(1, np.log10(len(x) // 4), 20).astype(int))
    F = []
    used = []
    for s in scales:
        n = len(y) // s
        if n < 2:
            continue
        seg = y[:n * s].reshape(n, s)
        tt = np.arange(s)
        c = np.polyfit(tt, seg.T, 1)
        fit = np.outer(c[0], tt) + c[1][:, None]
        F.append(np.sqrt(((seg - fit) ** 2).mean()))
        used.append(s)
    return float(np.polyfit(np.log(used), np.log(F), 1)[0])

def perm_entropy(x, m=4, tau=1):
    """排列熵(归一化到 0–1)。O(N) 量级。"""
    n = len(x) - (m - 1) * tau
    idx = np.arange(m) * tau
    win = x[np.arange(n)[:, None] + idx]
    order = np.argsort(win, axis=1)
    key = (order * (m ** np.arange(m))).sum(1)
    _, cnt = np.unique(key, return_counts=True)
    p = cnt / cnt.sum()
    return float(-(p * np.log(p)).sum() / np.log(math.factorial(m)))

def lz_complexity(x):
    """Lempel-Ziv 复杂度(按中位数二值化后计子串数)。O(N) 量级。"""
    s = (x > np.median(x)).astype(np.uint8)
    s = s.tobytes().decode("latin1")
    i, k, l, c, n = 0, 1, 1, 1, len(s)
    while True:
        if l + k > n:
            c += 1
            break
        if s[i:i + k] == s[l:l + k]:
            k += 1
        else:
            c += 1
            l += k
            i = 0
            k = 1
            if l + 1 > n:
                break
    return c

def acf_dominant_period(x, lo=10, hi=3000):
    """自相关主周期(滞后点数)。用 FFT,O(N log N)。"""
    y = x - x.mean()
    f = np.fft.rfft(y, 2 * len(y))
    a = np.fft.irfft(f * np.conj(f))[:len(y)] / np.dot(y, y)
    return float(np.argmax(a[lo:hi]) + lo)

print()
print("  --- 可直接全长计算的(单人实测)---")
for name, fn in [("DFA 标度指数", lambda: dfa(mag)),
                 ("排列熵 PermEn(m=4)", lambda: perm_entropy(mag)),
                 ("LZ 复杂度", lambda: lz_complexity(mag)),
                 ("自相关主周期(FFT)", lambda: acf_dominant_period(mag))]:
    t0 = time.time()
    v = fn()
    dt = time.time() - t0
    print(f"    {name:22s} {dt:7.3f} 秒/人  -> 全体 {len(SUBJ)} 人 "
          f"{dt*len(SUBJ):7.2f} 秒   实测值={v:.4f}")

print()
print("  --- 平方复杂度的:样本熵 SampEn(小规模实测 + O(N²) 外推)---")
def sample_entropy(z, m=2, r_ratio=0.2):
    r = r_ratio * z.std()
    n = len(z)
    def count(mm):
        tpl = np.lib.stride_tricks.sliding_window_view(z, mm)
        c = 0
        for i in range(len(tpl)):
            c += int(np.sum(np.max(np.abs(tpl - tpl[i]), axis=1) <= r)) - 1
        return c
    a, b = count(m + 1), count(m)
    return float(-np.log(a / b)) if a > 0 and b > 0 else float("nan")

for sub in (1500, 3000):
    t0 = time.time()
    v = sample_entropy(mag[:sub])
    dt = time.time() - t0
    est = dt * (N / sub) ** 2
    print(f"    N={sub:5d}: 实测 {dt:6.2f} 秒  值={v:.4f}"
          f"  -> 外推全长 N={N}: {est/60:8.1f} 分钟/人 = {est*len(SUBJ)/3600:6.1f} 小时/{len(SUBJ)}人")

print()
print("  --- RQA 递归量化分析:内存占用 ---")
print(f"    递归矩阵尺寸 = N × N = {N:,} × {N:,} = {N**2:,} 个元素")
print(f"    即使每个元素只占 1 字节(布尔),单人也需 {N**2/1e9:.1f} GB")
print(f"    -> 全分辨率不可行;要算必须先降采样或分窗,而'降到多少/窗多长'又是一组")
print(f"       无依据的新参数(与 ISSUE-115 同类问题)。")

print("\n" + "=" * 80)
print("探针结束。本脚本未写任何文件。")
print("=" * 80)
