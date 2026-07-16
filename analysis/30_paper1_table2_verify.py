#!/usr/bin/env python3
"""
30_paper1_table2_verify.py — 逐行复算论文1 (Wang, Sensors 2025 25(20):6459) 3.1 节 Table 2。

运行:  .venv/bin/python analysis/30_paper1_table2_verify.py

目的:对 Table 2 每一行,回答两个问题
  (1) 这个变量在公开数据(Zenodo 14875672)里到底存不存在?
  (2) 存在的,论文报的均值/SD/p 值能不能从原始数据复算出来?
只用原始 CSV,不采信论文文字口径。SNAP 子量表题号见 CODEBOOK §2.2。
"""
import os
import numpy as np, pandas as pd
from scipy.stats import ttest_ind, chi2_contingency

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIN = os.path.join(ROOT, "data", "Demographic and mental health data.csv")

df = pd.read_csv(CLIN, encoding="utf-8-sig", dtype=str)
df.columns = [c.strip() for c in df.columns]
sex = df["SEX"].str.strip().str.lower()

SNAP = [f"a{i}" for i in range(1, 27)]
num = df.copy()
for c in SNAP + ["BMI", "height(cm)", "weight(kg)"]:
    num[c] = pd.to_numeric(num[c], errors="coerce")

def hr(t): print("\n" + "=" * 74 + f"\n{t}\n" + "=" * 74)

# ---- SNAP 子量表(CODEBOOK §2.2,原始尺度 1-4,不减 1) ----
INATT = [f"a{i}" for i in range(1, 10)]    # 注意力缺陷 9 题
HYPER = [f"a{i}" for i in range(10, 19)]   # 多动/冲动 9 题
ODD   = [f"a{i}" for i in range(19, 27)]   # 对立违抗 8 题

# ================================================================ 0 哪些列存在
hr("0  Table 2 各变量在公开数据里是否存在(依据:CSV 列名)")
have = set(df.columns)
checklist = {
    "Age 年龄":            any(c.lower() in have for c in ["age", "Age"]),
    "Grade 年级":          any("grade" in c.lower() for c in have),
    "Health state 健康":   any("health" in c.lower() for c in have),
    "Diet state 饮食":     any("diet" in c.lower() for c in have),
    "Parental education":  any("parent" in c.lower() or "educat" in c.lower() for c in have),
    "BMI":                 "BMI" in have,
    "SEX 性别":            "SEX" in have,
    "SNAP-IV a1..a26":     all(c in have for c in SNAP),
}
for k, v in checklist.items():
    print(f"   {'存在 ' if v else '缺失*'}  {k}")
print("\n   实际列:", list(df.columns[:5]), "... + SDQ*/a* 问卷项")
print("   => 年龄/年级/健康/饮食/父母教育 5 个变量不在公开数据中,无法从原始数据复算")

# ================================================================ helper
def by_sex_cont(series, mask, target_total, target_m, target_f, p_paper):
    """连续变量:总体/男/女 的 mean±sd + Welch t 检验 p"""
    v  = series[mask]
    vm = series[mask & (sex == "male")]
    vf = series[mask & (sex == "female")]
    t, p = ttest_ind(vm.dropna(), vf.dropna(), equal_var=False)  # Welch
    print(f"   本数据: 总 n={v.notna().sum():2d} {v.mean():6.2f}±{v.std(ddof=1):.2f} | "
          f"男 n={vm.notna().sum():2d} {vm.mean():6.2f}±{vm.std(ddof=1):.2f} | "
          f"女 n={vf.notna().sum():2d} {vf.mean():6.2f}±{vf.std(ddof=1):.2f} | Welch p={p:.3f}")
    print(f"   论文报: 总    {target_total} | 男 {target_m} | 女 {target_f} | p={p_paper}")

# ================================================================ SNAP 子量表 + 总分
# 论文 n=50。本数据有完整 SNAP 者 N=? 先按"完整 SNAP"子集算(与论文标签口径一致)
hassnap = num[SNAP].notna().all(axis=1)
print(f"\n完整 SNAP 应答者: N={int(hassnap.sum())} (男 {int((hassnap&(sex=='male')).sum())}, "
      f"女 {int((hassnap&(sex=='female')).sum())})   论文称 N=50 (男29/女21)")

hr("1  SNAP-IV 注意力缺陷 Inattention (a1-a9)  —— 论文 Table 2")
by_sex_cont(num[INATT].sum(axis=1), hassnap, "15.76±4.11", "16.93±4.02", "14.14±3.76", "0.01")

hr("2  SNAP-IV 多动/冲动 Hyperactivity (a10-a18)  —— 论文 Table 2")
by_sex_cont(num[HYPER].sum(axis=1), hassnap, "13.80±3.42", "14.72±3.39", "12.52±3.09", "0.02")

hr("3  SNAP-IV 对立违抗 Oppositional (a19-a26)  —— 论文 Table 2")
by_sex_cont(num[ODD].sum(axis=1), hassnap, "13.60±2.60", "14.24±2.84", "12.71±1.95", "0.02")

hr("4  SNAP-IV 总分 Total (a1-a26)  —— 论文 Table 2")
by_sex_cont(num[SNAP].sum(axis=1), hassnap, "42.98±9.13", "45.69±9.23", "39.24±7.72", "0.01")

hr("5  BMI  —— 论文 Table 2 (总 16.57±2.69, 男 16.93±2.95, 女 16.07±2.25, p=0.24)")
print("   [完整 SNAP 子集]")
by_sex_cont(num["BMI"], hassnap, "16.57±2.69", "16.93±2.95", "16.07±2.25", "0.24")
print("   [有 BMI 的全部行]")
by_sex_cont(num["BMI"], num["BMI"].notna(), "16.57±2.69", "16.93±2.95", "16.07±2.25", "0.24")

# ================================================================ ADHD 标签
hr("6  ADHD 分类 (SNAP 原始总分 -> Z -> T=Z*10+50, T>=55)  —— 论文 13/37")
v = num[SNAP].sum(axis=1)[hassnap]
z = (v - v.mean()) / v.std(ddof=1)
T = z * 10 + 50
adhd = T >= 55
s2 = sex[hassnap]
print(f"   本数据: ADHD={int(adhd.sum())} / 非ADHD={int((~adhd).sum())}  (N={len(v)})")
print(f"           男 ADHD {int((adhd&(s2=='male')).sum())}/{int((s2=='male').sum())} | "
      f"女 ADHD {int((adhd&(s2=='female')).sum())}/{int((s2=='female').sum())}")
print(f"   论文报: ADHD=13 / 非ADHD=37 (N=50) | 男 11/29 | 女 2/21")
# 性别 x ADHD 的卡方
ct = pd.crosstab(s2, adhd)
try:
    chi2, pc, _, _ = chi2_contingency(ct)
    print(f"   性别×ADHD 卡方 p={pc:.3f}  (论文报 p=0.02~0.04)")
except Exception as e:
    print("   卡方失败:", e)

print("\n完成。'缺失*' 的变量无法复算;其余对照论文数字判断吻合度。")
