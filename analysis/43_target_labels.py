# -*- coding: utf-8 -*-
# 阶段2:把连续目标 y 切成分组标签(喂分类模型)。只读 targets.csv,输出:
#   analysis/target_labels.csv  —— 每个 (目标 × 切法) 一列
#   分位数切法(样本内相对排名,不依赖常模,永远可辩护):median 二分 / 三分 / 四分。
#   常模锚定二分:仅 SNAP 总分 T≥55(论文1 的 ADHD 定义,在这24人内重算)。
#   诚实标注:SDQ多动常模异常线≥8 在本样本 0/24 退化,不生成;切不出 k 组的显式记录。
import numpy as np, pandas as pd, pathlib
ROOT=pathlib.Path("/Users/shiyu/Projects/adhd-segmentation")
t=pd.read_csv(ROOT/"analysis/targets.csv").set_index("subject")

out=pd.DataFrame(index=t.index)
log=[]   # (标签列名, 切法, 各组人数, 备注)

def qcut_label(v,k,name):
    """分位数切 k 组;并列过多则丢重复边界,报告实际组数与人数。"""
    try:
        lab=pd.qcut(v,k,labels=False,duplicates="drop")
    except Exception as e:
        log.append((name,f"q{k}","FAILED",str(e))); return None
    ng=lab.nunique()
    sizes=lab.value_counts().sort_index().to_dict()
    note="" if ng==k else f"并列导致实际只有 {ng} 组(目标k={k})"
    log.append((name,f"q{k}",sizes,note))
    return lab

for c in t.columns:
    v=t[c]
    # 中位二分 / 三分 / 四分
    for k,tag in [(2,"bin"),(3,"ter"),(4,"quar")]:
        lab=qcut_label(v,k,f"{c}__q{tag}")
        if lab is not None: out[f"{c}__q{tag}"]=lab

# ---- 常模锚定二分:SNAP 总分 T≥55(论文1 口径,样本内重算)----
v=t["snap_total"]; z=(v-v.mean())/v.std(ddof=1); T=z*10+50
out["snap_total__normT55"]=(T>=55).astype(int)
log.append(("snap_total__normT55","norm(T>=55)",
            out["snap_total__normT55"].value_counts().sort_index().to_dict(),
            "论文1 ADHD 定义(在24人内重算,与论文n=50不同)"))

# ---- 退化记录:SDQ多动常模≥8 ----
deg=int((t["sdq_hyper"]>=8).sum())
log.append(("sdq_hyper__norm8","norm(>=8)",{"阳性":deg,"阴性":24-deg},
            "退化:0/24 达到异常线 → 不生成此列"))

out.to_csv(ROOT/"analysis/target_labels.csv")

# ---- 汇报 ----
print("目标标签表 -> analysis/target_labels.csv  形状:",out.shape)
print("\n每列(切法 / 各组人数 / 备注):")
for name,scheme,sizes,note in log:
    gen = "(未生成)" if "不生成" in note else ""
    print(f"  {name:24} {scheme:12} {str(sizes):28} {note}{gen}")
print("\n连续回归目标仍用 targets.csv 原列(10 个)。")
print("生成的分组标签列数:",out.shape[1])
