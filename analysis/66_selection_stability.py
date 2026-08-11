# -*- coding: utf-8 -*-
"""
66_selection_stability.py
Does the B track lean on a stable set of features, or does every fold pick a
different set?

analysis/B_multivariate.csv and analysis/B_oof_predictions.csv cannot answer
that: neither records which features SelectKBest chose.  The only trace in the
committed tables is bmi_sel_frac, which counts folds for exactly one feature
(BMI).  So the per-fold selection is recomputed here.

WHAT IS RECOMPUTED, AND WHAT IS NOT
    Only the two leading steps of the pipeline -- VarianceThreshold then
    SelectKBest.  No model is fitted and no permutation is run.  Selection sits
    before the model in the pipeline and never sees it, so for one
    (variant, target, k, fold) the selected set is IDENTICAL for ridge, svr and
    rf (and for logit, svm and rf on the classification side).  A panel labelled
    "ridge" below is therefore also the panel for svr and for rf.

NO HAND-COPYING
    The two steps are not retyped here.  reg_pipe / clf_pipe / KS are pulled out
    of analysis/45_multivariate_cv.py with ast and executed, then the "vt" and
    "sel" steps are lifted off the constructed Pipeline object and cloned per
    fold.  If 45 changes its threshold, its score function or its k list, this
    script follows automatically.  Same technique, same reason, as
    analysis/65_oof_predictions.py.

ARM
    main only: n = 24, all subjects, no BMI column.  That is the arm whose
    results enter the FDR family; the two n = 23 BMI arms are exploratory and are
    not drawn here.

Outputs
    outputs/figures/fig17_selection_frequency_profile.png
    outputs/figures/fig18_selection_folds_sdq_emo_ridge.png
    outputs/tables/66_selection_stability.md

Re-run with:
    .venv/bin/python analysis/66_selection_stability.py
"""
import ast
import io
import pathlib
import subprocess
import sys
import warnings

warnings.filterwarnings("ignore")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_regression, f_classif, VarianceThreshold
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.svm import SVR, SVC
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import LeaveOneOut

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = HERE / "45_multivariate_cv.py"
FIGDIR = ROOT / "outputs" / "figures"
TABDIR = ROOT / "outputs" / "tables"
FIGDIR.mkdir(parents=True, exist_ok=True)
TABDIR.mkdir(parents=True, exist_ok=True)

BLUE = "#4878a8"
ORANGE = "#e08214"
RED = "#b2182b"
INK = "#333333"
MUTED = "#777777"
GRID = "#E3E3E3"


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


def head(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)


# --------------------------------------------------------------- pull from 45
head("[1] PIPELINE DEFINITIONS LIFTED OUT OF 45_multivariate_cv.py")

WANT_FUNC = {"reg_pipe", "clf_pipe"}
WANT_NAME = {"KS"}
tree = ast.parse(SRC.read_text(encoding="utf-8"))
picked = []
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in WANT_FUNC:
        picked.append(node)
    elif isinstance(node, ast.Assign):
        if any(isinstance(t, ast.Name) and t.id in WANT_NAME for t in node.targets):
            picked.append(node)
got_f = {n.name for n in picked if isinstance(n, ast.FunctionDef)}
got_n = {t.id for n in picked if isinstance(n, ast.Assign)
         for t in n.targets if isinstance(t, ast.Name)}
assert got_f == WANT_FUNC, f"missing functions from 45: {WANT_FUNC - got_f}"
assert WANT_NAME <= got_n, f"missing constants from 45: {WANT_NAME - got_n}"

NS = dict(np=np, Pipeline=Pipeline, StandardScaler=StandardScaler,
          SelectKBest=SelectKBest, f_regression=f_regression, f_classif=f_classif,
          VarianceThreshold=VarianceThreshold, Ridge=Ridge, SVR=SVR, SVC=SVC,
          LogisticRegression=LogisticRegression,
          RandomForestRegressor=RandomForestRegressor,
          RandomForestClassifier=RandomForestClassifier)
exec(compile(ast.fix_missing_locations(ast.Module(body=picked, type_ignores=[])),
             "<extracted-from-45>", "exec"), NS)
reg_pipe, clf_pipe, KS = NS["reg_pipe"], NS["clf_pipe"], NS["KS"]
print(f"  extracted reg_pipe / clf_pipe / KS = {KS}")

# the model argument is irrelevant to selection; None never gets fitted here
PROTO = {"reg": lambda k: reg_pipe(None, k), "bin": lambda k: clf_pipe(None, k),
         "multi": lambda k: clf_pipe(None, k)}
for name, mk in PROTO.items():
    p = mk(KS[0])
    vt, sel = p.named_steps["vt"], p.named_steps["sel"]
    print(f"  {name:5}  step 'vt' = {vt.__class__.__name__}(threshold={vt.threshold})"
          f"   step 'sel' = {sel.__class__.__name__}"
          f"(score_func={sel.score_func.__name__}, k={sel.k})")

# --------------------------------------------------------------------- inputs
head("[2] INPUTS AND TARGET LISTS -- same rules as 45_multivariate_cv.py")

X = pd.read_csv(ROOT / "analysis/features.csv").set_index("subject")
Yc = pd.read_csv(ROOT / "analysis/targets.csv").set_index("subject")
Yl = pd.read_csv(ROOT / "analysis/target_labels.csv").set_index("subject")
Ylm = pd.read_csv(ROOT / "analysis/target_labels_meta.csv")
assert list(X.index) == list(Yc.index) == list(Yl.index)

SUBJ = list(X.index)
FEAT = list(X.columns)
Xv = X.to_numpy(float)
n = len(X)
loo = LeaveOneOut()

DEGEN = set(Ylm.loc[Ylm["degenerate"] == True, "label_name"])
CONT = list(Yc.columns)
BIN = [c for c in Yl.columns if c.endswith("__qbin") and c not in DEGEN]
MULTI = [c for c in Yl.columns if c.endswith(("__qter", "__qquar")) and c not in DEGEN]

print(f"  features: {len(FEAT)}   subjects: {n}   folds per combination: {n} (leave-one-out)")
print(f"  targets:  reg {len(CONT)}   bin {len(BIN)}   multi {len(MULTI)}"
      f"   -> {(len(CONT) + len(BIN) + len(MULTI)) * len(KS)} (target, k) combinations")
print(f"  arm: main only (n = {n}, no BMI column)")

# ------------------------------------------------------------------ recompute
head("[3] RECOMPUTING THE PER-FOLD SELECTION")
print("  For each (track, target, k) and each of the 24 leave-one-out training")
print("  sets: fit VarianceThreshold, then SelectKBest, then map the selected")
print("  positions back to the original feature columns.")
print("  No model is fitted. Selection precedes the model in the pipeline and")
print("  does not see it, so ridge / svr / rf share one selection, as do")
print("  logit / svm / rf.")

TASKS = ([("reg", t, Yc[t].to_numpy(float)) for t in CONT]
         + [("bin", t, Yl[t].to_numpy(int)) for t in BIN]
         + [("multi", t, Yl[t].to_numpy(int)) for t in MULTI])

SEL = {}          # (track, target, k) -> boolean array, folds x features
for track, t, y in TASKS:
    if len(np.unique(y)) < 2:
        continue
    for k in KS:
        proto = PROTO[track](k)
        vt0, sel0 = proto.named_steps["vt"], proto.named_steps["sel"]
        M = np.zeros((n, len(FEAT)), bool)
        for f, (tr, _) in enumerate(loo.split(Xv)):
            vt = clone(vt0).fit(Xv[tr])
            keep = np.flatnonzero(vt.get_support())
            sel = clone(sel0).fit(Xv[tr][:, keep], y[tr])
            M[f, keep[sel.get_support()]] = True
            assert M[f].sum() == k, f"fold {f} selected {M[f].sum()} features, expected {k}"
        SEL[(track, t, k)] = M
print(f"\n  done: {len(SEL)} (track, target, k) combinations x {n} folds")

# ------------------------------------------------------------------- summary
head("[4] HOW MANY DISTINCT FEATURES DOES EACH COMBINATION TOUCH")
print("  ever      = features selected in at least one of the 24 folds")
print("  all-24    = features selected in every fold")
print("  ever / k  = 1.0 means the same k features every fold; larger means churn")
print("  the ceiling is k x 24 (a completely different set in every fold)")

rows = []
for (track, t, k), M in SEL.items():
    cnt = M.sum(axis=0)
    rows.append(dict(track=track, target=t, k=k,
                     ever=int((cnt > 0).sum()), all24=int((cnt == n).sum()),
                     half=int((cnt >= n / 2).sum()), ratio=(cnt > 0).sum() / k))
S = pd.DataFrame(rows).sort_values(["track", "k", "ever"]).reset_index(drop=True)
print()
print(S.to_string(index=False, float_format=lambda v: f"{v:.2f}"))
print("\n  by track and k:")
print(S.groupby(["track", "k"])[["ever", "all24", "half", "ratio"]]
      .agg(["min", "median", "max"]).to_string())

# ------------------------------------------------------- FIGURE 17 (profile A)
head("[5] FIGURE 17 -- selection-frequency profile")

TRACKS = [("reg", CONT, BLUE, "continuous targets"),
          ("bin", BIN, ORANGE, "binary targets"),
          ("multi", MULTI, BLUE, "multi-class targets")]

fig, axes = plt.subplots(len(KS), 3, figsize=(15.5, 8.4), sharey=True)
for r, k in enumerate(KS):
    for c, (track, tlist, color, label) in enumerate(TRACKS):
        ax = axes[r][c]
        lines = [(t, np.sort(SEL[(track, t, k)].sum(axis=0))[::-1])
                 for t in tlist if (track, t, k) in SEL]
        xmax = max(int((v > 0).sum()) for _, v in lines)
        for t, v in lines:
            v = v[v > 0]
            ax.plot(range(1, len(v) + 1), v, lw=1.1, alpha=0.7, color=color)
        ax.axhline(n, color=MUTED, ls=":", lw=1.0)
        ax.axvline(k, color=RED, lw=1.6,
                   label=f"x = k = {k}: where a perfectly\nstable profile would stop")
        ax.set_xlim(0.5, xmax + 0.5)
        ax.set_ylim(0, n + 1.2)
        ax.set_yticks([0, 5, 10, 15, 20, n])
        ax.set_title(f"{label}   (k = {k}, {len(lines)} targets)", fontsize=10, color=INK)
        ax.set_xlabel("features, ranked by how many folds selected them", fontsize=8.5,
                      color=MUTED)
        if c == 0:
            ax.set_ylabel(f"folds selecting it (of {n})", fontsize=8.5, color=MUTED)
        ax.grid(alpha=0.22, lw=0.6)
        ax.set_axisbelow(True)
        ax.tick_params(colors=MUTED, labelsize=8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        med = int(np.median([int((v > 0).sum()) for _, v in lines]))
        ax.text(0.97, 0.93, f"median features ever selected: {med}\n(k = {k}, so "
                            f"{med / k:.1f}x the ceiling of a stable set)",
                transform=ax.transAxes, ha="right", va="top", fontsize=7.6, color=INK)
        if r == 0 and c == 0:
            ax.legend(fontsize=7.4, frameon=False, loc="upper right",
                      bbox_to_anchor=(1.0, 0.72))

fig.suptitle("Fig 17  Does one set of features keep getting selected, or does every fold pick a different set?",
             fontsize=12.5, x=0.012, ha="left", color=INK)
fig.tight_layout()
fig.subplots_adjust(top=0.90, bottom=0.155)
fig.text(0.012, 0.015,
         "One line per target. A line is that target's 608 features sorted by how many of the 24 leave-one-out folds selected them, zeros dropped. A perfectly stable selection is a "
         "flat line at 24 that stops\nexactly at x = k (red): the same k features every fold. A line that slopes away to the right is churn -- features that entered a few folds and not the rest. "
         f"Selection is the VarianceThreshold + SelectKBest\nprefix of the pipeline in 45_multivariate_cv.py, recomputed here; it runs before the model and never sees it, so ridge, svr and rf share one line, as do logit, svm and rf. Arm: main, n = {n}.",
         fontsize=7.2, color="#444444", linespacing=1.5)
fig.savefig(FIGDIR / "fig17_selection_frequency_profile.png", dpi=200)
plt.close(fig)
print(f"  wrote {FIGDIR / 'fig17_selection_frequency_profile.png'}")

# --------------------------------------------------- FIGURE 18 (heatmap B)
head("[6] FIGURE 18 -- fold x feature map for sdq_emo, ridge")
print("  ridge is a regression model, so the target is the continuous sdq_emo and")
print("  the score function is f_regression. svr and rf give the same two panels.")

TARGET = "sdq_emo"
panels = [(k, SEL[("reg", TARGET, k)]) for k in KS]
widths = [max(1, int((M.sum(axis=0) > 0).sum())) for _, M in panels]

fig, axes = plt.subplots(1, len(panels), figsize=(16.0, 7.2),
                         gridspec_kw={"width_ratios": widths, "wspace": 0.03})
for ax, (k, M) in zip(np.atleast_1d(axes), panels):
    cnt = M.sum(axis=0)
    order = np.argsort(-cnt, kind="stable")
    order = order[cnt[order] > 0]
    G = M[:, order].astype(float)
    ax.imshow(np.ma.masked_where(G == 0, G), aspect="auto", cmap=matplotlib.colors.ListedColormap([BLUE]),
              interpolation="nearest", vmin=0, vmax=1)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([FEAT[i] for i in order], rotation=90, fontsize=6.0, color=INK)
    ax.set_yticks(range(n))
    # only the leftmost panel carries the fold names; repeating them would put a
    # column of text on top of the panel to its left
    ax.set_yticklabels([f"without {s}" for s in SUBJ] if ax is np.atleast_1d(axes)[0]
                       else [""] * n, fontsize=6.4, color=INK)
    ax.set_xticks(np.arange(-0.5, len(order), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n, 1), minor=True)
    ax.grid(which="minor", color="#FFFFFF", lw=1.0)
    ax.tick_params(which="minor", length=0)
    core = int((cnt == n).sum())
    ax.set_title(f"k = {k}   |   {len(order)} features ever selected   |   "
                 f"{core} selected in all {n} folds",
                 fontsize=10, color=INK)
    if ax is np.atleast_1d(axes)[0]:
        ax.set_ylabel("the fold, named by the child held out", fontsize=9, color=MUTED)

fig.suptitle(f"Fig 18  Which features each fold selected -- target {TARGET}, model ridge",
             fontsize=12.5, x=0.012, ha="left", color=INK)
fig.tight_layout()
fig.subplots_adjust(top=0.90, bottom=0.30)
fig.text(0.012, 0.018,
         "A filled cell means that feature was in the top k of that fold's training set. Columns are ordered by how many folds selected them, so a solid block on the left is the stable core and the "
         "ragged right-hand region is what changes\nwith the sample. Selection is the VarianceThreshold + SelectKBest prefix of 45_multivariate_cv.py, recomputed here; it runs before the model, so these "
         "two panels are also the panels for svr and for rf.\nLeave-one-out folds share 22 of 24 children with each other, which pushes agreement up on its own -- so a ragged region here is stronger "
         "evidence of instability than a solid block is evidence of stability. Arm: main.",
         fontsize=7.2, color="#444444", linespacing=1.5)
fig.savefig(FIGDIR / "fig18_selection_folds_sdq_emo_ridge.png", dpi=200)
plt.close(fig)
print(f"  wrote {FIGDIR / 'fig18_selection_folds_sdq_emo_ridge.png'}")

print(f"\n  the two panels of fig 18, as numbers:")
for k, M in panels:
    cnt = M.sum(axis=0)
    idx = np.argsort(-cnt, kind="stable")
    idx = idx[cnt[idx] > 0]
    print(f"\n  k = {k}: {len(idx)} features ever selected, of {len(FEAT)}")
    print(f"    {'folds':>5}  feature")
    for i in idx:
        print(f"    {cnt[i]:5d}  {FEAT[i]}")

# ---------------------------------------------------------------------------
# snapshot
# ---------------------------------------------------------------------------
try:
    commit = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
except Exception:
    commit = "(git unavailable)"
body = tee.buf.getvalue()
sys.stdout = tee.stream
hdr = (
    "# 66_selection_stability.md -- verbatim stdout snapshot\n\n"
    "**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.\n\n"
    "- Producing script: `analysis/66_selection_stability.py`\n"
    f"- Repository HEAD when this snapshot was generated: `{commit}`\n"
    "- Reproduce with: `.venv/bin/python analysis/66_selection_stability.py`\n"
    "- Recomputes only the VarianceThreshold + SelectKBest prefix of the pipeline in\n"
    "  `analysis/45_multivariate_cv.py`, which is lifted out of that file with `ast`\n"
    "  rather than retyped. No model is fitted and no permutation is run.\n\n"
    "```text\n"
)
(TABDIR / "66_selection_stability.md").write_text(hdr + body + "```\n", encoding="utf-8")
print(f"\nwrote {TABDIR / '66_selection_stability.md'}")
