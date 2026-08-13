# -*- coding: utf-8 -*-
# =============================================================================
# 73_reg_kgrid.py -- FS-D10 step 1: the regression twin of the K-grid screen,
# run so the user can pick the regression model for the final delivery
# (decision 2026-08-13: "回归三模型先扫再选").
#
# 10 continuous targets (analysis/targets.csv) x ridge / svr / rf-regression
# x K = 1..512, leave-one-out, no permutations.  reg_pipe / REG / reg_skill
# are lifted from 45_multivariate_cv.py via ast; the selector is
# f_regression (the FS-D9 criterion's regression counterpart).  Metrics per
# combination, computed once over the 24 collected LOO predictions exactly as
# production does: rmse, mae, Spearman rho, skill (= 1 - rmse / dummy-rmse).
#
# Gates before the sweep (the 71 pattern):
#   V1 production reproduction -- lifted reg_pipe on the full 608-column
#      table must reproduce all 60 main-arm reg rows of B_multivariate.csv
#      (10 targets x 3 models x k in {5,10}) cell for cell.
#   V2 loop equivalence -- the fast shared-ranking LOO loop must equal the
#      sklearn pipeline prediction-for-prediction at probe K values
#      (selected indices re-sorted to original order: rf is column-order
#      sensitive, the lesson from 71's first smoke).
#
# Outputs: analysis/kgrid_reg.csv (15,360 rows) and the stdout snapshot
# analysis/probe_outputs/kgrid_reg.md.
# Reproduce with: .venv/bin/python analysis/73_reg_kgrid.py   (SMOKE=1 shrinks)
# =============================================================================
import ast, io, os, pathlib, subprocess, sys, time, warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("PYTHONWARNINGS", "ignore")

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.stats import rankdata, spearmanr
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
SNAP = HERE / "probe_outputs" / "kgrid_reg.md"
OUT = ROOT / "analysis" / "kgrid_reg.csv"
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


# ---- lift reg_pipe / REG / reg_skill from production ------------------------
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
assert set(wanted) == {"reg_pipe", "reg_skill", "REG"}
ns = dict(Pipeline=Pipeline, VarianceThreshold=VarianceThreshold,
          SelectKBest=SelectKBest, f_regression=f_regression,
          StandardScaler=StandardScaler, Ridge=Ridge, SVR=SVR,
          RandomForestRegressor=RandomForestRegressor, np=np)
mod = ast.Module(body=[wanted["reg_pipe"], wanted["reg_skill"],
                       wanted["REG"]], type_ignores=[])
exec(compile(ast.fix_missing_locations(mod), "<45_extract>", "exec"), ns)
reg_pipe, reg_skill, REG = ns["reg_pipe"], ns["reg_skill"], ns["REG"]
MODELS = list(REG)  # ridge, svr, rf

X = pd.read_csv(ROOT / "analysis/features.csv").set_index("subject")
Yc = pd.read_csv(ROOT / "analysis/targets.csv").set_index("subject")
CONT = list(Yc.columns)
keep = pd.read_csv(ROOT / "analysis/feature_keeplist_512.csv")["feature"].tolist()
X608 = X.to_numpy(float)
X512 = X[keep].to_numpy(float)
loo = LeaveOneOut()

section("0] SETUP")
print(f"  models lifted from 45: {MODELS}   continuous targets: {len(CONT)}")
print(f"  full table {X608.shape}, keep-list set {X512.shape}   SMOKE: {SMOKE}")


def metrics(y, pred):
    return dict(rmse=float(np.sqrt(np.mean((y - pred) ** 2))),
                mae=float(np.mean(np.abs(y - pred))),
                rho=float(spearmanr(y, pred).statistic),
                skill=float(reg_skill(y, pred)))


section("V1] PRODUCTION REPRODUCTION -- reg main arm of B_multivariate.csv")
B = pd.read_csv(ROOT / "analysis/B_multivariate.csv")
rows = B[(B["variant"] == "main") & (B["track"] == "reg")]
if SMOKE:
    rows = rows[rows["target"].isin(CONT[:2])]
worst = 0.0
t0 = time.time()
for _, r in rows.iterrows():
    y = Yc[r["target"]].to_numpy(float)
    pred = cross_val_predict(reg_pipe(REG[r["model"]](), int(r["k"])),
                             X608, y, cv=loo, n_jobs=-1)
    mine = metrics(y, pred)
    worst = max(worst, max(abs(mine[m] - r[m])
                           for m in ("rmse", "mae", "rho", "skill")))
print(f"  {len(rows)} combinations recomputed in {time.time()-t0:.0f}s; "
      f"max |diff| vs committed table = {worst:.2e}")
assert worst < 1e-9, "production reproduction FAILED"
print("  GATE PASSED")


def fold_preds(Xv, y, i, Ks, models):
    tr = np.ones(len(y), bool)
    tr[i] = False
    Xtr, Xte = Xv[tr], Xv[[i]]
    m_keep = Xtr.var(axis=0) > 0.0
    Xtr, Xte = Xtr[:, m_keep], Xte[:, m_keep]
    F, _ = f_regression(Xtr, y[tr])
    F = np.where(np.isnan(F), -np.inf, F)
    order = np.argsort(F, kind="mergesort")
    out = {}
    for k in Ks:
        idx = np.sort(order[-min(k, Xtr.shape[1]):])   # original column order
        sc = StandardScaler().fit(Xtr[:, idx])
        A, Bte = sc.transform(Xtr[:, idx]), sc.transform(Xte[:, idx])
        for m in models:
            mdl = REG[m]()
            mdl.fit(A, y[tr])
            out[(k, m)] = float(mdl.predict(Bte)[0])
    return out


def sweep_target(y, Ks):
    per_fold = Parallel(n_jobs=-1)(
        delayed(fold_preds)(X512, y, i, Ks, MODELS) for i in range(len(y)))
    return {(k, m): np.array([per_fold[i][(k, m)] for i in range(len(y))])
            for k in Ks for m in MODELS}


section("V2] LOOP EQUIVALENCE on the 512-column set")
vb_targets = CONT[:1] if SMOKE else [CONT[0], CONT[-1]]
vb_ks = [1, 10, 101] if SMOKE else [1, 5, 10, 50, 101, 400]
bad = 0
for t in vb_targets:
    y = Yc[t].to_numpy(float)
    preds = sweep_target(y, vb_ks)
    for k in vb_ks:
        for m in MODELS:
            ref = cross_val_predict(reg_pipe(REG[m](), k), X512, y,
                                    cv=loo, n_jobs=-1)
            if not np.allclose(ref, preds[(k, m)], rtol=0, atol=1e-10):
                bad += 1
                print(f"  MISMATCH {t} {m} k={k}")
print(f"  compared {len(vb_targets)}x{len(vb_ks)}x{len(MODELS)}; "
      f"mismatches = {bad}")
assert bad == 0
print("  GATE PASSED")

section("S] FULL SWEEP")
KS_ALL = list(range(1, 9)) if SMOKE else list(range(1, 513))
targets = CONT[:1] if SMOKE else CONT
print(f"  grid: {len(targets)} targets x {len(MODELS)} models x "
      f"{len(KS_ALL)} K values")
rows_out = []
t_all = time.time()
for t in targets:
    t0 = time.time()
    y = Yc[t].to_numpy(float)
    preds = sweep_target(y, KS_ALL)
    for m in MODELS:
        for k in KS_ALL:
            rows_out.append(dict(target=t, model=m, k=k,
                                 **metrics(y, preds[(k, m)])))
    print(f"  {t:<20} done in {time.time()-t0:6.1f}s", flush=True)
res = pd.DataFrame(rows_out)
print(f"  sweep total: {(time.time()-t_all)/60:.1f} min")

section("R] RESULT SUMMARY")
if not SMOKE:
    res.to_csv(OUT, index=False)
    print(f"  written: {OUT.relative_to(ROOT)}  ({len(res)} rows)")
print("\n  best K per (target, model) by skill (exploration numbers; "
      "skill > 0 = beats predicting the mean):")
idx = res.groupby(["target", "model"])["skill"].idxmax()
for _, r in res.loc[idx].sort_values("skill", ascending=False).iterrows():
    print(f"    {r['target']:<20} {r['model']:<6} k={int(r['k']):>3}  "
          f"skill={r['skill']:+.3f}  rmse={r['rmse']:.3f}  "
          f"mae={r['mae']:.3f}  rho={r['rho']:+.3f}")

sys.stdout = sys.__stdout__
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                      capture_output=True, text=True).stdout.strip()
if not SMOKE:
    SNAP.write_text(
        "# kgrid_reg.md -- verbatim stdout snapshot\n\n"
        "**Do not hand-edit.** To update, re-run the producing script and let "
        "it overwrite this file.\n\n"
        "- Producing script: `analysis/73_reg_kgrid.py`\n"
        f"- Repository HEAD when this snapshot was generated: `{head}`\n"
        "- Reproduce with: `.venv/bin/python analysis/73_reg_kgrid.py`\n\n"
        "```text\n" + buf.getvalue() + "\n```\n",
        encoding="utf-8")
    print(f"\nsnapshot written: {SNAP.relative_to(ROOT)}")
else:
    print("\nSMOKE run: no csv, no snapshot")
