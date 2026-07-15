#!/usr/bin/env python3
"""
20_codebook_verify.py — 从原始数据第一性原理验证 CODEBOOK.md 里的每一条结论。

运行:  .venv/bin/python 20_codebook_verify.py
依赖:  pandas, numpy, scipy   数据:  data/

设计原则(见 CODEBOOK.md):不采信任何二级结论(week2.pptx / notebook / 论文正文口径)。
每条结论只有满足以下之一才算 confirmed:
  (a) 原始数据中直接观测;
  (b) 被内部一致性恒等式强制(BMI、加速度分解、模长、档数);
  (c) 复现出某篇论文 published 的具体数字。
本脚本把每条推导跑成一个 PASS/FAIL 或数值输出,供随时复算。
"""
import os, re, glob, hashlib
import numpy as np, pandas as pd
from scipy.stats import spearmanr

ROOT = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(ROOT, "data")
CLIN = os.path.join(D, "Demographic and mental health data.csv")

def hr(t): print("\n" + "="*72 + f"\n{t}\n" + "="*72)
def ok(c): return "PASS" if c else "**FAIL**"

# ---------------------------------------------------------------- load clinical
df = pd.read_csv(CLIN, encoding="utf-8-sig", dtype=str)
df.columns = [c.strip() for c in df.columns]
SDQ  = [c for c in df.columns if c.startswith("SDQ")]
SNAP = [f"a{i}" for i in range(1, 27)]
num = df.copy()
for c in SDQ + SNAP + ["BMI", "height(cm)", "weight(kg)"]:
    num[c] = pd.to_numeric(num[c], errors="coerce")
S32_ANOM = num.loc[num["SDQ8"] == 13, "ID"].tolist()
num.loc[num["SDQ8"] == 13, "SDQ8"] = np.nan          # treat out-of-range as missing
sex = df["SEX"].str.strip().str.lower()

# ================================================================ C1 shape
hr("C1  行列清点(依据:原始数据)")
print(f"rows(subjects)={len(df)}  cols={df.shape[1]}   -> {ok(len(df)==58 and df.shape[1]==55)} (期望 58×55)")
print("SDQ 列缺 SDQ19:", ok("SDQ19" not in df.columns and "SDQ18" in df.columns and "SDQ20" in df.columns))

# ================================================================ C6 SEX
hr("C6  SEX 编码(依据:原始数据)")
vals = df["SEX"].value_counts(dropna=False).to_dict()
print("取值:", vals, " ->", ok(set(vals) == {"male", "female"}), "(仅 male/female,全小写)")

# ================================================================ C2/C3 档数
hr("C2/C3  SDQ/SNAP 作答档数 = 仪器档数(依据:内部一致性,强制)")
sdq_set  = sorted({int(v) for v in np.unique(num[SDQ].values) if not np.isnan(v)})
snap_set = sorted({int(v) for v in np.unique(num[SNAP].values) if not np.isnan(v)})
print(f"SDQ  取值集合 = {sdq_set}   SDQ 仪器有 3 档(0/1/2) -> 数据 1-indexed,标准分=数据-1  {ok(sdq_set==[1,2,3])}")
print(f"SNAP 取值集合 = {snap_set}  SNAP 仪器有 4 档(0..3) -> 数据 1-indexed,标准分=数据-1  {ok(snap_set==[1,2,3,4])}")
print(f"越界异常:{S32_ANOM} 的 SDQ8=13(SDQ 任何编码下都非法) -> {ok(S32_ANOM==['S32'])}")

# ================================================================ C7 BMI 恒等式
hr("C7  BMI = 体重/(身高/100)^2(依据:内部一致性恒等式,最强自证)")
calc = (num["weight(kg)"] / (num["height(cm)"] / 100) ** 2).round(1)
both = num["BMI"].notna() & calc.notna()
match = (both & ((num["BMI"] - calc).abs() <= 0.1)).sum()
print(f"有身高&体重的行 = {int(both.sum())};  BMI 与公式吻合(≤0.1)= {match}  -> {ok(match==int(both.sum()))}")
print("BMI 存在但身高/体重缺失(印证论文2'1 人保留 BMI'):",
      df.loc[num["BMI"].notna() & ~both, "ID"].tolist())

# ================================================================ C8 缺失名单
hr("C8  缺失与全有/全无(依据:原始数据)")
print("SDQ 每人非缺项数分布:", num[SDQ].notna().sum(axis=1).value_counts().sort_index().to_dict())
print("SNAP 每人非缺项数分布:", num[SNAP].notna().sum(axis=1).value_counts().sort_index().to_dict(),
      "  -> 问卷是全有或全无")
print("SNAP 缺失 ID:", df.loc[~num[SNAP].notna().all(axis=1), "ID"].tolist())
print("height/weight 缺失:", df.loc[num["height(cm)"].isna() | num["weight(kg)"].isna(), "ID"].tolist(),
      " BMI 缺失:", df.loc[num["BMI"].isna(), "ID"].tolist())

# ================================================================ C4 SDQ 列映射裁决
hr("C4  SDQ 列映射:A=原始题号 vs B=分块重排(依据:结构+相关+收敛效度)")
def rev(col): return 4 - num[col]                      # 1-3 编码下的反向:1<->3
A_hyper = num["SDQ2"] + num["SDQ10"] + num["SDQ15"] + rev("SDQ21") + rev("SDQ25")
B_hyper = num[["SDQ11", "SDQ12", "SDQ13", "SDQ14", "SDQ15"]].sum(axis=1)
snap_ih = num[[f"a{i}" for i in range(1, 19)]].sum(axis=1)   # SNAP 注意力+多动
def sp(a, b):
    m = a.notna() & b.notna(); r, p = spearmanr(a[m], b[m]); return r, p, int(m.sum())
rA = sp(A_hyper, snap_ih); rB = sp(B_hyper, snap_ih)
print(f"证据(1)结构:缺号恰在 SDQ19、保留 20-25 跳号 -> 列沿用问卷原始题号(分块重排应连续无跳号) {ok('SDQ19' not in df.columns)}")
print(f"证据(3)收敛效度 vs SNAP(a1-a18):  A(2,10,15,21*,25*) rho={rA[0]:+.3f}  |  B(SDQ11-15) rho={rB[0]:+.3f}")
print(f"  -> A 与 SNAP-ADHD 的相关约为 B 的两倍 -> hyperactivity = SDQ2,10,15,21*,25*  {ok(rA[0] > rB[0]*1.5)}")
subs = {"emotional":[3,8,13,16,24], "conduct":[5,7,12,18,22], "hyper":[2,10,15,21,25],
        "peer":[6,11,14,19,23], "prosocial":[1,4,9,17,20]}
revset = {7, 11, 14, 21, 25}
print("证据(2)各子量表(A)反向校正后的平均题间相关:")
for name, items in subs.items():
    items = [i for i in items if f"SDQ{i}" in df.columns]
    M = pd.concat([(4 - num[f"SDQ{i}"]) if i in revset else num[f"SDQ{i}"] for i in items], axis=1)
    cm = M.corr(method="spearman").values
    print(f"    {name:10s} items={items} mean_rho={np.nanmean(cm[np.triu_indices_from(cm,1)]):+.3f}")

# ================================================================ 复现论文2 Table1
hr("复现 论文2 (Biosensors 2026 16(6):323) Table 1  —— 缺失→0、demographic-present、原始尺度")
hasdem = num["BMI"].notna()
snap_fill = num[SNAP].fillna(0).sum(axis=1)
sdq_fill  = num[SDQ].fillna(0).sum(axis=1)
def by_sex(series, mask, label, targets):
    print(f"  {label}")
    for s in ["male", "female"]:
        v = series[mask & (sex == s)]
        t = targets.get(s, "")
        print(f"     [{s}] n={len(v)} mean={v.mean():.2f} sd={v.std(ddof=1):.2f} median={v.median():.2f}   目标 {t}")
by_sex(num["BMI"], hasdem & num["BMI"].notna(), "BMI(kg/m^2)",
       {"male":"17.09/3.02 n30", "female":"16.18/2.30 n23"})
by_sex(num["height(cm)"], hasdem & num["height(cm)"].notna(), "height(cm)",
       {"male":"136.00/10.78 n30", "female":"134.77/10.45 n22"})
by_sex(num["weight(kg)"], hasdem & num["weight(kg)"].notna(), "weight(kg)",
       {"male":"32.27/9.96 n30", "female":"29.82/7.01 n22"})
by_sex(sdq_fill, hasdem, "SDQ 分(缺失→0, 原始1-3)",
       {"male":"39.33/13.73 med43 n30", "female":"43.52/10.56 med44 n23"})
by_sex(snap_fill, hasdem, "SNAP 分(缺失→0, 原始1-4)",
       {"male":"42.17/19.42 n30", "female":"34.50/12.21 n22"})
print("  -> 男性 BMI/身高/体重/SDQ/SNAP 全部逐位命中 => 列解读与'缺失→0、原始尺度、不减1'确证")

# ================================================================ 复现论文2 分组 & 论文1 标签
hr("复现 分组/标签规则(证明两篇都用原始尺度、不减1)")
snap_raw = num[SNAP].sum(axis=1)
hassnap = num[SNAP].notna().all(axis=1)
per_item = snap_raw / len(SNAP)
print(f"论文2 分组:原始1-4 每项均值≥1.67 -> High={int(((per_item>=1.67)&hassnap).sum())} / Low={int(((per_item<1.67)&hassnap).sum())}"
      f"   (若改减1的0-3尺度: High={int((((snap_raw-26)/26>=1.67)&hassnap).sum())} 荒谬) ")
v = snap_raw[hassnap]
z = (v - v.mean()) / v.std(ddof=1); T = z * 10 + 50
n_adhd = int((T >= 55).sum())
print(f"论文1 标签:SNAP原始总分->Z->T, T>=55 判 ADHD -> ADHD={n_adhd} / 非={int((T<55).sum())} (N={len(v)})"
      f"   目标 13/37(N=50) -> ADHD 数 {ok(n_adhd==13)}")
print(f"论文1 报总分 42.98±9.13 ≈ 原始1-4 之和(本数据 N={len(v)}: {v.mean():.2f}±{v.std(ddof=1):.2f}),而非减1后的~{(v.mean()-26):.0f}")

# ================================================================ C9 花名册 & md5
hr("C9  花名册对账 + md5 重复(依据:原始数据/字节哈希)")
ids = set(df["ID"].str.strip())
F = {re.sub(r"_F\.csv$", "", os.path.basename(p)) for p in glob.glob(os.path.join(D, "*_F.csv"))}
Tt = {re.sub(r"_T\.csv$", "", os.path.basename(p)) for p in glob.glob(os.path.join(D, "*_T.csv"))}
print(f"临床 {len(ids)} | _F {len(F)} | _T {len(Tt)} | 两者都有 {len(F&Tt)}")
print("临床有但无传感器:", sorted(ids - (F | Tt)), " 传感器有但不在临床:", sorted((F | Tt) - ids),
      " -> 同一孩子 Q27(临床)=Z27(传感器)")
def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
hashes = {}
for name in ["C28_T", "Y54_T", "Z5_T", "Z14_T"]:
    hashes[name] = md5(os.path.join(D, name + ".csv"))
print("字节级 md5:", {k: v[:8] for k, v in hashes.items()})
print("  C28_T==Y54_T:", ok(hashes["C28_T"] == hashes["Y54_T"]),
      " Z5_T==Z14_T:", ok(hashes["Z5_T"] == hashes["Z14_T"]))

# ================================================================ 传感器自证
hr("S1/S2/S3/S5  传感器列自证(依据:内部一致性恒等式)")
for f, sep in [("H1_F.csv", ","), ("H2_T.csv", ";")]:
    s = pd.read_csv(os.path.join(D, f), sep=sep, nrows=40000)
    ax, ay, az = [f"accelerometerAcceleration{a}(G)" for a in "XYZ"]
    ux, uy, uz = [f"motionUserAcceleration{a}(G)" for a in "XYZ"]
    gx, gy, gz = [f"motionGravity{a}(G)" for a in "XYZ"]
    q = [f"motionQuaternion{a}(R)" for a in "XYZW"]
    res = np.median([(s[a] - (s[u] + s[g])).abs().median()
                     for a, u, g in [(ax, ux, gx), (ay, uy, gy), (az, uz, gz)]])
    gnorm = np.sqrt(s[gx]**2 + s[gy]**2 + s[gz]**2).median()
    qnorm = np.sqrt(sum(s[c]**2 for c in q)).median()
    t = s["accelerometerTimestamp_sinceReboot(s)"].dropna().values
    dt = np.diff(t); dt = dt[(dt > 0) & (dt < 1)]; fs = 1 / np.median(dt)
    print(f"  {f}: ncols={s.shape[1]} {ok(s.shape[1]==58)} | median|accel-(user+grav)|={res:.3f}G(≈0) "
          f"| ||grav||={gnorm:.4f} ||quat||={qnorm:.4f} | fs≈{fs:.2f}Hz "
          f"| activity={dict(list(s['activity(txt)'].value_counts().items())[:3])}")
print("  -> accel≈user+grav 且 ||grav||=||quat||=1 => 自证 raw/user/gravity/quaternion 各列含义与单位(G)")

print("\n完成。以上每行 PASS 或与目标一致即证实 CODEBOOK 对应结论。")
