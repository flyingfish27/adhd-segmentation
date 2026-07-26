# -*- coding: utf-8 -*-
# TASK-115 决策探针:毛刺清理【前后】,路径B 那 45 列与症状分的关系差多少。
#
# ⚠️ 这只探针与 55/56 号不同:它【使用症状分】。用途是回答用户的问题——"清理不清理,
#    结论会不会不一样"。由此产生一条必须随结果一起声明的事实:
#    **做不做清理这个决定,是在看过它与症状分的关系之后做的**(用户 2026-07-26 明确要求把
#    这一点写进落盘记录)。看结果再定分析方案属结果依赖的决策,不声明就是隐瞒;声明了,
#    读者才能自行折价。参见 ISSUE-115 关于"先挑后测"的同类论述。
#
# 只跑普通秩相关,不跑置换检验——证"空"不需要置换,置换是用来保卫阳性发现的。
# 判读标尺(n=24 的硬事实,已记于 working/task.md 的 TASK-10 条目):
#   单次检验 p<0.05 需要 |ρ| ≥ 0.404;真实 ρ=0.4 时检出概率仅 49%。
#   纯噪声下,45 列 × 10 目标 = 450 次检验里期望有 0.05×450 ≈ 22.5 个 |ρ|≥0.404。
#
# 本脚本只读,不写任何产物。
# 复现命令: ADHD_ROOT=<有 data/ 的仓库根> .venv/bin/python analysis/57_cleaning_vs_targets.py
import importlib.util, pathlib, time
import numpy as np, pandas as pd
from scipy.ndimage import uniform_filter1d
from scipy.stats import spearmanr

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("f42", HERE / "42_features_full.py")
f42 = importlib.util.module_from_spec(spec); spec.loader.exec_module(f42)
SRC, DATA, ROOT = f42.SRC, f42.DATA, f42.ROOT

def banner(title, *lines):
    print("\n" + "#" * 84); print(f"# {title}")
    for l in lines: print(f"#   {l}")
    print("#" * 84)

# ---------- 清理手法(与 55/56 号探针同一套实现) ----------
def envelope(mag, fs, win_s):
    if win_s <= 0: return mag
    return np.sqrt(uniform_filter1d(mag ** 2, size=max(1, int(round(win_s * fs))), mode="nearest"))

def binarize(x, hi, lo):
    if lo >= hi: return x > hi
    s = np.full(len(x), -1, np.int8); s[x > hi] = 1; s[x < lo] = 0
    valid = s >= 0
    if not valid.any(): return np.zeros(len(x), bool)
    idx = np.where(valid, np.arange(len(x)), 0); np.maximum.accumulate(idx, out=idx)
    out = s[idx].astype(bool); out[: int(np.argmax(valid))] = False
    return out

def merge_short(active, min_len):
    if min_len <= 1: return active
    idx = np.flatnonzero(np.diff(active.astype(np.int8)) != 0) + 1
    st = np.concatenate([[0], idx]); en = np.concatenate([idx, [len(active)]])
    vals = active[st].copy(); lens = en - st
    for i in range(1, len(vals)):
        if lens[i] < min_len: vals[i] = vals[i - 1]
    out = np.empty_like(active)
    for i in range(len(vals)): out[st[i]:en[i]] = vals[i]
    return out

def tstruct(active, fs, pct):
    """与出厂 f_tstruct() 同口径的 5 个量(列名也照抄),供逐列对照。"""
    idx = np.flatnonzero(np.diff(active.astype(np.int8)) != 0) + 1
    st = np.concatenate([[0], idx]); en = np.concatenate([idx, [len(active)]])
    lens = (en - st) / fs; act = lens[active[st]]
    dur_min = len(active) / fs / 60.0
    o = {f"actfrac_p{pct}": float(active.mean()),
         f"switchmin_p{pct}": float(np.sum(np.abs(np.diff(active.astype(np.int8))) > 0) / dur_min)}
    if act.size:
        o[f"actbout_med_p{pct}"] = float(np.median(act))
        o[f"actbout_cv_p{pct}"] = float(act.std() / act.mean()) if act.mean() > 0 else 0.0
        o[f"actshort_p{pct}"] = float(np.mean(act < 1.0))
    else:
        o[f"actbout_med_p{pct}"] = 0.0; o[f"actbout_cv_p{pct}"] = 0.0; o[f"actshort_p{pct}"] = 0.0
    return o

# ================== 载入 ==================
aud = pd.read_csv(SRC / "figures/subject_audit.csv")
SUBJ = sorted(aud[(aud.status == "usable") & (aud["_T"].astype(str).str.lower() == "yes")]
              .subject.tolist())
tgt = pd.read_csv(ROOT / "analysis/targets.csv").set_index("subject").loc[SUBJ]
TARGETS = list(tgt.columns)
t0 = time.time(); MAG = {}; FSS = {}
for s in SUBJ:
    df, fs, t, _ = f42.load_T(DATA / f"{s}_T.csv")
    MAG[s] = np.linalg.norm(df[f42.USER_ACC].astype(float).to_numpy(), axis=1); FSS[s] = fs
UAMED = pd.Series({s: float(np.median(MAG[s])) for s in SUBJ})
print(f"载入 {len(SUBJ)} 人 × {len(MAG[SUBJ[0]]):,} 点,耗时 {time.time()-t0:.1f} 秒")
print(f"症状目标 {len(TARGETS)} 个: {TARGETS}")

PCTS = f42.PCTS
# 待比较的版本:第一行是出厂现状,其余是清理后的几组代表性参数
VERSIONS = [
    ("现状(不清理)",              dict(win=0,   ratio=1.0, mb=0.0)),
    ("只抹平 1 秒",               dict(win=1.0, ratio=1.0, mb=0.0)),
    ("抹0.5秒+迟滞0.8+并0.5秒",   dict(win=0.5, ratio=0.8, mb=0.5)),
    ("抹1秒+迟滞0.8+并0.5秒",     dict(win=1.0, ratio=0.8, mb=0.5)),
    ("抹2秒+迟滞0.8+并1秒",       dict(win=2.0, ratio=0.8, mb=1.0)),
]

def build(cfg):
    """按一组参数算出 24人 × 45列 的路径B特征表(与出厂列名一致)。"""
    env = {s: envelope(MAG[s], FSS[s], cfg["win"]) for s in SUBJ}
    rows = {}
    for pct in PCTS:
        hi = float(np.median([np.percentile(env[s], pct) for s in SUBJ]))
        lo = hi * cfg["ratio"]
        for s in SUBJ:
            a = binarize(env[s], hi, lo)
            ml = int(round(cfg["mb"] * FSS[s]))
            if ml > 1: a = merge_short(a, ml)
            rows.setdefault(s, {}).update(tstruct(a, FSS[s], pct))
    return pd.DataFrame([rows[s] for s in SUBJ], index=SUBJ)

THRESH = 0.404          # n=24 下单次检验 p<0.05 所需的 |ρ|
def corrmat(F):
    """45 列 × 10 目标的秩相关矩阵。常数列返回 nan。"""
    M = pd.DataFrame(index=F.columns, columns=TARGETS, dtype=float)
    for c in F.columns:
        v = F[c].to_numpy(float)
        if np.nanstd(v) == 0: continue
        for tname in TARGETS:
            M.loc[c, tname] = spearmanr(v, tgt[tname].to_numpy(float)).statistic
    return M

banner("路径B 45 列 × 10 个症状分:清理前后的秩相关对照",
       f"标尺:n=24 下单次检验 p<0.05 需 |ρ| ≥ {THRESH};450 次检验在纯噪声下期望约 22.5 个达标",
       "本表【未做多重比较校正】,也未跑置换检验——用途是看'清理会不会改变结论的有无',不是下结论")

TAB = {}
for name, cfg in VERSIONS:
    F = build(cfg); M = corrmat(F); TAB[name] = (F, M)
    a = M.to_numpy(float); fin = np.isfinite(a)
    nconst = int((~np.isfinite(a).any(axis=1)).sum())
    hits = int((np.abs(a[fin]) >= THRESH).sum())
    print(f"\n=== {name} ===")
    print(f"  常数列(无区分度,相关为 nan)  : {nconst} / {len(M)} 列")
    print(f"  |ρ| ≥ {THRESH} 的格子数        : {hits} / {int(fin.sum())}"
          f"   (纯噪声期望 {0.05*int(fin.sum()):.1f})")
    print(f"  全表最大 |ρ|                  : {np.nanmax(np.abs(a)):.3f}")
    idx = np.unravel_index(np.nanargmax(np.abs(np.where(fin, a, np.nan))), a.shape)
    print(f"    落在                        : {M.index[idx[0]]}  ×  {TARGETS[idx[1]]}"
          f"  (ρ={a[idx[0], idx[1]]:+.3f})")
    top = (M.abs().stack().sort_values(ascending=False).head(5))
    print("  前 5 强(列 × 目标 : ρ):")
    for (c, tn), v in top.items():
        print(f"    {c:22} × {tn:16} ρ={M.loc[c, tn]:+.3f}")

# ---------- 逐目标对照:每个症状分在各版本下的最大 |ρ| ----------
banner("逐目标对照 —— 每个症状分在各版本下能拿到的最大 |ρ|",
       f"任一格 ≥ {THRESH} 才算达到未校正的 p<0.05")
print(f"\n  {'目标':<18}" + "".join(f"{n:>26}" for n, _ in VERSIONS))
for tname in TARGETS:
    cells = ""
    for name, _ in VERSIONS:
        M = TAB[name][1]
        cells += f"{np.nanmax(np.abs(M[tname].to_numpy(float))):>26.3f}"
    print(f"  {tname:<18}{cells}")

# ---------- 负对照 ----------
banner("负对照 uaMag_median(运动总量)× 各症状分 —— 与清理无关,作参照",
       "若某个清理版本的最强观测还不如'这孩子动多用力'这一个数,说明结构特征没带来额外信息")
print()
for tname in TARGETS:
    r = spearmanr(UAMED.to_numpy(float), tgt[tname].to_numpy(float)).statistic
    print(f"  uaMag_median × {tname:16} ρ={r:+.3f}{'   <- |ρ|≥0.404' if abs(r) >= THRESH else ''}")

# ---------- 清理是否改变了列的排序 ----------
banner("清理是否改变了'哪些列最像有信号'的排序",
       "对每个症状分,把 45 列按 |ρ| 排序,再看清理前后这个排序的秩相关。",
       "接近 1 = 清理没改变哪些列突出;接近 0 = 换了一批列突出。")
base = TAB["现状(不清理)"][1]
print(f"\n  {'目标':<18}" + "".join(f"{n:>26}" for n, _ in VERSIONS[1:]))
for tname in TARGETS:
    b = base[tname].to_numpy(float)
    cells = ""
    for name, _ in VERSIONS[1:]:
        v = TAB[name][1][tname].to_numpy(float)
        ok = np.isfinite(b) & np.isfinite(v)
        rr = spearmanr(np.abs(b[ok]), np.abs(v[ok])).statistic if ok.sum() > 5 else np.nan
        cells += f"{rr:>26.3f}"
    print(f"  {tname:<18}{cells}")

# ---------- 校正后还剩什么 ----------
def bh(p):
    """Benjamini-Hochberg,与 44_univariate_screen.py 的 bh() 同一算法。"""
    p = np.asarray(p, float); m = len(p); o = np.argsort(p)
    q = np.empty(m); prev = 1.0
    for rank, i in enumerate(o[::-1]):
        k = m - rank
        prev = min(prev, p[i] * m / k); q[i] = prev
    return q

banner("多重比较校正之后还剩什么 —— 这才是'有没有发现'的判据",
       "家族口径 = 每个版本【自己那 450 次检验(45 列 × 10 目标)】为一族做 BH-FDR。",
       "注意这是【偏宽松】的口径:真实家族还要包含其余 500 多列特征,故真实 q 只会更大、不会更小。")
print(f"\n  {'版本':<26}{'最大|ρ|':>10}{'该格未校正 p':>16}{'BH 校正后最小 q':>18}{'q<0.05 的格子数':>18}")
for name, _ in VERSIONS:
    M = TAB[name][1]; F = TAB[name][0]
    ps, rs = [], []
    for c in M.index:
        v = F[c].to_numpy(float)
        if np.nanstd(v) == 0: continue
        for tname in TARGETS:
            r = spearmanr(v, tgt[tname].to_numpy(float))
            ps.append(r.pvalue); rs.append(abs(r.statistic))
    ps = np.array(ps); rs = np.array(rs); q = bh(ps)
    i = int(np.nanargmax(rs))
    print(f"  {name:<26}{rs[i]:>10.3f}{ps[i]:>16.4f}{np.nanmin(q):>18.3f}{int((q<0.05).sum()):>18d}")

banner("那 45 列彼此有多冗余 —— '纯噪声期望 22.5 个'这个标尺失效多少",
       "上文用的 0.05×450≈22.5 假设 450 次检验相互独立。实际 45 列是 5 个指标族 × 9 档嵌套百分位,",
       "高度相关。这里用主成分数量估'有效独立列数':列相关矩阵的特征值中,累计解释 95% 方差所需的个数。")
print(f"\n  {'版本':<26}{'名义列数':>10}{'有效独立列数(95%方差)':>24}{'有效检验数':>14}{'噪声期望达标数':>16}")
for name, _ in VERSIONS:
    F = TAB[name][0]
    X = F.to_numpy(float)
    keep = np.nanstd(X, axis=0) > 0
    X = X[:, keep]
    X = (X - X.mean(0)) / X.std(0)
    ev = np.linalg.eigvalsh(np.corrcoef(X, rowvar=False))[::-1]
    ev = ev[ev > 0]; k = int(np.searchsorted(np.cumsum(ev) / ev.sum(), 0.95) + 1)
    print(f"  {name:<26}{int(keep.sum()):>10d}{k:>24d}{k*len(TARGETS):>14d}"
          f"{0.05*k*len(TARGETS):>16.1f}")

print("\n" + "=" * 84)
print("⚠️ 声明:本探针使用了症状分。若据此决定做不做毛刺清理,该决定即为【看过结果之后做的】,")
print("   须随结论一起声明(用户 2026-07-26 要求)。本脚本只读,不写任何产物。")
