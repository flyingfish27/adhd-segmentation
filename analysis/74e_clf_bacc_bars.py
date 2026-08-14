# -*- coding: utf-8 -*-
# =============================================================================
# 74e_clf_bacc_bars.py -- the classification delivery as paired bars (user
# request 2026-08-14: "logit 画一个 bacc 的", matching the re-spec'd bar
# style of 74d: blue delivered model / green baseline, best rows on top).
#
# Input : analysis/final_clf_metrics.csv
# Output: outputs/figures/final_clf_bacc_bars.png
#
# One row per delivered classifier (24): green bar = that target's own
# chance level (0.50 binary, 0.33 tertile, 0.25 quartile -- the green
# lengths make the differing baselines visible), blue bar = nested-logit
# balanced accuracy.  Blue longer than green = beats guessing.  Rows sorted
# by delivered bacc, best at the top.
# Reproduce with: .venv/bin/python analysis/74e_clf_bacc_bars.py
# =============================================================================
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "outputs" / "figures" / "final_clf_bacc_bars.png"
BLUE, GREEN, INK, MUTED = "#2a78d6", "#1baf7a", "#1a1a19", "#6b6a63"

m = pd.read_csv(ROOT / "analysis/final_clf_metrics.csv")
m = m.sort_values("bacc")            # barh: y=0 bottom -> best ends on top

fig, ax = plt.subplots(figsize=(11.5, 11))
fig.patch.set_facecolor("#fcfcfb")
ys = np.arange(len(m))
ax.barh(ys + 0.19, m["chance"], height=0.34, color=GREEN,
        label="chance (guessing) level")
ax.barh(ys - 0.19, m["bacc"], height=0.34, color=BLUE,
        label="delivered logit model (nested bacc)")
for y, (_, r) in zip(ys, m.iterrows()):
    ax.annotate(f"{r['chance']:.2f}", xy=(r["chance"], y + 0.19),
                xytext=(4, 0), textcoords="offset points", va="center",
                fontsize=8, color=MUTED)
    ax.annotate(f"{r['bacc']:.2f}", xy=(r["bacc"], y - 0.19),
                xytext=(4, 0), textcoords="offset points", va="center",
                fontsize=8, color=INK)
def nice(t):
    return (t.replace("__qbin", " (binary)")
             .replace("__qter", " (tertile)")
             .replace("__qquar", " (quartile)"))


labels = [f"{nice(t)}  K={int(k)}"
          for t, k in zip(m["target"], m["k_final"])]
ax.set_yticks(ys, labels, fontsize=9)
ax.set_xlim(0, 0.92)
ax.set_xlabel("leave-one-out balanced accuracy", fontsize=10, color=INK)
ax.legend(loc="lower right", frameon=False, fontsize=9.5)
ax.grid(axis="x", color="#e8e7e0", lw=0.6)
ax.set_axisbelow(True)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.tick_params(colors=MUTED, labelsize=9)
fig.suptitle("Classification delivery: nested-logit balanced accuracy vs "
             "each target's chance level", x=0.01, y=0.99, ha="left",
             fontsize=13, color=INK)
fig.text(0.01, 0.955, "blue bar longer than its green partner = beats "
         "guessing; chance differs by label kind (0.50 / 0.33 / 0.25). "
         "Nested numbers, no significance testing.", fontsize=9.5,
         color=MUTED)
fig.tight_layout(rect=(0, 0, 1, 0.94))
fig.savefig(OUT, dpi=150, facecolor=fig.get_facecolor())
print(f"written: {OUT.relative_to(ROOT)}")
