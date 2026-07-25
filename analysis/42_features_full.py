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
# 配方:时域(14)/频域(7)/时间结构。
#   时间结构有两条方法不同的路径,TASK-1 起【都在本脚本内原生算】(不再 join 外部表
#   temporal_features.csv),并各扫全部百分位档(见 PCTS):
#     路径A time_structure() 滑窗法,阈值=【各人自己】的百分位(保 amplitude-invariant);
#     路径B f_tstruct()      逐样本法,阈值=【24人合池】线(每人一票,故 actfrac 不再恒常数)。
#   两路的合并成"一个可复用统一函数"这件事按用户裁决推迟(见 backlog);此处两函数并存。
import numpy as np, pandas as pd, pathlib
from scipy.stats import skew, kurtosis
ROOT=pathlib.Path("/Users/shiyu/Projects/adhd-segmentation")
DATA=ROOT/"data"
RAW_ACC =[f"accelerometerAcceleration{a}(G)" for a in "XYZ"]
USER_ACC=[f"motionUserAcceleration{a}(G)"   for a in "XYZ"]
GYRO    =[f"motionRotationRate{a}(rad/s)"    for a in "XYZ"]
ATT     =["motionPitch(rad)","motionRoll(rad)","motionYaw(rad)"]
REF_HEADER=[c.strip() for c in pd.read_csv(DATA/"H45_T.csv",sep=";",nrows=0).columns]

# ---------- TASK-102:把所有人截到相同长度 ----------
# 为什么要截:24 人录制时长不等(3 人 41-44 分钟,21 人 58.4-59.75 分钟),特征因此
#   同时受"时长"和"信号非平稳"污染,人和人不可比(见 ISSUE-107 / ISSUE-113)。
# 截多长:取最短那人的长度,保留【前半段】。
# 口径 = P1「相同采样点数」(2026-07-22 用户裁决;另一口径 P2 是「相同时长」)。
#   实测依据 = analysis/46_duration_audit.py 的输出:
#     · 最短者 F55 恰为 73643 点(41.32 分钟),与本常量一致;
#     · 24 人 fs 全部落在 29.708-29.717 Hz(极差 0.0088 Hz),各人内部采样完全规则、无 >1s 断档;
#     · 因此 P1 与 P2 保留的点数最多相差 32 点(约 1.08 秒)。
#   选 P1 的客观后果:所有人的特征向量长度完全相同;各人实际时长相差最多约 1.08 秒。
#   截断丢弃全体合计 389.6 分钟,占原始总记录时长的 28.2%。
# 怎么关掉:把 N_TRUNC 设为 None 即完全不截断。
#   TASK-1 的「先证等价」回归测试必须在【未截断】信号上跑——参照表
#   temporal_features.BACKUP.csv 是全长信号的产物,截断后无法逐列复现。
N_TRUNC=73643

def sniff(path):
    with open(path) as f: line=f.readline()
    return ";" if line.count(";")>line.count(",") else ","

def load_T(path,n_max=N_TRUNC):
    df=pd.read_csv(path,sep=sniff(path),low_memory=False)
    cols=[c.strip() for c in df.columns]
    if "accelerometerTimestamp_sinceReboot(s)" not in cols:     # 表头损坏 -> 按列位移植
        assert len(cols)==len(REF_HEADER), f"{path.name}: {len(cols)} cols"
        df.columns=REF_HEADER
    else:
        df.columns=cols
    n_full=len(df)                                              # 截断前的原始点数
    if n_max is not None:
        assert n_full>=n_max, f"{path.name}: 仅 {n_full} 点,短于截断长度 {n_max}"
        df=df.iloc[:n_max]                                      # 取前半段
    t=df["accelerometerTimestamp_sinceReboot(s)"].astype(float).to_numpy(); t=t-t[0]
    fs=1.0/np.median(np.diff(t))
    raw=np.linalg.norm(df[RAW_ACC].astype(float).to_numpy(),axis=1)   # 重力自检
    g=float(np.median(raw)); assert 0.9<g<1.1, f"{path.name}: |a| median={g:.3f}"
    return df,fs,t,n_full

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

def f_tstruct(mag,fs,thr_pct,thr=None):
    # thr=None -> 用本人自己的第 thr_pct 百分位(旧行为、也是路径B原来的口径);
    # 传入 thr  -> 用这条现成阈值(TASK-1 决策3 最小改动:让路径B改用 24 人【合池】
    #   阈值,合池线怎么算见主循环。列名仍用 thr_pct 后缀,不受 thr 影响)。
    if thr is None:
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

# ---------- TASK-1:统一的「时间结构」函数(路径 A 的原生实现) ----------
# 这是原 notebook analysis/10_activity_verify.ipynb 里 temporal_features() 那条路子
# 的脚本内实现:先把信号按【滑动窗口】聚合成 w_mean / w_sd,再对【窗均值】卡百分位
# 阈值二值化,最后对【活动段与静止段同时】做游程统计。
#   它与本文件上面的 f_tstruct()(路径 B:在【逐个采样点】上直接卡阈值)是两条
#   方法不同的做法。TASK-1 的做法是把"先滑窗平滑、再二值化"保留成一个显式选项,
#   而不是把它删掉。两条路径目前并存。
#
# 参数全部 keyword-only 且【不给默认值】——调用方必须把每个数字显式写出来,
#   代码里不留隐藏的魔法数字。
#     win_s   滑动窗口长度(秒)      step_s  滑动窗口步长(秒)
#     pct     二值化用的阈值百分位   short_s "短活动段"的判定上限(秒)
#
# 返回值是【未取整】的原始浮点数。原 notebook 对每个键都做了 round(),那是写 csv 时
#   的显示精度、不属于计算本身;等价比对时由 analysis/verify_temporal_provenance.py
#   施加同一套取整后再逐列比。
def time_structure(mag,t,fs,*,win_s,step_s,pct,short_s):
    mag=np.asarray(mag,float)
    win,step=int(win_s*fs),int(step_s*fs)
    idx=range(0,len(mag)-win,step)
    w_mean=np.array([mag[s:s+win].mean() for s in idx])
    w_sd  =np.array([mag[s:s+win].std()  for s in idx])

    thr=np.percentile(w_mean,pct)          # 阈值卡在【窗均值】上,不是逐样本
    active=w_mean>thr

    edges=np.concatenate([[0],np.where(np.diff(active.astype(int))!=0)[0]+1,[len(active)]])
    durs  =np.diff(edges)*step_s           # 每段时长(秒)= 窗数 × 步长
    states=active[edges[:-1]]              # True = 活动段
    act,stl=durs[states],durs[~states]
    dur_min=t[-1]/60.0

    def cv(x): return float(x.std()/x.mean()) if len(x)>1 and x.mean()>0 else np.nan
    return {
        "switch_per_min" : (len(durs)-1)/dur_min,
        "act_bout_median": float(np.median(act)) if len(act) else np.nan,
        "stl_bout_median": float(np.median(stl)) if len(stl) else np.nan,
        "act_bout_cv"    : cv(act),
        "stl_bout_cv"    : cv(stl),
        "frac_act_short" : float((act<=short_s).mean()) if len(act) else np.nan,
        "within_win_sd"  : float(np.median(w_sd)),
        "mag_median"     : float(np.median(mag)),
        "dur_min"        : dur_min,
        "n_bouts"        : len(durs),
    }

# ---------- TASK-1:时间结构的扫描档位与固定窗参数 ----------
# 阈值百分位【全范围粗扫】(决策8,2026-07-25 用户拍板):路径A、路径B 都扫这9档。
#   进 features.csv 是固定表结构,故用固定网格;"粗扫→细化"若将来要做,是换网格重生成表。
PCTS=(10,20,30,40,50,60,70,80,90)
# 路径A滑窗参数(决策8只扫百分位,窗/步/短段判定沿用现状;其数值依据待 ISSUE-115)。
TS_WIN_S, TS_STEP_S, TS_SHORT_S = 10, 5, 10

# ================= 主循环 =================
# 收进 __main__ 保护:让本文件既能当脚本跑(行为与之前完全一致),
#   也能被 analysis/verify_temporal_provenance.py import 进去、直接调用上面那些
#   函数做等价回归测试——测的是【生产代码本身】,不是它的一份副本。
if __name__=="__main__":
    aud=pd.read_csv(ROOT/"figures/subject_audit.csv")
    SUBJ=sorted(aud[(aud.status=="usable")&(aud["_T"].astype(str).str.lower()=="yes")].subject.tolist())
    assert len(SUBJ)==24

    rows=[]; n_full_all={}; cache={}
    # ---- 第一趟:逐人算通道特征 + 路径A(各人自己阈值),并缓存 uaMag 供路径B第二趟用 ----
    for i,s in enumerate(SUBJ,1):
        df,fs,t,n_full=load_T(DATA/f"{s}_T.csv")
        n_full_all[s]=n_full
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
        feat.pop("jerk_median",None)     # TASK-1 决策7:删恒常数列 jerk_median(24人恒0,分布对称于0)
        # 路径A(决策5=各人自己阈值):滑窗法,原生实现、不再 join 外部表;扫全部百分位。
        for j,pct in enumerate(PCTS):
            ts=time_structure(uaMag,t,fs,win_s=TS_WIN_S,step_s=TS_STEP_S,pct=pct,short_s=TS_SHORT_S)
            for k in ("switch_per_min","act_bout_median","stl_bout_median",
                      "act_bout_cv","stl_bout_cv","frac_act_short"):
                feat[f"{k}_p{pct}"]=ts[k]
            if j==0: feat["within_win_sd"]=ts["within_win_sd"]   # 只依赖窗参数、与pct无关,取一次即可
        # mag_median 去重(决策=保留 uaMag_median、删 mag_median):此处不写 mag_median,
        #   uaMag_median 已由上面 uaMag 通道的 f_time 产出。
        rows.append(feat); cache[s]=(uaMag,fs)    # 路径B第二趟(合池阈值)要用 uaMag
        cut=n_full-len(uaMag)
        print(f"[{i:2}/24] {s:5} fs={fs:.2f} n={len(uaMag):6d} (原 {n_full:6d}, 截掉 {cut:6d}) 路径A+通道列已算")

    # ---- TASK-102 截断自检:数据集若变动,这里会显性报错而不是静默算错 ----
    if N_TRUNC is not None:
        n_min=min(n_full_all.values()); who=min(n_full_all,key=n_full_all.get)
        assert n_min==N_TRUNC, (f"最短记录已不是 {N_TRUNC} 点,而是 {n_min} 点(被试 {who})"
                                f" —— 数据集已变动,N_TRUNC 需按 analysis/46_duration_audit.py 重新核定")
        print(f"\n[TASK-102] 截断口径 P1:每人取前 {N_TRUNC} 点(约 41.32 分钟,取前半段)")
        print(f"           最短者 {who} 恰为 {n_min} 点,与 N_TRUNC 一致(自检通过)")
        print(f"           全体原始合计 {sum(n_full_all.values()):,} 点 -> 截断后 {24*N_TRUNC:,} 点"
              f",丢弃 {100*(1-24*N_TRUNC/sum(n_full_all.values())):.1f}%")
    else:
        print("\n[TASK-102] N_TRUNC=None -> 未截断,使用全长信号")

    # ---- 第二趟:路径B(逐样本法),用 24 人【合池】阈值(决策5 c2「每人一票」) ----
    # 合池线 = 先给每个孩子各自算他自己的第 pct 百分位,得 24 个数,再取这 24 个数的中位数。
    #   与路径A(各人自己阈值)不同:路径B 的阈值对 24 人是同一条,故 actfrac 不再恒为常数。
    # TASK-1 消除了对 temporal_features.csv 的 join:路径A的列现在也在本脚本内原生算(截断信号),
    #   features.csv 不再是"截断267 + 全长8"的混合口径,全表统一口径。
    pooled={pct: float(np.median([np.percentile(cache[s][0],pct) for s in SUBJ])) for pct in PCTS}
    feat_by_s={r["subject"]:r for r in rows}
    for s in SUBJ:
        uaMag,fs=cache[s]
        for pct in PCTS:
            feat_by_s[s].update(f_tstruct(uaMag,fs,pct,thr=pooled[pct]))
    print("\n[TASK-1] 路径B合池阈值(24人每人一票的中位数,单位G):",
          {f"p{p}":round(v,4) for p,v in pooled.items()})

    feats=pd.DataFrame(rows).set_index("subject").loc[SUBJ]
    EXPECT=252+11*len(PCTS)          # 12通道×21 −jerk_median +路径A(6k+1) +路径B(5k) = 252+11k
    assert feats.shape[1]==EXPECT, f"列数 {feats.shape[1]} != 预期 {EXPECT}(k={len(PCTS)})"
    assert "mag_median" not in feats.columns, "mag_median 应已去重删除"
    assert "jerk_median" not in feats.columns, "jerk_median 应已删除"
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
