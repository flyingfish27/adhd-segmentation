# -*- coding: utf-8 -*-
"""
63_partial_vs_plain_diff.py
Results analysis: how far does partialling out total movement (uamag) move the
univariate statistics already stored in analysis/A_univariate.csv?

Reads analysis/A_univariate.csv (produced by 44_univariate_screen.py) and nothing
else.  It re-runs no screen and fits no model: both the plain and the partial
columns are read straight out of that file and subtracted.

Only the 450 cells where a partial column is non-NaN take part.  Those are the
45 "path B" features x 10 continuous targets for rho, and the same 45 features x
10 __qbin targets for AUC; the remaining 563 features have no partial column by
construction (see analysis/MODEL_MENU.md).

Figure layout (2 rows x 2 columns):
    row 1 = rho, row 2 = AUC;
    left  = all 450 pairs ranked by |difference| (x-axis is rank, because 450
            feature names cannot be printed side by side);
    right = the top 30 pairs with full feature and target names.

Outputs
    outputs/figures/fig16_partial_vs_plain_absdiff.png
    outputs/tables/63_partial_vs_plain_diff.md

Re-run with:
    .venv/bin/python analysis/63_partial_vs_plain_diff.py
"""
import io
import pathlib
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIGDIR = ROOT / "outputs" / "figures"
TABDIR = ROOT / "outputs" / "tables"
FIGDIR.mkdir(parents=True, exist_ok=True)
TABDIR.mkdir(parents=True, exist_ok=True)

TOP_N = 30
BLUE = "#4269D0"
INK = "#333333"
MUTED = "#777777"
GRID = "#E3E3E3"


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

A = pd.read_csv(ROOT / "analysis/A_univariate.csv")

METRICS = [
    ("rho", "rho_partial_uamag", "|rho_partial_uamag - rho|", "cont"),
    ("auc", "auc_partial_uamag", "|auc_partial_uamag - auc|", "bin"),
]


def paired(base, part):
    """The cells where the partial column exists, with the signed and absolute shift."""
    sub = A[A[part].notna()].copy()
    sub["diff"] = sub[part] - sub[base]
    sub["absdiff"] = sub["diff"].abs()
    return sub.sort_values("absdiff", ascending=False).reset_index(drop=True)


print("\n" + "=" * 78)
print("[1] HOW MANY CELLS HAVE BOTH A PLAIN AND A PARTIAL VALUE")
print("=" * 78)
print(f"  analysis/A_univariate.csv holds {len(A):,} rows in total.")
for base, part, label, kind in METRICS:
    sub = paired(base, part)
    print(f"\n  {part} (type={kind}):")
    print(f"    non-NaN:        {len(sub):>6,}")
    print(f"    NaN:            {len(A) - len(sub):>6,}")
    print(f"    features:       {sub['feature'].nunique():>6}")
    print(f"    targets:        {sub['target'].nunique():>6}  "
          f"({sub['feature'].nunique()} x {sub['target'].nunique()} = {len(sub)})")

print("\n" + "=" * 78)
print("[2] RANGE OF THE SHIFT")
print("=" * 78)
print("  Signed shift is partial minus plain. A negative value means partialling")
print("  out total movement lowered the statistic.")
print(f"\n  {'comparison':<34} {'min':>10} {'max':>10} {'median':>10} "
      f"{'|min|':>10} {'|max|':>10}")
for base, part, label, kind in METRICS:
    d = paired(base, part)["diff"]
    print(f"  {label:<34} {d.min():>10.4f} {d.max():>10.4f} {d.median():>10.4f} "
          f"{d.abs().min():>10.4f} {d.abs().max():>10.4f}")

print("\n" + "=" * 78)
print(f"[3] THE {TOP_N} LARGEST SHIFTS PER COMPARISON")
print("=" * 78)
for base, part, label, kind in METRICS:
    sub = paired(base, part)
    print(f"\n  {label} -- top {TOP_N} of {len(sub)} cells")
    print(sub[["feature", "target", base, part, "diff", "absdiff"]]
          .head(TOP_N).to_string(index=False))

print("\n" + "=" * 78)
print("[4] FIGURE")
print("=" * 78)

fig, axes = plt.subplots(
    2, 2, figsize=(15, 12), gridspec_kw={"width_ratios": [1.15, 1]}
)
fig.subplots_adjust(hspace=0.35, wspace=0.32, left=0.06, right=0.97,
                    top=0.93, bottom=0.06)

for row, (base, part, label, kind) in enumerate(METRICS):
    sub = paired(base, part)
    n = len(sub)

    # left: every cell, ranked
    ax = axes[row][0]
    ax.bar(range(1, n + 1), sub["absdiff"], width=1.0, color=BLUE, linewidth=0)
    ax.set_title(f"{label} -- all {n} feature x target cells, sorted descending",
                 fontsize=11, color=INK, loc="left")
    ax.set_xlabel(f"rank (1-{n})", fontsize=9, color=MUTED)
    ax.set_ylabel("|difference|", fontsize=9, color=MUTED)
    ax.set_xlim(0, n + 1)
    ax.grid(axis="y", color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.annotate(f"max = {sub['absdiff'].iloc[0]:.4f}",
                xy=(1, sub["absdiff"].iloc[0]),
                xytext=(n * 0.05, sub["absdiff"].iloc[0] * 0.97),
                fontsize=8, color=INK, va="top")

    # right: the top N, named
    ax = axes[row][1]
    top = sub.head(TOP_N).iloc[::-1]     # reversed so the largest bar sits on top
    names = [f"{f}  ({t})" for f, t in zip(top["feature"], top["target"])]
    ax.barh(range(len(top)), top["absdiff"], height=0.72, color=BLUE, linewidth=0)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(names, fontsize=6.5, color=INK)
    ax.set_title(f"top {TOP_N} cells", fontsize=11, color=INK, loc="left")
    ax.set_xlabel("|difference|", fontsize=9, color=MUTED)
    ax.grid(axis="x", color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.margins(y=0.01)

fig.suptitle("A_univariate.csv: absolute difference between the partial (uamag) "
             "and plain columns",
             fontsize=13, color=INK, x=0.06, ha="left")
fig.savefig(FIGDIR / "fig16_partial_vs_plain_absdiff.png", dpi=200)
plt.close(fig)
print(f"  wrote {FIGDIR / 'fig16_partial_vs_plain_absdiff.png'}")

# ---------------------------------------------------------------------------
# snapshot
# ---------------------------------------------------------------------------
try:
    commit = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
except Exception:
    commit = "(git unavailable)"
body = tee.buf.getvalue()
sys.stdout = tee.stream
hdr = (
    "# 63_partial_vs_plain_diff.md -- verbatim stdout snapshot\n\n"
    "**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.\n\n"
    "- Producing script: `analysis/63_partial_vs_plain_diff.py`\n"
    f"- Repository HEAD when this snapshot was generated: `{commit}`\n"
    "- Reproduce with: `.venv/bin/python analysis/63_partial_vs_plain_diff.py`\n"
    "- Reads `analysis/A_univariate.csv` only. Nothing is refitted: both columns of\n"
    "  every comparison are read from that file and subtracted.\n\n"
    "```text\n"
)
(TABDIR / "63_partial_vs_plain_diff.md").write_text(hdr + body + "```\n", encoding="utf-8")
print(f"\nwrote {TABDIR / '63_partial_vs_plain_diff.md'}")
