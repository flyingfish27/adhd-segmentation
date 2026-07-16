# -*- coding: utf-8 -*-
# 不预设任何分组、不做反向校正:把 24 题两两相关全部排序,负数在前。
import pandas as pd, numpy as np
from itertools import combinations
P="/Users/shiyu/Projects/adhd-segmentation/data/Demographic and mental health data.csv"
df=pd.read_csv(P,encoding="utf-8-sig",dtype=str); df.columns=[c.strip() for c in df.columns]
SDQ=[c for c in df.columns if c.startswith("SDQ")]
num=df.copy()
for c in SDQ: num[c]=pd.to_numeric(num[c],errors="coerce")
num.loc[num["SDQ8"]==13,"SDQ8"]=np.nan       # 唯一处理:剔除越界异常
avail=[int(c[3:]) for c in SDQ]

# 原始相关(不翻转任何题)
X=pd.DataFrame({i:num[f"SDQ{i}"] for i in avail})
C=X.corr(method="spearman")

# 标准子量表归属(仅用于事后打标签解释,不参与计算/排序)
sub={**{i:"emo" for i in [3,8,13,16,24]}, **{i:"cond" for i in [5,7,12,18,22]},
     **{i:"hyp" for i in [2,10,15,21,25]}, **{i:"peer" for i in [6,11,14,19,23]},
     **{i:"pro" for i in [1,4,9,17,20]}}
rev={7,11,14,21,25}
def tag(i): return f"SDQ{i}({sub[i]}{'*' if i in rev else ''})"

pairs=[]
for a,b in combinations(avail,2):
    r=C.loc[a,b]
    if not np.isnan(r): pairs.append((r,a,b))
pairs.sort()                                  # 升序:最负在前

print(f"共 {len(pairs)} 对。*=该题在标准SDQ里是反向计分题(子量表标签仅事后解释用)\n")
print("========== 最负的 14 对(负数在前)==========")
for r,a,b in pairs[:14]:
    same = "  <同一子量表>" if sub[a]==sub[b] else ""
    print(f"  {r:+.3f}   {tag(a):16s} <-> {tag(b):16s}{same}")
print("\n========== 最正的 14 对 ==========")
for r,a,b in pairs[-14:][::-1]:
    same = "  <同一子量表>" if sub[a]==sub[b] else ""
    print(f"  {r:+.3f}   {tag(a):16s} <-> {tag(b):16s}{same}")

# 统计:正相关里"同子量表"占比 vs 负相关里"跨子量表 & 涉及反向题"占比
top_pos=[p for p in pairs if p[0]>=0.35]
top_neg=[p for p in pairs if p[0]<=-0.30]
def frac_same(ps):
    return sum(sub[a]==sub[b] for _,a,b in ps), len(ps)
sp=frac_same(top_pos); sn=frac_same(top_neg)
print(f"\n强正相关(r>=0.35)共 {sp[1]} 对,其中同一子量表 {sp[0]} 对")
print(f"强负相关(r<=-0.30)共 {sn[1]} 对,其中涉及反向题(*)的 "
      f"{sum((a in rev)or(b in rev) for _,a,b in top_neg)} 对")
