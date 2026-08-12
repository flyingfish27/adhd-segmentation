# -*- coding: utf-8 -*-
# =============================================================================
# 71a_kgrid_plot.py -- draw the K-grid baseline curves (user request
# 2026-08-12: "三条线代表三个模型，横轴是 K").
#
# Input : analysis/kgrid_baseline_bin.csv (written by 71_kgrid_baseline.py)
# Output: outputs/figures/kgrid_baseline_bacc_curves.png
#
# One panel per binary target (sorted by that target's peak balanced accuracy,
# strongest first), three fixed-color lines per panel (logit / svm / rf --
# color follows the model everywhere), x = K on a log2 axis because every
# interesting optimum sits at small K, y = balanced accuracy with the 0.5
# chance line drawn.  A dot marks each model's best K in the panel; only the
# panel's single best cell gets a text label (selective labeling).
# Palette: first three categorical slots of the dataviz reference palette,
# validated all-pairs (CVD dE 9.2, normal 27.6, script run 2026-08-12).
# Reproduce with: .venv/bin/python analysis/71a_kgrid_plot.py
# =============================================================================
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "outputs" / "figures" / "kgrid_baseline_bacc_curves.png"

COLORS = {"logit": "#2a78d6", "svm": "#eb6834", "rf": "#1baf7a"}
INK, MUTED = "#1a1a19", "#6b6a63"

r = pd.read_csv(ROOT / "analysis" / "kgrid_baseline_bin.csv")
targets = (r.groupby("target")["bacc"].max()
             .sort_values(ascending=False).index.tolist())

fig, axes = plt.subplots(2, 5, figsize=(16, 7.2), sharex=True, sharey=True)
fig.patch.set_facecolor("#fcfcfb")
for ax, t in zip(axes.ravel(), targets):
    sub = r[r["target"] == t]
    best_cell = sub.loc[sub["bacc"].idxmax()]
    for m in ("logit", "svm", "rf"):
        s = sub[sub["model"] == m].sort_values("k")
        ax.plot(s["k"], s["bacc"], color=COLORS[m], lw=1.6, alpha=0.9,
                solid_joinstyle="round")
        b = s.loc[s["bacc"].idxmax()]
        ax.plot(b["k"], b["bacc"], "o", color=COLORS[m], ms=4.5, zorder=5)
    ax.axhline(0.5, color=MUTED, lw=0.8, ls=(0, (4, 3)), zorder=1)
    ax.set_xscale("log", base=2)
    ax.set_xticks([1, 4, 16, 64, 256])
    ax.set_xticklabels(["1", "4", "16", "64", "256"])
    ax.set_ylim(0.25, 0.92)
    ax.set_title(t.replace("__qbin", ""), fontsize=10, color=INK, pad=4)
    ax.annotate(f"best: {best_cell['model']} k={int(best_cell['k'])} "
                f"bacc={best_cell['bacc']:.3f}",
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
    ax.set_ylabel("balanced accuracy (LOO)", fontsize=9, color=INK)

handles = [plt.Line2D([], [], color=COLORS[m], lw=2, label=m)
           for m in ("logit", "svm", "rf")]
fig.legend(handles=handles, loc="upper right", ncol=3, frameon=False,
           bbox_to_anchor=(0.99, 1.0), fontsize=10)
fig.suptitle("K-grid screen: balanced accuracy vs K, 512-column keep-list "
             "(LOO, no permutations; max-over-grid is selection-biased)",
             x=0.01, ha="left", fontsize=12, color=INK)
fig.text(0.01, 0.945, "panels sorted by peak bacc; dashed line = chance (0.5); "
         "dots = each model's best K", fontsize=9, color=MUTED)
fig.tight_layout(rect=(0, 0, 1, 0.93))
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=150, facecolor=fig.get_facecolor())
print(f"written: {OUT.relative_to(ROOT)}")
