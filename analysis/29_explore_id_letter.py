# -*- coding: utf-8 -*-
# 目的(只做这一件事):探索 ID 首字母编码了什么信息。不预设是年级。
# 把首字母/数字结构、以及首字母与身高/体重/BMI/性别/SDQ/SNAP/ADHD 的关系摊开,
# 并和论文1 报告的数字对照(N=50, 29M/21F, 13 ADHD, 男37.9%/女9.5%, age9.16, BMI16.57)。
import re, numpy as np, pandas as pd
pd.set_option("display.width",220); pd.set_option("display.max_rows",80)
P="/Users/shiyu/Projects/adhd-segmentation/data/Demographic and mental health data.csv"
df=pd.read_csv(P,encoding="utf-8-sig",dtype=str); df.columns=[c.strip() for c in df.columns]
SNAP=[f"a{i}" for i in range(1,27)]; SDQ=[c for c in df.columns if c.startswith("SDQ")]
for c in SNAP+SDQ+["BMI","height(cm)","weight(kg)"]: df[c]=pd.to_numeric(df[c],errors="coerce")
df.loc[df["SDQ8"]==13,"SDQ8"]=np.nan

# 解析 ID
m=df["ID"].str.extract(r'^([A-Za-z]+)(\d+)$')
df["L"]=m[0]; df["Num"]=pd.to_numeric(m[1])
sex=df["SEX"].str.strip().str.lower()
df["male"]=(sex=="male").astype(int)

# ADHD 标签(论文1:SNAP总分->Z->T>=55)
tot=df[SNAP].sum(axis=1,min_count=len(SNAP))
z=(tot-tot.mean())/tot.std(ddof=1)
df["ADHD"]=((z*10+50)>=55).where(tot.notna())

print("===== 1. 按数字排序,看首字母是否成连续块(块=批次/班级?散=按人属性如姓氏?) =====")
s=df.sort_values("Num")
print("  Num->L :", "  ".join(f"{int(r.Num)}{r.L}" for _,r in s.iterrows()))
print(f"  数字范围: {int(df.Num.min())}-{int(df.Num.max())}  唯一? {df.Num.is_unique}  共 {len(df)} 人")
print(f"  出现的首字母: {sorted(df['L'].unique())}  (共 {df['L'].nunique()} 种)")

print("\n===== 2. 每个首字母的画像 =====")
g=df.groupby("L")
tab=pd.DataFrame({
  "n":g.size(),
  "num范围":g["Num"].apply(lambda x:f"{int(x.min())}-{int(x.max())}"),
  "%男":(g["male"].mean()*100).round(0),
  "身高_mean":g["height(cm)"].mean().round(1),
  "身高_sd":g["height(cm)"].std(ddof=1).round(1),
  "BMI_mean":g["BMI"].mean().round(1),
  "SDQ和_mean":g[SDQ].apply(lambda x:x.sum(axis=1,min_count=1).mean()).round(1),
  "SNAP和_mean":g[SNAP].apply(lambda x:x.sum(axis=1,min_count=len(SNAP)).mean()).round(1),
  "ADHD数":g["ADHD"].sum(),
}).sort_values("num范围", key=lambda s: s.str.split("-").str[0].astype(int))
print(tab.to_string())

print("\n===== 3. 首字母能否解释身高方差?(eta^2: 越接近1越像'同字母=同年龄/班级') =====")
h=df.dropna(subset=["height(cm)"])
grand=h["height(cm)"].mean()
ss_tot=((h["height(cm)"]-grand)**2).sum()
ss_between=h.groupby("L")["height(cm)"].apply(lambda x:len(x)*(x.mean()-grand)**2).sum()
print(f"  身高 eta^2(首字母)= {ss_between/ss_tot:.3f}   （对照:随机应≈字母数/人数）")
# 同理 BMI、SNAP
for col,name in [("BMI","BMI"),]:
    hh=df.dropna(subset=[col]); gm=hh[col].mean()
    sst=((hh[col]-gm)**2).sum()
    ssb=hh.groupby("L")[col].apply(lambda x:len(x)*(x.mean()-gm)**2).sum()
    print(f"  {name} eta^2(首字母)= {ssb/sst:.3f}")

print("\n===== 4. 数字(登记序号)与身高/BMI 的相关(是否按体型/年龄登记?) =====")
for col in ["height(cm)","BMI"]:
    d=df.dropna(subset=[col,"Num"])
    print(f"  Num vs {col}: Spearman rho={d['Num'].corr(d[col],method='spearman'):+.3f}")

print("\n===== 5. 和论文1 对照 =====")
print(f"  性别: 男={int(df['male'].sum())} 女={int((1-df['male']).sum())}  (论文1: 29男/21女, N=50)")
na=df.dropna(subset=["ADHD"])
mA=na[na.male==1]["ADHD"].sum(); fA=na[na.male==0]["ADHD"].sum()
mN=(na.male==1).sum(); fN=(na.male==0).sum()
print(f"  ADHD: 男 {int(mA)}/{mN}={mA/mN*100:.1f}%  女 {int(fA)}/{fN}={fA/fN*100:.1f}%  合计 {int(na['ADHD'].sum())}")
print(f"        (论文1: 男37.9% 女9.5% 合计13)")
print(f"  BMI 全体 mean={df['BMI'].mean():.2f} sd={df['BMI'].std(ddof=1):.2f}  (论文1: 16.57±2.69)")
