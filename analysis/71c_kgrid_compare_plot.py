# -*- coding: utf-8 -*-
# =============================================================================
# 71c_kgrid_compare_plot.py -- F-test vs MI-z selector, one panel per target
# (user request 2026-08-12: "先给我图我看看" after the FS-D6 comparison).
#
# Inputs : analysis/kgrid_baseline_bin.csv (F-test sweep, 71_)
#          analysis/kgrid_mi_bin.csv       (MI-z sweep, 71b_)
# Output : outputs/figures/kgrid_f_vs_mi_bacc.png
#
# Each panel shows, per selector, the ENVELOPE over the three models: at every
# K the best balanced accuracy any of logit/svm/rf reaches.  That is itself a
# max (stated on the figure); the per-model curves live in the two CSVs.
# Panel order matches outputs/figures/kgrid_baseline_bacc_curves.png (sorted
# by the F-test peak) so the two figures can be read side by side.
# Colors: categorical slots 1-2 of the validated reference palette.
# Reproduce with: .venv/bin/python analysis/71c_kgrid_compare_plot.py
# =============================================================================
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "outputs" / "figures" / "kgrid_f_vs_mi_bacc.png"

COLORS = {"F-test": "#2a78d6", "MI-z": "#eb6834"}
INK, MUTED = "#1a1a19", "#6b6a63"

f = pd.read_csv(ROOT / "analysis" / "kgrid_baseline_bin.csv")
m = pd.read_csv(ROOT / "analysis" / "kgrid_mi_bin.csv")
env = {"F-test": f.groupby(["target", "k"])["bacc"].max().reset_index(),
       "MI-z": m.groupby(["target", "k"])["bacc"].max().reset_index()}
targets = (f.groupby("target")["bacc"].max()
             .sort_values(ascending=False).index.tolist())

fig, axes = plt.subplots(2, 5, figsize=(16, 7.2), sharex=True, sharey=True)
fig.patch.set_facecolor("#fcfcfb")
for ax, t in zip(axes.ravel(), targets):
    peaks = {}
    for sel, df in env.items():
        s = df[df["target"] == t].sort_values("k")
        ax.plot(s["k"], s["bacc"], color=COLORS[sel], lw=1.7, alpha=0.9)
        b = s.loc[s["bacc"].idxmax()]
        peaks[sel] = b
        ax.plot(b["k"], b["bacc"], "o", color=COLORS[sel], ms=4.5, zorder=5)
    ax.axhline(0.5, color=MUTED, lw=0.8, ls=(0, (4, 3)), zorder=1)
    ax.set_xscale("log", base=2)
    ax.set_xticks([1, 4, 16, 64, 256])
    ax.set_xticklabels(["1", "4", "16", "64", "256"])
    ax.set_ylim(0.3, 0.92)
    ax.set_title(t.replace("__qbin", ""), fontsize=10, color=INK, pad=4)
    ax.annotate(f"F {peaks['F-test']['bacc']:.3f} (k={int(peaks['F-test']['k'])})"
                f"  ·  MI {peaks['MI-z']['bacc']:.3f} (k={int(peaks['MI-z']['k'])})",
                xy=(0.03, 0.03), xycoords="axes fraction",
                fontsize=7.3, color=MUTED)
    ax.grid(axis="y", color="#e8e7e0", lw=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=8)
for ax in axes[1]:
    ax.set_xlabel("K (features selected per fold)", fontsize=9, color=INK)
for ax in axes[:, 0]:
    ax.set_ylabel("balanced accuracy (LOO)", fontsize=9, color=INK)

handles = [plt.Line2D([], [], color=c, lw=2, label=s) for s, c in COLORS.items()]
fig.legend(handles=handles, loc="upper right", ncol=2, frameon=False,
           bbox_to_anchor=(0.99, 1.0), fontsize=10)
fig.suptitle("Selector comparison: F-test vs permutation-z mutual information "
             "(per-K envelope over the three models; exploration numbers)",
             x=0.01, ha="left", fontsize=12, color=INK)
fig.text(0.01, 0.945, "each line = best bacc among logit/svm/rf at that K; "
         "panels sorted by F-test peak; dashed = chance; dots = each "
         "selector's best K", fontsize=9, color=MUTED)
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig(OUT, dpi=150, facecolor=fig.get_facecolor())
print(f"written: {OUT.relative_to(ROOT)}")
