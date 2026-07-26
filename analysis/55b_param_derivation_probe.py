# -*- coding: utf-8 -*-
# TASK-115 参数推导探针:三个清理参数能否【从数据本身推出来】,而不是拍脑袋定。
#
# 背景:ISSUE-102 裁决采纳三样清理手法(①RMS 抹平 ②迟滞双阈值 ③最短段合并),但三样各自的
#   参数值没有出处。ISSUE-102 条目给的三条出路是:扫描并报整条曲线 / 另找文献依据 /
#   明确标注为无依据的探索性取值。本探针试第四条:能不能从数据本身推出一个值。
#
# 判据 = 分半信度(split-half reliability),【全程不看症状分】,故不构成"先挑后测"。
#   做法:把每个孩子的记录切成前后两半,各算一遍特征,再看跨 24 人这两套值的秩相关。
#     · 相关高 = 该特征量到的是这孩子稳定的属性(前后两半是同一个人);
#     · 相关低 = 量到的是噪声(同一个人前后两半都对不上,更不用说人和人比)。
#   为什么这个判据【有内部最优点】而不是越抹越好:
#     · 抹得太少 -> 量的是阈值附近的毛刺 -> 前后两半对不上 -> 信度低;
#     · 抹得太多 -> 所有孩子被抹成一样 -> 孩子间差异消失 -> 信度可能仍高但【区分度】没了。
#   故本探针同时报第二个量:【跨被试离散度】(24 人该特征的四分位距 / 中位数),
#     用来看抹平是否把人和人的差异一起抹掉了。两个量要一起读。
#
# 三个参数各自的推导路径:
#   ① 抹平时长  -> 探针A:分半信度 + 跨被试离散度 随抹平时长的变化曲线,找内部最优。
#   ② 两线间距  -> 探针B:同一套判据,在几个抹平时长下扫间距。
#   ③ 最短段    -> 探针C:抹平 W 秒后,信号本身不可能有短于 W 的变化,故任何 ≤W 的合并
#                   都是空操作。本探针把"抹平后短于 W 的段占比"直接测出来验证这一点。
#
# 本脚本【只读、不写任何产物】。
# 复现命令: ADHD_ROOT=<有 data/ 的仓库根> .venv/bin/python analysis/55b_param_derivation_probe.py
import importlib.util, pathlib, time
import numpy as np, pandas as pd
from scipy.ndimage import uniform_filter1d
from scipy.stats import spearmanr

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("f42", HERE / "42_features_full.py")
f42 = importlib.util.module_from_spec(spec); spec.loader.exec_module(f42)
SRC, DATA = f42.SRC, f42.DATA

def banner(title, *lines):
    print("\n" + "#" * 84); print(f"# {title}")
    for l in lines: print(f"#   {l}")
    print("#" * 84)

# ---------- 与 55a 号探针同一套清理实现(保持口径一致) ----------
def envelope(mag, fs, win_s):
    if win_s <= 0: return mag
    n = max(1, int(round(win_s * fs)))
    return np.sqrt(uniform_filter1d(mag ** 2, size=n, mode="nearest"))

def binarize(x, thr_hi, thr_lo):
    if thr_lo >= thr_hi: return x > thr_hi
    s = np.full(len(x), -1, np.int8); s[x > thr_hi] = 1; s[x < thr_lo] = 0
    valid = s >= 0
    if not valid.any(): return np.zeros(len(x), bool)
    idx = np.where(valid, np.arange(len(x)), 0); np.maximum.accumulate(idx, out=idx)
    out = s[idx].astype(bool); out[: int(np.argmax(valid))] = False
    return out

def feats(active, fs):
    idx = np.flatnonzero(np.diff(active.astype(np.int8)) != 0) + 1
    st = np.concatenate([[0], idx]); en = np.concatenate([idx, [len(active)]])
    lens = (en - st) / fs; act = lens[active[st]]
    dur_min = len(active) / fs / 60.0
    def cv(x): return float(x.std() / x.mean()) if len(x) > 1 and x.mean() > 0 else np.nan
    return {"actfrac": float(active.mean()),
            "switch_per_min": float(np.sum(np.abs(np.diff(active.astype(np.int8))) > 0) / dur_min),
            "act_bout_median": float(np.median(act)) if act.size else np.nan,
            "act_bout_cv": cv(act),
            "actshort_lt1s": float(np.mean(act < 1.0)) if act.size else np.nan}

FEATNAMES = ["actfrac", "switch_per_min", "act_bout_median", "act_bout_cv", "actshort_lt1s"]

def splithalf(vals1, vals2):
    """跨被试的分半秩相关。任一半退化成常数则返回 nan(该特征此设定下无区分度)。"""
    a = np.array(vals1, float); b = np.array(vals2, float)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 5 or np.nanstd(a[ok]) == 0 or np.nanstd(b[ok]) == 0: return np.nan
    return float(spearmanr(a[ok], b[ok]).statistic)

def dispersion(vals):
    """跨被试离散度 = 四分位距 / |中位数|。抹平若把人和人的差异抹平,这个数会塌下去。"""
    v = np.array(vals, float); v = v[np.isfinite(v)]
    if v.size < 5: return np.nan
    med = np.median(v)
    return float((np.percentile(v, 75) - np.percentile(v, 25)) / abs(med)) if med != 0 else np.nan

# ================== 载入 ==================
aud = pd.read_csv(SRC / "figures/subject_audit.csv")
SUBJ = sorted(aud[(aud.status == "usable") & (aud["_T"].astype(str).str.lower() == "yes")]
              .subject.tolist())
assert len(SUBJ) == 24
t0 = time.time(); MAG = {}; FSS = {}
for s in SUBJ:
    df, fs, t, _ = f42.load_T(DATA / f"{s}_T.csv")
    MAG[s] = np.linalg.norm(df[f42.USER_ACC].astype(float).to_numpy(), axis=1); FSS[s] = fs
fs = float(np.median(list(FSS.values())))
N = len(MAG[SUBJ[0]]); HALF = N // 2
print(f"载入 {len(SUBJ)} 人 × {N:,} 点(N_TRUNC={f42.N_TRUNC}),fs≈{fs:.3f} Hz,耗时 {time.time()-t0:.1f} 秒")
print(f"分半:前半 {HALF:,} 点({HALF/fs/60:.2f} 分钟) / 后半 {N-HALF:,} 点({(N-HALF)/fs/60:.2f} 分钟)")

def run(win_s, pct, ratio=1.0):
    """返回 (全段特征表, 前半特征表, 后半特征表);阈值一律用【全段】算的合池线,
       两半共用同一条线——否则前后两半的'阈值'不同,分半信度就掺进了阈值的差异。"""
    env = {s: envelope(MAG[s], FSS[s], win_s) for s in SUBJ}
    hi = float(np.median([np.percentile(env[s], pct) for s in SUBJ]))
    lo = hi * ratio
    full, h1, h2 = {}, {}, {}
    for s in SUBJ:
        e = env[s]
        full[s] = feats(binarize(e, hi, lo), FSS[s])
        h1[s] = feats(binarize(e[:HALF], hi, lo), FSS[s])
        h2[s] = feats(binarize(e[HALF:], hi, lo), FSS[s])
    return full, h1, h2, hi

def report(full, h1, h2, tag):
    r = {}
    for f in FEATNAMES:
        r[f] = (splithalf([h1[s][f] for s in SUBJ], [h2[s][f] for s in SUBJ]),
                dispersion([full[s][f] for s in SUBJ]))
    return tag, r

def show(rows, head):
    print(f"\n{head}")
    print(f"  {'设定':<22}" + "".join(f"{f:>19}" for f in FEATNAMES))
    print(f"  {'':<22}" + "".join(f"{'信度 / 离散度':>19}" for _ in FEATNAMES))
    for tag, r in rows:
        cells = ""
        for f in FEATNAMES:
            sh, dp = r[f]
            cells += f"{('nan' if not np.isfinite(sh) else f'{sh:+.3f}'):>10}" \
                     f"{('  nan' if not np.isfinite(dp) else f' /{dp:5.2f}'):>9}"
        print(f"  {tag:<22}{cells}")

# ================== 探针A:抹平时长 ==================
banner("探针A  参数① 抹平时长能否推导 —— 分半信度 + 跨被试离散度",
       "每格两个数:左=分半秩相关(该特征量到的是不是这孩子稳定的属性,越高越是);",
       "            右=跨 24 人的四分位距/中位数(孩子之间还剩多少差异,塌到 0 = 抹平了)",
       "若信度曲线有【内部最高点】,该点就是从数据推出来的抹平时长;",
       "若单调上升,则推不出来——那说明'越抹越稳'只是把大家抹得一样(看右边那个数是否同步塌陷)")
WINS = [0, 0.25, 0.5, 1, 2, 3, 5, 8]
for pct in (50, 90):
    rows = []
    for w in WINS:
        full, h1, h2, hi = run(w, pct)
        rows.append(report(full, h1, h2, f"抹平={w}秒 (线{hi:.3f}G)"))
    show(rows, f"=== 阈值档 p{pct}(单阈值、不合并) ===")

# ================== 探针B:两线间距 ==================
banner("探针B  参数② 两条线的间距能否推导 —— 同一套判据",
       "在三个抹平时长下各扫四种间距(下线 = 上线 × r);r=1.0 即不加迟滞")
for pct in (50, 90):
    for w in (0.5, 1.0, 2.0):
        rows = []
        for r in (1.0, 0.9, 0.8, 0.7):
            full, h1, h2, hi = run(w, pct, ratio=r)
            tag = "无迟滞" if r == 1.0 else f"下线=上线×{r}"
            rows.append(report(full, h1, h2, f"{tag}"))
        show(rows, f"=== 阈值档 p{pct},抹平={w} 秒 ===")

# ================== 探针C:最短段是不是独立参数 ==================
banner("探针C  参数③ 最短段合并是不是独立参数",
       "命题:抹平 W 秒之后,包络本身不可能有短于 W 的变化,故任何 ≤W 的合并长度都是空操作。",
       "验证:直接测'抹平 W 秒后,活动段中短于 W 的占比'。若接近 0,则命题成立,",
       "      最短段不是独立参数——它由抹平时长定死,不需要另外拍一个数。")
print(f"\n  {'抹平W':<10}{'阈值档':<8}{'活动段总数(24人中位)':>22}{'短于W的占比':>16}{'短于W/2的占比':>16}")
for w in (0.5, 1.0, 2.0, 5.0):
    for pct in (50, 90):
        env = {s: envelope(MAG[s], FSS[s], w) for s in SUBJ}
        hi = float(np.median([np.percentile(env[s], pct) for s in SUBJ]))
        nb, frac_w, frac_h = [], [], []
        for s in SUBJ:
            a = binarize(env[s], hi, hi)
            idx = np.flatnonzero(np.diff(a.astype(np.int8)) != 0) + 1
            st = np.concatenate([[0], idx]); en = np.concatenate([idx, [len(a)]])
            act = ((en - st) / FSS[s])[a[st]]
            if act.size:
                nb.append(act.size); frac_w.append(float(np.mean(act < w)))
                frac_h.append(float(np.mean(act < w / 2)))
        print(f"  {w:<10}{'p'+str(pct):<8}{np.median(nb):>22.0f}"
              f"{np.median(frac_w)*100:>15.1f}%{np.median(frac_h)*100:>15.1f}%")

print("\n" + "=" * 84)
print("说明:本探针只读、不写任何产物,且【全程未使用症状分】,故用它选参数不构成先挑后测。")
