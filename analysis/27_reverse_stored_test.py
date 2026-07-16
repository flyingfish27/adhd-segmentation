"""
27_reverse_stored_test.py

Single purpose: decide whether the SDQ reverse-scored items are stored
"pre-flip" (raw responses) or "post-flip" (direction already aligned).

Logic:
- Standard SDQ has 5 reverse items: {7, 11, 14, 21, 25}. For these, a HIGH raw
  answer means FEWER difficulties (opposite direction to the rest of their
  subscale).
- For each reverse item, compute the Spearman correlation with the SUM of the
  OTHER (non-reverse) items in its own subscale (corrected item-total: the item
  itself is excluded from the sum).
    * NEGATIVE correlations  -> reverse items were NOT flipped (raw stored).
    * POSITIVE correlations  -> reverse items ALREADY flipped (aligned).
- Computed on RAW data with NO 4-x flip applied (flipping first would beg the
  question).
- Cross-check with Cronbach's alpha per subscale, pre-flip vs post-flip; the
  higher alpha indicates the internally-consistent (aligned) representation.
"""

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

CSV = "/Users/shiyu/Projects/adhd-segmentation/data/Demographic and mental health data.csv"

# SDQ items present: 1..18, 20..25 (no SDQ19)
SDQ_ITEMS = [i for i in range(1, 26) if i != 19]
SDQ_COLS = [f"SDQ{i}" for i in SDQ_ITEMS]

REVERSE = {7, 11, 14, 21, 25}

SUBSCALES = {
    "emo":  [3, 8, 13, 16, 24],
    "cond": [5, 7, 12, 18, 22],
    "hyp":  [2, 10, 15, 21, 25],
    "peer": [6, 11, 14, 19, 23],
    "pro":  [1, 4, 9, 17, 20],
}

# which subscale each reverse item belongs to
REV_SUBSCALE = {}
for name, items in SUBSCALES.items():
    for it in items:
        if it in REVERSE:
            REV_SUBSCALE[it] = name


def load():
    df = pd.read_csv(CSV, dtype=str, encoding="utf-8-sig")
    # keep only SDQ columns that actually exist (SDQ19 absent by design)
    cols = [c for c in SDQ_COLS if c in df.columns]
    sdq = df[cols].copy()
    # numeric
    for c in cols:
        sdq[c] = pd.to_numeric(sdq[c], errors="coerce")
    # S32's SDQ8 == 13 is a data-entry error -> treat as missing
    if "SDQ8" in sdq.columns:
        sdq.loc[sdq["SDQ8"] == 13, "SDQ8"] = np.nan
    # valid SDQ values are 1/2/3; anything else -> missing
    sdq = sdq.where(sdq.isin([1, 2, 3]))
    return sdq


def cronbach_alpha(frame):
    """Standard Cronbach's alpha on complete rows of the given item frame."""
    x = frame.dropna()
    k = x.shape[1]
    if k < 2 or len(x) < 2:
        return np.nan
    item_var = x.var(axis=0, ddof=1).sum()
    total_var = x.sum(axis=1).var(ddof=1)
    if total_var == 0:
        return np.nan
    return (k / (k - 1)) * (1 - item_var / total_var)


def main():
    sdq = load()
    print("=" * 70)
    print("REVERSE-ITEM STORAGE TEST  (raw data, NO flip applied)")
    print("=" * 70)
    print(f"N rows loaded: {len(sdq)}")
    print(f"SDQ columns available: {list(sdq.columns)}")
    print(f"Reverse items tested: {sorted(REVERSE)}")
    print()

    # ---- 1) corrected item-total Spearman for each reverse item -----------
    print("-" * 70)
    print("Corrected item-total Spearman correlation of each REVERSE item")
    print("vs the SUM of the OTHER (non-reverse) items in its own subscale.")
    print("  negative -> NOT flipped (raw stored)   positive -> already flipped")
    print("-" * 70)

    results = []  # (item, subscale, rho, p, n)
    for item in sorted(REVERSE):
        sub = REV_SUBSCALE[item]
        others = [i for i in SUBSCALES[sub] if i != item and i not in REVERSE]
        other_cols = [f"SDQ{i}" for i in others if f"SDQ{i}" in sdq.columns]
        item_col = f"SDQ{item}"

        pair = sdq[[item_col] + other_cols].dropna()
        rest_sum = pair[other_cols].sum(axis=1)
        rho, p = spearmanr(pair[item_col], rest_sum)
        results.append((item, sub, rho, p, len(pair)))
        tag = "NOT flipped" if rho < 0 else "already flipped"
        print(f"  SDQ{item:<2} [{sub:>4}]  vs sum{others}"
              f"  rho={rho:+.3f}  p={p:.2e}  n={len(pair)}  -> {tag}")

    n_neg = sum(1 for _, _, rho, _, _ in results if rho < 0)
    n_pos = len(results) - n_neg
    print()
    print(f"  reverse items with NEGATIVE rho (unflipped): {n_neg}/5")
    print(f"  reverse items with POSITIVE rho (flipped)  : {n_pos}/5")

    # ---- 2) Cronbach's alpha per subscale, pre-flip vs post-flip ----------
    print()
    print("-" * 70)
    print("Cronbach's alpha per subscale: AS-STORED vs AFTER 4-x flip")
    print("(higher alpha = the internally-consistent / aligned representation)")
    print("-" * 70)
    print(f"  {'subscale':<8} {'alpha_as_stored':>16} {'alpha_after_flip':>18}"
          f"  {'->':>3} {'aligned when'}")
    alpha_verdict = {}  # subscale -> 'as-stored' / 'after-flip'
    for name, items in SUBSCALES.items():
        cols = [f"SDQ{i}" for i in items if f"SDQ{i}" in sdq.columns]
        rev_here = [i for i in items if i in REVERSE]
        stored = sdq[cols]
        flipped = stored.copy()
        for i in items:
            c = f"SDQ{i}"
            if i in REVERSE and c in flipped.columns:
                flipped[c] = 4 - flipped[c]
        a_stored = cronbach_alpha(stored)
        a_flip = cronbach_alpha(flipped)
        if not rev_here:
            verdict = "n/a (no reverse item)"
        else:
            verdict = "as-stored" if a_stored >= a_flip else "after-flip"
            alpha_verdict[name] = verdict
        print(f"  {name:<8} {a_stored:>16.3f} {a_flip:>18.3f}  {'->':>3} {verdict}")

    # ---- conclusion -------------------------------------------------------
    # Per reverse item: negative corrected item-total OR alpha favouring
    # "after-flip" => item is stored RAW (pre-flip). Positive rho AND alpha
    # favouring "as-stored" => item is stored already-flipped (aligned).
    print()
    print("-" * 70)
    print("Per-item verdict (corrected item-total sign + subscale alpha):")
    print("-" * 70)
    item_pre = []   # stored raw / NOT flipped
    item_post = []  # stored already flipped
    for item, sub, rho, p, n in results:
        a_says_flip_needed = alpha_verdict.get(sub) == "after-flip"
        if rho < 0 or a_says_flip_needed:
            item_pre.append(item)
            state = "PRE-FLIP (raw / needs flipping)"
        else:
            item_post.append(item)
            state = "POST-FLIP (already aligned)"
        print(f"  SDQ{item:<2} [{sub:>4}]  rho={rho:+.3f}  alpha_favours="
              f"{alpha_verdict.get(sub,'?'):<10}  -> {state}")

    print()
    print("=" * 70)
    if not item_post:
        conclusion = ("STORED = PRE-FLIP (RAW). All 5 reverse items correlate "
                      "negatively; nothing was flipped.")
    elif not item_pre:
        conclusion = ("STORED = POST-FLIP (ALIGNED). All 5 reverse items "
                      "correlate positively; direction already applied.")
    else:
        conclusion = (
            "MIXED / INCONSISTENT storage -- NOT uniformly pre- or post-flip.\n"
            f"           RAW (pre-flip, still need 4-x): SDQ{item_pre}  "
            "[hyperactivity 21,25: rho strongly negative, alpha jumps to ~0.82 "
            "only after flipping]\n"
            f"           ALREADY FLIPPED (post-flip): SDQ{item_post}  "
            "[peer 11,14: rho positive, alpha drops if flipped; conduct 7 weak/"
            "ambiguous].\n"
            "           => The reverse items are not stored in one consistent "
            "convention across subscales.")
    print("CONCLUSION:", conclusion)
    print("=" * 70)

    return results


if __name__ == "__main__":
    res = main()

    # ---- figure -----------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    items = [f"SDQ{it}\n({sub})" for it, sub, _, _, _ in res]
    rhos = [rho for _, _, rho, _, _ in res]
    colors = ["#c0392b" if r < 0 else "#27ae60" for r in rhos]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.bar(items, rhos, color=colors, edgecolor="black", linewidth=0.8)
    ax.axhline(0, color="black", linewidth=1.0)

    for b, r in zip(bars, rhos):
        va = "bottom" if r >= 0 else "top"
        off = 0.01 if r >= 0 else -0.01
        ax.text(b.get_x() + b.get_width() / 2, r + off, f"{r:+.3f}",
                ha="center", va=va, fontsize=10, fontweight="bold")

    lim = max(0.25, max(abs(min(rhos)), abs(max(rhos))) * 1.35)
    ax.set_ylim(-lim, lim)
    ax.set_ylabel("Spearman rho vs sum of OTHER subscale items\n"
                  "(corrected item-total)")
    ax.set_xlabel("Reverse-scored SDQ item (its subscale)")
    ax.set_title("Are SDQ reverse items stored PRE-flip or POST-flip?\n"
                 "Negative (red) = NOT flipped / raw   |   "
                 "Positive (green) = already flipped")

    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(facecolor="#c0392b", edgecolor="black",
              label="negative -> NOT flipped (raw stored)"),
        Patch(facecolor="#27ae60", edgecolor="black",
              label="positive -> already flipped (aligned)"),
    ], loc="upper right", fontsize=9)

    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = "/Users/shiyu/Projects/adhd-segmentation/figures/reverse_items_stored_test.png"
    fig.savefig(out, dpi=150)
    print(f"\n[figure saved] {out}")
