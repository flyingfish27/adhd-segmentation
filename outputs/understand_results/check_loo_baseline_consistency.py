#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检验 A_univariate.csv 里 LOOCV 指标是否自洽。

前提(由 analysis/44_univariate_screen.py 的 loo_simple_lr() 定义,
见该函数内 `base=(y-y.mean())*n/(n-1)` 那两行):
  对同一个 target,608 个 feature 共用同一个 leave-one-out dummy baseline
  (= 留一均值预测)。记 ss 为特征模型的 PRESS,ss0 为 baseline 的 PRESS,n=24:
      loo_rmse = sqrt(ss  / n)
      loo_r2cv = 1 - ss / ss0
  =>  RMSE_baseline = sqrt(ss0 / n) = loo_rmse / sqrt(1 - loo_r2cv)
  该式与 feature 无关,故同一 target 的 608 行必须反推出同一个数。

本脚本做两件事:
  [1] 逐 target 反推 608 个 baseline RMSE,报告其离散程度;
  [2] 独立交叉验证:直接从 analysis/targets.csv 的真值 y 算
      RMSE_baseline = sqrt( mean( ((y_i - ȳ) * n/(n-1))^2 ) ),
      与 [1] 的反推值比对。[1] 只证明 CSV 内部自洽,[2] 才证明它算的是那个 baseline。

输入(两者均已入版本控制,可在 worktree 里直接跑,不需要 ADHD_ROOT):
  analysis/A_univariate.csv
  analysis/targets.csv
输出:只打 stdout,不写盘。
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
A_PATH = ROOT / "analysis" / "A_univariate.csv"
Y_PATH = ROOT / "analysis" / "targets.csv"

pd.set_option("display.width", 200)

a = pd.read_csv(A_PATH)
y_df = pd.read_csv(Y_PATH).set_index("subject")
n = len(y_df)

print(f"A_univariate.csv : {A_PATH}   rows={len(a)}")
print(f"targets.csv      : {Y_PATH}   n_subjects={n}")
print()

# ---- 行的分层:哪些行有 LOOCV 指标 ----
has_loo = a["loo_r2cv"].notna() & a["loo_rmse"].notna()
print("[0] 行的分层")
print(f"    总行数                  : {len(a)}")
print(f"    loo_r2cv/loo_rmse 均非空: {int(has_loo.sum())}")
print(f"    两列均为空              : {int((a['loo_r2cv'].isna() & a['loo_rmse'].isna()).sum())}")
print(f"    仅其一为空(异常)        : "
      f"{int((a['loo_r2cv'].isna() ^ a['loo_rmse'].isna()).sum())}")
print("    按 type 计:")
print(a.assign(has_loo=has_loo).groupby("type")["has_loo"]
      .agg(rows="size", with_loo="sum").to_string())
print()

cont = a[has_loo].copy()

# ---- 反推 baseline RMSE ----
denom = 1.0 - cont["loo_r2cv"]
bad = denom <= 0
if bad.any():
    print(f"!! 有 {int(bad.sum())} 行 1-loo_r2cv <= 0,无法反推,已剔除并单列如下:")
    print(cont.loc[bad, ["target", "feature", "loo_r2cv", "loo_rmse"]].to_string(index=False))
    print()
cont = cont[~bad]
cont["baseline_rmse_implied"] = cont["loo_rmse"] / np.sqrt(1.0 - cont["loo_r2cv"])

# ---- [1] 逐 target 的离散程度 ----
g = cont.groupby("target")["baseline_rmse_implied"]
summ = pd.DataFrame({
    "n_rows": g.size(),
    "min": g.min(),
    "max": g.max(),
    "median": g.median(),
    "std": g.std(),
})
summ["max-min"] = summ["max"] - summ["min"]
summ["rel_spread"] = summ["max-min"] / summ["median"]   # 相对极差
summ = summ.sort_values("rel_spread", ascending=False)

print("[1] 逐 target:608 行反推出的 baseline RMSE 的离散程度")
print("    rel_spread = (max-min)/median。若各行一致,应在 float 舍入量级(~1e-15)。")
print(summ.to_string(float_format=lambda v: f"{v:.6e}"))
print()

# ---- [2] 独立交叉验证:直接从 y 算真值 ----
print("[2] 独立交叉验证:直接由 targets.csv 的 y 计算 baseline RMSE")
print("    truth = sqrt( mean( ((y - mean(y)) * n/(n-1))^2 ) ),n =", n)
rows = []
for tgt in summ.index:
    if tgt not in y_df.columns:
        rows.append({"target": tgt, "note": "targets.csv 无此列", "truth": np.nan,
                     "implied_median": summ.loc[tgt, "median"], "rel_err": np.nan,
                     "n_nonnull_y": np.nan})
        continue
    y = y_df[tgt].to_numpy(dtype=float)
    n_ok = int(np.isfinite(y).sum())
    base = (y - np.nanmean(y)) * n / (n - 1)
    truth = float(np.sqrt(np.nanmean(base ** 2)))
    implied = float(summ.loc[tgt, "median"])
    rows.append({"target": tgt, "n_nonnull_y": n_ok, "truth": truth,
                 "implied_median": implied,
                 "rel_err": abs(implied - truth) / truth if truth > 0 else np.nan,
                 "note": ""})
cross = pd.DataFrame(rows).set_index("target")
print(cross.to_string(float_format=lambda v: f"{v:.6e}"))
print()

# ---- 结论行(只报可观测事实) ----
worst_rel = summ["rel_spread"].max()
worst_tgt = summ["rel_spread"].idxmax()
print("[3] 可观测结果")
print(f"    同一 target 内反推值的最大相对极差: {worst_rel:.3e}  (target = {worst_tgt})")
if cross["rel_err"].notna().any():
    wc = cross["rel_err"].idxmax()
    print(f"    反推值 vs 由 y 直算的真值,最大相对误差: "
          f"{cross['rel_err'].max():.3e}  (target = {wc})")
print(f"    参考量级: float64 eps = {np.finfo(float).eps:.3e}")
