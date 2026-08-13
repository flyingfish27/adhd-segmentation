# -*- coding: utf-8 -*-
# =============================================================================
# 74_final_clf.py -- FS-D10: the classification delivery.  10 binary + 14
# multiclass targets, nested-K logit, full-sample refit, serialised models.
#
# Spec (user decisions 2026-08-13, ledger TASK-124 / FS-D10):
#   nested evaluation : outer LOO-24.  Inside each fold: for every inner
#     LOO-23 split, rank the 512 features by f_classif on the 22 inner-train
#     subjects and, for K = 1..20, fit logit on the top-K and score the inner
#     held-out subject's log-loss.  K* = the K with the smallest summed inner
#     log-loss (ties -> smaller K, declared).  Then rank on the full 23, take
#     the top K*, fit logit, predict the outer held-out child.  The 24
#     collected predictions give f1(macro)/acc/bacc -- numbers that honestly
#     cover the whole "F-rank + auto-K + logit" procedure.
#   final refit       : the same K-selection rule run once on all 24 subjects
#     (LOO-24 as the inner loop) -> K_final; rank on all 24, take the top
#     K_final, fit logit on everyone.  That fitted object IS the deliverable;
#     the nested metrics are its performance estimate.
#   model             : CLF['logit'] lifted from 45_multivariate_cv.py via
#     ast; multiclass targets use the same estimator (multinomial), exactly
#     as production 45 does.
#   feature pool      : analysis/feature_keeplist_512.csv (frozen, FS-D5).
#   declared          : no significance testing in this delivery; per-class
#     n is 6-8 for the multiclass targets; scale caveats for sdq_peer /
#     sdq_pro; yaw_bp_hf carries on-record wear-artifact and duration
#     caveats; track A is retired as a reference.
#
# Gates before the sweep:
#   V1 production reproduction -- lifted clf_pipe on the full 608-column
#      table must reproduce every main-arm logit row of B_multivariate.csv
#      (bin AND multi, k in {5,10}) cell for cell.
#   G2 fixed-K equivalence -- with the inner selection bypassed and K forced,
#      the hand loop must equal cross_val_predict of the sklearn pipeline
#      prediction-for-prediction on the 512-column set.
#   G3 determinism -- one fold recomputed twice, bit-identical.
#   Round-trip     -- every saved joblib is loaded back and its predictions
#      on the 24 subjects must equal the in-script refit predictions.
#
# Outputs: analysis/final_clf_metrics.csv   (24 rows)
#          analysis/final_clf_features.csv  (final feature lists + coefs)
#          analysis/final_clf_folds.csv     (per-fold K* and features)
#          outputs/models/<target>__clf.joblib  (24 files)
#          analysis/probe_outputs/final_clf.md  (stdout snapshot)
# Reproduce with: .venv/bin/python analysis/74_final_clf.py   (SMOKE=1 shrinks)
# =============================================================================
import ast, io, os, pathlib, subprocess, sys, time, warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("PYTHONWARNINGS", "ignore")

import joblib
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
SNAP = HERE / "probe_outputs" / "final_clf.md"
MODELDIR = ROOT / "outputs" / "models"
KS_INNER = list(range(1, 21))
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


# ---- lift clf_pipe / CLF from production ------------------------------------
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
ns = dict(Pipeline=Pipeline, VarianceThreshold=VarianceThreshold,
          SelectKBest=SelectKBest, f_classif=f_classif,
          StandardScaler=StandardScaler, LogisticRegression=LogisticRegression,
          SVC=SVC, RandomForestClassifier=RandomForestClassifier)
mod = ast.Module(body=[wanted["clf_pipe"], wanted["CLF"]], type_ignores=[])
exec(compile(ast.fix_missing_locations(mod), "<45_extract>", "exec"), ns)
clf_pipe, make_logit = ns["clf_pipe"], ns["CLF"]["logit"]

# ---- inputs -----------------------------------------------------------------
X = pd.read_csv(ROOT / "analysis/features.csv").set_index("subject")
Yl = pd.read_csv(ROOT / "analysis/target_labels.csv").set_index("subject")
Ylm = pd.read_csv(ROOT / "analysis/target_labels_meta.csv")
DEGEN = set(Ylm.loc[Ylm["degenerate"] == True, "label_name"])
BIN = [c for c in Yl.columns if c.endswith("__qbin") and c not in DEGEN]
MULTI = [c for c in Yl.columns
         if c.endswith(("__qter", "__qquar")) and c not in DEGEN]
keep = pd.read_csv(ROOT / "analysis/feature_keeplist_512.csv")["feature"].tolist()
X608 = X.to_numpy(float)
X512 = X[keep].to_numpy(float)
TARGETS = [(t, "bin") for t in BIN] + [(t, "multi") for t in MULTI]

section("0] SETUP")
print(f"  targets: {len(BIN)} bin + {len(MULTI)} multi = {len(TARGETS)}")
print(f"  inner K grid: 1..{KS_INNER[-1]}   pool: {X512.shape[1]} columns   "
      f"SMOKE: {SMOKE}")


def scale_cols(train, test):
    mu, sd = train.mean(0), train.std(0)
    sd = np.where(sd == 0.0, 1.0, sd)
    return (train - mu) / sd, (test - mu) / sd


def rank_features(Xtr, ytr):
    """f_classif ranking; returns column indices, best last (sklearn order)"""
    F, _ = f_classif(Xtr, ytr)
    F = np.where(np.isnan(F), -np.inf, F)
    return np.argsort(F, kind="mergesort")


def choose_k(Xtr, ytr, ks):
    """summed inner-LOO log-loss for every K; returns (k_star, loss_per_k).

    Inner splits whose held-out subject is the ONLY member of its class
    within this training set are skipped: the inner model cannot contain
    that class, so its log-loss is undefined.  The skip applies to every K
    identically, so the K comparison stays fair.  This arises for quartile
    labels with a 2-subject class (e.g. snap_hyper__qquar, 11/2/7/4) and is
    declared in the delivery notes."""
    losses = np.zeros(len(ks))
    for j in range(len(ytr)):
        m = np.ones(len(ytr), bool)
        m[j] = False
        if not (ytr[m] == ytr[j]).any():
            continue
        A, b = scale_cols(Xtr[m], Xtr[[j]])
        order = rank_features(Xtr[m], ytr[m])
        for ki, k in enumerate(ks):
            idx = np.sort(order[-k:])
            mdl = make_logit()
            mdl.fit(A[:, idx], ytr[m])
            p = mdl.predict_proba(b[:, idx])[0]
            losses[ki] -= np.log(p[list(mdl.classes_).index(ytr[j])])
    k_star = ks[int(np.argmin(losses))]      # argmin takes the FIRST minimum
    return k_star, losses                     # -> ties break to smaller K


def fit_at_k(Xtr, ytr, Xte, k):
    """rank on Xtr, top-k, scale, fit logit; returns (pred, idx, model, mu, sd)"""
    order = rank_features(Xtr, ytr)
    idx = np.sort(order[-k:])
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd = np.where(sd == 0.0, 1.0, sd)
    mdl = make_logit()
    mdl.fit(((Xtr - mu) / sd)[:, idx], ytr)
    pred = mdl.predict(((Xte - mu) / sd)[:, idx])
    return pred, idx, mdl, mu, sd


def outer_fold(i, y):
    tr = np.ones(len(y), bool)
    tr[i] = False
    k_star, _ = choose_k(X512[tr], y[tr], KS_INNER)
    pred, idx, _, _, _ = fit_at_k(X512[tr], y[tr], X512[[i]], k_star)
    return int(pred[0]), k_star, [keep[c] for c in idx]


section("V1] PRODUCTION REPRODUCTION -- logit rows, bin AND multi main arm")
B = pd.read_csv(ROOT / "analysis/B_multivariate.csv")
rows = B[(B["variant"] == "main") & (B["model"] == "logit")
         & (B["track"].isin(["bin", "multi"]))]
if SMOKE:
    rows = rows.groupby("track").head(2)
worst = 0.0
t0 = time.time()
for _, r in rows.iterrows():
    y = Yl[r["target"]].to_numpy(int)
    pred = cross_val_predict(clf_pipe(make_logit(), int(r["k"])), X608, y,
                             cv=LeaveOneOut(), n_jobs=-1)
    mine = dict(f1=f1_score(y, pred, average="macro"),
                acc=accuracy_score(y, pred),
                bacc=balanced_accuracy_score(y, pred))
    worst = max(worst, max(abs(mine[m] - r[m]) for m in ("f1", "acc", "bacc")))
print(f"  {len(rows)} combinations recomputed in {time.time()-t0:.0f}s; "
      f"max |diff| = {worst:.2e}")
assert worst < 1e-9
print("  GATE PASSED")

section("G2] FIXED-K EQUIVALENCE on the 512-column set")
bad = 0
for t in [BIN[0], MULTI[0]]:
    y = Yl[t].to_numpy(int)
    for k in (1, 5, 12):
        ref = cross_val_predict(clf_pipe(make_logit(), k), X512, y,
                                cv=LeaveOneOut(), n_jobs=-1)
        mine = np.array([fit_at_k(X512[np.arange(24) != i],
                                  y[np.arange(24) != i],
                                  X512[[i]], k)[0][0] for i in range(24)])
        bad += int(not np.array_equal(ref, mine))
print(f"  2 targets x 3 K compared; mismatches = {bad}")
assert bad == 0
print("  GATE PASSED")

section("G3] DETERMINISM")
y0 = Yl[BIN[0]].to_numpy(int)
assert outer_fold(0, y0) == outer_fold(0, y0)
print("  fold 0 recomputed twice: identical -- GATE PASSED")

section("S] NESTED DELIVERY RUN")
MODELDIR.mkdir(parents=True, exist_ok=True)
metrics_rows, feat_rows, fold_rows = [], [], []
t_all = time.time()
for t, track in (TARGETS[:1] + TARGETS[10:11] if SMOKE else TARGETS):
    t0 = time.time()
    y = Yl[t].to_numpy(int)
    res = Parallel(n_jobs=-1)(
        delayed(outer_fold)(i, y) for i in range(len(y)))
    preds = np.array([r[0] for r in res])
    kstars = [r[1] for r in res]
    for i, r in enumerate(res):
        fold_rows.append(dict(target=t, track=track, fold=i, k_star=r[1],
                              features=";".join(r[2])))
    # final refit on all 24 with the same K rule
    k_final, _ = choose_k(X512, y, KS_INNER)
    _, idx, mdl, mu, sd = fit_at_k(X512, y, X512, k_final)
    feats = [keep[c] for c in idx]
    coefs = np.atleast_2d(mdl.coef_)
    for rank, (c, f) in enumerate(zip(idx, feats), 1):
        row = dict(target=t, track=track, rank=rank, feature=f)
        for ci in range(coefs.shape[0]):
            row[f"coef_c{ci}"] = coefs[ci, rank - 1]
        feat_rows.append(row)
    for ci, b0 in enumerate(np.atleast_1d(mdl.intercept_)):
        feat_rows.append(dict(target=t, track=track, rank=0,
                              feature="(intercept)", **{f"coef_c{ci}": b0}))
    payload = dict(target=t, track=track, features=feats, k_final=k_final,
                   mu=mu[idx], sd=sd[idx], model=mdl,
                   classes=list(mdl.classes_),
                   note="X[features] -> (x-mu)/sd -> model.predict")
    path = MODELDIR / f"{t}__clf.joblib"
    joblib.dump(payload, path)
    loaded = joblib.load(path)
    Xsel = X[loaded["features"]].to_numpy(float)
    rp = loaded["model"].predict((Xsel - loaded["mu"]) / loaded["sd"])
    ip = mdl.predict(((X512 - mu) / sd)[:, idx])
    assert np.array_equal(rp, ip), f"joblib round-trip failed for {t}"
    ncls = len(np.unique(y))
    metrics_rows.append(dict(
        target=t, track=track, n_classes=ncls,
        class_sizes="/".join(map(str, np.bincount(y))),
        chance=round(1.0 / ncls, 3),
        f1=f1_score(y, preds, average="macro"),
        acc=accuracy_score(y, preds),
        bacc=balanced_accuracy_score(y, preds),
        k_star_median=float(np.median(kstars)),
        k_star_min=min(kstars), k_star_max=max(kstars),
        k_final=k_final))
    print(f"  {t:<28} bacc={metrics_rows[-1]['bacc']:.3f} "
          f"K*: med={np.median(kstars):.0f} range={min(kstars)}-{max(kstars)} "
          f"K_final={k_final}  ({time.time()-t0:5.1f}s)", flush=True)
print(f"  total: {(time.time()-t_all)/60:.1f} min")

section("R] DELIVERY SUMMARY")
met = pd.DataFrame(metrics_rows)
if not SMOKE:
    met.to_csv(ROOT / "analysis/final_clf_metrics.csv", index=False)
    pd.DataFrame(feat_rows).to_csv(ROOT / "analysis/final_clf_features.csv",
                                   index=False)
    pd.DataFrame(fold_rows).to_csv(ROOT / "analysis/final_clf_folds.csv",
                                   index=False)
    print("  written: final_clf_metrics.csv, final_clf_features.csv, "
          "final_clf_folds.csv, and "
          f"{len(metrics_rows)} joblib files under outputs/models/")
print("\n  DECLARATIONS: no significance testing in this delivery; nested "
      "numbers cover the full F-rank+auto-K+logit procedure; multiclass "
      "targets have 6-8 children per class; sdq_peer (4 of 5 items) and "
      "sdq_pro (reverse-scored control) carry scale caveats; yaw_bp_hf "
      "carries on-record wear-artifact and duration-confound caveats; "
      "track A is retired as a reference.\n")
for _, r in met.sort_values("bacc", ascending=False).iterrows():
    print(f"    {r['target']:<28} {r['track']:<5} bacc={r['bacc']:.3f} "
          f"(chance {r['chance']:.2f})  f1={r['f1']:.3f}  "
          f"K_final={int(r['k_final'])}")

sys.stdout = sys.__stdout__
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                      capture_output=True, text=True).stdout.strip()
if not SMOKE:
    SNAP.write_text(
        "# final_clf.md -- verbatim stdout snapshot\n\n"
        "**Do not hand-edit.** To update, re-run the producing script and let "
        "it overwrite this file.\n\n"
        "- Producing script: `analysis/74_final_clf.py`\n"
        f"- Repository HEAD when this snapshot was generated: `{head}`\n"
        "- Reproduce with: `.venv/bin/python analysis/74_final_clf.py`\n\n"
        "```text\n" + buf.getvalue() + "\n```\n",
        encoding="utf-8")
    print(f"\nsnapshot written: {SNAP.relative_to(ROOT)}")
else:
    print("\nSMOKE run: no csv, no snapshot, models written to outputs/models/")
