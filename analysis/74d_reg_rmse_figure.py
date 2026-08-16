# -*- coding: utf-8 -*-
# =============================================================================
# 74d_reg_rmse_figure.py -- the regression delivery in RMSE units (user
# request 2026-08-14: "不是 skill 的，新做一个 rmse 的").
#
# Input : analysis/final_reg_metrics.csv
# Output: outputs/figures/final_reg_rmse.png
#
# Two renderings of the same content (user asked for a bar version too):
#   outputs/figures/final_reg_rmse.png       -- dumbbell per target
#   outputs/figures/final_reg_rmse_bars.png  -- paired horizontal bars
# Grey = RMSE of predicting the mean (the dummy baseline, recovered exactly
# as rmse / (1 - skill)); blue = RMSE of the delivered nested-ridge model.
# Blue shorter than grey = the model reduces error.  Units are each
# questionnaire's own points, so rows are NOT comparable to each other --
# the within-row comparison is the message (stated on the figures).
# Sorted by skill so the four genuine improvements sit on top.
# Reproduce with: .venv/bin/python analysis/74d_reg_rmse_figure.py
# =============================================================================
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "outputs" / "figures" / "final_reg_rmse.png"
BLUE, GREY, INK, MUTED = "#2a78d6", "#9a998f", "#1a1a19", "#6b6a63"

m = pd.read_csv(ROOT / "analysis/final_reg_metrics.csv")
m["dummy"] = m["rmse"] / (1.0 - m["skill"])
m = m.sort_values("skill")   # best at top of the barh

fig, ax = plt.subplots(figsize=(11, 6.2))
fig.patch.set_facecolor("#fcfcfb")
ys = range(len(m))
for y, (_, r) in zip(ys, m.iterrows()):
    ax.plot([r["dummy"], r["rmse"]], [y, y], color="#d8d7cd", lw=2.5,
            zorder=2)
    better = r["rmse"] < r["dummy"]
    ax.annotate(f"{r['rmse']:.2f}", xy=(r["rmse"], y),
                xytext=(-8 if better else 8, 0), textcoords="offset points",
                va="center", ha="right" if better else "left",
                fontsize=8.5, color=INK)
    ax.annotate(f"{r['dummy']:.2f}", xy=(r["dummy"], y),
                xytext=(8 if better else -8, 0), textcoords="offset points",
                va="center", ha="left" if better else "right",
                fontsize=8.5, color=MUTED)
ax.scatter(m["dummy"], list(ys), s=70, color=GREY, zorder=4,
           label="predict the mean (baseline)")
ax.scatter(m["rmse"], list(ys), s=70, color=BLUE, zorder=5,
           label="delivered ridge model")
ax.set_yticks(list(ys),
              [f"{t}  (K={int(k)})" for t, k in zip(m["target"], m["k_final"])],
              fontsize=9.5)
ax.set_xlabel("leave-one-out RMSE, in each questionnaire's own points "
              "(rows are NOT cross-comparable)", fontsize=10, color=INK)
ax.legend(loc="lower right", frameon=False, fontsize=9.5)
ax.grid(axis="x", color="#e8e7e0", lw=0.6)
ax.set_axisbelow(True)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.tick_params(colors=MUTED, labelsize=9)
fig.suptitle("Regression delivery in RMSE units: model error vs "
             "predicting the mean", x=0.01, y=0.985, ha="left",
             fontsize=13, color=INK)
fig.text(0.01, 0.925, "blue left of grey = the model reduces error; the "
         "within-row gap is the message. Nested numbers, no significance "
         "testing.", fontsize=9.5, color=MUTED)
fig.tight_layout(rect=(0, 0, 1, 0.9))
fig.savefig(OUT, dpi=150, facecolor=fig.get_facecolor())
print(f"written: {OUT.relative_to(ROOT)}")

# ---- paired-bar rendering ---------------------------------------------------
# 2026-08-16 final spec: data reverted to the predict-the-mean dummy baseline
# (the all-512 variant was tried and rolled back by the user), so the legend
# reverts to truthful labels.  Kept from the re-spec: +1 font sizes, full
# scale names, the K explainer line, and a LIGHTER grey for the partner bar.
GREY2 = "#bfbeb5"
NAME = {"snap_inatt": "SNAP-IV_inattention",
        "snap_hyper": "SNAP-IV_hyperactivity",
        "snap_odd": "SNAP-IV_oppositional",
        "snap_adhd_total": "SNAP-IV_ADHD_total",
        "sdq_emo": "SDQ_emotional",
        "sdq_cond": "SDQ_conduct",
        "sdq_hyper": "SDQ_hyperactivity",
        "sdq_peer": "SDQ_peer_problems",
        "sdq_pro": "SDQ_prosocial",
        "sdq_totdiff": "SDQ_total_difficulties"}
mb = m.sort_values("rmse", ascending=False).copy()  # barh: y=0 = bottom row
OUT2 = ROOT / "outputs" / "figures" / "final_reg_rmse_bars.png"
fig2, ax = plt.subplots(figsize=(11, 7))
fig2.patch.set_facecolor("#fcfcfb")
ys = np.arange(len(mb))
ax.barh(ys + 0.19, mb["dummy"], height=0.34, color=GREY2,
        label="predict the mean (baseline)")
ax.barh(ys - 0.19, mb["rmse"], height=0.34, color=BLUE,
        label="delivered ridge model")
for y, (_, r) in zip(ys, mb.iterrows()):
    ax.annotate(f"{r['dummy']:.2f}", xy=(r["dummy"], y + 0.19),
                xytext=(4, 0), textcoords="offset points", va="center",
                fontsize=9.5, color=MUTED)
    ax.annotate(f"{r['rmse']:.2f}", xy=(r["rmse"], y - 0.19),
                xytext=(4, 0), textcoords="offset points", va="center",
                fontsize=9.5, color=INK)
ax.set_yticks(ys, [f"{NAME[t]}  (K={int(k)})"
                   for t, k in zip(mb["target"], mb["k_final"])],
              fontsize=10.5)
ax.set_xlabel("leave-one-out RMSE, in each questionnaire's own points "
              "(rows are NOT cross-comparable)", fontsize=11, color=INK)
ax.legend(loc="upper right", frameon=False, fontsize=10.5)
ax.annotate("K = feature counts in best performance",
            xy=(0.985, 0.855), xycoords="axes fraction", ha="right",
            fontsize=10.5, color=MUTED)
ax.grid(axis="x", color="#e8e7e0", lw=0.6)
ax.set_axisbelow(True)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.tick_params(colors=MUTED, labelsize=10)
fig2.suptitle("Regression delivery in RMSE units: model error vs "
              "predicting the mean", x=0.01, y=0.985, ha="left",
              fontsize=14, color=INK)
fig2.text(0.01, 0.93, "blue bar shorter than its grey partner = the model "
          "reduces error. Nested numbers, no significance testing.",
          fontsize=10.5, color=MUTED)
fig2.tight_layout(rect=(0, 0, 1, 0.905))
fig2.savefig(OUT2, dpi=150, facecolor=fig2.get_facecolor())
print(f"written: {OUT2.relative_to(ROOT)}")
