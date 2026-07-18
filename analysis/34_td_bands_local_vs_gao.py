"""
Test the claim: "PARENT-RATED TOTAL DIFFICULTIES BANDS (mainland China):
Bands were set by THIS SAMPLE'S OWN distribution -> normal 0-16 (81%),
borderline 17-18 (8%), abnormal 19-40 (11%)."

The exact numbers 0-16/17-18/19-40 & 81/8/11% are Gao et al. 2013 (PMC4054577,
N=22,108, 8 provinces) Table 6 -- an EXTERNAL national norm.

Question here: does the LOCAL dataset's OWN distribution produce those bands?
If not, "this sample's own distribution" can only mean Gao's sample, not ours.

Complications in the local data (see SDQ_FINDINGS.md / CODEBOOK.md):
  - values are 1-indexed {1,2,3}; standard SDQ score = value - 1 (0/1/2)
  - SDQ19 (a peer item) is ABSENT -> only 19 of the 20 difficulty items
  - reverse items {7,11,14,21,25} stored UN-flipped -> flip with (2 - std)
  - S32 SDQ8 == 13 is an illegal value -> treat as missing
"""
import numpy as np, pandas as pd

CSV = "/Users/shiyu/Projects/adhd-segmentation/data/Demographic and mental health data.csv"

EMO  = [3, 8, 13, 16, 24]
CON  = [5, 7, 12, 18, 22]
HYP  = [2, 10, 15, 21, 25]
PEER = [6, 11, 14, 19, 23]          # 19 absent
DIFF = EMO + CON + HYP + PEER        # 20 difficulty items (standard)
REV  = {7, 11, 14, 21, 25}

df = pd.read_csv(CSV, dtype=str, encoding="utf-8-sig")
df.columns = [c.strip() for c in df.columns]

present = [i for i in DIFF if f"SDQ{i}" in df.columns]
missing = [i for i in DIFF if f"SDQ{i}" not in df.columns]
print(f"rows in CSV                : {len(df)}")
print(f"difficulty items present   : {len(present)}/20   missing = {missing}")

# standard 0-2 score, reverse-corrected
std = pd.DataFrame(index=df.index)
for i in present:
    c = f"SDQ{i}"
    x = pd.to_numeric(df[c], errors="coerce")
    x = x.where(x.isin([1, 2, 3]))               # 1/2/3 valid; else NaN (kills S32 SDQ8=13)
    s = x - 1                                     # -> 0/1/2
    if i in REV:
        s = 2 - s                                 # flip
    std[c] = s

# require a complete SDQ set (all 19 present items answered) for a valid total
complete = std.dropna(how="any")
print(f"subjects with complete SDQ : {len(complete)}")

td19 = complete.sum(axis=1)                       # sum of 19 items, range 0-38
td_prorated = td19 * 20.0 / 19.0                  # standard proration for the 1 missing item -> 0-40

print("\n--- LOCAL sample's OWN Total Difficulties (standard scoring, reverse-corrected) ---")
for name, s in [("sum of 19 items (0-38)", td19), ("prorated to 20 items (0-40)", td_prorated)]:
    p80, p90 = np.percentile(s, [80, 90])
    print(f"\n{name}:  n={len(s)}  min={s.min():.1f}  median={s.median():.1f}  "
          f"max={s.max():.1f}  mean={s.mean():.2f}")
    print(f"    OWN 80th pct = {p80:.1f}   OWN 90th pct = {p90:.1f}")
    # bands implied by THIS sample's own 80/90 percentiles
    norm = (s <= p80).mean() * 100
    bord = ((s > p80) & (s <= p90)).mean() * 100
    abn  = (s > p90).mean() * 100
    print(f"    implied bands from OWN distribution: "
          f"normal<= {p80:.0f} ({norm:.0f}%) | borderline {p80:.0f}-{p90:.0f} ({bord:.0f}%) | "
          f"abnormal > {p90:.0f} ({abn:.0f}%)")

print("\n--- Apply GAO's external bands (0-16 / 17-18 / 19-40) to the LOCAL prorated score ---")
g_norm = (td_prorated <= 16).mean() * 100
g_bord = ((td_prorated >= 17) & (td_prorated <= 18)).mean() * 100
g_abn  = (td_prorated >= 19).mean() * 100
print(f"    normal 0-16 = {g_norm:.0f}%   borderline 17-18 = {g_bord:.0f}%   abnormal 19-40 = {g_abn:.0f}%")
print(f"    (Gao's OWN national sample: 81% / 8% / 11%)")

print("\n--- If one naively summed the AS-STORED 1-3 values over 19 items (the papers' scale) ---")
raw = pd.DataFrame({f"SDQ{i}": pd.to_numeric(df[f'SDQ{i}'], errors='coerce').where(
        lambda v: v.isin([1,2,3])) for i in present}).dropna(how="any").sum(axis=1)
print(f"    n={len(raw)}  range {raw.min():.0f}-{raw.max():.0f}  (structurally cannot be a 0-40 scale)")
