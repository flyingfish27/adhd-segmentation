# -*- coding: utf-8 -*-
# 纯探查:只在每个孩子最"静止"的片段里找窄震颤峰(3-12Hz)。
# 真震颤 = 静止时频谱上一个又窄又尖的峰(峰突出度高);挥手跑动是宽带,不算。
# 无金标准,仅看信号里到底有没有这种结构。只读 data/。
import glob, os, numpy as np, pandas as pd
from scipy.signal import welch
D="/Users/shiyu/Projects/adhd-segmentation/data/"
ux,uy,uz=[f"motionUserAcceleration{a}(G)" for a in "XYZ"]
ts="accelerometerTimestamp_sinceReboot(s)"

def stillest_window(mag, fs, win_s=4.0):
    w=int(win_s*fs);
    if len(mag)<w: return mag
    # 逐窗算 RMS,取最小(最静止)
    best=None; bestrms=1e9
    for i in range(0,len(mag)-w,int(fs*0.5)):
        seg=mag[i:i+w]; r=np.sqrt(np.mean((seg-seg.mean())**2))
        if r<bestrms: bestrms=r; best=seg
    return best, bestrms

print(f"{'subj':6} {'静止段RMS(G)':>11} {'峰频Hz':>7} {'峰突出度x基线':>12} {'判读':>10}")
print("-"*60)
rows=[]
for f in sorted(glob.glob(D+"*_F.csv")):
    subj=os.path.basename(f).replace("_F.csv","")
    try:
        df=pd.read_csv(f, sep=",")
        t=df[ts].values; fs=1/np.median(np.diff(t))
        mag=np.sqrt(df[ux]**2+df[uy]**2+df[uz]**2).values
        seg,rms=stillest_window(mag,fs,4.0)
        seg=seg-seg.mean()
        fr,P=welch(seg, fs=fs, nperseg=min(256,len(seg)))
        m=(fr>=3)&(fr<=12)
        if m.sum()<3: continue
        Pb=P[m]; frb=fr[m]
        pk=np.argmax(Pb); peakf=frb[pk]; peakP=Pb[pk]
        base=np.median(Pb)+1e-15
        prom=peakP/base                       # 峰突出度(相对邻域基线)
        verdict="窄峰!" if (prom>8 and rms<0.03) else ("可疑" if prom>6 else "宽带/无")
        rows.append((subj,rms,peakf,prom,verdict))
    except Exception as e:
        continue
# 按突出度排序,最像震颤的在最上面
for subj,rms,peakf,prom,verdict in sorted(rows,key=lambda r:-r[3]):
    print(f"{subj:6} {rms:11.4f} {peakf:7.2f} {prom:12.1f} {verdict:>10}")

print(f"\n共 {len(rows)} 个孩子。判据:静止段RMS<0.03G 且 3-12Hz 峰突出度>8x基线 => 疑似窄震颤峰。")
print("提醒:即使出现窄峰,也可能是手表贴合/机械共振/单次抖动,无神经科真值无法确认是病理性震颤。")
