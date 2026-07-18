# -*- coding: utf-8 -*-
# 阶段1:全量特征提取(信号通道 × 配方),按 Daniel 的预处理树铺开。
#   只读 data/;输出 analysis/features.csv(替换阶段0的最小版)。
#   每个特征命名 {通道}_{配方},含义见 analysis/FEATURE_MENU.md。
#
# 通道(死通道 磁场/航向/GPS/电量 一律排除):
#   uaX/uaY/uaZ/uaMag   去重力加速度(motionUserAcceleration，单位 G)
#   gyX/gyY/gyZ/gyMag   角速度(motionRotationRate，rad/s)
#   pitch/roll/yaw      姿态角(motionPitch/Roll/Yaw，rad)
#   jerk                |a| 的时间导数(爆发性)
# 配方:时域(14)/频域(7)/时间结构×多阈值(在 |a| 上)。
import numpy as np, pandas as pd, pathlib
from scipy.stats import skew, kurtosis
ROOT=pathlib.Path("/Users/shiyu/Projects/adhd-segmentation")
DATA=ROOT/"data"
RAW_ACC =[f"accelerometerAcceleration{a}(G)" for a in "XYZ"]
USER_ACC=[f"motionUserAcceleration{a}(G)"   for a in "XYZ"]
GYRO    =[f"motionRotationRate{a}(rad/s)"    for a in "XYZ"]
ATT     =["motionPitch(rad)","motionRoll(rad)","motionYaw(rad)"]
REF_HEADER=[c.strip() for c in pd.read_csv(DATA/"H45_T.csv",sep=";",nrows=0).columns]

def sniff(path):
    with open(path) as f: line=f.readline()
    return ";" if line.count(";")>line.count(",") else ","

def load_T(path):
    df=pd.read_csv(path,sep=sniff(path),low_memory=False)
    cols=[c.strip() for c in df.columns]
    if "accelerometerTimestamp_sinceReboot(s)" not in cols:     # 表头损坏 -> 按列位移植
        assert len(cols)==len(REF_HEADER), f"{path.name}: {len(cols)} cols"
        df.columns=REF_HEADER
    else:
        df.columns=cols
    t=df["accelerometerTimestamp_sinceReboot(s)"].astype(float).to_numpy(); t=t-t[0]
    fs=1.0/np.median(np.diff(t))
    raw=np.linalg.norm(df[RAW_ACC].astype(float).to_numpy(),axis=1)   # 重力自检
    g=float(np.median(raw)); assert 0.9<g<1.1, f"{path.name}: |a| median={g:.3f}"
    return df,fs,t

# ---------- 配方:时域(14 个统计量) ----------
def f_time(x):
    x=np.asarray(x,float); x=x[np.isfinite(x)]
    xc=x-x.mean()
    zc=int(np.sum(np.abs(np.diff(np.sign(xc)))>0))
    q75,q25=np.percentile(x,[75,25])
    return {
        "mean":x.mean(), "std":x.std(ddof=1), "var":x.var(ddof=1),
        "rms":np.sqrt((x**2).mean()), "min":x.min(), "max":x.max(),
        "range":x.max()-x.min(), "median":np.median(x), "iqr":q75-q25,
        "mad":np.median(np.abs(x-np.median(x))),
        "skew":float(skew(x)), "kurt":float(kurtosis(x)),
        "zcr":zc/len(x), "madiff":np.mean(np.abs(np.diff(x))),
    }

# ---------- 配方:频域(7 个,去均值+Hann 窗) ----------
def f_freq(x,fs):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; x=x-x.mean()
    n=len(x); w=np.hanning(n); xw=x*w
    P=np.abs(np.fft.rfft(xw))**2
    f=np.fft.rfftfreq(n,d=1.0/fs)
    P[0]=0.0                                   # 去 DC
    tot=P.sum()
    if tot<=0: return {k:0.0 for k in ["domfreq","centroid","spread","entropy","bp_lf","bp_mf","bp_hf"]}
    p=P/tot
    dom=f[np.argmax(P)]
    cen=float((f*p).sum())
    spr=float(np.sqrt(((f-cen)**2*p).sum()))
    ent=float(-(p[p>0]*np.log(p[p>0])).sum()/np.log(len(p)))
    nyq=fs/2
    def band(lo,hi): return float(P[(f>=lo)&(f<hi)].sum()/tot)
    return {"domfreq":float(dom),"centroid":cen,"spread":spr,"entropy":ent,
            "bp_lf":band(0.5,3),"bp_mf":band(3,6),"bp_hf":band(6,nyq)}

# ---------- 时间结构 × 多阈值(在 |a| 上) ----------
def run_lengths(mask):
    if mask.size==0: return np.array([]),np.array([])
    idx=np.flatnonzero(np.diff(mask.astype(int))!=0)+1
    segs=np.split(mask,idx)
    lens=np.array([len(s) for s in segs]); vals=np.array([s[0] for s in segs])
    return lens[vals==1],lens[vals==0]     # 活动段, 静止段(单位: 样本数)

def f_tstruct(mag,fs,thr_pct):
    thr=np.percentile(mag,thr_pct)
    active=mag>thr
    act_len,stl_len=run_lengths(active)
    dur_min=len(mag)/fs/60.0
    n_switch=int(np.sum(np.abs(np.diff(active.astype(int)))>0))
    out={f"actfrac_p{thr_pct}":float(active.mean()),
         f"switchmin_p{thr_pct}":n_switch/dur_min}
    if act_len.size:
        a=act_len/fs
        out[f"actbout_med_p{thr_pct}"]=float(np.median(a))
        out[f"actbout_cv_p{thr_pct}"]=float(a.std()/a.mean()) if a.mean()>0 else 0.0
        out[f"actshort_p{thr_pct}"]=float(np.mean(a<1.0))   # <1s 短爆发占比
    else:
        out[f"actbout_med_p{thr_pct}"]=0.0; out[f"actbout_cv_p{thr_pct}"]=0.0; out[f"actshort_p{thr_pct}"]=0.0
    return out

# ================= 主循环 =================
aud=pd.read_csv(ROOT/"figures/subject_audit.csv")
SUBJ=sorted(aud[(aud.status=="usable")&(aud["_T"].astype(str).str.lower()=="yes")].subject.tolist())
assert len(SUBJ)==24

rows=[]
for i,s in enumerate(SUBJ,1):
    df,fs,t=load_T(DATA/f"{s}_T.csv")
    ua=df[USER_ACC].astype(float).to_numpy()
    gy=df[GYRO].astype(float).to_numpy()
    att=df[ATT].astype(float).to_numpy()
    uaMag=np.linalg.norm(ua,axis=1); gyMag=np.linalg.norm(gy,axis=1)
    jerk=np.diff(uaMag)*fs
    channels={
        "uaX":ua[:,0],"uaY":ua[:,1],"uaZ":ua[:,2],"uaMag":uaMag,
        "gyX":gy[:,0],"gyY":gy[:,1],"gyZ":gy[:,2],"gyMag":gyMag,
        "pitch":att[:,0],"roll":att[:,1],"yaw":att[:,2],
        "jerk":jerk,
    }
    feat={"subject":s}
    for name,x in channels.items():
        for k,v in f_time(x).items():  feat[f"{name}_{k}"]=v
        for k,v in f_freq(x,fs).items():feat[f"{name}_{k}"]=v
    for pct in (50,75,90):
        feat.update(f_tstruct(uaMag,fs,pct))
    rows.append(feat)
    print(f"[{i:2}/24] {s:5} fs={fs:.2f} n={len(uaMag):6d} 特征数={len(feat)-1}")

new=pd.DataFrame(rows).set_index("subject")
# 复用已验证的 8 个时间结构特征(median 阈值那套)
old=pd.read_csv(ROOT/"temporal_features.csv").set_index("subject")
keep=["switch_per_min","act_bout_median","stl_bout_median","act_bout_cv","stl_bout_cv",
      "frac_act_short","within_win_sd","mag_median"]
feats=new.join(old[keep]).loc[SUBJ]
feats.to_csv(ROOT/"analysis/features.csv")

# ---- 汇报 ----
tgt=pd.read_csv(ROOT/"analysis/targets.csv").set_index("subject")
print("\n===== features.csv:",feats.shape," targets.csv:",tgt.shape,"=====")
print("总特征列数:",feats.shape[1])
print("样本对齐?",list(feats.index)==list(tgt.index))
print("特征缺失合计:",int(feats.isna().sum().sum())," | 非有限值:",int((~np.isfinite(feats.to_numpy(float))).sum()))
# 每通道特征数概览
import collections
pref=collections.Counter(c.split("_")[0] for c in feats.columns)
print("每前缀特征数:",dict(pref))
print("\n示例列(前30):",list(feats.columns[:30]))
