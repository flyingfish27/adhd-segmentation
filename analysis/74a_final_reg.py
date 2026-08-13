# -*- coding: utf-8 -*-
# =============================================================================
# 74a_final_reg.py -- FS-D10: the regression delivery.  10 continuous targets,
# nested-K ridge (user decision 2026-08-13 from the 73a curves), full-sample
# refit, serialised models.  Mirrors 74_final_clf.py exactly, with:
#   selector  f_regression   inner criterion  summed LOO-23 squared error
#   model     REG['ridge'] lifted from 45_multivariate_cv.py via ast
#   metrics   rmse / mae / Spearman rho / skill (production reg_skill)
# Inner K grid 1..20, ties -> smaller K.  No class-vanishing issue exists in
# regression, so no inner-split skipping is needed.
#
# Gates: V1 -- lifted reg_pipe reproduces all main-arm ridge rows of
# B_multivariate.csv (k in {5,10}) cell for cell on the 608-column table;
# G2 -- fixed-K hand loop equals the sklearn pipeline on the 512 set;
# G3 -- determinism; round-trip -- reloaded joblib predictions equal the
# in-script refit predictions.
#
# Outputs: analysis/final_reg_metrics.csv, final_reg_features.csv,
# final_reg_folds.csv, outputs/models/<target>__reg.joblib (10 files),
# analysis/probe_outputs/final_reg.md.
# Reproduce with: .venv/bin/python analysis/74a_final_reg.py  (SMOKE=1 shrinks)
# =============================================================================
import ast, io, os, pathlib, subprocess, sys, time, warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("PYTHONWARNINGS", "ignore")

import joblib
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.stats import spearmanr
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import (SelectKBest, f_regression,
                                       VarianceThreshold)
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_predict, LeaveOneOut

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SNAP = HERE / "probe_outputs" / "final_reg.md"
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


src = (HERE / "45_multivariate_cv.py").read_text()
tree = ast.parse(src)
wanted = {}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in ("reg_pipe",
                                                          "reg_skill"):
        wanted[node.name] = node
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == "REG":
                wanted["REG"] = node
ns = dict(Pipeline=Pipeline, VarianceThreshold=VarianceThreshold,
          SelectKBest=SelectKBest, f_regression=f_regression,
          StandardScaler=StandardScaler, Ridge=Ridge, SVR=SVR,
          RandomForestRegressor=RandomForestRegressor, np=np)
mod = ast.Module(body=[wanted["reg_pipe"], wanted["reg_skill"],
                       wanted["REG"]], type_ignores=[])
exec(compile(ast.fix_missing_locations(mod), "<45_extract>", "exec"), ns)
reg_pipe, reg_skill, make_ridge = ns["reg_pipe"], ns["reg_skill"], ns["REG"]["ridge"]

X = pd.read_csv(ROOT / "analysis/features.csv").set_index("subject")
Yc = pd.read_csv(ROOT / "analysis/targets.csv").set_index("subject")
CONT = list(Yc.columns)
keep = pd.read_csv(ROOT / "analysis/feature_keeplist_512.csv")["feature"].tolist()
X608 = X.to_numpy(float)
X512 = X[keep].to_numpy(float)

section("0] SETUP")
print(f"  model: ridge lifted from 45 (REG['ridge'])   targets: {len(CONT)}")
print(f"  inner K grid: 1..{KS_INNER[-1]}   pool: {X512.shape[1]}   SMOKE: {SMOKE}")


def metrics(y, pred):
    return dict(rmse=float(np.sqrt(np.mean((y - pred) ** 2))),
                mae=float(np.mean(np.abs(y - pred))),
                rho=float(spearmanr(y, pred).statistic),
                skill=float(reg_skill(y, pred)))


def scale_cols(train, test):
    mu, sd = train.mean(0), train.std(0)
    sd = np.where(sd == 0.0, 1.0, sd)
    return (train - mu) / sd, (test - mu) / sd


def rank_features(Xtr, ytr):
    F, _ = f_regression(Xtr, ytr)
    F = np.where(np.isnan(F), -np.inf, F)
    return np.argsort(F, kind="mergesort")


def choose_k(Xtr, ytr, ks):
    """summed inner-LOO squared error per K; ties -> smaller K (first argmin)"""
    losses = np.zeros(len(ks))
    for j in range(len(ytr)):
        m = np.ones(len(ytr), bool)
        m[j] = False
        A, b = scale_cols(Xtr[m], Xtr[[j]])
        order = rank_features(Xtr[m], ytr[m])
        for ki, k in enumerate(ks):
            idx = np.sort(order[-k:])
            mdl = make_ridge()
            mdl.fit(A[:, idx], ytr[m])
            losses[ki] += float((mdl.predict(b[:, idx])[0] - ytr[j]) ** 2)
    return ks[int(np.argmin(losses))], losses


def fit_at_k(Xtr, ytr, Xte, k):
    order = rank_features(Xtr, ytr)
    idx = np.sort(order[-k:])
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd = np.where(sd == 0.0, 1.0, sd)
    mdl = make_ridge()
    mdl.fit(((Xtr - mu) / sd)[:, idx], ytr)
    pred = mdl.predict(((Xte - mu) / sd)[:, idx])
    return pred, idx, mdl, mu, sd


def outer_fold(i, y):
    tr = np.ones(len(y), bool)
    tr[i] = False
    k_star, _ = choose_k(X512[tr], y[tr], KS_INNER)
    pred, idx, _, _, _ = fit_at_k(X512[tr], y[tr], X512[[i]], k_star)
    return float(pred[0]), k_star, [keep[c] for c in idx]


section("V1] PRODUCTION REPRODUCTION -- ridge rows, reg main arm")
B = pd.read_csv(ROOT / "analysis/B_multivariate.csv")
rows = B[(B["variant"] == "main") & (B["track"] == "reg")
         & (B["model"] == "ridge")]
if SMOKE:
    rows = rows.head(4)
worst = 0.0
for _, r in rows.iterrows():
    y = Yc[r["target"]].to_numpy(float)
    pred = cross_val_predict(reg_pipe(make_ridge(), int(r["k"])), X608, y,
                             cv=LeaveOneOut(), n_jobs=-1)
    mine = metrics(y, pred)
    worst = max(worst, max(abs(mine[m] - r[m])
                           for m in ("rmse", "mae", "rho", "skill")))
print(f"  {len(rows)} combinations; max |diff| = {worst:.2e}")
assert worst < 1e-9
print("  GATE PASSED")

section("G2] FIXED-K EQUIVALENCE on the 512-column set")
bad = 0
for t in [CONT[0]]:
    y = Yc[t].to_numpy(float)
    for k in (1, 5, 12):
        ref = cross_val_predict(reg_pipe(make_ridge(), k), X512, y,
                                cv=LeaveOneOut(), n_jobs=-1)
        mine = np.array([fit_at_k(X512[np.arange(24) != i],
                                  y[np.arange(24) != i], X512[[i]], k)[0][0]
                         for i in range(24)])
        bad += int(not np.allclose(ref, mine, rtol=0, atol=1e-10))
print(f"  1 target x 3 K compared; mismatches = {bad}")
assert bad == 0
print("  GATE PASSED")

section("G3] DETERMINISM")
y0 = Yc[CONT[0]].to_numpy(float)
assert outer_fold(0, y0) == outer_fold(0, y0)
print("  fold 0 recomputed twice: identical -- GATE PASSED")

section("S] NESTED DELIVERY RUN")
MODELDIR.mkdir(parents=True, exist_ok=True)
metrics_rows, feat_rows, fold_rows = [], [], []
t_all = time.time()
for t in (CONT[:2] if SMOKE else CONT):
    t0 = time.time()
    y = Yc[t].to_numpy(float)
    res = Parallel(n_jobs=-1)(
        delayed(outer_fold)(i, y) for i in range(len(y)))
    preds = np.array([r[0] for r in res])
    kstars = [r[1] for r in res]
    for i, r in enumerate(res):
        fold_rows.append(dict(target=t, track="reg", fold=i, k_star=r[1],
                              features=";".join(r[2])))
    k_final, _ = choose_k(X512, y, KS_INNER)
    _, idx, mdl, mu, sd = fit_at_k(X512, y, X512, k_final)
    feats = [keep[c] for c in idx]
    for rank, f in enumerate(feats, 1):
        feat_rows.append(dict(target=t, track="reg", rank=rank, feature=f,
                              coef=float(mdl.coef_[rank - 1])))
    feat_rows.append(dict(target=t, track="reg", rank=0,
                          feature="(intercept)", coef=float(mdl.intercept_)))
    payload = dict(target=t, track="reg", features=feats, k_final=k_final,
                   mu=mu[idx], sd=sd[idx], model=mdl,
                   note="X[features] -> (x-mu)/sd -> model.predict")
    path = MODELDIR / f"{t}__reg.joblib"
    joblib.dump(payload, path)
    loaded = joblib.load(path)
    Xsel = X[loaded["features"]].to_numpy(float)
    rp = loaded["model"].predict((Xsel - loaded["mu"]) / loaded["sd"])
    ip = mdl.predict(((X512 - mu) / sd)[:, idx])
    assert np.allclose(rp, ip, rtol=0, atol=1e-12)
    mrow = metrics(y, preds)
    metrics_rows.append(dict(target=t, track="reg", **mrow,
                             k_star_median=float(np.median(kstars)),
                             k_star_min=min(kstars), k_star_max=max(kstars),
                             k_final=k_final))
    print(f"  {t:<20} skill={mrow['skill']:+.3f} rmse={mrow['rmse']:.3f} "
          f"K*: med={np.median(kstars):.0f} range={min(kstars)}-{max(kstars)} "
          f"K_final={k_final}  ({time.time()-t0:5.1f}s)", flush=True)
print(f"  total: {(time.time()-t_all)/60:.1f} min")

section("R] DELIVERY SUMMARY")
met = pd.DataFrame(metrics_rows)
if not SMOKE:
    met.to_csv(ROOT / "analysis/final_reg_metrics.csv", index=False)
    pd.DataFrame(feat_rows).to_csv(ROOT / "analysis/final_reg_features.csv",
                                   index=False)
    pd.DataFrame(fold_rows).to_csv(ROOT / "analysis/final_reg_folds.csv",
                                   index=False)
    print(f"  written: final_reg_metrics.csv, final_reg_features.csv, "
          f"final_reg_folds.csv, {len(metrics_rows)} joblib files")
print("\n  DECLARATIONS: no significance testing; nested numbers cover the "
      "full f_regression-rank+auto-K+ridge procedure; skill <= 0 means the "
      "delivered model does not beat predicting the mean and is shipped as "
      "such; scale caveats as recorded for the classification delivery.\n")
for _, r in met.sort_values("skill", ascending=False).iterrows():
    print(f"    {r['target']:<20} skill={r['skill']:+.3f}  "
          f"rmse={r['rmse']:.3f}  mae={r['mae']:.3f}  rho={r['rho']:+.3f}  "
          f"K_final={int(r['k_final'])}")

sys.stdout = sys.__stdout__
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                      capture_output=True, text=True).stdout.strip()
if not SMOKE:
    SNAP.write_text(
        "# final_reg.md -- verbatim stdout snapshot\n\n"
        "**Do not hand-edit.** To update, re-run the producing script and let "
        "it overwrite this file.\n\n"
        "- Producing script: `analysis/74a_final_reg.py`\n"
        f"- Repository HEAD when this snapshot was generated: `{head}`\n"
        "- Reproduce with: `.venv/bin/python analysis/74a_final_reg.py`\n\n"
        "```text\n" + buf.getvalue() + "\n```\n",
        encoding="utf-8")
    print(f"\nsnapshot written: {SNAP.relative_to(ROOT)}")
else:
    print("\nSMOKE run: no csv/snapshot")
