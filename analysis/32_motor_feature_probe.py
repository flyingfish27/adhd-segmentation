# -*- coding: utf-8 -*-
# 目的(探查,不是检测器):看"运动障碍类"信号在 _F(100Hz)数据里是否可见/可算。
# (c)震颤 = 3-12Hz 频谱峰;(b)DCD = 动作平滑度(jerk 相对量)+ 子动作密度。
# 无金标准,仅描述信号结构。只读 data/。
import glob, os, numpy as np, pandas as pd
from scipy.signal import welch, find_peaks
D="/Users/shiyu/Projects/adhd-segmentation/data/"
files=sorted(glob.glob(D+"*_F.csv"))[:8]
ux,uy,uz=[f"motionUserAcceleration{a}(G)" for a in "XYZ"]
ts="accelerometerTimestamp_sinceReboot(s)"

print(f"{'subj':6} {'fs':>6} {'dur_s':>6} | {'主频Hz':>6} {'震颤带%(3-12Hz)':>13} {'粗动%(0.5-3Hz)':>13} | {'jerk比(平滑↓)':>12} {'子动作/秒':>9}")
print("-"*100)
for f in files:
    df=pd.read_csv(f, sep=",")
    subj=os.path.basename(f).replace("_F.csv","")
    t=df[ts].values; dt=np.median(np.diff(t)); fs=1/dt
    mag=np.sqrt(df[ux]**2+df[uy]**2+df[uz]**2).values   # 去重力后的运动幅值(G)
    mag=mag-np.mean(mag)
    # 频谱
    fr,P=welch(mag, fs=fs, nperseg=min(1024,len(mag)))
    band=lambda lo,hi:(P[(fr>=lo)&(fr<hi)].sum())
    tot=P[(fr>=0.3)&(fr<20)].sum()+1e-12
    dom=fr[(fr>=0.3)&(fr<15)][np.argmax(P[(fr>=0.3)&(fr<15)])]
    tremor=band(3,12)/tot*100; gross=band(0.5,3)/tot*100
    # 平滑度:jerk = 幅值的时间导数;jerk_rms / accel_rms 越大越"顿挫"(越不平滑)
    jerk=np.diff(mag)*fs
    jerk_ratio=np.sqrt(np.mean(jerk**2))/(np.sqrt(np.mean(mag**2))+1e-9)
    # 子动作密度:幅值包络的局部峰个数/秒(越多=动作越碎)
    pk,_=find_peaks(np.abs(mag), distance=int(fs*0.15), height=np.std(mag)*0.5)
    subm=len(pk)/(len(mag)/fs)
    print(f"{subj:6} {fs:6.1f} {len(mag)/fs:6.1f} | {dom:6.2f} {tremor:13.1f} {gross:13.1f} | {jerk_ratio:12.2f} {subm:9.2f}")

print("\n说明:主频=运动主频率;震颤带%/粗动%=功率占比;jerk比=不平滑度(越大越顿挫);子动作/秒=动作碎片度。")
print("无金标准 -> 只反映信号结构,不能据此判'有无运动障碍'。")
