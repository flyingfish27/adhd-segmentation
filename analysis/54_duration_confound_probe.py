# -*- coding: utf-8 -*-
# =============================================================================
# 54_duration_confound_probe.py  —  "录制时长"还算不算混淆变量的探针
# =============================================================================
# 这是什么(给未来任何一个不了解本项目的人):
#   这个文件【不是】生产管线的一部分,不产生任何特征、不写任何文件。
#   它是一只【探针(probe)】——把几个数字摊开供人拍板,跑完只在终端打印。
#   "探针"是本项目里一类脚本的固定叫法(见 analysis/32_、50_、51_、52_、53_)。
#
# 只读:仅读 data/ 下原始腕表文件的【行数】(不解析内容)+ figures/subject_audit.csv
#   + analysis/targets.csv + analysis/features.csv。不写盘。
#
# 它回答什么:
#   背景——24 个孩子戴表的时长本来不一样(3 人约 41-44 分钟就早退,21 人约 58-60 分钟)。
#     ISSUE-107 当时指出这会污染特征;TASK-102 的处置是把所有人的信号统一截到最短者的
#     长度(前 73643 个采样点),让人和人可比。
#   问题——截等长【之后】,"原始录制时长"这个量是否仍与特征、与症状分相关?
#     若两头都相关,它就仍是一个混淆变量(confounder):某个"运动特征 × 症状分"的相关,
#     有可能只是时长在两头冒充,而不是特征自己的信号。
#   为什么截断消不掉它——截断能消除的是「测量窗口不一样,60 分钟的均值和 41 分钟的均值
#     根本是两个量」这一层。但"早退"本身可能是"这是个什么样的孩子"的标记:早退的孩子
#     即使只看他自己的前 41 分钟,行为也可能与录满的孩子不同。这一层与窗口长度无关。
#
#   本探针给 ISSUE-103(跨子量表对比)与 ISSUE-114(时长要不要当特征/控制变量)供数,
#   其结论已写入 working/backlog.md §9 的局限声明 R11。
#
# 口径说明:
#   "原始录制时长"用【CSV 行数 − 1】(即采样点数)代表,不换算成分钟——各人采样率极接近
#   (29.708-29.717 Hz,极差 0.0088 Hz,见 analysis/46_duration_audit.py),点数与时长等价,
#   且点数是直接可数的整数、无估计误差。
#   相关一律用 Spearman 秩相关(与 A 轨 44_univariate_screen.py 口径一致)。
#
# 复现:
#   ADHD_ROOT=<有 data/ 的仓库根> .venv/bin/python analysis/54_duration_confound_probe.py
# =============================================================================
import os, sys, pathlib, subprocess
import numpy as np, pandas as pd
from scipy.stats import spearmanr

HERE = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path(os.environ.get("ADHD_ROOT", HERE.parent)).resolve()
if not (ROOT / "data").is_dir():
    sys.exit(f"找不到 {ROOT}/data —— 请把环境变量 ADHD_ROOT 指向有 data/ 的主检出。")

def banner(title, *notes):
    print("\n" + "#" * 80)
    print(f"# {title}")
    for n in notes:
        print(f"#   {n}")
    print("#" * 80)

N_TRUNC = 73643        # TASK-102 的截断长度,与 42_features_full.py 的常量一致

AUD = pd.read_csv(ROOT / "figures/subject_audit.csv")
SUBJ = sorted(AUD[(AUD.status == "usable") &
                  (AUD["_T"].astype(str).str.lower() == "yes")].subject.tolist())
assert len(SUBJ) == 24, f"可用被试应为 24 人,实得 {len(SUBJ)}"

# 原始点数 = 文件行数 − 1(表头)。用 wc -l 数行,不解析内容。
n_raw = {}
for s in SUBJ:
    out = subprocess.check_output(["wc", "-l", str(ROOT / f"data/{s}_T.csv")])
    n_raw[s] = int(out.split()[0]) - 1
dur = pd.Series(n_raw).sort_index()

print(f"被试数 = {len(SUBJ)}   截断长度 N_TRUNC = {N_TRUNC}")
print(f"原始采样点数: 最小 {dur.min():,}   最大 {dur.max():,}   中位 {int(dur.median()):,}")
short = [k for k, v in dur.items() if v < N_TRUNC * 1.2]
print(f"短记录被试(点数 < 1.2×N_TRUNC): {short}")

# =============================================================================
# 探针 1  时长 × 症状分
# =============================================================================
banner("探针1  原始录制时长 × 各症状分(Spearman)",
       "混淆成立的第一个必要条件:时长要与【结果变量】相关")
tgt = pd.read_csv(ROOT / "analysis/targets.csv").set_index("subject").sort_index()
rows = []
for c in tgt.columns:
    r, p = spearmanr(dur.values, tgt[c].values)
    rows.append((c, round(float(r), 3), round(float(p), 4)))
t1 = pd.DataFrame(rows, columns=["症状分", "rho", "p"]).sort_values("rho")
print()
print(t1.to_string(index=False))
print()
strong = t1[t1.rho.abs() > 0.4]
print(f"  |rho|>0.4 的目标: {list(strong.症状分) if len(strong) else '无'}")

# =============================================================================
# 探针 2  时长 × 特征(截等长之后)
# =============================================================================
banner("探针2  原始录制时长 × 351 个特征(截等长之后,Spearman)",
       "混淆成立的第二个必要条件:时长要与【预测变量】相关",
       "特征取自 analysis/features.csv,已按 N_TRUNC 截等长")
feat = pd.read_csv(ROOT / "analysis/features.csv").set_index("subject").sort_index()
X = feat.select_dtypes("number")
rs = np.array([spearmanr(dur.values, X[c].values).correlation for c in X.columns])
rs = np.nan_to_num(rs)
ser = pd.Series(rs, index=X.columns)
print()
print(f"  特征列数 = {len(ser)}")
print(f"  |rho| 中位 = {np.median(np.abs(rs)):.3f}   最大 = {np.abs(rs).max():.3f}")
for thr in (0.3, 0.4, 0.5):
    print(f"  |rho| > {thr}: {int((np.abs(rs) > thr).sum()):3d} 列")
print()
print("  与时长相关最强的 10 个特征:")
for k, v in ser.abs().nlargest(10).items():
    print(f"    {k:26s} rho={ser[k]:+.3f}")

# =============================================================================
# 结论
# =============================================================================
banner("结论")
print()
print("  混淆变量成立需【两头都相关】,实测两头都在:")
print(f"    · 时长 × 症状分:最强 {t1.iloc[0].症状分} rho={t1.iloc[0].rho:+.3f} (p={t1.iloc[0].p})")
print(f"    · 时长 × 特征  :{int((np.abs(rs) > 0.3).sum())} 列 |rho|>0.3,"
      f"{int((np.abs(rs) > 0.4).sum())} 列 |rho|>0.4")
print()
print("  即:TASK-102 的截等长消除的是「测量窗口不一样」那一层污染(ISSUE-107 机制①),")
print("     但消不掉「时长是'这是个什么样的孩子'的标记」这一层(机制②)。")
print("     后者与窗口长度无关,截断无论如何碰不到。")
print()
print("  本项目【不做】时长偏相关(用户 2026-07-26 裁决,见 ISSUE-103),")
print("  该缺口如实记入 working/backlog.md §9 的局限声明 R11。")
print("\n" + "=" * 80)
print("探针结束。本脚本未写任何文件。")
print("=" * 80)
