# -*- coding: utf-8 -*-
# =============================================================================
# 72a_sfs_vs_filter_plot.py -- nested SFS vs the filter baseline, logit only.
#
# Inputs : analysis/kgrid_baseline_bin.csv (filter sweep; logit rows, K<=20)
#          analysis/sfs_logit_bin.csv      (nested SFS curve, d=1..20)
# Output : outputs/figures/sfs_vs_filter_logit_bacc.png
#
# Apples NOT quite to apples, stated on the figure: the filter curve's
# selection (per-fold F-ranking) is inside the outer folds but the CHOICE of
# reading it at a given K is not nested either way; the SFS curve's feature
# choices are fully nested per fold.  Both x-axes count "features in the
# model", linear 1..20.  Panel order matches the earlier figures (F-test
# peak).  Colors: slots 1-2 of the validated reference palette.
# Reproduce with: .venv/bin/python analysis/72a_sfs_vs_filter_plot.py
# =============================================================================
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "outputs" / "figures" / "sfs_vs_filter_logit_bacc.png"

COLORS = {"filter (F-test, logit)": "#2a78d6", "nested SFS (logit)": "#eb6834"}
INK, MUTED = "#1a1a19", "#6b6a63"

f = pd.read_csv(ROOT / "analysis" / "kgrid_baseline_bin.csv")
s = pd.read_csv(ROOT / "analysis" / "sfs_logit_bin.csv")
flt = f[(f["model"] == "logit") & (f["k"] <= 20)].rename(columns={"k": "d"})
targets = (f.groupby("target")["bacc"].max()
             .sort_values(ascending=False).index.tolist())

fig, axes = plt.subplots(2, 5, figsize=(16, 7.2), sharex=True, sharey=True)
fig.patch.set_facecolor("#fcfcfb")
for ax, t in zip(axes.ravel(), targets):
    series = {"filter (F-test, logit)": flt[flt["target"] == t],
              "nested SFS (logit)": s[s["target"] == t]}
    note = []
    for name, df in series.items():
        df = df.sort_values("d")
        ax.plot(df["d"], df["bacc"], color=COLORS[name], lw=1.7, alpha=0.9)
        b = df.loc[df["bacc"].idxmax()]
        ax.plot(b["d"], b["bacc"], "o", color=COLORS[name], ms=4.5, zorder=5)
        note.append(f"{b['bacc']:.3f}@{int(b['d'])}")
    ax.axhline(0.5, color=MUTED, lw=0.8, ls=(0, (4, 3)), zorder=1)
    ax.set_xticks([1, 5, 10, 15, 20])
    ax.set_ylim(0.3, 0.92)
    ax.set_title(t.replace("__qbin", ""), fontsize=10, color=INK, pad=4)
    ax.annotate(f"filter {note[0]}  ·  SFS {note[1]}",
                xy=(0.03, 0.03), xycoords="axes fraction",
                fontsize=7.3, color=MUTED)
    ax.grid(axis="y", color="#e8e7e0", lw=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=8)
for ax in axes[1]:
    ax.set_xlabel("features in the model (K / SFS depth d)", fontsize=9,
                  color=INK)
for ax in axes[:, 0]:
    ax.set_ylabel("balanced accuracy (LOO)", fontsize=9, color=INK)

handles = [plt.Line2D([], [], color=c, lw=2, label=n)
           for n, c in COLORS.items()]
fig.legend(handles=handles, loc="upper right", ncol=2, frameon=False,
           bbox_to_anchor=(0.99, 1.0), fontsize=10)
fig.suptitle("Nested SFS vs filter baseline, logit only, first 20 features "
             "(LOO; SFS feature choices fully nested, both curve maxima are "
             "still a selection)", x=0.01, ha="left", fontsize=12, color=INK)
fig.text(0.01, 0.945, "panels in the F-test figure's order; dashed = chance; "
         "dots = each curve's best depth", fontsize=9, color=MUTED)
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig(OUT, dpi=150, facecolor=fig.get_facecolor())
print(f"written: {OUT.relative_to(ROOT)}")
