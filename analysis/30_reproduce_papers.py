# -*- coding: utf-8 -*-
# 目的:从 data/ 重算,复现论文1 和论文2 的数字;核心裁决——论文2 的 1.67 阈值
# 到底卡在 0-3 还是 1-4 尺度。只读 data/,不改动。
import numpy as np, pandas as pd
P="/Users/shiyu/Projects/adhd-segmentation/data/Demographic and mental health data.csv"
df=pd.read_csv(P,encoding="utf-8-sig",dtype=str); df.columns=[c.strip() for c in df.columns]
SNAP=[f"a{i}" for i in range(1,27)]; SDQ=[c for c in df.columns if c.startswith("SDQ")]
for c in SNAP+SDQ+["BMI","height(cm)","weight(kg)"]: df[c]=pd.to_numeric(df[c],errors="coerce")
df.loc[df["SDQ8"]==13,"SDQ8"]=np.nan
sex=df["SEX"].str.strip().str.lower()
hasdem=df["BMI"].notna()

def by_sex(series, mask, label, tgt):
    print(f"  {label}")
    for s in ["male","female"]:
        v=series[mask&(sex==s)].dropna()
        print(f"    [{s:6}] n={len(v)} mean={v.mean():.2f} sd={v.std(ddof=1):.2f} median={v.median():.2f}   目标 {tgt.get(s,'')}")

print("="*70)
print("论文1 复现  (标签: SNAP总分 -> Z -> T=Z*10+50 -> T>=55)")
print("  论文报告: ADHD 13/50 = 26%, 男 37.9%(11/29), 女 9.5%(2/21)")
print("="*70)
snap_tot=df[SNAP].sum(axis=1, min_count=len(SNAP))   # 原始 1-4 之和,仅26项齐全者
comp=snap_tot.notna()
v=snap_tot[comp]
print(f"SNAP总分(原始1-4): N={len(v)} mean={v.mean():.2f} sd={v.std(ddof=1):.2f}   [0-3尺度: mean={(v-26).mean():.2f}]")
z=(v-v.mean())/v.std(ddof=1); T=z*10+50; adhd=T>=55
mA=int(((sex=='male')&comp&adhd).sum()); fA=int(((sex=='female')&comp&adhd).sum())
mN=int(((sex=='male')&comp).sum());     fN=int(((sex=='female')&comp).sum())
print(f"T>=55 判 ADHD: 合计 {int(adhd.sum())}  |  男 {mA}/{mN}={mA/mN*100:.1f}%  女 {fA}/{fN}={fA/fN*100:.1f}%")
print(f"  -> ADHD 数 {'命中13' if adhd.sum()==13 else '未中'};男女各 {mA}/{fA}(论文 11/2)")
print(f"  注:减1变0-3再算,ADHD 数 = {int(((( (v-26)-(v-26).mean())/(v-26).std(ddof=1)*10+50)>=55).sum())}(T分对平移不变,应仍13)")

print("\n"+"="*70)
print("论文2 复现  Table 1  (缺失->0, demographic-present, 原始尺度)")
print("="*70)
by_sex(df["height(cm)"], hasdem&df["height(cm)"].notna(), "height(cm)", {"male":"136.00/10.78 n30","female":"134.77/10.45 n22"})
by_sex(df["weight(kg)"], hasdem&df["weight(kg)"].notna(), "weight(kg)", {"male":"32.27/9.96 n30","female":"29.82/7.01 n22"})
by_sex(df["BMI"],        hasdem&df["BMI"].notna(),        "BMI",        {"male":"17.09/3.02 n30","female":"16.18/2.30 n23"})
by_sex(df[SDQ].fillna(0).sum(axis=1),  hasdem, "SDQ 分(缺->0,原始1-3和)",  {"male":"39.33/13.73 med43 n30","female":"43.52/10.56 med44 n23"})
by_sex(df[SNAP].fillna(0).sum(axis=1), hasdem, "SNAP分(缺->0,原始1-4和)", {"male":"42.17/19.42 n30","female":"34.50/12.21 n22"})

print("\n"+"="*70)
print("★ 核心裁决:论文2 分组阈值 mean SNAP >= 1.67 落在哪个尺度?")
print("  (论文说'高症状组比低症状组小',可作合理性判据)")
print("="*70)
# 每人 SNAP 每项均值(仅 SNAP 齐全者)
per_raw=(snap_tot/len(SNAP))[comp]        # 原始 1-4 尺度
per_03 = per_raw - 1                        # 减1 -> 标准 0-3 尺度
print(f"SNAP 齐全者 N={len(per_raw)}")
print(f"每项均值(原始1-4): 全体 mean={per_raw.mean():.3f} median={per_raw.median():.3f} min={per_raw.min():.2f} max={per_raw.max():.2f}")
print(f"每项均值(0-3尺度): 全体 mean={per_03.mean():.3f} median={per_03.median():.3f} min={per_03.min():.2f} max={per_03.max():.2f}")
print()
hi_raw=int((per_raw>=1.67).sum()); lo_raw=len(per_raw)-hi_raw
hi_03 =int((per_03 >=1.67).sum()); lo_03 =len(per_03)-hi_03
print(f"阈值 1.67 卡在【原始 1-4】: High={hi_raw}  Low={lo_raw}   (High {'<' if hi_raw<lo_raw else '>='} Low)")
print(f"阈值 1.67 卡在【0-3 标准】: High={hi_03}  Low={lo_03}   (High {'<' if hi_03<lo_03 else '>='} Low)")
print()
print(f"-> 1.67 ≈ 原始1-4 的全体均值({per_raw.mean():.2f})/中位数({per_raw.median():.2f}),在1-4上给出可用的 {hi_raw}/{lo_raw} 分组;")
print(f"   在0-3上退化成 {hi_03}/{lo_03}(几乎全 Low,无法做组间比较)。")
print(f"   结论:论文2 的 1.67 是卡在【原始 1-4 尺度】(即数据 as-stored,未减1)。")
