# -*- coding: utf-8 -*-
# =============================================================================
# 70c_dedup_095_greedy.py -- execute FS-D4: pairwise-guaranteed dedup at
# |Spearman| >= 0.95 (user decision 2026-08-12: scheme B, "逐对贪心", with the
# static declared priority order; approved after seeing the order-sensitivity
# measurement of forward/backward/float variants).
#
# Input set: analysis/features.csv MINUS rec_dur_min (FS-D1) MINUS the 33
# FS-D3 drops (hardcoded below from analysis/probe_outputs/dedup_099.md and
# asserted against the table) = 574 columns.
#
# ALGORITHM (declared, deterministic):
#   sort all columns by the keep-priority below, walk the list once, keep a
#   column unless it correlates >= 0.95 with an already-kept column (then
#   drop it and record the kept partner).  Guarantee by construction: every
#   dropped column has a kept partner at |rho| >= 0.95; kept columns are
#   pairwise < 0.95.
#
# KEEP PRIORITY (same rule family as FS-D3, declared in the ledger):
#   0. protected, never dropped: uaMag_median (negative control),
#      frac_act_short_w10_p20 and act_bout_median_w0.5_p80 (carriers of the
#      two phase-1 FDR survivors; measured max partners 0.58 / 0.76, so the
#      protection is declarative rather than load-bearing);
#   1. more unique values; 2. no on-record caveat (path-B = R10);
#   3. smaller grid distance to centre / earlier elementary-form suffix;
#   4. lexicographic, the stated-arbitrary fallback.
#
# Writes (besides the stdout snapshot analysis/probe_outputs/dedup_095.md):
#   analysis/feature_keeplist_512.csv -- the 512 surviving column names in
#   features.csv column order.  Added 2026-08-12 under FS-D5: the K-grid
#   baseline (71_) and any future wrapper must read the SAME frozen input,
#   so the ledger chain FS-D1/D3/D4 is materialised here, by the script
#   that computed it, rather than re-derived downstream.
# Reproduce with: .venv/bin/python analysis/70c_dedup_095_greedy.py
# =============================================================================
import io, pathlib, re, subprocess, sys
from collections import Counter

import numpy as np
import pandas as pd
from scipy.stats import rankdata

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SNAP = HERE / "probe_outputs" / "dedup_095.md"

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


FS_D3_DROPS = [
    "gyMag_range", "gyMag_var", "gyX_mad", "gyX_rms", "gyX_var", "gyY_mad",
    "gyY_rms", "gyY_spread", "gyY_var", "gyZ_mad", "gyZ_rms", "gyZ_spread",
    "gyZ_var", "jerk_mad", "jerk_rms", "jerk_var", "pitch_range",
    "pitch_spread", "pitch_var", "roll_spread", "roll_var", "uaMag_madiff",
    "uaMag_range", "uaMag_var", "uaX_mad", "uaX_rms", "uaX_var", "uaY_rms",
    "uaY_var", "uaZ_rms", "uaZ_var", "yaw_spread", "yaw_var",
]
PROTECT = ["uaMag_median", "frac_act_short_w10_p20", "act_bout_median_w0.5_p80"]

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


def fam(c):
    if pathA_re.match(c) or wwsd_re.match(c):
        return "pathA"
    if pathB_re.match(c):
        return "pathB"
    if re.match(r"^(uaMag|gyMag|jerk)_(dfa_alpha|hurst_rs|permen_m3|lz_c|"
                r"acf_tau_1e_s|acf_dom_period_s|acf_dom_peak|peak_rate_min|"
                r"peak_ipi_med_s|peak_ipi_cv|peak_amp_med|peak_amp_cv)$", c):
        return "nonlinear"
    return "channel"


df = pd.read_csv(ROOT / "analysis" / "features.csv")
feat = df.drop(columns=["subject", "rec_dur_min"])  # FS-D1
assert all(c in feat.columns for c in FS_D3_DROPS)
feat = feat.drop(columns=FS_D3_DROPS)               # FS-D3
cols = list(feat.columns)
n = len(cols)
nuni = feat.nunique()

section("1] INPUT SET AFTER FS-D1 + FS-D3")
print(f"  working set: {n} columns (608 - 1 - 33)")
assert n == 574
X = np.apply_along_axis(rankdata, 0, feat.to_numpy(float))
X = (X - X.mean(0)) / X.std(0)
C = np.abs(X.T @ X / X.shape[0])
np.fill_diagonal(C, 0.0)
iu = np.triu_indices(n, k=1)
print(f"  consistency with FS-D3: max pairwise |rho| = {C[iu].max():.4f} (< 0.99)")
assert C[iu].max() < 0.99
THR = 0.95
print(f"  pairs at |rho| >= {THR}: {(C[iu] >= THR).sum()}")

section("2] GREEDY SCAN IN THE DECLARED PRIORITY ORDER")


def keep_key(c):
    return (0 if c in PROTECT else 1,
            -int(nuni[c]),
            1 if pathB_re.match(c) else 0,
            grid_dist(c),
            suffix_rank(c),
            c)


order = sorted(range(n), key=lambda i: keep_key(cols[i]))
kept, drops = [], []
for i in order:
    partners = [(C[i, j], j) for j in kept if C[i, j] >= THR]
    if partners:
        r, j = max(partners)
        drops.append((cols[i], cols[j], r))
    else:
        kept.append(i)
print(f"  scanned {n} columns; kept {len(kept)}, dropped {len(drops)}")
print(f"\n  every dropped column with its kept partner:")
for c, k, r in sorted(drops):
    print(f"    drop {c:<28} kept twin {k:<28} |rho|={r:.3f}")

section("3] RESULT")
drop_names = sorted(c for c, _, _ in drops)
print(f"  working set after FS-D4: {n} - {len(drops)} = {n - len(drops)} columns")
rhos = [r for _, _, r in drops]
print(f"  dropped-vs-kept |rho|: min={min(rhos):.3f} median={np.median(rhos):.3f} "
      f"max={max(rhos):.3f}")
print(f"  dropped, by family: "
      f"{dict(Counter(fam(c) for c in drop_names))}")
kept_names = [cols[i] for i in kept]
print(f"  remaining, by family: "
      f"{dict(Counter(fam(c) for c in kept_names))}")
for c in PROTECT:
    print(f"  protected column still present: {c}: {c in kept_names}")
Xr = feat[kept_names].to_numpy(float)
Rr = np.apply_along_axis(rankdata, 0, Xr)
Rr = (Rr - Rr.mean(0)) / Rr.std(0)
Cr = np.abs(Rr.T @ Rr / Rr.shape[0])
np.fill_diagonal(Cr, 0.0)
print(f"  verification: max pairwise |rho| among kept = {Cr.max():.4f} "
      f"(must be < {THR})")
assert Cr.max() < THR

keep_in_table_order = [c for c in cols if c in set(kept_names)]
assert len(keep_in_table_order) == len(kept_names)
KEEP_OUT = ROOT / "analysis" / "feature_keeplist_512.csv"
pd.DataFrame({"feature": keep_in_table_order}).to_csv(KEEP_OUT, index=False)
print(f"  keep-list materialised (FS-D5): {KEEP_OUT.relative_to(ROOT)} "
      f"({len(keep_in_table_order)} rows, features.csv column order)")

sys.stdout = sys.__stdout__
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                      capture_output=True, text=True).stdout.strip()
SNAP.write_text(
    "# dedup_095.md -- verbatim stdout snapshot\n\n"
    "**Do not hand-edit.** To update, re-run the producing script and let it "
    "overwrite this file.\n\n"
    "- Producing script: `analysis/70c_dedup_095_greedy.py`\n"
    f"- Repository HEAD when this snapshot was generated: `{head}`\n"
    "- Reproduce with: `.venv/bin/python analysis/70c_dedup_095_greedy.py`\n\n"
    "```text\n" + buf.getvalue() + "\n```\n",
    encoding="utf-8")
print(f"\nsnapshot written: {SNAP.relative_to(ROOT)}")
