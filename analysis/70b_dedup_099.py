# -*- coding: utf-8 -*-
# =============================================================================
# 70b_dedup_099.py -- execute FS-D3: drop near-duplicate columns at
# |Spearman| >= 0.99 (user decision 2026-08-12: "先把两两 |Spearman| 中
# ≥0.99 的删了"), keeping one column per connected group.
#
# Input set: analysis/features.csv MINUS rec_dur_min (FS-D1) = 607 columns.
# Groups: connected components of |Spearman| >= 0.99 (construction identical
# to 70_feature_inventory.py section [5]).
#
# KEEP RULE, declared and deterministic (the user can overrule any group):
#   0. uaMag_median, the on-record negative control, is never dropped;
#   1. more unique values (resolution) wins;
#   2. a column without an on-record caveat beats a path-B column (R10);
#   3. swept-parameter columns: smaller grid distance to the centre
#      (w2 / p50) wins;  channel statistics: an "elementary form" priority
#      list wins (mean, median, std, zcr, iqr, min, max, skew, kurt,
#      madiff, rms, mad, range, var -- earlier = kept);
#   4. final fallback, declared arbitrary: lexicographically first.
#
# At |rho| = 1.00 the members are rank-identical: for every Spearman-based
# statistic downstream the kept column carries exactly the same information
# as the dropped ones.
#
# Read-only apart from the stdout snapshot
# analysis/probe_outputs/dedup_099.md.
# Reproduce with: .venv/bin/python analysis/70b_dedup_099.py
# =============================================================================
import io, pathlib, re, subprocess, sys

import numpy as np
import pandas as pd
from scipy.stats import rankdata

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SNAP = HERE / "probe_outputs" / "dedup_099.md"

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


W_ORDER = ["0.5", "1", "2", "5", "10"]
pathA_re = re.compile(
    r"^(switch_per_min|act_bout_median|stl_bout_median|act_bout_cv|stl_bout_cv|"
    r"frac_act_short)_w(0\.5|1|2|5|10)_p(10|20|30|40|50|60|70|80|90)$")
wwsd_re = re.compile(r"^within_win_sd_w(0\.5|1|2|5|10)$")
pathB_re = re.compile(
    r"^(actfrac|switchmin|actbout_med|actbout_cv|actshort)_p(10|20|30|40|50|60|70|80|90)$")
PRIORITY = ["mean", "median", "std", "zcr", "iqr", "min", "max", "skew",
            "kurt", "madiff", "rms", "mad", "range", "var"]
CHANNELS = ["uaX", "uaY", "uaZ", "uaMag", "gyX", "gyY", "gyZ", "gyMag",
            "pitch", "roll", "yaw", "jerk"]


def grid_dist(c):
    m = pathA_re.match(c)
    if m:
        return abs(W_ORDER.index(m.group(2)) - 2) + abs(int(m.group(3)) // 10 - 1 - 4)
    m = wwsd_re.match(c)
    if m:
        return abs(W_ORDER.index(m.group(1)) - 2)
    m = pathB_re.match(c)
    if m:
        return abs(int(m.group(2)) // 10 - 1 - 4)
    return 0


def suffix_rank(c):
    for ch in CHANNELS:
        if c.startswith(ch + "_"):
            suf = c[len(ch) + 1:]
            return PRIORITY.index(suf) if suf in PRIORITY else len(PRIORITY)
    return len(PRIORITY)


df = pd.read_csv(ROOT / "analysis" / "features.csv")
feat = df.drop(columns=["subject", "rec_dur_min"])  # FS-D1
cols = list(feat.columns)
n = len(cols)
nuni = feat.nunique()

section("1] GROUPS AT |Spearman| >= 0.99")
X = feat.to_numpy(float)
R = np.apply_along_axis(rankdata, 0, X)
R = (R - R.mean(0)) / R.std(0)
C = np.abs(R.T @ R / R.shape[0])
np.fill_diagonal(C, 0.0)
THR = 0.99
print(f"  working set: {n} columns (FS-D1 already applied)")
iu = np.triu_indices(n, k=1)
print(f"  pairs with |rho| >= {THR}: {(C[iu] >= THR).sum()}")

parent = list(range(n))


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


for a, b in zip(*np.where(C >= THR)):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb
groups = {}
for i in range(n):
    groups.setdefault(find(i), []).append(i)
multi = sorted([g for g in groups.values() if len(g) > 1], key=len, reverse=True)
print(f"  groups of near-duplicates: {len(multi)} "
      f"(sizes {[len(g) for g in multi]})")

section("2] KEEP / DROP PER GROUP (keep rule in the header comment)")


def keep_key(c):
    return (0 if c == "uaMag_median" else 1,
            -int(nuni[c]),
            1 if pathB_re.match(c) else 0,
            grid_dist(c),
            suffix_rank(c),
            c)


drops = []
for gi, g in enumerate(multi, 1):
    names = sorted((cols[i] for i in g), key=keep_key)
    keep, rest = names[0], names[1:]
    sub = C[np.ix_(g, g)]
    mn = sub[np.triu_indices(len(g), k=1)].min()
    drops += rest
    flag = "  [negative control kept]" if keep == "uaMag_median" else ""
    print(f"  D{gi:02d} (internal min |rho| {mn:.3f})  "
          f"KEEP {keep} (nunique={int(nuni[keep])}){flag}")
    for c in rest:
        print(f"        drop {c} (nunique={int(nuni[c])}, "
              f"|rho| vs kept = {C[cols.index(keep), cols.index(c)]:.3f})")

section("3] RESULT")
drops = sorted(drops)
print(f"  columns dropped: {len(drops)}")
print(f"  working set after FS-D3: {n} - {len(drops)} = {n - len(drops)} columns")
print(f"  negative control uaMag_median still present: "
      f"{'uaMag_median' not in drops}")
print(f"  phase-1 FDR survivors untouched: "
      f"{'frac_act_short_w10_p20' not in drops and 'act_bout_median_w0.5_p80' not in drops}")
print("\n  full drop list:")
for c in drops:
    print(f"    {c}")
rem = [c for c in cols if c not in drops]
Xr = feat[rem].to_numpy(float)
Rr = np.apply_along_axis(rankdata, 0, Xr)
Rr = (Rr - Rr.mean(0)) / Rr.std(0)
Cr = np.abs(Rr.T @ Rr / Rr.shape[0])
np.fill_diagonal(Cr, 0.0)
print(f"\n  verification: max pairwise |rho| among the remaining "
      f"{len(rem)} columns = {Cr.max():.4f} (must be < {THR})")
assert Cr.max() < THR

sys.stdout = sys.__stdout__
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                      capture_output=True, text=True).stdout.strip()
SNAP.write_text(
    "# dedup_099.md -- verbatim stdout snapshot\n\n"
    "**Do not hand-edit.** To update, re-run the producing script and let it "
    "overwrite this file.\n\n"
    "- Producing script: `analysis/70b_dedup_099.py`\n"
    f"- Repository HEAD when this snapshot was generated: `{head}`\n"
    "- Reproduce with: `.venv/bin/python analysis/70b_dedup_099.py`\n\n"
    "```text\n" + buf.getvalue() + "\n```\n",
    encoding="utf-8")
print(f"\nsnapshot written: {SNAP.relative_to(ROOT)}")
