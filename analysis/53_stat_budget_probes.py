# -*- coding: utf-8 -*-
# =============================================================================
# 53_stat_budget_probes.py  —  "统计预算"探针:多加特征要付多少校正代价、n=24 能看见多大的关系
# =============================================================================
# 这是什么(给未来任何一个不了解本项目的人):
#   这个文件【不是】生产管线的一部分,不产生任何特征、不写任何文件。
#   它是三只【探针(probe)】——把几个数字摊开供人拍板,跑完只在终端打印。
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
#   探针 3 —— 置换分辨率给 FDR 设的硬门槛   → 供 ISSUE-121 / TASK-113
#     背景:本项目的 p 值不是从理论分布查表来的,而是【置换检验】算的——把症状分随机打乱
#       很多次,看"打乱后的成绩比真实成绩还好"的比例有多少,这个比例就是 p。
#       打乱的次数(NPERM)决定了 p 能取到的【最小值】:打乱 5000 次,p 最小只能到 1/5000。
#     问题:BH-FDR 的 q 值算法是 q = p × 家族里的检验总数 ÷ 该检验的排名。若最强的那个
#       检验已经把 p 打到下限,它的 q 就等于 "p下限 × 检验总数"。家族一大,这个乘积可能
#       直接超过 0.05——那么【无论数据里有多强的信号,排名第一的检验都不可能通过校正】。
#       此时唯一的出路是有多个检验【并列】达到下限,把分母上的"排名"抬上去。
#     本探针回答:在各种家族口径下,需要多少个检验同时达到 p 下限,才可能有一条通过 q<0.05?
#     为什么重要:这个门槛与"数据里有没有信号"无关,是纯粹由置换次数和家族大小决定的
#       【结构性上限】。若门槛高到不现实,那个口径就等于事先宣布不会有任何确证结论。
#     两轨的 p 下限公式【不同】,本探针分别处理:
#       A 轨 44_univariate_screen.py:64  pval = max(pval, 1.0/NPERM)      -> 下限 1/NPERM
#       B 轨 45_multivariate_cv.py:101   return (sum(hits)+1)/(NPERM+1)   -> 下限 1/(NPERM+1)
#     NPERM 的取值直接从两个生产脚本里解析,不在此处硬编,以免与生产代码漂移。
#
# 复现:
#   ADHD_ROOT=<有 analysis/A_univariate.csv 的仓库根> .venv/bin/python analysis/53_stat_budget_probes.py
#
# 注意:探针 1 依赖 analysis/A_univariate.csv。该文件是 44_univariate_screen.py 的产物、
#   未纳入 git 版本控制(见 .gitignore),故本探针在干净检出上跑不了,须先跑一次 A 轨。
#   本文件头部会打印它读到的那份 A_univariate.csv 的形状与时间戳,以便判断结果的时效。
# =============================================================================
import os, sys, re, pathlib, datetime
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

# =============================================================================
# 探针 3  置换分辨率给 FDR 设的硬门槛
# =============================================================================
def parse_nperm(path):
    """从生产脚本里解析 NPERM 的取值,避免与生产代码漂移。"""
    txt = pathlib.Path(path).read_text()
    m = re.search(r"^NPERM\s*=\s*(\d+)", txt, re.M) or re.search(r"NPERM\s*=\s*(\d+)", txt)
    if not m:
        sys.exit(f"在 {path} 里找不到 NPERM 的赋值")
    return int(m.group(1))

NPERM_A = parse_nperm(HERE / "44_univariate_screen.py")
NPERM_B = parse_nperm(HERE / "45_multivariate_cv.py")
FLOOR_A = 1.0 / NPERM_A              # 44:64  pval = max(pval, 1.0/NPERM)
FLOOR_B = 1.0 / (NPERM_B + 1)        # 45:101 (sum(hits)+1)/(NPERM+1)

banner("探针3  置换分辨率给 BH-FDR 设的硬门槛(供 ISSUE-121 / TASK-113)",
       f"A 轨 NPERM={NPERM_A}(解析自 44_univariate_screen.py) -> p 下限 = 1/NPERM = {FLOOR_A:.6f}",
       f"B 轨 NPERM={NPERM_B}(解析自 45_multivariate_cv.py) -> p 下限 = 1/(NPERM+1) = {FLOOR_B:.6f}",
       "q(排名第1) = p下限 × 家族检验总数;需 N 个并列达下限才可能有一条 q<0.05")

def need_tied(floor, m):
    """要让至少一个检验通过 q<0.05,需多少个检验并列达到 p 下限。
    BH: q(rank=i) = p × m / i。取 p=floor,解 floor×m/i < 0.05 得 i > floor×m/0.05。"""
    return int(np.ceil(floor * m / 0.05))

# 特征数有两个来源,必须分清:
#   n_feat_A  = 旧 A 表 A_univariate.csv 里每个目标的检验数——那份表算于 TASK-1 重写之前,
#               已过期(见探针1 打印的文件时间戳),仅用于说明"当时的门槛"。
#   n_feat_now= 当前 analysis/features.csv 的实际特征列数——TASK-106 重跑后 A 表将与它一致,
#               ISSUE-121 条目里引用的数字用的是这一个。
n_feat_A = n_feat_cur
F_PATH = ROOT / "analysis/features.csv"
n_feat_now = (pd.read_csv(F_PATH, nrows=1).shape[1] - 1) if F_PATH.exists() else n_feat_A
print()
print(f"  [特征数口径] 旧 A 表每目标检验数 = {n_feat_A}(已过期);"
      f"当前 features.csv 特征列数 = {n_feat_now}(TASK-106 重跑后 A 表将与此一致)")

# B 轨的家族大小 = 「目标 × 模型 × k」组合数。ISSUE-121 / TASK-113 条目里记的是 198,
#   但那个数是 2026-07-18 那次跑出来的,【已过期】:TASK-109(commit a13dc7d)删掉了
#   snap_total 及其标签列 snap_total__wang2025T55,二分目标由 11 个降到 10 个,
#   family 随之由 198 降到 192(11-10=1 个目标 × 3 模型 × 2 个 k = 6)。
#   故这里【按 45_multivariate_cv.py 的同一套选取规则从标签表现算】,不硬编,
#   并把条目里记的 198 一并列出来做对照,以免读者拿旧数去核对。
N_MODELS, N_K = 3, 2                      # REG/CLF 各 3 个模型;KS=[5,10]
def b_family_size():
    """复算 B 轨组合数。规则与 45_multivariate_cv.py 的 CONT / BIN / MULTI 三段一致。"""
    Yc_ = pd.read_csv(ROOT / "analysis/targets.csv").set_index("subject")
    Yl_ = pd.read_csv(ROOT / "analysis/target_labels.csv").set_index("subject")
    Ylm_ = pd.read_csv(ROOT / "analysis/target_labels_meta.csv")
    degen = set(Ylm_.loc[Ylm_["degenerate"] == True, "label_name"])
    n_bin = len([c for c in Yl_.columns if c.endswith("__qbin") and c not in degen])
    n_multi = len([f"{b}__{s}"
                   for b in ["snap_inatt", "snap_hyper", "snap_odd", "snap_adhd_total",
                             "sdq_hyper", "sdq_totdiff"]
                   for s in ["qter", "qquar"]
                   if f"{b}__{s}" in Yl_.columns
                   and Yl_[f"{b}__{s}"].nunique() == (3 if s == "qter" else 4)
                   and f"{b}__{s}" not in degen])
    return (Yc_.shape[1] + n_bin + n_multi) * N_MODELS * N_K, Yc_.shape[1], n_bin, n_multi

B_M, _nc, _nb, _nm = b_family_size()
B_RECORDED = 198                          # ISSUE-121 / TASK-113 条目里写死的数(2026-07-18 口径)
print(f"  [B轨家族大小] 现算 = ({_nc} 连续 + {_nb} 二分 + {_nm} 多分类) × {N_MODELS} 模型"
      f" × {N_K} 个 k = {B_M}"
      + ("" if B_M == B_RECORDED else
         f"  ← 与条目里记的 {B_RECORDED} 不一致(TASK-109 删 snap_total__wang2025T55 所致),"
         f"须回头核对 ISSUE-121 / TASK-113 条目"))

CASES = [
    ("A轨 · 每个目标各自一族(ISSUE-121 裁定的 5b 口径,当前特征数)", FLOOR_A, n_feat_now),
    ("A轨 · 同上,TASK-108 完成后(特征 -> 571)",                    FLOOR_A, 571),
    ("A轨 · 4 个主目标合成一族(5a,未采纳)",                        FLOOR_A, 4 * n_feat_now),
    ("A轨 · 全部 21 个目标族合并",                                  FLOOR_A, 21 * n_feat_now),
    ("B轨 · 全部组合一族(现算 m=%d,现状 NPERM=%d)" % (B_M, NPERM_B), FLOOR_B, B_M),
    ("B轨 · 同上,但按条目记的 m=%d" % B_RECORDED,                   FLOOR_B, B_RECORDED),
    ("〔改动前对照〕B轨 m=%d,NPERM=500(TASK-113 改动之前)" % B_M,   1/501,   B_M),
    ("A+B 全合并(方案b,未采纳)",                                    FLOOR_A, 21 * n_feat_now + B_M),
    ("〔对照〕A轨 每目标一族,按【旧】A 表的 %d 特征" % n_feat_A,    FLOOR_A, n_feat_A),
]
rows = []
for lab, fl, m in CASES:
    rows.append({"家族口径": lab, "p下限": round(fl, 6), "检验数m": m,
                 "q(排名第1)": round(fl * m, 4), "需几个并列达下限": need_tied(fl, m)})
print()
print(pd.DataFrame(rows).to_string(index=False))
print()
print("  读法:「q(排名第1)」若已 >0.05,则最强的那个检验【单靠自己永远过不了校正】,")
print("        必须靠多个检验并列达到 p 下限、把排名抬上去才可能有一条存活。")
print("        该门槛与数据里有没有信号无关,纯由置换次数与家族大小决定。")
print()
print(f"  ISSUE-121 据此裁定:确证家族取「4 个主目标各自一族」(每族 m={n_feat_now},"
      f"需 {need_tied(FLOOR_A, n_feat_now)} 个),")
_before = 1/501
if NPERM_B >= 5000:
    print(f"  并把 B 轨 NPERM 由 500 提到 {NPERM_B}(TASK-113,【已改,本次解析到的即是改后值】):")
    print(f"    改动前 NPERM=500  -> B 轨排名第 1 的 q={_before*B_M:.3f}"
          f"(需 {need_tied(_before,B_M)} 个并列达 p 下限才可能有 1 条过 q<0.05)")
    print(f"    改动后 NPERM={NPERM_B} -> q={FLOOR_B*B_M:.3f}"
          f"(需 {need_tied(FLOOR_B,B_M)} 个),即单个即可通过。")
else:
    print(f"  并把 B 轨 NPERM 由 {NPERM_B} 提到 5000(TASK-113,【尚未改】):")
    print(f"    现状 NPERM={NPERM_B} -> B 轨排名第 1 的 q={FLOOR_B*B_M:.3f}"
          f"(需 {need_tied(FLOOR_B,B_M)} 个并列)")
    print(f"    提到 5000 后    -> q={B_M/5001:.3f}(需 {need_tied(1/5001,B_M)} 个),即单个即可通过。")

print("\n" + "=" * 80)
print("探针结束。本脚本未写任何文件。")
print("=" * 80)
