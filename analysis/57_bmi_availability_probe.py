# -*- coding: utf-8 -*-
# =============================================================================
# 57_bmi_availability_probe.py  —  体质指数(BMI)在 24 个建模样本里到底有多少、长什么样
# =============================================================================
# 这是什么(给未来任何一个不了解本项目的人):
#   这个文件【不是】生产管线的一部分,不产生任何特征、不写任何文件。
#   它是一只【探针(probe)】——把几个数字摊开供人拍板,跑完只在终端打印。
#   "探针"是本项目里一类脚本的固定叫法(见 analysis/32_、50_、51_、52_、53_、54_)。
#
# 只读:data/Demographic and mental health data.csv(原始临床问卷表)
#       + figures/subject_audit.csv(哪 24 个人进建模)
#       + analysis/targets.csv(10 个症状分)
#       + analysis/features.csv(351 个运动特征,用于看 BMI 与特征的相关)
#   不写盘。
#
# 它回答什么:
#   TASK-105 要"把 BMI 作为探索性协变量纳入分析"。条目只有一句话,没写死实现方式,
#   也没写死缺失值怎么处理。要拍板得先知道三件事,本探针就测这三件:
#     ① 24 个建模样本里【实际】有几个人有 BMI?缺的是哪几个人?
#        (CODEBOOK.md §缺失 记的是"BMI 缺 5"——但那是【整张临床表】的口径,
#         整张表有 55 行而建模只用 24 人,两个口径的缺失人数【不是同一个数】。)
#     ② BMI 自己与 10 个症状分有没有关系?——这决定了把它当【自变量】看有没有名堂。
#     ③ BMI 与 351 个运动特征、与负对照 uaMag_median 有没有关系?——这决定了把它当
#        【协变量】控制掉会不会改变结论:若 BMI 与特征基本无关,控制它等于什么都没做。
#
# 口径说明:
#   · 相关一律用 Spearman 秩相关(与 A 轨 analysis/44_univariate_screen.py 口径一致)。
#   · BMI 直接取原始表的 BMI 列,不重算。CODEBOOK.md §2 已实证 BMI = weight/(height/100)²
#     在全部 52 个有身高体重的行上吻合(误差≤0.1),故该列自证即 BMI。
#   · 缺失只报事实(谁缺、缺几个),【不】在本探针里做任何填补——怎么处理是待拍板的决策点。
#
# 复现:
#   ADHD_ROOT=<有 data/ 的仓库根> .venv/bin/python analysis/57_bmi_availability_probe.py
# =============================================================================
import os, sys, pathlib
import numpy as np, pandas as pd
from scipy.stats import spearmanr

HERE = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path(os.environ.get("ADHD_ROOT", HERE.parent)).resolve()
if not (ROOT / "data").is_dir():
    sys.exit(f"找不到 {ROOT}/data —— 请把环境变量 ADHD_ROOT 指向有 data/ 的主检出。")

def banner(title, *notes):
    print("\n" + "#" * 80)
    print(f"# {title}")
    for n in notes:
        print(f"#   {n}")
    print("#" * 80)

pd.set_option("display.width", 200)

# ---------------------------------------------------------------- 读入
clin = pd.read_csv(ROOT / "data/Demographic and mental health data.csv",
                   encoding="utf-8-sig", dtype=str)
clin.columns = [c.strip() for c in clin.columns]
aud = pd.read_csv(ROOT / "figures/subject_audit.csv")
SUBJ = sorted(aud[(aud.status == "usable")
                  & (aud["_T"].astype(str).str.lower() == "yes")].subject.tolist())
assert len(SUBJ) == 24, f"建模样本应为 24 人,实得 {len(SUBJ)}"

clin = clin.set_index("ID")
for c in ["BMI", "height(cm)", "weight(kg)"]:
    clin[c] = pd.to_numeric(clin[c], errors="coerce")

Y = pd.read_csv(ROOT / "analysis/targets.csv").set_index("subject")
F_PATH = ROOT / "analysis/features.csv"
X = pd.read_csv(F_PATH).set_index("subject") if F_PATH.exists() else None

# =============================================================================
banner("探针1  BMI 在整张临床表 vs 在 24 个建模样本里的可得性",
       "两个口径必须分清:CODEBOOK.md 记的『BMI 缺 5』是整张表的口径,不是建模样本的口径")

print(f"\n  整张临床表行数 = {len(clin)}")
for c in ["BMI", "height(cm)", "weight(kg)"]:
    print(f"    {c:12} 有值 {clin[c].notna().sum():3d} 缺失 {clin[c].isna().sum():3d}")

sub = clin.loc[SUBJ]
print(f"\n  24 个建模样本(figures/subject_audit.csv 里 status=usable 且 _T=yes 的人):")
for c in ["BMI", "height(cm)", "weight(kg)"]:
    miss = sorted(sub.index[sub[c].isna()].tolist())
    print(f"    {c:12} 有值 {sub[c].notna().sum():3d} 缺失 {sub[c].isna().sum():3d}"
          f"  缺失者: {miss if miss else '无'}")

print("\n  24 人逐行明细(BMI / 身高 / 体重 / 性别):")
det = sub[["SEX", "BMI", "height(cm)", "weight(kg)"]].copy()
print(det.to_string())

bmi = sub["BMI"].astype(float)
ok = bmi.notna()
print(f"\n  有 BMI 的 {ok.sum()} 人的分布:")
print(f"    最小 {bmi.min():.2f}  25分位 {bmi.quantile(.25):.2f}  中位 {bmi.median():.2f}"
      f"  75分位 {bmi.quantile(.75):.2f}  最大 {bmi.max():.2f}  均值 {bmi.mean():.2f}")

# 缺失是否与性别有关(缺失机制的一个最起码的检查)
print("\n  BMI 缺失 × 性别列联(看缺失是不是集中在某一性别):")
print(pd.crosstab(sub["SEX"], bmi.isna().map({True: "BMI缺失", False: "BMI有值"})).to_string())

# =============================================================================
banner("探针2  BMI 自己与 10 个症状分的秩相关",
       "这回答『把 BMI 当自变量看』有没有名堂;n = 有 BMI 的人数,不是 24",
       "未做任何多重比较校正——这里是 10 个检验,p<0.05 里约有 0.5 个是纯噪声期望")

rows = []
for t in Y.columns:
    y = Y.loc[SUBJ, t].astype(float)
    m = ok & y.notna()
    if m.sum() < 4:
        rows.append({"目标": t, "n": int(m.sum()), "rho": np.nan, "p": np.nan})
        continue
    r, p = spearmanr(bmi[m], y[m])
    rows.append({"目标": t, "n": int(m.sum()), "rho": round(float(r), 3),
                 "p": round(float(p), 4)})
tb = pd.DataFrame(rows).sort_values("rho", key=lambda s: s.abs(), ascending=False)
print()
print(tb.to_string(index=False))
print(f"\n  |rho| 最大者: {tb.iloc[0]['目标']}  rho={tb.iloc[0]['rho']}  p={tb.iloc[0]['p']}")
print(f"  未校正 p<0.05 的目标数: {(tb['p'] < 0.05).sum()} / {len(tb)}"
      f"  (纯噪声下的期望 = 0.05 × {len(tb)} = {0.05*len(tb):.1f})")

# =============================================================================
banner("探针3  BMI 与运动特征的秩相关",
       "这回答『把 BMI 当协变量控制掉』会不会改变结论:",
       "若 BMI 与特征基本无关,控制它在数学上近乎不做任何事(偏相关≈原相关)")

if X is None:
    print(f"\n  跳过:{F_PATH} 不存在。该文件是 42_features_full.py 的产物、未入版本控制,")
    print("  在干净 checkout / worktree 上没有。请把 ADHD_ROOT 指向有它的仓库根。")
else:
    Xs = X.loc[SUBJ]
    print(f"\n  特征表 {F_PATH.name}: {Xs.shape[0]} 人 × {Xs.shape[1]} 列")
    rs = {}
    for c in Xs.columns:
        v = Xs[c].astype(float)
        m = ok & v.notna()
        if m.sum() < 4 or v[m].nunique() < 2:
            continue
        rs[c] = float(spearmanr(bmi[m], v[m]).correlation)
    s = pd.Series(rs).dropna()
    a = s.abs()
    print(f"    可算相关的列数 {len(s)}")
    print(f"    |rho| 中位 {a.median():.3f}  75分位 {a.quantile(.75):.3f}  最大 {a.max():.3f}")
    for thr in (0.3, 0.4, 0.5):
        print(f"    |rho| > {thr}: {(a > thr).sum()} 列")
    print("\n    与 BMI 相关最强的 10 列:")
    top = s.reindex(a.sort_values(ascending=False).index).head(10)
    for k, v in top.items():
        print(f"      {k:28} {v:+.3f}")

    if "uaMag_median" in Xs.columns:
        v = Xs["uaMag_median"].astype(float); m = ok & v.notna()
        r, p = spearmanr(bmi[m], v[m])
        print(f"\n    负对照 uaMag_median(运动总量)× BMI: rho={r:+.3f}  p={p:.4f}  n={m.sum()}")

    # 路径B的 45 列(TASK-106 偏相关的对象)单独看一眼
    PB = [c for c in Xs.columns if any(c.startswith(p + "_p") for p in
          ("actfrac", "switchmin", "actbout_med", "actbout_cv", "actshort"))]
    if PB:
        ab = s.reindex(PB).dropna().abs()
        print(f"\n    其中『路径B』那 {len(PB)} 列与 BMI 的 |rho|:"
              f" 中位 {ab.median():.3f} 最大 {ab.max():.3f}")

print("\n" + "=" * 80)
print("探针结束。本脚本未写任何文件。")
