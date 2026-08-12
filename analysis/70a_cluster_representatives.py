# -*- coding: utf-8 -*-
# =============================================================================
# 70a_cluster_representatives.py -- pick one representative per redundancy
# cluster, by the user's three criteria (TASK-124 decision FS-D2, 2026-08-12)
#
# Input set: analysis/features.csv MINUS rec_dur_min (decision FS-D1 -- the
# column is ruled out of the reduction; not yet physically removed upstream).
#
# Clusters: connected components of |Spearman| >= 0.90 among the remaining
# 607 features, same construction as 70_feature_inventory.py section [5].
# NOTE these are *connected components*: membership chains transitively, so a
# large component does NOT mean every pair inside it correlates >= 0.90; each
# cluster line therefore reports its internal min/median pairwise |rho|.
#
# The three criteria (user-specified, verbatim intent):
#   C1  highest resolution: the member with the most unique values (of 24)
#   C2  central parameters: e.g. w2_p50 preferred over w0.5_p90.
#       Operationalised as grid distance to the centre: path-A
#       {metric}_w{w}_p{p} -> |idx(w)-2| + |idx(p)-4| over w in
#       (0.5,1,2,5,10), p in (10..90); within_win_sd_w{w} -> |idx(w)-2|;
#       path-B {metric}_p{p} -> |idx(p)-4|.  Members with no swept parameter
#       (channel stats, nonlinear) carry no C2 preference and stay eligible.
#   C3  explainable.  Operationalised (agent proposal, awaiting user assent)
#       via on-record interpretability caveats: path-B columns carry the R10
#       limitation (individual differences largely encode movement total);
#       acf_dom_period_s must be reported together with acf_dom_peak.  Columns
#       with a caveat lose C3; metrics differing only in parameters do not
#       differ on C3.  uaMag_median is additionally flagged as the negative
#       control (a warning about disposal, not a C3 disqualifier).
#
# For every multi-member cluster the script reports whether one column meets
# all three criteria at once, as the user asked to be told first.
#
# Read-only apart from the stdout snapshot
# analysis/probe_outputs/cluster_representatives.md.
# Reproduce with: .venv/bin/python analysis/70a_cluster_representatives.py
# =============================================================================
import io, pathlib, re, subprocess, sys
from collections import Counter

import numpy as np
import pandas as pd
from scipy.stats import rankdata

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SNAP = HERE / "probe_outputs" / "cluster_representatives.md"

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


def param_score(c):
    """grid distance to the centre; None = no swept parameter"""
    m = pathA_re.match(c)
    if m:
        return abs(W_ORDER.index(m.group(2)) - 2) + abs(int(m.group(3)) // 10 - 1 - 4)
    m = wwsd_re.match(c)
    if m:
        return abs(W_ORDER.index(m.group(1)) - 2)
    m = pathB_re.match(c)
    if m:
        return abs(int(m.group(2)) // 10 - 1 - 4)
    return None


def stem(c):
    m = pathA_re.match(c)
    if m:
        return m.group(1)
    if wwsd_re.match(c):
        return "within_win_sd"
    m = pathB_re.match(c)
    if m:
        return m.group(1) + "[pathB]"
    return c


def c3_flags(c):
    f = []
    if pathB_re.match(c):
        f.append("R10")
    if c.endswith("acf_dom_period_s"):
        f.append("acf-pair")
    return f


df = pd.read_csv(ROOT / "analysis" / "features.csv")
feat = df.drop(columns=["subject"])

section("1] INPUT SET AFTER FS-D1")
assert "rec_dur_min" in feat.columns
Xall = feat.to_numpy(float)
Rall = np.apply_along_axis(rankdata, 0, Xall)
Rall = (Rall - Rall.mean(0)) / Rall.std(0)
Call = np.abs(Rall.T @ Rall / Rall.shape[0])
np.fill_diagonal(Call, 0.0)
ri = feat.columns.get_loc("rec_dur_min")
partner = feat.columns[np.argmax(Call[ri])]
print(f"  features.csv feature columns: {feat.shape[1]}")
print(f"  dropped by FS-D1: rec_dur_min  (for the record, its strongest")
print(f"  partner among the other 607 was {partner}, |rho| = {Call[ri].max():.3f})")
feat = feat.drop(columns=["rec_dur_min"])
cols = list(feat.columns)
n = len(cols)
print(f"  working set: {n} columns")

section("2] CONNECTED COMPONENTS AT |Spearman| >= 0.90 (construction = 70 [5])")
X = feat.to_numpy(float)
R = np.apply_along_axis(rankdata, 0, X)
R = (R - R.mean(0)) / R.std(0)
C = np.abs(R.T @ R / R.shape[0])
np.fill_diagonal(C, 0.0)
THR = 0.90
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
singles = [g[0] for g in groups.values() if len(g) == 1]
print(f"  groups: {len(groups)}  =  {len(singles)} singletons + {len(multi)} clusters")
print(f"  (70 [5] measured on 608 columns: 347 = 298 + 49; the difference is"
      f" rec_dur_min itself)" if len(groups) == 346 else
      f"  NOTE: differs from 70 [5] beyond the rec_dur_min bookkeeping -- inspect")
print(f"  cluster sizes, descending: {[len(g) for g in multi]}")
print(f"  would-be column count after picking 1 per cluster: "
      f"{len(singles)} + {len(multi)} = {len(singles) + len(multi)}")

nuni = feat.nunique()

section("3] PER-CLUSTER VERDICT ON THE THREE CRITERIA")
print("  C1 = most unique values | C2 = most central parameters | C3 = no")
print("  on-record interpretability caveat.  'ALL-3' = one column wins all")
print("  three at once (as asked: reported first, conflicts called out).\n")

rows = []
details = []
for gi, g in enumerate(multi, 1):
    names = [cols[i] for i in g]
    gid = f"G{gi:02d}"
    sub = C[np.ix_(g, g)]
    iu = np.triu_indices(len(g), k=1)
    in_rho = sub[iu]
    nu = {c: int(nuni[c]) for c in names}
    sc = {c: param_score(c) for c in names}
    fl = {c: c3_flags(c) for c in names}
    c1 = {c for c in names if nu[c] == max(nu.values())}
    scored = {c: s for c, s in sc.items() if s is not None}
    if scored:
        best = min(scored.values())
        c2 = {c for c in names if sc[c] is None or sc[c] == best}
        c2_note = f"min grid dist {best}"
    else:
        c2 = set(names)
        c2_note = "no swept params -- C2 unconstraining"
    c3 = {c for c in names if not fl[c]}
    c3_all_flagged = not c3
    if c3_all_flagged:
        c3 = set(names)
    inter = c1 & c2 & c3
    comp = Counter(stem(c) for c in names)
    compstr = ", ".join(f"{k}x{v}" if v > 1 else k for k, v in comp.most_common())
    if len(inter) == 1:
        verdict = f"ALL-3: {next(iter(inter))}"
    elif len(inter) > 1:
        verdict = f"ALL-3 tie ({len(inter)}): " + ", ".join(sorted(inter))
    else:
        verdict = "CONFLICT"
    if c3_all_flagged:
        verdict += "  [every member carries an on-record caveat]"
    if "uaMag_median" in names:
        verdict += "  [contains negative control uaMag_median]"
    rows.append((gid, len(g), in_rho.min(), np.median(in_rho), compstr, verdict))
    if len(inter) != 1 or c3_all_flagged:
        det = [f"  {gid}  ({len(g)} cols; internal |rho| min {in_rho.min():.2f} "
               f"med {np.median(in_rho):.2f})  members by stem: {compstr}"]
        det.append(f"      C1 (nunique={max(nu.values())}): "
                   + ", ".join(sorted(c1)))
        det.append(f"      C2 ({c2_note}): "
                   + ", ".join(sorted(c2)[:8]) + (" ..." if len(c2) > 8 else ""))
        det.append(f"      C3 excluded: "
                   + (", ".join(f"{c}[{'+'.join(fl[c])}]" for c in sorted(names)
                                if fl[c]) or "none"))
        det.append(f"      C1&C2 = " + (", ".join(sorted(c1 & c2)) or "(empty)"))
        details.append("\n".join(det))

for gid, size, mn, md, compstr, verdict in rows:
    print(f"  {gid} size={size:>2} in|rho| min={mn:.2f} med={md:.2f}  "
          f"[{compstr}]")
    print(f"       -> {verdict}")

section("4] CLUSTERS NEEDING A CALL (no unique ALL-3, or caveats)")
if details:
    print("\n\n".join(details))
else:
    print("  none -- every cluster has a unique all-three representative")

section("5] SUMMARY")
n_all3 = sum(1 for r in rows if r[5].startswith("ALL-3:"))
n_tie = sum(1 for r in rows if r[5].startswith("ALL-3 tie"))
n_conf = sum(1 for r in rows if r[5].startswith("CONFLICT"))
print(f"  clusters with a unique all-three column: {n_all3} of {len(rows)}")
print(f"  clusters where several columns tie on all three: {n_tie}")
print(f"  clusters where no column satisfies all three: {n_conf}")

section("6] FULL MEMBERSHIP (for the record)")
for gi, g in enumerate(multi, 1):
    names = sorted(cols[i] for i in g)
    print(f"  G{gi:02d} ({len(g)}): " + ", ".join(names))

sys.stdout = sys.__stdout__
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                      capture_output=True, text=True).stdout.strip()
SNAP.write_text(
    "# cluster_representatives.md -- verbatim stdout snapshot\n\n"
    "**Do not hand-edit.** To update, re-run the producing script and let it "
    "overwrite this file.\n\n"
    "- Producing script: `analysis/70a_cluster_representatives.py`\n"
    f"- Repository HEAD when this snapshot was generated: `{head}`\n"
    "- Reproduce with: `.venv/bin/python analysis/70a_cluster_representatives.py`\n\n"
    "```text\n" + buf.getvalue() + "\n```\n",
    encoding="utf-8")
print(f"\nsnapshot written: {SNAP.relative_to(ROOT)}")
