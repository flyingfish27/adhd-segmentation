# -*- coding: utf-8 -*-
# TASK-116 体检:新加的特征列 rec_dur_min(录制时长)长什么样、口径怎么选、有多脆。
#
# 背景:ISSUE-114 于 2026-07-26 裁决"录制时长【当特征】、不当控制变量",执行落在 TASK-116——
#   在 analysis/42_features_full.py 里加一列,记【截断之前】那个人的真实录制长度
#   (TASK-102 已把参与计算的窗口统一到 N_TRUNC=73643 点,若记截断后的长度则 24 人全同)。
#
# 本脚本要回答四个问题(前三个 ISSUE-114 条目提过但从未量化,第四个此前无人提出):
#   ① 这一列的取值实际怎么分布?有多少个不同的值?
#   ② 与 10 个症状分的秩相关各是多少(ISSUE-114 只记了 sdq_totdiff 的 ρ=−0.474)。
#   ③ ISSUE-114 原话说它"极其脆弱:这个相关几乎全押在只有 3 个早退孩子身上,抽掉一个就可能崩"
#      —— 崩到什么程度?用留一法逐个抽掉再重算,把这句话变成数字。
#   ④ 【本脚本发现的问题】"录制时长"有三种度量方式,它们给出【不同的排序和不同的结论】:
#        口径① 采样点数 n_full          —— 探针 54 用的(`wc -l` 数行),ISSUE-114/R11/ISSUE-103 引用的 ρ=−0.474 出自这里
#        口径② 时间戳跨度 t[-1]−t[0]    —— 直接测量的真实时钟时长,无估计误差;TASK-116 的 rec_dur_min 取此口径
#        口径③ n_full / fs / 60         —— 由点数换算,fs 由采样间隔中位数估得
#      探针 54 的头部注释写着"各人采样率极接近……点数与时长等价"。**本脚本证伪该等价性**:
#      对秩统计而言三者不等价,因为 24 人里 21 人都录满、真实时长跨度仅约 1.36 分钟
#      (其中 20 人落在不到 0.4 秒之内),而采样率的相对差异(0.03%)与之同量级,
#      故除不除以 fs 会把这 20 人的排序整个打乱。
#
# ⚠️ 本脚本使用症状分。它不做分析方案的选择——该列是否纳入已由 ISSUE-114 裁定;
#    本脚本只是把一个【已经决定要用】的列的性质与已知局限量化,供交付局限清单(backlog §9 R11)引用。
#
# 只读,不写产物。
# 复现命令: ADHD_ROOT=<有 data/ 的仓库根> .venv/bin/python analysis/56_rec_duration_column_audit.py
import importlib.util, pathlib
import numpy as np, pandas as pd
from scipy.stats import spearmanr

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("f42", HERE / "42_features_full.py")
f42 = importlib.util.module_from_spec(spec); spec.loader.exec_module(f42)

aud = pd.read_csv(f42.SRC / "figures/subject_audit.csv")
SUBJ = sorted(aud[(aud.status == "usable") & (aud["_T"].astype(str).str.lower() == "yes")]
              .subject.tolist())
rows = []
for s in SUBJ:
    df, fs, t, n_full = f42.load_T(f42.DATA / f"{s}_T.csv")
    rows.append(dict(subject=s, n_full=n_full, fs=fs,
                     span_min=df.attrs["span_full_s"] / 60.0,       # 口径②(生产列)
                     n_over_fs_min=n_full / fs / 60.0))             # 口径③
D = pd.DataFrame(rows).set_index("subject").sort_values("span_min")
tgt = pd.read_csv(f42.ROOT / "analysis/targets.csv").set_index("subject").loc[D.index]
TARGETS = list(tgt.columns)
MEASURES = [("① 采样点数 n_full", D.n_full.to_numpy(float)),
            ("② 时间戳跨度(生产列 rec_dur_min)", D.span_min.to_numpy(float)),
            ("③ n_full/fs/60", D.n_over_fs_min.to_numpy(float))]

print("=" * 82)
print("① rec_dur_min 的实际分布(24 人,按真实时长升序;span_min 即入表的那一列)")
print("=" * 82)
print(D.to_string(float_format=lambda v: f"{v:.5f}"))

v = D.span_min.to_numpy(float)
print(f"\n  取值范围        : {v.min():.3f} – {v.max():.3f} 分钟")
print(f"  不同取值个数    : {len(np.unique(v))} / 24")
lg = v[v > 50]
print(f"  '录满'那组      : {len(lg)} 人,跨度 {lg.max()-lg.min():.3f} 分钟 = {60*(lg.max()-lg.min()):.1f} 秒")
tight = v[v > 59.5]
print(f"  其中最挤的一簇  : {len(tight)} 人落在 {tight.min():.4f}–{tight.max():.4f} 分钟,"
      f"跨度仅 {60*(tight.max()-tight.min()):.2f} 秒")
print(f"  '早退'那组      : {(v < 50).sum()} 人 = {list(D.index[v < 50])}")
print("\n  读法:这一列在结构上接近一个【3–4 档变量】(3 个早退 + 1 个 58.4 分 + 20 个≈59.750 分),")
print("        不是连续变量。那 20 人之间的排序由不足 0.4 秒的停表时刻差决定,")
print("        而秩相关会把这些亚秒差异当成真实的排名信息来用。")

print("\n" + "=" * 82)
print("④ 三种口径彼此有多不一致(本脚本发现的问题,先看这个——它决定下面所有数字的意义)")
print("=" * 82)
print("\n  三种口径【互相之间】的秩相关(若'点数与时长等价'成立,这里应全部≈1.000):")
for i in range(len(MEASURES)):
    for j in range(i + 1, len(MEASURES)):
        r = spearmanr(MEASURES[i][1], MEASURES[j][1]).statistic
        print(f"    {MEASURES[i][0]:32} vs {MEASURES[j][0]:32} ρ={r:+.4f}")
print("\n  同一个症状分,三种口径给出的相关(挑 |ρ| 最大的三个目标展示):")
print(f"\n  {'目标':<18}" + "".join(f"{m:>36}" for m, _ in MEASURES))
for tn in TARGETS:
    cells = ""
    for _, mv in MEASURES:
        r = spearmanr(mv, tgt[tn].to_numpy(float))
        mark = " *" if r.pvalue < 0.05 else "  "
        cells += f"{f'{r.statistic:+.3f} (p={r.pvalue:.3f}){mark}':>36}"
    print(f"  {tn:<18}{cells}")
print("\n  ( * = 未校正 p<0.05 )")
print("  读法:同一个物理量的三种度量,给出的结论不一致——例如 sdq_totdiff 在口径① 下 p=0.016,")
print("        在口径②③ 下 p=0.16/0.24。ISSUE-114/R11/ISSUE-103 引用的 ρ=−0.474 出自口径①。")

print("\n" + "=" * 82)
print("② 生产列(口径②)与 10 个症状分的秩相关")
print("=" * 82)
base = {}
for tn in TARGETS:
    r = spearmanr(v, tgt[tn].to_numpy(float))
    base[tn] = (r.statistic, r.pvalue)
    flag = "  <- |ρ|≥0.404(未校正 p<0.05)" if abs(r.statistic) >= 0.404 else ""
    print(f"  rec_dur_min × {tn:16} ρ={r.statistic:+.3f}  p={r.pvalue:.4f}{flag}")

print("\n" + "=" * 82)
print("③ 脆弱性:留一法逐个抽掉一个被试后重算(把 ISSUE-114 那句'抽掉一个就可能崩'变成数字)")
print("=" * 82)
for name, mv in MEASURES:
    print(f"\n  --- 口径 {name} ---")
    for tn in TARGETS:
        r0 = spearmanr(mv, tgt[tn].to_numpy(float)).statistic
        if abs(r0) < 0.30: continue
        y = tgt[tn].to_numpy(float)
        loo = sorted((spearmanr(np.delete(mv, i), np.delete(y, i)).statistic, s)
                     for i, s in enumerate(D.index))
        weakest = min(loo, key=lambda x: abs(x[0]))
        n_lose = sum(1 for r_, _ in loo if abs(r_) < 0.404)
        print(f"    {tn:14} 全体 ρ={r0:+.3f} | 留一范围 {loo[0][0]:+.3f}~{loo[-1][0]:+.3f}"
              f" | 最弱 {weakest[0]:+.3f}(抽掉 {weakest[1]})"
              f" | {n_lose}/24 种留一会让 |ρ|<0.404")

print("\n" + "=" * 82)
print("⑤ 抽掉全部 3 个早退被试后,这一列还剩什么")
print("=" * 82)
keep = v > 50
print(f"  剩 {keep.sum()} 人,真实时长跨度 {v[keep].max()-v[keep].min():.3f} 分钟")
for tn in TARGETS:
    r = spearmanr(v[keep], tgt[tn].to_numpy(float)[keep]).statistic
    print(f"    rec_dur_min × {tn:16} ρ={r:+.3f}   (全体 24 人时为 {base[tn][0]:+.3f})")
print("\n  读法:若抽掉早退者之后相关塌掉,说明这一列携带的信息基本就是'谁早退了',")
print("        而不是'录制时长'这个连续量本身。这正是 backlog §9 的 R11 要声明的内容。")
print("\n注:本脚本只读、不写产物。该列是否纳入已由 ISSUE-114 裁定,本脚本不做方案选择。")
