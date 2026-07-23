# -*- coding: utf-8 -*-
# 阶段3-A轨:单变量筛查。每个特征单独 × 每个目标,诚实评估。一次只用1个特征 → 无多变量过拟合。
#   连续目标:Spearman ρ(效应量) + 置换 p + 留一 R²_cv(闭式PRESS,泛化) + 留一 RMSE/MAE。
#   二分目标:AUC(=Mann-Whitney,秩基,免拟合) + 置换 p。
#   置换零分布对固定目标与特征无关(只依赖 n / 组大小)→ 每目标算一次,275特征共用。
# 输出 analysis/A_univariate.csv(长表),并打印各目标 top 命中 + 负对照 mag_median。
import numpy as np, pandas as pd, pathlib
from scipy.stats import rankdata
ROOT=pathlib.Path("/Users/shiyu/Projects/adhd-segmentation")
rng=np.random.default_rng(20260717)
NPERM=5000

X=pd.read_csv(ROOT/"analysis/features.csv").set_index("subject")
Ycont=pd.read_csv(ROOT/"analysis/targets.csv").set_index("subject")
Ybin =pd.read_csv(ROOT/"analysis/target_labels.csv").set_index("subject")
Ymeta=pd.read_csv(ROOT/"analysis/target_labels_meta.csv")
assert list(X.index)==list(Ycont.index)==list(Ybin.index)
FEATS=list(X.columns); n=len(X)

# TASK-8 决定5:退化列(声明切 k 组、实际某组 0 人)由标签引擎照常写进 target_labels.csv
# 并在 meta 里标 degenerate=true;下游必须按该字段主动过滤,否则常数列进模型会重演
# ISSUE-101(sklearn 报 ConstantInputWarning、相关系数出 NaN)。
DEGEN=set(Ymeta.loc[Ymeta["degenerate"]==True,"label_name"])

# 只取“干净二分”标签(qbin + 论文1 口径的 T>=55);多分类留给 B 轨
# snap_total__wang2025T55 旧名 snap_total__normT55,TASK-8 决定2 改名:那个 T 分的
# mean/sd 取自这 24 个孩子自己、不是人群常模,叫 "norm" 名不副实。
BIN=[c for c in Ybin.columns if c.endswith("__qbin")]+["snap_total__wang2025T55"]
BIN=[c for c in BIN if c not in DEGEN]

def spearman(xr,yr):                       # 已是秩;Pearson on ranks
    xr=xr-xr.mean(); yr=yr-yr.mean()
    d=np.sqrt((xr**2).sum()*(yr**2).sum())
    return float((xr*yr).sum()/d) if d>0 else 0.0

def loo_simple_lr(x,y):
    """单变量OLS的留一:闭式。返回 R²_cv, RMSE_cv, MAE_cv。基线=留一预测均值。"""
    x=x.astype(float); y=y.astype(float)
    xm=x.mean(); Sxx=((x-xm)**2).sum()
    if Sxx<=0: return np.nan,np.nan,np.nan
    b=((x-xm)*(y-y.mean())).sum()/Sxx; a=y.mean()-b*xm
    e=y-(a+b*x); h=1.0/n+(x-xm)**2/Sxx     # 杠杆
    loo=e/(1.0-h)                          # 留一残差(PRESS)
    ss=(loo**2).sum()
    # 基线:留一均值预测 = (Σy - y_i)/(n-1);其留一残差 = (y_i-ȳ)*n/(n-1)
    base=(y-y.mean())*n/(n-1); ss0=(base**2).sum()
    r2=1-ss/ss0 if ss0>0 else np.nan
    return float(r2), float(np.sqrt(ss/n)), float(np.abs(loo).mean())

# ---------- 连续目标 ----------
rows=[]
Xrank={f:rankdata(X[f].to_numpy()) for f in FEATS}
for tcol in Ycont.columns:
    y=Ycont[tcol].to_numpy(float); yr=rankdata(y)
    # 置换零分布(打乱 yr,与特征无关)——收集 |ρ| 分布
    null=np.empty(NPERM)
    for k in range(NPERM):
        p=rng.permutation(yr); null[k]=abs(spearman(rankdata(np.arange(n)),p))
    # 注:用固定秩1..n vs 打乱秩,等价于任意无并列特征的零分布
    null.sort()
    for f in FEATS:
        rho=spearman(Xrank[f],yr)
        pval=(np.searchsorted(null,abs(rho),side="right"))
        pval=1-pval/NPERM; pval=max(pval,1.0/NPERM)
        r2,rmse,mae=loo_simple_lr(X[f].to_numpy(),y)
        rows.append(dict(target=tcol,type="cont",feature=f,rho=rho,perm_p=pval,
                         loo_r2cv=r2,loo_rmse=rmse,loo_mae=mae))

# ---------- 二分目标 ----------
def auc(x,lab):
    r=rankdata(x); n1=lab.sum(); n0=len(lab)-n1
    if n1==0 or n0==0: return np.nan
    return float((r[lab==1].sum()-n1*(n1+1)/2)/(n1*n0))

for tcol in BIN:
    lab=Ybin[tcol].to_numpy(int)
    n1=lab.sum();
    if n1==0 or n1==n: continue
    null=np.empty(NPERM)
    base=np.arange(n)
    for k in range(NPERM):
        p=rng.permutation(lab); null[k]=abs(auc(base,p)-0.5)
    null.sort()
    for f in FEATS:
        a=auc(X[f].to_numpy(),lab)
        pval=1-np.searchsorted(null,abs(a-0.5),side="right")/NPERM; pval=max(pval,1.0/NPERM)
        rows.append(dict(target=tcol,type="bin",feature=f,rho=a,perm_p=pval,
                         loo_r2cv=np.nan,loo_rmse=np.nan,loo_mae=np.nan))

R=pd.DataFrame(rows)
R.to_csv(ROOT/"analysis/A_univariate.csv",index=False)

# ---- BH-FDR(每目标族内)----
def bh(p):
    p=np.asarray(p); m=len(p); o=np.argsort(p); q=np.empty(m)
    prev=1.0
    for rank,idx in enumerate(o[::-1]):
        i=m-rank; val=min(prev,p[idx]*m/i); prev=val; q[idx]=val
    return q
R["q_fdr"]=np.nan
for t,g in R.groupby("target"):
    R.loc[g.index,"q_fdr"]=bh(g["perm_p"].values)
R.to_csv(ROOT/"analysis/A_univariate.csv",index=False)

# ================= 汇报 =================
pd.set_option("display.width",200)
print(f"A轨完成:{len(FEATS)} 特征 × ({Ycont.shape[1]} 连续 + {len(BIN)} 二分) 目标  → analysis/A_univariate.csv  ({len(R)} 行)")
print("置换次数:",NPERM,"  留一 n:",n)

print("\n========== 连续目标:各目标 top3(按 |ρ|),并给出留一 R²_cv 和 FDR-q ==========")
cont=R[R.type=="cont"].copy(); cont["abs_rho"]=cont.rho.abs()
for t in Ycont.columns:
    g=cont[cont.target==t].sort_values("abs_rho",ascending=False).head(3)
    print(f"\n--- {t} ---")
    print(g[["feature","rho","perm_p","q_fdr","loo_r2cv","loo_rmse"]].to_string(index=False,
          formatters={"rho":"{:+.3f}".format,"perm_p":"{:.4f}".format,"q_fdr":"{:.3f}".format,
                      "loo_r2cv":"{:+.3f}".format,"loo_rmse":"{:.2f}".format}))

print("\n========== 关键:留一 R²_cv > 0 的特征-目标数(真能泛化的) ==========")
pos=cont[cont.loo_r2cv>0]
print(f"  R²_cv>0: {len(pos)} / {len(cont)} 个组合")
if len(pos):
    print(pos.sort_values("loo_r2cv",ascending=False).head(10)[
        ["target","feature","rho","perm_p","q_fdr","loo_r2cv"]].to_string(index=False,
        formatters={"rho":"{:+.3f}".format,"perm_p":"{:.4f}".format,"q_fdr":"{:.3f}".format,"loo_r2cv":"{:+.3f}".format}))

print("\n========== FDR q<0.05 的组合(校正后仍显著) ==========")
sig=R[R.q_fdr<0.05].sort_values("q_fdr")
print(f"  连续+二分共 {len(sig)} 个 (总组合 {len(R)})")
if len(sig): print(sig[["target","type","feature","rho","perm_p","q_fdr","loo_r2cv"]].head(20).to_string(index=False))

print("\n========== 负对照 mag_median(总运动量)对各连续目标 ==========")
nc=cont[cont.feature=="mag_median"].sort_values("abs_rho",ascending=False)
print(nc[["target","rho","perm_p","q_fdr","loo_r2cv"]].to_string(index=False,
      formatters={"rho":"{:+.3f}".format,"perm_p":"{:.4f}".format,"q_fdr":"{:.3f}".format,"loo_r2cv":"{:+.3f}".format}))

print("\n========== 二分目标:各目标 top3(按 |AUC-0.5|) ==========")
b=R[R.type=="bin"].copy(); b["absa"]=(b.rho-0.5).abs()
for t in BIN:
    g=b[b.target==t].sort_values("absa",ascending=False).head(3)
    print(f"\n--- {t} (AUC) ---")
    print(g[["feature","rho","perm_p","q_fdr"]].to_string(index=False,
          formatters={"rho":"{:.3f}".format,"perm_p":"{:.4f}".format,"q_fdr":"{:.3f}".format}))
