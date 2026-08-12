# -*- coding: utf-8 -*-
# =============================================================================
# 71b_kgrid_mi.py -- FS-D6: the mutual-information twin of the K-grid screen,
# in the "rich" configuration the user asked for (2026-08-12: "按照最富裕的
# 不要委屈的跑").
#
# Selection score, computed inside every training fold:
#     z_j = (MI_j(observed) - mean MI_j(y permuted)) / sd MI_j(y permuted)
# with P = 200 label permutations per fold.  MI is sklearn's mixed estimator:
# the 77 globally-discrete columns (<= 10 unique values of 24) are counted via
# contingency tables (discrete_features mask), the rest use the kNN estimator.
# Mixing raw MI estimates is NOT rank-comparable at n = 23 -- the counting
# estimator inflates multi-level discrete columns by ~(levels-1)/(2n), measured
# 4-5x on this data -- but the permutation z absorbs each estimator's own bias
# into its own null, which is the point of paying for P permutations.
#
# Everything else mirrors 71_kgrid_baseline.py exactly: K = 1..512, the 10
# __qbin targets, clf_pipe / CLF lifted from 45_multivariate_cv.py via ast,
# leave-one-out, selected indices re-sorted into original column order before
# fitting (the RF column-order lesson from 71's V2 gate), metrics f1(macro) /
# accuracy / balanced accuracy computed once over the 24 collected predictions.
# No permutation *testing* of results -- this remains an exploration round and
# adds a second selector to the search space (declared in the ledger).
#
# Seeds, all fixed: observed-MI jitter seed = 1000+fold; permutation p of a
# fold uses seed = fold*1000 + p for both the label shuffle and the MI jitter.
# Determinism gate: one (target, fold) is recomputed twice and must agree
# bit-for-bit before the sweep runs.
#
# Outputs: analysis/kgrid_mi_bin.csv (same schema as kgrid_baseline_bin.csv)
# and the stdout snapshot analysis/probe_outputs/kgrid_mi.md.
# Reproduce with: .venv/bin/python analysis/71b_kgrid_mi.py   (SMOKE=1 shrinks)
# =============================================================================
import ast, io, os, pathlib, subprocess, sys, time, warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("PYTHONWARNINGS", "ignore")

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import (SelectKBest, f_classif,
                                       mutual_info_classif, VarianceThreshold)
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, accuracy_score, balanced_accuracy_score

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SNAP = HERE / "probe_outputs" / "kgrid_mi.md"
OUT = ROOT / "analysis" / "kgrid_mi_bin.csv"
SMOKE = bool(os.environ.get("SMOKE"))
NPERM_MI = 20 if SMOKE else 200
DISCRETE_MAX_UNIQUE = 10

buf = io.StringIO()


class Tee:
    def write(self, s):
        sys.__stdout__.write(s)
        buf.write(s)

    def flush(self):
        sys.__stdout__.flush()


sys.stdout = Tee()


def section(title):
    print("\n" + "=" * 78 + f"\n[{title}\n" + "=" * 78, flush=True)


# ---- lift clf_pipe / CLF from production (identical to 71) ------------------
src = (HERE / "45_multivariate_cv.py").read_text()
tree = ast.parse(src)
wanted = {}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == "clf_pipe":
        wanted["clf_pipe"] = node
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == "CLF":
                wanted["CLF"] = node
assert set(wanted) == {"clf_pipe", "CLF"}
ns = dict(Pipeline=Pipeline, VarianceThreshold=VarianceThreshold,
          SelectKBest=SelectKBest, f_classif=f_classif,
          StandardScaler=StandardScaler, LogisticRegression=LogisticRegression,
          SVC=SVC, RandomForestClassifier=RandomForestClassifier)
mod = ast.Module(body=[wanted["clf_pipe"], wanted["CLF"]], type_ignores=[])
exec(compile(ast.fix_missing_locations(mod), "<45_extract>", "exec"), ns)
CLF = ns["CLF"]
MODELS = list(CLF)

# ---- inputs -----------------------------------------------------------------
X = pd.read_csv(ROOT / "analysis/features.csv").set_index("subject")
Yl = pd.read_csv(ROOT / "analysis/target_labels.csv").set_index("subject")
Ylm = pd.read_csv(ROOT / "analysis/target_labels_meta.csv")
DEGEN = set(Ylm.loc[Ylm["degenerate"] == True, "label_name"])
BIN = [c for c in Yl.columns if c.endswith("__qbin") and c not in DEGEN]
keep = pd.read_csv(ROOT / "analysis/feature_keeplist_512.csv")["feature"].tolist()
X512 = X[keep].to_numpy(float)
DISC = (X[keep].nunique() <= DISCRETE_MAX_UNIQUE).to_numpy()

section("0] SETUP")
print(f"  selector: permutation-z of mixed-estimator MI, P={NPERM_MI}/fold")
print(f"  discrete mask: {DISC.sum()} of {len(keep)} columns "
      f"(<= {DISCRETE_MAX_UNIQUE} unique values)")
print(f"  models: {MODELS}   targets: {len(BIN)}   SMOKE: {SMOKE}")


def mi_z_ranking(Xtr, ytr, fold):
    """z-standardised mixed MI for every column of Xtr; higher = stronger."""
    disc = DISC[:Xtr.shape[1]] if Xtr.shape[1] != len(DISC) else DISC
    obs = mutual_info_classif(Xtr, ytr, discrete_features=disc,
                              random_state=1000 + fold)
    null = np.empty((NPERM_MI, Xtr.shape[1]))
    for p in range(NPERM_MI):
        seed = fold * 1000 + p
        yp = np.random.default_rng(seed).permutation(ytr)
        null[p] = mutual_info_classif(Xtr, yp, discrete_features=disc,
                                      random_state=seed)
    sd = null.std(axis=0)
    sd[sd == 0] = np.inf          # a column whose null never moves scores z=0
    return (obs - null.mean(axis=0)) / sd


def fold_preds(i, y, Ks):
    tr = np.ones(len(y), bool)
    tr[i] = False
    Xtr, Xte = X512[tr], X512[[i]]
    m_keep = Xtr.var(axis=0) > 0.0
    Xtr, Xte = Xtr[:, m_keep], Xte[:, m_keep]
    z = mi_z_ranking(Xtr, y[tr], i)
    assert len(z) == Xtr.shape[1]
    order = np.argsort(z, kind="mergesort")
    out = {}
    for k in Ks:
        idx = np.sort(order[-min(k, Xtr.shape[1]):])   # original column order
        sc = StandardScaler().fit(Xtr[:, idx])
        A, Bte = sc.transform(Xtr[:, idx]), sc.transform(Xte[:, idx])
        for m in MODELS:
            mdl = CLF[m]()
            mdl.fit(A, y[tr])
            out[(k, m)] = int(mdl.predict(Bte)[0])
    return out


# NOTE the variance filter above uses the fold's own mask, so DISC (global
# indexing) must be re-aligned; with no constant columns in any fold of the
# 512 set the mask is all-True and the two indexings coincide -- asserted:
for i in range(24):
    tr = np.ones(24, bool); tr[i] = False
    assert (X512[tr].var(axis=0) > 0.0).all(), \
        "a fold has a constant column; DISC re-alignment needed"
print("  fold-constant check: no fold of the 512-column set drops a column")

section("G] DETERMINISM GATE")
y0 = Yl[BIN[0]].to_numpy(int)
a = fold_preds(0, y0, [1, 5, 50])
b = fold_preds(0, y0, [1, 5, 50])
assert a == b, "non-deterministic selection"
print("  same (target, fold) computed twice: identical -- GATE PASSED")

section("S] FULL SWEEP")
KS_ALL = list(range(1, 9)) if SMOKE else list(range(1, 513))
targets = BIN[:1] if SMOKE else BIN
print(f"  grid: {len(targets)} targets x {len(MODELS)} models x "
      f"{len(KS_ALL)} K values")
rows_out = []
t_all = time.time()
for t in targets:
    t0 = time.time()
    y = Yl[t].to_numpy(int)
    per_fold = Parallel(n_jobs=-1)(
        delayed(fold_preds)(i, y, KS_ALL) for i in range(len(y)))
    for m in MODELS:
        for k in KS_ALL:
            p = np.array([per_fold[i][(k, m)] for i in range(len(y))])
            rows_out.append(dict(
                target=t, model=m, k=k,
                f1=f1_score(y, p, average="macro"),
                acc=accuracy_score(y, p),
                bacc=balanced_accuracy_score(y, p)))
    print(f"  {t:<28} done in {time.time()-t0:6.1f}s", flush=True)
res = pd.DataFrame(rows_out)
print(f"  sweep total: {(time.time()-t_all)/60:.1f} min")

section("R] RESULT SUMMARY")
if not SMOKE:
    res.to_csv(OUT, index=False)
    print(f"  written: {OUT.relative_to(ROOT)}  ({len(res)} rows)")
print("\n  best K per (target, model) by balanced accuracy "
      "(exploration numbers -- max over the grid is selection-biased, and "
      "this is the SECOND selector swept):")
idx = res.groupby(["target", "model"])["bacc"].idxmax()
best = res.loc[idx].sort_values("bacc", ascending=False)
for _, r in best.iterrows():
    print(f"    {r['target']:<28} {r['model']:<6} k={int(r['k']):>3}  "
          f"bacc={r['bacc']:.3f}  f1={r['f1']:.3f}  acc={r['acc']:.3f}")

sys.stdout = sys.__stdout__
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                      capture_output=True, text=True).stdout.strip()
if not SMOKE:
    SNAP.write_text(
        "# kgrid_mi.md -- verbatim stdout snapshot\n\n"
        "**Do not hand-edit.** To update, re-run the producing script and let "
        "it overwrite this file.\n\n"
        "- Producing script: `analysis/71b_kgrid_mi.py`\n"
        f"- Repository HEAD when this snapshot was generated: `{head}`\n"
        "- Reproduce with: `.venv/bin/python analysis/71b_kgrid_mi.py`\n\n"
        "```text\n" + buf.getvalue() + "\n```\n",
        encoding="utf-8")
    print(f"\nsnapshot written: {SNAP.relative_to(ROOT)}")
else:
    print("\nSMOKE run: no csv, no snapshot")
