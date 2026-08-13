# -*- coding: utf-8 -*-
# =============================================================================
# 73a_reg_kgrid_plot.py -- the regression sweep drawn for model selection
# (FS-D10 step: user picks the regression model from these curves).
#
# Input : analysis/kgrid_reg.csv (written by 73_reg_kgrid.py)
# Output: outputs/figures/kgrid_reg_skill_curves.png
#
# One panel per continuous target, three model lines (ridge/svr/rf), x = K on
# log2, y = skill = 1 - RMSE/dummy-RMSE (0 = predicting the mean; negative =
# worse than the mean).  Same design family and palette as the earlier sweep
# figures; model colors parallel the classification figure (linear model
# blue, kernel model orange, forest green).  Panels sorted by peak skill.
# Reproduce with: .venv/bin/python analysis/73a_reg_kgrid_plot.py
# =============================================================================
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "outputs" / "figures" / "kgrid_reg_skill_curves.png"

COLORS = {"ridge": "#2a78d6", "svr": "#eb6834", "rf": "#1baf7a"}
INK, MUTED = "#1a1a19", "#6b6a63"

r = pd.read_csv(ROOT / "analysis" / "kgrid_reg.csv")
targets = (r.groupby("target")["skill"].max()
             .sort_values(ascending=False).index.tolist())

fig, axes = plt.subplots(2, 5, figsize=(16, 7.2), sharex=True, sharey=True)
fig.patch.set_facecolor("#fcfcfb")
for ax, t in zip(axes.ravel(), targets):
    sub = r[r["target"] == t]
    best_cell = sub.loc[sub["skill"].idxmax()]
    for m in ("ridge", "svr", "rf"):
        s = sub[sub["model"] == m].sort_values("k")
        ax.plot(s["k"], s["skill"], color=COLORS[m], lw=1.6, alpha=0.9)
        b = s.loc[s["skill"].idxmax()]
        ax.plot(b["k"], b["skill"], "o", color=COLORS[m], ms=4.5, zorder=5)
    ax.axhline(0.0, color=MUTED, lw=0.8, ls=(0, (4, 3)), zorder=1)
    ax.set_xscale("log", base=2)
    ax.set_xticks([1, 4, 16, 64, 256])
    ax.set_xticklabels(["1", "4", "16", "64", "256"])
    ax.set_ylim(-0.55, 0.42)
    ax.set_title(t, fontsize=10, color=INK, pad=4)
    ax.annotate(f"best: {best_cell['model']} k={int(best_cell['k'])} "
                f"skill={best_cell['skill']:+.3f}",
                xy=(0.03, 0.03), xycoords="axes fraction",
                fontsize=7.5, color=MUTED)
    ax.grid(axis="y", color="#e8e7e0", lw=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=8)
for ax in axes[1]:
    ax.set_xlabel("K (features selected per fold)", fontsize=9, color=INK)
for ax in axes[:, 0]:
    ax.set_ylabel("skill (0 = predict the mean)", fontsize=9, color=INK)

handles = [plt.Line2D([], [], color=c, lw=2, label=m)
           for m, c in COLORS.items()]
fig.legend(handles=handles, loc="upper right", ncol=3, frameon=False,
           bbox_to_anchor=(0.99, 1.0), fontsize=10)
fig.suptitle("Regression K-grid: skill vs K, 512-column keep-list "
             "(LOO, no permutations; max-over-grid is selection-biased)",
             x=0.01, ha="left", fontsize=12, color=INK)
fig.text(0.01, 0.945, "panels sorted by peak skill; dashed line = dummy "
         "(mean) baseline; dots = each model's best K", fontsize=9,
         color=MUTED)
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig(OUT, dpi=150, facecolor=fig.get_facecolor())
print(f"written: {OUT.relative_to(ROOT)}")
