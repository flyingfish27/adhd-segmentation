# -*- coding: utf-8 -*-
# =============================================================================
# 72b_step1_stability_plot.py -- does the cross-fold agreement of SFS's FIRST
# pick go together with the SFS peak score?  (user request 2026-08-13:
# "第1步一致率和SFS在图上的最高分有必要研究吗，我想你画个图我看看")
#
# Inputs : analysis/sfs_logit_paths.csv (per-fold selections, step 1 used)
#          analysis/sfs_logit_bin.csv  (bacc(d) curves; peak over d=1..20)
# Output : outputs/figures/sfs_step1_agreement_vs_peak.png
#
# One point per target: x = share of the 24 outer folds that chose the
# target's most-common step-1 feature; y = the SFS curve's peak balanced
# accuracy.  Every point is direct-labeled (target + its modal step-1
# feature), single series, so no legend.  The peak is a max over 20 depths
# (exploration-grade, stated on the figure).
# Reproduce with: .venv/bin/python analysis/72b_step1_stability_plot.py
# =============================================================================
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import spearmanr

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "outputs" / "figures" / "sfs_step1_agreement_vs_peak.png"
BLUE, INK, MUTED = "#2a78d6", "#1a1a19", "#6b6a63"

paths = pd.read_csv(ROOT / "analysis" / "sfs_logit_paths.csv")
curve = pd.read_csv(ROOT / "analysis" / "sfs_logit_bin.csv")

rows = []
for t, g in paths[paths["step"] == 1].groupby("target"):
    top = g["feature"].value_counts()
    rows.append(dict(target=t.replace("__qbin", ""),
                     feat=top.index[0],
                     agree=top.iloc[0] / len(g),
                     peak=curve.loc[curve["target"] == t, "bacc"].max()))
df = pd.DataFrame(rows)
rho, _ = spearmanr(df["agree"], df["peak"])

fig, ax = plt.subplots(figsize=(9.5, 7))
fig.patch.set_facecolor("#fcfcfb")
ax.axhline(0.5, color=MUTED, lw=0.9, ls=(0, (4, 3)))
ax.annotate("chance", xy=(0.995, 0.502), xycoords=("axes fraction", "data"),
            ha="right", fontsize=8.5, color=MUTED)
ax.scatter(df["agree"], df["peak"], s=70, color=BLUE, zorder=5)
offsets = {"snap_adhd_total": (-8, 10), "sdq_emo": (-8, -20),
           "sdq_totdiff": (10, -16), "snap_odd": (-8, 10),
           "snap_inatt": (-160, -6), "sdq_pro": (6, -4),
           "sdq_peer": (-8, 10), "sdq_cond": (-110, -4),
           "snap_hyper": (8, -4), "sdq_hyper": (8, -4)}
for _, r in df.iterrows():
    dx, dy = offsets.get(r["target"], (8, 0))
    ax.annotate(f"{r['target']}\n({r['feat']}, {r['agree']*24:.0f}/24)",
                xy=(r["agree"], r["peak"]), xytext=(dx, dy),
                textcoords="offset points", fontsize=8.2, color=INK,
                linespacing=1.25)
ax.set_xlabel("step-1 agreement: share of the 24 folds choosing the modal "
              "first feature", fontsize=10, color=INK)
ax.set_ylabel("SFS peak balanced accuracy (max over d = 1..20)",
              fontsize=10, color=INK)
ax.set_xlim(0.22, 1.06)
ax.set_ylim(0.44, 0.88)
ax.grid(color="#e8e7e0", lw=0.6)
ax.set_axisbelow(True)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.tick_params(colors=MUTED, labelsize=9)
ax.set_title("Does a stable first pick go with a higher SFS peak?",
             loc="left", fontsize=13, color=INK, pad=30)
ax.text(0, 1.02, f"one point per target; peaks are max-over-path "
        f"(exploration); Spearman rho = {rho:.2f} across these 10 points "
        f"(descriptive, n=10)", transform=ax.transAxes, fontsize=9,
        color=MUTED)
fig.tight_layout()
fig.savefig(OUT, dpi=150, facecolor=fig.get_facecolor())
print(f"written: {OUT.relative_to(ROOT)}")
