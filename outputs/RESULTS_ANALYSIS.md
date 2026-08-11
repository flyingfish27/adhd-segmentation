# Modelling results: what the two tracks actually show

An analysis of the results already committed to this repository — not a new model, and
not a re-run of the two scripts that produced them.

**Observation baseline.** Branch `results-analysis`, HEAD `5a0ca0e`; `main` at `beae3b0`.
〔2026-08-11 note: `5a0ca0e` is where this document was first committed; seven later commits
amended it (through `f6b3f14` and beyond) without refreshing this line. This file's git
history, not this line, is the authoritative record of its versions.〕
Every number below was measured from the CSV files by the three scripts listed under
*Reproducing this*, and none was copied from prose. Where a number contradicts a
document in the repository, the disagreement is reported in *Documents that no longer
match the tables* rather than silently resolved.

---

## 1. What was analysed

Two result tables, and the tables they were computed from.

| File | Shape as measured | What it holds |
|---|---|---|
| `analysis/A_univariate.csv` | 12,160 rows × 12 columns | one row per (feature × target): the univariate screen |
| `analysis/B_multivariate.csv` | 576 rows × 18 columns | one row per (arm × target × model × k): the cross-validated models |
| `analysis/features.csv` | 24 × 609 | 608 movement features + the subject key |
| `analysis/targets.csv` | 24 × 11 | 10 continuous symptom scores + subject |
| `analysis/target_labels.csv` | 24 × 40 | 39 grouped labels + subject |
| `analysis/target_labels_meta.csv` | 40 × 17 | one row per labelling rule |
| `analysis/items.csv` | 24 × 51 | item-level standardised questionnaire scores |
| `figures/subject_audit.csv` | 58 × 8 | the record-level selection audit |

**The cohort is 24 children.** `figures/subject_audit.csv` holds 58 records; 42 are marked
`usable` and 33 have a task-state recording (`_T == yes`); the 24 analysed are those
satisfying both. The 16 excluded records give reasons: 6 missing both questionnaires,
4 duplicate task recordings, 3 missing SNAP, 2 missing SDQ, 1 missing SDQ with an illegal
value. All five subject-indexed tables carry the identical 24 subjects in identical order.

**The screen is 608 features wide.** Decoding the column names gives: 275 time-structure
"path A" columns (a sweep over 5 window lengths × 9 activity-threshold percentiles), 167
time-domain statistics, 84 frequency-domain statistics, 45 time-structure "path B" columns
(pooled threshold), 36 nonlinear/complexity columns on the `uaMag`, `gyMag` and `jerk`
channels, and `rec_dur_min`, the recording duration. Nothing is left undecoded.

**12,160 statistical tests were run in the univariate track alone**: 608 features × (10
continuous targets + 10 median-split binary targets). The multivariate track adds 204
cross-validated model fits in its confirmatory arm.

Figures: `fig01_label_group_sizes.png`, `fig02_feature_families.png`.

---

## 2. What each track did

**Track A — univariate screening** (`analysis/44_univariate_screen.py`). Each feature is
tested against each target on its own. For the 10 continuous targets the statistic is a
Spearman rank correlation, accompanied by a closed-form leave-one-out R² (`loo_r2cv`). For
the 10 binary targets it is the rank-based AUC. Significance comes from 100,000 permutations
per target, and Benjamini–Hochberg false-discovery correction is applied within each target
family (m = 608, 20 families).

**Track B — multivariate cross-validation** (`analysis/45_multivariate_cv.py`). All 608
features enter a pipeline of variance filtering → `SelectKBest` (univariate F score, k ∈
{5, 10}) → standardisation → model, refitted inside every fold of a 24-fold leave-one-out
loop. Regression uses Ridge, SVR and random forest; classification uses logistic regression,
linear SVM and random forest. Combinations that beat a dummy baseline are permutation-tested
5,000 times, and BH correction is applied over all 204 combinations of the confirmatory arm.

The two are **not independent**. The B pipeline's `SelectKBest` step is itself a univariate
screen, refitted per fold. It differs from track A in the statistic (an F score on raw values
rather than Spearman on ranks), in selecting inside folds rather than on the full sample, and
in fitting a model afterwards — but agreement between the tracks is weaker evidence than
agreement between genuinely separate methods would be.

---

## 3. Track A: the univariate screen

### 3.1 In aggregate, the screen produced what chance produces

The permutation nulls the screen used were rebuilt here with the identical construction and
compared against the observed effect sizes.

| Quantity | Observed | Expected if every cell were null |
|---|---|---|
| Median \|Spearman rho\|, 6,080 continuous cells | 0.145 | 0.144 |
| Continuous cells above their target's null 95th percentile | 267 | 304 |
| Binary cells above their target's null 95th percentile | 316 | 304 |
| Cells at raw p < 0.05, all 12,160 | 604 | 608 |

Per target the ratio of observed to expected exceedances ranges from 0.23 (`snap_odd`) to
1.87 (`sdq_cond`) on the continuous side and 0.33 (`sdq_pro__qbin`) to 2.76
(`sdq_cond__qbin`) on the binary side, with no target's excess large enough to survive its
own correction except as described in 3.3.

The 608 features are strongly correlated with one another — the same channel at adjacent
percentile and window settings — so these counts are not 608 independent trials. They
describe where the observed distribution sits relative to the null; they are not themselves
a test. Figures: `fig03`, `fig04`.

### 3.2 Held-out prediction is essentially absent

`loo_r2cv` is the honest generalisation measure in this track: it asks whether a
single-feature fit predicts a child who was not used to fit it. Its median across the 6,080
continuous cells is **−0.056** — the typical feature predicts a held-out child *worse* than
the training mean does. 1,226 cells (20.2%) reach `loo_r2cv > 0`; a permutation null built
here for that same quantity puts the chance rate at 18.4%. Cells above the null 95th
percentile: 254 observed against 304 expected. Figure: `fig06`.

### 3.3 Three cells of 12,160 survive the correction

| Target | Feature | rho | loo_r2cv | q (published) | q (correctly specified) |
|---|---|---|---|---|---|
| `snap_inatt` | `frac_act_short_w10_p20` | +0.767 | 0.376 | 0.0061 | 0.0122 |
| `snap_adhd_total` | `frac_act_short_w10_p20` | +0.772 | 0.381 | 0.0061 | 0.0182 |
| `sdq_emo` | `act_bout_median_w0.5_p80` | +0.772 | 0.611 | 0.0061 | 0.0061 |

Twelve of the twenty targets have a smallest q above 0.5 and six above 0.9; `snap_odd`
reaches only 0.994.
Each survivor rests exactly on the permutation floor of 1e-5, meaning 100,000 shuffles never
matched it and its true p is smaller than 1e-5 by an amount these permutations cannot
resolve. Figures: `fig05`, `fig07`.

`fig07` row 1 draws each relationship with its ordinary least squares line, `y = w·x + b`,
plus the 24 refits that each leave one subject out. That line is **not** the statistic the
screen tested — the screen used Spearman rank correlation, which involves no line — but it is
the fit whose leave-one-out error becomes the `loo_r2cv` column, so it is the only thing on
that figure that speaks to prediction rather than description. The two statistics disagree
here, which is worth seeing rather than glossing:

| Cell | `w` | `b` | Pearson r (the line) | Spearman rho (the test) | in-sample R² | leave-one-out R² |
|---|---|---|---|---|---|---|
| `snap_inatt` × `frac_act_short_w10_p20` | +53.20 | −2.50 | +0.663 | +0.767 | 0.440 | +0.376 |
| `snap_adhd_total` × `frac_act_short_w10_p20` | +101.13 | −6.39 | +0.670 | +0.772 | 0.449 | +0.381 |
| `sdq_emo` × `act_bout_median_w0.5_p80` | +7.34 | −3.64 | +0.790 | +0.772 | 0.624 | +0.611 |

In physical terms the first line says: across the observed range of that feature (0.069 to
0.296), the fit predicts a swing of +12.1 points on a SNAP inattention scale whose observed
range is 1 to 19. The gap between the in-sample and leave-one-out R² columns — 0.440 → 0.376,
0.449 → 0.381, 0.624 → 0.611 — is what fitting 24 points to a two-parameter line costs.

Four properties of these three, measured rather than assumed:

- **They are robust to any single child.** Removing any one of the 24 subjects moves rho by
  at most 0.035, and no removal brings any of them near the null.
- **Two of them are one finding.** `snap_adhd_total` is by construction the sum of the SNAP
  inattention and hyperactivity items and correlates with `snap_inatt` at rho = +0.962. The
  same feature appearing against both is one result measured twice.
- **They are not explained by how much the child moved.** `frac_act_short_w10_p20` correlates
  with the movement-total control `uaMag_median` at −0.211, and `act_bout_median_w0.5_p80` at
  −0.175.
- **Their neighbours in the parameter grid are weaker, in an orderly way that settles
  nothing.** Path-A features are computed on a 5-window × 9-percentile grid over the same
  recording, giving 45 views. For `frac_act_short` on `snap_inatt` the surviving cell is
  \|rho\| 0.767 while the grid median is 0.062 and only 2 of 45 cells clear the null 95th
  percentile; the `act_bout_median` grid on `sdq_emo` has grid median 0.225 and 6 of 45 above
  the null. `fig07` row 3 shows both grids.

  That looked at first like an isolated spike, which would be the shape a maximum over many
  correlated noisy cells produces. **Measurement does not support reading it that way.** The
  neighbouring settings share only 0.13–0.72 rank correlation with the cell that survived, so
  they were never near-duplicates of it, and each neighbour's own effect is close to what
  simple attenuation predicts (|corr with the hit| × |the hit's rho|):

  | neighbour | corr with the hit | its own \|rho\| | attenuation predicts |
  |---|---|---|---|
  | `frac_act_short_w10_p30` | +0.514 | 0.430 | 0.394 |
  | `frac_act_short_w5_p20` | +0.350 | 0.316 | 0.268 |
  | `frac_act_short_w10_p10` | +0.132 | 0.201 | 0.101 |
  | `act_bout_median_w1_p80` | +0.715 | 0.606 | 0.552 |
  | `act_bout_median_w0.5_p90` | +0.544 | 0.328 | 0.420 |

  **But attenuation is an algebraic identity: it holds whether the hit's 0.77 is real or
  chance.** So the orderly drop-off is evidence for neither. The grid neighbourhood, which an
  earlier draft of this document treated as grounds for suspicion, turns out to be
  uninformative in both directions, and is recorded here as such.

One further property of the third survivor: `act_bout_median_w0.5_p80` takes only **4 distinct
values** across the 24 children (6 subjects at 0.5, 14 at 0.75, 3 at 1.0, 1 at 1.25). The
relationship it describes is therefore a comparison of four groups, not a graded association.

### 3.4 The negative control is inert

`uaMag_median`, the designated stand-in for "how much this child moved", ranks a median of
**466th of 608** features across the twenty targets. It reaches the top 5% for no target and
p < 0.05 for no target; its smallest p is 0.145. Whatever this screen is picking up, it is not
total movement. Figure: `fig09`.

### 3.5 Removing total movement changes nothing, because nothing is there

45 of the 608 features carry a movement-total adjustment (partial correlation for continuous
targets, residualised AUC for binary); the other 563 carry none. Across the 450 continuous
cells the median effect goes from 0.134 to 0.137, and across the 450 binary cells from 0.085
to 0.086. Cells above their target's null 95th percentile actually *increase*, 4 → 14 and
9 → 16. Figure: `fig10`.

---

## 4. Track B: the cross-validated models

### 4.1 Nothing survives

**The smallest q-value in the entire table is 0.5303.** The smallest permutation p is 0.0082;
on its own, against a family of 204, that rank-1 value would give q = 1.67, capped at 1. The
published 0.5303 is lower than that because the BH step-up carries down the running minimum
from a higher rank — here rank 8, where p = 0.0208 gives 0.0208 × 204 / 8 = 0.5303.

Of the 204 confirmatory combinations, 70 were permutation-tested and 13 reach p < 0.05 against
3.5 expected if all 70 were null. The other 134 never beat their dummy baseline, were never
tested, and enter the correction at p = 1 — which is a conservative convention that can hide
a real finding but cannot manufacture one. Figures: `fig11`, `fig12`.

The strongest results:

| Track | Target | Model | k | Metric | perm_p |
|---|---|---|---|---|---|
| multiclass | `snap_inatt__qquar` | random forest | 5 | balanced accuracy 0.521 | 0.0082 |
| multiclass | `snap_inatt__qquar` | random forest | 10 | balanced accuracy 0.479 | 0.0108 |
| multiclass | `sdq_emo__qter` | linear SVM | 5 | balanced accuracy 0.627 | 0.0120 |
| binary | `sdq_totdiff__qbin` | random forest | 5 | balanced accuracy 0.822 | 0.0130 |
| regression | `sdq_emo` | ridge | 10 | skill 0.155 | 0.0206 |

All five rows above carry the same `q_fdr`, 0.5303 — the running minimum the BH step-up
carries down. The first combination whose q rises above it is `sdq_emo` / ridge / k = 5, at
0.5666.

Median skill across the 60 regression combinations is **−0.069**: the typical fitted model
predicts a held-out child worse than the training mean.

### 4.2 The movement-total comparison is weaker than it looks

`skill_over_nc` compares the full 608-feature model against a model given only `uaMag_median`.
30 of 60 regression combinations are positive. But `nc_skill` is itself negative for all ten
targets (−0.086 to −0.034), so "beats the movement-total model" means "less bad than a model
that is already worse than predicting the mean". Only 14 of those 30 also beat the dummy
baseline. The 144 classification combinations have **no movement-total control at all**.
Figure: `fig13`.

### 4.3 The BMI arms cannot answer the question they were built for

BMI was never selected into the model in **201 of 204** combinations (`bmi_sel_frac` mean
0.0006, maximum 0.0435). Adding BMI changes the metric by exactly zero in 203 of 204
combinations, while dropping the single child who has no BMI recorded moves metrics by a
median of about 0.03 and by up to 0.35. "Adding BMI made no difference" here means BMI never
entered the model — a different statement from "BMI is unrelated to symptoms". Figure: `fig15`.

---

## 5. Verification carried out

Everything below was checked rather than assumed, and every check is reproduced in the stdout
snapshots under `outputs/tables/`.

| Check | Result |
|---|---|
| 40 published effect sizes recomputed from `features.csv` + targets with an independent implementation | Largest disagreement 8.3e-17 (rho) and 5.6e-17 (AUC) — float rounding only |
| All 12,160 published `perm_p` re-derived against independently drawn nulls | Rank correlation 0.999934; 12,152 of 12,160 on the same side of p < 0.05 |
| Published `q_fdr` in `A_univariate.csv` recomputed with an independent BH implementation | Largest deviation 5.5e-14 |
| Published `q_fdr` in `B_multivariate.csv` recomputed under the documented m = 204 family | Deviation 1.2e-15 |
| Label group sizes recomputed from `target_labels.csv` against `target_labels_meta.csv` | 0 mismatches across all 39 emitted columns |
| Screened feature set vs the columns of `features.csv` | Identical; 0 features either way |
| 11 internal-consistency assertions on `B_multivariate.csv` (metric ranges, `skill_over_nc` identity, per-track column presence, n per arm) | 11 of 11 pass |
| Degenerate labels reaching either track | None |

**The published tables reproduce from their committed inputs.** No discrepancy was found
between what the two scripts report and what their inputs support.

---

## 6. Two observations about the procedure

These concern how the results were computed, not what they show. Both were found while
checking the survivors and are stated here because they bear on how the numbers should be read.

**(a) The permutation gate on the multivariate track used 0.5 for every classification target.
This has since been changed; the paragraph is kept because it explains why the earlier figures
differ from the current ones.**

*As observed:* `45_multivariate_cv.py` sent a combination to permutation testing when balanced
accuracy exceeded 0.5. That is the chance level for the ten 2-class targets, but the multiclass
targets have 3 or 4 classes and chance levels of 1/3 or 1/4. Of the 72 multiclass combinations,
21 beat their own chance level; 20 of those were gated out and entered the correction at p = 1
without ever being tested. Their balanced accuracies ran from 0.313 to 0.479. The consequence
was one-directional: those combinations could only have been under-credited, never
over-credited.

*As resolved,* in commit `58b7bbf` — the same commit removed a hardcoded whitelist of six
multiclass base names, so the multiclass target list grew as well. The gate now reads each
target's own class count, `bacc > 1 / n_classes`. What changed in the numbers:

| | before `58b7bbf` | now |
|---|---|---|
| combinations in the family, m | 192 | 204 |
| multiclass combinations | 72 | 84 |
| permutation-tested | 43 (reg 14, bin 28, multi 1) | 70 (reg 14, bin 28, multi 28) |
| never tested, entered at p = 1 | 149 | 134 |
| `perm_p` < 0.05 | 6 | 13 |
| smallest `q_fdr` | 1.0000 | 0.5303 |
| `q_fdr` < 0.05 | 0 | 0 |

A flat `bacc > 0.5` rule would today test 5 of the 84 multiclass combinations; the own-chance
rule tests 28. In `fig12b` the "beat their baseline" and "permutation tested" bars are now
produced by the same rule and are therefore equal at 70; in the earlier version of that figure
they differed, and the gap was this gate.

**(b) The two tracks use different permutation tail conventions, and one of them is only safe
because of an unrelated approximation.** `44_univariate_screen.py` reports
`#{null > observed} / NPERM` floored at `1/NPERM`; `45_multivariate_cv.py` reports the standard
`(1 + #{null >= observed}) / (1 + NPERM)`. The two agree for a continuous null and diverge for a
discrete one. Track A's null is built by shuffling the target against the untied rank vector
`0..n-1` — its own comment records that this is the null "of any feature *without* ties" — and
137 of the 608 features do contain ties, 31 of them taking four or fewer distinct values.

The two issues interact, and the interaction is what matters:

- As published, the null is continuous, so the strictly-greater convention costs nothing. **The
  published p-values are not distorted.**
- Correcting the null to respect each feature's ties *without also* correcting the tail
  convention yields 11 FDR survivors, 8 of which have an honest p above 0.001. Worked example
  in `fig08c`: `act_bout_median_w2_p90` takes the value 2.0 for 22 of 24 children and 1.0 and
  3.0 for one child each; against `sdq_emo__qbin` its null has a two-point support {0, 0.0799},
  the observed statistic is the upper point, `P(null > observed) = 0` and
  `P(null >= observed) = 0.522`. The strictly-greater convention reports 1e-5 for a result whose
  honest p is roughly one half.
- Correcting **both** together leaves the same three cells the screen already reported, at
  q = 0.0061, 0.0122 and 0.0182.

So the published yield stands, and the note is a caution about what would happen if the null
were tightened in isolation. Figure: `fig08`.

---

## 7. Conclusion

**These results do not establish a relationship between wrist-worn accelerometer features and
questionnaire symptom scores in this cohort of 24 children.**

The grounds, in order of weight:

1. **The screen as a whole behaves like noise.** 604 of 12,160 cells reach raw p < 0.05 where
   608 are expected by chance. The median observed effect equals the median null effect to
   three decimal places. The count of cells clearing the null 95th percentile is *below* chance
   on the continuous half and 4% above it on the binary half.

2. **Prediction of an unseen child fails on both tracks.** Median leave-one-out R² is −0.056
   across the univariate screen and median skill is −0.069 across the 60 cross-validated
   regressions. Both mean the same thing: the typical fitted relationship does worse than
   predicting the group average.

3. **The multivariate track yields nothing at all.** Its smallest false-discovery q-value is
   0.5303. Its best single result, balanced accuracy 0.822 on `sdq_totdiff__qbin`, has a
   permutation p of 0.013, which does not survive a family of 204.

4. **Three cells of 12,160 do survive correction on the univariate track, and they survive a
   correctly specified test.** They are not artefacts of the tie/tail issue in §6, they are not
   driven by any single child, and they are not explained by total movement. This is a real
   positive finding and it should not be rounded down to zero.

What those three cells will and will not support:

- They are **two** distinct findings, not three: `snap_inatt` and `snap_adhd_total` are nested
  targets correlating at 0.962, and the same feature drives both.
- One of the two is on **`sdq_emo`, the SDQ emotional-symptoms subscale** — a scale carried in
  this project as a non-ADHD comparison, precisely so that a movement signal claimed to be
  ADHD-specific can be checked against it. It is the single strongest result in the entire
  screen (rho +0.772, leave-one-out R² 0.611), and its feature takes only four distinct values
  across 24 children.
- The ADHD-side finding, `frac_act_short_w10_p20` against SNAP inattention, sits in a
  parameter grid whose other 44 cells have a median \|rho\| of 0.062. §3.3 examines whether
  that pattern incriminates it and concludes that it does not — the neighbouring settings
  share only 0.13–0.51 with it, and their weaker effects are what attenuation predicts
  regardless of whether the hit is real. So the grid tells us nothing either way, and the
  question stays open on other grounds: **it was selected as the maximum of 12,160 comparisons,
  and the data that selected it cannot also test it.**
- Neither finding is corroborated by the multivariate track, and the two tracks are not
  independent in any case (§2).

The honest summary is that at n = 24 with 608 features, this design has enough resolution to
rule out a large, broad, robust movement signal — and it does rule one out — but not enough to
settle whether the two surviving cells are real. `MODEL_MENU.md` §5 records the power of this
design as approximately 49%.

---

## 8. What this analysis could not settle

- **Whether the two surviving cells replicate.** Nothing in a single 24-subject dataset can
  answer this. It requires either a held-out cohort or a pre-registered test of those two
  specific feature–target pairs.
- **Whether recording duration confounds the multivariate track.** `rec_dur_min` is one of the
  608 screened features and can be selected into any multivariate model, while
  `MODEL_MENU.md` §5 lists recording duration as an uncontrolled confound. Whether it entered
  any fitted model cannot be recovered from the committed tables.

  It does **not** explain the two surviving univariate findings, which was checked rather than
  assumed. `act_bout_median_w0.5_p80` correlates with recording length at −0.468 — the
  strongest association that feature has with anything measured here apart from bout
  fragmentation — so the check was warranted. Controlling for it leaves the findings intact:

  | Cell | rho | rho(feature, duration) | rho(duration, target) | partial rho |
  |---|---|---|---|---|
  | `sdq_emo` × `act_bout_median_w0.5_p80` | +0.772 | −0.468 | −0.283 | **+0.754** |
  | `snap_inatt` × `frac_act_short_w10_p20` | +0.767 | −0.173 | −0.078 | **+0.767** |
  | `snap_adhd_total` × `frac_act_short_w10_p20` | +0.772 | −0.173 | −0.050 | **+0.776** |

  Recording length spans only 41.3 to 59.8 minutes with a median of 59.8, i.e. most children
  sit at the ceiling, which limits how much damage it could do in this cohort regardless.
- **Whether the classification half of track B leaks total movement.** It has no negative
  control, by an explicit decision recorded in `45_multivariate_cv.py`. Nothing in the
  committed tables lets that be checked after the fact.
- **The true p-values of the three surviving cells.** All three rest on the permutation floor;
  resolving them further requires more permutations, which requires re-running the screen.
- **Anything requiring `data/`.** The raw recordings are, by design, not in version control.

## 9. Documents that no longer match the tables

Reported as measured facts; where each of these should go is not decided here.

| Document | What it states | What the tables measure |
|---|---|---|
| `FEATURE_MENU.md` line 3 | `features.csv` is 24 × 351 | 24 × 609 (608 features) |
| `FEATURE_MENU.md` line 83 | "351 features ≫ 24 samples" | 608 features |
| `FEATURE_MENU.md` §4 | path-A stems carry no window term, implying 55 columns | 275 columns, sweeping windows of 0.5/1/2/5/10 s |
| `FEATURE_MENU.md` | no mention of the 36 nonlinear/complexity columns or of `rec_dur_min` | both present in the screened set |
| `TARGET_MENU.md` line 5 | `target_labels.csv` is 24 × 31 | 24 × 40 (39 label columns) |
| `TARGET_MENU.md` line 94 | "4 main targets × 351 features = 1,404 tests" | 4 × 608 = 2,432 |

`INVENTORY.md` line 186 already records the 351 → 608 breakdown correctly and attributes it to
three tasks (+220 window sweep, +1 `rec_dur_min`, +36 new feature classes); 55 + 220 + 36 + 1
reproduces the measured composition exactly. `MODEL_MENU.md` carries inline corrections for its
own stale figures. So the counts are accounted for in the repository — it is the naming-rule
document a reader would consult to decode a feature name that is out of date.

Options, with their consequences:
- Leave them and rely on this document — the stale numbers stay discoverable only by whoever
  reads this file.
- Correct them inline in the style already used elsewhere in those files (original text kept,
  parenthetical correction appended) — consistent with existing practice, and touches four
  files this task did not otherwise modify.
- Record them as ledger entries in `working/` — this analysis did not read or write the
  `working/` triple, by instruction, so that has not been done.

〔2026-08-11〕 Resolved in part: the four `FEATURE_MENU.md` rows above were settled by the
second option — the inline corrections dated 2026-08-03, which had been sitting uncommitted
in the working tree, are committed in the same commit as this note (user decision,
2026-08-11). The two `TARGET_MENU.md` rows remain as measured.

---

## Reproducing this

```
.venv/bin/python analysis/60_results_inventory.py      # inventory and integrity audit
.venv/bin/python analysis/61_univariate_analysis.py    # track A          (~15 s)
.venv/bin/python analysis/62_multivariate_analysis.py  # track B          (~5 s)
.venv/bin/python analysis/63_partial_vs_plain_diff.py  # partial shift    (~2 s)
.venv/bin/python analysis/64_fig05b_standalone.py      # fig 5b alone     (~2 s)
.venv/bin/python analysis/66_selection_stability.py    # fold selection   (~5 s)
```

Each script derives all paths from its own location, reads only committed CSV files, touches
nothing under `data/`, and writes a verbatim copy of its stdout to `outputs/tables/`. Neither
`44_univariate_screen.py` nor `45_multivariate_cv.py` was re-run at any point.

The permutation nulls rebuilt in `61_` are not a re-run of the screen: they use the identical
construction from `44_univariate_screen.py` and depend only on the cohort size and the target,
never on the feature, which is why 608 features can share one. No null is rebuilt for track B,
whose null requires permuting the entire cross-validation — measured by its own script at about
14.7 hours.

## Figure index

| Figure | Shows |
|---|---|
| `fig01_label_group_sizes.png` | how each of the 39 label columns splits the 24 children, and which track used it |
| `fig02_feature_families.png` | the composition of the 608-feature screen, and how much of it carries a movement-total control |
| `fig03_effect_vs_null_continuous.png` | all 6,080 continuous effect sizes against the permutation null they were tested against |
| `fig04_effect_vs_null_binary.png` | the same for the binary half, per target, because the null depends on the group split |
| `fig05_fdr_per_target.png` | each target's 608 p-values against the BH threshold, and how close each came |
| `fig06_effect_vs_generalization.png` | in-sample correlation against leave-one-out R², with the null rate for the latter |
| `fig07_surviving_cells.png` | the three surviving cells: the relationship, the drop-one-subject check, the parameter-grid neighbourhood |
| `fig08_tie_corrected_pvalues.png` | how tied the features are, the effect of correctly specifying the null, and why the tail convention cannot be changed alone |
| `fig09_negative_control_rank.png` | where the movement-total control ranks among the 608 features of each target |
| `fig10_partial_control_pathB.png` | the 45 path-B columns before and after removing total movement |
| `fig11_cv_results_vs_baseline.png` | all 204 cross-validated results against the baseline each has to beat |
| `fig12_permutation_and_fdr.png` | the whole FDR family including the 134 never tested, and the funnel down to zero survivors |
| `fig13_full_model_vs_movement_total.png` | the 608-feature model against a model given only total movement |
| `fig14_track_agreement.png` | whether the two tracks pick out the same targets, with their non-independence stated |
| `fig15_bmi_arm.png` | whether BMI ever entered the model, and how that compares with dropping one child |
| `fig16_partial_vs_plain_absdiff.png` | how far partialling out total movement shifts each of the 450 path-B statistics, ranked (`fig10` shows the same columns as before-and-after pairs; this one shows the size of the shift) |
| `fig05b_standalone.png` | panel b of `fig05` on its own canvas, drawn from the same code and the same numbers; nothing is added and nothing is recomputed. The figure-level footnote of `fig05` is not carried over, because it describes panel a |
| `fig17_selection_frequency_profile.png` | for every track-B target and both k, how many of the 24 folds selected each feature — the shape that separates "one stable set" from "a different set every fold" |
| `fig18_selection_folds_sdq_emo_ridge.png` | the same question for one combination in full detail: which features each of the 24 folds picked for `sdq_emo` at k = 5 and k = 10 |
