# -*- coding: utf-8 -*-
# =============================================================================
# 51_jerk_channel_audit.py  —  jerk 通道 21 列的逐列体检(TASK-1 决策7)
# =============================================================================
# 这是什么:一只【探针】(探索性、只读 data/、只打印、供人决策,不进生产链路)。
#   背景:features.csv 里 jerk 通道有 21 列(jerk = |a| 的时间导数 = diff(uaMag)*fs,
#   "动作变化多突然")。已知 jerk_median 一列 24 人恒为 0。用户要求把【整个通道
#   21 列】一起复核,看哪些列是"按构造退化/被单尖峰主导/被求导操作本身决定",
#   哪些看起来还携带被试信息。本脚本只给客观判据,去留由人定。
#
# 四项检查(每项对应一类可能的问题):
#   A 退化:每列在 24 人间有几个不同值 / 标准差。→ 抓恒常数或近常数列。
#   B 单尖峰主导:jerk 有 ±300~500 G/s 的极端尖峰(可能是磕碰/削顶,见 ISSUE-104/110)。
#     对每人算 max|jerk| / p99.9 之比、以及"最大那一个采样点占了平方和的多少"。
#     → 抓 min/max/range/std/var/rms 这类被单点主导、量的是"表被撞过一次"的列。
#   C 求导噪声:jerk=diff() 会放大相邻采样点的噪声。把信号先轻度平滑(5 点)再求导,
#     看 std 掉多少。掉得越多 = 原 jerk_std 越多来自采样噪声而非真实动作。
#   D 求导操作的指纹:数学上求导把频谱能量系统性推向高频(乘以 ~频率)。比较同一人
#     mag 与 jerk 的频谱质心;若 jerk 质心一律远高于 mag、且 entropy 在 24 人间挤成
#     一条窄带,说明 domfreq/centroid/spread/entropy 这些频域列主要反映"求导"这个
#     操作、而不是这个孩子。
#
# 口径:用 features.csv 的默认口径(N_TRUNC 截断信号),以匹配现表里那 21 列的实际值。
#   (jerk_median=0 在截断前后都成立,见 TASK-102 记录。)
# 只读、不写盘。可移植:路径按 __file__ 相对解析;worktree 里跑用 ADHD_ROOT 覆盖。
#   跑法: <根>/.venv/bin/python analysis/51_jerk_channel_audit.py
# 关联:working/task.md TASK-1 的 jerk_median 项;working/issue.md ISSUE-104/110。
# =============================================================================
import importlib.util, os, pathlib
import numpy as np, pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path(os.environ.get("ADHD_ROOT", HERE.parent)).resolve()
DATA = ROOT / "data"
if not DATA.is_dir():
    raise SystemExit(f"找不到 data/(在 {DATA})。worktree 里跑请设 ADHD_ROOT 指向主检出。")

_spec = importlib.util.spec_from_file_location("features_full", HERE / "42_features_full.py")
FF = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(FF)
UA = FF.USER_ACC

aud = pd.read_csv(ROOT / "figures/subject_audit.csv")
SUBJ = sorted(aud[(aud.status == "usable") & (aud["_T"].astype(str).str.lower() == "yes")].subject)

TIME_KEYS = list(FF.f_time(np.arange(100.0)).keys())        # 14 个时域键名(顺序与 42 一致)

rows = []          # 每人一行的 21 列 jerk 特征(复算,匹配 42 的口径)
raw = {}           # 每人的原始 jerk 序列,供 B/C/D 深检
for s in SUBJ:
    df, fs, t, _ = FF.load_T(DATA / f"{s}_T.csv")           # 默认口径=截断(匹配 features.csv)
    uaMag = np.linalg.norm(df[UA].astype(float).to_numpy(), axis=1)
    jerk = np.diff(uaMag) * fs
    raw[s] = (uaMag, jerk, fs)
    feat = {"subject": s}
    for k, v in FF.f_time(jerk).items():  feat[f"jerk_{k}"] = v
    for k, v in FF.f_freq(jerk, fs).items(): feat[f"jerk_{k}"] = v
    rows.append(feat)
J = pd.DataFrame(rows).set_index("subject")
JCOLS = [c for c in J.columns]

# ---------- A 退化 ----------
print("#"*82); print("# A 退化检查:每列在 24 人间的不同取值数 / 标准差 / 值域"); print("#"*82)
print(f"{'列名':16}{'不同值':>7}{'标准差':>13}{'最小':>13}{'最大':>13}   判读")
for c in JCOLS:
    v = J[c].to_numpy(float); nu = len(np.unique(np.round(v, 9)))
    tag = "★恒常数(0信息)" if nu == 1 else ("近常数?" if J[c].std()/(abs(J[c].mean())+1e-12) < 0.02 else "")
    print(f"{c:16}{nu:>7d}{v.std():>13.4g}{v.min():>13.4g}{v.max():>13.4g}   {tag}")

# ---------- B 单尖峰主导 ----------
print("\n"+"#"*82); print("# B 单尖峰主导:max|jerk|/p99.9 之比,和'最大单点占平方和的比例'(24人分布)")
print("#   比值/占比越大 = 该量越被单次极端尖峰(疑磕碰/削顶)主导,而非动作模式"); print("#"*82)
ratios, ss_top1 = [], []
for s in SUBJ:
    _, jk, _ = raw[s]; a = np.abs(jk)
    ratios.append(a.max()/np.percentile(a, 99.9))
    ss = jk**2; ss_top1.append(ss.max()/ss.sum())
ratios = np.array(ratios); ss_top1 = np.array(ss_top1)
print(f"  max|jerk|/p99.9 :  最小{ratios.min():6.2f}  中位{np.median(ratios):6.2f}  最大{ratios.max():6.2f}")
print(f"  最大单点占平方和:  最小{ss_top1.min():8.4%}  中位{np.median(ss_top1):8.4%}  最大{ss_top1.max():8.4%}")
print("  → 受此影响的列:jerk_min / jerk_max / jerk_range / jerk_var / jerk_rms / jerk_std / jerk_kurt")

# ---------- C 求导噪声 ----------
print("\n"+"#"*82); print("# C 求导噪声:先把 uaMag 做 5 点滑动平均再求导,std 掉多少(24人分布)")
print("#   掉得越多 = 原 jerk_std/var/rms 越多来自相邻采样点噪声而非真实动作"); print("#"*82)
drop = []
for s in SUBJ:
    um, jk, fs = raw[s]
    k = 5; kern = np.ones(k)/k
    um_s = np.convolve(um, kern, mode="same")
    jk_s = np.diff(um_s)*fs
    drop.append(1 - jk_s.std()/jk.std())
drop = np.array(drop)
print(f"  std 相对下降:  最小{drop.min():7.2%}  中位{np.median(drop):7.2%}  最大{drop.max():7.2%}")
print("  → 受此影响的列:jerk_std / jerk_var / jerk_rms / jerk_mad / jerk_madiff")

# ---------- D 求导操作的频谱指纹 ----------
print("\n"+"#"*82); print("# D 求导指纹:同一人 mag 频谱质心 vs jerk 频谱质心;jerk_entropy 的跨人窄度")
print("#   jerk 质心一律远高于 mag + entropy 挤成窄带 = 频域列主要反映'求导'而非被试"); print("#"*82)
mc, jc = [], []
for s in SUBJ:
    um, jk, fs = raw[s]
    mc.append(FF.f_freq(um, fs)["centroid"]); jc.append(FF.f_freq(jk, fs)["centroid"])
mc, jc = np.array(mc), np.array(jc)
print(f"  mag 频谱质心(Hz) : 中位 {np.median(mc):5.2f}  [{mc.min():.2f}, {mc.max():.2f}]")
print(f"  jerk频谱质心(Hz) : 中位 {np.median(jc):5.2f}  [{jc.min():.2f}, {jc.max():.2f}]")
print(f"  每人 jerk质心 > mag质心 的人数: {(jc>mc).sum()}/24")
ent = J["jerk_entropy"].to_numpy(float)
print(f"  jerk_entropy 跨24人: [{ent.min():.4f}, {ent.max():.4f}]  极差 {ent.max()-ent.min():.4f}(越小越像操作指纹)")
print("  → 受此影响的列:jerk_domfreq / jerk_centroid / jerk_spread / jerk_entropy / jerk_bp_lf/mf/hf")

print("\n"+"="*82)
print("说明:以上是客观判据,不含去留判断。哪几列删/换/留,由人按这些数字决定。")
print("="*82)
