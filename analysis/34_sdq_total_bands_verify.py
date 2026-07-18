#!/usr/bin/env python3
"""
34_sdq_total_bands_verify.py — Does the LOCAL sample's own SDQ Total Difficulties
distribution actually give bands 0-16 (81%) / 17-18 (8%) / 19-40 (11%) with the
80th/90th percentiles at 16/18, as the claim states?

Claim under review:
  "Bands were set by THIS SAMPLE'S OWN distribution — normal <80th pct = 0-16 (81%),
   borderline 80-90th = 17-18 (8%), abnormal >90th = 19-40 (11%)."

We compute the local sample's Total Difficulties from raw CSV and read off its
ACTUAL empirical 80th/90th percentiles + band counts. Standard SDQ 0/1/2 scoring:
data is 1-indexed (std = data-1), 4 difficulty subscales (Emotional/Conduct/
Hyperactivity/Peer = 20 items), reverse items {7,11,14,21,25} flipped (3-data on
0-2 std). NOTE: SDQ19 (a peer difficulty item) is MISSING in this dataset, so a
clean 0-40 Total requires proration.
"""
import os, numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV  = os.path.join(ROOT, "data", "Demographic and mental health data.csv")
df   = pd.read_csv(CSV, encoding="utf-8-sig", dtype=str)
df.columns = [c.strip() for c in df.columns]

# ---- SDQ subscales (CODEBOOK §2.1). * = reverse. SDQ19 (peer) MISSING in data.
EMO  = [3, 8, 13, 16, 24]
CON  = [5, 7, 12, 18, 22]        # 7 reverse
HYP  = [2, 10, 15, 21, 25]       # 21,25 reverse
PEER = [6, 11, 14, 19, 23]       # 11,14 reverse ; 19 MISSING
REV  = {7, 11, 14, 21, 25}
DIFF_ITEMS = EMO + CON + HYP + PEER          # 20 standard difficulty items
present = [i for i in DIFF_ITEMS if f"SDQ{i}" in df.columns]
missing = [i for i in DIFF_ITEMS if f"SDQ{i}" not in df.columns]

print(f"CSV rows (subjects): {len(df)}")
print(f"Difficulty items expected: 20 ; present: {len(present)} ; MISSING: {missing}")

def std_item(col_series, item):
    """standard 0-2 score: std = data-1 ; reverse -> 3-data. Non-{1,2,3} -> NaN."""
    x = pd.to_numeric(col_series, errors="coerce")
    x = x.where(x.isin([1, 2, 3]))          # drop S32/SDQ8=13 style illegals
    return (3 - x) if item in REV else (x - 1)

std = pd.DataFrame({f"SDQ{i}": std_item(df[f"SDQ{i}"], i) for i in present})

# subjects with ALL present difficulty items answered (19 items, peer missing 19)
complete = std.notna().all(axis=1)
print(f"Subjects with all {len(present)} present difficulty items: {int(complete.sum())}")

sub = std[complete]

# --- (A) raw 19-item sum (peer down one item; max = 19*2 = 38)
tot19 = sub.sum(axis=1)

# --- (B) prorate to 20 items so it lives on the real 0-40 Total scale
tot20 = tot19 * (20.0 / 19.0)

def report(name, s):
    s = s.dropna()
    p80, p90 = np.percentile(s, [80, 90], method="linear")
    print(f"\n--- {name} (n={len(s)}) ---")
    print(f"  min={s.min():.1f} max={s.max():.1f} mean={s.mean():.2f} median={s.median():.1f}")
    print(f"  ACTUAL 80th pct = {p80:.2f} | 90th pct = {p90:.2f}")
    # Apply the CLAIM's fixed cutpoints (normal 0-16, borderline 17-18, abnormal >=19)
    n_norm = int((s <= 16).sum()); n_bord = int(((s >= 17) & (s <= 18)).sum()); n_abn = int((s >= 19).sum())
    tot = len(s)
    print(f"  Using CLAIM's fixed cuts 0-16 / 17-18 / 19-40 on THIS sample:")
    print(f"    normal 0-16   : {n_norm:3d}  ({100*n_norm/tot:.0f}%)   [claim says 81%]")
    print(f"    borderline 17-18: {n_bord:3d}  ({100*n_bord/tot:.0f}%)   [claim says 8%]")
    print(f"    abnormal 19-40: {n_abn:3d}  ({100*n_abn/tot:.0f}%)   [claim says 11%]")

report("(A) raw 19-item Total (max 38, peer missing item19)", tot19)
report("(B) prorated to 20 items -> 0-40 scale", tot20)

# also: where would THIS sample's own 80/90 pct actually place the abnormal cut?
for name, s in [("A-19item", tot19.dropna()), ("B-prorated40", tot20.dropna())]:
    p80, p90 = np.percentile(s, [80, 90], method="linear")
    n_abn = int((s > p90).sum())
    print(f"\n[{name}] this sample's OWN >90th-pct abnormal cut = {p90:.1f} "
          f"(claim asserts 90th pct = 18, abnormal starts 19)")
