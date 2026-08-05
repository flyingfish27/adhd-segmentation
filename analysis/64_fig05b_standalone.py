# -*- coding: utf-8 -*-
"""
64_fig05b_standalone.py
Redraws panel b of fig05_fdr_per_target.png on its own, with no other panel
beside it.

The drawing code below is copied verbatim from analysis/61_univariate_analysis.py
-- the block that starts at "ax = axB" and ends at "ax.set_xlim(right=...)"
(grep for "Fig 5b  How close each target came to surviving").  Colours, scales,
sort order, tick labels, bar heights, the q = 0.05 rule, the per-bar annotations
and the title string are unchanged.  The only differences are the figure size,
which no longer has to share a canvas, and the absence of the figure-level
footnote of fig05, which describes panel a.

The inputs F (per-target minimum q and the count of cells passing q < 0.05) are
rebuilt from analysis/A_univariate.csv exactly as 61_univariate_analysis.py
builds them: same target order (continuous targets sorted, then binary targets
sorted), same columns, then the same F.sort_values("minq").

Outputs
    outputs/figures/fig05b_standalone.png
    outputs/tables/64_fig05b_standalone.md

Re-run with:
    .venv/bin/python analysis/64_fig05b_standalone.py
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
CONT = sorted(A.loc[A["type"] == "cont", "target"].unique())
BIN = sorted(A.loc[A["type"] == "bin", "target"].unique())

# --- F, rebuilt exactly as 61_univariate_analysis.py builds it -------------
fdr_rows = []
for t in CONT + BIN:
    g = A[A["target"] == t]
    fdr_rows.append(dict(target=t, kind="cont" if t in CONT else "bin",
                         minp=g["perm_p"].min(), minq=g["q_fdr"].min(),
                         s05=int((g["q_fdr"] < 0.05).sum()), s10=int((g["q_fdr"] < 0.10).sum()),
                         raw=int((g["perm_p"] < 0.05).sum()), exp=len(g) * 0.05))
F = pd.DataFrame(fdr_rows)

# --- panel b, verbatim from 61_univariate_analysis.py ----------------------
fig, ax = plt.subplots(figsize=(6.4, 5.8))

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
# --- end verbatim block ----------------------------------------------------

fig.tight_layout()
fig.savefig(FIGDIR / "fig05b_standalone.png", dpi=200)
plt.close(fig)
print(f"wrote {FIGDIR / 'fig05b_standalone.png'}")

print("\nthe numbers drawn, in the plotted order:")
print(F2[["target", "kind", "minq", "s05"]].to_string(index=False))

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
    "# 64_fig05b_standalone.md -- verbatim stdout snapshot\n\n"
    "**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.\n\n"
    "- Producing script: `analysis/64_fig05b_standalone.py`\n"
    f"- Repository HEAD when this snapshot was generated: `{commit}`\n"
    "- Reproduce with: `.venv/bin/python analysis/64_fig05b_standalone.py`\n"
    "- Reads `analysis/A_univariate.csv` only. The drawing code is copied verbatim from\n"
    "  the panel-b block of `analysis/61_univariate_analysis.py`; nothing is recomputed.\n\n"
    "```text\n"
)
(TABDIR / "64_fig05b_standalone.md").write_text(hdr + body + "```\n", encoding="utf-8")
print(f"\nwrote {TABDIR / '64_fig05b_standalone.md'}")
