# -*- coding: utf-8 -*-
# =============================================================================
# 53_stat_budget_probes.py  —  "统计预算"探针:多加特征要付多少校正代价、n=24 能看见多大的关系
# =============================================================================
# 这是什么(给未来任何一个不了解本项目的人):
#   这个文件【不是】生产管线的一部分,不产生任何特征、不写任何文件。
#   它是两只【探针(probe)】——把几个数字摊开供人拍板,跑完只在终端打印。
#   "探针"是本项目里一类脚本的固定叫法(见 analysis/32_、33_、50_、51_、52_),
#   含义=探索性、只读、只打印、结论供人决策,不参与生产链路。
#
# 与 52_scan_compute_cost.py 的分工:52 号量的是【机器时间和内存】(要跑多久、
#   放不放得下);本文件量的是【统计预算】(多测几次要在显著性上付多少代价、
#   本项目的样本量能看见多大的关系)。两者都不读原始腕表信号以外的东西——
#   本文件更进一步,连原始信号都不读,只读既有的建模结果表。
#
# 它给哪些决策供数:
#
#   探针 1 —— 特征数增长对多重比较校正的代价   → 供 TASK-10 / TASK-108 / ISSUE-121
#     背景:A 轨(单变量筛查,analysis/44_univariate_screen.py)把每个特征单独与每个
#       症状分算一次相关,再用 BH-FDR 做多重比较校正,得到 q 值(q<0.05 才算通过)。
#       测得越多,纯靠运气蒙中的越多,校正就扣得越狠。
#     问题:如果特征数从现在的数量再往上加(TASK-10 补特征大类、TASK-108 扫窗长
#       都会加列),已有那些线索的 q 值会变差多少?
#     算法:取 A_univariate.csv 里每个目标现有的置换 p 值,再往里掺 K 个"纯噪声"
#       特征(其 p 值服从 0–1 均匀分布),重算 BH-FDR,看最小 q 怎么动。重复多次取中位。
#       同时算一个反向情形:若新增的特征里【有一个是真信号】,q 会怎么动。
#     为什么要模拟而不是直接乘:BH-FDR 不是简单的 p×m,它按排名逐个比较,
#       新增的检验同时进入分子和分母,所以必须真的重算一遍。
#
#   探针 2 —— n=24 能看见多大的关系(检验效能与置信区间)  → 供 ISSUE-116 / 全项目
#     背景:本项目可用被试 24 人。样本量决定了"多弱的关系能被看见"和"看见了能说多准"。
#     算法:纯统计公式,不读数据。①算 p<0.05 所需的最小相关系数;②算若真实关系是
#       某个强度,能被测出来的概率(检验效能 power);③算观测到某个相关系数时,
#       它的 95% 置信区间有多宽(Fisher z 变换);④反过来算要达到 80% 效能需要多少人。
#     用途:它划定的是【上限】——任何特征工程、任何模型、任何筛选方法都突破不了它。
#
# 复现:
#   ADHD_ROOT=<有 analysis/A_univariate.csv 的仓库根> .venv/bin/python analysis/53_stat_budget_probes.py
#
# 注意:探针 1 依赖 analysis/A_univariate.csv。该文件是 44_univariate_screen.py 的产物、
#   未纳入 git 版本控制(见 .gitignore),故本探针在干净检出上跑不了,须先跑一次 A 轨。
#   本文件头部会打印它读到的那份 A_univariate.csv 的形状与时间戳,以便判断结果的时效。
# =============================================================================
import os, sys, pathlib, datetime
import numpy as np, pandas as pd
from scipy import stats

HERE = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path(os.environ.get("ADHD_ROOT", HERE.parent)).resolve()
RNG = np.random.default_rng(0)          # 固定随机种子,让模拟结果可复现

def banner(title, *notes):
    print("\n" + "#" * 80)
    print(f"# {title}")
    for n in notes:
        print(f"#   {n}")
    print("#" * 80)

# =============================================================================
# 探针 1  特征数增长对多重比较校正的代价
# =============================================================================
A_PATH = ROOT / "analysis/A_univariate.csv"
if not A_PATH.exists():
    sys.exit(f"找不到 {A_PATH} —— 该表是 44_univariate_screen.py 的产物且不入库,"
             f"请先跑一次 A 轨,或把 ADHD_ROOT 指向已有该文件的检出。")

A = pd.read_csv(A_PATH)
mtime = datetime.datetime.fromtimestamp(A_PATH.stat().st_mtime)

def bh(p):
    """Benjamini-Hochberg FDR:输入一组 p 值,返回对应的 q 值。
    与 44_univariate_screen.py:95-99 的实现逐行一致(故意复刻,保证口径相同)。"""
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p)
    q = np.empty(m)
    prev = 1.0
    for rank, idx in enumerate(order[::-1]):
        i = m - rank
        val = min(prev, p[idx] * m / i)
        prev = val
        q[idx] = val
    return q

CONT = A[A.type == "cont"]
n_feat_cur = CONT.groupby("target").size().iloc[0]
targets = sorted(CONT.target.unique())

banner("探针1  特征数增长对 BH-FDR 校正的代价(供 TASK-10 / TASK-108 / ISSUE-121)",
       f"数据源: {A_PATH}",
       f"  形状 {A.shape[0]} 行 × {A.shape[1]} 列;文件时间戳 {mtime:%Y-%m-%d %H:%M}",
       f"现有连续目标 {len(targets)} 个,每个目标 {n_feat_cur} 个特征各测一次",
       f"新增特征按【纯噪声】模拟(p ~ Uniform(0,1)),每种情形重复 {200} 次取中位数",
       "q<0.05 才算通过校正")

ADD = (0, 200, 400, 600)
NSIM = 200
rows = []
for t in targets:
    p0 = CONT.loc[CONT.target == t, "perm_p"].to_numpy(float)
    rec = {"目标": t, "现有特征数": len(p0), "最小p": round(float(p0.min()), 4)}
    for K in ADD:
        if K == 0:
            rec[f"q(+{K})"] = round(float(bh(p0).min()), 3)
        else:
            vals = [bh(np.concatenate([p0, RNG.uniform(0, 1, K)])).min() for _ in range(NSIM)]
            rec[f"q(+{K})"] = round(float(np.median(vals)), 3)
    rows.append(rec)
res = pd.DataFrame(rows).sort_values("q(+0)")
print()
print(res.to_string(index=False))

print()
print("  --- 反向情形:若新增的特征里【有 1 个是真信号】(p=0.001)---")
best_t = res.iloc[0]["目标"]
p0 = CONT.loc[CONT.target == best_t, "perm_p"].to_numpy(float)
for K in ADD:
    extra = np.concatenate([[0.001], RNG.uniform(0, 1, K)]) if K else np.array([0.001])
    print(f"    目标 {best_t}:新增 {K:3d} 个噪声特征 + 1 个真信号 -> "
          f"最小 q = {bh(np.concatenate([p0, extra])).min():.3f}")
print(f"    对照:不新增任何特征时 最小 q = {bh(p0).min():.3f}")
print("    -> 即新增特征对 q 的影响是双向的:纯噪声使其变差,含真信号则可使其变好。")

print()
print("  --- 全局检验数与纯噪声期望的对照 ---")
n_all = len(A)
n_sig = int((A.perm_p < 0.05).sum())
print(f"    A 轨全部检验数(含二分目标)= {n_all:,}")
print(f"    其中 p<0.05 的实际个数 = {n_sig}")
print(f"    纯噪声下 p<0.05 的期望个数 = 0.05 × {n_all:,} = {0.05*n_all:.1f}")
print(f"    实际 / 噪声期望 = {n_sig/(0.05*n_all):.2f}")
print(f"    现有 q<0.05 的检验数 = {int((A.q_fdr < 0.05).sum())}")
print("    注:现有 q_fdr 列是【按每个目标各自校正】算的"
      "(44_univariate_screen.py:101 的 groupby('target')),")
print("       与 ISSUE-121 待裁的『分轨 a / 合并 b』两个方案都不同——那是第三种口径。")

# =============================================================================
# 探针 2  n=24 能看见多大的关系
# =============================================================================
N_SUBJ = 24
ALPHA = 0.05

banner(f"探针2  样本量 n={N_SUBJ} 的检验效能与置信区间(供 ISSUE-116 / 全项目)",
       "纯统计公式,不读数据。相关系数的抽样分布用 Fisher z 变换近似",
       "它划定的是上限:任何特征工程 / 模型 / 筛选方法都突破不了")

tc = stats.t.ppf(1 - ALPHA / 2, N_SUBJ - 2)
r_crit = tc / np.sqrt(N_SUBJ - 2 + tc ** 2)
print()
print(f"  --- ① 单次检验要达到 p<{ALPHA} 所需的最小相关系数 ---")
print(f"      |rho| >= {r_crit:.3f}   (弱于这个数的关系,在 n={N_SUBJ} 下单次检验看不见)")

print()
print(f"  --- ② 检验效能:真实关系为某强度时,能被测出来的概率 ---")
se = 1 / np.sqrt(N_SUBJ - 3)
zc = np.arctanh(r_crit)
for rtrue in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7):
    z = np.arctanh(rtrue)
    power = stats.norm.sf((zc - z) / se) + stats.norm.cdf((-zc - z) / se)
    print(f"      真实 rho={rtrue:.1f}  ->  检出概率 = {power*100:5.1f}%")

print()
print(f"  --- ③ 观测到某个相关系数时,它的 95% 置信区间 ---")
for r in (0.30, 0.40, 0.45, 0.50, 0.57, 0.70):
    z = np.arctanh(r)
    lo, hi = np.tanh(z - 1.96 * se), np.tanh(z + 1.96 * se)
    print(f"      观测 rho={r:.2f}  ->  95%CI [{lo:+.2f}, {hi:+.2f}]   区间宽度 {hi-lo:.2f}")
print(f"      -> 区间普遍很宽:即使观测到较大的相关,也只能说方向,说不准强度。")

print()
print(f"  --- ④ 反过来:要达到 80% 检验效能,需要多少人 ---")
for rtrue in (0.3, 0.4, 0.5, 0.6):
    z = np.arctanh(rtrue)
    nn = ((1.96 + 0.84) / z) ** 2 + 3
    print(f"      若真实 rho={rtrue:.1f}  ->  需要 n ≈ {int(np.ceil(nn))}")

print("\n" + "=" * 80)
print("探针结束。本脚本未写任何文件。")
print("=" * 80)
