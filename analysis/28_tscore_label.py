# -*- coding: utf-8 -*-
# 目的:把论文1的 ADHD 标签算法(SNAP总分 -> Z -> T=Z*10+50 -> T>=55)逐步算出来,看真实数值。
import pandas as pd, numpy as np
P="/Users/shiyu/Projects/adhd-segmentation/data/Demographic and mental health data.csv"
df=pd.read_csv(P,encoding="utf-8-sig",dtype=str); df.columns=[c.strip() for c in df.columns]
SNAP=[f"a{i}" for i in range(1,27)]
num=df.copy()
for c in SNAP: num[c]=pd.to_numeric(num[c],errors="coerce")

# 每人 SNAP 总分 = 26 项之和(原始 1-4),只取 26 项齐全者
total=num[SNAP].sum(axis=1, min_count=len(SNAP))
sub=df.loc[total.notna(),"ID"]; total=total.dropna()

mean=total.mean(); sd=total.std(ddof=1)          # 论文说的"样本均值和标准差"
z=(total-mean)/sd                                 # 第1步:Z 分
T=z*10+50                                          # 第2步:T = Z*10+50
adhd=T>=55                                          # 第3步:阈值

print(f"参与者数(SNAP齐全) N = {len(total)}")
print(f"SNAP总分:  mean = {mean:.4f}   sd = {sd:.4f}")
print(f"T>=55  <=>  Z>=0.5  <=>  总分 >= mean + 0.5*sd = {mean + 0.5*sd:.4f}")
print(f"ADHD(T>=55) 人数 = {int(adhd.sum())}   非ADHD = {int((~adhd).sum())}")
print()
print("被判 ADHD 的人(ID, 总分, Z, T):")
for i in total.index:
    if adhd[i]:
        print(f"  {df.loc[i,'ID']:>4}  total={total[i]:.0f}  Z={z[i]:+.3f}  T={T[i]:.2f}")

print("\n【要点1】整个标签只依赖 mean 和 sd —— T 分只是把 Z 线性放大(×10+50)。")
print("       T>=55 完全等价于 Z>=0.5,即'总分比样本均值高出 0.5 个标准差'。")

# 验证:对 SNAP 做 -1 偏移(1-4 -> 0-3),标签是否改变?
total0=(num[SNAP]-1).sum(axis=1, min_count=len(SNAP)).dropna()
z0=(total0-total0.mean())/total0.std(ddof=1); T0=z0*10+50
print(f"\n【要点2】若把 SNAP 减1变 0-3 再算:ADHD 人数 = {int((T0>=55).sum())}  (与上面相同)")
print("       => 因为 Z 分对'每人同减一个常数'不变,所以是否减1不影响标签。")
