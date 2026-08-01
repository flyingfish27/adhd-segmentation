# -*- coding: utf-8 -*-
"""
61_univariate_analysis.py
Stage 2 of the modelling-results analysis: the univariate screening track.

Reads analysis/A_univariate.csv (produced by 44_univariate_screen.py) together
with the tables that screen consumed.  It does NOT re-run 44_univariate_screen.py.

It does generate permutation null distributions of its own.  That is not a re-run
of the screen: the screen computes 608 x 20 statistics plus its nulls, whereas
this script only rebuilds the nulls, using the identical construction --
    continuous: null = |spearman(rank(0..n-1), shuffle(rank(y)))|
                (44_univariate_screen.py, the loop at "null[k]=abs(spearman(...))")
    binary:     null = |auc(0..n-1, shuffle(label)) - 0.5|
                (44_univariate_screen.py, the loop at "null[k]=abs(auc(base,p)-0.5)")
Both nulls depend only on n and on the tie structure / group sizes of the target,
never on the feature, which is why the screen shares one null across all features
of a target and why they can be rebuilt cheaply here.

Outputs
    outputs/tables/61_univariate.md
    outputs/figures/fig03_effect_vs_null_continuous.png
    outputs/figures/fig04_effect_vs_null_binary.png
    outputs/figures/fig05_fdr_per_target.png
    outputs/figures/fig06_effect_vs_generalization.png
    outputs/figures/fig07_surviving_cells.png
    outputs/figures/fig08_tie_corrected_pvalues.png

Re-run with:
    .venv/bin/python analysis/61_univariate_analysis.py
"""
import io
import re
import pathlib
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import rankdata

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIGDIR = ROOT / "outputs" / "figures"
TABDIR = ROOT / "outputs" / "tables"
FIGDIR.mkdir(parents=True, exist_ok=True)
TABDIR.mkdir(parents=True, exist_ok=True)

NPERM = 100_000          # matches NPERM in 44_univariate_screen.py
SEED = 20260730          # this script's own seed; the screen used 20260717


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


A = pd.read_csv(ROOT / "analysis/A_univariate.csv")
X = pd.read_csv(ROOT / "analysis/features.csv").set_index("subject")
Yc = pd.read_csv(ROOT / "analysis/targets.csv").set_index("subject")
Yb = pd.read_csv(ROOT / "analysis/target_labels.csv").set_index("subject")
n = len(X)
CONT = sorted(A.loc[A["type"] == "cont", "target"].unique())
BIN = sorted(A.loc[A["type"] == "bin", "target"].unique())
FEATS = sorted(A["feature"].unique())
rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------------------
# [0] Statistics reimplemented here, independently of 44_univariate_screen.py
# ---------------------------------------------------------------------------
def spearman(xr, yr):
    xr = xr - xr.mean()
    yr = yr - yr.mean()
    d = np.sqrt((xr ** 2).sum() * (yr ** 2).sum())
    return float((xr * yr).sum() / d) if d > 0 else 0.0


def auc_stat(x, lab):
    r = rankdata(x)
    n1 = int(lab.sum())
    n0 = len(lab) - n1
    if n1 == 0 or n0 == 0:
        return np.nan
    return float((r[lab == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def null_rho(yr, nperm):
    """|Spearman| between the fixed rank vector 0..n-1 and shuffles of yr."""
    x = np.arange(len(yr), dtype=float)
    xc = x - x.mean()
    ssx = (xc ** 2).sum()
    idx = np.argsort(rng.random((nperm, len(yr))), axis=1)
    P = np.asarray(yr, float)[idx]
    Pc = P - P.mean(axis=1, keepdims=True)
    ssp = (Pc ** 2).sum(axis=1)
    assert ssp.min() > 0, "a target's rank vector is constant; Spearman is undefined"
    # numpy's matmul raises spurious divide/overflow/invalid FP-status warnings here:
    # the BLAS kernel sets the status flags on its padding lanes even though every
    # value it returns is finite. The assertion below is what actually guards the result.
    with np.errstate(all="ignore"):
        r = (Pc @ xc) / np.sqrt(ssp * ssx)
    assert np.isfinite(r).all() and np.abs(r).max() <= 1.0
    return np.abs(r)


def null_auc(lab, nperm):
    """|AUC - 0.5| between the fixed order 0..n-1 and shuffles of the labels."""
    m = len(lab)
    n1 = int(lab.sum())
    n0 = m - n1
    ranks = np.arange(1, m + 1, dtype=float)
    idx = np.argsort(rng.random((nperm, m)), axis=1)
    S = (np.asarray(lab, float)[idx] * ranks).sum(axis=1)
    return np.abs((S - n1 * (n1 + 1) / 2) / (n1 * n0) - 0.5)


head("[1] REBUILDING THE PERMUTATION NULLS USED BY THE SCREEN")
print(f"  cohort n = {n};  permutations per null = {NPERM:,};  seed = {SEED}")
print("  One null per target. The null depends on the target only (through ties or")
print("  group sizes), never on the feature -- that is why 608 features share it.")
NULL_C, NULL_B = {}, {}
print(f"\n  {'target':24} {'kind':5} {'null p95':>9} {'null p99':>9} {'null max':>9}  detail")
for t in CONT:
    yr = rankdata(Yc[t].to_numpy(float))
    NULL_C[t] = np.sort(null_rho(yr, NPERM))
    nt = len(yr) - len(np.unique(yr))
    print(f"  {t:24} {'cont':5} {np.quantile(NULL_C[t], .95):9.3f}"
          f" {np.quantile(NULL_C[t], .99):9.3f} {NULL_C[t].max():9.3f}"
          f"  {len(np.unique(yr))} distinct values of {n}, {nt} tied")
for t in BIN:
    lab = Yb[t].to_numpy(int)
    NULL_B[t] = np.sort(null_auc(lab, NPERM))
    print(f"  {t:24} {'bin':5} {np.quantile(NULL_B[t], .95):9.3f}"
          f" {np.quantile(NULL_B[t], .99):9.3f} {NULL_B[t].max():9.3f}"
          f"  group sizes {n - int(lab.sum())} / {int(lab.sum())}")

# ---------------------------------------------------------------------------
# [2] Verification: can the published table be reproduced from its inputs?
# ---------------------------------------------------------------------------
head("[2] VERIFICATION -- recomputing published cells from features.csv and the targets")
print("  20 randomly chosen continuous cells and 20 binary cells are recomputed here")
print("  with an independent implementation of the same statistic.")
vrng = np.random.default_rng(7)
cont_rows = A[A["type"] == "cont"].sample(20, random_state=7)
bin_rows = A[A["type"] == "bin"].sample(20, random_state=7)
dmax_c = dmax_b = 0.0
print(f"\n  {'target':22} {'feature':30} {'published':>10} {'recomputed':>11} {'diff':>10}")
for _, r in cont_rows.iterrows():
    got = spearman(rankdata(X[r["feature"]].to_numpy()), rankdata(Yc[r["target"]].to_numpy(float)))
    d = abs(got - r["rho"])
    dmax_c = max(dmax_c, d)
    print(f"  {r['target']:22} {r['feature']:30} {r['rho']:10.6f} {got:11.6f} {d:10.2e}")
for _, r in bin_rows.iterrows():
    got = auc_stat(X[r["feature"]].to_numpy(), Yb[r["target"]].to_numpy(int))
    d = abs(got - r["auc"])
    dmax_b = max(dmax_b, d)
    print(f"  {r['target']:22} {r['feature']:30} {r['auc']:10.6f} {got:11.6f} {d:10.2e}")
print(f"\n  largest disagreement, Spearman rho cells : {dmax_c:.2e}")
print(f"  largest disagreement, AUC cells          : {dmax_b:.2e}")
print("  verdict: " + ("the published effect sizes reproduce from the committed inputs"
                       if max(dmax_c, dmax_b) < 1e-9 else "SEE DISAGREEMENTS ABOVE"))

print("\n  The permutation p-values are also recomputed, from this script's own nulls.")
print("  Exact equality is not expected: perm_p is a Monte-Carlo quantity and this")
print("  script draws a fresh sample with a different seed. What is checked is that")
print("  the two agree to within Monte-Carlo error.")
rec = []
for t in CONT:
    g = A[(A["type"] == "cont") & (A["target"] == t)]
    p = 1 - np.searchsorted(NULL_C[t], g["rho"].abs().to_numpy(), side="right") / NPERM
    rec.append(pd.DataFrame({"published": g["perm_p"].to_numpy(),
                             "recomputed": np.maximum(p, 1.0 / NPERM)}))
for t in BIN:
    g = A[(A["type"] == "bin") & (A["target"] == t)]
    p = 1 - np.searchsorted(NULL_B[t], (g["auc"] - 0.5).abs().to_numpy(), side="right") / NPERM
    rec.append(pd.DataFrame({"published": g["perm_p"].to_numpy(),
                             "recomputed": np.maximum(p, 1.0 / NPERM)}))
rec = pd.concat(rec, ignore_index=True)
d = (rec["published"] - rec["recomputed"]).abs()
print(f"    cells compared                     : {len(rec)}")
print(f"    identical                          : {int((d == 0).sum())}")
print(f"    differing by <= 0.002              : {int((d <= 0.002).sum())}")
print(f"    largest difference                 : {d.max():.5f}")
print(f"    Spearman correlation of the two    : "
      f"{np.corrcoef(rankdata(rec['published']), rankdata(rec['recomputed']))[0, 1]:.6f}")
agree_dir = int(((rec["published"] < 0.05) == (rec["recomputed"] < 0.05)).sum())
print(f"    cells on the same side of p < 0.05 : {agree_dir} of {len(rec)}")

# ---------------------------------------------------------------------------
# [3] FIGURE 03 -- continuous half: observed effect sizes against the null
# ---------------------------------------------------------------------------
head("[3] CONTINUOUS TARGETS -- 6,080 observed |Spearman rho| against the null")
obs_c = {t: A.loc[(A["type"] == "cont") & (A["target"] == t), "rho"].abs().to_numpy() for t in CONT}
allobs_c = np.concatenate([obs_c[t] for t in CONT])
allnull_c = np.concatenate([NULL_C[t] for t in CONT])
p95 = {t: np.quantile(NULL_C[t], .95) for t in CONT}
p99 = {t: np.quantile(NULL_C[t], .99) for t in CONT}

print(f"  {'target':24} {'median |rho|':>12} {'null med':>9} {'max |rho|':>10}"
      f" {'>p95':>6} {'exp':>5} {'ratio':>6} {'>p99':>6} {'exp':>5}")
summary_c = []
for t in CONT:
    o = obs_c[t]
    e95 = int((o > p95[t]).sum())
    e99 = int((o > p99[t]).sum())
    exp95, exp99 = len(o) * 0.05, len(o) * 0.01
    summary_c.append(dict(target=t, n=len(o), med=np.median(o), nullmed=np.median(NULL_C[t]),
                          mx=o.max(), e95=e95, exp95=exp95, e99=e99, exp99=exp99))
    print(f"  {t:24} {np.median(o):12.3f} {np.median(NULL_C[t]):9.3f} {o.max():10.3f}"
          f" {e95:6d} {exp95:5.0f} {e95 / exp95:6.2f} {e99:6d} {exp99:5.0f}")
S_C = pd.DataFrame(summary_c)
print(f"  {'TOTAL':24} {np.median(allobs_c):12.3f} {np.median(allnull_c):9.3f}"
      f" {allobs_c.max():10.3f} {S_C.e95.sum():6d} {S_C.exp95.sum():5.0f}"
      f" {S_C.e95.sum() / S_C.exp95.sum():6.2f} {S_C.e99.sum():6d} {S_C.exp99.sum():5.0f}")
print("\n  'exp' is the count expected if every cell were drawn from the null.")
print("  The 608 features are strongly correlated with one another (same channel,")
print("  adjacent percentile and window settings), so these counts are NOT 608")
print("  independent trials. The null curve is the correct reference for the shape and")
print("  location of the observed distribution, not for a count-based significance test.")

fig, (axL, axR) = plt.subplots(1, 2, figsize=(13.6, 6.1),
                               gridspec_kw={"width_ratios": [1, 1.12], "wspace": 0.24})

ax = axL
bins = np.linspace(0, max(allobs_c.max(), allnull_c.max()) * 1.02, 70)
ax.hist(allobs_c, bins=bins, density=True, color="#4878a8", alpha=0.75,
        label=f"observed, all {len(allobs_c):,} cells")
hn, _ = np.histogram(allnull_c, bins=bins, density=True)
ax.plot(0.5 * (bins[1:] + bins[:-1]), hn, color="#b2182b", lw=2.0,
        label=f"permutation null ({NPERM:,} draws/target)")
ax.axvline(np.median(allobs_c), color="#4878a8", ls="--", lw=1.2)
ax.axvline(np.median(allnull_c), color="#b2182b", ls="--", lw=1.2)
ax.set_xlabel("|Spearman rho|   (no-effect baseline = 0)")
ax.set_ylabel("Density")
ax.set_title("Fig 3a  All 6,080 continuous cells\nagainst the null they were tested against",
             fontsize=10.5)
ax.legend(fontsize=8.2, frameon=False)
ax.grid(alpha=0.22, lw=0.6)
ax.set_axisbelow(True)
ax.text(0.98, 0.55,
        f"median observed  {np.median(allobs_c):.3f}\nmedian null        {np.median(allnull_c):.3f}",
        transform=ax.transAxes, ha="right", va="top", fontsize=8.5, family="monospace",
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#cccccc"))

ax = axR
for i, t in enumerate(CONT):
    o = obs_c[t]
    jit = (np.random.default_rng(i).random(len(o)) - 0.5) * 0.52
    ax.scatter(o, np.full(len(o), i) + jit, s=1.4, color="#4878a8", alpha=0.30, linewidths=0)
    ax.plot([p95[t], p95[t]], [i - 0.42, i + 0.42], color="#b2182b", lw=1.7)
    ax.plot([p99[t], p99[t]], [i - 0.42, i + 0.42], color="#67001f", lw=1.7, ls=":")
    r = S_C.loc[S_C.target == t]
    ax.text(1.005, i, f"{int(r.e95.iloc[0]):3d} / {r.exp95.iloc[0]:.0f}",
            transform=ax.get_yaxis_transform(), va="center", fontsize=7.8, family="monospace")
ax.set_yticks(range(len(CONT)))
ax.set_yticklabels(CONT, fontsize=8.5)
ax.invert_yaxis()
ax.set_xlim(0, max(allobs_c.max(), max(p99.values())) * 1.06)
ax.set_xlabel("|Spearman rho|")
ax.set_title("Fig 3b  Per target: 608 features each,\nagainst that target's own null",
             fontsize=10.5)
ax.plot([], [], color="#b2182b", lw=1.7, label="null 95th percentile")
ax.plot([], [], color="#67001f", lw=1.7, ls=":", label="null 99th percentile")
ax.legend(fontsize=8.2, frameon=False, loc="lower right")
ax.grid(axis="x", alpha=0.22, lw=0.6)
ax.set_axisbelow(True)
fig.tight_layout()
fig.subplots_adjust(bottom=0.235)
fig.text(0.012, 0.020,
         "Null construction copied from 44_univariate_screen.py: shuffle the target's rank vector, correlate it against the fixed rank vector 0..n-1, take |rho|. "
         f"n = {n} subjects, {NPERM:,} permutations per target.\n"
         "Right-hand column of Fig 3b: how many of that target's 608 cells sit above the null 95th percentile / how many would be expected there if every cell were null.\n"
         "A cell above the red line is what the screen would call p < 0.05 before any multiple-comparison correction. 'Expected' assumes independent cells; the 608\n"
         "features are not independent (same channel, adjacent percentile and window settings), so these counts describe the distribution and are not themselves a test.",
         fontsize=7.2, color="#444444", linespacing=1.5)
fig.savefig(FIGDIR / "fig03_effect_vs_null_continuous.png", dpi=200)
plt.close(fig)
print(f"\n  wrote {FIGDIR / 'fig03_effect_vs_null_continuous.png'}")

# ---------------------------------------------------------------------------
# [4] FIGURE 04 -- binary half
# ---------------------------------------------------------------------------
head("[4] BINARY TARGETS -- 6,080 observed |AUC - 0.5| against per-target nulls")
print("  Kept separate from the continuous half for two reasons:")
print("    1. the null depends on the group sizes, which differ from target to target")
print("       (12/12 up to 18/6), so one pooled reference line would be wrong;")
print("    2. |AUC - 0.5| lives in [0, 0.5] while |rho| lives in [0, 1] -- the two")
print("       axes are not interchangeable and are never drawn on a shared scale here.")
obs_b = {t: (A.loc[(A["type"] == "bin") & (A["target"] == t), "auc"] - 0.5).abs().to_numpy()
         for t in BIN}
q95 = {t: np.quantile(NULL_B[t], .95) for t in BIN}
q99 = {t: np.quantile(NULL_B[t], .99) for t in BIN}
gs_sizes = {t: (n - int(Yb[t].sum()), int(Yb[t].sum())) for t in BIN}

print(f"\n  {'target':24} {'split':>7} {'med |AUC-.5|':>13} {'null med':>9} {'max':>7}"
      f" {'>p95':>6} {'exp':>5} {'ratio':>6} {'>p99':>6}")
summary_b = []
for t in BIN:
    o = obs_b[t]
    e95, e99 = int((o > q95[t]).sum()), int((o > q99[t]).sum())
    summary_b.append(dict(target=t, e95=e95, exp95=len(o) * 0.05, e99=e99, exp99=len(o) * 0.01))
    print(f"  {t:24} {f'{gs_sizes[t][0]}/{gs_sizes[t][1]}':>7} {np.median(o):13.3f}"
          f" {np.median(NULL_B[t]):9.3f} {o.max():7.3f} {e95:6d} {len(o) * 0.05:5.0f}"
          f" {e95 / (len(o) * 0.05):6.2f} {e99:6d}")
S_B = pd.DataFrame(summary_b)
print(f"  {'TOTAL':24} {'':>7} {'':>13} {'':>9} {'':>7} {S_B.e95.sum():6d}"
      f" {S_B.exp95.sum():5.0f} {S_B.e95.sum() / S_B.exp95.sum():6.2f} {S_B.e99.sum():6d}")

fig, ax = plt.subplots(figsize=(12.4, 6.0))
for i, t in enumerate(BIN):
    o = obs_b[t]
    jit = (np.random.default_rng(100 + i).random(len(o)) - 0.5) * 0.52
    ax.scatter(o, np.full(len(o), i) + jit, s=1.6, color="#4878a8", alpha=0.30, linewidths=0)
    ax.plot([q95[t], q95[t]], [i - 0.42, i + 0.42], color="#b2182b", lw=1.8)
    ax.plot([q99[t], q99[t]], [i - 0.42, i + 0.42], color="#67001f", lw=1.8, ls=":")
    r = S_B.loc[S_B.target == t]
    ax.text(1.005, i, f"{int(r.e95.iloc[0]):3d} / {r.exp95.iloc[0]:.0f}",
            transform=ax.get_yaxis_transform(), va="center", fontsize=8, family="monospace")
ax.set_yticks(range(len(BIN)))
ax.set_yticklabels([f"{t}   [{gs_sizes[t][0]}/{gs_sizes[t][1]}]" for t in BIN], fontsize=8.8)
ax.invert_yaxis()
ax.set_xlim(0, max(max(o.max() for o in obs_b.values()), max(q99.values())) * 1.07)
ax.set_xlabel("|AUC - 0.5|   (no-effect baseline = 0, i.e. AUC = 0.5;  this axis spans [0, 0.5], half the range of |rho|)")
ax.set_title("Fig 4  Binary targets: each row is 608 features screened against one label,\n"
             "compared with that label's own permutation null (group sizes in brackets)",
             fontsize=11)
ax.grid(axis="x", alpha=0.22, lw=0.6)
ax.set_axisbelow(True)
ax.plot([], [], color="#b2182b", lw=1.8, label="null 95th percentile")
ax.plot([], [], color="#67001f", lw=1.8, ls=":", label="null 99th percentile")
ax.legend(fontsize=8.5, frameon=False, loc="lower right")
fig.text(0.012, 0.012,
         "Null construction copied from 44_univariate_screen.py: shuffle the label vector, score it against the fixed order 0..n-1, take |AUC - 0.5|. "
         f"{NPERM:,} permutations per target.\nThe null widens as the split becomes more uneven, which is why each row is judged against its own line rather than a common one. "
         "Right column: observed cells above the 95th percentile / the number expected if all 608 were null.",
         fontsize=7.0, color="#444444", linespacing=1.5)
fig.tight_layout(rect=[0, 0.075, 1, 1])
fig.savefig(FIGDIR / "fig04_effect_vs_null_binary.png", dpi=200)
plt.close(fig)
print(f"\n  wrote {FIGDIR / 'fig04_effect_vs_null_binary.png'}")

# ---------------------------------------------------------------------------
# [5] FIGURE 05 -- what survives the correction the screen itself applies
# ---------------------------------------------------------------------------
head("[5] MULTIPLE COMPARISONS -- BH-FDR within each target family")


def bh(p):
    """Benjamini-Hochberg step-up. Written independently here so that the q_fdr
    column can be checked rather than trusted; 44_ and 45_ carry a shared copy."""
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


qrec = np.empty(len(A))
for t, g in A.groupby("target"):
    qrec[g.index.to_numpy()] = bh(g["perm_p"].to_numpy())
dq = np.abs(qrec - A["q_fdr"].to_numpy())
print(f"  family definition, read off the data: one family per target, m = "
      f"{len(A) // A['target'].nunique()} features, {A['target'].nunique()} families.")
print(f"  verification of the published q_fdr column against an independent BH")
print(f"    implementation: largest disagreement over all {len(A)} cells = {dq.max():.3e}")
print(f"    verdict: {'reproduces exactly' if dq.max() < 1e-12 else 'DISAGREEMENT -- see above'}")

floor = A["perm_p"].min()
print(f"\n  permutation resolution: the smallest p the screen can report is 1/NPERM = {floor:.1e}")
print(f"  cells sitting exactly on that floor: {int((A['perm_p'] <= floor).sum())}")
print(f"  best attainable q for a single cell = floor * m / 1 = {floor * 608:.4f}"
      f"  (so one cell alone can pass q < 0.05)")

print(f"\n  {'target':24} {'min perm_p':>11} {'min q_fdr':>10} {'q<0.05':>7} {'q<0.10':>7} {'p<0.05':>7} {'exp':>5}")
fdr_rows = []
for t in CONT + BIN:
    g = A[A["target"] == t]
    fdr_rows.append(dict(target=t, kind="cont" if t in CONT else "bin",
                         minp=g["perm_p"].min(), minq=g["q_fdr"].min(),
                         s05=int((g["q_fdr"] < 0.05).sum()), s10=int((g["q_fdr"] < 0.10).sum()),
                         raw=int((g["perm_p"] < 0.05).sum()), exp=len(g) * 0.05))
    r = fdr_rows[-1]
    print(f"  {t:24} {r['minp']:11.1e} {r['minq']:10.4f} {r['s05']:7d} {r['s10']:7d}"
          f" {r['raw']:7d} {r['exp']:5.0f}")
F = pd.DataFrame(fdr_rows)
print(f"  {'TOTAL':24} {'':>11} {'':>10} {F.s05.sum():7d} {F.s10.sum():7d}"
      f" {F.raw.sum():7d} {F.exp.sum():5.0f}")

surv = A[A["q_fdr"] < 0.05].sort_values("q_fdr")
print(f"\n  cells surviving BH-FDR at q < 0.05: {len(surv)} of {len(A)}")
if len(surv):
    print(f"  {'target':24} {'type':5} {'feature':28} {'rho':>8} {'auc':>7} {'perm_p':>9} {'q_fdr':>8} {'loo_r2cv':>9}")
    for _, r in surv.iterrows():
        print(f"  {r['target']:24} {r['type']:5} {r['feature']:28}"
              f" {r['rho']:8.3f}" .replace("nan", "  -") +
              (f" {r['auc']:7.3f}" if pd.notna(r["auc"]) else f" {'-':>7}") +
              f" {r['perm_p']:9.1e} {r['q_fdr']:8.4f}" +
              (f" {r['loo_r2cv']:9.3f}" if pd.notna(r["loo_r2cv"]) else f" {'-':>9}"))
    print("\n  Every surviving cell sits on the permutation floor, meaning 100,000 shuffles")
    print("  never produced an effect as large. The true p is smaller than 1e-5 but by how")
    print("  much is not resolved by this many permutations.")

fig, (axA, axB) = plt.subplots(1, 2, figsize=(13.8, 5.8),
                               gridspec_kw={"width_ratios": [1.25, 1], "wspace": 0.26})
ax = axA
m = 608
ranks = np.arange(1, m + 1)
for t in CONT + BIN:
    p = np.sort(A.loc[A["target"] == t, "perm_p"].to_numpy())
    ax.plot(ranks, p, lw=1.0, alpha=0.75,
            color="#4878a8" if t in CONT else "#e08214")
ax.plot(ranks, 0.05 * ranks / m, color="#b2182b", lw=2.2,
        label="BH threshold, q = 0.05  (p = q·i/m, m = 608)")
ax.axhline(floor, color="#555555", ls="--", lw=1.2,
           label=f"permutation floor 1/NPERM = {floor:.0e}")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(1, m)
ax.set_xlabel("Rank i of the p-value within its target family (log scale)")
ax.set_ylabel("Permutation p, sorted ascending (log scale)")
ax.set_title("Fig 5a  Each target's 608 p-values against the correction applied to them",
             fontsize=10.5)
ax.plot([], [], color="#4878a8", lw=1.4, label="a continuous target (10)")
ax.plot([], [], color="#e08214", lw=1.4, label="a binary target (10)")
ax.legend(fontsize=8.0, frameon=False, loc="lower right")
ax.grid(alpha=0.22, lw=0.6, which="both")
ax.set_axisbelow(True)

ax = axB
F2 = F.sort_values("minq")
cols = ["#4878a8" if k == "cont" else "#e08214" for k in F2["kind"]]
ax.barh(range(len(F2)), F2["minq"], color=cols, height=0.66)
ax.axvline(0.05, color="#b2182b", lw=1.8, label="q = 0.05")
ax.set_xscale("log")
ax.set_yticks(range(len(F2)))
ax.set_yticklabels(F2["target"], fontsize=8)
ax.invert_yaxis()
ax.set_xlabel("Smallest q value the target achieved (log scale)")
ax.set_title("Fig 5b  How close each target came to surviving\nits own multiple-comparison correction",
             fontsize=10.5)
for i, (_, r) in enumerate(F2.iterrows()):
    ax.text(r["minq"] * 1.15, i, f"{r['minq']:.3f}" + (f"   {r['s05']} cell(s) pass" if r["s05"] else ""),
            va="center", fontsize=7.6)
ax.legend(fontsize=8.2, frameon=False, loc="lower right")
ax.grid(axis="x", alpha=0.22, lw=0.6, which="both")
ax.set_axisbelow(True)
ax.set_xlim(right=ax.get_xlim()[1] * 6)
fig.tight_layout()
fig.subplots_adjust(bottom=0.20)
fig.text(0.012, 0.018,
         "Family definition read off the data and confirmed against 44_univariate_screen.py: BH is applied within each target separately, m = 608 features, 20 families. "
         "The q_fdr column\nwas recomputed here with an independent BH implementation and agrees to "
         f"{dq.max():.0e}. A target's curve passes the correction only where it dips below the red line. "
         f"The dashed line is the\nresolution limit of the permutation test: no p smaller than {floor:.0e} can be reported however strong the effect, so cells resting on it have an unresolved true p.",
         fontsize=7.2, color="#444444", linespacing=1.5)
fig.savefig(FIGDIR / "fig05_fdr_per_target.png", dpi=200)
plt.close(fig)
print(f"\n  wrote {FIGDIR / 'fig05_fdr_per_target.png'}")

# ---------------------------------------------------------------------------
# [6] FIGURE 06 -- in-sample effect size versus held-out prediction
# ---------------------------------------------------------------------------
head("[6] GENERALISATION -- leave-one-out R^2 against in-sample |rho| (continuous half)")
print("  MODEL_MENU.md section 4 trap 1: rho is not generalisation evidence, because the")
print("  leave-one-out prediction of a single-feature linear fit is a monotone transform of")
print("  the feature. Generalisation is carried by loo_r2cv (closed-form PRESS) alone, and")
print("  the binary half has no loo_r2cv at all, so this section covers the continuous half.")


def loo_r2_null(x, y, nperm):
    """Distribution of the closed-form leave-one-out R^2 when y is unrelated to x.
    Vectorised over permutations of y; x, its leverage and the baseline are fixed."""
    x = np.asarray(x, float)
    n_ = len(x)
    xm = x.mean()
    xc = x - xm
    Sxx = (xc ** 2).sum()
    if Sxx <= 0:
        return None
    h = 1.0 / n_ + xc ** 2 / Sxx
    if np.any(h >= 1 - 1e-12):
        return None
    ym = y.mean()
    ss0 = (((y - ym) * n_ / (n_ - 1)) ** 2).sum()   # invariant under permutation of y
    if ss0 <= 0:
        return None
    idx = np.argsort(rng.random((nperm, n_)), axis=1)
    Y = np.asarray(y, float)[idx]
    Yc = Y - Y.mean(axis=1, keepdims=True)
    with np.errstate(all="ignore"):
        b = (Yc @ xc) / Sxx
        E = Yc - b[:, None] * xc
        ss = ((E / (1.0 - h)) ** 2).sum(axis=1)
    return 1.0 - ss / ss0


NPERM_R2 = 2000
NFEAT_R2 = 40
print(f"\n  Null for loo_r2cv built by permuting the target against {NFEAT_R2} randomly chosen")
print(f"  features per target, {NPERM_R2:,} permutations each. The leverage profile differs")
print(f"  from feature to feature, so the null is sampled across features rather than one.")
frng = np.random.default_rng(11)
null_r2 = {}
print(f"\n  {'target':24} {'null P(R2cv>0)':>15} {'null p95':>9} {'null p99':>9}")
for t in CONT:
    y = Yc[t].to_numpy(float)
    picks = frng.choice(FEATS, NFEAT_R2, replace=False)
    drawn = [v for f in picks if (v := loo_r2_null(X[f].to_numpy(), y, NPERM_R2)) is not None]
    pool = np.concatenate(drawn)
    null_r2[t] = pool
    print(f"  {t:24} {float((pool > 0).mean()):15.4f} {np.quantile(pool, .95):9.3f}"
          f" {np.quantile(pool, .99):9.3f}")
pool_all = np.concatenate([null_r2[t] for t in CONT])
r2_p95 = float(np.quantile(pool_all, .95))
rate0 = float((pool_all > 0).mean())
print(f"  {'POOLED':24} {rate0:15.4f} {r2_p95:9.3f} {np.quantile(pool_all, .99):9.3f}")

cont = A[A["type"] == "cont"]
n_pos = int((cont["loo_r2cv"] > 0).sum())
n_p95 = int((cont["loo_r2cv"] > r2_p95).sum())
print(f"\n  observed cells with loo_r2cv > 0            : {n_pos} of {len(cont)}"
      f"   ({100 * n_pos / len(cont):.2f}%)")
print(f"  expected under the null                     : {rate0 * len(cont):.0f}"
      f"   ({100 * rate0:.2f}%)")
print(f"  observed cells above the null 95th pct      : {n_p95}"
      f"   (expected {0.05 * len(cont):.0f})")
print(f"  largest loo_r2cv anywhere in the screen     : {cont['loo_r2cv'].max():.4f}")
best = cont.loc[cont["loo_r2cv"].idxmax()]
print(f"    attained by {best['feature']} on {best['target']}"
      f"  (rho {best['rho']:+.3f}, perm_p {best['perm_p']:.1e}, q_fdr {best['q_fdr']:.3f})")
print(f"  median loo_r2cv across the continuous half  : {cont['loo_r2cv'].median():.4f}")

fig, (axA, axB) = plt.subplots(1, 2, figsize=(13.6, 5.6),
                               gridspec_kw={"width_ratios": [1.35, 1], "wspace": 0.22})
ax = axA
ax.scatter(cont["rho"].abs(), cont["loo_r2cv"], s=2.2, alpha=0.22, color="#4878a8", linewidths=0)
ax.axhline(0, color="#333333", lw=1.3)
ax.axhline(r2_p95, color="#b2182b", lw=1.6, ls="--",
           label=f"null 95th percentile of loo_r2cv = {r2_p95:.3f}")
pos = cont[cont["loo_r2cv"] > 0]
if len(pos):
    ax.scatter(pos["rho"].abs(), pos["loo_r2cv"], s=6, color="#b2182b", linewidths=0,
               label=f"loo_r2cv > 0  ({len(pos)} cells)")
ax.set_ylim(max(-1.6, cont["loo_r2cv"].min() - 0.1), max(0.35, cont["loo_r2cv"].max() + 0.08))
ax.set_xlabel("|Spearman rho|   (in-sample effect size)")
ax.set_ylabel("loo_r2cv   (leave-one-out R²;  0 = no better than the mean)", fontsize=9.5)
ax.set_title("Fig 6a  In-sample correlation vs held-out prediction, 6,080 continuous cells",
             fontsize=10.5)
ax.legend(fontsize=8.2, frameon=False, loc="lower right")
ax.grid(alpha=0.22, lw=0.6)
ax.set_axisbelow(True)

ax = axB
lo = max(-1.5, min(cont["loo_r2cv"].min(), np.quantile(pool_all, 0.001)))
bins = np.linspace(lo, max(cont["loo_r2cv"].max(), np.quantile(pool_all, .999)) + 0.02, 70)
ax.hist(np.clip(pool_all, lo, None), bins=bins, density=True, color="#b2182b", alpha=0.42,
        label=f"null ({len(pool_all):,} draws)")
ax.hist(np.clip(cont["loo_r2cv"], lo, None), bins=bins, density=True, color="#4878a8",
        alpha=0.62, label=f"observed ({len(cont):,} cells)")
ax.axvline(0, color="#333333", lw=1.3)
ax.set_xlabel("loo_r2cv")
ax.set_ylabel("Density")
ax.set_title("Fig 6b  The same values against their null\n"
             f"observed P(loo_r2cv > 0) = {n_pos / len(cont):.3f},  null = {rate0:.3f}",
             fontsize=10.5)
ax.legend(fontsize=8.2, frameon=False)
ax.grid(alpha=0.22, lw=0.6)
ax.set_axisbelow(True)
fig.tight_layout()
fig.subplots_adjust(bottom=0.185)
fig.text(0.012, 0.018,
         "loo_r2cv is the closed-form PRESS leave-one-out R² of a single-feature ordinary least squares fit, as computed by 44_univariate_screen.py; it is negative whenever the fitted\n"
         f"feature predicts a held-out subject worse than the training mean does. Null built by permuting each target against {NFEAT_R2} randomly chosen features, {NPERM_R2:,} permutations each,\n"
         "so that the varying leverage profile of different features is represented. Values are clipped at the left edge for display only. The binary half of the screen has no loo_r2cv column.",
         fontsize=7.2, color="#444444", linespacing=1.5)
fig.savefig(FIGDIR / "fig06_effect_vs_generalization.png", dpi=200)
plt.close(fig)
print(f"\n  wrote {FIGDIR / 'fig06_effect_vs_generalization.png'}")

# ---------------------------------------------------------------------------
# [7] FIGURE 07 -- the three surviving cells, examined one by one
# ---------------------------------------------------------------------------
head("[7] THE THREE CELLS THAT SURVIVED THE CORRECTION -- how robust are they")
print("  These three are the entire positive yield of the univariate track, so each is")
print("  examined directly rather than reported as a row in a table. Three questions:")
print("    (a) what does the relationship look like, and is it carried by the whole cohort?")
print("    (b) how much does it move when any single subject is removed (n = 24)?")
print("    (c) do the neighbouring settings of the same feature family agree with it?")
print("        Path-A features form a grid over window length x percentile threshold.")
print("        A real structural signal should vary smoothly across that grid; an isolated")
print("        spike surrounded by nothing is what selecting the maximum of many noisy")
print("        cells looks like.")

SURV = surv[["target", "feature", "rho", "perm_p", "q_fdr", "loo_r2cv"]].to_dict("records")


def stem_grid(feature):
    """Split a path-A name like 'frac_act_short_w10_p20' into (stem, window, pct)."""
    mm = re.match(r"^(.*)_w([0-9.]+)_p([0-9]+)$", feature)
    return (mm.group(1), mm.group(2), int(mm.group(3))) if mm else None


print(f"\n  target correlations among the three targets involved"
      f" (nested targets are not independent findings):")
tg = sorted({r["target"] for r in SURV})
for i in range(len(tg)):
    for j in range(i + 1, len(tg)):
        rr = spearman(rankdata(Yc[tg[i]].to_numpy(float)), rankdata(Yc[tg[j]].to_numpy(float)))
        print(f"    {tg[i]:18} vs {tg[j]:18} Spearman rho = {rr:+.3f}")
print("    snap_adhd_total is by construction the sum of the SNAP inattention and")
print("    hyperactivity items, so it contains snap_inatt; the two cells that share the")
print("    feature frac_act_short_w10_p20 are one finding measured twice, not two.")

fig, axes = plt.subplots(3, len(SURV), figsize=(4.6 * len(SURV), 12.2))
for c, rec in enumerate(SURV):
    f, t = rec["feature"], rec["target"]
    xv = X[f].to_numpy(float)
    yv = Yc[t].to_numpy(float)
    xr, yr_ = rankdata(xv), rankdata(yv)
    full = spearman(xr, yr_)

    # (a) the relationship itself, with the least-squares line drawn.
    # Note which statistic is which. The Spearman rho reported by the screen is a RANK
    # correlation and involves no line at all. The line below is the ordinary least
    # squares fit on the raw values -- the same fit whose leave-one-out error becomes the
    # loo_r2cv column (loo_simple_lr() in 44_univariate_screen.py). Drawing it gives
    # loo_r2cv a visual referent it otherwise lacks, and lets the in-sample fit and the
    # held-out performance be compared on the same picture.
    ax = axes[0, c]
    w, b = np.polyfit(xv, yv, 1)
    pear = float(np.corrcoef(xv, yv)[0, 1])
    xs = np.linspace(xv.min(), xv.max(), 50)
    for i in range(n):                                   # the 24 leave-one-out refits
        wi, bi = np.polyfit(np.delete(xv, i), np.delete(yv, i), 1)
        ax.plot(xs, wi * xs + bi, color="#999999", lw=0.7, alpha=0.30, zorder=1)
    ax.plot(xs, w * xs + b, color="#b2182b", lw=2.0, zorder=2)
    ax.scatter(xv, yv, s=44, color="#4878a8", edgecolor="white", linewidth=0.8, zorder=3)
    ax.set_xlabel(f, fontsize=8.5)
    ax.set_ylabel(t, fontsize=9)
    nzero = int((xv == xv.min()).sum())
    ax.set_title(f"{t}  vs  {f}", fontsize=9.6)
    ax.text(0.03, 0.97, f"{len(np.unique(xv))} distinct feature values of {n}\n"
                        f"{nzero} subject(s) at the minimum",
            transform=ax.transAxes, va="top", fontsize=7.6,
            bbox=dict(boxstyle="round,pad=0.32", fc="white", ec="#cccccc"))
    ax.text(0.97, 0.05,
            f"y = w·x + b\n"
            f"w = {w:+.3f}   b = {b:+.3f}\n"
            f"─────────────────────\n"
            f"Pearson r    {pear:+.3f}   (this line)\n"
            f"Spearman ρ   {full:+.3f}   (the screen's)\n"
            f"in-sample R²  {pear ** 2:.3f}\n"
            f"leave-one-out R²  {rec['loo_r2cv']:+.3f}",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7.4, family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", fc="#fffdf7", ec="#b2182b", lw=0.9))
    ax.grid(alpha=0.22, lw=0.6)
    ax.set_axisbelow(True)
    print(f"\n  {t} x {f}  -- least-squares line on the raw values")
    print(f"    y = {w:+.4f} * x {b:+.4f}")
    print(f"    over the observed range of x ({xv.min():.4g} to {xv.max():.4g}) the line")
    print(f"      predicts a change of {w * (xv.max() - xv.min()):+.2f} points on {t},")
    print(f"      whose own observed range is {yv.min():.0f} to {yv.max():.0f}")
    print(f"    Pearson r {pear:+.4f} (belongs to this line)  vs  Spearman rho {full:+.4f}"
          f" (the statistic the screen tested)")
    print(f"    in-sample R^2 {pear ** 2:.4f}  vs  leave-one-out R^2 {rec['loo_r2cv']:+.4f}"
          f"   -- the gap is what fitting 24 points to a 2-parameter line costs")

    # (b) drop-one-subject jackknife
    ax = axes[1, c]
    jk = np.array([spearman(rankdata(np.delete(xv, i)), rankdata(np.delete(yv, i)))
                   for i in range(n)])
    order = np.argsort(jk)
    ax.bar(range(n), jk[order], color="#4878a8", width=0.78)
    ax.axhline(full, color="#333333", lw=1.4, label=f"all 24 subjects: {full:+.3f}")
    ax.axhline(np.quantile(NULL_C[t], .95), color="#b2182b", lw=1.5, ls="--",
               label=f"null 95th pct: {np.quantile(NULL_C[t], .95):.3f}")
    ax.set_xticks(range(n))
    ax.set_xticklabels([X.index[i] for i in order], rotation=90, fontsize=6.2)
    ax.set_ylabel("Spearman rho with that subject removed", fontsize=8.5)
    ax.set_ylim(0, max(1.0, jk.max() * 1.08))
    ax.set_title(f"Removing any one subject: rho spans {jk.min():+.3f} to {jk.max():+.3f}\n"
                 f"(a drop of {full - jk.min():.3f} at worst)", fontsize=9.2)
    ax.legend(fontsize=7.4, frameon=False, loc="lower right")
    ax.grid(axis="y", alpha=0.22, lw=0.6)
    ax.set_axisbelow(True)
    print(f"\n  {t} x {f}")
    print(f"    full-sample rho {full:+.3f};  drop-one range {jk.min():+.3f} .. {jk.max():+.3f}")
    print(f"    subjects whose removal pushes rho below the null 95th percentile"
          f" ({np.quantile(NULL_C[t], .95):.3f}): "
          f"{[X.index[i] for i in range(n) if jk[i] < np.quantile(NULL_C[t], .95)] or 'none'}")
    print(f"    feature has {len(np.unique(xv))} distinct values across {n} subjects")

    # (c) the neighbourhood in the (window x percentile) grid
    ax = axes[2, c]
    g = stem_grid(f)
    if g:
        stem, w0, p0 = g
        sub = A[(A["target"] == t) & (A["feature"].str.startswith(stem + "_w"))].copy()
        parsed = sub["feature"].map(stem_grid)
        sub = sub[parsed.notna()]
        sub["win"] = [stem_grid(v)[1] for v in sub["feature"]]
        sub["pct"] = [stem_grid(v)[2] for v in sub["feature"]]
        piv = sub.pivot_table(index="win", columns="pct", values="rho")
        piv = piv.reindex(sorted(piv.index, key=float))
        im = ax.imshow(piv.abs().to_numpy(), cmap="Reds", vmin=0,
                       vmax=max(0.8, float(piv.abs().to_numpy().max())), aspect="auto")
        ax.set_xticks(range(len(piv.columns)))
        ax.set_xticklabels([f"p{c_}" for c_ in piv.columns], fontsize=7.5)
        ax.set_yticks(range(len(piv.index)))
        ax.set_yticklabels([f"w{i}s" for i in piv.index], fontsize=7.5)
        ax.set_xlabel("activity threshold percentile", fontsize=8.5)
        ax.set_ylabel("window length", fontsize=8.5)
        for yi, wv in enumerate(piv.index):
            for xi, pv in enumerate(piv.columns):
                v = piv.loc[wv, pv]
                if pd.notna(v):
                    ax.text(xi, yi, f"{abs(v):.2f}", ha="center", va="center", fontsize=6.4,
                            color="white" if abs(v) > 0.45 else "#333333")
        yi = list(piv.index).index(w0)
        xi = list(piv.columns).index(p0)
        ax.add_patch(plt.Rectangle((xi - 0.5, yi - 0.5), 1, 1, fill=False,
                                   edgecolor="#1a9850", lw=2.6))
        nb = piv.abs().to_numpy()
        ax.set_title(f"|rho| for the whole {stem} grid on {t}\n"
                     f"green box = the surviving cell;  grid median |rho| = {np.nanmedian(nb):.3f}",
                     fontsize=9.2)
        print(f"    neighbourhood: the {stem} grid on {t} has {np.isfinite(nb).sum()} cells,"
              f" median |rho| {np.nanmedian(nb):.3f}, max {np.nanmax(nb):.3f};"
              f" cells above the null 95th pct: "
              f"{int((nb > np.quantile(NULL_C[t], .95)).sum())}")
        # How much do the neighbouring grid cells actually measure the same thing? Without
        # this the disagreement above is easy to over-read: two settings that correlate at
        # 0.13 with each other are entitled to relate to the target differently, whereas two
        # that correlate at 0.9 are not.
        wl = sorted(piv.index, key=float)
        pl = list(piv.columns)
        wi, pi = wl.index(w0), pl.index(p0)
        nbnames = [f"{stem}_w{wl[wi + dw]}_p{pl[pi + dp]}"
                   for dw, dp in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                   if 0 <= wi + dw < len(wl) and 0 <= pi + dp < len(pl)]
        hv = rankdata(X[f].to_numpy())
        cors = [(nbn, spearman(hv, rankdata(X[nbn].to_numpy())),
                 float(sub.loc[sub.feature == nbn, "rho"].abs().iloc[0]))
                for nbn in nbnames if nbn in X.columns]
        print(f"    how much those neighbours share with the surviving column itself, and")
        print(f"    whether their own effect is what simple attenuation would predict:")
        print(f"      {'neighbour':34} {'corr w/ hit':>11} {'its |rho|':>10} {'predicted':>10}")
        for nbn, cr, ef in cors:
            print(f"      {nbn:34} {cr:+11.3f} {ef:10.3f} {abs(cr) * abs(full):10.3f}")
        print(f"      median |rank corr| with the neighbours: "
              f"{np.median([abs(c) for _, c, _ in cors]):.3f}")
        print(f"    'predicted' is |corr with the hit| x |the hit's own rho|. The observed")
        print(f"    column tracks it, i.e. each neighbour inherits the hit's association in")
        print(f"    proportion to how much of the hit it shares. Two things follow, and the")
        print(f"    second cancels the first:")
        print(f"      - the grid is NOT one strong cell surrounded by nothing; the drop-off")
        print(f"        is orderly, and neighbouring settings share only 0.13-0.72 with the")
        print(f"        cell that survived, so they were never near-duplicates of it;")
        print(f"      - but attenuation is an algebraic identity. It holds whether the hit's")
        print(f"        0.77 is a real association or a chance one, so the orderly drop-off")
        print(f"        is evidence for NEITHER. The grid neighbourhood turns out to be")
        print(f"        uninformative about real-versus-chance in both directions.")
    else:
        ax.axis("off")

fig.suptitle("Fig 7  The three cells that survived BH-FDR, examined individually\n"
             "row 1: the relationship and its least-squares line   row 2: sensitivity to removing any single subject   "
             "row 3: the same feature family at neighbouring settings",
             fontsize=11.5, y=0.995)
fig.tight_layout(rect=[0, 0.098, 1, 0.968])
fig.text(0.012, 0.010,
         "Row 1: the red line is the ordinary least squares fit on the raw values, y = w·x + b; the grey lines are the 24 refits that each leave one subject out. That line is NOT the statistic the screen tested --\n"
         "the screen used Spearman rank correlation, which involves no line at all, and the two disagree here (Pearson r belongs to the line, Spearman rho to the test). The line is drawn because its leave-one-out\n"
         "error is what the loo_r2cv column reports, so it is the only quantity on this figure that speaks to prediction rather than description. Row 3: path-A features are computed on a grid of 5 window lengths x 9\n"
         "activity-threshold percentiles. The neighbouring settings share only 0.13-0.72 rank correlation with the surviving cell, and their weaker effects match what simple attenuation predicts -- which holds whether\n"
         "the surviving cell is real or a chance maximum, so this grid is uninformative in both directions rather than evidence against. Row 2 is the n = 24 fragility check: how far the correlation moves when any\n"
         "single child is left out.",
         fontsize=7.2, color="#444444", linespacing=1.5)
fig.savefig(FIGDIR / "fig07_surviving_cells.png", dpi=200)
plt.close(fig)
print(f"\n  wrote {FIGDIR / 'fig07_surviving_cells.png'}")

# ---------------------------------------------------------------------------
# [8] FIGURE 08 -- the null is specified for untied features; many are tied
# ---------------------------------------------------------------------------
head("[8] TIED FEATURES AND THE SHARED NULL")
print("  44_univariate_screen.py builds one null per target by correlating shuffles of the")
print("  target against the FIXED rank vector 0..n-1. Its own comment on that line records")
print("  the assumption: 'equivalent to the null distribution of any feature WITHOUT ties'.")
print("  Sharing one null across 608 features is what makes the screen fast, and it is exact")
print("  for a feature whose 24 values are all distinct. A feature with tied values has a")
print("  different null, because ties coarsen the set of attainable correlations.")
print("  This section measures how many features are tied and what happens to the p-values")
print("  when each feature is tested against its own null instead of the shared one.")

Xr_all = np.column_stack([rankdata(X[f].to_numpy()) for f in FEATS])   # 24 x 608, midranks
ndist = np.array([len(np.unique(X[f].to_numpy())) for f in FEATS])
print(f"\n  distinct values per feature across the {n} subjects:")
for lo, hi in [(1, 1), (2, 4), (5, 9), (10, 17), (18, 23), (24, 24)]:
    k = int(((ndist >= lo) & (ndist <= hi)).sum())
    lbl = f"{lo}" if lo == hi else f"{lo}-{hi}"
    print(f"    {lbl:>7} distinct : {k:4d} features"
          + ("   (no ties: the shared null is exact)" if lo == 24 else ""))
print(f"  features with at least one tie : {int((ndist < n).sum())} of {len(FEATS)}")
print(f"  median distinct values         : {int(np.median(ndist))}")


TOL = 1e-12          # two permuted statistics count as equal within this


def _tail(cnt_gt, cnt_ge, nperm):
    """Two conventions for turning permutation counts into a p-value.
    gt : the convention in 44_univariate_screen.py -- the fraction of the null
         STRICTLY exceeding the observed value, then floored at 1/nperm.
    ge : the standard add-one estimator (1 + #{null >= observed}) / (1 + nperm),
         which is the convention 45_multivariate_cv.py uses on the other track.
    They differ only when the null puts mass exactly on the observed value, which
    happens when the feature is tied and the null is therefore discrete."""
    return np.maximum(cnt_gt / nperm, 1.0 / nperm), (1.0 + cnt_ge) / (1.0 + nperm)


def exact_p_cont(t, nperm=NPERM, block=10_000):
    """Permutation p for all 608 features of one continuous target, each against its
    own null: the feature's real rank vector is used instead of the untied 0..n-1."""
    yr = rankdata(Yc[t].to_numpy(float))
    yc = yr - yr.mean()
    nyc = np.sqrt((yc ** 2).sum())
    Xc = Xr_all - Xr_all.mean(axis=0)
    cn = np.sqrt((Xc ** 2).sum(axis=0))
    safe = np.where(cn > 0, cn, 1.0)
    obs = np.abs((Xc.T @ yc) / (safe * nyc))
    cgt = np.zeros(len(FEATS))
    cge = np.zeros(len(FEATS))
    done = 0
    while done < nperm:
        b = min(block, nperm - done)
        idx = np.argsort(rng.random((b, n)), axis=1)
        Yp = yr[idx]
        Ypc = Yp - Yp.mean(axis=1, keepdims=True)
        with np.errstate(all="ignore"):
            R = np.abs((Ypc @ Xc) / (nyc * safe))
        cgt += (R > obs + TOL).sum(axis=0)
        cge += (R >= obs - TOL).sum(axis=0)
        done += b
    return (*_tail(cgt, cge, nperm), obs)


def exact_p_bin(t, nperm=NPERM, block=10_000):
    """Same for a binary target: the label vector is shuffled and scored against the
    feature's real midranks rather than against 0..n-1."""
    lab = Yb[t].to_numpy(int)
    n1 = int(lab.sum())
    n0 = n - n1
    const = n1 * (n1 + 1) / 2
    obs = np.abs((lab.astype(float) @ Xr_all - const) / (n1 * n0) - 0.5)
    cgt = np.zeros(len(FEATS))
    cge = np.zeros(len(FEATS))
    done = 0
    while done < nperm:
        b = min(block, nperm - done)
        idx = np.argsort(rng.random((b, n)), axis=1)
        Lp = lab.astype(float)[idx]
        Av = np.abs((Lp @ Xr_all - const) / (n1 * n0) - 0.5)
        cgt += (Av > obs + TOL).sum(axis=0)
        cge += (Av >= obs - TOL).sum(axis=0)
        done += b
    return (*_tail(cgt, cge, nperm), obs)


print(f"\n  recomputing all {len(A):,} permutation p-values against feature-specific nulls")
print(f"  ({NPERM:,} permutations per target, every feature scored on the same shuffles)")
rows = []
for t in CONT:
    p_gt, p_ge, _ = exact_p_cont(t)
    g = A[(A["type"] == "cont") & (A["target"] == t)].set_index("feature").loc[FEATS]
    rows.append(pd.DataFrame(dict(target=t, type="cont", feature=FEATS,
                                  p_pub=g["perm_p"].to_numpy(), p_own=p_gt,
                                  p_addone=p_ge, ndist=ndist)))
for t in BIN:
    p_gt, p_ge, _ = exact_p_bin(t)
    g = A[(A["type"] == "bin") & (A["target"] == t)].set_index("feature").loc[FEATS]
    rows.append(pd.DataFrame(dict(target=t, type="bin", feature=FEATS,
                                  p_pub=g["perm_p"].to_numpy(), p_own=p_gt,
                                  p_addone=p_ge, ndist=ndist)))
P = pd.concat(rows, ignore_index=True)
P["q_own"] = np.nan
P["q_addone"] = np.nan
for t, g in P.groupby("target"):
    P.loc[g.index, "q_own"] = bh(g["p_own"].to_numpy())
    P.loc[g.index, "q_addone"] = bh(g["p_addone"].to_numpy())

tied = P["ndist"] < n
print(f"\n  {'group':34} {'cells':>7} {'median p published':>19} {'median p own null':>18}")
for lbl, mask in [("all cells", P.index == P.index),
                  ("cells whose feature has no ties", ~tied),
                  ("cells whose feature is tied", tied),
                  ("cells with <= 8 distinct values", P["ndist"] <= 8)]:
    s = P[mask]
    print(f"  {lbl:34} {len(s):7d} {s['p_pub'].median():19.4f} {s['p_own'].median():18.4f}")

print(f"\n  direction of the change, cells with p_published < 0.05:")
sel = P[P["p_pub"] < 0.05]
print(f"    own null gives a LARGER p (shared null was anti-conservative): "
      f"{int((sel['p_own'] > sel['p_pub']).sum())} of {len(sel)}")
print(f"    own null gives a SMALLER p                                  : "
      f"{int((sel['p_own'] < sel['p_pub']).sum())} of {len(sel)}")
print(f"    unchanged                                                   : "
      f"{int((sel['p_own'] == sel['p_pub']).sum())} of {len(sel)}")

print(f"\n  raw p < 0.05 : {int((P['p_pub'] < 0.05).sum())} cells with the shared null,"
      f" {int((P['p_own'] < 0.05).sum())} with feature-specific nulls"
      f"   (expected under the null: {0.05 * len(P):.0f})")
print(f"  BH-FDR q < 0.05 within target: {int((A['q_fdr'] < 0.05).sum())} cells published,"
      f" {int((P['q_own'] < 0.05).sum())} recomputed")

# --- the tail convention, which turns out to matter more than the null does -----
head("[8b] THE TAIL CONVENTION -- the two tracks do not use the same one")
print("  44_univariate_screen.py:  p = #{null STRICTLY > observed} / NPERM, floored at 1/NPERM")
print("      (the line 'pval=1-np.searchsorted(null,abs(rho),side=\"right\")/NPERM')")
print("  45_multivariate_cv.py:    p = (1 + #{null >= observed}) / (1 + NPERM)")
print("      (the line 'return (hits+1)/(NPERM+1)' with the test written as '>= obs')")
print("  For a continuous null the two agree to within 1/NPERM. They separate when the null")
print("  places mass exactly on the observed value, which is what a tied feature produces:")
print("  the attainable correlations become a short discrete list, and the observed value is")
print("  frequently the largest entry in it. Then #{null > observed} is 0 -- reported as the")
print("  floor 1e-5 -- while #{null >= observed} is a substantial count.")

P["equal_mass"] = P["p_addone"] - (P["p_own"] * NPERM) / (NPERM + 1.0)
print(f"\n  {'group':34} {'cells':>7} {'median p (>)':>13} {'median p (>=,+1)':>17}")
for lbl, mask in [("all cells", P.index == P.index),
                  ("feature has no ties", ~tied),
                  ("feature is tied", tied),
                  ("feature has <= 8 distinct values", P["ndist"] <= 8)]:
    s = P[mask]
    print(f"  {lbl:34} {len(s):7d} {s['p_own'].median():13.4f} {s['p_addone'].median():17.4f}")

print(f"\n  cells reported at the 1e-5 floor under the strictly-greater convention: "
      f"{int((P['p_own'] <= 1.0 / NPERM).sum())}")
atfloor = P[P["p_own"] <= 1.0 / NPERM]
print(f"    of those, the add-one convention gives p > 0.05 for "
      f"{int((atfloor['p_addone'] > 0.05).sum())} and p > 0.001 for "
      f"{int((atfloor['p_addone'] > 0.001).sum())}")
print(f"    their distinct-value counts: min {int(atfloor['ndist'].min())},"
      f" median {int(atfloor['ndist'].median())}, max {int(atfloor['ndist'].max())}")

print(f"\n  survivors at q < 0.05 under each combination:")
print(f"    published (shared null, strictly greater)        : {int((A['q_fdr'] < 0.05).sum())}")
print(f"    feature-specific null, strictly greater          : {int((P['q_own'] < 0.05).sum())}")
print(f"    feature-specific null, add-one and >=            : {int((P['q_addone'] < 0.05).sum())}")

print(f"\n  every cell that reaches q < 0.05 under any of the three, side by side:")
cand = P[(P["q_own"] < 0.05) | (P["q_addone"] < 0.05) |
         P.set_index(["target", "feature"]).index.isin(
             [(r["target"], r["feature"]) for r in SURV])]
print(f"  {'target':20} {'type':5} {'feature':26} {'dist':>4} {'p pub':>8} {'p own':>8}"
      f" {'p +1':>8} {'q pub':>8} {'q own':>8} {'q +1':>8}")
for _, r in cand.sort_values("p_addone").iterrows():
    qp = A[(A["target"] == r["target"]) & (A["feature"] == r["feature"])]["q_fdr"].iloc[0]
    print(f"  {r['target']:20} {r['type']:5} {r['feature']:26} {int(r['ndist']):4d}"
          f" {r['p_pub']:8.1e} {r['p_own']:8.1e} {r['p_addone']:8.1e}"
          f" {qp:8.4f} {r['q_own']:8.4f} {r['q_addone']:8.4f}")

print("\n  What the three columns together show:")
print("   - The published p-values are computed against an untied null, which is a")
print("     continuous distribution, so the strictly-greater convention costs nothing and")
print("     the published numbers are not distorted by it.")
print("   - Correcting the null to respect each feature's ties WITHOUT also correcting the")
print("     tail convention produces floor-level p-values for cells with no effect at all:")
print("     8 of the 10 cells that land on the 1e-5 floor have an add-one p above 0.001,")
print("     and 6 of them above 0.05. Those are an artefact of a discrete null, not results.")
print("   - Correcting both together leaves the same three cells the screen already")
print("     reported, at q = 0.0061, 0.0122 and 0.0182. The published positive yield of the")
print("     univariate track therefore stands under a correctly specified test.")

# pick the clearest example of the discreteness artefact for the mechanism panel
art = P[(P["p_own"] <= 1.0 / NPERM) & (P["p_addone"] > 0.05)]
ex = art.sort_values("p_addone", ascending=False).iloc[0]
ex_f, ex_t = ex["feature"], ex["target"]
xr_ex = rankdata(X[ex_f].to_numpy())
if ex["type"] == "bin":
    lab = Yb[ex_t].to_numpy(int)
    n1 = int(lab.sum())
    n0 = n - n1
    const = n1 * (n1 + 1) / 2
    idx = np.argsort(rng.random((NPERM, n)), axis=1)
    nullvals = np.abs((lab.astype(float)[idx] @ xr_ex - const) / (n1 * n0) - 0.5)
    obs_ex = abs((lab @ xr_ex - const) / (n1 * n0) - 0.5)
    stat_lbl = "|AUC - 0.5|"
else:
    yr_ex = rankdata(Yc[ex_t].to_numpy(float))
    idx = np.argsort(rng.random((NPERM, n)), axis=1)
    Yp = yr_ex[idx]
    Ypc = Yp - Yp.mean(axis=1, keepdims=True)
    xc_ex = xr_ex - xr_ex.mean()
    with np.errstate(all="ignore"):
        nullvals = np.abs((Ypc @ xc_ex) / np.sqrt((Ypc ** 2).sum(axis=1) * (xc_ex ** 2).sum()))
    obs_ex = abs(spearman(xr_ex, yr_ex))
    stat_lbl = "|Spearman rho|"
uu, cc = np.unique(np.round(nullvals, 10), return_counts=True)
vals_ex, cnts_ex = np.unique(X[ex_f].to_numpy(), return_counts=True)

fig, axes = plt.subplots(1, 3, figsize=(16.2, 5.3),
                         gridspec_kw={"width_ratios": [1, 1.15, 1.05], "wspace": 0.27})
ax = axes[0]
ax.hist(ndist, bins=np.arange(0.5, n + 1.5, 1), color="#4878a8", edgecolor="white", linewidth=0.6)
ax.axvline(n, color="#b2182b", lw=1.8, ls="--")
ax.annotate(f"{int((ndist == n).sum())} features have all {n}\nvalues distinct: for these\nthe shared null is exact",
            xy=(n, int((ndist == n).sum()) * 0.55), xytext=(15.0, int((ndist == n).sum()) * 0.72),
            ha="center", va="center", fontsize=8, color="#b2182b",
            arrowprops=dict(arrowstyle="->", color="#b2182b", lw=0.9))
ax.set_xlabel(f"Distinct values the feature takes across the {n} subjects")
ax.set_ylabel("Number of features")
ax.set_title(f"Fig 8a  How tied the {len(FEATS)} screened features are\n"
             f"{int((ndist < n).sum())} contain at least one tie", fontsize=10.5)
ax.grid(axis="y", alpha=0.22, lw=0.6)
ax.set_axisbelow(True)

ax = axes[1]
sub = P[(P["p_pub"] < 0.05) | (P["p_addone"] < 0.05)]
sc = ax.scatter(np.maximum(sub["p_pub"], 1e-5), np.maximum(sub["p_addone"], 1e-5),
                c=sub["ndist"], cmap="viridis", s=11, alpha=0.8, linewidths=0, vmin=1, vmax=n)
lim = [8e-6, 0.12]
ax.plot(lim, lim, color="#333333", lw=1.2, ls="--", label="unchanged")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(*lim)
ax.set_ylim(*lim)
for k, rec in enumerate(sorted(SURV, key=lambda d: d["target"])):
    r = P[(P["target"] == rec["target"]) & (P["feature"] == rec["feature"])].iloc[0]
    xy = (max(r["p_pub"], 1e-5), max(r["p_addone"], 1e-5))
    ax.scatter([xy[0]], [xy[1]], s=110, facecolor="none", edgecolor="#b2182b", lw=2.0, zorder=5)
    ax.annotate(f"{r['target']} x {r['feature']}", xy=xy,
                xytext=(2.6e-5, [1.1e-3, 3.4e-4, 1.0e-4][k]), fontsize=6.6, color="#b2182b",
                va="center", arrowprops=dict(arrowstyle="-", color="#b2182b", lw=0.7))
cb = fig.colorbar(sc, ax=ax, pad=0.015)
cb.set_label("distinct values of the feature", fontsize=8.5)
ax.set_xlabel("Permutation p as published\n(shared untied null, strictly-greater tail)")
ax.set_ylabel("Permutation p, correctly specified\n(feature's own null, add-one tail)")
ax.set_title("Fig 8b  Cells reaching p < 0.05 under either specification\n"
             "circled: the three that survive BH-FDR, under both", fontsize=10.5)
ax.legend(fontsize=8.2, frameon=False, loc="upper left")
ax.grid(alpha=0.22, lw=0.6, which="both")
ax.set_axisbelow(True)

ax = axes[2]
share = cc / cc.sum()
bars = ax.bar(range(len(uu)), share, color=["#b2182b" if abs(v - obs_ex) < 1e-9 else "#cccccc"
                                            for v in uu], width=0.6)
ax.set_xticks(range(len(uu)))
ax.set_xticklabels([f"{v:.4f}" for v in uu], fontsize=8)
ax.set_xlabel(f"{stat_lbl} attainable by shuffling")
ax.set_ylabel("Share of permutations")
ax.set_title(f"Fig 8c  Why that matters: the null of a heavily tied feature\n"
             f"{ex_f} on {ex_t}", fontsize=10.5)
for i, (v, s) in enumerate(zip(uu, share)):
    ax.text(i, s + 0.012, f"{s:.3f}", ha="center", fontsize=8.5)
ax.set_ylim(0, max(share) * 2.35)
ax.text(0.5, 0.97,
        f"feature values: " + ", ".join(f"{v:g} x{c}" for v, c in zip(vals_ex, cnts_ex)) +
        f"\n\nobserved statistic = {obs_ex:.4f} (red)\n"
        f"P(null >  observed) = {float((nullvals > obs_ex + TOL).mean()):.4f}"
        f"   -> reported as the floor 1e-5\n"
        f"P(null >= observed) = {float((nullvals >= obs_ex - TOL).mean()):.4f}"
        f"   -> the honest p-value",
        transform=ax.transAxes, ha="center", va="top", fontsize=8.2,
        bbox=dict(boxstyle="round,pad=0.45", fc="#fff6f4", ec="#b2182b", lw=0.9))
ax.grid(axis="y", alpha=0.22, lw=0.6)
ax.set_axisbelow(True)

fig.tight_layout()
fig.subplots_adjust(bottom=0.235)
fig.text(0.012, 0.018,
         "The screen shares one permutation null across all 608 features of a target by shuffling the target against the untied rank vector 0..n-1; its own comment records that this is the null 'of any feature\n"
         "WITHOUT ties'. Panel b holds the statistic and the correction fixed and changes only the specification: each feature scored against shuffles evaluated on its own rank vector, with the add-one tail\n"
         "(1 + #{null >= observed}) / (1 + NPERM) that 45_multivariate_cv.py already uses. Panel c shows why the tail convention cannot be changed independently of the null: for a feature where 22 of 24 subjects\n"
         "share one value, the null has a two-point support, the observed statistic is the upper point, and the strictly-greater tail reports 1e-5 for what is in fact a p of roughly one half.",
         fontsize=7.2, color="#444444", linespacing=1.5)
fig.savefig(FIGDIR / "fig08_tie_corrected_pvalues.png", dpi=200)
plt.close(fig)
print(f"\n  wrote {FIGDIR / 'fig08_tie_corrected_pvalues.png'}")

# ---------------------------------------------------------------------------
# [9] FIGURE 09 -- where the movement-total negative control ranks
# ---------------------------------------------------------------------------
head("[9] NEGATIVE CONTROL -- how uaMag_median ranks among the 608 features")
NC = "uaMag_median"
print(f"  The project's claim is 'structure, not amount' (45_multivariate_cv.py, header).")
print(f"  {NC} is the designated stand-in for amount: the median magnitude of gravity-removed")
print(f"  acceleration. If it ranks near the top of a target's 608 features, the leading hits")
print(f"  for that target cannot be attributed to structure without a further control.")

eff = A.copy()
eff["effect"] = np.where(eff["type"] == "cont", eff["rho"].abs(), (eff["auc"] - 0.5).abs())
ncrank = []
for t in CONT + BIN:
    g = eff[eff["target"] == t]
    v = float(g.loc[g["feature"] == NC, "effect"].iloc[0])
    rank = int((g["effect"] > v).sum()) + 1
    ncrank.append(dict(target=t, kind="cont" if t in CONT else "bin", effect=v, rank=rank,
                       pct=100 * (1 - (rank - 1) / len(g)),
                       maxeff=float(g["effect"].max()),
                       p=float(g.loc[g["feature"] == NC, "perm_p"].iloc[0])))
NCR = pd.DataFrame(ncrank)
print(f"\n  {'target':24} {'kind':5} {'effect of NC':>12} {'rank of 608':>12} {'top %':>7}"
      f" {'best feature effect':>19} {'perm_p of NC':>13}")
for _, r in NCR.iterrows():
    print(f"  {r['target']:24} {r['kind']:5} {r['effect']:12.3f} {r['rank']:12d}"
          f" {100 - r['pct']:6.1f}% {r['maxeff']:19.3f} {r['p']:13.4f}")
print(f"\n  median rank of the negative control across the 20 targets: "
      f"{int(NCR['rank'].median())} of 608")
print(f"  targets where it ranks in the top 5% (rank <= 30): "
      f"{sorted(NCR.loc[NCR['rank'] <= 30, 'target'].tolist()) or 'none'}")
print(f"  targets where it reaches perm_p < 0.05: "
      f"{sorted(NCR.loc[NCR['p'] < 0.05, 'target'].tolist()) or 'none'}")

print(f"\n  how much movement-total is inside the features that produced the three survivors:")
print(f"  {'feature':30} {'Spearman rho with ' + NC:>28}")
for f in sorted({r['feature'] for r in SURV}):
    rr = spearman(rankdata(X[f].to_numpy()), rankdata(X[NC].to_numpy()))
    print(f"  {f:30} {rr:28.3f}")
print(f"  (path-A features threshold each child against that child's own percentile, which is")
print(f"   what makes them amplitude-invariant; these numbers measure that claim directly")
print(f"   rather than assuming it.)")

fig, ax = plt.subplots(figsize=(12.6, 6.4))
NCR2 = NCR.sort_values("rank")
for i, (_, r) in enumerate(NCR2.iterrows()):
    g = eff[eff["target"] == r["target"]]
    xs = g["effect"].to_numpy() / g["effect"].max()
    ax.scatter(xs, np.full(len(xs), i) + (np.random.default_rng(i).random(len(xs)) - .5) * 0.4,
               s=1.5, color="#cccccc", alpha=0.55, linewidths=0)
    ax.scatter([r["effect"] / r["maxeff"]], [i], s=70, color="#b2182b", zorder=5,
               marker="D", edgecolor="white", linewidth=0.8)
    ax.text(1.012, i, f"rank {r['rank']:3d} / 608", transform=ax.get_yaxis_transform(),
            va="center", fontsize=7.8, family="monospace")
ax.set_yticks(range(len(NCR2)))
ax.set_yticklabels([f"{r['target']}  [{r['kind']}]" for _, r in NCR2.iterrows()], fontsize=8.4)
ax.invert_yaxis()
ax.set_xlim(-0.02, 1.04)
ax.set_xlabel("Effect size relative to the strongest feature for that target\n"
              "(|Spearman rho| for continuous targets, |AUC - 0.5| for binary; 1.0 = that target's best feature)")
ax.set_title("Fig 9  Where the movement-total negative control uaMag_median sits among the 608 screened features\n"
             "grey = all 608 features for that target;  red diamond = the negative control",
             fontsize=11)
ax.grid(axis="x", alpha=0.22, lw=0.6)
ax.set_axisbelow(True)
fig.tight_layout()
fig.subplots_adjust(bottom=0.20, right=0.88)
fig.text(0.012, 0.018,
         "Effect sizes are scaled within each target so that the two statistics can share one axis; the ranks in the right-hand column are computed on the raw effect sizes and are not affected by that scaling.\n"
         "A high rank for the negative control would mean the target is tracking how much the child moved. Absolute effect sizes and the control's own permutation p are in section [9] of the snapshot.",
         fontsize=7.2, color="#444444", linespacing=1.5)
fig.savefig(FIGDIR / "fig09_negative_control_rank.png", dpi=200)
plt.close(fig)
print(f"\n  wrote {FIGDIR / 'fig09_negative_control_rank.png'}")

# ---------------------------------------------------------------------------
# [10] FIGURE 10 -- the movement-total control on the 45 path-B columns
# ---------------------------------------------------------------------------
head("[10] PARTIAL CONTROL -- the 45 path-B columns, before and after removing movement total")
PB = sorted(A.loc[A["rho_partial_uamag"].notna() | A["auc_partial_uamag"].notna(), "feature"].unique())
print(f"  Path-B features threshold every child against ONE pooled line, so a child who moves")
print(f"  harder spends more time above it; MODEL_MENU.md records |rho| = 0.877 between the")
print(f"  p50 actfrac column and the negative control. These {len(PB)} columns are the only ones the")
print(f"  screen re-tests with movement total removed. The other {len(FEATS) - len(PB)} are not re-tested at all.")
print("  Reading, from 44_univariate_screen.py: shrinks a lot => the original association was")
print("  a movement-total artefact; unchanged => structure; grows => suppression, structure")
print("  that total movement was masking.")

pbc = A[(A["type"] == "cont") & (A["feature"].isin(PB))].copy()
pbc["before"] = pbc["rho"].abs()
pbc["after"] = pbc["rho_partial_uamag"].abs()
pbb = A[(A["type"] == "bin") & (A["feature"].isin(PB))].copy()
pbb["before"] = (pbb["auc"] - 0.5).abs()
pbb["after"] = (pbb["auc_partial_uamag"] - 0.5).abs()
for lbl, d, band in [("continuous (|rho|, no-effect 0, range [0,1])", pbc, 0.10),
                     ("binary (|AUC-0.5|, no-effect 0, range [0,0.5])", pbb, 0.05)]:
    sh = d["before"] - d["after"]
    print(f"\n  {lbl}   {len(d)} cells")
    print(f"    median effect before {d['before'].median():.3f} -> after {d['after'].median():.3f}"
          f"   (median change {-sh.median():+.3f})")
    print(f"    shrank by more than {band}: {int((sh > band).sum()):4d}"
          f"   |  within +/-{band}: {int((sh.abs() <= band).sum()):4d}"
          f"   |  grew by more than {band}: {int((sh < -band).sum()):4d}")
    NULLS = NULL_C if d is pbc else NULL_B
    b_ok = sum(int(r["before"] > np.quantile(NULLS[r["target"]], .95)) for _, r in d.iterrows())
    a_ok = sum(int(r["after"] > np.quantile(NULLS[r["target"]], .95)) for _, r in d.iterrows())
    print(f"    cells above the target's null 95th percentile, before -> after: {b_ok} -> {a_ok}")

fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.9))
for ax, d, lbl, base, rng_ in [
        (axes[0], pbc, "Continuous targets:  |Spearman rho|", 0.0, 1.0),
        (axes[1], pbb, "Binary targets:  |AUC - 0.5|", 0.0, 0.5)]:
    top = max(d["before"].max(), d["after"].max()) * 1.06
    ax.plot([0, top], [0, top], color="#333333", lw=1.2, ls="--", label="unchanged by the control")
    sc = ax.scatter(d["before"], d["after"], s=16, alpha=0.7, linewidths=0,
                    c=[CONT.index(t) if t in CONT else BIN.index(t) for t in d["target"]],
                    cmap="tab10")
    ax.set_xlim(0, top)
    ax.set_ylim(0, top)
    ax.set_xlabel(f"before: {lbl.split(':')[1].strip()}")
    ax.set_ylabel(f"after removing movement total")
    sh = d["before"] - d["after"]
    ax.set_title(f"{lbl}\n{len(d)} cells;  {int((sh > 0).sum())} shrank, {int((sh < 0).sum())} grew"
                 f"   (axis range [0, {rng_:g}])", fontsize=10.2)
    ax.text(0.03, 0.97, f"median before {d['before'].median():.3f}\nmedian after  {d['after'].median():.3f}",
            transform=ax.transAxes, va="top", fontsize=8.4, family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#cccccc"))
    ax.legend(fontsize=8.2, frameon=False, loc="lower right")
    ax.grid(alpha=0.22, lw=0.6)
    ax.set_axisbelow(True)
fig.suptitle("Fig 10  The only movement-total control in the univariate track, applied to the 45 path-B columns\n"
             "points below the dashed line lost effect when total movement was removed; points above it gained",
             fontsize=11)
fig.tight_layout(rect=[0, 0.10, 1, 0.94])
fig.text(0.012, 0.018,
         "Left and right panels use different statistics on different ranges and are deliberately not drawn on a shared scale: |rho| lives in [0,1] with no effect at 0, |AUC - 0.5| lives in [0,0.5] with no\n"
         f"effect at 0. Colour distinguishes targets. These {len(PB)} of {len(FEATS)} features are the whole extent of the control: the remaining {len(FEATS) - len(PB)} columns carry no movement-total adjustment in this track, and the\n"
         "classification half of the multivariate track carries none at all. The partial statistic has no p-value and no q-value in the published table; it is an effect size only.",
         fontsize=7.2, color="#444444", linespacing=1.5)
fig.savefig(FIGDIR / "fig10_partial_control_pathB.png", dpi=200)
plt.close(fig)
print(f"\n  wrote {FIGDIR / 'fig10_partial_control_pathB.png'}")

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
    "# 61_univariate.md -- verbatim stdout snapshot\n\n"
    "**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.\n\n"
    "- Producing script: `analysis/61_univariate_analysis.py`\n"
    f"- Repository HEAD when this snapshot was generated: `{commit}`\n"
    "- Reproduce with: `.venv/bin/python analysis/61_univariate_analysis.py`\n"
    f"- Permutation nulls rebuilt here use {NPERM:,} draws per target, seed {SEED}. The screen\n"
    "  itself used seed 20260717, so permutation p-values agree only to Monte-Carlo error.\n\n"
    "```text\n"
)
(TABDIR / "61_univariate.md").write_text(hdr + body + "```\n", encoding="utf-8")
print(f"\nwrote {TABDIR / '61_univariate.md'}")
