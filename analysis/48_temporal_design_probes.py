# -*- coding: utf-8 -*-
# =============================================================================
# 48_temporal_design_probes.py  —  TASK-1「时间结构特征族重写」的两只设计探针
# =============================================================================
# 这是什么(给未来任何一个不了解本项目的人):
#   这个文件【不是】生产管线的一部分,不产生任何特征、不写任何文件、不进 features.csv。
#   它是两只【探针(probe)】——在真实数据上把几个数字摊开,专门用来给 TASK-1 的
#   两个设计【决策】提供事实依据,好让人(不是这个脚本)去拍板。跑完只在终端打印。
#
#   "探针"在本项目里是一类脚本的固定叫法(见 analysis/32_、33_ 等),含义=探索性、
#   只读、只打印、结论供人决策,不参与生产链路。本文件属同类。
#
# 只读:仅读 data/ 下的原始腕表文件 + figures/subject_audit.csv(24 人名单)。
#   不写盘。符合本项目 data/ 只读约定(有 PreToolUse 钩子强制)。
#
# 两只探针分别回答什么:
#
#   探针 1 —— 自相关衰减时间尺度
#     问题:每个孩子"此刻的动作强度"能预测"多少秒之后的动作强度"?
#     算法:对未截断的去重力动作强度 uaMag 求自相关函数(ACF),报告它衰减到
#           1/e、0.5、0.2 各需多少秒,以及"首个过零前的积分时间尺度"。
#     用途:给 TASK-1 里"滑窗平滑窗长 win_s / 活动包络窗长 env_s 该取几秒"一个
#           【从本数据推出来的锚点】,替代此前拍脑袋的数(见 working/issue.md 的
#           ISSUE-115:那几个参数值"没依据")。
#     已知局限:本数据是自由生活(free-living)、非平稳,自相关未必有干净的单一
#           衰减尺度,跨人离散可能很大——这一点在探索阶段看一眼本身有意义,
#           但读数时要知道它不一定给出一个"唯一正确"的窗长。
#
#   探针 2 —— 合池阈值 vs 各人自己阈值:结构特征的"总量泄漏"代价
#     问题:如果把活动阈值改成"全体 24 人合池一条线"(ISSUE-101 讨论里的 c2
#           每人一票),那些描述"运动【怎么组织】"的结构特征,会不会因此变得跟
#           "运动【总量】"高度相关?——若相关很高,等于把"这个孩子整体动多用力/
#           幅度多大"这个变量偷偷泄漏进了本该只看节奏结构的特征里。
#     算法:对 p=50/75/90 三档,分别用【各人自己的百分位】和【合池线(24 人各自
#           该百分位的中位数)】两种阈值,各算一套结构特征,再算每个结构特征与
#           负对照 uaMag_median(=运动总量)的秩相关 |ρ|,两种口径并排对比。
#     用途:量化"改用合池阈值的代价",给 TASK-1 决策5(路径 A 的阈值口径)供数。
#           判据(用户原话):相关越高,越不该合池——那是某种程度的标签/变量泄漏。
#
# 参数说明(重要):本文件用的 win_s=10, step_s=5, short_s=10 是【路径 A 现用的
#   那组参数】,拿来当探测口径,不代表这组参数已被论证/认可(恰恰 ISSUE-115 指出
#   它们没依据)。探针 1 的产出正是用来重新审视这个 10。
#
# 为什么在【未截断】信号上跑:这两个问题问的是信号本身的时间结构与幅度组织,
#   与 TASK-102 的"截到 41 分钟"无关,故一律 load_T(..., n_max=None) 读全长。
#
# 怎么跑:  <项目根>/.venv/bin/python analysis/48_temporal_design_probes.py
#   依赖 numpy / pandas / scipy(见 requirements 环境)。首跑约 25 秒(读 24 人)。
#
# 溯源:2026-07-23 首次运行的原始输出,记录在 TASK-1 的会话决策过程中;本脚本是
#   那批数字的【可复现来源】。关联 working/task.md 的 TASK-1、working/issue.md 的
#   ISSUE-101 / ISSUE-102 / ISSUE-115。
# =============================================================================
import importlib.util, os, pathlib
import numpy as np, pandas as pd
from scipy.stats import spearmanr

# --- 项目根:默认按本文件位置解析(analysis/ 的上一级),不写死绝对路径 ---
#   正常检出里 analysis/ 与 data/ 同级,这就对了,陌生人 clone 下来直接能跑。
#   例外:在 git worktree 里跑时,worktree 不检出 data/(只在主检出里),这时用
#   环境变量 ADHD_ROOT 指到数据实际所在的仓库根即可。例:
#     ADHD_ROOT=/path/to/main-checkout  python analysis/48_temporal_design_probes.py
HERE = pathlib.Path(__file__).resolve().parent          # .../analysis
ROOT = pathlib.Path(os.environ.get("ADHD_ROOT", HERE.parent)).resolve()
DATA = ROOT / "data"
if not DATA.is_dir():                                    # 早失败,给出可操作的提示
    raise SystemExit(f"找不到 data/(在 {DATA})。若在 worktree 里跑,请设 "
                     f"ADHD_ROOT 指向有 data/ 的主检出。")

# --- import 生产脚本 42,复用它的 load_T / USER_ACC(它主流程在 __main__ 保护下,
#     import 不触发全量跑)。同样按相对路径,保证测的是【本仓库这一份】。---
_spec = importlib.util.spec_from_file_location("features_full", HERE / "42_features_full.py")
FF = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(FF)
UA = FF.USER_ACC

WIN_S, STEP_S, SHORT_S = 10, 5, 10      # 路径 A 现用参数(见上方"参数说明")

aud = pd.read_csv(ROOT / "figures/subject_audit.csv")
SUBJ = sorted(aud[(aud.status == "usable") & (aud["_T"].astype(str).str.lower() == "yes")].subject)
assert len(SUBJ) == 24, f"期望 24 人,实得 {len(SUBJ)}"


# ---------- 探针 1 的核心:自相关衰减尺度 ----------
def acf_timescales(x, fs, max_lag_s=120):
    """返回 (衰到 1/e 的秒数, 衰到 0.5 的秒数, 衰到 0.2 的秒数, 积分时间尺度秒)。"""
    x = np.asarray(x, float); x = x - x.mean(); n = len(x)
    m = 1 << int(np.ceil(np.log2(2 * n)))               # FFT 补零到 2 的幂,算线性自相关
    F = np.fft.rfft(x, m)
    ac = np.fft.irfft(F * np.conj(F), m)[:n]; ac = ac / ac[0]     # 归一化到 ac[0]=1
    maxlag = min(n - 1, int(max_lag_s * fs))
    ac = ac[:maxlag + 1]; lags = np.arange(len(ac)) / fs
    def cross(level):                                   # 首次跌破 level 的滞后秒数
        idx = np.where(ac < level)[0]
        return lags[idx[0]] if len(idx) else np.nan
    zc = np.where(ac < 0)[0]; end = zc[0] if len(zc) else len(ac)
    integ = ac[:end].sum() / fs                         # 首个过零前的积分(记忆总量)
    return cross(1 / np.e), cross(0.5), cross(0.2), integ


# ---------- 探针 2 的核心:给定一条阈值,算一套结构特征 ----------
def struct(w, thr, dur_min):
    """w=窗均值序列, thr=阈值, dur_min=记录时长(分)。返回一套时间结构特征。"""
    active = w > thr
    edges = np.concatenate([[0], np.where(np.diff(active.astype(int)) != 0)[0] + 1, [len(active)]])
    durs = np.diff(edges) * STEP_S; states = active[edges[:-1]]
    act, stl = durs[states], durs[~states]
    def cv(x): return float(x.std() / x.mean()) if len(x) > 1 and x.mean() > 0 else np.nan
    return {"actfrac": float(active.mean()),
            "switch_per_min": (len(durs) - 1) / dur_min,
            "act_bout_median": float(np.median(act)) if len(act) else np.nan,
            "stl_bout_median": float(np.median(stl)) if len(stl) else np.nan,
            "act_bout_cv": cv(act), "stl_bout_cv": cv(stl),
            "frac_act_short": float((act <= SHORT_S).mean()) if len(act) else np.nan}


# ================= 读一次数据,两只探针共用 =================
W = {}; DURMIN = {}; UAMED = {}; TS = []
for s in SUBJ:
    df, fs, t, _ = FF.load_T(DATA / f"{s}_T.csv", n_max=None)     # 未截断
    mag = np.linalg.norm(df[UA].astype(float).to_numpy(), axis=1)
    e163, e50, e20, ig = acf_timescales(mag, fs)
    TS.append({"subject": s, "fs": fs, "tau_1/e_s": e163, "tau_0.5_s": e50,
               "tau_0.2_s": e20, "integ_s": ig})
    win, step = int(WIN_S * fs), int(STEP_S * fs)
    W[s] = np.array([mag[i:i + win].mean() for i in range(0, len(mag) - win, step)])
    DURMIN[s] = t[-1] / 60.0; UAMED[s] = float(np.median(mag))


# ================= 探针 1 输出 =================
print("#" * 80)
print("# 探针1  自相关衰减时间尺度(未截断 uaMag,每人一行,单位秒)")
print("#   tau_X = 自相关从 1 降到 X 所需的滞后秒数;integ = 首个过零前的积分时间尺度")
print("#" * 80)
T = pd.DataFrame(TS).set_index("subject")
print(T.round(3).to_string())
print("\n--- 24 人分布(秒) ---")
for c in ["tau_1/e_s", "tau_0.5_s", "tau_0.2_s", "integ_s"]:
    v = T[c].to_numpy(float); v = v[np.isfinite(v)]
    print(f"  {c:12} 最小{v.min():7.3f}  25%{np.percentile(v,25):7.3f}  "
          f"中位{np.median(v):7.3f}  75%{np.percentile(v,75):7.3f}  最大{v.max():7.3f}")
print(f"\n  参照:路径 A 现用平滑窗长 = {WIN_S} 秒。上面这些尺度给它一个数据锚点。")


# ================= 探针 2 输出 =================
print("\n" + "#" * 80)
print("# 探针2  合池 vs 各人自己 —— 结构特征 与 运动总量(uaMag_median)的秩相关")
print("#   |ρ| 越高 = 该结构特征越受'这孩子整体动多用力'影响 = 合池后越像总量泄漏")
print("#" * 80)
FEATS = ["actfrac", "switch_per_min", "act_bout_median", "stl_bout_median",
         "act_bout_cv", "stl_bout_cv", "frac_act_short"]
uamed = np.array([UAMED[s] for s in SUBJ])
for p in (50, 75, 90):
    pooled = float(np.median([np.percentile(W[s], p) for s in SUBJ]))
    own_vals = {f: [] for f in FEATS}; pool_vals = {f: [] for f in FEATS}
    for s in SUBJ:
        so = struct(W[s], np.percentile(W[s], p), DURMIN[s])     # 各人自己阈值
        spool = struct(W[s], pooled, DURMIN[s])                  # 合池阈值
        for f in FEATS:
            own_vals[f].append(so[f]); pool_vals[f].append(spool[f])
    print(f"\n===== 阈值百分位 p={p}  |  合池线={pooled:.4f} G =====")
    print(f"{'特征':16} {'各人阈值:|ρ|与总量':>18} {'合池阈值:|ρ|与总量':>18}   在24人间是否退化")
    for f in FEATS:
        ov = np.array(own_vals[f], float); pv = np.array(pool_vals[f], float)
        def rho(x):
            m = np.isfinite(x) & np.isfinite(uamed)
            return spearmanr(x[m], uamed[m]).correlation if m.sum() > 2 and np.std(x[m]) > 0 else np.nan
        ro, rp = rho(ov), rho(pv)
        deg = "各人阈值下:常数" if np.nanstd(ov) == 0 else f"各人阈值下:{len(np.unique(np.round(ov,6)))}个值"
        print(f"{f:16} {abs(ro):>18.3f} {abs(rp):>18.3f}   {deg}")
    print(f"  (提示:actfrac 在'各人阈值'下恒={1-p/100:.2f},其'|ρ|与总量'无意义;看它'合池阈值'列)")
