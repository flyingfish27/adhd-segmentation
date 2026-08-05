# 62_multivariate.md -- verbatim stdout snapshot

**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.

- Producing script: `analysis/62_multivariate_analysis.py`
- Repository HEAD when this snapshot was generated: `6fbaaa643c269e44964efd4f1eb8e758a427bcb5`
- Reproduce with: `.venv/bin/python analysis/62_multivariate_analysis.py`
- No permutation null is rebuilt for this track: the B-track null requires permuting the
  whole cross-validation, which its producing script measures at about 14.7 hours.

```text

==============================================================================
[1] INTERNAL CONSISTENCY OF B_multivariate.csv
==============================================================================
  rows: 612   arms: {'main': np.int64(204), 'nobmi_n23': np.int64(204), 'bmi_n23': np.int64(204)}
  MODEL_MENU.md section 4 trap 7: any count over this table must first be
  restricted to variant == 'main', or it is inflated threefold. Main arm: 204 rows.
  [ok ] every main-arm row used all 24 subjects   n values [np.int64(24)]
  [ok ] the two exploratory arms used 23 subjects
  [ok ] balanced accuracy within [0, 1]   range 0.000 .. 0.822
  [ok ] macro F1 within [0, 1]   range 0.000 .. 0.822
  [ok ] accuracy within [0, 1]
  [ok ] skill <= 1 (it is 1 - RMSE/RMSE_dummy, so it cannot exceed 1)   range -0.434 .. 0.163
  [ok ] skill_over_nc equals skill - nc_skill   max deviation 1.11e-16
  [ok ] regression metrics absent on classification rows and vice versa
  [ok ] nc_skill is a property of the target alone, identical across model and k
  [ok ] published q_fdr reproduces from perm_p with the documented m = 204 family   max deviation 1.22e-15
  [ok ] q_fdr is present only on the main arm

  11 of 11 checks passed

==============================================================================
[2] EVERY MAIN-ARM COMBINATION AGAINST ITS BASELINE
==============================================================================
  Regression baseline: skill = 0, i.e. the same RMSE as always predicting the
  training mean. Classification baseline: balanced accuracy = 1/k, where k is the
  number of classes -- 1/2 for the 10 __qbin targets, 1/3 for the 7 __qter and
  1/4 for the 7 __qquar.

  track   combinations  beat baseline   share     best  best combination
  reg               60             14   23.3%    0.163  sdq_emo / ridge / k5
  bin               60             28   46.7%    0.822  sdq_totdiff__qbin / rf / k5
  multi             84             28   33.3%    0.627  sdq_emo__qter / logit / k5

  the permutation gate, as written in 45_multivariate_cv.py:
    regression      skill > 0             -- this is exactly the dummy baseline
    classification  bacc > 1 / n_classes  -- each target against its own chance level
  For the 84 multiclass combinations, chance is 1/3 or 1/4, not 1/2.
    above their own chance level       : 28
    of those, permutation-tested       : 28
    a flat bacc > 0.5 rule would test  : 5
  Until commit 58b7bbf the gate WAS that flat bacc > 0.5, which is the chance
  level of a 2-class target only. Multiclass combinations that beat 1/3 or 1/4
  but not 1/2 therefore entered the FDR family at p = 1 without ever being
  tested. That is no longer the case: the gate now reads each target's own
  class count, so this figure's 'beat their baseline' and 'permutation tested'
  counts are produced by the same rule.

  wrote /Users/shiyu/Projects/adhd-segmentation/outputs/figures/fig11_cv_results_vs_baseline.png

==============================================================================
[3] PERMUTATION AND FDR ON THE B TRACK
==============================================================================
  combinations in the family                 : 204
  actually permutation-tested                : 70   (reg 14, bin 28, multi 28)
  never tested, entered the family as p = 1  : 134
  permutation resolution 1/(NPERM+1)         : 2.00e-04
  smallest perm_p anywhere in the table      : 0.0082
    -- no combination came within a factor of 41 of the resolution limit,
       so unlike the A track nothing here is pinned to the floor.
  perm_p < 0.05                              : 13   (of 70 tested; if all 70 were null, 3.5 would be expected)
  q_fdr < 0.05                               : 0
  q_fdr < 0.10                               : 0
  smallest q_fdr in the table                : 0.5303

  the ten smallest permutation p-values:
  track  target                   model    k   metric   perm_p    q_fdr
  multi  snap_inatt__qquar        rf       5    0.521   0.0082   0.5303
  multi  snap_inatt__qquar        rf      10    0.479   0.0108   0.5303
  multi  sdq_emo__qter            svm      5    0.627   0.0120   0.5303
  bin    sdq_totdiff__qbin        rf       5    0.822   0.0130   0.5303
  multi  sdq_emo__qter            logit    5    0.627   0.0156   0.5303
  multi  snap_inatt__qquar        svm     10    0.469   0.0190   0.5303
  reg    sdq_emo                  ridge   10    0.155   0.0206   0.5303
  multi  sdq_emo__qter            rf       5    0.607   0.0208   0.5303
  reg    sdq_emo                  ridge    5    0.163   0.0250   0.5666
  reg    sdq_emo                  svr     10    0.085   0.0336   0.6853

  wrote /Users/shiyu/Projects/adhd-segmentation/outputs/figures/fig12_permutation_and_fdr.png

==============================================================================
[4] FULL MODEL vs MOVEMENT TOTAL ALONE (regression half only)
==============================================================================
  nc_skill is the skill of a model given a single feature, uaMag_median, through the
  same leave-one-out procedure. skill_over_nc = skill - nc_skill, on a shared
  denominator, so it answers: how much does the 608-feature model add over knowing
  only how much the child moved.
  This control exists for the 60 regression rows. The 144 classification rows have
  no negative control at all -- a decision recorded in 45_multivariate_cv.py and
  required to be declared with the results.

  target                nc_skill  best skill  best skill_over_nc  models beating nc
  sdq_cond                -0.070       0.016               0.086             5 / 6
  sdq_emo                 -0.061       0.163               0.224             6 / 6
  sdq_hyper               -0.046      -0.097              -0.051             0 / 6
  sdq_peer                -0.086       0.015               0.101             3 / 6
  sdq_pro                 -0.034      -0.094              -0.060             0 / 6
  sdq_totdiff             -0.063      -0.140              -0.077             0 / 6
  snap_adhd_total         -0.067       0.051               0.118             4 / 6
  snap_hyper              -0.070       0.055               0.125             6 / 6
  snap_inatt              -0.067       0.049               0.116             5 / 6
  snap_odd                -0.078      -0.045               0.033             1 / 6

  regression combinations with skill > 0 (beat the dummy)      : 14 of 60
  regression combinations with skill_over_nc > 0 (beat movement total): 30 of 60
  targets where the movement-total model alone has skill > 0   : none
  median skill across the 60 regression combinations           : -0.069
  median nc_skill                                              : -0.067

  A qualification that changes how skill_over_nc should be read here: nc_skill is
  negative for all 10 targets (range -0.086 to -0.034).
  The movement-total model is itself worse than the dummy. So skill_over_nc > 0 means
  'less bad than a model that is already worse than predicting the mean', not 'good'.
  Of the 30 combinations that beat the movement-total model, 14 also beat the dummy baseline.

  wrote /Users/shiyu/Projects/adhd-segmentation/outputs/figures/fig13_full_model_vs_movement_total.png

==============================================================================
[5] AGREEMENT BETWEEN THE TWO TRACKS
==============================================================================
  How independent are they, actually? Less than the two-track framing suggests.
  The B pipeline is VarianceThreshold -> SelectKBest(F score) -> StandardScaler ->
  model. SelectKBest ranks features by a univariate F statistic, so the B track
  begins with a univariate screen of its own, refitted inside each fold. It differs
  from the A track in using an F statistic on raw values rather than Spearman on
  ranks, in selecting inside folds rather than on the full sample, and in then
  fitting a model on the survivors -- but it is not an independent second look.
  A correlation between the two tracks is therefore expected to some degree, and
  agreement between them is weaker evidence than agreement between genuinely
  separate methods would be.

  target                   kind        A best effect  A min q   B best  B metric
  sdq_cond                 continuous          0.668    0.231    0.016     skill
  sdq_emo                  continuous          0.772    0.006    0.163     skill
  sdq_hyper                continuous          0.590    0.922   -0.097     skill
  sdq_peer                 continuous          0.618    0.833    0.015     skill
  sdq_pro                  continuous          0.572    0.916   -0.094     skill
  sdq_totdiff              continuous          0.528    0.975   -0.140     skill
  snap_adhd_total          continuous          0.772    0.006    0.051     skill
  snap_hyper               continuous          0.720    0.061    0.055     skill
  snap_inatt               continuous          0.767    0.006    0.049     skill
  snap_odd                 continuous          0.538    0.994   -0.045     skill
  sdq_cond__qbin           binary              0.414    0.127    0.656      bacc
  sdq_emo__qbin            binary              0.333    0.964    0.625      bacc
  sdq_hyper__qbin          binary              0.350    0.504    0.607      bacc
  sdq_peer__qbin           binary              0.389    0.542    0.639      bacc
  sdq_pro__qbin            binary              0.307    0.980    0.322      bacc
  sdq_totdiff__qbin        binary              0.396    0.210    0.822      bacc
  snap_adhd_total__qbin    binary              0.396    0.231    0.500      bacc
  snap_hyper__qbin         binary              0.318    0.675    0.503      bacc
  snap_inatt__qbin         binary              0.368    0.669    0.542      bacc
  snap_odd__qbin           binary              0.367    0.884    0.678      bacc

  continuous: Spearman correlation between the A-track best effect and the
    B-track best metric across the 10 targets = +0.915
    (10 points; with n = 10 this number is itself very imprecise and is
     reported as a description of the scatter, not as a test.)

  binary: Spearman correlation between the A-track best effect and the
    B-track best metric across the 10 targets = +0.564
    (10 points; with n = 10 this number is itself very imprecise and is
     reported as a description of the scatter, not as a test.)

  wrote /Users/shiyu/Projects/adhd-segmentation/outputs/figures/fig14_track_agreement.png

==============================================================================
[6] THE TWO EXPLORATORY ARMS (BMI)
==============================================================================
  Three arms exist so that two changes can be separated: bmi_n23 minus nobmi_n23 is
  the effect of adding BMI, and nobmi_n23 minus main is the effect of dropping the
  one subject who has no BMI recorded. Neither exploratory arm enters the FDR family
  and neither was permutation-tested.

  bmi_sel_frac -- the share of leave-one-out folds in which SelectKBest actually
  chose BMI into the top-k. MODEL_MENU.md marks this as required reading, because
  if it is near zero then 'adding BMI changed nothing' means BMI never entered the
  model, which is a different statement from 'BMI is unrelated to symptoms'.
    combinations in the arm  : 204
    mean                     : 0.0006
    max                      : 0.0435
    never selected (== 0)    : 201 of 204
    selected in every fold   : 0 of 204

  [reg] skill
    adding BMI      (bmi_n23 - nobmi_n23): median +0.0000  max |diff| 0.0000  nonzero 0/60
    dropping 1 subj (nobmi_n23 - main)   : median +0.0287  max |diff| 0.2319  nonzero 60/60
    ratio of the two typical magnitudes  : 0.00

  [bin] bacc
    adding BMI      (bmi_n23 - nobmi_n23): median +0.0000  max |diff| 0.0000  nonzero 0/60
    dropping 1 subj (nobmi_n23 - main)   : median +0.0261  max |diff| 0.3542  nonzero 60/60
    ratio of the two typical magnitudes  : 0.00

  [multi] bacc
    adding BMI      (bmi_n23 - nobmi_n23): median +0.0000  max |diff| 0.0312  nonzero 1/84
    dropping 1 subj (nobmi_n23 - main)   : median +0.0232  max |diff| 0.2565  nonzero 81/84
    ratio of the two typical magnitudes  : 0.00

  wrote /Users/shiyu/Projects/adhd-segmentation/outputs/figures/fig15_bmi_arm.png
```
