# -*- coding: utf-8 -*-
# =============================================================================
# 74b_delivery_figure.py -- the delivery summary figure (user request
# 2026-08-14: draw the products of 74 / 74a).
#
# Inputs : analysis/final_clf_metrics.csv, analysis/final_reg_metrics.csv
# Output : outputs/figures/final_delivery_summary.png
#
# Left panel, classification (24 targets): horizontal bars of
# bacc MINUS each target's own chance level (bin 0.50, qter 0.33,
# qquar 0.25) -- the only scale on which the three label kinds are
# comparable.  Color = label kind (validated slots 1-3).  Right panel,
# regression (10 targets): horizontal bars of skill (0 = predicting the
# mean).  Both sorted, zero-anchored; K_final in every row label; nested
# numbers, no significance testing (stated on the figure).
# Reproduce with: .venv/bin/python analysis/74b_delivery_figure.py
# =============================================================================
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "outputs" / "figures" / "final_delivery_summary.png"
INK, MUTED = "#1a1a19", "#6b6a63"
KIND = {"__qbin": ("binary", "#2a78d6"), "__qter": ("tertile", "#eb6834"),
        "__qquar": ("quartile", "#1baf7a")}

clf = pd.read_csv(ROOT / "analysis/final_clf_metrics.csv")
reg = pd.read_csv(ROOT / "analysis/final_reg_metrics.csv")
clf["excess"] = clf["bacc"] - clf["chance"]
clf["kind"] = [next(v[0] for s, v in KIND.items() if t.endswith(s))
               for t in clf["target"]]
clf["color"] = [next(v[1] for s, v in KIND.items() if t.endswith(s))
                for t in clf["target"]]
clf = clf.sort_values("excess")
reg = reg.sort_values("skill")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8.6),
                               gridspec_kw=dict(width_ratios=[1.15, 1]))
fig.patch.set_facecolor("#fcfcfb")

lab1 = [f"{t.split('__')[0]}  (K={int(k)})"
        for t, k in zip(clf["target"], clf["k_final"])]
ax1.barh(range(len(clf)), clf["excess"], color=clf["color"], height=0.62)
ax1.set_yticks(range(len(clf)), lab1, fontsize=8.5)
for i, (e, b) in enumerate(zip(clf["excess"], clf["bacc"])):
    ax1.annotate(f"{b:.2f}", xy=(e, i), xytext=(4 if e >= 0 else -4, 0),
                 textcoords="offset points", va="center",
                 ha="left" if e >= 0 else "right", fontsize=7.5, color=MUTED)
ax1.axvline(0, color=INK, lw=0.9)
ax1.set_xlabel("balanced accuracy − chance  (chance: 0.50 / 0.33 / 0.25)",
               fontsize=10, color=INK)
ax1.set_title("Classification delivery (nested logit)", loc="left",
              fontsize=12, color=INK)
handles = [plt.Rectangle((0, 0), 1, 1, color=v[1]) for v in KIND.values()]
ax1.legend(handles, [v[0] for v in KIND.values()], loc="lower right",
           frameon=False, fontsize=9)

lab2 = [f"{t}  (K={int(k)})" for t, k in zip(reg["target"], reg["k_final"])]
ax2.barh(range(len(reg)), reg["skill"], color="#2a78d6", height=0.55)
ax2.set_yticks(range(len(reg)), lab2, fontsize=9)
for i, s in enumerate(reg["skill"]):
    ax2.annotate(f"{s:+.3f}", xy=(s, i), xytext=(4 if s >= 0 else -4, 0),
                 textcoords="offset points", va="center",
                 ha="left" if s >= 0 else "right", fontsize=8, color=MUTED)
ax2.axvline(0, color=INK, lw=0.9)
ax2.set_xlim(-0.55, 0.34)
ax2.set_xlabel("skill  (0 = predicting the mean)", fontsize=10, color=INK)
ax2.set_title("Regression delivery (nested ridge)", loc="left",
              fontsize=12, color=INK)

for ax in (ax1, ax2):
    ax.grid(axis="x", color="#e8e7e0", lw=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(colors=MUTED)
fig.suptitle("Final delivery: every model's honest held-out performance "
             "(fully nested feature selection; no significance testing)",
             x=0.01, y=0.995, ha="left", fontsize=13, color=INK)
fig.text(0.01, 0.952, "bars right of zero = better than guessing; "
         "K = features in the delivered full-sample refit", fontsize=9.5,
         color=MUTED)
fig.tight_layout(rect=(0, 0, 1, 0.935))
fig.savefig(OUT, dpi=150, facecolor=fig.get_facecolor())
print(f"written: {OUT.relative_to(ROOT)}")
