# -*- coding: utf-8 -*-
# ============================================================================
# 目的(只做这一件事):探索性找规律。
# 把所有反向题先翻正(4-x),让 24 题方向统一,再把两两相关排序(负数在前),
# 看哪些题真正"一起动"(正相关)、哪些真正"对立"(负相关)。
# 方向已对齐,所以这里的负相关 = 真正的构念对立,不是反向计分造成的假象。
# (要回答"数据存的是翻转前还是翻转后"是另一个问题,见另一个专门脚本,不在此混。)
# ============================================================================
import pandas as pd, numpy as np
from itertools import combinations
P="/Users/shiyu/Projects/adhd-segmentation/data/Demographic and mental health data.csv"
df=pd.read_csv(P,encoding="utf-8-sig",dtype=str); df.columns=[c.strip() for c in df.columns]
SDQ=[c for c in df.columns if c.startswith("SDQ")]
num=df.copy()
for c in SDQ: num[c]=pd.to_numeric(num[c],errors="coerce")
num.loc[num["SDQ8"]==13,"SDQ8"]=np.nan
avail=[int(c[3:]) for c in SDQ]

# 全部方向对齐:反向题翻正 4-x
revset={7,11,14,21,25}
Xr=pd.DataFrame({i:(4-num[f"SDQ{i}"]) if i in revset else num[f"SDQ{i}"] for i in avail})
C=Xr.corr(method="spearman")

# 子量表标签,仅事后解读用
sub={**{i:"emo" for i in [3,8,13,16,24]}, **{i:"cond" for i in [5,7,12,18,22]},
     **{i:"hyp" for i in [2,10,15,21,25]}, **{i:"peer" for i in [6,11,14,19,23]},
     **{i:"pro" for i in [1,4,9,17,20]}}
def tag(i): return f"SDQ{i}({sub[i]})"

pairs=[(C.loc[a,b],a,b) for a,b in combinations(avail,2) if not np.isnan(C.loc[a,b])]
pairs.sort()   # 负数在前

print(f"共 {len(pairs)} 对(所有题方向已翻正)。\n")
print("========== 最负的 14 对(负数在前 = 最强对立)==========")
for r,a,b in pairs[:14]:
    print(f"  {r:+.3f}   {tag(a):14s} <-> {tag(b):14s}  {'同组' if sub[a]==sub[b] else '跨组'}")
print("\n========== 最正的 14 对(= 最强一起动)==========")
for r,a,b in pairs[-14:][::-1]:
    print(f"  {r:+.3f}   {tag(a):14s} <-> {tag(b):14s}  {'同组' if sub[a]==sub[b] else '跨组'}")
