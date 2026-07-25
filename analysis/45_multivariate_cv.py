# -*- coding: utf-8 -*-
# 阶段3-B轨:多变量模型(logistic/SVM/RF)。留一CV,fold内做一切(防泄漏)。
#   管线 = StandardScaler + SelectKBest(F值 top-k) + 模型,只在训练折 fit。
#   留一收集 24 预测后再算指标。基线:哑(均值/多数类)+ 负对照(仅 uaMag_median)。
#   两阶段:先全量出指标(快,折并行);再只对超过哑基线的组合跑置换(n_perm=500,并行)。
# 输出 analysis/B_multivariate.csv。
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
ROOT=pathlib.Path("/Users/shiyu/Projects/adhd-segmentation")
rng=np.random.default_rng(20260718); NPERM=500
loo=LeaveOneOut()

X=pd.read_csv(ROOT/"analysis/features.csv").set_index("subject")
Yc=pd.read_csv(ROOT/"analysis/targets.csv").set_index("subject")
Yl=pd.read_csv(ROOT/"analysis/target_labels.csv").set_index("subject")
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
BIN=[c for c in Yl.columns if c.endswith("__qbin")]+["snap_total__normT55"]
MULTI=[f"{b}__{s}" for b in ["snap_inatt","snap_hyper","snap_odd","snap_total","sdq_hyper","sdq_totdiff"]
       for s in ["qter","qquar"] if Yl[f"{b}__{s}"].nunique()==(3 if s=="qter" else 4)]

rows=[]
# ---------- 回归 ----------
say("=== 回归(%d 连续 × 3 模型 × k{5,10}) 主指标 ==="%len(CONT))
for t in CONT:
    y=Yc[t].to_numpy(float)
    ncp=cvp(Pipeline([("sc",StandardScaler()),("m",Ridge(alpha=10.0))]),mag,y)
    ncsk=reg_skill(y,ncp)
    for mn,mk in REG.items():
        for k in KS:
            pred=cvp(reg_pipe(mk(),k),Xv,y)
            rmse=float(np.sqrt(np.mean((y-pred)**2))); mae=float(np.mean(np.abs(y-pred)))
            rho=float(spearmanr(y,pred).correlation) if np.std(pred)>0 else 0.0
            rows.append(dict(track="reg",target=t,model=mn,k=k,rmse=rmse,mae=mae,rho=rho,
                             skill=reg_skill(y,pred),nc_skill=ncsk,perm_p=np.nan))
    say(f"  {t:12} 负对照(uaMag_median) skill={ncsk:+.3f}")

# ---------- 分类 ----------
def run_clf(tlist,track):
    say(f"=== {track}(%d 目标 × 3 模型 × k{{5,10}}) 主指标 ==="%len(tlist))
    for t in tlist:
        y=Yl[t].to_numpy(int)
        if len(np.unique(y))<2: continue
        for mn,mk in CLF.items():
            for k in KS:
                pred=cvp(clf_pipe(mk(),k),Xv,y)
                rows.append(dict(track=track,target=t,model=mn,k=k,
                    f1=f1_score(y,pred,average="macro"),acc=accuracy_score(y,pred),
                    bacc=balanced_accuracy_score(y,pred),perm_p=np.nan))
        say(f"  {t} 完成")
run_clf(BIN,"bin"); run_clf(MULTI,"multi")

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

regw=R[(R.track=="reg")&(R.skill>0)]
clfw=R[(R.track.isin(["bin","multi"]))&(R.bacc>0.5)]
say(f"\n=== 置换阶段:回归 {len(regw)} 个(skill>0)+ 分类 {len(clfw)} 个(bacc>0.5) 待检 ===")
for i,r in regw.iterrows():
    R.loc[i,"perm_p"]=perm_reg(r.target,r.model,int(r.k),r.skill)
    say(f"  perm reg {r.target}/{r.model}/k{int(r.k)} skill={r.skill:+.3f} -> p={R.loc[i,'perm_p']:.3f}")
for i,r in clfw.iterrows():
    R.loc[i,"perm_p"]=perm_clf(r.target,r.model,int(r.k),r.bacc)
    say(f"  perm clf {r.target}/{r.model}/k{int(r.k)} bacc={r.bacc:.3f} -> p={R.loc[i,'perm_p']:.3f}")

R.to_csv(ROOT/"analysis/B_multivariate.csv",index=False)
pd.set_option("display.width",220)
say("\n>>> analysis/B_multivariate.csv  共 %d 行"%len(R))
say("\n===== 回归:skill>0(击败哑基线) =====")
w=R[(R.track=='reg')&(R.skill>0)].sort_values("skill",ascending=False)
say(f"  {len(w)}/{len(R[R.track=='reg'])} 击败哑基线")
if len(w): say(w[["target","model","k","rmse","rho","skill","nc_skill","perm_p"]].to_string(index=False))
for tr,lab in [("bin","二分类"),("multi","多分类")]:
    w=R[(R.track==tr)&(R.bacc>0.5)].sort_values("bacc",ascending=False)
    say(f"\n===== {lab}:balanced_acc>0.5 =====  {len(w)}/{len(R[R.track==tr])}")
    if len(w): say(w[["target","model","k","f1","acc","bacc","perm_p"]].to_string(index=False))
say("\n===== 置换 p<0.05 =====")
sig=R[R.perm_p<0.05].sort_values("perm_p")
say("  %d 个"%len(sig))
if len(sig): say(sig.to_string(index=False))
