# -*- coding: utf-8 -*-
# =============================================================================
# 70_feature_inventory.py -- read-only inventory of analysis/features.csv
# (TASK-124, phase 2 "feature-table reduction", first probe; user-directed step
#  2026-08-11: "先去看一下现在的 features 是什么情况")
#
# Measures, from the CSV itself (never copied from FEATURE_MENU.md):
#   [1] shape / key / dtypes
#   [2] family decomposition by the documented naming rules, with an exact
#       total-count assertion (608)
#   [3] missing values, per column
#   [4] degenerate columns: constants and low-unique-count columns
#   [4b] near-constant columns: mode dominance -- how many of the 24 subjects
#        share the single most frequent value (exact ties; user-directed step
#        2026-08-11: "常数特征、几乎全是同一个值的特征，找出来")
#   [5] redundancy: pairwise |Spearman| among all 608 features on the 24
#       subjects, plus connected components at two thresholds
#
# Read-only: writes nothing except the stdout snapshot
# analysis/probe_outputs/feature_inventory.md (house pattern of 60_-66_).
# Inputs are all under version control -- run from any checkout, no ADHD_ROOT.
# Reproduce with: .venv/bin/python analysis/70_feature_inventory.py
# =============================================================================
import io, pathlib, re, subprocess, sys

import numpy as np
import pandas as pd
from scipy.stats import rankdata

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SNAP = HERE / "probe_outputs" / "feature_inventory.md"

buf = io.StringIO()


class Tee:
    def write(self, s):
        sys.__stdout__.write(s)
        buf.write(s)

    def flush(self):
        sys.__stdout__.flush()


sys.stdout = Tee()


def section(title):
    print("\n" + "=" * 78 + f"\n[{title}\n" + "=" * 78)


df = pd.read_csv(ROOT / "analysis" / "features.csv")

section("1] SHAPE / KEY / DTYPES")
print(f"  file: analysis/features.csv")
print(f"  shape: {df.shape[0]} rows x {df.shape[1]} columns")
assert "subject" in df.columns
feat = df.drop(columns=["subject"])
print(f"  key column: 'subject' ({df['subject'].nunique()} unique of {len(df)})")
print(f"  feature columns: {feat.shape[1]}")
nonnum = [c for c in feat.columns if not np.issubdtype(feat[c].dtype, np.number)]
print(f"  non-numeric feature columns: {len(nonnum)}" + (f"  {nonnum}" if nonnum else ""))

section("2] FAMILY DECOMPOSITION BY NAMING RULE (asserted, not assumed)")
CHANNELS = ["uaX", "uaY", "uaZ", "uaMag", "gyX", "gyY", "gyZ", "gyMag",
            "pitch", "roll", "yaw", "jerk"]
NL_SUFF = ["dfa_alpha", "hurst_rs", "permen_m3", "lz_c", "acf_tau_1e_s",
           "acf_dom_period_s", "acf_dom_peak", "peak_rate_min",
           "peak_ipi_med_s", "peak_ipi_cv", "peak_amp_med", "peak_amp_cv"]
pathA_re = re.compile(
    r"^(switch_per_min|act_bout_median|stl_bout_median|act_bout_cv|stl_bout_cv|"
    r"frac_act_short)_w(0\.5|1|2|5|10)_p(10|20|30|40|50|60|70|80|90)$")
wwsd_re = re.compile(r"^within_win_sd_w(0\.5|1|2|5|10)$")
pathB_re = re.compile(
    r"^(actfrac|switchmin|actbout_med|actbout_cv|actshort)_p(10|20|30|40|50|60|70|80|90)$")
nl_re = re.compile(r"^(uaMag|gyMag|jerk)_(" + "|".join(NL_SUFF) + r")$")

fam = {}
for c in feat.columns:
    if pathA_re.match(c) or wwsd_re.match(c):
        fam[c] = "pathA_tstruct"
    elif pathB_re.match(c):
        fam[c] = "pathB_tstruct"
    elif nl_re.match(c):
        fam[c] = "nonlinear"
    elif c == "rec_dur_min":
        fam[c] = "rec_dur"
    elif any(c.startswith(ch + "_") for ch in CHANNELS):
        fam[c] = "channel_stat"
    else:
        fam[c] = "UNCLASSIFIED"
fs = pd.Series(fam)
counts = fs.value_counts()
for k in ["channel_stat", "pathA_tstruct", "pathB_tstruct", "nonlinear",
          "rec_dur", "UNCLASSIFIED"]:
    print(f"  {k:<14} {counts.get(k, 0):>4}")
assert counts.get("UNCLASSIFIED", 0) == 0, fs[fs == "UNCLASSIFIED"].index.tolist()
assert (counts.get("channel_stat", 0), counts.get("pathA_tstruct", 0),
        counts.get("pathB_tstruct", 0), counts.get("nonlinear", 0),
        counts.get("rec_dur", 0)) == (251, 275, 45, 36, 1), counts.to_dict()
print("  assertion passed: 251 + 275 + 45 + 36 + 1 = 608")
print("\n  channel_stat columns per channel:")
per_ch = {ch: sum(1 for c, f in fam.items()
                  if f == "channel_stat" and c.startswith(ch + "_"))
          for ch in CHANNELS}
for ch in CHANNELS:
    print(f"    {ch:<6} {per_ch[ch]:>3}")
print(f"  negative-control column present: {'uaMag_median' in feat.columns}"
      f"  ('uaMag_median')")

section("3] MISSING VALUES")
nan_per_col = feat.isna().sum()
with_nan = nan_per_col[nan_per_col > 0].sort_values(ascending=False)
print(f"  columns with any NaN: {len(with_nan)} of {feat.shape[1]}")
for c, n in with_nan.items():
    print(f"    {c:<28} NaN in {n:>2}/24 subjects   family={fam[c]}")

section("4] DEGENERATE / DISCRETE COLUMNS")
nuni = feat.nunique(dropna=True)
print(f"  constant columns (1 unique value): {(nuni == 1).sum()}")
for thr in (2, 3, 4, 5, 10):
    print(f"  columns with <= {thr:>2} unique values (of 24): {(nuni <= thr).sum()}")
low = nuni[nuni <= 5].sort_values()
print(f"\n  the {len(low)} columns with <= 5 unique values, by family:")
lowfam = pd.Series({c: fam[c] for c in low.index}).value_counts()
for k, v in lowfam.items():
    print(f"    {k:<14} {v:>3}")
print("\n  worst 15 (fewest unique values):")
for c in low.index[:15]:
    print(f"    {c:<28} {nuni[c]} unique   family={fam[c]}")

section("4b] NEAR-CONSTANT: MODE DOMINANCE (exact ties among the 24 values)")
mode_n = feat.apply(lambda s: int(s.value_counts(dropna=True).iloc[0]))
mode_v = feat.apply(lambda s: s.value_counts(dropna=True).index[0])
print("  'mode_n' = subjects sharing the single most frequent value (of 24).")
print("  a constant column would be mode_n = 24; measured max is "
      f"{mode_n.max()}.\n")
print("  distribution:")
for thr in (24, 23, 22, 20, 18, 16, 14, 12):
    print(f"    columns with mode_n >= {thr:>2}: {(mode_n >= thr).sum():>3}")
dom = mode_n[mode_n >= 12].sort_values(ascending=False)
print(f"\n  full list of the {len(dom)} columns with mode_n >= 12 "
      f"(most frequent value shared by half the sample or more):")
print(f"    {'column':<28} {'mode_n':>6} {'nunique':>8} {'mode value':>12}  family")
for c in dom.index:
    print(f"    {c:<28} {dom[c]:>4}/24 {nuni[c]:>8} {mode_v[c]:>12.6g}  {fam[c]}")

section("5] REDUNDANCY -- pairwise |Spearman| on the 24 subjects")
# rank once per column (NaN-aware: rank only non-NaN, pairwise complete obs
# would be costlier; here we drop NaN columns from the matrix and say so)
nan_cols = list(with_nan.index)
X = feat.drop(columns=nan_cols)
print(f"  computed on {X.shape[1]} columns ({len(nan_cols)} NaN-bearing columns"
      f" excluded from the matrix, listed in [3])")
R = np.apply_along_axis(rankdata, 0, X.to_numpy(float))
R = (R - R.mean(0)) / R.std(0)
C = np.abs(R.T @ R / R.shape[0])
np.fill_diagonal(C, 0.0)
iu = np.triu_indices_from(C, k=1)
pairs = C[iu]
n = X.shape[1]
print(f"  feature pairs total: {pairs.size}")
for thr in (0.999, 0.99, 0.95, 0.90, 0.80):
    print(f"  pairs with |rho| >= {thr:<5}: {(pairs >= thr).sum():>6}")
print(f"  features having at least one partner |rho| >= 0.95: "
      f"{(C.max(1) >= 0.95).sum()} of {n}")
print(f"  features having at least one partner |rho| >= 0.90: "
      f"{(C.max(1) >= 0.90).sum()} of {n}")


def components(thr):
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b in zip(*np.where(C >= thr)):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    roots = pd.Series([find(i) for i in range(n)])
    sizes = roots.value_counts()
    return sizes


for thr in (0.95, 0.90):
    sizes = components(thr)
    print(f"\n  connected components at |rho| >= {thr}: {len(sizes)} groups "
          f"(from {n} features)")
    print(f"    singletons: {(sizes == 1).sum()}   largest group: {sizes.max()}")
    print(f"    group-size distribution (size: how many groups): "
          f"{dict(sizes.value_counts().sort_index())}")

section("6] EXACT-DUPLICATE CHECK (identical values, not just rank-identical)")
dup = 0
seen = {}
for c in X.columns:
    key = X[c].round(12).to_numpy().tobytes()
    if key in seen:
        print(f"    duplicate pair: {seen[key]}  ==  {c}")
        dup += 1
    else:
        seen[key] = c
print(f"  exact duplicate column pairs: {dup}")

# ---- snapshot ---------------------------------------------------------------
sys.stdout = sys.__stdout__
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                      capture_output=True, text=True).stdout.strip()
SNAP.write_text(
    "# feature_inventory.md -- verbatim stdout snapshot\n\n"
    "**Do not hand-edit.** To update, re-run the producing script and let it "
    "overwrite this file.\n\n"
    "- Producing script: `analysis/70_feature_inventory.py`\n"
    f"- Repository HEAD when this snapshot was generated: `{head}`\n"
    "- Reproduce with: `.venv/bin/python analysis/70_feature_inventory.py`\n\n"
    "```text\n" + buf.getvalue() + "\n```\n",
    encoding="utf-8")
print(f"\nsnapshot written: {SNAP.relative_to(ROOT)}")
