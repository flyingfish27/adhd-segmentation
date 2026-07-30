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

Re-run with:
    .venv/bin/python analysis/61_univariate_analysis.py
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
