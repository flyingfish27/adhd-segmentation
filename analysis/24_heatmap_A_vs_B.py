# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
from itertools import combinations
import matplotlib; matplotlib.use("Agg")
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
Cfull=Xr.corr(method="spearman")

# 两套分组
A=[("Emotional",[3,8,13,16,24]),("Conduct",[5,7,12,18,22]),("Hyperactivity",[2,10,15,21,25]),
   ("Peer",[6,11,14,23]),("Prosocial",[1,4,9,17,20])]
B=[("Cols 1-5",[1,2,3,4,5]),("Cols 6-10",[6,7,8,9,10]),("Cols 11-15",[11,12,13,14,15]),
   ("Cols 16-20",[16,17,18,20]),("Cols 21-25",[21,22,23,24,25])]

def wb(groups):
    g={i:name for name,items in groups for i in items}
    win,bet=[],[]
    for a,b in combinations(avail,2):
        r=Cfull.loc[a,b]
        if np.isnan(r): continue
        (win if g[a]==g[b] else bet).append(r)
    return np.mean(win),np.mean(bet)

fig,axes=plt.subplots(1,2,figsize=(18,8.8))
for ax,(groups,title,who) in zip(axes,[(A,"A: ordered by standard subscales (= original item numbers)","A"),
                                        (B,"B: ordered by contiguous column blocks","B")]):
    order=[i for _,items in groups for i in items]
    C=Cfull.loc[order,order]
    im=ax.imshow(C.values,cmap="RdBu_r",vmin=-1,vmax=1)
    n=len(order); labels=[f"SDQ{i}" for i in order]
    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels(labels,rotation=90,fontsize=6.5,color="#333")
    ax.set_yticklabels(labels,fontsize=6.5,color="#333")
    ax.set_xticks(np.arange(-.5,n,1),minor=True); ax.set_yticks(np.arange(-.5,n,1),minor=True)
    ax.grid(which="minor",color="white",linewidth=1); ax.tick_params(which="minor",length=0)
    b=0
    for name,items in groups:
        k=len(items)
        ax.add_patch(Rectangle((b-0.5,b-0.5),k,k,fill=False,edgecolor="black",linewidth=2.4))
        ax.text(b+k/2-0.5,-0.75,name,ha="center",va="bottom",fontsize=8,fontweight="bold",color="#222")
        b+=k
    w,bt=wb(groups)
    ax.set_title(f"{title}\nwithin={w:+.3f}  between={bt:+.3f}  gap={w-bt:+.3f}",
                 fontsize=12,pad=30,color="#111")

fig.suptitle("Same correlations, different grouping:  A shows red diagonal blocks;  B shows none (blocks vanish => B is wrong)",
             fontsize=13,y=0.99,color="#111")
cax=fig.add_axes([0.93,0.15,0.015,0.7]); fig.colorbar(im,cax=cax,label="Spearman r")
plt.tight_layout(rect=[0,0,0.92,0.96])
out="/Users/shiyu/Projects/adhd-segmentation/figures/sdq_corr_A_vs_B.png"
plt.savefig(out,dpi=150,bbox_inches="tight",facecolor="white"); print("saved:",out)
