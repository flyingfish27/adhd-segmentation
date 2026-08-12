# -*- coding: utf-8 -*-
# =============================================================================
# 71_kgrid_baseline.py -- FS-D5: full K-grid screen of the three classifiers,
# doubling as the frozen baseline any future wrapper must beat.
#
# Spec (user decisions 2026-08-12, ledger TASK-124 / FS-D5):
#   feature set : analysis/feature_keeplist_512.csv (materialised by 70c)
#   K grid      : 1..512 (every value)
#   targets     : the 10 __qbin labels, degenerate-filtered as in production
#   models      : logit / linear SVM / RF-200 -- clf_pipe and CLF are lifted
#                 from 45_multivariate_cv.py via ast (65_ precedent), never
#                 retyped
#   protocol    : leave-one-out, collect 24 predictions, then f1(macro) /
#                 accuracy / balanced accuracy once -- exactly production
#   permutations: none (exploration/tuning round; the selection layer over
#                 3 models x 512 K x 10 targets is declared, not tested)
#
# TWO VALIDATION GATES run before the sweep; the sweep only runs if both pass:
#   [V1] production reproduction -- on the FULL 608-column features.csv,
#        recompute all 60 (bin x model x k in {5,10}) main-arm combinations
#        with the lifted pipeline and compare f1/acc/bacc against the
#        committed analysis/B_multivariate.csv, cell by cell.
#   [V2] loop equivalence -- the fast hand-written LOO loop below (per fold:
#        variance filter, one f_classif ranking shared by every K, then
#        scale+fit per K) must give IDENTICAL predictions to the sklearn
#        pipeline at probe K values on the 512-column set.
#
# One documented deviation at the grid ceiling: if a fold's variance filter
# drops columns (the low-unique bout columns can go constant in a training
# fold), production SelectKBest(k=512) would raise; this script selects
# min(k, surviving_width) columns instead -- the precedent is the
# bmi_sel_frac helper in 45_multivariate_cv.py, which does the same.
#
# Outputs: analysis/kgrid_baseline_bin.csv (target x model x K long table,
# 15,360 rows) and the stdout snapshot analysis/probe_outputs/kgrid_baseline.md.
# Reproduce with: .venv/bin/python analysis/71_kgrid_baseline.py
# (env SMOKE=1 shrinks everything for a wiring test and writes no csv)
# =============================================================================
import ast, io, os, pathlib, subprocess, sys, time, warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("PYTHONWARNINGS", "ignore")

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectKBest, f_classif, VarianceThreshold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_predict, LeaveOneOut
from sklearn.metrics import f1_score, accuracy_score, balanced_accuracy_score

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SNAP = HERE / "probe_outputs" / "kgrid_baseline.md"
OUT = ROOT / "analysis" / "kgrid_baseline_bin.csv"
SMOKE = bool(os.environ.get("SMOKE"))

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


# ---- lift clf_pipe / CLF from production, never retype ----------------------
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
clf_pipe, CLF = ns["clf_pipe"], ns["CLF"]
MODELS = list(CLF)  # logit, svm, rf

# ---- inputs -----------------------------------------------------------------
X = pd.read_csv(ROOT / "analysis/features.csv").set_index("subject")
Yl = pd.read_csv(ROOT / "analysis/target_labels.csv").set_index("subject")
Ylm = pd.read_csv(ROOT / "analysis/target_labels_meta.csv")
DEGEN = set(Ylm.loc[Ylm["degenerate"] == True, "label_name"])
BIN = [c for c in Yl.columns if c.endswith("__qbin") and c not in DEGEN]
keep = pd.read_csv(ROOT / "analysis/feature_keeplist_512.csv")["feature"].tolist()
assert all(c in X.columns for c in keep) and len(keep) == 512
X608 = X.to_numpy(float)
X512 = X[keep].to_numpy(float)
loo = LeaveOneOut()

section("0] SETUP")
print(f"  models lifted from 45_multivariate_cv.py: {MODELS}")
print(f"  binary targets ({len(BIN)}): {BIN}")
print(f"  full table {X608.shape}, keep-list set {X512.shape}")
print(f"  SMOKE mode: {SMOKE}")

# ---- [V1] reproduce the committed production numbers on 608 columns ---------
section("V1] PRODUCTION REPRODUCTION -- bin main arm of B_multivariate.csv")
B = pd.read_csv(ROOT / "analysis/B_multivariate.csv")
rows = B[(B["variant"] == "main") & (B["track"] == "bin")]
if SMOKE:
    rows = rows[rows["target"].isin(BIN[:2])]
worst = 0.0
t0 = time.time()
for _, r in rows.iterrows():
    y = Yl[r["target"]].to_numpy(int)
    pred = cross_val_predict(clf_pipe(CLF[r["model"]](), int(r["k"])),
                             X608, y, cv=loo, n_jobs=-1)
    mine = dict(f1=f1_score(y, pred, average="macro"),
                acc=accuracy_score(y, pred),
                bacc=balanced_accuracy_score(y, pred))
    d = max(abs(mine[m] - r[m]) for m in ("f1", "acc", "bacc"))
    worst = max(worst, d)
print(f"  {len(rows)} combinations recomputed in {time.time()-t0:.0f}s; "
      f"max |diff| vs committed table = {worst:.2e}")
assert worst < 1e-9, "production reproduction FAILED -- do not trust the sweep"
print("  GATE PASSED")

# ---- fast LOO loop: one ranking per fold, shared by every K -----------------
def fold_preds(Xv, y, i, Ks, models):
    tr = np.ones(len(y), bool)
    tr[i] = False
    Xtr, Xte = Xv[tr], Xv[[i]]
    m_keep = Xtr.var(axis=0) > 0.0
    Xtr, Xte = Xtr[:, m_keep], Xte[:, m_keep]
    F, _ = f_classif(Xtr, y[tr])
    F = np.where(np.isnan(F), -np.inf, F)          # sklearn _clean_nans
    order = np.argsort(F, kind="mergesort")        # sklearn SelectKBest order
    out = {}
    for k in Ks:
        # SelectKBest applies a boolean mask, so selected columns keep their
        # ORIGINAL order.  RF is not column-order-invariant (max_features
        # subsampling follows column positions), hence the np.sort -- V2
        # caught exactly this on the first smoke run.
        idx = np.sort(order[-min(k, Xtr.shape[1]):])
        sc = StandardScaler().fit(Xtr[:, idx])
        A, Bte = sc.transform(Xtr[:, idx]), sc.transform(Xte[:, idx])
        for m in models:
            mdl = CLF[m]()
            mdl.fit(A, y[tr])
            out[(k, m)] = int(mdl.predict(Bte)[0])
    return out


def sweep_target(Xv, y, Ks, models):
    per_fold = Parallel(n_jobs=-1)(
        delayed(fold_preds)(Xv, y, i, Ks, models) for i in range(len(y)))
    preds = {(k, m): np.array([per_fold[i][(k, m)] for i in range(len(y))])
             for k in Ks for m in models}
    return preds


# ---- [V2] loop equivalence against the sklearn pipeline ---------------------
section("V2] LOOP EQUIVALENCE on the 512-column set")
vb_targets = BIN[:1] if SMOKE else [BIN[0], BIN[-1]]
vb_ks = [1, 10, 101] if SMOKE else [1, 5, 10, 50, 101, 400]
bad = 0
for t in vb_targets:
    y = Yl[t].to_numpy(int)
    preds = sweep_target(X512, y, vb_ks, MODELS)
    for k in vb_ks:
        for m in MODELS:
            ref = cross_val_predict(clf_pipe(CLF[m](), k), X512, y,
                                    cv=loo, n_jobs=-1)
            if not np.array_equal(ref, preds[(k, m)]):
                bad += 1
                print(f"  MISMATCH {t} {m} k={k}")
print(f"  compared {len(vb_targets)}x{len(vb_ks)}x{len(MODELS)} combinations; "
      f"mismatches = {bad}")
assert bad == 0, "loop does not reproduce the pipeline -- do not trust the sweep"
print("  GATE PASSED")

# ---- [S] the sweep ----------------------------------------------------------
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
    preds = sweep_target(X512, y, KS_ALL, MODELS)
    for m in MODELS:
        for k in KS_ALL:
            p = preds[(k, m)]
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
      "(exploration numbers -- the max over this grid is selection-biased):")
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
        "# kgrid_baseline.md -- verbatim stdout snapshot\n\n"
        "**Do not hand-edit.** To update, re-run the producing script and let "
        "it overwrite this file.\n\n"
        "- Producing script: `analysis/71_kgrid_baseline.py`\n"
        f"- Repository HEAD when this snapshot was generated: `{head}`\n"
        "- Reproduce with: `.venv/bin/python analysis/71_kgrid_baseline.py`\n\n"
        "```text\n" + buf.getvalue() + "\n```\n",
        encoding="utf-8")
    print(f"\nsnapshot written: {SNAP.relative_to(ROOT)}")
else:
    print("\nSMOKE run: no csv, no snapshot")
