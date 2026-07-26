# -*- coding: utf-8 -*-
# 阶段3-B轨:多变量模型(logistic/SVM/RF)。留一CV,fold内做一切(防泄漏)。
#   管线 = StandardScaler + SelectKBest(F值 top-k) + 模型,只在训练折 fit。
#   留一收集 24 预测后再算指标。基线:哑(均值/多数类)+ 负对照(仅 uaMag_median)。
#   两阶段:先全量出指标(快,折并行);再只对超过哑基线的组合跑置换(NPERM,并行)。
# 输出 analysis/B_multivariate.csv。
#
# =============================================================================
# 【运动总量怎么被控制的:两条轨分工不同,且 B 轨内部本身不对称——必读】
# =============================================================================
# 本项目立论是"结构而非总量",以 uaMag_median(去重力动作强度中位数=运动总量)作负对照。
# 两条轨用各自【结构上恰当】的方式控制它:
#   · A 轨(44_univariate_screen.py)用【偏相关】——逐特征扣掉总量后重算相关。
#   · B 轨(本脚本)的【回归】那半用【负对照模型】——完整模型 vs 仅用总量的模型,
#     即 skill(完整) 与 nc_skill(只用 uaMag_median) 两列,并显式输出二者之差 skill_over_nc。
# B 轨【不做偏相关】(2026-07-26 用户裁决):本脚本每行是「目标 × 模型 × k」,没有逐特征的
#   相关,偏相关在这个行结构里没有对应量。
#
# 【须随交付一起声明的不对称】(2026-07-26 用户裁决:分类那半【不补】负对照,改为如实声明):
#   「B 轨回归有负对照(nc_skill);B 轨分类无负对照,故 R10 所述的运动总量泄漏在分类结果上
#     未被控制,须在交付局限中声明。」
#   (R10 = working/backlog.md §9 的局限条目:路径B的 45 列时间结构特征部分编码运动总量。)
#
# =============================================================================
# 【TASK-113:B 轨的多重比较校正(FDR)与置换次数】
# =============================================================================
#   · 家族口径 = B 轨自身全部 198 个「目标 × 模型 × k」组合为【一族】(分轨校正,不与 A 轨合并)。
#   · 那 174 个没有 p 值的组合按 p=1 计入分母(即 m=198,不是 m=24),【不】给它们补跑置换。
#     为什么:B 轨是两阶段设计——先给全部 198 个组合算指标,再【只对赢过哑基线的】跑置换
#     (回归 skill>0、分类 bacc>0.5),实测只有 24 个有 p 值。若只对那 24 个做 FDR(m=24),
#     分母就漏掉了"我们其实看了 198 个、只正式检验了 24 个"这个【数据依赖的挑选】带来的多重性。
#     p=1 是【保守近似、不是精确值】:那 174 个是"没赢过哑基线",在 n=24 下没有信号的模型
#     留一成绩本来就常为负,其中有些若真跑置换 p 未必接近 1。记为 1 会让校正比真实情况更严
#     ——只会漏掉真发现、不会制造假发现。
#   · NPERM 由 500 提到 5000:p 值公式是 (hits+1)/(NPERM+1),故 NPERM 决定 p 的下限。
#     配上 m=198:NPERM=500 时 p 下限 0.002、排名第 1 的 q=0.395,需 8 个组合并列打到下限
#     才可能有 1 个过 q<0.05——即最强的结果【单靠自己永远过不了 FDR】;
#     NPERM=5000 时 p 下限 0.0002、排名第 1 的 q=0.040,单个即可通过。
#     证据快照:analysis/probe_outputs/fdr_permutation_floor.md(产出脚本 53_stat_budget_probes.py
#     探针3;该探针从本脚本正则解析 NPERM、不硬编,改完重跑即自动反映新值)。
#
# =============================================================================
# 【TASK-105:BMI 作为探索性协变量】
# =============================================================================
#   2026-07-26 用户裁决＝方案 b:把 BMI(体质指数)作为一个【额外的输入列】塞进多变量模型。
#   缺失处理裁决＝只在涉及 BMI 的计算上降到 n=23(24 人里 Y55 一人缺 BMI,身高体重一并缺;
#   其余分析仍用 24 人)。实测可得性见 analysis/probe_outputs/bmi_availability.md。
#   本脚本据此跑三个 variant(见输出表的 variant 列),详见下方 BMI 一节的注释。
import numpy as np, pandas as pd, pathlib, warnings, sys, os
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"]="ignore"          # 让 joblib 子进程也静默
np.seterr(all="ignore")
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_regression, f_classif, VarianceThreshold
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.svm import SVR, SVC
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import cross_val_predict, LeaveOneOut
from sklearn.metrics import f1_score, accuracy_score, balanced_accuracy_score
from joblib import Parallel, delayed
from scipy.stats import spearmanr
warnings.filterwarnings("ignore")
def say(*a): print(*a); sys.stdout.flush()
# ROOT 定位(2026-07-26 改,原为写死的主检出绝对路径 "/Users/shiyu/Projects/adhd-segmentation"):
#   默认按本脚本自身位置往上一级推算仓库根,故在任何 checkout/worktree 里跑都写回它自己的
#   目录,不会把 B_multivariate.csv 泄漏进别的 checkout。该泄漏此前已实际发生过
#   (TASK-102、TASK-9),且【不报错】——是静默出错,见 ENGINEERING_NOTES.md 第 14 节。
#   例外:analysis/features.csv 未入版本控制、只存在于主检出;在 worktree 里跑请设
#   ADHD_ROOT 指过去。同款写法先例:analysis/40_targets.py:15、53_stat_budget_probes.py:65。
HERE=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path(os.environ.get("ADHD_ROOT", HERE.parent)).resolve()
assert (ROOT/"analysis/features.csv").is_file(), (
    f"找不到 {ROOT}/analysis/features.csv —— 该文件未入版本控制,只存在于跑过 "
    f"42_features_full.py 的检出里;在 worktree 里跑请设 ADHD_ROOT 指过去。")
rng=np.random.default_rng(20260718)
NPERM=5000                      # TASK-113:由 500 提到 5000。理由见文件头部注释。
loo=LeaveOneOut()

X=pd.read_csv(ROOT/"analysis/features.csv").set_index("subject")
Yc=pd.read_csv(ROOT/"analysis/targets.csv").set_index("subject")
Yl=pd.read_csv(ROOT/"analysis/target_labels.csv").set_index("subject")
Ylm=pd.read_csv(ROOT/"analysis/target_labels_meta.csv")
Xv=X.to_numpy(float); n=len(X); KS=[5,10]
mag=X[["uaMag_median"]].to_numpy(float)

# 先方差过滤(去折内常数特征)→ 选 top-k(F检验,尺度无关)→ 只标准化被选列 → 模型。防 std=0 除零。
def reg_pipe(m,k): return Pipeline([("vt",VarianceThreshold(0.0)),("sel",SelectKBest(f_regression,k=k)),
                                    ("sc",StandardScaler()),("m",m)])
def clf_pipe(m,k): return Pipeline([("vt",VarianceThreshold(0.0)),("sel",SelectKBest(f_classif,k=k)),
                                    ("sc",StandardScaler()),("m",m)])
REG={"ridge":lambda:Ridge(alpha=10.0),"svr":lambda:SVR(kernel="rbf",C=1.0),
     "rf":lambda:RandomForestRegressor(n_estimators=200,max_features="sqrt",min_samples_leaf=2,random_state=0,n_jobs=1)}
CLF={"logit":lambda:LogisticRegression(penalty="l2",C=1.0,max_iter=2000),
     "svm":lambda:SVC(kernel="linear",C=1.0),
     "rf":lambda:RandomForestClassifier(n_estimators=200,max_features="sqrt",min_samples_leaf=2,random_state=0,n_jobs=1)}

def reg_skill(y,pred):
    base=np.sqrt(np.mean((y-y.mean())**2)); return 1-np.sqrt(np.mean((y-pred)**2))/base
def cvp(pipe,data,y): return cross_val_predict(pipe,data,y,cv=loo,n_jobs=-1)

CONT=list(Yc.columns)
# TASK-8 决定5:退化列(声明切 k 组、实际某组 0 人)在 meta 里标 degenerate=true,
# 下游必须过滤掉,否则常数列进模型会重演 ISSUE-101(ConstantInputWarning / NaN 相关)。
DEGEN=set(Ylm.loc[Ylm["degenerate"]==True,"label_name"])
# ISSUE-116/TASK-109:原先这里还硬编了一个论文1 口径的 T>=55 标签
# (snap_total__wang2025T55),已连同其上游列 snap_total 一并删除,故不再拼接。
BIN=[c for c in Yl.columns if c.endswith("__qbin")]
BIN=[c for c in BIN if c not in DEGEN]
MULTI=[f"{b}__{s}" for b in ["snap_inatt","snap_hyper","snap_odd","snap_adhd_total","sdq_hyper","sdq_totdiff"]
       for s in ["qter","qquar"] if Yl[f"{b}__{s}"].nunique()==(3 if s=="qter" else 4)]
MULTI=[c for c in MULTI if c not in DEGEN]

# =============================================================================
# TASK-105:BMI 作为额外输入列(variant 三个臂)
# =============================================================================
# 【为什么是三个臂,不是两个】:Y55 缺 BMI,加 BMI 的那一臂只能用 23 人。若只跑
#   「24 人不含 BMI」与「23 人含 BMI」两臂,两者之间【同时】变了两件事(少一个人、
#   多一列),任何差异都无法归因。故必须有第三臂「23 人不含 BMI」做匹配对照:
#     main       n=24  351 列          <- 正式结果,唯一进 FDR 家族的那一臂
#     nobmi_n23  n=23  351 列          <- 匹配对照,只为让下一行可判读
#     bmi_n23    n=23  352 列(+bmi)   <- 探索臂
#   判读:bmi_n23 与 nobmi_n23 的差 = BMI 带来的;nobmi_n23 与 main 的差 = 少了 Y55 带来的。
# 【这两个 n=23 臂不进 FDR 家族、不跑置换】:ISSUE-121 / TASK-113 把 B 轨的家族口径
#   写死为「B 轨自身全部 198 个组合为一族」,m=198。把探索臂并进去会把 m 变成 594、
#   改变所有 q 值,那不是已裁定的口径。故它们的 perm_p / q_fdr 一律留空,属探索层。
# 【一个必须一起报的量 bmi_sel_frac】:管线是 SelectKBest 只选 top-k(k=5 或 10)
#   /352 列,BMI 未必被选中。若不报"BMI 在多少比例的留一折里真被选进模型",
#   「加了 BMI 没差别」这个观察就【无法判读】——分不清是 BMI 不起作用,还是它压根没进模型。
# 【DATA_ROOT 与 ROOT 为什么要分开】:本脚本的【输出】必须落在自己的 checkout 里(ROOT),
#   但 BMI 的来源 data/(2.7GB 原始下载,按设计不入版本控制)【只存在于主检出】——
#   worktree 不复制未跟踪的大文件(ENGINEERING_NOTES.md §2 实测)。若沿用单个 ADHD_ROOT
#   把两者一起指向主检出,输出就又泄漏回主检出(正是 §14 记载的那个根因)。故拆成两个:
#     ADHD_ROOT       -> 读写分析产物的仓库根(默认＝脚本自己的仓库)
#     ADHD_DATA_ROOT  -> 只读原始 data/ 的仓库根(默认＝ADHD_ROOT,主检出上二者相同)
#   在 worktree 里跑:ADHD_DATA_ROOT=/Users/shiyu/Projects/adhd-segmentation .venv/bin/python analysis/45_multivariate_cv.py
DATA_ROOT=pathlib.Path(os.environ.get("ADHD_DATA_ROOT", ROOT)).resolve()
CLIN=DATA_ROOT/"data/Demographic and mental health data.csv"
clin=pd.read_csv(CLIN,encoding="utf-8-sig",dtype=str) if CLIN.is_file() else None
if clin is not None:
    clin.columns=[c.strip() for c in clin.columns]
    bmi_s=pd.to_numeric(clin.set_index("ID")["BMI"],errors="coerce").reindex(X.index)
else:
    bmi_s=pd.Series(np.nan,index=X.index)
    say(f"!! 找不到 {CLIN} —— BMI 臂(TASK-105)将被跳过;"
        f"设 ADHD_DATA_ROOT 指向有 data/ 的检出可启用")
HAS_BMI=bmi_s.notna().to_numpy()
say(f"\n[TASK-105] BMI 可得性:{int(HAS_BMI.sum())}/{n} 人有 BMI"
    f"{'' if HAS_BMI.all() else ';缺失者 '+str(sorted(X.index[~HAS_BMI].tolist()))}")

Xv_b23=np.hstack([Xv[HAS_BMI],bmi_s.to_numpy(float)[HAS_BMI,None]])   # 23 × 352,BMI 在最后一列
Xv_n23=Xv[HAS_BMI]                                                    # 23 × 351
ARMS=[("main",Xv,np.ones(n,bool))]
if HAS_BMI.sum()>=10 and not HAS_BMI.all():
    ARMS += [("nobmi_n23",Xv_n23,HAS_BMI),("bmi_n23",Xv_b23,HAS_BMI)]
elif HAS_BMI.all():
    ARMS += [("bmi_n23",np.hstack([Xv,bmi_s.to_numpy(float)[:,None]]),np.ones(n,bool))]

def bmi_sel_frac(data,y,k,score_func):
    """BMI(最后一列)在多少【比例的留一折】里被 SelectKBest 选进 top-k。
    管线顺序是 VarianceThreshold -> SelectKBest,故要把选中位置映射回原始列号。"""
    idx=data.shape[1]-1; hit=0
    for tr,_ in loo.split(data):
        vt=VarianceThreshold(0.0).fit(data[tr]); keep=np.flatnonzero(vt.get_support())
        Xt=vt.transform(data[tr])
        sel=SelectKBest(score_func,k=min(k,Xt.shape[1])).fit(Xt,y[tr])
        hit+=int(idx in keep[sel.get_support()])
    return hit/data.shape[0]

rows=[]
# ---------- 回归 ----------
# 【skill_over_nc 这一列是什么、为什么这个减法有意义】(TASK-106,供 TASK-107 的读者判读):
#   reg_skill(y,pred) = 1 − RMSE(预测) / RMSE(永远猜平均值)          <- 见 reg_skill 定义
#   skill 与 nc_skill 用的是【同一个分母】(同一个 base),故
#     skill − nc_skill = (只用总量的误差 − 完整模型的误差) ÷ 猜平均值的误差
#   即「完整模型比【只知道运动总量】好出多少,以【什么都不知道】为尺度衡量」。
# 【判读规则】:
#     明显 > 0 ⇒ 结构特征带来了总量之外的信息
#     ≈ 0     ⇒ 完整模型那点成绩只用运动总量就能拿到(即 backlog §9 的 R10 担心的情形成真)
#     < 0     ⇒ 加了那些特征反而更差(n=24 下常见,通常是过拟合)
# 【边界 —— 防止过度解读】:它仍是【基线对比】而非【模型内分解】。它回答"完整模型是否
#   胜过总量单独",【不】回答"完整模型这点成绩里有多少来自总量"。后者只有 A 轨的偏相关
#   (44_univariate_screen.py 的 rho_partial_uamag 列)能逐列答。
# 这一列的价值是把「本来就存在、但要读者跨列心算」的判断变成可直接排序筛选的数——
#   198 行表格里没人会逐行做减法。
def run_reg(arm,data,m):
    say(f"=== [{arm}] 回归(%d 连续 × 3 模型 × k{{5,10}}) 主指标  n=%d 列=%d ==="
        %(len(CONT),data.shape[0],data.shape[1]))
    magA=mag[m]
    for t in CONT:
        y=Yc[t].to_numpy(float)[m]
        ncsk=reg_skill(y,cvp(Pipeline([("sc",StandardScaler()),("m",Ridge(alpha=10.0))]),magA,y))
        for mn,mk in REG.items():
            for k in KS:
                pred=cvp(reg_pipe(mk(),k),data,y)
                rmse=float(np.sqrt(np.mean((y-pred)**2))); mae=float(np.mean(np.abs(y-pred)))
                rho=float(spearmanr(y,pred).correlation) if np.std(pred)>0 else 0.0
                sk=reg_skill(y,pred)
                rows.append(dict(variant=arm,track="reg",target=t,model=mn,k=k,n=len(y),
                                 rmse=rmse,mae=mae,rho=rho,skill=sk,nc_skill=ncsk,
                                 skill_over_nc=sk-ncsk,perm_p=np.nan,
                                 bmi_sel_frac=(bmi_sel_frac(data,y,k,f_regression)
                                               if arm=="bmi_n23" else np.nan)))
        say(f"  {t:12} 负对照(uaMag_median) skill={ncsk:+.3f}")

# ---------- 分类 ----------
# 【不对称,须随交付一起声明】:分类那半【没有】负对照字段(2026-07-26 用户裁决:不补)。
#   即 B 轨的运动总量对照只有回归那半有。定稿措辞见文件头部。
def run_clf(tlist,track,arm,data,m):
    say(f"=== [{arm}] {track}(%d 目标 × 3 模型 × k{{5,10}}) 主指标 ==="%len(tlist))
    for t in tlist:
        y=Yl[t].to_numpy(int)[m]
        if len(np.unique(y))<2: continue
        for mn,mk in CLF.items():
            for k in KS:
                pred=cvp(clf_pipe(mk(),k),data,y)
                rows.append(dict(variant=arm,track=track,target=t,model=mn,k=k,n=len(y),
                    f1=f1_score(y,pred,average="macro"),acc=accuracy_score(y,pred),
                    bacc=balanced_accuracy_score(y,pred),perm_p=np.nan,
                    bmi_sel_frac=(bmi_sel_frac(data,y,k,f_classif)
                                  if arm=="bmi_n23" else np.nan)))
        say(f"  {t} 完成")

for arm,data,m in ARMS:
    run_reg(arm,data,m)
    run_clf(BIN,"bin",arm,data,m); run_clf(MULTI,"multi",arm,data,m)

R=pd.DataFrame(rows)

# ---------- 置换:只对超过哑基线的组合 ----------
def perm_reg(target,model,k,obs):
    y=Yc[target].to_numpy(float); pipe=reg_pipe(REG[model](),k)
    def one(seed):
        yp=np.random.default_rng(seed).permutation(y); pr=cvp(pipe,Xv,yp)
        return reg_skill(yp,pr)>=obs
    hits=Parallel(n_jobs=-1)(delayed(one)(int(s)) for s in rng.integers(0,1e9,NPERM))
    return (sum(hits)+1)/(NPERM+1)
def perm_clf(target,model,k,obs):
    y=Yl[target].to_numpy(int); pipe=clf_pipe(CLF[model](),k)
    def one(seed):
        yp=np.random.default_rng(seed).permutation(y); pr=cvp(pipe,Xv,yp)
        return balanced_accuracy_score(yp,pr)>=obs
    hits=Parallel(n_jobs=-1)(delayed(one)(int(s)) for s in rng.integers(0,1e9,NPERM))
    return (sum(hits)+1)/(NPERM+1)

# 置换【只跑 main 臂】:两个 n=23 的 BMI 探索臂不进 FDR 家族、也不跑置换(见上方 TASK-105 注释)。
regw=R[(R.variant=="main")&(R.track=="reg")&(R.skill>0)]
clfw=R[(R.variant=="main")&(R.track.isin(["bin","multi"]))&(R.bacc>0.5)]
say(f"\n=== 置换阶段(仅 main 臂,NPERM={NPERM}):回归 {len(regw)} 个(skill>0)"
    f"+ 分类 {len(clfw)} 个(bacc>0.5) 待检 ===")
for i,r in regw.iterrows():
    R.loc[i,"perm_p"]=perm_reg(r.target,r.model,int(r.k),r.skill)
    say(f"  perm reg {r.target}/{r.model}/k{int(r.k)} skill={r.skill:+.3f} -> p={R.loc[i,'perm_p']:.3f}")
for i,r in clfw.iterrows():
    R.loc[i,"perm_p"]=perm_clf(r.target,r.model,int(r.k),r.bacc)
    say(f"  perm clf {r.target}/{r.model}/k{int(r.k)} bacc={r.bacc:.3f} -> p={R.loc[i,'perm_p']:.3f}")

# ---------- TASK-113:BH-FDR(B 轨自身全部 198 个组合为一族) ----------
# bh() 逐字复制自 44_univariate_screen.py 的同名函数,以保证两轨口径完全一致。
#   【为什么是复制而不是 import】:44 号脚本整个文件是顶层代码、没有 main 保护,
#   用 importlib 载入它会把整条 A 轨(置换 5000 次、实测约 5.7 小时)整个跑一遍。
#   本项目已有的 importlib 复用先例(50_/51_/52_ 载入 42_features_full.py)成立,
#   是因为 42 号有 main 保护、载入不触发计算。
#   【改动纪律】:两处必须保持一致——改任一处都要同步另一处。
def bh(p):
    p=np.asarray(p); m=len(p); o=np.argsort(p); q=np.empty(m)
    prev=1.0
    for rank,idx in enumerate(o[::-1]):
        i=m-rank; val=min(prev,p[idx]*m/i); prev=val; q[idx]=val
    return q

R["q_fdr"]=np.nan
MAIN=(R.variant=="main").to_numpy()
pv=R.loc[MAIN,"perm_p"].to_numpy(float)
n_noperm=int(np.isnan(pv).sum())
pv_filled=np.where(np.isnan(pv),1.0,pv)     # 没跑置换的按 p=1 计入分母,不补跑(TASK-113 第 2 件事)
R.loc[MAIN,"q_fdr"]=bh(pv_filled)
say(f"\n=== TASK-113 BH-FDR:家族 = main 臂全部 {int(MAIN.sum())} 个组合 ===")
say(f"  其中有置换 p 的 {int(MAIN.sum())-n_noperm} 个;无 p 的 {n_noperm} 个按 p=1 计入分母"
    f"(故 m={int(MAIN.sum())},不是 m={int(MAIN.sum())-n_noperm})")
if int(MAIN.sum())!=198:
    say(f"  !! 注意:main 臂组合数为 {int(MAIN.sum())},不是 ISSUE-121/TASK-113 写定的 198。"
        f"家族大小变了,q 值口径随之改变,须回头核对条目。")
say(f"  q<0.05 的组合数:{int((R.loc[MAIN,'q_fdr']<0.05).sum())}")
say("  提醒:p=1 是【保守近似】——那 %d 个是『没赢过哑基线』,不是『真跑了置换得 p=1』。"%n_noperm)
say("        这样只会漏掉真发现、不会制造假发现;两个 n=23 的 BMI 探索臂不在本家族内(q 留空)。")

R.to_csv(ROOT/"analysis/B_multivariate.csv",index=False)
pd.set_option("display.width",220)
say("\n>>> analysis/B_multivariate.csv  共 %d 行"%len(R))
say("  各臂行数:"+"  ".join(f"{v}={int((R.variant==v).sum())}" for v in R.variant.unique()))
M=R[R.variant=="main"]

say("\n===== [main] 回归:skill>0(击败哑基线) =====")
w=M[(M.track=='reg')&(M.skill>0)].sort_values("skill",ascending=False)
say(f"  {len(w)}/{len(M[M.track=='reg'])} 击败哑基线")
if len(w): say(w[["target","model","k","rmse","rho","skill","nc_skill","skill_over_nc",
                  "perm_p","q_fdr"]].to_string(index=False))
say("\n===== [main] 回归:skill_over_nc 排名(完整模型比『只知道运动总量』好出多少) =====")
say("  >0 结构特征带来了总量之外的信息;≈0 那点成绩只用总量就能拿到(R10 担心的情形);<0 更差。")
w=M[M.track=='reg'].sort_values("skill_over_nc",ascending=False).head(10)
say(w[["target","model","k","skill","nc_skill","skill_over_nc"]].to_string(index=False))
for tr,lab in [("bin","二分类"),("multi","多分类")]:
    w=M[(M.track==tr)&(M.bacc>0.5)].sort_values("bacc",ascending=False)
    say(f"\n===== [main] {lab}:balanced_acc>0.5 =====  {len(w)}/{len(M[M.track==tr])}")
    say("  (分类那半无负对照字段——B 轨的运动总量对照只有回归那半有,见文件头部声明)")
    if len(w): say(w[["target","model","k","f1","acc","bacc","perm_p","q_fdr"]].to_string(index=False))
say("\n===== [main] 置换 p<0.05 =====")
sig=M[M.perm_p<0.05].sort_values("perm_p")
say("  %d 个"%len(sig))
if len(sig): say(sig[["track","target","model","k","skill","bacc","perm_p","q_fdr"]].to_string(index=False))
say("\n===== [main] FDR q<0.05(校正后仍显著) =====")
sq=M[M.q_fdr<0.05].sort_values("q_fdr")
say("  %d 个 / 家族 %d"%(len(sq),len(M)))
if len(sq): say(sq[["track","target","model","k","perm_p","q_fdr"]].to_string(index=False))

# ---------- TASK-105:BMI 探索臂的对照 ----------
if "bmi_n23" in set(R.variant):
    say("\n===== [TASK-105] BMI 探索臂:bmi_n23 vs nobmi_n23(同 23 人,唯一差别是多了 BMI 列) =====")
    say("  这两臂【不进 FDR 家族、不跑置换】,属探索层,不下确证性结论。")
    key=["track","target","model","k"]
    a=R[R.variant=="bmi_n23"].set_index(key)
    b=R[R.variant=="nobmi_n23"].set_index(key)
    say(f"\n  BMI 被 SelectKBest 选进模型的折比例 bmi_sel_frac:"
        f" 均值 {a.bmi_sel_frac.mean():.3f}  最大 {a.bmi_sel_frac.max():.3f}"
        f"  从未被选中(=0) 的组合数 {int((a.bmi_sel_frac==0).sum())}/{len(a)}")
    say("  读法:若 bmi_sel_frac 多为 0,则『加了 BMI 没差别』说明的是 BMI 压根没进模型,")
    say("        而不是『BMI 与症状无关』——两者是不同的结论,不可混为一谈。")
    for tr,met in [("reg","skill"),("bin","bacc"),("multi","bacc")]:
        aa=a[a.index.get_level_values(0)==tr]; bb=b[b.index.get_level_values(0)==tr]
        if not len(aa): continue
        d=(aa[met]-bb[met]).dropna()
        say(f"\n  [{tr}] {met} 差值(bmi_n23 − nobmi_n23):中位 {d.median():+.4f}"
            f"  最大 {d.max():+.4f}  最小 {d.min():+.4f}  非零组合数 {int((d.abs()>1e-9).sum())}/{len(d)}")
        top=d.reindex(d.abs().sort_values(ascending=False).index).head(5)
        for idx,v in top.items():
            say(f"      {'/'.join(map(str,idx)):46} {v:+.4f}"
                f"  (bmi_sel_frac={aa.loc[idx,'bmi_sel_frac']:.2f})")
    say("\n  另一个对照(不是 BMI 的效果,是【少了 Y55 一个人】的效果):nobmi_n23 vs main")
    c=R[R.variant=="main"].set_index(key)
    d2=(b[b.index.get_level_values(0)=="reg"]["skill"]-c[c.index.get_level_values(0)=="reg"]["skill"]).dropna()
    say(f"      [reg] skill 差值中位 {d2.median():+.4f}  最大 |差| {d2.abs().max():.4f}")
    say("      若这一行的量级与上面 BMI 那一行相当或更大,则 BMI 那点差异无法与『少一个人』区分开。")
