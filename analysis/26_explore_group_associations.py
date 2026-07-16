# -*- coding: utf-8 -*-
# ============================================================================
# 目的(只做这一件事):方向全部对齐(反向题翻正 Xr=4-x)后,看子量表(组)
# 之间哪些正相关(一起动)、哪些对立(负)。产出 5x5 "子量表 x 子量表" 平均
# Spearman 相关矩阵 + 热力图。不涉及"数据是否已翻转"的问题。
# ============================================================================
import pandas as pd, numpy as np
from itertools import combinations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform

P = "/Users/shiyu/Projects/adhd-segmentation/data/Demographic and mental health data.csv"
FIG = "/Users/shiyu/Projects/adhd-segmentation/figures/sdq_group_association_5x5.png"

df = pd.read_csv(P, encoding="utf-8-sig", dtype=str)
df.columns = [c.strip() for c in df.columns]
SDQ = [c for c in df.columns if c.startswith("SDQ")]
num = df.copy()
for c in SDQ:
    num[c] = pd.to_numeric(num[c], errors="coerce")
num.loc[num["SDQ8"] == 13, "SDQ8"] = np.nan   # 唯一异常值当缺失
avail = [int(c[3:]) for c in SDQ]

# 方向全部对齐:反向题翻正 4-x
revset = {7, 11, 14, 21, 25}
Xr = pd.DataFrame({i: (4 - num[f"SDQ{i}"]) if i in revset else num[f"SDQ{i}"] for i in avail})
C = Xr.corr(method="spearman")   # 24x24 题级相关(方向已对齐)

# 标准子量表
subs = {"emo": [3, 8, 13, 16, 24], "cond": [5, 7, 12, 18, 22],
        "hyp": [2, 10, 15, 21, 25], "peer": [6, 11, 14, 19, 23],
        "pro": [1, 4, 9, 17, 20]}
subs = {g: [i for i in items if i in avail] for g, items in subs.items()}  # SDQ19 缺失,剔除
groups = list(subs.keys())   # emo cond hyp peer pro

# ---- 5x5 组x组平均相关矩阵 ----
# 对角(组内)= 该组内所有题对相关的平均;非对角(组间)= 跨组每对题相关的平均
M = pd.DataFrame(np.nan, index=groups, columns=groups)
for g1 in groups:
    for g2 in groups:
        if g1 == g2:
            vals = [C.loc[a, b] for a, b in combinations(subs[g1], 2)]
        else:
            vals = [C.loc[a, b] for a in subs[g1] for b in subs[g2]]
        vals = [v for v in vals if not np.isnan(v)]
        M.loc[g1, g2] = np.mean(vals)

pd.set_option("display.width", 120, "display.float_format", lambda x: f"{x:+.3f}")
print("========== 5x5 子量表 x 子量表 平均 Spearman 相关(方向已对齐)==========")
print("对角=组内平均一致性;非对角=组间平均关联(正=一起动,负=对立)\n")
print(M.to_string())

# 组间关联排序(只看非对角)
print("\n---------- 组间关联排序(非对角,负在前 = 对立)----------")
offpairs = [(M.loc[g1, g2], g1, g2) for g1, g2 in combinations(groups, 2)]
offpairs.sort()
for r, g1, g2 in offpairs:
    tone = "对立(负)" if r < 0 else "一起动(正)"
    print(f"  {r:+.3f}   {g1:5s} <-> {g2:5s}   {tone}")

# ---- 热力图 ----
labels_full = {"emo": "Emotional", "cond": "Conduct", "hyp": "Hyperactivity",
               "peer": "Peer", "pro": "Prosocial"}
labs = [labels_full[g] for g in groups]
A = M.values.astype(float)
fig, ax = plt.subplots(figsize=(7.2, 6.2))
im = ax.imshow(A, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(5)); ax.set_yticks(range(5))
ax.set_xticklabels(labs, rotation=30, ha="right"); ax.set_yticklabels(labs)
for i in range(5):
    for j in range(5):
        v = A[i, j]
        ax.text(j, i, f"{v:+.2f}", ha="center", va="center",
                color="white" if abs(v) > 0.55 else "black", fontsize=11)
ax.set_title("SDQ subscale x subscale mean Spearman correlation\n(all items direction-aligned, reverse items flipped 4-x)",
             fontsize=11)
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cb.set_label("mean Spearman r")
fig.tight_layout()
fig.savefig(FIG, dpi=150)
print(f"\n[saved figure] {FIG}")

# ---- 可选:层次聚类(距离=1-相关,对齐后不取绝对值)----
print("\n========== 可选:题级层次聚类(距离=1-corr,方向已对齐)==========")
D = 1.0 - C.values
np.fill_diagonal(D, 0.0)
D = (D + D.T) / 2.0
Z = linkage(squareform(D, checks=False), method="average")
order = dendrogram(Z, no_plot=True, labels=list(C.columns))["ivl"]
sub_of = {i: g for g, items in subs.items() for i in items}
print("叶序(从聚类树)及其所属组:")
print("  " + "  ".join(f"SDQ{i}({sub_of[i]})" for i in order))
