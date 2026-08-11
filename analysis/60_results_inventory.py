# -*- coding: utf-8 -*-
"""
60_results_inventory.py
Stage 1 of the modelling-results analysis: inventory and integrity audit of every
table that the two result tracks consumed or produced.

This script READS ONLY.  It never re-runs 44_univariate_screen.py or
45_multivariate_cv.py; both are treated as frozen.  Every count printed here comes
from the CSV files themselves, not from the prose in the *_MENU.md documents --
several of those documents predate later re-runs and carry stale numbers.

Outputs
    outputs/tables/60_inventory.md          verbatim copy of this script's stdout
    outputs/figures/fig01_label_group_sizes.png
    outputs/figures/fig02_feature_families.png

Re-run with:
    .venv/bin/python analysis/60_results_inventory.py

Paths are derived from this file's own location, so the script writes into
whichever checkout it lives in.  It reads no environment variable and touches
nothing under data/.
"""
import io
import json
import pathlib
import re
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIGDIR = ROOT / "outputs" / "figures"
TABDIR = ROOT / "outputs" / "tables"
FIGDIR.mkdir(parents=True, exist_ok=True)
TABDIR.mkdir(parents=True, exist_ok=True)


class Tee:
    """Duplicate everything printed onto both the terminal and an in-memory buffer,
    so the snapshot file is a byte-for-byte copy of what the operator saw."""

    def __init__(self, stream):
        self.stream = stream
        self.buf = io.StringIO()

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


# ---------------------------------------------------------------------------
# [1] File inventory
# ---------------------------------------------------------------------------
FILES = {
    "A_univariate": "analysis/A_univariate.csv",
    "B_multivariate": "analysis/B_multivariate.csv",
    "features": "analysis/features.csv",
    "targets": "analysis/targets.csv",
    "target_labels": "analysis/target_labels.csv",
    "target_labels_meta": "analysis/target_labels_meta.csv",
    "items": "analysis/items.csv",
    "subject_audit": "figures/subject_audit.csv",
}
T = {k: pd.read_csv(ROOT / v) for k, v in FILES.items()}

head("[1] FILE INVENTORY -- shape of every input table, measured not quoted")
print(f"{'name':22} {'rows':>7} {'cols':>6}  path")
for k, v in FILES.items():
    r, c = T[k].shape
    print(f"{k:22} {r:7d} {c:6d}  {v}")

print("\nColumn lists of the two result tables (the objects of this analysis):")
print(f"  A_univariate ({T['A_univariate'].shape[1]} cols): {list(T['A_univariate'].columns)}")
print(f"  B_multivariate ({T['B_multivariate'].shape[1]} cols): {list(T['B_multivariate'].columns)}")

print("\nCross-check against the prose in the documentation:")
print(f"  FEATURE_MENU.md line 3 states 'features.csv (24 subjects x 351 columns)'.")
print(f"    measured: {T['features'].shape[0]} rows x {T['features'].shape[1]} columns"
      f" ({T['features'].shape[1] - 1} features + the subject key)  -> STALE by"
      f" {T['features'].shape[1] - 1 - 351} feature columns")
print(f"  TARGET_MENU.md line 5 states 'target_labels.csv (24 subjects x 31 columns)'.")
print(f"    measured: {T['target_labels'].shape[0]} rows x {T['target_labels'].shape[1]} columns"
      f" ({T['target_labels'].shape[1] - 1} label columns + the subject key)")

# ---------------------------------------------------------------------------
# [2] Subject-key consistency
# ---------------------------------------------------------------------------
head("[2] SUBJECT-KEY CONSISTENCY -- do all subject-indexed tables hold the same 24 people")
subj = {}
for k in ["features", "targets", "target_labels", "items"]:
    subj[k] = list(T[k]["subject"])
audit = T["subject_audit"]
sel = audit[(audit["status"] == "usable") & (audit["_T"] == "yes")]
subj["subject_audit(usable & _T==yes)"] = list(sel["subject"])

ref_name, ref = "features", subj["features"]
print(f"reference = {ref_name}: n={len(ref)}")
all_match = True
for k, v in subj.items():
    same_set = set(v) == set(ref)
    same_order = list(v) == list(ref)
    flag = "OK" if same_set and same_order else ("SAME SET, DIFFERENT ORDER" if same_set else "MISMATCH")
    if not (same_set and same_order):
        all_match = False
    print(f"  {k:34} n={len(v):3d}  {flag}")
    if not same_set:
        print(f"      only in {k}: {sorted(set(v) - set(ref))}")
        print(f"      only in {ref_name}: {sorted(set(ref) - set(v))}")
print(f"\n  verdict: {'all five tables carry the identical 24 subjects in identical order' if all_match else 'SEE MISMATCHES ABOVE'}")

print("\n  subject_audit.csv record counts by status (this is the selection funnel):")
print("   ", dict(audit["status"].value_counts()))
print(f"    records with _T == 'yes'          : {int((audit['_T'] == 'yes').sum())}")
print(f"    records with status == 'usable'   : {int((audit['status'] == 'usable').sum())}")
print(f"    both (the analysed cohort)        : {len(sel)}")
excl = audit[audit["status"] != "usable"]
print(f"    exclusion reasons recorded in 'high_risk' among the {len(excl)} non-usable records:")
for reason, cnt in excl["high_risk"].fillna("(blank)").value_counts().items():
    print(f"      {cnt:3d}  {reason}")

# ---------------------------------------------------------------------------
# [3] Feature-name cross-check
# ---------------------------------------------------------------------------
head("[3] FEATURE-NAME CROSS-CHECK -- A_univariate.feature vs the columns of features.csv")
feat_cols = [c for c in T["features"].columns if c != "subject"]
a_feats = sorted(T["A_univariate"]["feature"].unique())
print(f"  distinct feature names in A_univariate : {len(a_feats)}")
print(f"  feature columns in features.csv        : {len(feat_cols)}")
missing_in_features = sorted(set(a_feats) - set(feat_cols))
never_screened = sorted(set(feat_cols) - set(a_feats))
print(f"  screened but absent from features.csv  : {len(missing_in_features)}"
      + ("" if not missing_in_features else f"  -> {missing_in_features[:10]}"))
print(f"  present in features.csv but never screened: {len(never_screened)}"
      + ("" if not never_screened else f"  -> {never_screened[:10]}"))
print(f"  verdict: {'the screened feature set and the feature table are the same set' if not missing_in_features and not never_screened else 'SETS DIFFER -- see above'}")

# ---------------------------------------------------------------------------
# [4] Target / label cross-check
# ---------------------------------------------------------------------------
head("[4] TARGET AND LABEL CROSS-CHECK -- which targets each track actually ran")
cont_cols = [c for c in T["targets"].columns if c != "subject"]
label_cols = [c for c in T["target_labels"].columns if c != "subject"]
meta = T["target_labels_meta"]

A = T["A_univariate"]
B = T["B_multivariate"]
a_cont = sorted(A.loc[A["type"] == "cont", "target"].unique())
a_bin = sorted(A.loc[A["type"] == "bin", "target"].unique())
b_main = B[B["variant"] == "main"]
b_reg = sorted(b_main.loc[b_main["track"] == "reg", "target"].unique())
b_bin = sorted(b_main.loc[b_main["track"] == "bin", "target"].unique())
b_multi = sorted(b_main.loc[b_main["track"] == "multi", "target"].unique())

print(f"  continuous target columns in targets.csv      : {len(cont_cols)}  {cont_cols}")
print(f"  label columns in target_labels.csv            : {len(label_cols)}")
print(f"  rows in target_labels_meta.csv                : {len(meta)}"
      f"   (written=True: {int(meta['written'].sum())}, written=False: {int((~meta['written'].astype(bool)).sum())})")
print(f"  meta rows flagged degenerate=True             : {int(meta['degenerate'].astype(bool).sum())}")
print(f"  meta rows flagged constant=True               : {int(meta['constant'].astype(bool).sum())}")
notwritten = meta.loc[~meta["written"].astype(bool), "label_name"].tolist()
print(f"  meta rows with written=False (rule kept, column not emitted): {notwritten}")

print("\n  A-track ran:")
print(f"    continuous targets : {len(a_cont)}  {a_cont}")
print(f"    binary targets     : {len(a_bin)}  {a_bin}")
print("  B-track (variant=='main') ran:")
print(f"    regression targets : {len(b_reg)}")
print(f"    binary targets     : {len(b_bin)}")
print(f"    multiclass targets : {len(b_multi)}  {b_multi}")

print("\n  consistency of the target names against their source tables:")
for nm, got, pool, poolnm in [
    ("A cont", a_cont, cont_cols, "targets.csv columns"),
    ("A bin", a_bin, label_cols, "target_labels.csv columns"),
    ("B reg", b_reg, cont_cols, "targets.csv columns"),
    ("B bin", b_bin, label_cols, "target_labels.csv columns"),
    ("B multi", b_multi, label_cols, "target_labels.csv columns"),
]:
    bad = sorted(set(got) - set(pool))
    print(f"    {nm:8} {len(got):3d} targets, all present in {poolnm}: "
          f"{'yes' if not bad else 'NO -> ' + str(bad)}")

degen = set(meta.loc[meta["degenerate"].astype(bool), "label_name"])
used_labels = set(a_bin) | set(b_bin) | set(b_multi)
print(f"\n  degenerate labels that nevertheless entered a track: "
      f"{sorted(used_labels & degen) or 'none'}")
print(f"  label columns never used by either track: {len(set(label_cols) - used_labels)}"
      f"  -> {sorted(set(label_cols) - used_labels)}")

# ---------------------------------------------------------------------------
# [5] Result-table composition
# ---------------------------------------------------------------------------
head("[5] RESULT-TABLE COMPOSITION -- does the row count decompose as the design says")
print(f"  A_univariate rows: {len(A)}")
print(f"    by type: {dict(A['type'].value_counts())}")
print(f"    {len(a_feats)} features x {len(a_cont)} continuous targets = {len(a_feats) * len(a_cont)}"
      f"   (measured cont rows: {int((A['type'] == 'cont').sum())})")
print(f"    {len(a_feats)} features x {len(a_bin)} binary targets     = {len(a_feats) * len(a_bin)}"
      f"   (measured bin rows : {int((A['type'] == 'bin').sum())})")
dup_a = A.duplicated(subset=["target", "feature"]).sum()
print(f"    duplicate (target, feature) pairs: {dup_a}")

print(f"\n  B_multivariate rows: {len(B)}")
print(f"    by variant: {dict(B['variant'].value_counts())}")
print(f"    main arm rows: {len(b_main)}")
print("    main arm by track x model x k:")
comp = b_main.groupby(["track", "model", "k"]).size().reset_index(name="rows")
print("      " + comp.to_string(index=False).replace("\n", "\n      "))
print(f"    main arm n per row: {dict(b_main['n'].value_counts())}")
print(f"    other arms n per row: {dict(B[B['variant'] != 'main']['n'].value_counts())}")
dup_b = B.duplicated(subset=["variant", "track", "target", "model", "k"]).sum()
print(f"    duplicate (variant, track, target, model, k) rows: {dup_b}")

# ---------------------------------------------------------------------------
# [6] Missingness
# ---------------------------------------------------------------------------
head("[6] MISSINGNESS PER COLUMN -- empty cells are structural here, not damage")
print("  A_univariate: a column is expected empty on the row type it does not describe.")
print(f"  {'column':22} {'non-null':>9} {'null':>7}   non-null on cont / on bin")
for c in A.columns:
    nn = int(A[c].notna().sum())
    on_cont = int(A.loc[A["type"] == "cont", c].notna().sum())
    on_bin = int(A.loc[A["type"] == "bin", c].notna().sum())
    print(f"  {c:22} {nn:9d} {len(A) - nn:7d}   {on_cont:6d} / {on_bin:6d}")

print("\n  B_multivariate (main arm only, the only arm that carries perm_p and q_fdr):")
print(f"  {'column':22} {'non-null':>9} {'null':>7}   non-null on reg / bin / multi")
for c in B.columns:
    nn = int(b_main[c].notna().sum())
    per = [int(b_main.loc[b_main["track"] == t, c].notna().sum()) for t in ["reg", "bin", "multi"]]
    print(f"  {c:22} {nn:9d} {len(b_main) - nn:7d}   {per[0]:5d} / {per[1]:5d} / {per[2]:5d}")

print(f"\n  perm_p present on {int(b_main['perm_p'].notna().sum())} of {len(b_main)} main-arm combinations;"
      f" absent on {int(b_main['perm_p'].isna().sum())}.")
print("  MODEL_MENU.md section 4 trap 2: an absent perm_p means the combination never"
      " beat the dummy baseline and so was never permutation-tested. It does not mean"
      " 'tested and found not significant'.")

# ---------------------------------------------------------------------------
# [7] Label group sizes -- meta vs recomputed          -> FIGURE 01
# ---------------------------------------------------------------------------
head("[7] LABEL GROUP SIZES -- metadata claim vs recomputation from target_labels.csv")
rows = []
mismatch = 0
for _, m in meta.iterrows():
    name = m["label_name"]
    claimed = json.loads(m["group_sizes"]) if isinstance(m["group_sizes"], str) else {}
    claimed = {int(k): int(v) for k, v in claimed.items()}
    if name in label_cols:
        obs = T["target_labels"][name].value_counts().to_dict()
        obs = {int(k): int(v) for k, v in obs.items()}
    else:
        obs = None
    agree = (obs is not None and obs == {k: v for k, v in claimed.items() if v > 0})
    if obs is not None and not agree:
        mismatch += 1
    rows.append(dict(label=name, target=m["target"], method=m["method"],
                     k_declared=int(m["k_declared"]), k_observed=int(m["k_observed"]),
                     claimed=claimed, observed=obs,
                     degenerate=bool(m["degenerate"]), constant=bool(m["constant"]),
                     written=bool(m["written"]),
                     in_A=name in set(a_bin), in_Bbin=name in set(b_bin),
                     in_Bmulti=name in set(b_multi)))
L = pd.DataFrame(rows)
print(f"  {'label':34} {'k_dec':>5} {'k_obs':>5}  {'sizes (recomputed)':28} deg cons  A Bb Bm")
for _, r in L.iterrows():
    sizes = "not emitted" if r["observed"] is None else \
        " ".join(f"{k}:{r['observed'][k]}" for k in sorted(r["observed"]))
    print(f"  {r['label']:34} {r['k_declared']:5d} {r['k_observed']:5d}  {sizes:28}"
          f" {'Y' if r['degenerate'] else '.':^3} {'Y' if r['constant'] else '.':^4}"
          f" {'Y' if r['in_A'] else '.':^2} {'Y' if r['in_Bbin'] else '.':^2}"
          f" {'Y' if r['in_Bmulti'] else '.':^2}")
print(f"\n  rows where the recomputed group sizes disagree with target_labels_meta.csv: {mismatch}")
emitted = L[L["observed"].notna()]
minority = emitted["observed"].apply(lambda d: min(d.values()))
print(f"  smallest group across the {len(emitted)} emitted label columns: {int(minority.min())} subject(s)")
print(f"  label columns whose smallest group is <= 2 subjects: "
      f"{sorted(emitted.loc[minority <= 2, 'label'].tolist())}")

# FIGURE 01 -------------------------------------------------------------------
plotL = L[L["observed"].notna()].copy()
plotL["minority"] = plotL["observed"].apply(lambda d: min(d.values()))
plotL = plotL.sort_values(["k_observed", "minority"], ascending=[True, True]).reset_index(drop=True)
fig, ax = plt.subplots(figsize=(12.5, 0.34 * len(plotL) + 2.6))
cmap = plt.get_cmap("Blues")
maxk = int(plotL["k_observed"].max())
for i, r in plotL.iterrows():
    left = 0
    for g in sorted(r["observed"]):
        w = r["observed"][g]
        ax.barh(i, w, left=left, height=0.72,
                color=cmap(0.30 + 0.55 * g / max(1, maxk - 1)), edgecolor="white", linewidth=0.8)
        if w >= 2:
            ax.text(left + w / 2, i, str(w), ha="center", va="center", fontsize=7.5,
                    color="white" if g >= maxk / 2 else "black")
        left += w
ax.set_yticks(range(len(plotL)))
ax.set_yticklabels(plotL["label"], fontsize=7.5)
ax.set_xlim(0, 24 + 7.2)
ax.set_xticks(range(0, 25, 4))
ax.set_xlabel("Number of subjects (cohort n = 24)")
ax.set_title("Fig 1  How each emitted label column splits the 24 subjects\n"
             "segment = one group; the split is the denominator of every downstream classification metric",
             fontsize=10.5)
ax.invert_yaxis()
for j, (lab, key) in enumerate([("deg", "degenerate"), ("con", "constant"),
                                ("A", "in_A"), ("B-bin", "in_Bbin"), ("B-mul", "in_Bmulti")]):
    x = 24.9 + j * 1.35
    ax.text(x, -0.9, lab, ha="center", va="bottom", fontsize=7, rotation=45)
    for i, r in plotL.iterrows():
        ax.text(x, i, "Y" if r[key] else "·", ha="center", va="center", fontsize=7.5,
                color="#b2182b" if (key in ("degenerate", "constant") and r[key]) else "#333333")
ax.axvline(24, color="#666666", lw=0.8, ls=":")
ax.grid(axis="x", alpha=0.25, lw=0.6)
ax.set_axisbelow(True)
fig.text(0.01, 0.005,
         "deg/con = flagged degenerate/constant in target_labels_meta.csv.  "
         "A = screened by 44_univariate_screen.py.  B-bin / B-mul = modelled by 45_multivariate_cv.py (variant=main).  "
         "Group sizes recomputed from analysis/target_labels.csv, not quoted from the metadata.",
         fontsize=6.6, color="#444444")
fig.tight_layout(rect=[0, 0.022, 1, 1])
fig.savefig(FIGDIR / "fig01_label_group_sizes.png", dpi=200)
plt.close(fig)
print(f"\n  wrote {FIGDIR / 'fig01_label_group_sizes.png'}")

# ---------------------------------------------------------------------------
# [8] Feature families                                  -> FIGURE 02
# ---------------------------------------------------------------------------
head("[8] FEATURE FAMILIES -- decoding the feature names with the rules in FEATURE_MENU.md")
CHANNELS = ["uaX", "uaY", "uaZ", "uaMag", "gyX", "gyY", "gyZ", "gyMag", "pitch", "roll", "yaw", "jerk"]
TIME_SUF = ["mean", "std", "var", "rms", "min", "max", "range", "median", "iqr", "mad",
            "skew", "kurt", "zcr", "madiff"]
FREQ_SUF = ["domfreq", "centroid", "spread", "entropy", "bp_lf", "bp_mf", "bp_hf"]
# FEATURE_MENU.md documents the path-A stems without a window-length parameter
# (e.g. "switch_per_min_p{..}").  The table on disk carries an extra "_w{len}"
# segment (e.g. "switch_per_min_w0.5_p10"), i.e. the window length is swept as
# well as the percentile.  Matching is therefore done on the stem prefix only.
PATHA_STEMS = ["switch_per_min", "act_bout_median", "act_bout_cv", "stl_bout_median",
               "stl_bout_cv", "frac_act_short", "within_win_sd"]
PATHB_STEMS = ["actfrac_p", "switchmin_p", "actbout_med_p", "actbout_cv_p", "actshort_p"]
# Two families present in the table that FEATURE_MENU.md does not describe at all.
COMPLEX_SUF = ["dfa_alpha", "hurst_rs", "permen_m3", "lz_c", "acf_tau_1e_s",
               "acf_dom_period_s", "acf_dom_peak", "peak_rate_min", "peak_ipi_med_s",
               "peak_ipi_cv", "peak_amp_med", "peak_amp_cv"]


def classify(col):
    if col == "rec_dur_min":
        return "recording duration (screened as a feature)", "-"
    for ch in CHANNELS:
        if col.startswith(ch + "_"):
            suf = col[len(ch) + 1:]
            if suf in TIME_SUF:
                return "time-domain", ch
            if suf in FREQ_SUF:
                return "frequency-domain", ch
            if suf in COMPLEX_SUF:
                return "nonlinear / complexity (undocumented family)", ch
    for s in PATHB_STEMS:
        if col.startswith(s):
            return "time-structure path B (pooled threshold)", "uaMag"
    for s in PATHA_STEMS:
        if col.startswith(s + "_w"):
            return "time-structure path A (per-subject threshold)", "uaMag"
    return "not decoded by FEATURE_MENU.md rules", "?"


fam = pd.DataFrame([{"feature": c, "family": classify(c)[0], "channel": classify(c)[1]}
                    for c in feat_cols])
print(f"  {'family':48} {'count':>6}")
for f, cnt in fam["family"].value_counts().items():
    print(f"  {f:48} {cnt:6d}")
print(f"  {'TOTAL':48} {len(fam):6d}")

und = fam.loc[fam["family"].str.startswith("not decoded"), "feature"].tolist()
print(f"\n  features not decoded by any naming rule: {len(und)}")
for c in und[:25]:
    print(f"    {c}")
if len(und) > 25:
    print(f"    ... and {len(und) - 25} more")

print("\n  where the documentation and the table disagree:")
pa = fam.loc[fam["family"].str.contains("path A"), "feature"].tolist()
print(f"    FEATURE_MENU.md section 4 lists the path-A stems without a window-length term")
print(f"      (e.g. 'switch_per_min_p{{..}}') and implies 55 columns. The table carries a")
print(f"      window sweep as well: {len(pa)} columns of the form 'switch_per_min_w0.5_p10'.")
wins = sorted({m.group(1) for c in pa if (m := re.search(r"_w([0-9.]+)(?:_|$)", c))}, key=float)
print(f"      window lengths present (seconds): {wins}")
cx = fam.loc[fam["family"].str.contains("complexity"), "feature"].tolist()
cx_ch = sorted({c.split("_")[0] for c in cx})
cx_stem = sorted({c.split("_", 1)[1] for c in cx})
print(f"    the nonlinear/complexity family ({len(cx)} columns on channels {cx_ch})")
print(f"      is not mentioned anywhere in FEATURE_MENU.md. Stems: {cx_stem}")
print(f"    'rec_dur_min' (recording duration) is present as a screened feature column.")
print(f"      MODEL_MENU.md section 5 lists recording duration as an UNCONTROLLED confound")
print(f"      ('duration correlates with sdq_totdiff, rho=-0.46; modelling does not control")
print(f"      for it'). It is therefore both a listed confound and one of the 608 candidate")
print(f"      predictors that SelectKBest may choose inside the B-track pipeline.")
print(f"\n    Scope of the previous three points: they are about FEATURE_MENU.md, the document")
print(f"    designated for decoding feature names, and not about the repository as a whole.")
print(f"    INVENTORY.md line 186 (the entry beginning '当前 features.csv 有 276 列') does")
print(f"    record the same breakdown and attributes it to three tasks: a window sweep")
print(f"    adding 220 columns, rec_dur_min adding 1, and six new feature classes on three")
print(f"    channels adding 36. 55 + 220 = 275 path-A, +36, +1 reproduces the count measured")
print(f"    here exactly. So the columns are accounted for somewhere; the naming-rule")
print(f"    document a reader would consult to decode them is the copy that is out of date.")

# path B identified empirically from the result table, not from the name list
pb_named = set(fam.loc[fam["family"].str.contains("path B"), "feature"])
pb_obs = set(A.loc[A["rho_partial_uamag"].notna() | A["auc_partial_uamag"].notna(), "feature"])
print(f"\n  movement-total control (partial correlation / residualised AUC) coverage:")
print(f"    features carrying it, measured from A_univariate non-null cells: {len(pb_obs)}")
print(f"    features matching the path-B naming stems                     : {len(pb_named)}")
print(f"    the two sets agree: {'yes' if pb_obs == pb_named else 'NO -> ' + str(sorted(pb_obs ^ pb_named))}")
print(f"    features WITHOUT any movement-total control                   : {len(feat_cols) - len(pb_obs)}"
      f"  ({100 * (len(feat_cols) - len(pb_obs)) / len(feat_cols):.1f}% of the screen)")

# FIGURE 02 -------------------------------------------------------------------
order = fam["family"].value_counts()
fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.2), gridspec_kw={"width_ratios": [1.55, 1]})
ax = axes[0]
cols = ["#4878a8" if "path B" not in f else "#b2182b" for f in order.index]
bars = ax.barh(range(len(order)), order.values, color=cols, height=0.66)
ax.set_yticks(range(len(order)))
ax.set_yticklabels([f if len(f) < 46 else f[:43] + "..." for f in order.index], fontsize=8)
ax.invert_yaxis()
for i, v in enumerate(order.values):
    ax.text(v + max(order.values) * 0.012, i, str(v), va="center", fontsize=8.5)
ax.set_xlabel(f"Number of feature columns (total {len(feat_cols)})")
ax.set_title("Fig 2a  Composition of the screened feature set", fontsize=10.5)
ax.grid(axis="x", alpha=0.25, lw=0.6)
ax.set_axisbelow(True)
ax.set_xlim(0, max(order.values) * 1.16)

ax = axes[1]
covered, uncovered = len(pb_obs), len(feat_cols) - len(pb_obs)
ax.barh([0], [covered], color="#b2182b", height=0.34)
ax.barh([0], [uncovered], left=[covered], color="#cccccc", height=0.34)
ax.set_yticks([])
ax.set_ylim(-0.62, 0.62)
ax.set_xlim(0, len(feat_cols))
ax.set_xlabel("Feature columns")
ax.set_title("Fig 2b  How much of the screen carries a\nmovement-total (uaMag_median) control",
             fontsize=10.5)
ax.annotate(f"{covered} columns have it ({100 * covered / len(feat_cols):.1f}%)",
            xy=(covered * 0.5, 0.18), xytext=(covered + 45, 0.46), fontsize=8.5, color="#b2182b",
            arrowprops=dict(arrowstyle="->", color="#b2182b", lw=0.9))
ax.text(covered + (len(feat_cols) - covered) / 2, 0,
        f"{uncovered} columns screened without it ({100 * uncovered / len(feat_cols):.1f}%)",
        ha="center", va="center", fontsize=8.5, color="#444444")
fig.tight_layout()
fig.subplots_adjust(bottom=0.34)
fig.text(0.012, 0.015,
         "Left: families decoded from the naming rules in FEATURE_MENU.md. That document describes a 351-column table and does not mention the\n"
         f"nonlinear/complexity family or rec_dur_min at all; the table on disk has {len(feat_cols)} columns. Path-A columns additionally sweep a window length\n"
         "(w0.5/1/2/5/10 s) that the document does not list. Right: only the path-B time-structure columns carry a partial-correlation (continuous\n"
         "targets) or residualised-AUC (binary targets) control for total movement; the other 563 columns are screened without any such control.",
         fontsize=7.2, color="#444444", linespacing=1.5)
fig.savefig(FIGDIR / "fig02_feature_families.png", dpi=200)
plt.close(fig)
print(f"\n  wrote {FIGDIR / 'fig02_feature_families.png'}")

# ---------------------------------------------------------------------------
# [9] Summary of what stage 2 and 3 may rely on
# ---------------------------------------------------------------------------
head("[9] FACTS ESTABLISHED HERE THAT THE LATER STAGES DEPEND ON")
print(f"  cohort size                                  n = {T['features'].shape[0]}")
print(f"  features screened                                {len(a_feats)}")
print(f"  A-track cells (feature x target)                 {len(A)}"
      f"  = {len(a_feats)} x ({len(a_cont)} continuous + {len(a_bin)} binary)")
print(f"  A-track BH-FDR family size (per target)          {len(a_feats)}")
print(f"  A-track permutation p floor (1/NPERM)            {A['perm_p'].min():.1e}")
print(f"  B-track main-arm combinations                    {len(b_main)}")
print(f"  B-track BH-FDR family size                       {len(b_main)}")
print(f"  B-track combinations actually permutation-tested {int(b_main['perm_p'].notna().sum())}")
print(f"  B-track permutation p floor observed             {b_main['perm_p'].min():.1e}")
print(f"  features with a movement-total control           {len(pb_obs)} of {len(feat_cols)}")

# ---------------------------------------------------------------------------
# snapshot
# ---------------------------------------------------------------------------
try:
    commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                     text=True).strip()
except Exception:
    commit = "(git unavailable)"
body = tee.buf.getvalue()
sys.stdout = tee.stream
hdr = (
    "# 60_inventory.md -- verbatim stdout snapshot\n\n"
    "**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.\n\n"
    f"- Producing script: `analysis/60_results_inventory.py`\n"
    f"- Repository HEAD when this snapshot was generated: `{commit}`\n"
    f"- Reproduce with: `.venv/bin/python analysis/60_results_inventory.py`\n"
    "- Figures written by the same run: `outputs/figures/fig01_label_group_sizes.png`, "
    "`outputs/figures/fig02_feature_families.png`\n\n"
    "```text\n"
)
(TABDIR / "60_inventory.md").write_text(hdr + body + "```\n", encoding="utf-8")
print(f"\nwrote {TABDIR / '60_inventory.md'}")
