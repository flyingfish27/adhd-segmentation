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
# 配方:时域(14)/频域(7)/时间结构/非线性等 6 类(TASK-10)/录制时长(TASK-116)。
#   时间结构有两条方法不同的路径,TASK-1 起【都在本脚本内原生算】(不再 join 外部表
#   temporal_features.csv),并各扫全部百分位档(见 PCTS):
#     路径A time_structure() 滑窗法,阈值=【各人自己】的百分位(保 amplitude-invariant);
#       TASK-108 起窗长/步长也扫 5 组(见 TS_WINS),故路径A是【窗配置 × 阈值】双层扫描。
#     路径B f_tstruct()      逐样本法,阈值=【24人合池】线(每人一票,故 actfrac 不再恒常数)。
#   两路的合并成"一个可复用统一函数"这件事按用户裁决推迟(见 backlog);此处两函数并存。
import os, numpy as np, pandas as pd, pathlib
from scipy.stats import skew, kurtosis
# ROOT 定位(2026-07-26 改,原为写死的主检出绝对路径 /Users/shiyu/Projects/adhd-segmentation):
#   写死的后果是——在任何 git worktree 里跑本脚本,产物 analysis/features.csv 都会被写进
#   【主检出】,静默覆盖别的桌子正在用的那张表(不报错)。故拆成两个根:
#     ROOT = 本脚本所在的 checkout(产物写这里,永远是自己的桌子);
#     SRC  = 原始数据与上游产物所在的 checkout(data/ 与 figures/subject_audit.csv 都
#            未入 git,不随 worktree 复制,所以在 worktree 里跑必须用 ADHD_ROOT 指向主检出)。
#   在主检出里跑时两者相同,行为与改动前完全一致。
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parent
SRC =pathlib.Path(os.environ.get("ADHD_ROOT", ROOT)).resolve()
DATA=SRC/"data"
assert DATA.is_dir(), (f"找不到 {DATA} —— 本脚本要读原始数据;若在 worktree 里跑,"
                       f"请设 ADHD_ROOT 指向有 data/ 的主检出。")
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
    # TASK-116:截断【之前】的真实时钟时长(秒)= 时间戳跨度,直接测量、无估计误差。
    #   放进 df.attrs 而不是加返回值,是为了不破坏现有 7 处 `df,fs,t,n_full = load_T(...)` 的解包
    #   (verify_temporal_provenance.py 与 50/52/55a/55b/55c/56 号探针)。
    _tf=df["accelerometerTimestamp_sinceReboot(s)"].astype(float).to_numpy()
    span_full_s=float(_tf[-1]-_tf[0])
    if n_max is not None:
        assert n_full>=n_max, f"{path.name}: 仅 {n_full} 点,短于截断长度 {n_max}"
        df=df.iloc[:n_max]                                      # 取前半段
    df.attrs["span_full_s"]=span_full_s
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

# ---------- TASK-10:补算缺失的特征大类(6 类,ISSUE-8 / 2026-07-26 用户裁决) ----------
# 裁决做的 6 类:① DFA 标度指数 ② Hurst 指数 ③ 排列熵 ④ LZ 复杂度
#               ⑤ 自相关/周期性(主周期、衰减率) ⑥ 事件/峰(峰数、峰间隔、峰幅分布)
# 本阶段暂缓的 5 类(理由见 working/task.md 的 TASK-10 条目):RQA(算不动)、样本熵(慢约300倍
#   且与排列熵信息重叠)、跨通道/小波/姿态动态(与现有 251 个统计量重叠度较高)。
#
# ⚠️ 这 6 类【各自带着自己的参数】,和 ISSUE-115/ISSUE-102 争论的是同一类问题:
#   有出处的:LZ 的"中位数二值化"、排列熵的 τ=1、DFA 的一阶去趋势 —— 均为各方法的标准做法。
#   无出处的(本文件是它们的唯一登记点,须随结果一起声明):
#     · DFA / Hurst 的尺度范围下界 16 点、上界 N/10;
#     · 排列熵的嵌入维 m=3;
#     · 自相关的最大滞后 60 秒(超过它一律记为未衰减);
#     · 峰检测的高度门槛"中位数 + 2×MAD"与最小峰间距 0.5 秒。
#   本轮【不扫描】这些参数。理由:TASK-115 已实测同类参数在 n=24 下无法由数据确定
#   (快照 probe_outputs/param_derivation.md),扫描只会把无法确定的参数变成更多的列。
def dfa_alpha(x, scales):
    """去趋势波动分析的标度指数 α:对累积离差序列分窗一阶去趋势,看波动随窗长的幂律斜率。"""
    # 一阶去趋势用【居中时间轴的闭式解】而非 lstsq:后者在 n 达数千时设计矩阵条件数很差,
    #   实测会抛 divide-by-zero / overflow 告警。闭式解无矩阵求逆,数值稳定且更快。
    y=np.cumsum(x-x.mean()); out=[]; used=[]
    for n in scales:
        m=len(y)//n
        if m<2: continue
        seg=y[:m*n].reshape(m,n)
        tc=np.arange(n)-(n-1)/2.0                 # 居中 -> 斜率与截距解耦
        slope=(seg*tc).sum(1)/(tc*tc).sum()
        resid=seg-(seg.mean(1,keepdims=True)+slope[:,None]*tc)
        f=float(np.sqrt((resid**2).mean()))
        if np.isfinite(f) and f>0: out.append(f); used.append(n)
    if len(used)<3: return np.nan
    return float(np.polyfit(np.log(used),np.log(out),1)[0])

def hurst_rs(x, scales):
    """Hurst 指数(重标极差 R/S 法):看极差与标准差之比随窗长的幂律斜率。"""
    out=[]
    for n in scales:
        m=len(x)//n
        if m<1: out.append(np.nan); continue
        seg=x[:m*n].reshape(m,n)
        Z=np.cumsum(seg-seg.mean(1,keepdims=True),axis=1)
        R=Z.max(1)-Z.min(1); S=seg.std(1,ddof=1)
        v=R[S>0]/S[S>0]
        out.append(float(v.mean()) if v.size else np.nan)
    RS=np.array(out); ok=np.isfinite(RS)&(RS>0)
    if ok.sum()<3: return np.nan
    return float(np.polyfit(np.log(np.asarray(scales)[ok]),np.log(RS[ok]),1)[0])

def perm_entropy(x, m=3, tau=1):
    """排列熵:把每 m 个相邻点的【大小次序】当成一个符号,统计这些符号的分布有多均匀。
       归一化到 [0,1](除以 log(m!))。1 = 完全不可预测,0 = 完全规则。"""
    span=(m-1)*tau+1
    if len(x)<span+1: return np.nan
    emb=np.lib.stride_tricks.sliding_window_view(x,span)[:,::tau]
    order=np.argsort(emb,axis=1,kind="stable")
    code=np.zeros(len(order),np.int64)
    for i in range(m): code=code*m+order[:,i]
    _,cnt=np.unique(code,return_counts=True)
    p=cnt/cnt.sum()
    import math
    return float(-(p*np.log(p)).sum()/np.log(math.factorial(m)))

def lz_complexity(x):
    """LZ 复杂度(按中位数二值化后计不重复短语数),归一化为 C·log2(n)/n。
       变体 = LZ78 字典解析(逐点扩张当前短语,遇到字典里没有的就收一个新短语并清空)。
       为什么不用经典 LZ76(Kaspar-Schuster):它的朴素实现是 O(n²),实测在 n=73643 上
         单通道超过 10 分钟、12 通道 24 人不可行;LZ78 是 O(n),实测 0.5 秒/通道。
       ⚠️ 与 analysis/52_scan_compute_cost.py 探针2 里那个 LZ 实现【不是同一变体】。
         那只探针只用于测【耗时】、其数值未进任何产物,故本处换变体不影响任何既有快照。"""
    b=(np.asarray(x)>np.median(x)).astype(np.uint8).tobytes(); n=len(b)
    if n<2: return np.nan
    seen=set(); w=b""; C=0
    for i in range(n):
        wc=w+b[i:i+1]
        if wc in seen: w=wc
        else: seen.add(wc); C+=1; w=b""
    if w: C+=1
    return float(C*np.log2(n)/n)

def acf_features(x, fs, max_lag_s=60.0):
    """自相关/周期性:衰减率(自相关跌到 1/e 的滞后秒数)与主周期(首个过零点之后的最强峰)。"""
    x=np.asarray(x,float); x=x-x.mean(); n=len(x)
    if n<10 or x.std()==0: return {"acf_tau_1e_s":np.nan,"acf_dom_period_s":np.nan,"acf_dom_peak":np.nan}
    nf=1<<int(np.ceil(np.log2(2*n)))
    F=np.fft.rfft(x,nf); ac=np.fft.irfft(F*np.conj(F),nf)[:n].real
    ac=ac/ac[0]
    ml=min(n-1,int(max_lag_s*fs)); ac=ac[:ml]
    below=np.flatnonzero(ac<1.0/np.e)
    tau=float(below[0]/fs) if below.size else np.nan     # 未在 max_lag_s 内衰减 -> nan(删失,不记成上限)
    # 主周期 = 【首个局部极小之后】的最强自相关峰。
    #   不用"首个过零点之后"那种写法:去重力动作强度这类【恒正】信号的自相关长期不过零,
    #   实测 24 人里有 16 人在 60 秒内根本不过零,那样写会让主周期对多数人为 NaN——
    #   那是实现缺陷,不是"这些孩子没有周期"这个数据事实。
    d=np.diff(ac); rise=np.flatnonzero(d>0)
    if rise.size and rise[0]+1<len(ac):
        k0=int(rise[0])+1
        k=int(np.argmax(ac[k0:]))+k0
        dom=float(k/fs); pk=float(ac[k])
    else: dom,pk=np.nan,np.nan
    # acf_dom_peak 是主周期那一点的自相关高度,用来判读主周期有没有意义:
    #   高度接近 0 说明"最强峰"只是噪声起伏,该周期不可解释。报告须带上这一列。
    return {"acf_tau_1e_s":tau,"acf_dom_period_s":dom,"acf_dom_peak":pk}

def peak_features(x, fs, k_mad=2.0, min_gap_s=0.5):
    """事件/峰:峰的密度、峰间隔的中位与变异、峰幅的中位与变异。
       高度门槛 = 中位数 + k_mad×(1.4826×MAD);最小峰间距 min_gap_s 秒。"""
    from scipy.signal import find_peaks
    x=np.asarray(x,float); med=float(np.median(x))
    mad=float(np.median(np.abs(x-med)))*1.4826
    if not np.isfinite(mad) or mad<=0:
        return {"peak_rate_min":np.nan,"peak_ipi_med_s":np.nan,"peak_ipi_cv":np.nan,
                "peak_amp_med":np.nan,"peak_amp_cv":np.nan}
    pk,pr=find_peaks(x,height=med+k_mad*mad,distance=max(1,int(min_gap_s*fs)))
    dur_min=len(x)/fs/60.0
    if pk.size<3:
        return {"peak_rate_min":float(pk.size/dur_min),"peak_ipi_med_s":np.nan,"peak_ipi_cv":np.nan,
                "peak_amp_med":float(np.median(pr["peak_heights"])) if pk.size else np.nan,
                "peak_amp_cv":np.nan}
    ipi=np.diff(pk)/fs; amp=pr["peak_heights"]
    def cv(a): return float(a.std()/a.mean()) if a.mean()>0 else np.nan
    return {"peak_rate_min":float(pk.size/dur_min),"peak_ipi_med_s":float(np.median(ipi)),
            "peak_ipi_cv":cv(ipi),"peak_amp_med":float(np.median(amp)),"peak_amp_cv":cv(amp)}

def f_nonlinear(x, fs):
    """TASK-10 的 6 类合起来:每个通道 12 列。"""
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    scales=np.unique(np.logspace(np.log10(16),np.log10(max(32,n//10)),20).astype(int))
    o={"dfa_alpha":dfa_alpha(x,scales),"hurst_rs":hurst_rs(x,scales),
       "permen_m3":perm_entropy(x),"lz_c":lz_complexity(x)}
    o.update(acf_features(x,fs)); o.update(peak_features(x,fs))
    return o

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
# 路径A滑窗参数。TASK-108(来源 ISSUE-115,2026-07-26)把窗长/步长由单值 (10,5) 扩成
#   【5 组敏感性扫描】,短段判定 short_s 固定 10 秒不扫。
#   扫这 5 组的依据(ISSUE-115 裁决,两端有据、中间过渡):
#     · 0.5 秒 = 贴着信号自身"记忆长度"的下沿——24 人 uaMag 自相关衰减到 1/e 的时间
#       实测中位 1.363 秒、25/75 分位 0.530/2.171 秒、全体 0.236-7.876 秒
#       (快照 analysis/probe_outputs/autocorr_timescale.md,脚本 50_temporal_design_probes.py 探针1);
#     · 10 秒 = 改动前沿用的现状值(源自早期 notebook,无数据依据);
#     · 1 / 2 / 5 秒 = 两端之间的过渡档。步长一律取窗长的一半。
#   目的(用户 2026-07-25 原话):把结论从"在某一组参数下没发现信号"升级为
#     "在 0.5-10 秒的整个平滑尺度上都没有信号"。
#   统计合法性:本网格已【先于任何扫描结果】写进 working/issue.md 的 ISSUE-115 条目,
#     故属预先指定的稳健性检验,不是看过结果再补搜索。
#   连带限制(须随结果一起报告):段时长按构造 = 步长的整数倍(见下面 durs 那行),而
#     short_s 固定 10 秒,故 frac_act_short 这一列在 step=5 秒下只能取极少数离散值、
#     在 step=0.25 秒下可取约 40 档——同一列在 5 组设定间分辨率相差约 20 倍,横向比较须知情。
TS_WINS=((0.5,0.25),(1,0.5),(2,1),(5,2.5),(10,5))    # (win_s, step_s),单位秒
TS_SHORT_S=10

# ---------- TASK-10:6 类新特征算在哪些通道上〔2026-07-26 用户裁决〕 ----------
# 裁决 = uaMag(去重力动作强度)+ gyMag(角速度大小)+ jerk(uaMag 的时间导数,爆发性)。
#   每通道 12 列 × 3 通道 = 36 列。选这三个的客观依据(实测,见下)与未取全部 12 通道的代价:
#   · 这三个通道在 24 人上【无 NaN、无常数列】;
#   · 若取全部 12 通道(+144 列),实测会引入 9 个含 NaN 的列——姿态角上基本没有超过峰检测
#     门槛的峰:roll 的 4 个峰特征对 9/24 人为 NaN、yaw 的 4 个对 21/24 人为 NaN、
#     pitch_peak_amp_cv 对 1/24 人为 NaN;
#   · 多重比较代价:已实测新增 200 列会让目标 sdq_cond 的最小 q 由 0.412 升到 0.517
#     (快照 probe_outputs/fdr_family_growth.md)。本裁决只加 36 列。
#   · 算力不是约束:f_nonlinear 单通道单人实测 18 毫秒。
NL_CHANNELS=("uaMag","gyMag","jerk")
def wtag(win_s):
    """窗配置的列名后缀:0.5 -> 'w0.5',10 -> 'w10'。不编步长——步长恒为窗长一半。"""
    return f"w{win_s:g}"

# ================= 主循环 =================
# 收进 __main__ 保护:让本文件既能当脚本跑(行为与之前完全一致),
#   也能被 analysis/verify_temporal_provenance.py import 进去、直接调用上面那些
#   函数做等价回归测试——测的是【生产代码本身】,不是它的一份副本。
if __name__=="__main__":
    aud=pd.read_csv(SRC/"figures/subject_audit.csv")   # 未入 git,只在主检出有,故走 SRC
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
        # TASK-10:6 类新特征(非线性/复杂度、自相关周期性、事件/峰),只在 NL_CHANNELS 上算
        for name in NL_CHANNELS:
            for k,v in f_nonlinear(channels[name],fs).items(): feat[f"{name}_{k}"]=v
        feat.pop("jerk_median",None)     # TASK-1 决策7:删恒常数列 jerk_median(24人恒0,分布对称于0)
        # ---------- TASK-116(来源 ISSUE-114,2026-07-26 用户裁决=当特征):录制时长 ----------
        # 记的是【截断之前】那个人的真实录制长度。为什么必须是截断前:TASK-102 已把参与
        #   计算的窗口统一到 N_TRUNC=73643 点,若记截断后的长度则 24 人全同、无区分度。
        # 为什么这个量要当特征:实测(探针 analysis/54_duration_confound_probe.py,快照
        #   probe_outputs/duration_confound.md)录制时长与症状分 sdq_totdiff 的秩相关
        #   ρ=−0.474(症状越重录得越短),且与 101 个特征的 |ρ|>0.3。显式列出来,
        #   等于让模型看见这个量,而不是让它藏在别的特征里冒充运动信号。
        # 裁决的另一半:当【控制变量】那半=不当(ISSUE-103 裁决时定,局限已记 backlog §9 的 R11)。
        # ⚠️ 口径选择不是无关紧要的 —— 三种度量"同一个物理量"的方式给出不同的排序,
        #   实测(analysis/56_rec_duration_column_audit.py,快照 probe_outputs/rec_duration_column.md):
        #     ① 采样点数 n_full               × sdq_totdiff  ρ=−0.485 (p=0.016)
        #     ② 时间戳跨度 t[-1]−t[0](本列)   × sdq_totdiff  ρ=−0.295 (p=0.162)
        #     ③ n_full/fs/60                  × sdq_totdiff  ρ=−0.250 (p=0.239)
        #   三者【彼此】的秩相关仅 0.49–0.67。成因:24 人里 21 人都录满,其真实时长跨度
        #   仅 1.36 分钟,其中 20 人落在 0.36 秒之内;而各人采样率差异(29.708–29.717 Hz,
        #   相对差 0.03%)与这 0.36 秒同量级,故除不除以 fs 会把这 20 人的排序整个打乱。
        #   即这一列在 20 个录满者之间的排名由亚秒级停表时刻差决定,秩相关会把它当真实信息用。
        #   ISSUE-114 / backlog §9 R11 / ISSUE-103 引用的 ρ=−0.474 出自口径①(探针 54 用
        #   `wc -l` 数点数),该探针头部写着"点数与时长等价"——对秩统计而言这句不成立。
        # 本列取口径② = 时间戳跨度,理由:它是"录制时长"这个名字所指的量的【直接测量】,
        #   无采样率估计误差。此选择须与上述三个数一并报告(口径变了,立论数字随之变)。
        feat["rec_dur_min"]=df.attrs["span_full_s"]/60.0
        # 路径A(决策5=各人自己阈值):滑窗法,原生实现、不再 join 外部表;
        #   TASK-108 起是【双层扫描】= 5 组窗配置 × 9 档阈值百分位。
        #   列名必须同时编码两维(如 switch_per_min_w0.5_p50),否则 5 组窗配置的同名列会互相覆盖。
        for win_s,step_s in TS_WINS:
            wt=wtag(win_s)
            for j,pct in enumerate(PCTS):
                ts=time_structure(uaMag,t,fs,win_s=win_s,step_s=step_s,pct=pct,short_s=TS_SHORT_S)
                for k in ("switch_per_min","act_bout_median","stl_bout_median",
                          "act_bout_cv","stl_bout_cv","frac_act_short"):
                    feat[f"{k}_{wt}_p{pct}"]=ts[k]
                # within_win_sd 只依赖窗参数、与 pct 无关,故每组窗配置取一次(共 5 列)
                if j==0: feat[f"within_win_sd_{wt}"]=ts["within_win_sd"]
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
    # 列数断言(TASK-108 起随窗配置组数 W 变化):
    #   ① 通道特征 12通道×(时域14+频域7) − jerk_median = 251
    #   ② 路径A  (6 个随阈值变的指标 × k 档 + within_win_sd 1 列) × W 组窗配置
    #   ③ 路径B  5 族 × k 档(逐样本法,不受窗参数影响)
    #   ④ TASK-116 的 rec_dur_min(录制时长)1 列
    #   ⑤ TASK-10 的 6 类新特征:12 列 × len(NL_CHANNELS) 个通道
    K,W=len(PCTS),len(TS_WINS)
    EXPECT=251 + (6*K+1)*W + 5*K + 1 + 12*len(NL_CHANNELS)
    assert feats.shape[1]==EXPECT, f"列数 {feats.shape[1]} != 预期 {EXPECT}(k={K}, W={W})"
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
