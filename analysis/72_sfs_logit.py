# -*- coding: utf-8 -*-
# =============================================================================
# 72_sfs_logit.py -- FS-D8: nested sequential forward selection with the
# locked classifier (logit, FS-D7), spec frozen with the user 2026-08-13.
#
#   outer loop : LOO-24; each fold runs its OWN complete SFS on its 23
#                training subjects and predicts its held-out child at every
#                path depth d = 1..20 -> a bacc(d) curve per target,
#                curve-vs-curve comparable with the frozen K-grid baseline.
#   inner score: LOO-23 log-loss (selection); outer reporting stays
#                bacc/f1/acc -- two different quantities by design, declared.
#   tie-break  : exact log-loss ties take the candidate earlier in
#                features.csv column order (declared arbitrary; strict "<"
#                during the scan implements it).
#   model      : LogisticRegression lifted from 45_multivariate_cv.py via ast
#                (the CLF dict); pipeline = per-column standardisation + logit.
#                No VarianceThreshold: no LOO fold of the 512-column keep-list
#                drops a column (asserted in 71b); inner 22-subject folds may
#                contain constant columns, which standardise to all-zero
#                (scale-of-zero treated as 1, sklearn's own convention) and
#                are harmless to an L2 logit.
#   speed      : per inner split the full 512-column matrix is standardised
#                once and subsets are column slices -- identical to fitting
#                StandardScaler on the subset, since the operation is
#                per-column (gate G2 checks this against sklearn pipelines).
#
# Feature pool: analysis/feature_keeplist_512.csv.  Targets: the 10 __qbin
# labels, degenerate-filtered as in production.  D = 20.
#
# Gates before the sweep:
#   G1 determinism -- one fold recomputed twice must agree bit-for-bit;
#   G2 library equivalence -- the hand inner-LOO log-loss for sample
#      candidates must match Pipeline(StandardScaler, logit) +
#      cross_val_predict(predict_proba) + sklearn log_loss to float noise.
#
# Outputs: analysis/sfs_logit_bin.csv   (target x depth x f1/acc/bacc)
#          analysis/sfs_logit_paths.csv (target, fold, step, feature -- the
#                                        per-fold selection record)
#          analysis/probe_outputs/sfs_logit.md (stdout snapshot)
# Reproduce with: .venv/bin/python analysis/72_sfs_logit.py   (SMOKE=1 shrinks)
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
from sklearn.metrics import (f1_score, accuracy_score, balanced_accuracy_score,
                             log_loss)

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SNAP = HERE / "probe_outputs" / "sfs_logit.md"
OUT_CURVE = ROOT / "analysis" / "sfs_logit_bin.csv"
OUT_PATHS = ROOT / "analysis" / "sfs_logit_paths.csv"
SMOKE = bool(os.environ.get("SMOKE"))
DEPTH = 3 if SMOKE else 20

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


# ---- lift the locked model from production ----------------------------------
src = (HERE / "45_multivariate_cv.py").read_text()
tree = ast.parse(src)
clf_node = next(n for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "CLF"
                        for t in n.targets))
ns = dict(LogisticRegression=LogisticRegression, SVC=SVC,
          RandomForestClassifier=RandomForestClassifier)
exec(compile(ast.fix_missing_locations(ast.Module(body=[clf_node],
     type_ignores=[])), "<45_extract>", "exec"), ns)
make_logit = ns["CLF"]["logit"]

# ---- inputs -----------------------------------------------------------------
X = pd.read_csv(ROOT / "analysis/features.csv").set_index("subject")
Yl = pd.read_csv(ROOT / "analysis/target_labels.csv").set_index("subject")
Ylm = pd.read_csv(ROOT / "analysis/target_labels_meta.csv")
DEGEN = set(Ylm.loc[Ylm["degenerate"] == True, "label_name"])
BIN = [c for c in Yl.columns if c.endswith("__qbin") and c not in DEGEN]
keep = pd.read_csv(ROOT / "analysis/feature_keeplist_512.csv")["feature"].tolist()
X512 = X[keep].to_numpy(float)
NFEAT = X512.shape[1]

section("0] SETUP")
print(f"  model: logit lifted from 45 (CLF['logit'])   pool: {NFEAT} columns")
print(f"  depth D = {DEPTH}   targets: {len(BIN)}   inner CV: LOO-23, "
      f"log-loss   SMOKE: {SMOKE}")


def scale_cols(train, test):
    mu, sd = train.mean(0), train.std(0)
    sd = np.where(sd == 0.0, 1.0, sd)
    return (train - mu) / sd, (test - mu) / sd


def inner_splits(Xtr, ytr):
    """pre-scaled (train22, held1) pairs for the 23 inner LOO splits"""
    out = []
    for j in range(len(ytr)):
        m = np.ones(len(ytr), bool)
        m[j] = False
        A, b = scale_cols(Xtr[m], Xtr[[j]])
        out.append((A, b, ytr[m], ytr[j]))
    return out


def cand_logloss(splits, cols):
    """summed inner LOO-23 log-loss of logit on the given column subset"""
    ll = 0.0
    for A, b, ya, yb in splits:
        mdl = make_logit()
        mdl.fit(A[:, cols], ya)
        p = mdl.predict_proba(b[:, cols])[0]
        ll -= np.log(p[list(mdl.classes_).index(yb)])
    return ll


def sfs_fold(i, y, depth):
    """run SFS on the 23 training subjects of outer fold i; return the path
    and the held-out prediction at every depth"""
    tr = np.ones(len(y), bool)
    tr[i] = False
    Xtr, ytr = X512[tr], y[tr]
    splits = inner_splits(Xtr, ytr)
    A_out, b_out = scale_cols(Xtr, X512[[i]])
    sel, path, preds = [], [], []
    remaining = list(range(NFEAT))
    for _ in range(depth):
        best_c, best_ll = None, np.inf
        for c in remaining:                      # ascending order = tie-break
            ll = cand_logloss(splits, sel + [c])
            if ll < best_ll:
                best_c, best_ll = c, ll
        sel.append(best_c)
        remaining.remove(best_c)
        path.append(best_c)
        mdl = make_logit()
        mdl.fit(A_out[:, sel], ytr)
        preds.append(int(mdl.predict(b_out[:, sel])[0]))
    return path, preds


section("G1] DETERMINISM GATE")
y0 = Yl[BIN[0]].to_numpy(int)
r1 = sfs_fold(0, y0, 2)
r2 = sfs_fold(0, y0, 2)
assert r1 == r2, "non-deterministic SFS"
print("  fold 0 recomputed twice: identical -- GATE PASSED")

section("G2] LIBRARY EQUIVALENCE GATE (hand log-loss vs sklearn pipeline)")
tr = np.ones(24, bool)
tr[0] = False
Xtr, ytr = X512[tr], y0[tr]
splits = inner_splits(Xtr, ytr)
worst = 0.0
for c in [0, 17, 255, 400, 511]:
    hand = cand_logloss(splits, [c]) / len(ytr)
    pipe = Pipeline([("sc", StandardScaler()), ("m", make_logit())])
    proba = cross_val_predict(pipe, Xtr[:, [c]], ytr, cv=LeaveOneOut(),
                              method="predict_proba")
    ref = log_loss(ytr, proba, labels=[0, 1])
    worst = max(worst, abs(hand - ref))
print(f"  5 candidates compared; max |diff| = {worst:.2e}")
assert worst < 1e-10, "hand loss does not reproduce the sklearn pipeline"
print("  GATE PASSED")

section("S] NESTED SFS")
rows_curve, rows_path = [], []
t_all = time.time()
for t in (BIN[:1] if SMOKE else BIN):
    t0 = time.time()
    y = Yl[t].to_numpy(int)
    res = Parallel(n_jobs=-1)(
        delayed(sfs_fold)(i, y, DEPTH) for i in range(len(y)))
    for i, (path, _) in enumerate(res):
        for step, c in enumerate(path, 1):
            rows_path.append(dict(target=t, fold=i, step=step,
                                  feature=keep[c]))
    for d in range(1, DEPTH + 1):
        p = np.array([res[i][1][d - 1] for i in range(len(y))])
        rows_curve.append(dict(
            target=t, d=d,
            f1=f1_score(y, p, average="macro"),
            acc=accuracy_score(y, p),
            bacc=balanced_accuracy_score(y, p)))
    print(f"  {t:<28} done in {time.time()-t0:6.1f}s", flush=True)
curve = pd.DataFrame(rows_curve)
paths = pd.DataFrame(rows_path)
print(f"  total: {(time.time()-t_all)/60:.1f} min")

section("R] RESULT SUMMARY")
if not SMOKE:
    curve.to_csv(OUT_CURVE, index=False)
    paths.to_csv(OUT_PATHS, index=False)
    print(f"  written: {OUT_CURVE.relative_to(ROOT)} ({len(curve)} rows), "
          f"{OUT_PATHS.relative_to(ROOT)} ({len(paths)} rows)")
print("\n  best depth per target by bacc (exploration; max over the path):")
idx = curve.groupby("target")["bacc"].idxmax()
for _, r in curve.loc[idx].sort_values("bacc", ascending=False).iterrows():
    print(f"    {r['target']:<28} d={int(r['d']):>2}  bacc={r['bacc']:.3f}  "
          f"f1={r['f1']:.3f}  acc={r['acc']:.3f}")
print("\n  step-1 pick per target (folds agreeing on the most-chosen feature):")
for t in (BIN[:1] if SMOKE else BIN):
    s1 = paths[(paths["target"] == t) & (paths["step"] == 1)]["feature"]
    top = s1.value_counts()
    print(f"    {t:<28} {top.index[0]} ({top.iloc[0]}/{len(s1)})")

sys.stdout = sys.__stdout__
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                      capture_output=True, text=True).stdout.strip()
if not SMOKE:
    SNAP.write_text(
        "# sfs_logit.md -- verbatim stdout snapshot\n\n"
        "**Do not hand-edit.** To update, re-run the producing script and let "
        "it overwrite this file.\n\n"
        "- Producing script: `analysis/72_sfs_logit.py`\n"
        f"- Repository HEAD when this snapshot was generated: `{head}`\n"
        "- Reproduce with: `.venv/bin/python analysis/72_sfs_logit.py`\n\n"
        "```text\n" + buf.getvalue() + "\n```\n",
        encoding="utf-8")
    print(f"\nsnapshot written: {SNAP.relative_to(ROOT)}")
else:
    print("\nSMOKE run: no csv, no snapshot")
