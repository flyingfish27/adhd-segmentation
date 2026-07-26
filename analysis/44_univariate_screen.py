# -*- coding: utf-8 -*-
# 阶段3-A轨:单变量筛查。每个特征单独 × 每个目标,诚实评估。一次只用1个特征 → 无多变量过拟合。
#   连续目标:Spearman ρ(效应量) + 置换 p + 留一 R²_cv(闭式PRESS,泛化) + 留一 RMSE/MAE。
#   二分目标:AUC(=Mann-Whitney,秩基,免拟合) + 置换 p。
#   置换零分布对固定目标与特征无关(只依赖 n / 组大小)→ 每目标算一次,275特征共用。
# 输出 analysis/A_univariate.csv(长表),并打印各目标 top 命中 + 负对照 uaMag_median。
#
# 【TASK-106 新增】路径B的 45 列额外输出一列「控制 uaMag_median 后的偏相关」,
#   列名 rho_partial_uamag;是什么、怎么判读见下方 PATHB 一节的注释。
import os, numpy as np, pandas as pd, pathlib
from scipy.stats import rankdata
# ROOT 定位(2026-07-26 改,原为写死的主检出绝对路径 "/Users/shiyu/Projects/adhd-segmentation"):
#   默认按本脚本自身位置往上一级推算仓库根,故在任何 checkout/worktree 里跑都写回它自己的
#   目录,不会把产物泄漏进别的 checkout。该泄漏此前已实际发生过(TASK-102、TASK-9),
#   且【不报错】——是静默出错,见 ENGINEERING_NOTES.md 第 14 节。
#   例外:analysis/features.csv 未入版本控制、只存在于主检出;在 worktree 里跑请用环境变量
#   指过去——  ADHD_ROOT=/Users/shiyu/Projects/adhd-segmentation .venv/bin/python analysis/44_univariate_screen.py
#   同款写法的先例:analysis/40_targets.py:15、50_temporal_design_probes.py:64、52_scan_compute_cost.py:47。
HERE=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path(os.environ.get("ADHD_ROOT", HERE.parent)).resolve()
assert (ROOT/"analysis/features.csv").is_file(), (
    f"找不到 {ROOT}/analysis/features.csv —— 该文件未入版本控制,只存在于跑过 "
    f"42_features_full.py 的检出里;在 worktree 里跑请设 ADHD_ROOT 指过去。")
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

# 只取“干净二分”标签(qbin);多分类留给 B 轨。
# ISSUE-116/TASK-109:原先这里还硬编了一个论文1 口径的 T>=55 标签
# (snap_total__wang2025T55),已连同其上游列 snap_total 一并删除,故不再拼接。
BIN=[c for c in Ybin.columns if c.endswith("__qbin")]
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

# ================= TASK-106:路径B 45 列的「控制 uaMag_median 后的偏相关」 =================
# 【为什么只对这 45 列做】(2026-07-26 用户裁决,范围不扩到全部 351 列):
#   特征脚本 42_features_full.py 把"时间结构"分两条路径算——
#     路径A(滑窗法,55 列,列名 switch_per_min_p* / act_bout_median_p* / ... / within_win_sd)
#       用【每个孩子自己的】动作强度百分位当"在动/没在动"的阈值 → amplitude-invariant,
#       实测 p50 档与 uaMag_median 的 |ρ| 仅 0.155-0.46,不存在本节要修的缺陷。
#     路径B(逐样本法,45 列,即下面 PATHB_STEMS 那 5 个词头 × 9 个百分位档)
#       用【24 人合池的一条共同阈值线】→ 整体动作幅度大的孩子自然更多时间落在线之上,
#       于是这些列的个体差异【基本就是"这孩子动多用力"(运动总量)】。实测 p50 档 actfrac
#       与负对照 uaMag_median 的秩相关 |ρ|=0.877(证据 analysis/probe_outputs/pooling_leakage.md,
#       局限登记 working/backlog.md §9 的 R10)。
#   其余 306 列(时域/频域 251 列 + 路径A 55 列)本就不涉及合池阈值,没有这个泄漏问题,
#   故不需要这道过滤。偏相关是为修 R10 那个特定缺陷而设的手段,缺陷不存在的列不用它。
#
# 【偏相关是什么】(详见 ENGINEERING_NOTES.md §17.1):扣掉运动总量 Z 的影响之后,
#   特征 X 与症状分 Y 还剩多少关系。做法 = 先用 Z 去预测 X、从 X 里减掉能被 Z 解释的那部分
#   得到残差,对 Y 同样处理,再拿两个残差求相关。
#
# 【判读规则 —— 这是这一列全部的价值所在,供 TASK-107 汇总表使用】:
#     某列扣掉总量后相关【消失】  ⇒ 该列的信号是【总量假象】,不能拿它支撑"结构"主张;
#     某列扣掉总量后相关【仍在】  ⇒ 该列是【真结构信号】。
#   交付报告须写明:路径B列的结构性结论一律以偏相关为准,未做偏相关的原始相关不得单独
#   支撑"结构"主张。
#
#   【第三种情形:偏相关反而比原相关更强】(2026-07-26 实测本表确实出现,首次登记于此)
#   task.md TASK-106 条目写的判读规则只列了"消失/仍在"两种,但偏相关在数学上【不受
#   |偏相关| ≤ |ρ| 约束】——控制变量被扣掉后相关变强是标准现象,统计学叫【抑制
#   (suppression)】:运动总量同时与特征、与症状分相关,且方向搭配使它在原始相关里
#   【盖住】了特征自己的信号;扣掉它,被盖住的信号才露出来。
#   判读:这一类【不是】总量假象,恰恰相反——它是被总量掩盖的结构信号,比"仍在"那一类
#   更强地支持"结构而非总量"。但须注意 n=24 下偏相关的抽样波动比原相关更大(多估了一个
#   回归系数、少了一个自由度),故这一类须结合样本量声明来读,不能只看数值变大就下结论。
#
# 【两轨分工】(2026-07-26 用户裁决):两条轨用各自结构上恰当的方式控制运动总量——
#   A 轨(本脚本)用【偏相关】(逐特征扣掉总量后重算相关);
#   B 轨(45_multivariate_cv.py)回归用【负对照模型】(完整模型 vs 仅用总量的模型),
#   B 轨【不做】偏相关(它每行是"目标×模型×k"、没有逐特征的相关,偏相关在那里没有对应量)。
#
# 【这一列没有 p 值、也没有 q 值】:它是效应量,不进多重比较的账。ISSUE-121 裁定的
#   A 轨家族口径(每个目标各自一族、m=特征数)只针对 perm_p / q_fdr 那一路,不受本列影响。
NC="uaMag_median"                        # 负对照 = 去重力动作强度中位数,代表"运动总量"
assert NC in X.columns, f"负对照列 {NC} 不在特征表里 —— 偏相关无从算起"
PATHB_STEMS=("actfrac","switchmin","actbout_med","actbout_cv","actshort")
PATHB=[c for c in FEATS if any(c.startswith(s+"_p") for s in PATHB_STEMS)]
print(f"[TASK-106] 路径B列(偏相关的对象): {len(PATHB)} 列"
      + ("" if len(PATHB)==45 else "  ← 注意:不是预期的 45 列,请核对 42_features_full.py 的 PCTS 与路径B列名"))
print("           列名:", ", ".join(sorted(PATHB)))
PATHB=set(PATHB)

ZR=rankdata(X[NC].to_numpy())            # 控制变量的秩(偏相关在秩上做,与 Spearman 口径一致)
def resid_on_z(vr):
    """把秩向量 vr 对 ZR 做一元线性回归,返回残差 = vr 里与运动总量无关的成分。"""
    zc=ZR-ZR.mean(); szz=(zc**2).sum()
    vc=vr-vr.mean()
    if szz<=0: return vc
    return vc-((vc*zc).sum()/szz)*zc

# ---------- 连续目标 ----------
rows=[]
Xrank={f:rankdata(X[f].to_numpy()) for f in FEATS}
XresidB={f:resid_on_z(Xrank[f]) for f in PATHB}   # 只有路径B列需要,算一次复用
for tcol in Ycont.columns:
    y=Ycont[tcol].to_numpy(float); yr=rankdata(y)
    # 置换零分布(打乱 yr,与特征无关)——收集 |ρ| 分布
    null=np.empty(NPERM)
    for k in range(NPERM):
        p=rng.permutation(yr); null[k]=abs(spearman(rankdata(np.arange(n)),p))
    # 注:用固定秩1..n vs 打乱秩,等价于任意无并列特征的零分布
    null.sort()
    yresid=resid_on_z(yr)                 # 症状分的秩里与运动总量无关的成分
    for f in FEATS:
        rho=spearman(Xrank[f],yr)
        pval=(np.searchsorted(null,abs(rho),side="right"))
        pval=1-pval/NPERM; pval=max(pval,1.0/NPERM)
        r2,rmse,mae=loo_simple_lr(X[f].to_numpy(),y)
        # 连续目标的偏相关 = 两个残差的相关,与同行 rho 同量纲、可直接比较"掉了多少"
        pr=spearman(XresidB[f],yresid) if f in PATHB else np.nan
        rows.append(dict(target=tcol,type="cont",feature=f,rho=rho,perm_p=pval,
                         loo_r2cv=r2,loo_rmse=rmse,loo_mae=mae,rho_partial_uamag=pr))

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
        # 二分目标没有"偏相关"这个量(本行 rho 列装的是 AUC、不是 ρ),故改报
        # 【残差化后的 AUC】:先把特征扣掉运动总量、再用残差算 AUC。它与同行的 rho(=AUC)
        # 同量纲、可直接比较"掉了多少"(2026-07-26 用户裁决:连续+二分都做,二分走这条)。
        pr=auc(XresidB[f],lab) if f in PATHB else np.nan
        rows.append(dict(target=tcol,type="bin",feature=f,rho=a,perm_p=pval,
                         loo_r2cv=np.nan,loo_rmse=np.nan,loo_mae=np.nan,rho_partial_uamag=pr))

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

print("\n========== 负对照 uaMag_median(总运动量)对各连续目标 ==========")
nc=cont[cont.feature=="uaMag_median"].sort_values("abs_rho",ascending=False)
print(nc[["target","rho","perm_p","q_fdr","loo_r2cv"]].to_string(index=False,
      formatters={"rho":"{:+.3f}".format,"perm_p":"{:.4f}".format,"q_fdr":"{:.3f}".format,"loo_r2cv":"{:+.3f}".format}))

print("\n========== TASK-106:路径B 45 列 扣掉运动总量后还剩多少(连续目标) ==========")
print("  判读三种情形:|偏相关| 相对 |ρ| 大幅【缩小】⇒ 原相关是运动总量假象;")
print("             【基本不变】⇒ 真结构信号;【反而变大】⇒ 抑制(suppression),")
print("             即结构信号原先被运动总量盖住,扣掉才露出来——不是假象。")
print("  注:本列无 p 值、无 q 值,是效应量,不进多重比较的账。二分目标那半报的是")
print("      『残差化后的 AUC』(与该行 rho 列的 AUC 同量纲),见下方单独一节。")
pb=cont[cont.feature.isin(PATHB)].copy()
if len(pb):
    pb["abs_partial"]=pb.rho_partial_uamag.abs()
    pb["shrink"]=pb.abs_rho-pb.abs_partial
    print(f"\n  路径B连续组合共 {len(pb)} 个({len(PATHB)} 列 × {Ycont.shape[1]} 连续目标)")
    print(f"  |ρ| 中位 {pb.abs_rho.median():.3f} -> |偏相关| 中位 {pb.abs_partial.median():.3f}"
          f"  (中位缩小 {pb.shrink.median():+.3f})")
    print(f"  |ρ|>0.3 的组合数 {int((pb.abs_rho>0.3).sum())} -> 扣掉总量后仍 >0.3 的"
          f" {int((pb.abs_partial>0.3).sum())} 个")
    print(f"  三种情形各有多少(以 |偏相关|-|ρ| 分档): 缩小>0.1 的 {int((pb.shrink>0.1).sum())} 个"
          f" / 基本不变(±0.1) 的 {int((pb.shrink.abs()<=0.1).sum())} 个"
          f" / 变大>0.1 的 {int((pb.shrink< -0.1).sum())} 个")
    print("\n  缩小最多的 10 个(最像总量假象):")
    print(pb.sort_values("shrink",ascending=False).head(10)[
        ["target","feature","rho","rho_partial_uamag"]].to_string(index=False,
        formatters={"rho":"{:+.3f}".format,"rho_partial_uamag":"{:+.3f}".format}))
    print("\n  变大最多的 10 个(抑制:结构信号原先被总量盖住):")
    print(pb.sort_values("shrink").head(10)[
        ["target","feature","rho","rho_partial_uamag"]].to_string(index=False,
        formatters={"rho":"{:+.3f}".format,"rho_partial_uamag":"{:+.3f}".format}))
    print("\n  扣掉总量后 |偏相关| 仍最大的 10 个(最像真结构信号):")
    print(pb.sort_values("abs_partial",ascending=False).head(10)[
        ["target","feature","rho","rho_partial_uamag"]].to_string(index=False,
        formatters={"rho":"{:+.3f}".format,"rho_partial_uamag":"{:+.3f}".format}))
else:
    print("  路径B列在本特征表里一个都没匹配上 —— 请核对 PATHB_STEMS 与 42_features_full.py 的列名。")

print("\n========== 二分目标:各目标 top3(按 |AUC-0.5|) ==========")
b=R[R.type=="bin"].copy(); b["absa"]=(b.rho-0.5).abs()
for t in BIN:
    g=b[b.target==t].sort_values("absa",ascending=False).head(3)
    print(f"\n--- {t} (AUC) ---")
    print(g[["feature","rho","perm_p","q_fdr"]].to_string(index=False,
          formatters={"rho":"{:.3f}".format,"perm_p":"{:.4f}".format,"q_fdr":"{:.3f}".format}))
