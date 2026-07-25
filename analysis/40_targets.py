# -*- coding: utf-8 -*-
# 阶段0:为 24 个建模样本算出【所有候选目标 y】(SNAP/SDQ 各子量表+总),标准尺度。
# 标准计分:数据 1-indexed(CODEBOOK §1),标准分 = 数据-1;
#   SNAP 无反向题;SDQ 反向题(7,11,14,21,25)标准反向分 = 3 - 数据。
# 只读 data/,输出 analysis/targets.csv。
import numpy as np, pandas as pd
ROOT="/Users/shiyu/Projects/adhd-segmentation/"
clin=pd.read_csv(ROOT+"data/Demographic and mental health data.csv",encoding="utf-8-sig",dtype=str)
clin.columns=[c.strip() for c in clin.columns]
aud=pd.read_csv(ROOT+"figures/subject_audit.csv")
SUBJ=sorted(aud[(aud.status=="usable")&(aud["_T"].astype(str).str.lower()=="yes")].subject.tolist())
assert len(SUBJ)==24, len(SUBJ)

df=clin.set_index("ID")
SDQ=[f"SDQ{i}" for i in range(1,26) if f"SDQ{i}" in df.columns]
SNAP=[f"a{i}" for i in range(1,27)]
for c in SDQ+SNAP: df[c]=pd.to_numeric(df[c],errors="coerce")
df.loc[df.get("SDQ8")==13,"SDQ8"]=np.nan   # 越界异常(不过 S32 不在24人里)

REV={7,11,14,21,25}                          # SDQ 反向题
def sdq_std(i):                              # 标准 0-2:反向=3-d,正向=d-1
    d=df[f"SDQ{i}"]
    return (3-d) if i in REV else (d-1)
def sdq_sub(items):                          # 子量表标准分(某题缺就该人 NaN)
    cols=[sdq_std(i) for i in items if f"SDQ{i}" in df.columns]
    return pd.concat(cols,axis=1).sum(axis=1,min_count=len(cols))
def snap_sub(items):                         # SNAP 标准 0-3 = d-1
    cols=[(df[f"a{i}"]-1) for i in items]
    return pd.concat(cols,axis=1).sum(axis=1,min_count=len(cols))

T=pd.DataFrame(index=df.index)
# ---- SNAP(标准 0-3/项)----
T["snap_inatt"]=snap_sub(range(1,10))        # 注意力缺陷 9题 0-27
T["snap_hyper"]=snap_sub(range(10,19))       # 多动 9题 0-27
T["snap_odd"]  =snap_sub(range(19,27))       # 对立违抗 8题 0-24
T["snap_total"]=snap_sub(range(1,27))        # 0-78
# ---- SDQ(标准 0-2/项)----
T["sdq_hyper"]=sdq_sub([2,10,15,21,25])      # 多动 5题 0-10
T["sdq_emo"]  =sdq_sub([3,8,13,16,24])       # 情绪 0-10
T["sdq_cond"] =sdq_sub([5,7,12,18,22])       # 品行 0-10
T["sdq_peer"] =sdq_sub([6,11,14,23])         # 同伴 4题(缺19)0-8
T["sdq_pro"]  =sdq_sub([1,4,9,17,20])        # 亲社会 0-10
T["sdq_totdiff"]=T[["sdq_emo","sdq_cond","sdq_hyper","sdq_peer"]].sum(axis=1,min_count=4)  # 总困难

out=T.loc[SUBJ]
out.index.name="subject"
out.to_csv(ROOT+"analysis/targets.csv")

# ---- 题目级标准计分表 items.csv(TASK-8 决定4:"桥")----
# 为什么要这张表:标签引擎 43_target_labels.py 的 symptom_count 切法要按题计数
# (某题评分够高才算"有该症状"),而 targets.csv 只有 10 个子量表总分、没有逐题分。
# 让引擎自己去啃 data/ 里的原始问卷,就得把下面这套换算(1-indexed 减 1、SDQ 反向
# 题翻转)在两个文件里各写一遍,将来必然漂移且不一致时不报错。所以在这里多输出一张
# 逐题表,换算逻辑只有这一份;引擎只读 targets.csv + items.csv,不碰 data/。
I=pd.DataFrame(index=df.index)
for i in range(1,27):        I[f"snap_a{i}"]=df[f"a{i}"]-1        # SNAP 标准 0-3
for i in range(1,26):                                            # SDQ 标准 0-2(缺 SDQ19)
    if f"SDQ{i}" in df.columns: I[f"sdq_{i}"]=sdq_std(i)
items=I.loc[SUBJ]; items.index.name="subject"
items.to_csv(ROOT+"analysis/items.csv")

print(f"24 人候选目标 -> analysis/targets.csv  ({out.shape[0]}行 × {out.shape[1]}列)")
print(f"24 人逐题标准分 -> analysis/items.csv  ({items.shape[0]}行 × {items.shape[1]}列;"
      f"SNAP 26 题 0-3 + SDQ {items.shape[1]-26} 题 0-2,反向题已翻转)")
print("\n各目标:范围 / 均值 / 缺失数")
for c in out.columns:
    v=out[c]
    print(f"  {c:12} min={v.min():.0f} max={v.max():.0f} mean={v.mean():.1f}  缺失={v.isna().sum()}")
print("\n前5行:"); print(out.head().round(1).to_string())
