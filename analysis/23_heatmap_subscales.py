# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

P="/Users/shiyu/Projects/adhd-segmentation/data/Demographic and mental health data.csv"
df=pd.read_csv(P,encoding="utf-8-sig",dtype=str); df.columns=[c.strip() for c in df.columns]
SDQ=[c for c in df.columns if c.startswith("SDQ")]
num=df.copy()
for c in SDQ: num[c]=pd.to_numeric(num[c],errors="coerce")
num.loc[num["SDQ8"]==13,"SDQ8"]=np.nan
avail=[int(c[3:]) for c in SDQ]; revset={7,11,14,21,25}
Xr=pd.DataFrame({i:(4-num[f"SDQ{i}"]) if i in revset else num[f"SDQ{i}"] for i in avail})

# 按子量表 A 排序(缺 19)
groups=[("Emotional",[3,8,13,16,24]),("Conduct",[5,7,12,18,22]),
        ("Hyperactivity",[2,10,15,21,25]),("Peer",[6,11,14,23]),
        ("Prosocial",[1,4,9,17,20])]
order=[i for _,items in groups for i in items]
C=Xr[order].corr(method="spearman")

# --- 发散配色:-1 蓝 / 0 中性 / +1 红,vmin/vmax 对称使 0 落在中点 ---
fig,ax=plt.subplots(figsize=(11,9.2))
im=ax.imshow(C.values,cmap="RdBu_r",vmin=-1,vmax=1)
cbar=fig.colorbar(im,ax=ax,shrink=0.82,pad=0.02)
cbar.set_label("Spearman correlation (reverse items corrected)",fontsize=10)

n=len(order)
labels=[f"SDQ{i}" for i in order]
ax.set_xticks(range(n)); ax.set_yticks(range(n))
ax.set_xticklabels(labels,rotation=90,fontsize=7.5,color="#333")
ax.set_yticklabels(labels,fontsize=7.5,color="#333")
ax.set_xticks(np.arange(-.5,n,1),minor=True); ax.set_yticks(np.arange(-.5,n,1),minor=True)
ax.grid(which="minor",color="white",linewidth=1.2); ax.tick_params(which="minor",length=0)

# 每格标注相关值(小字,深色对浅底/浅色对深底)
for r in range(n):
    for c in range(n):
        v=C.values[r,c]
        ax.text(c,r,f"{v:+.2f}"[1:] if v>=0 else f"{v:.2f}",
                ha="center",va="center",fontsize=5.6,
                color="white" if abs(v)>0.6 else "#444")

# 子量表边界粗线 + 组名
b=0
for name,items in groups:
    k=len(items)
    ax.add_patch(Rectangle((b-0.5,b-0.5),k,k,fill=False,edgecolor="black",linewidth=2.2))
    ax.text(b+k/2-0.5,-0.75,name,ha="center",va="bottom",fontsize=9,fontweight="bold",color="#222")
    b+=k

ax.set_title("SDQ 24-item correlation matrix (ordered by the 5 standard subscales)\n"
             "Black box = within-subscale  ->  Hyperactivity forms a bright block; Peer stays pale",
             fontsize=12,pad=46,color="#111")
plt.tight_layout()
out="/Users/shiyu/Projects/adhd-segmentation/figures/sdq_corr_heatmap.png"
plt.savefig(out,dpi=150,bbox_inches="tight",facecolor="white")
print("saved:",out)
