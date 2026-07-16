# -*- coding: utf-8 -*-
# 完全不预设分组、不翻转任何题:让层次聚类自己把 24 题分簇。
# 距离 = 1 - |相关|,这样"强正"和"强负"都算"近"(反向题也能和本构念聚在一起)。
import pandas as pd, numpy as np
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
from scipy.spatial.distance import squareform

P="/Users/shiyu/Projects/adhd-segmentation/data/Demographic and mental health data.csv"
df=pd.read_csv(P,encoding="utf-8-sig",dtype=str); df.columns=[c.strip() for c in df.columns]
SDQ=[c for c in df.columns if c.startswith("SDQ")]
num=df.copy()
for c in SDQ: num[c]=pd.to_numeric(num[c],errors="coerce")
num.loc[num["SDQ8"]==13,"SDQ8"]=np.nan
avail=[int(c[3:]) for c in SDQ]

X=pd.DataFrame({i:num[f"SDQ{i}"] for i in avail})   # 原始,不翻转
C=X.corr(method="spearman")

# 标准子量表(仅事后打标签核对,不参与聚类)
sub={**{i:"emo" for i in [3,8,13,16,24]}, **{i:"cond" for i in [5,7,12,18,22]},
     **{i:"hyp" for i in [2,10,15,21,25]}, **{i:"peer" for i in [6,11,14,19,23]},
     **{i:"pro" for i in [1,4,9,17,20]}}
rev={7,11,14,21,25}
def tag(i): return f"SDQ{i}({sub[i]}{'*' if i in rev else ''})"

# 距离矩阵 D = 1 - |C|,对角置 0
D=(1-C.abs()).values
np.fill_diagonal(D,0.0)
Z=linkage(squareform(D,checks=False), method="average")

# 树状图的叶子顺序(聚类自己决定的排列)
order_idx=dendrogram(Z, no_plot=True)["leaves"]
leaf_order=[avail[i] for i in order_idx]
print("聚类自己得到的题目排列(叶子顺序):")
print("  ", " ".join(tag(i) for i in leaf_order))

# 切成 5 簇,列出每簇成员
lab=fcluster(Z, t=5, criterion="maxclust")
print("\n切成 5 簇(算法自动分,未告知任何标签):")
for c in sorted(set(lab)):
    members=[avail[i] for i in range(len(avail)) if lab[i]==c]
    print(f"  簇{c}: " + "  ".join(tag(i) for i in members))

# 交叉表:发现的簇 vs 标准子量表
print("\n交叉表(行=算法发现的簇,列=标准子量表,格子=题数):")
ct=pd.crosstab(pd.Series(lab,name="cluster"),
               pd.Series([sub[i] for i in avail],name="canonical"))
print(ct.to_string())
