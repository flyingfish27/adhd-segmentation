# -*- coding: utf-8 -*-
# TASK-115 / ISSUE-102 设计探针:为"路径B毛刺清理"的三个参数找数据依据。
#
# 背景(给不懂本项目的人):特征脚本 analysis/42_features_full.py 的"路径B"在约 30Hz 的
#   原始手腕去重力动作强度信号(uaMag,单位 G)上【逐个采样点】判断"高于阈值=在动、
#   低于=静止",据此统计活动段时长、每分钟切换次数等 45 列特征。原始信号在阈值上下反复
#   抖动,切出成千上万个只有 3-5 个采样点(约 0.1 秒)的碎片段,这些数字量的是噪声不是行为
#   (ISSUE-102)。修法(actigraphy 标准三样,ISSUE-102 已裁决采纳):
#     ① 先把信号平滑成"活动包络"(滑动均方根 RMS);
#     ② 卡阈值时加"迟滞"(进入活动与退出活动用两个不同阈值);
#     ③ "最短段合并"(把过短的碎段并进相邻状态)。
#   三样各自的参数值(RMS 窗几秒 / 迟滞两阈值 / 最短段多长)【没有出处】,属 ISSUE-115
#   所指"拍脑袋"的同类,而 ISSUE-115 的裁决未覆盖这三样。本探针的用途 = 把三个参数的
#   候选值各自的客观后果测出来,供用户拍板。本脚本【只读、不写任何产物】。
#
# 复现命令: ADHD_ROOT=<有 data/ 的仓库根> .venv/bin/python analysis/55_cleaning_param_probe.py
import os, sys, time, importlib.util, pathlib
import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.stats import spearmanr

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("f42", HERE / "42_features_full.py")
f42 = importlib.util.module_from_spec(spec); spec.loader.exec_module(f42)
SRC, DATA = f42.SRC, f42.DATA

def banner(title, *lines):
    print("\n" + "#" * 80); print(f"# {title}")
    for l in lines: print(f"#   {l}")
    print("#" * 80)

# ---------------- 三样清理手法的实现 ----------------
def envelope(mag, fs, win_s):
    """滑动均方根(RMS)活动包络。win_s=0 表示不平滑(即现状:直接用原始信号)。"""
    if win_s <= 0: return mag
    n = max(1, int(round(win_s * fs)))
    return np.sqrt(uniform_filter1d(mag ** 2, size=n, mode="nearest"))

def binarize(x, thr_hi, thr_lo):
    """迟滞双阈值:x>thr_hi 进入活动,x<thr_lo 退出活动,两者之间保持原状态。
       thr_lo==thr_hi 即退化为现状的单阈值。信号开头未定状态时按'静止'起步。"""
    s = np.full(len(x), -1, np.int8)
    s[x > thr_hi] = 1
    s[x < thr_lo] = 0
    if thr_lo >= thr_hi:                      # 单阈值:>thr 为活动,其余静止
        return x > thr_hi
    valid = s >= 0
    if not valid.any(): return np.zeros(len(x), bool)
    idx = np.where(valid, np.arange(len(x)), 0)
    np.maximum.accumulate(idx, out=idx)
    out = s[idx].astype(bool)
    out[: int(np.argmax(valid))] = False       # 第一个已定状态之前一律记静止
    return out

def merge_short(active, min_len):
    """最短段合并:任何短于 min_len 个采样点的段,并进它【前面】那一段的状态。
       单趟扫描,天然收敛(合并后相邻同态段在下一步游程统计时自动接成一段)。"""
    if min_len <= 1: return active
    idx = np.flatnonzero(np.diff(active.astype(np.int8)) != 0) + 1
    starts = np.concatenate([[0], idx]); ends = np.concatenate([idx, [len(active)]])
    vals = active[starts].copy(); lens = ends - starts
    for i in range(1, len(vals)):
        if lens[i] < min_len: vals[i] = vals[i - 1]
    out = np.empty_like(active)
    for i in range(len(vals)): out[starts[i]:ends[i]] = vals[i]
    return out

def seg_stats(active, fs):
    """对二值序列做游程统计,返回与路径B同口径的几个量。"""
    idx = np.flatnonzero(np.diff(active.astype(np.int8)) != 0) + 1
    starts = np.concatenate([[0], idx]); ends = np.concatenate([idx, [len(active)]])
    lens = (ends - starts) / fs                      # 每段时长(秒)
    vals = active[starts]
    act = lens[vals]
    dur_min = len(active) / fs / 60.0
    return dict(
        actfrac=float(active.mean()),
        switch_per_min=float(np.sum(np.abs(np.diff(active.astype(np.int8))) > 0) / dur_min),
        act_bout_median=float(np.median(act)) if act.size else np.nan,
        frac_act_lt1s=float(np.mean(act < 1.0)) if act.size else np.nan,
        n_act_bouts=int(act.size),
    )

def pooled_thr(envs, pct):
    """合池阈值(TASK-1 决策5 的 c2「每人一票」):各人各算自己的第 pct 百分位,取 24 个数的中位数。
       注意:清理后阈值卡在【包络】上,故合池线必须在包络上重算——这正是 R10 那套泄漏数字
       可能整体失效的原因。"""
    return float(np.median([np.percentile(e, pct) for e in envs.values()]))

def run_variant(envs, fs, pct, hyst_lo_pct=None, hyst_ratio=1.0, min_bout_s=0.0):
    """对全体被试跑一种参数组合,返回 {被试: 指标dict} 与所用阈值。"""
    hi = pooled_thr(envs, pct)
    lo = pooled_thr(envs, hyst_lo_pct) if hyst_lo_pct is not None else hi * hyst_ratio
    min_len = int(round(min_bout_s * fs))
    out = {}
    for s, e in envs.items():
        a = binarize(e, hi, lo)
        if min_len > 1: a = merge_short(a, min_len)
        out[s] = seg_stats(a, fs)
    return out, hi, lo

def leak(res, key, mag_med):
    """该指标在 24 人间与'运动总量'负对照 uaMag_median 的秩相关绝对值(R10 口径)。"""
    subs = list(res)
    v = np.array([res[s][key] for s in subs], float)
    m = np.array([mag_med[s] for s in subs], float)
    if np.nanstd(v) == 0 or not np.all(np.isfinite(v)): return np.nan
    return abs(spearmanr(v, m).statistic)

def table(rows, cols, head):
    print(f"\n{head}")
    print("  " + "".join(f"{c:>16}" for c in cols))
    for name, d in rows:
        cells = "".join(f"{d[c]:>16.3f}" if isinstance(d[c], float) else f"{str(d[c]):>16}"
                        for c in cols)
        print(f"  {name:<26}{cells}")

# ================== 载入 24 人信号 ==================
aud = __import__("pandas").read_csv(SRC / "figures/subject_audit.csv")
SUBJ = sorted(aud[(aud.status == "usable") & (aud["_T"].astype(str).str.lower() == "yes")]
              .subject.tolist())
assert len(SUBJ) == 24
t0 = time.time(); MAG = {}; MAG_FULL = {}; FSS = {}
for s in SUBJ:
    df, fs, t, n_full = f42.load_T(DATA / f"{s}_T.csv", n_max=None)   # 先读全长
    m = np.linalg.norm(df[f42.USER_ACC].astype(float).to_numpy(), axis=1)
    MAG_FULL[s] = m                       # 未截断(探针5 口径核对要用)
    MAG[s] = m[:f42.N_TRUNC]              # 截断,与 features.csv 生产口径一致
    FSS[s] = fs
MAG_MED = {s: float(np.median(m)) for s, m in MAG.items()}
fs = float(np.median(list(FSS.values())))
print(f"载入 {len(SUBJ)} 人,每人 {len(MAG[SUBJ[0]]):,} 点(N_TRUNC={f42.N_TRUNC}),"
      f"fs≈{fs:.3f} Hz,耗时 {time.time()-t0:.1f} 秒")
print(f"被试列表: {SUBJ}")

MET = ["actfrac", "switch_per_min", "act_bout_median", "frac_act_lt1s", "n_act_bouts"]

def summarize(res, tag):
    d = {k: float(np.nanmedian([res[s][k] for s in SUBJ])) for k in MET}
    d["n_act_bouts"] = float(np.nanmedian([res[s]["n_act_bouts"] for s in SUBJ]))
    d["|ρ|actfrac~总量"] = leak(res, "actfrac", MAG_MED)
    d["|ρ|段中位~总量"] = leak(res, "act_bout_median", MAG_MED)
    return (tag, d)

SHOW = MET + ["|ρ|actfrac~总量", "|ρ|段中位~总量"]

# ================== 现状复核 ==================
banner("探针0  现状复核 —— ISSUE-102 报的毛刺数字能否复现",
       "现状 = 原始信号(不平滑) + 单阈值 + 不合并;阈值 = 24 人合池线(每人一票)",
       "ISSUE-102 原文(被试 H45):活动段中位 0.17 秒、92% 的段短于 1 秒、每分钟切换 148 次")
raw = {s: MAG[s] for s in SUBJ}
for pct in (50, 90):
    res, hi, lo = run_variant(raw, fs, pct)
    print(f"\n--- 阈值档 p{pct}  合池线={hi:.4f} G ---")
    print(f"  H45 实测: 活动段中位={res['H45']['act_bout_median']:.3f} 秒  "
          f"<1秒占比={res['H45']['frac_act_lt1s']*100:.1f}%  "
          f"切换={res['H45']['switch_per_min']:.1f} 次/分  "
          f"活动段数={res['H45']['n_act_bouts']}")
    table([summarize(res, f"现状 p{pct}(24人中位)")], SHOW, "")

# ================== 探针1:RMS 平滑窗长 ==================
banner("探针1  参数① RMS 平滑窗长 —— 取几秒",
       "只开平滑这一样(仍单阈值、不合并),看各候选窗长把碎片消到什么程度",
       "参照系:24 人 uaMag 自相关衰减到 1/e 的时间 中位 1.363 秒、25/75 分位 0.530/2.171 秒",
       "         (快照 analysis/probe_outputs/autocorr_timescale.md)")
WIN_CANDS = [0, 0.25, 0.5, 1, 2, 5]
for pct in (50, 90):
    rows = []
    for w in WIN_CANDS:
        envs = {s: envelope(MAG[s], fs, w) for s in SUBJ}
        res, hi, lo = run_variant(envs, fs, pct)
        rows.append(summarize(res, f"RMS窗={w}秒 (合池线{hi:.3f}G)"))
    table(rows, SHOW, f"=== 阈值档 p{pct}(每格为 24 人的中位数;后两列是与运动总量的秩相关) ===")

# ================== 探针2:迟滞两阈值 ==================
banner("探针2  参数② 迟滞的进入/退出两阈值 —— 差多少",
       "固定 RMS 窗=1 秒、不合并;比较三种参数化方式",
       "  (a) 无迟滞      = 进入与退出同一条线(现状)",
       "  (b) 比例式      = 退出线 = 进入线 × r,r 取 0.9/0.8/0.7",
       "  (c) 百分位对    = 进入线取第 p 档,退出线取第 p-10 档(与现有 9 档网格同源)")
for pct in (50, 90):
    envs = {s: envelope(MAG[s], fs, 1.0) for s in SUBJ}
    rows = []
    res, hi, lo = run_variant(envs, fs, pct); rows.append(summarize(res, f"(a) 无迟滞"))
    for r in (0.9, 0.8, 0.7):
        res, hi, lo = run_variant(envs, fs, pct, hyst_ratio=r)
        rows.append(summarize(res, f"(b) 退出=进入×{r} ({lo:.3f}G)"))
    if pct - 10 >= 5:
        res, hi, lo = run_variant(envs, fs, pct, hyst_lo_pct=pct - 10)
        rows.append(summarize(res, f"(c) 进p{pct}/退p{pct-10} ({lo:.3f}G)"))
    table(rows, SHOW, f"=== 阈值档 p{pct},RMS 窗=1 秒(进入线={hi:.3f}G) ===")

# ================== 探针3:最短段合并 ==================
banner("探针3  参数③ 最短段合并 —— 短于多少的段并掉",
       "固定 RMS 窗=1 秒 + 迟滞(退出=进入×0.8);逐个候选看剩余碎片")
for pct in (50, 90):
    envs = {s: envelope(MAG[s], fs, 1.0) for s in SUBJ}
    rows = []
    for mb in (0, 0.25, 0.5, 1.0, 2.0):
        res, hi, lo = run_variant(envs, fs, pct, hyst_ratio=0.8, min_bout_s=mb)
        rows.append(summarize(res, f"最短段={mb}秒"))
    table(rows, SHOW, f"=== 阈值档 p{pct},RMS 窗=1 秒 + 迟滞0.8 ===")

# ================== 探针4:三步的边际贡献 ==================
banner("探针4  三样手法各自的边际贡献 —— 谁在起作用",
       "逐步叠加:现状 -> +RMS(1秒) -> +迟滞(0.8) -> +最短段合并(1秒)")
for pct in (50, 90):
    rows = []
    res, _, _ = run_variant({s: MAG[s] for s in SUBJ}, fs, pct)
    rows.append(summarize(res, "0 现状(原始+单阈值)"))
    envs = {s: envelope(MAG[s], fs, 1.0) for s in SUBJ}
    res, _, _ = run_variant(envs, fs, pct); rows.append(summarize(res, "1 +RMS 1秒"))
    res, _, _ = run_variant(envs, fs, pct, hyst_ratio=0.8); rows.append(summarize(res, "2 +迟滞 0.8"))
    res, _, _ = run_variant(envs, fs, pct, hyst_ratio=0.8, min_bout_s=1.0)
    rows.append(summarize(res, "3 +最短段 1秒"))
    table(rows, SHOW, f"=== 阈值档 p{pct} ===")

# ================== 探针5:R10 那套泄漏数字的口径核对 ==================
banner("探针5  R10 泄漏数字的口径核对 —— 0.877 测的到底是哪个量",
       "起因:working/backlog.md §9 的 R10 与 working/task.md 的 TASK-1「未解决的方法学张力」",
       "      都把 |ρ|=0.877(p50 档)/0.300(p90 档)当作【路径B那 45 列】的泄漏程度,",
       "      出处是 analysis/probe_outputs/pooling_leakage.md(脚本 50_temporal_design_probes.py 探针2)。",
       "      但读该脚本第 101-126 行:它把阈值卡在【10 秒窗/5 秒步的窗均值序列】上,且读【未截断】信号——",
       "      那是【路径A的信号形态 + 路径B的合池阈值】,与出厂的路径B(逐采样点 + 截断 73643)不是同一个量。",
       "本探针把四种组合并排跑出来,判定 0.877 属于哪一格。",
       "⚠️ 本表不修改任何既有记录,只是把口径差异测出来备案(只进不出)。")

def winmean(m, fs_, win_s=10, step_s=5):
    w, st = int(win_s * fs_), int(step_s * fs_)
    return np.array([m[i:i + w].mean() for i in range(0, len(m) - w, st)])

print(f"\n  {'信号长度':<12}{'序列形态':<18}{'档':<5}{'合池线(G)':>11}"
      f"{'|ρ|actfrac~总量':>18}{'|ρ|段中位~总量':>18}")
for tag, SIG in (("未截断", MAG_FULL), ("截断73643", MAG)):
    med = [float(np.median(SIG[s])) for s in SUBJ]
    for mode in ("窗均值(10s/5s)", "逐采样点"):
        series = {s: (winmean(SIG[s], FSS[s]) if mode.startswith("窗") else SIG[s]) for s in SUBJ}
        for p in (50, 90):
            pooled = float(np.median([np.percentile(series[s], p) for s in SUBJ]))
            af, abm = [], []
            for s in SUBJ:
                a = series[s] > pooled
                af.append(float(a.mean()))
                idx = np.flatnonzero(np.diff(a.astype(np.int8)) != 0) + 1
                st_ = np.concatenate([[0], idx]); en = np.concatenate([idx, [len(a)]])
                unit = 5.0 if mode.startswith("窗") else 1.0 / FSS[s]
                act = (en - st_)[a[st_]] * unit
                abm.append(float(np.median(act)) if act.size else np.nan)
            def rr(v):
                v = np.array(v, float)
                return np.nan if np.nanstd(v) == 0 else abs(spearmanr(v, np.array(med, float)).statistic)
            print(f"  {tag:<12}{mode:<18}p{p:<4}{pooled:>11.4f}{rr(af):>18.3f}{rr(abm):>18.3f}")
print("\n  对照 analysis/probe_outputs/pooling_leakage.md 记的数:p50 档 actfrac 0.877 / act_bout_median 0.624;")
print("                                                  p90 档 actfrac 0.300 / act_bout_median 0.374")

print("\n" + "=" * 80)
print("说明:本探针只读,不写任何产物。上表用于给 TASK-115 的三个参数选值,")
print("     选定后由 42_features_full.py 落地,验收另见 TASK-115 的变化量化探针。")
