# -*- coding: utf-8 -*-
# 阶段3-A轨:单变量筛查。每个特征单独 × 每个目标,诚实评估。一次只用1个特征 → 无多变量过拟合。
#   连续目标:Spearman ρ(效应量) + 置换 p + 留一 R²_cv(闭式PRESS,泛化) + 留一 RMSE/MAE。
#   二分目标:AUC(=Mann-Whitney,秩基,免拟合) + 置换 p。
#   置换零分布对固定目标与特征无关(只依赖 n / 组大小)→ 每目标算一次,275特征共用。
# 输出 analysis/A_univariate.csv(长表),并打印各目标 top 命中 + 负对照 uaMag_median。
#
# 【TASK-106 新增】路径B的 45 列额外输出一列「控制 uaMag_median 后的偏相关」,
#   列名 rho_partial_uamag;是什么、怎么判读见下方 PATHB 一节的注释。
#
# =============================================================================
# 【TASK-120:rho 列拆成 rho + auc,2026-07-30 用户裁决】
# =============================================================================
# 【改动前的样子】输出表只有一列 rho,它【装两种不同的量】:
#     type=cont 的行装 Spearman ρ    —— 无效应基准 = 0    ,范围 [-1, +1]
#     type=bin  的行装 AUC           —— 无效应基准 = 0.5  ,范围 [ 0,  1]
#   这一点原先只写在代码注释和 analysis/MODEL_MENU.md 的字段表里,【表本身不体现】。
# 【为什么必须改,有实证】2026-07-29 管理窗口查「目前最好的结果是什么」,按 |rho| 排序取
#   前 5 条,【排出来的是错的】:二分行 AUC=0.12(即 |AUC-0.5|=0.38,很强的【反向】关系)
#   被排到末尾,而 AUC=0.55(几乎无效应)排在它前面。任何人用 Excel 打开这张表按 rho 排序
#   都会重演这个错误。【文档保护不了文件】——这是选「改列名」而不是「加文档警告」的理由。
# 【改动后】两列各管一种量,另一种留空(NaN):
#     rho 只在 type=cont 有值;auc 只在 type=bin 有值。
#   于是「按 rho 排序」这个动作在二分行上【拿不到数】,错误无法再发生。
# 【不改变任何数值】:ρ、AUC、perm_p、q_fdr 的算法一行未动,rng 种子仍是 20260717。
#   改完重跑,除列结构外应与改动前【逐格相同】——本次已逐格比对确认,结果见
#   analysis/probe_outputs/task120_column_split.md。
# 【一处仍未处理,知情保留】rho_partial_uamag 那一列【有同样的双含义问题】:
#   cont 行装偏相关(基准 0)、bin 行装残差化后的 AUC(基准 0.5)。本次【未拆】,
#   因 TASK-120 的登记范围只写了 rho 列。去向未定,见 working/task.md 的 TASK-120 条目。
#   〔【已处理】2026-07-30 同日:用户看过实测排错证据后裁决"照样拆",见下方 TASK-121 注释块。〕
#
# =============================================================================
# 【TASK-121:rho_partial_uamag 也拆成两列,2026-07-30 用户裁决】
# =============================================================================
# 【和 TASK-120 是同一个毛病的第二处】改动前 rho_partial_uamag 一列装两种量:
#     type=cont 的行装【控制 uaMag_median 后的偏相关】 —— 无效应基准 = 0  ,实测范围 -0.530 ~ +0.451
#     type=bin  的行装【残差化后的 AUC】               —— 无效应基准 = 0.5,实测范围  0.185 ~  0.861
# 【实测排错有多严重】把这 900 个有值的格子按 |值| 从大到小排(最自然的动作):
#     - 前 50 名【全部 50 个都是 bin 行】,450 个 cont 行一个都进不去
#       —— 因为 bin 的数绕着 0.5 转、|值| 天然 0.5 上下,cont 的数绕着 0 转、|值| 最大只 0.53。
#          排序变成了"先按行的类型分堆",而不是按关系强弱。
#     - 最强的 cont 行 actfrac_p60 x snap_hyper(值 -0.530):正确第 1 名 -> 按|值|排第 168 名
#     - actfrac_p90 x snap_odd__qbin(值 0.185,即 |0.185-0.5|=0.315,bin 行里第二强的反向关系):
#       正确第 66 名 -> 按|值|排【第 616 名】,掉 550 位
#     - 反过来 actshort_p10 x sdq_cond__qbin(值 0.719):按|值|排第 8 名 -> 正确其实第 161 名
# 【改动后】rho_partial_uamag 只在 cont 行有值,新列 auc_partial_uamag 只在 bin 行有值。
# 【不改变任何数值】算法一行未动,rng 种子仍 20260717。逐格比对见
#   analysis/probe_outputs/task121_partial_column_split.md。
# 【顺带订正一处假引用】原第 273 行那句「二分目标那半报的是『残差化后的 AUC』,见下方单独一节」
#   ——【那一节根本不存在】。全脚本 6 个小节标题里没有它,故这一列的 450 个 bin 行
#   【从未被打印过任何一次】,只写进 csv。该句已改成实话;要不要补那一节,去向未定
#   (见 working/task.md 的 TASK-121 条目)。
import os, numpy as np, pandas as pd, pathlib
from scipy.stats import rankdata
# ROOT 定位(2026-07-26 改,原为写死的主检出绝对路径 "/Users/shiyu/Projects/adhd-segmentation"):
#   默认按本脚本自身位置往上一级推算仓库根,故在任何 checkout/worktree 里跑都写回它自己的
#   目录,不会把产物泄漏进别的 checkout。该泄漏此前已实际发生过(TASK-102、TASK-9),
#   且【不报错】——是静默出错,见 ENGINEERING_NOTES.md 第 14 节。
#   例外:analysis/features.csv 未入版本控制、只存在于主检出;在 worktree 里跑请用环境变量
#   指过去——  ADHD_ROOT=/Users/shiyu/Projects/adhd-segmentation .venv/bin/python analysis/44_univariate_screen.py
#   〔【上面这个"例外"已不成立】,2026-07-30 TASK-120 改动时实测订正:analysis/features.csv
#     【已于 2026-07-28 入版本控制】(TASK-5,commit b135aae),故它在每个 worktree 里都在位,
#     跑本脚本【不再需要设 ADHD_ROOT】。本次在 worktree task-120-rho-auc 里未设该变量直接跑通,
#     且桌上 features.csv 的 md5 与主检出一致(6d36ee888f6d73647609b91eb85025e5)。
#     原文保留,因为 ADHD_ROOT 这个机制本身仍然存在、仍可用于"故意写回别处"的场合。〕
#   同款写法的先例:analysis/40_targets.py:15、50_temporal_design_probes.py:64、52_scan_compute_cost.py:47。
HERE=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path(os.environ.get("ADHD_ROOT", HERE.parent)).resolve()
assert (ROOT/"analysis/features.csv").is_file(), (
    f"找不到 {ROOT}/analysis/features.csv —— 该文件【已入版本控制】(2026-07-28,commit b135aae),"
    f"正常检出里都该在位;若这里报错,说明本次运行的 ROOT 指错了地方(现为 {ROOT}),"
    f"或该文件被本地删除。〔原文写的是'该文件未入版本控制、只存在于跑过 42_features_full.py "
    f"的检出里',2026-07-30 TASK-120 订正——入库后那句话不再成立。〕")
rng=np.random.default_rng(20260717)
# =============================================================================
# 【NPERM 由 5000 提到 100000,2026-07-29 用户裁决】
# =============================================================================
# 理由【不是】调参凑显著,是【测量精度不够】。置换 p 的下限 = 1/NPERM:
#   NPERM=5000  -> 下限 2e-4。而 A 轨每族 m = 特征数 = 608,BH-FDR 下单个最强命中的
#                  q 最好只能到 2e-4 x 608 = 0.1216 —— 【结构上永远进不了 0.05】,
#                  除非至少 3 个特征同时打到下限(0.05 / 2e-4 / 608 -> 需 rank >= 3)。
#   NPERM=100000-> 下限 1e-5,q 天花板 1e-5 x 608 = 0.0061,单个命中即可通过。
# 这与 TASK-113 当初把 B 轨 NPERM 由 500 提到 5000 是【同一个理由】(那时 q 天花板 0.383,
#   连门都摸不着);只是当时没意识到 5000 对 A 轨的 m=608 仍然不够。
# 【本改动不改变任何统计量、模型或特征选择】,只是把同一件事量得更准。
# 客观后果:A 轨全跑一遍由 5.0 秒 -> 52 秒(实测);FDR 存活由 0 条 -> 3 条。
#   改动前后的对照快照:analysis/probe_outputs/task106_run.md
#   改动前的产物已归档:archive/A_univariate__608feat_NPERM5000.csv
# 【一处仍须知情】:通过的 3 条,perm_p 仍卡在新下限 1e-5,即 10 万次置换仍无一次超过它们
#   —— 真实 p 可能更小,现在的尺子依然不够细。
# 【连带】53_stat_budget_probes.py 用正则从本文件解析 NPERM(不硬编),改完重跑即自动反映。
NPERM=100000

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
        # TASK-120:rho 只在连续行有值,auc 留空 —— 两种量不再挤在同一列(见头部注释)
        # TASK-121:同理,rho_partial_uamag 只在连续行、auc_partial_uamag 留空
        rows.append(dict(target=tcol,type="cont",feature=f,rho=rho,auc=np.nan,perm_p=pval,
                         loo_r2cv=r2,loo_rmse=rmse,loo_mae=mae,
                         rho_partial_uamag=pr,auc_partial_uamag=np.nan))

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
        # 二分目标没有"偏相关"这个量(本行的效应量是 AUC、不是 ρ),故改报
        # 【残差化后的 AUC】:先把特征扣掉运动总量、再用残差算 AUC。它与同行的 auc 列
        # 同量纲、可直接比较"掉了多少"(2026-07-26 用户裁决:连续+二分都做,二分走这条)。
        # 〔原注释写「本行 rho 列装的是 AUC」,TASK-120 拆列后 AUC 已搬进独立的 auc 列,
        #   rho 列在二分行为空;引用改为 auc 列。2026-07-30〕
        pr=auc(XresidB[f],lab) if f in PATHB else np.nan
        # TASK-120:auc 只在二分行有值,rho 留空
        # TASK-121:这个残差化 AUC 现在写进【auc_partial_uamag】列,不再挤进 rho_partial_uamag
        rows.append(dict(target=tcol,type="bin",feature=f,rho=np.nan,auc=a,perm_p=pval,
                         loo_r2cv=np.nan,loo_rmse=np.nan,loo_mae=np.nan,
                         rho_partial_uamag=np.nan,auc_partial_uamag=pr))

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
# TASK-120:本节【混着连续行和二分行】,故 rho 与 auc 两列都要打——
#   连续行只有 rho 有值(无效应基准 0)、二分行只有 auc 有值(无效应基准 0.5)。
#   拆列前这里只打一列 rho,读者看到的是【两种基准的数混在一栏】,无从分辨。
if len(sig): print(sig[["target","type","feature","rho","auc","perm_p","q_fdr","loo_r2cv"]].head(20).to_string(index=False))

print("\n========== 负对照 uaMag_median(总运动量)对各连续目标 ==========")
nc=cont[cont.feature=="uaMag_median"].sort_values("abs_rho",ascending=False)
print(nc[["target","rho","perm_p","q_fdr","loo_r2cv"]].to_string(index=False,
      formatters={"rho":"{:+.3f}".format,"perm_p":"{:.4f}".format,"q_fdr":"{:.3f}".format,"loo_r2cv":"{:+.3f}".format}))

print("\n========== TASK-106:路径B 45 列 扣掉运动总量后还剩多少(连续目标) ==========")
print("  判读三种情形:|偏相关| 相对 |ρ| 大幅【缩小】⇒ 原相关是运动总量假象;")
print("             【基本不变】⇒ 真结构信号;【反而变大】⇒ 抑制(suppression),")
print("             即结构信号原先被运动总量盖住,扣掉才露出来——不是假象。")
print("  注:本列无 p 值、无 q 值,是效应量,不进多重比较的账。")
print("  【二分目标那半在本脚本的 stdout 里不报】:它写在 csv 的 auc_partial_uamag 列")
print("      (TASK-121 由 rho_partial_uamag 拆出),是『残差化后的 AUC』、与该行 auc 列同量纲,")
print("      无效应基准 0.5。〔原文这里写的是『见下方单独一节』,而【那一节根本不存在】——")
print("       TASK-121 于 2026-07-30 查实并改成本句实话。要不要补上那一节,去向未定。〕")
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
b=R[R.type=="bin"].copy(); b["absa"]=(b.auc-0.5).abs()   # TASK-120:二分行的效应量在 auc 列
for t in BIN:
    g=b[b.target==t].sort_values("absa",ascending=False).head(3)
    print(f"\n--- {t} (AUC) ---")
    print(g[["feature","auc","perm_p","q_fdr"]].to_string(index=False,
          formatters={"auc":"{:.3f}".format,"perm_p":"{:.4f}".format,"q_fdr":"{:.3f}".format}))
