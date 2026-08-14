# -*- coding: utf-8 -*-
# =============================================================================
# 74c_carrier_scatter.py -- the two carrier features, shown raw (presentation
# figure; user request 2026-08-14).
#
# Inputs : analysis/features.csv, analysis/targets.csv
# Output : outputs/figures/carrier_features_scatter.png
#
# Two panels, one per delivered carrier feature: x = the feature's raw value,
# y = the continuous symptom score it carries, 24 children as open circles.
# The dashed horizontal line is the median split that defines the delivered
# classification target.  Spearman rho is annotated as an in-sample,
# descriptive number (no test).  No jitter anywhere: the vertical stacking in
# the right panel IS the on-record caveat that act_bout_median_w0.5_p80 takes
# only four distinct values -- the audience is meant to see it.
# Reproduce with: .venv/bin/python analysis/74c_carrier_scatter.py
# =============================================================================
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import spearmanr

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "outputs" / "figures" / "carrier_features_scatter.png"
BLUE, INK, MUTED = "#2a78d6", "#1a1a19", "#6b6a63"

X = pd.read_csv(ROOT / "analysis/features.csv").set_index("subject")
Y = pd.read_csv(ROOT / "analysis/targets.csv").set_index("subject")

PANELS = [
    dict(feat="frac_act_short_w10_p20", target="snap_adhd_total",
         ftext="share of short active bouts (≤10 s)\n"
               "10 s windows, 20th-percentile threshold",
         ttext="SNAP-IV ADHD total (0–54)"),
    dict(feat="act_bout_median_w0.5_p80", target="sdq_emo",
         ftext="median active-bout length (s)\n"
               "0.5 s windows, 80th-percentile threshold — "
               "only 4 distinct values",
         ttext="SDQ emotional symptoms (0–10)"),
]

fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.6))
fig.patch.set_facecolor("#fcfcfb")
for ax, p in zip(axes, PANELS):
    x, y = X[p["feat"]], Y[p["target"]]
    rho = spearmanr(x, y).statistic
    med = y.median()
    ax.axhline(med, color=MUTED, lw=0.9, ls=(0, (4, 3)))
    ax.annotate("median split → classification target",
                xy=(0.98, med), xycoords=("axes fraction", "data"),
                xytext=(0, 4), textcoords="offset points",
                ha="right", fontsize=8, color=MUTED)
    ax.scatter(x, y, s=55, facecolors="none", edgecolors=BLUE,
               linewidths=1.6, alpha=0.9)
    dup = pd.DataFrame({"x": x, "y": y}).value_counts()
    for (xi, yi), n in dup.items():
        if n > 1:
            ax.annotate(f"×{n}", xy=(xi, yi), xytext=(7, 5),
                        textcoords="offset points", fontsize=8, color=INK)
    ax.set_xlabel(p["ftext"], fontsize=9.5, color=INK)
    ax.set_ylabel(p["ttext"], fontsize=9.5, color=INK)
    ax.set_title(f"{p['feat']}  →  {p['target']}",
                 loc="left", fontsize=11, color=INK, pad=10)
    ax.annotate(f"Spearman ρ = {rho:+.2f}  (in-sample, descriptive)",
                xy=(0.02, 0.965), xycoords="axes fraction", va="top",
                fontsize=9, color=MUTED)
    ax.grid(color="#e8e7e0", lw=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=9)
fig.suptitle("The two features every selection method converged on — "
             "raw values, 24 children", x=0.01, y=0.99, ha="left",
             fontsize=13, color=INK)
fig.text(0.01, 0.925, "each circle is one child, ×n marks exact overlaps — "
         "no jitter: the vertical stacking on the right is the feature's "
         "4-value discreteness, shown deliberately", fontsize=9, color=MUTED)
fig.tight_layout(rect=(0, 0, 1, 0.885))
fig.savefig(OUT, dpi=150, facecolor=fig.get_facecolor())
print(f"written: {OUT.relative_to(ROOT)}")
