# -*- coding: utf-8 -*-
"""
62_multivariate_analysis.py
Stage 3 of the modelling-results analysis: the multivariate cross-validation track,
and the comparison between the two tracks.

Reads analysis/B_multivariate.csv (produced by 45_multivariate_cv.py) and
analysis/A_univariate.csv.  It does NOT re-run either producing script.

One consequence of that, stated up front because it shapes every figure here: the
B track's null is a permutation of the whole cross-validation, which
45_multivariate_cv.py measures at roughly 14.7 hours of compute.  This script
therefore does not build a null for the B track.  Its references are the two the
table already carries -- the dummy baseline (skill = 0 for regression, balanced
accuracy = 1/k for classification) and the stored perm_p / q_fdr columns.

Outputs
    outputs/tables/62_multivariate.md
    outputs/figures/fig11_cv_results_vs_baseline.png
    outputs/figures/fig12_permutation_and_fdr.png
    outputs/figures/fig13_full_model_vs_movement_total.png
    outputs/figures/fig14_track_agreement.png
    outputs/figures/fig15_bmi_arm.png

Re-run with:
    .venv/bin/python analysis/62_multivariate_analysis.py
"""
import io
import pathlib
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIGDIR = ROOT / "outputs" / "figures"
TABDIR = ROOT / "outputs" / "tables"
FIGDIR.mkdir(parents=True, exist_ok=True)
TABDIR.mkdir(parents=True, exist_ok=True)


class Tee:
    def __init__(self, stream):
        self.stream, self.buf = stream, io.StringIO()

    def write(self, s):
        self.stream.write(s)
        self.buf.write(s)

    def flush(self):
        self.stream.flush()


tee = Tee(sys.stdout)
sys.stdout = tee


def head(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


B = pd.read_csv(ROOT / "analysis/B_multivariate.csv")
A = pd.read_csv(ROOT / "analysis/A_univariate.csv")
Yl = pd.read_csv(ROOT / "analysis/target_labels.csv").set_index("subject")
Yc = pd.read_csv(ROOT / "analysis/targets.csv").set_index("subject")
M = B[B["variant"] == "main"].copy()

# number of classes and the chance level of balanced accuracy, per classification target
KCLASS = {c: int(Yl[c].nunique()) for c in Yl.columns}
M["chance"] = [1.0 / KCLASS[t] if tr in ("bin", "multi") else 0.0
               for t, tr in zip(M["target"], M["track"])]

# ---------------------------------------------------------------------------
# [1] Internal consistency of the published table
# ---------------------------------------------------------------------------
head("[1] INTERNAL CONSISTENCY OF B_multivariate.csv")
print(f"  rows: {len(B)}   arms: {dict(B['variant'].value_counts())}")
print(f"  MODEL_MENU.md section 4 trap 7: any count over this table must first be")
print(f"  restricted to variant == 'main', or it is inflated threefold. Main arm: {len(M)} rows.")
checks = []


def chk(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(f"  [{'ok ' if ok else 'FAIL'}] {name}{('   ' + detail) if detail else ''}")


reg, cls = M[M["track"] == "reg"], M[M["track"].isin(["bin", "multi"])]
chk("every main-arm row used all 24 subjects", (M["n"] == 24).all(),
    f"n values {sorted(M['n'].unique())}")
chk("the two exploratory arms used 23 subjects",
    (B.loc[B["variant"] != "main", "n"] == 23).all())
chk("balanced accuracy within [0, 1]", cls["bacc"].between(0, 1).all(),
    f"range {cls['bacc'].min():.3f} .. {cls['bacc'].max():.3f}")
chk("macro F1 within [0, 1]", cls["f1"].between(0, 1).all(),
    f"range {cls['f1'].min():.3f} .. {cls['f1'].max():.3f}")
chk("accuracy within [0, 1]", cls["acc"].between(0, 1).all())
chk("skill <= 1 (it is 1 - RMSE/RMSE_dummy, so it cannot exceed 1)", (reg["skill"] <= 1).all(),
    f"range {reg['skill'].min():.3f} .. {reg['skill'].max():.3f}")
chk("skill_over_nc equals skill - nc_skill",
    np.allclose(reg["skill_over_nc"], reg["skill"] - reg["nc_skill"]),
    f"max deviation {np.abs(reg['skill_over_nc'] - (reg['skill'] - reg['nc_skill'])).max():.2e}")
chk("regression metrics absent on classification rows and vice versa",
    cls[["rmse", "mae", "skill", "nc_skill"]].isna().all().all()
    and reg[["f1", "acc", "bacc"]].isna().all().all())
chk("nc_skill is a property of the target alone, identical across model and k",
    reg.groupby("target")["nc_skill"].nunique().eq(1).all())


def bh(p):
    p = np.asarray(p, float)
    m = len(p)
    o = np.argsort(p)
    q = np.empty(m)
    prev = 1.0
    for rank, idx in enumerate(o[::-1]):
        i = m - rank
        val = min(prev, p[idx] * m / i)
        prev = val
        q[idx] = val
    return q


qrec = bh(np.where(M["perm_p"].isna(), 1.0, M["perm_p"]).astype(float))
chk(f"published q_fdr reproduces from perm_p with the documented m = {len(M)} family",
    np.nanmax(np.abs(qrec - M["q_fdr"].to_numpy())) < 1e-12,
    f"max deviation {np.nanmax(np.abs(qrec - M['q_fdr'].to_numpy())):.2e}")
chk("q_fdr is present only on the main arm",
    B.loc[B["variant"] != "main", "q_fdr"].isna().all())
print(f"\n  {sum(1 for _, ok, _ in checks if ok)} of {len(checks)} checks passed")

# ---------------------------------------------------------------------------
# [2] FIGURE 11 -- every combination against its baseline
# ---------------------------------------------------------------------------
head("[2] EVERY MAIN-ARM COMBINATION AGAINST ITS BASELINE")
print("  Regression baseline: skill = 0, i.e. the same RMSE as always predicting the")
print("  training mean. Classification baseline: balanced accuracy = 1/k, where k is the")
NTGT = {suf: M.loc[M["target"].str.endswith(suf), "target"].nunique()
        for suf in ("__qbin", "__qter", "__qquar")}
print(f"  number of classes -- 1/2 for the {NTGT['__qbin']} __qbin targets, "
      f"1/3 for the {NTGT['__qter']} __qter and")
print(f"  1/4 for the {NTGT['__qquar']} __qquar.")
print(f"\n  {'track':6} {'combinations':>13} {'beat baseline':>14} {'share':>7} {'best':>8}  best combination")
for tr, met in [("reg", "skill"), ("bin", "bacc"), ("multi", "bacc")]:
    g = M[M["track"] == tr]
    won = g[g[met] > g["chance"]] if tr != "reg" else g[g[met] > 0]
    b = g.loc[g[met].idxmax()]
    print(f"  {tr:6} {len(g):13d} {len(won):14d} {100 * len(won) / len(g):6.1f}%"
          f" {g[met].max():8.3f}  {b['target']} / {b['model']} / k{int(b['k'])}")

print("\n  the permutation gate, as written in 45_multivariate_cv.py:")
print("    regression      skill > 0             -- this is exactly the dummy baseline")
print("    classification  bacc > 1 / n_classes  -- each target against its own chance level")
mult = M[M["track"] == "multi"]
above_chance = mult[mult["bacc"] > mult["chance"]]
would_pass_half = mult[mult["bacc"] > 0.5]
print(f"  For the {len(mult)} multiclass combinations, chance is 1/3 or 1/4, not 1/2.")
print(f"    above their own chance level       : {len(above_chance)}")
print(f"    of those, permutation-tested       : {int(above_chance['perm_p'].notna().sum())}")
print(f"    a flat bacc > 0.5 rule would test  : {len(would_pass_half)}")
print("  Until commit 58b7bbf the gate WAS that flat bacc > 0.5, which is the chance")
print("  level of a 2-class target only. Multiclass combinations that beat 1/3 or 1/4")
print("  but not 1/2 therefore entered the FDR family at p = 1 without ever being")
print("  tested. That is no longer the case: the gate now reads each target's own")
print("  class count, so this figure's 'beat their baseline' and 'permutation tested'")
print("  counts are produced by the same rule.")

fig, axes = plt.subplots(1, 3, figsize=(16.4, 6.2),
                         gridspec_kw={"width_ratios": [1, 1, 1.18], "wspace": 0.42})
MK = {5: "o", 10: "s"}
CM = {"ridge": "#4878a8", "svr": "#e08214", "rf": "#1a9850",
      "logit": "#4878a8", "svm": "#e08214"}
for ax, tr, met, xlab in [
        (axes[0], "reg", "skill", "skill  (0 = as good as predicting the training mean)"),
        (axes[1], "bin", "bacc", "balanced accuracy  (0.5 = chance for a 2-class target)"),
        (axes[2], "multi", "bacc", "balanced accuracy  (chance is 1/3 or 1/4, marked per row)")]:
    g = M[M["track"] == tr]
    tgts = sorted(g["target"].unique())
    for i, t in enumerate(tgts):
        gg = g[g["target"] == t]
        for _, r in gg.iterrows():
            ax.scatter(r[met], i + (0.16 if r["k"] == 10 else -0.16),
                       marker=MK[int(r["k"])], s=42, color=CM.get(r["model"], "#777777"),
                       alpha=0.9, edgecolor="white", linewidth=0.6, zorder=3)
        if tr != "reg":
            c = 1.0 / KCLASS[t]
            ax.plot([c, c], [i - 0.42, i + 0.42], color="#b2182b", lw=2.0, zorder=2)
    if tr == "reg":
        ax.axvline(0, color="#b2182b", lw=2.0)
    ax.set_yticks(range(len(tgts)))
    ax.set_yticklabels([t if tr == "reg" else f"{t}  [{KCLASS[t]}cl]" for t in tgts], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel(xlab, fontsize=9)
    ax.set_title({"reg": f"Fig 11a  Regression, {len(g)} combinations",
                  "bin": f"Fig 11b  Binary classification, {len(g)}",
                  "multi": f"Fig 11c  Multiclass, {len(g)}"}[tr], fontsize=10.5)
    ax.grid(axis="x", alpha=0.22, lw=0.6)
    ax.set_axisbelow(True)
h = [plt.Line2D([], [], marker="o", ls="", color=CM[m], label=m) for m in
     ["ridge", "svr", "rf", "logit", "svm"]]
h += [plt.Line2D([], [], marker=MK[k], ls="", color="#555555", label=f"k = {k} features")
      for k in (5, 10)]
h += [plt.Line2D([], [], color="#b2182b", lw=2.0, label="baseline / chance")]
axes[2].legend(handles=h, fontsize=8, frameon=False, loc="center left", bbox_to_anchor=(1.02, 0.5))
fig.suptitle(f"Fig 11  All {len(M)} main-arm cross-validated results against the baseline each one has to beat\n"
             f"leave-one-out over {int(M['n'].max())} subjects; feature selection and scaling refitted inside every fold",
             fontsize=11.5)
fig.subplots_adjust(left=0.085, right=0.885, top=0.855, bottom=0.235, wspace=0.42)
fig.text(0.012, 0.020,
         "'rf' appears in both the regression and the classification panels and is a different estimator in each (RandomForestRegressor / RandomForestClassifier). Hyperparameters are fixed, not tuned:\n"
         "alpha = 10, C = 1, 200 trees, k in {5, 10} (MODEL_MENU.md section 4 trap 3), so these are one reasonable default configuration rather than a best attainable model. The multiclass panel is drawn with\n"
         "a per-row chance line because chance depends on the number of classes; using 0.5 there would compare a 4-class result against a 2-class standard. The permutation gate in 45_multivariate_cv.py did\n"
         "exactly that until commit 58b7bbf and now reads each target's own class count instead.",
         fontsize=7.2, color="#444444", linespacing=1.5)
fig.savefig(FIGDIR / "fig11_cv_results_vs_baseline.png", dpi=200)
plt.close(fig)
print(f"\n  wrote {FIGDIR / 'fig11_cv_results_vs_baseline.png'}")

# ---------------------------------------------------------------------------
# [3] FIGURE 12 -- permutation and FDR, with the untested majority made visible
# ---------------------------------------------------------------------------
head("[3] PERMUTATION AND FDR ON THE B TRACK")
tested = M[M["perm_p"].notna()]
print(f"  combinations in the family                 : {len(M)}")
print(f"  actually permutation-tested                : {len(tested)}"
      f"   (reg {int((tested['track'] == 'reg').sum())},"
      f" bin {int((tested['track'] == 'bin').sum())},"
      f" multi {int((tested['track'] == 'multi').sum())})")
print(f"  never tested, entered the family as p = 1  : {int(M['perm_p'].isna().sum())}")
print(f"  permutation resolution 1/(NPERM+1)         : {1 / 5001:.2e}")
print(f"  smallest perm_p anywhere in the table      : {M['perm_p'].min():.4f}")
print(f"    -- no combination came within a factor of {M['perm_p'].min() / (1 / 5001):.0f} of the resolution limit,")
print(f"       so unlike the A track nothing here is pinned to the floor.")
print(f"  perm_p < 0.05                              : {int((M['perm_p'] < 0.05).sum())}"
      f"   (of {len(tested)} tested; if all {len(tested)} were null, {0.05 * len(tested):.1f} would be expected)")
print(f"  q_fdr < 0.05                               : {int((M['q_fdr'] < 0.05).sum())}")
print(f"  q_fdr < 0.10                               : {int((M['q_fdr'] < 0.10).sum())}")
print(f"  smallest q_fdr in the table                : {M['q_fdr'].min():.4f}")

print(f"\n  the ten smallest permutation p-values:")
print(f"  {'track':6} {'target':24} {'model':6} {'k':>3} {'metric':>8} {'perm_p':>8} {'q_fdr':>8}")
for _, r in M.nsmallest(10, "perm_p").iterrows():
    met = r["skill"] if r["track"] == "reg" else r["bacc"]
    print(f"  {r['track']:6} {r['target']:24} {r['model']:6} {int(r['k']):3d}"
          f" {met:8.3f} {r['perm_p']:8.4f} {r['q_fdr']:8.4f}")

fig, (axA, axB) = plt.subplots(1, 2, figsize=(13.8, 5.8),
                               gridspec_kw={"width_ratios": [1.2, 1], "wspace": 0.24})
ax = axA
pv = np.where(M["perm_p"].isna(), 1.0, M["perm_p"]).astype(float)
order = np.argsort(pv)
ranks = np.arange(1, len(M) + 1)
istested = M["perm_p"].notna().to_numpy()[order]
ax.scatter(ranks[istested], pv[order][istested], s=26, color="#4878a8", zorder=3,
           label=f"permutation-tested ({int(istested.sum())})")
ax.scatter(ranks[~istested], pv[order][~istested], s=14, color="#cccccc", zorder=2,
           label=f"never tested, entered as p = 1 ({int((~istested).sum())})")
ax.plot(ranks, 0.05 * ranks / len(M), color="#b2182b", lw=2.2,
        label=f"BH threshold q = 0.05  (m = {len(M)})")
ax.axhline(1 / 5001, color="#555555", ls="--", lw=1.2,
           label="permutation resolution 1/(5000+1)")
ax.set_yscale("log")
ax.set_xlabel(f"Rank within the family of {len(M)} combinations")
ax.set_ylabel("Permutation p (log scale)")
ax.set_title("Fig 12a  The whole FDR family, including the part that was never tested",
             fontsize=10.5)
ax.legend(fontsize=8.0, frameon=True, framealpha=0.95, edgecolor="#cccccc", loc="lower right")
ax.grid(alpha=0.22, lw=0.6, which="both")
ax.set_axisbelow(True)

ax = axB
lab = [f"all {len(M)}\ncombinations", "beat their\nbaseline", "permutation\ntested",
       "perm_p\n< 0.05", "q_fdr\n< 0.05"]
beat = int((M[M.track == "reg"]["skill"] > 0).sum() +
           (M[M.track != "reg"]["bacc"] > M[M.track != "reg"]["chance"]).sum())
vals = [len(M), beat, len(tested), int((M["perm_p"] < 0.05).sum()), int((M["q_fdr"] < 0.05).sum())]
bars = ax.bar(range(5), vals, color=["#cccccc", "#9ecae1", "#4878a8", "#e08214", "#b2182b"],
              width=0.62)
for i, v in enumerate(vals):
    ax.text(i, v + 3, str(v), ha="center", fontsize=10.5, fontweight="bold")
ax.set_xticks(range(5))
ax.set_xticklabels(lab, fontsize=8.4)
ax.set_ylabel("Number of combinations")
ax.set_ylim(0, len(M) * 1.14)
ax.set_title(f"Fig 12b  The funnel from {len(M)} combinations to what survives",
             fontsize=10.5)
ax.grid(axis="y", alpha=0.22, lw=0.6)
ax.set_axisbelow(True)
ax.text(0.5, 0.62, "'beat their baseline' and 'permutation tested' are now the\n"
                   "same rule: every track against its own chance level, 1/2 for\n"
                   "2-class targets and 1/3 or 1/4 for multiclass. Until commit\n"
                   "58b7bbf the gate was a flat bacc > 0.5, so fewer combinations\n"
                   "were tested than beat their baseline and the two bars differed.",
        transform=ax.transAxes, ha="center", fontsize=7.8,
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#cccccc"))
fig.tight_layout()
fig.subplots_adjust(bottom=0.185)
fig.text(0.012, 0.018,
         f"MODEL_MENU.md section 4 trap 2: an absent perm_p means the combination never beat the dummy baseline and so was never permutation-tested; it does not mean tested and found not significant. Those\n"
         f"{int(M['perm_p'].isna().sum())} combinations still enter the BH denominator at p = 1, which 45_multivariate_cv.py records as a deliberate conservative choice -- it can only hide a real finding, never manufacture one. Panel a\n"
         f"shows them so that the family size m = {len(M)} is visible rather than being a number in the caption.",
         fontsize=7.2, color="#444444", linespacing=1.5)
fig.savefig(FIGDIR / "fig12_permutation_and_fdr.png", dpi=200)
plt.close(fig)
print(f"\n  wrote {FIGDIR / 'fig12_permutation_and_fdr.png'}")

# ---------------------------------------------------------------------------
# [4] FIGURE 13 -- the full model against knowing only how much the child moved
# ---------------------------------------------------------------------------
head("[4] FULL MODEL vs MOVEMENT TOTAL ALONE (regression half only)")
print("  nc_skill is the skill of a model given a single feature, uaMag_median, through the")
print("  same leave-one-out procedure. skill_over_nc = skill - nc_skill, on a shared")
print("  denominator, so it answers: how much does the 608-feature model add over knowing")
print("  only how much the child moved.")
print(f"  This control exists for the {int((M['track'] == 'reg').sum())} regression rows. "
      f"The {int((M['track'] != 'reg').sum())} classification rows have")
print("  no negative control at all -- a decision recorded in 45_multivariate_cv.py and")
print("  required to be declared with the results.")
print(f"\n  {'target':20} {'nc_skill':>9} {'best skill':>11} {'best skill_over_nc':>19} {'models beating nc':>18}")
for t in sorted(reg["target"].unique()):
    g = reg[reg["target"] == t]
    print(f"  {t:20} {g['nc_skill'].iloc[0]:9.3f} {g['skill'].max():11.3f}"
          f" {g['skill_over_nc'].max():19.3f} {int((g['skill_over_nc'] > 0).sum()):13d} / {len(g)}")
print(f"\n  regression combinations with skill > 0 (beat the dummy)      : "
      f"{int((reg['skill'] > 0).sum())} of {len(reg)}")
print(f"  regression combinations with skill_over_nc > 0 (beat movement total): "
      f"{int((reg['skill_over_nc'] > 0).sum())} of {len(reg)}")
print(f"  targets where the movement-total model alone has skill > 0   : "
      f"{sorted(reg.loc[reg['nc_skill'] > 0, 'target'].unique().tolist()) or 'none'}")
print(f"  median skill across the {len(reg)} regression combinations           : {reg['skill'].median():.3f}")
print(f"  median nc_skill                                              : {reg['nc_skill'].median():.3f}")
print("\n  A qualification that changes how skill_over_nc should be read here: nc_skill is")
print(f"  negative for all 10 targets (range {reg['nc_skill'].min():.3f} to {reg['nc_skill'].max():.3f}).")
print("  The movement-total model is itself worse than the dummy. So skill_over_nc > 0 means")
print("  'less bad than a model that is already worse than predicting the mean', not 'good'.")
print(f"  Of the {int((reg['skill_over_nc'] > 0).sum())} combinations that beat the movement-total model,"
      f" {int(((reg['skill_over_nc'] > 0) & (reg['skill'] > 0)).sum())} also beat the dummy baseline.")

fig, (axA, axB) = plt.subplots(1, 2, figsize=(13.6, 5.9),
                               gridspec_kw={"width_ratios": [1.1, 1], "wspace": 0.26})
ax = axA
tg = sorted(reg["target"].unique())
for i, t in enumerate(tg):
    g = reg[reg["target"] == t]
    nc = g["nc_skill"].iloc[0]
    for _, r in g.iterrows():
        ax.plot([0, 1], [nc, r["skill"]], color=CM.get(r["model"], "#777777"),
                alpha=0.55, lw=1.0, zorder=2)
    ax.scatter([0], [nc], s=52, color="#b2182b", marker="D", zorder=4,
               edgecolor="white", linewidth=0.7)
    ax.scatter(np.full(len(g), 1.0), g["skill"], s=26, color="#4878a8", zorder=3,
               alpha=0.85, edgecolor="white", linewidth=0.5)
# label each target at its best combination, nudged apart so the names stay legible
lab_pts = sorted(((reg.loc[reg["target"] == t, "skill"].max(), t) for t in tg), reverse=True)
span = reg["skill"].max() - reg["skill"].min()
minsep = span * 0.038
placed = []
for yv, t in lab_pts:
    y = yv if not placed else min(yv, placed[-1] - minsep)
    placed.append(y)
    ax.plot([1.0, 1.028], [yv, y], color="#999999", lw=0.6)
    ax.text(1.034, y, t, fontsize=7.4, va="center")
ax.axhline(0, color="#333333", lw=1.4, ls="--")
ax.set_xlim(-0.18, 1.42)
ax.set_xticks([0, 1])
ax.set_xticklabels(["movement total only\n(uaMag_median + Ridge)",
                    "full model\n(608 features, top-k selected in fold)"], fontsize=8.6)
ax.set_ylabel("skill   (1 - RMSE / RMSE of predicting the mean)")
ax.set_title("Fig 13a  Does the 608-feature model beat knowing only how much the child moved?\n"
             "dashed line = the dummy baseline; every line is one model x k combination", fontsize=10.2)
ax.grid(axis="y", alpha=0.22, lw=0.6)
ax.set_axisbelow(True)

ax = axB
s = reg.sort_values("skill_over_nc")
ax.barh(range(len(s)), s["skill_over_nc"],
        color=["#1a9850" if v > 0 else "#b2182b" for v in s["skill_over_nc"]], height=0.8)
ax.axvline(0, color="#333333", lw=1.3)
ax.set_yticks([])
ax.set_xlabel("skill_over_nc  =  skill - nc_skill")
ax.set_ylabel(f"the {len(s)} regression combinations, sorted")
ax.set_title("Fig 13b  How much the full model adds over movement total\n"
             f"{int((s['skill_over_nc'] > 0).sum())} of {len(s)} combinations add anything at all",
             fontsize=10.2)
ax.grid(axis="x", alpha=0.22, lw=0.6)
ax.set_axisbelow(True)
ax.text(0.03, 0.96, f"The {int((M['track'] != 'reg').sum())} classification combinations\n"
                    "have no equivalent control:\n"
                    "the B track's movement-total comparison\nexists only on the regression half.",
        transform=ax.transAxes, fontsize=8.2, va="top",
        bbox=dict(boxstyle="round,pad=0.45", fc="#fff6f4", ec="#b2182b", lw=0.9))
fig.tight_layout()
fig.subplots_adjust(bottom=0.155)
fig.text(0.012, 0.018,
         "Reading, from 45_multivariate_cv.py: clearly above 0 means the structural features carry information beyond total movement; near 0 means that whatever the model achieved was available from total\n"
         "movement alone; below 0 means adding them made prediction worse. This is a baseline comparison and not a decomposition: it answers whether the full model beats total movement, not how much of\n"
         "its performance comes from total movement.",
         fontsize=7.2, color="#444444", linespacing=1.5)
fig.savefig(FIGDIR / "fig13_full_model_vs_movement_total.png", dpi=200)
plt.close(fig)
print(f"\n  wrote {FIGDIR / 'fig13_full_model_vs_movement_total.png'}")

# ---------------------------------------------------------------------------
# [5] FIGURE 14 -- do the two tracks point at the same targets
# ---------------------------------------------------------------------------
head("[5] AGREEMENT BETWEEN THE TWO TRACKS")
print("  How independent are they, actually? Less than the two-track framing suggests.")
print("  The B pipeline is VarianceThreshold -> SelectKBest(F score) -> StandardScaler ->")
print("  model. SelectKBest ranks features by a univariate F statistic, so the B track")
print("  begins with a univariate screen of its own, refitted inside each fold. It differs")
print("  from the A track in using an F statistic on raw values rather than Spearman on")
print("  ranks, in selecting inside folds rather than on the full sample, and in then")
print("  fitting a model on the survivors -- but it is not an independent second look.")
print("  A correlation between the two tracks is therefore expected to some degree, and")
print("  agreement between them is weaker evidence than agreement between genuinely")
print("  separate methods would be.")
rows = []
for t in sorted(reg["target"].unique()):
    a = A[(A["type"] == "cont") & (A["target"] == t)]
    rows.append(dict(target=t, kind="continuous", a_eff=a["rho"].abs().max(),
                     a_minq=a["q_fdr"].min(), b_best=reg.loc[reg["target"] == t, "skill"].max(),
                     b_metric="skill"))
binrows = M[M["track"] == "bin"]
for t in sorted(binrows["target"].unique()):
    a = A[(A["type"] == "bin") & (A["target"] == t)]
    rows.append(dict(target=t, kind="binary", a_eff=(a["auc"] - 0.5).abs().max(),
                     a_minq=a["q_fdr"].min(),
                     b_best=binrows.loc[binrows["target"] == t, "bacc"].max(), b_metric="bacc"))
T = pd.DataFrame(rows)
print(f"\n  {'target':24} {'kind':11} {'A best effect':>13} {'A min q':>8} {'B best':>8} {'B metric':>9}")
for _, r in T.iterrows():
    print(f"  {r['target']:24} {r['kind']:11} {r['a_eff']:13.3f} {r['a_minq']:8.3f}"
          f" {r['b_best']:8.3f} {r['b_metric']:>9}")
for kind in ["continuous", "binary"]:
    s = T[T["kind"] == kind]
    rr = np.corrcoef(s["a_eff"].rank(), s["b_best"].rank())[0, 1]
    print(f"\n  {kind}: Spearman correlation between the A-track best effect and the")
    print(f"    B-track best metric across the 10 targets = {rr:+.3f}")
    print(f"    (10 points; with n = 10 this number is itself very imprecise and is")
    print(f"     reported as a description of the scatter, not as a test.)")

fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.8))
for ax, kind, ylab, base in [
        (axes[0], "continuous", "B track: best skill over 6 model x k combinations", 0.0),
        (axes[1], "binary", "B track: best balanced accuracy over 6 combinations", 0.5)]:
    s = T[T["kind"] == kind].sort_values("b_best")
    ax.scatter(s["a_eff"], s["b_best"], s=64, color="#4878a8", edgecolor="white", linewidth=0.8,
               zorder=3)
    x0, x1 = s["a_eff"].min(), s["a_eff"].max()
    ax.set_xlim(x0 - (x1 - x0) * 0.13, x1 + (x1 - x0) * 0.13)
    y0, y1 = s["b_best"].min(), s["b_best"].max()
    ax.set_ylim(y0 - (y1 - y0) * 0.11, y1 + (y1 - y0) * 0.13)
    prev = None
    for _, r in s.iterrows():
        right = r["a_eff"] < (x0 + x1) / 2
        dx, ha = (8, "left") if right else (-8, "right")
        dy = 5
        if prev is not None and abs(r["b_best"] - prev) < (y1 - y0) * 0.055:
            dy = -11
        prev = r["b_best"]
        ax.annotate(r["target"], (r["a_eff"], r["b_best"]), textcoords="offset points",
                    xytext=(dx, dy), fontsize=7.6, ha=ha)
    ax.axhline(base, color="#b2182b", lw=1.6, ls="--",
               label="B-track baseline" + (" (skill = 0)" if kind == "continuous" else " (chance = 0.5)"))
    ax.set_xlabel("A track: largest effect size among 608 features\n"
                  + ("(|Spearman rho|)" if kind == "continuous" else "(|AUC - 0.5|)"), fontsize=9)
    ax.set_ylabel(ylab, fontsize=9)
    ax.set_title(f"Fig 14{'a' if kind == 'continuous' else 'b'}  {kind.capitalize()} targets",
                 fontsize=10.5)
    ax.legend(fontsize=8.2, frameon=False, loc="upper left")
    ax.grid(alpha=0.22, lw=0.6)
    ax.set_axisbelow(True)
fig.suptitle("Fig 14  Do the two tracks pick out the same targets?\n"
             "each point is one target: its strongest univariate result against its best cross-validated model",
             fontsize=11.5)
fig.tight_layout(rect=[0, 0.135, 1, 0.90])
fig.text(0.012, 0.018,
         "These two tracks are not independent, and the agreement visible here should be discounted accordingly. The B pipeline selects features with SelectKBest on a univariate F score inside each fold, so it\n"
         "begins with a univariate screen of its own; it differs from the A track in the statistic (F on raw values rather than Spearman on ranks), in selecting within folds rather than on the full sample, and in\n"
         "fitting a model afterwards. Measured rank correlation across the 10 targets: +0.915 continuous, +0.564 binary -- computed on 10 points and reported as a description of these scatters, not as a test.\n"
         "The three targets that produced the A track's only FDR survivors are snap_inatt, snap_adhd_total and sdq_emo; where each falls on the B-track axis is visible above.",
         fontsize=7.2, color="#444444", linespacing=1.5)
fig.savefig(FIGDIR / "fig14_track_agreement.png", dpi=200)
plt.close(fig)
print(f"\n  wrote {FIGDIR / 'fig14_track_agreement.png'}")

# ---------------------------------------------------------------------------
# [6] FIGURE 15 -- the BMI exploratory arms
# ---------------------------------------------------------------------------
head("[6] THE TWO EXPLORATORY ARMS (BMI)")
key = ["track", "target", "model", "k"]
a23 = B[B["variant"] == "bmi_n23"].set_index(key)
b23 = B[B["variant"] == "nobmi_n23"].set_index(key)
m24 = B[B["variant"] == "main"].set_index(key)
print("  Three arms exist so that two changes can be separated: bmi_n23 minus nobmi_n23 is")
print("  the effect of adding BMI, and nobmi_n23 minus main is the effect of dropping the")
print("  one subject who has no BMI recorded. Neither exploratory arm enters the FDR family")
print("  and neither was permutation-tested.")
print(f"\n  bmi_sel_frac -- the share of leave-one-out folds in which SelectKBest actually")
print(f"  chose BMI into the top-k. MODEL_MENU.md marks this as required reading, because")
print(f"  if it is near zero then 'adding BMI changed nothing' means BMI never entered the")
print(f"  model, which is a different statement from 'BMI is unrelated to symptoms'.")
bs = a23["bmi_sel_frac"]
print(f"    combinations in the arm  : {len(bs)}")
print(f"    mean                     : {bs.mean():.4f}")
print(f"    max                      : {bs.max():.4f}")
print(f"    never selected (== 0)    : {int((bs == 0).sum())} of {len(bs)}")
print(f"    selected in every fold   : {int((bs == 1).sum())} of {len(bs)}")

deltas = {}
for tr, met in [("reg", "skill"), ("bin", "bacc"), ("multi", "bacc")]:
    aa = a23[a23.index.get_level_values(0) == tr][met]
    bb = b23[b23.index.get_level_values(0) == tr][met]
    cc = m24[m24.index.get_level_values(0) == tr][met]
    d_bmi = (aa - bb).dropna()
    d_sub = (bb - cc).dropna()
    deltas[tr] = (d_bmi, d_sub)
    print(f"\n  [{tr}] {met}")
    print(f"    adding BMI      (bmi_n23 - nobmi_n23): median {d_bmi.median():+.4f}"
          f"  max |diff| {d_bmi.abs().max():.4f}  nonzero {int((d_bmi.abs() > 1e-9).sum())}/{len(d_bmi)}")
    print(f"    dropping 1 subj (nobmi_n23 - main)   : median {d_sub.median():+.4f}"
          f"  max |diff| {d_sub.abs().max():.4f}  nonzero {int((d_sub.abs() > 1e-9).sum())}/{len(d_sub)}")
    print(f"    ratio of the two typical magnitudes  : "
          f"{d_bmi.abs().median() / d_sub.abs().median():.2f}" if d_sub.abs().median() > 0 else "")

fig, (axA, axB) = plt.subplots(1, 2, figsize=(13.2, 5.4),
                               gridspec_kw={"width_ratios": [1, 1.25], "wspace": 0.24})
ax = axA
ax.hist(bs, bins=np.linspace(0, 1, 25), color="#4878a8", edgecolor="white", linewidth=0.6)
ax.set_xlabel("bmi_sel_frac  (share of folds in which BMI was selected into the model)")
ax.set_ylabel("Number of combinations")
ax.set_title(f"Fig 15a  Did BMI ever enter the model?\n"
             f"never selected in {int((bs == 0).sum())} of {len(bs)} combinations; mean {bs.mean():.3f}",
             fontsize=10.5)
ax.grid(axis="y", alpha=0.22, lw=0.6)
ax.set_axisbelow(True)

ax = axB
pos, labs = [], []
for i, (tr, lab) in enumerate([("reg", "regression\n(skill)"), ("bin", "binary\n(bacc)"),
                               ("multi", "multiclass\n(bacc)")]):
    d_bmi, d_sub = deltas[tr]
    ax.scatter(np.full(len(d_bmi), i - 0.16) + (np.random.default_rng(i).random(len(d_bmi)) - .5) * 0.12,
               d_bmi, s=20, color="#4878a8", alpha=0.75, linewidths=0)
    ax.scatter(np.full(len(d_sub), i + 0.16) + (np.random.default_rng(9 + i).random(len(d_sub)) - .5) * 0.12,
               d_sub, s=20, color="#e08214", alpha=0.75, linewidths=0)
    pos.append(i)
    labs.append(lab)
ax.axhline(0, color="#333333", lw=1.3)
ax.set_xticks(pos)
ax.set_xticklabels(labs, fontsize=9)
ax.set_ylabel("Change in the metric")
ax.set_title("Fig 15b  Adding BMI vs dropping one subject\n"
             "if the two clouds are comparable, the BMI effect cannot be separated from the sample change",
             fontsize=10.5)
ax.scatter([], [], s=26, color="#4878a8", label="adding BMI (bmi_n23 - nobmi_n23)")
ax.scatter([], [], s=26, color="#e08214", label="dropping subject Y55 (nobmi_n23 - main)")
ax.legend(fontsize=8.4, frameon=False, loc="lower right")
ax.grid(axis="y", alpha=0.22, lw=0.6)
ax.set_axisbelow(True)
fig.tight_layout()
fig.subplots_adjust(bottom=0.20)
fig.text(0.012, 0.018,
         "Both exploratory arms run on 23 subjects because one child has no BMI recorded. They carry no perm_p and no q_fdr and do not enter the FDR family, so nothing here is a confirmatory result.\n"
         "Panel b is the comparison 45_multivariate_cv.py asks for at the end of its own output: if the orange cloud is as large as the blue one, then whatever difference BMI appears to make is not\n"
         "distinguishable from the difference made by analysing 23 children instead of 24.",
         fontsize=7.2, color="#444444", linespacing=1.5)
fig.savefig(FIGDIR / "fig15_bmi_arm.png", dpi=200)
plt.close(fig)
print(f"\n  wrote {FIGDIR / 'fig15_bmi_arm.png'}")

# ---------------------------------------------------------------------------
# snapshot
# ---------------------------------------------------------------------------
try:
    commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
except Exception:
    commit = "(git unavailable)"
body = tee.buf.getvalue()
sys.stdout = tee.stream
hdr = (
    "# 62_multivariate.md -- verbatim stdout snapshot\n\n"
    "**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.\n\n"
    "- Producing script: `analysis/62_multivariate_analysis.py`\n"
    f"- Repository HEAD when this snapshot was generated: `{commit}`\n"
    "- Reproduce with: `.venv/bin/python analysis/62_multivariate_analysis.py`\n"
    "- No permutation null is rebuilt for this track: the B-track null requires permuting the\n"
    "  whole cross-validation, which its producing script measures at about 14.7 hours.\n\n"
    "```text\n"
)
(TABDIR / "62_multivariate.md").write_text(hdr + body + "```\n", encoding="utf-8")
print(f"\nwrote {TABDIR / '62_multivariate.md'}")
