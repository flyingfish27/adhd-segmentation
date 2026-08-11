# 66_selection_stability.md -- verbatim stdout snapshot

**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.

- Producing script: `analysis/66_selection_stability.py`
- Repository HEAD when this snapshot was generated: `66085a1e8544a7e69a22bfb4cb82f914a68057e8`
- Reproduce with: `.venv/bin/python analysis/66_selection_stability.py`
- Recomputes only the VarianceThreshold + SelectKBest prefix of the pipeline in
  `analysis/45_multivariate_cv.py`, which is lifted out of that file with `ast`
  rather than retyped. No model is fitted and no permutation is run.

```text

==============================================================================
[1] PIPELINE DEFINITIONS LIFTED OUT OF 45_multivariate_cv.py
==============================================================================
  extracted reg_pipe / clf_pipe / KS = [5, 10]
  reg    step 'vt' = VarianceThreshold(threshold=0.0)   step 'sel' = SelectKBest(score_func=f_regression, k=5)
  bin    step 'vt' = VarianceThreshold(threshold=0.0)   step 'sel' = SelectKBest(score_func=f_classif, k=5)
  multi  step 'vt' = VarianceThreshold(threshold=0.0)   step 'sel' = SelectKBest(score_func=f_classif, k=5)

==============================================================================
[2] INPUTS AND TARGET LISTS -- same rules as 45_multivariate_cv.py
==============================================================================
  features: 608   subjects: 24   folds per combination: 24 (leave-one-out)
  targets:  reg 10   bin 10   multi 14   -> 68 (target, k) combinations
  arm: main only (n = 24, no BMI column)

==============================================================================
[3] RECOMPUTING THE PER-FOLD SELECTION
==============================================================================
  For each (track, target, k) and each of the 24 leave-one-out training
  sets: fit VarianceThreshold, then SelectKBest, then map the selected
  positions back to the original feature columns.
  No model is fitted. Selection precedes the model in the pipeline and
  does not see it, so ridge / svr / rf share one selection, as do
  logit / svm / rf.

  done: 68 (track, target, k) combinations x 24 folds

==============================================================================
[4] HOW MANY DISTINCT FEATURES DOES EACH COMBINATION TOUCH
==============================================================================
  ever      = features selected in at least one of the 24 folds
  all-24    = features selected in every fold
  ever / k  = 1.0 means the same k features every fold; larger means churn
  the ceiling is k x 24 (a completely different set in every fold)

track                 target  k  ever  all24  half  ratio
  bin      sdq_totdiff__qbin  5     9      3     5   1.80
  bin          sdq_emo__qbin  5    13      2     5   2.60
  bin         sdq_peer__qbin  5    13      1     4   2.60
  bin        sdq_hyper__qbin  5    18      1     5   3.60
  bin         snap_odd__qbin  5    20      0     4   4.00
  bin         sdq_cond__qbin  5    21      0     4   4.20
  bin       snap_hyper__qbin  5    24      0     3   4.80
  bin       snap_inatt__qbin  5    25      1     3   5.00
  bin          sdq_pro__qbin  5    26      0     4   5.20
  bin  snap_adhd_total__qbin  5    28      1     5   5.60
  bin         sdq_peer__qbin 10    21      3    10   2.10
  bin         sdq_cond__qbin 10    27      1     9   2.70
  bin          sdq_emo__qbin 10    29      3     9   2.90
  bin      sdq_totdiff__qbin 10    29      5     8   2.90
  bin         snap_odd__qbin 10    32      2     8   3.20
  bin        sdq_hyper__qbin 10    35      4     8   3.50
  bin       snap_inatt__qbin 10    37      2     9   3.70
  bin          sdq_pro__qbin 10    37      1     7   3.70
  bin       snap_hyper__qbin 10    39      0     8   3.90
  bin  snap_adhd_total__qbin 10    46      1     7   4.60
multi          sdq_emo__qter  5     6      4     5   1.20
multi     sdq_totdiff__qquar  5    11      3     5   2.20
multi      snap_inatt__qquar  5    13      1     5   2.60
multi      snap_hyper__qquar  5    18      0     5   3.60
multi       snap_inatt__qter  5    20      3     3   4.00
multi       snap_hyper__qter  5    20      1     5   4.00
multi snap_adhd_total__qquar  5    24      1     4   4.80
multi      sdq_totdiff__qter  5    24      0     4   4.80
multi        sdq_cond__qquar  5    25      1     3   5.00
multi        sdq_hyper__qter  5    26      1     4   5.20
multi  snap_adhd_total__qter  5    31      1     3   6.20
multi         snap_odd__qter  5    33      0     3   6.60
multi        snap_odd__qquar  5    37      1     3   7.40
multi       sdq_hyper__qquar  5    37      0     3   7.40
multi      snap_inatt__qquar 10    21      4    11   2.10
multi          sdq_emo__qter 10    30      6     9   3.00
multi     sdq_totdiff__qquar 10    30      5     9   3.00
multi       snap_inatt__qter 10    35      3     8   3.50
multi snap_adhd_total__qquar 10    37      3    10   3.70
multi       snap_hyper__qter 10    41      3     8   4.10
multi        sdq_cond__qquar 10    43      1     9   4.30
multi        sdq_hyper__qter 10    46      2     8   4.60
multi  snap_adhd_total__qter 10    47      3     6   4.70
multi      sdq_totdiff__qter 10    47      2     8   4.70
multi      snap_hyper__qquar 10    52      0     7   5.20
multi         snap_odd__qter 10    56      2     8   5.60
multi       sdq_hyper__qquar 10    57      1     8   5.70
multi        snap_odd__qquar 10    63      1     6   6.30
  reg               sdq_cond  5    12      2     5   2.40
  reg             snap_hyper  5    14      1     4   2.80
  reg              sdq_hyper  5    15      1     5   3.00
  reg                sdq_emo  5    18      2     4   3.60
  reg        snap_adhd_total  5    19      1     5   3.80
  reg               sdq_peer  5    19      0     4   3.80
  reg               snap_odd  5    20      0     5   4.00
  reg             snap_inatt  5    22      1     5   4.40
  reg                sdq_pro  5    22      0     4   4.40
  reg            sdq_totdiff  5    23      0     4   4.60
  reg               sdq_cond 10    27      4     9   2.70
  reg               sdq_peer 10    27      1    10   2.70
  reg                sdq_pro 10    33      0     9   3.30
  reg             snap_hyper 10    34      2     8   3.40
  reg               snap_odd 10    35      0     9   3.50
  reg        snap_adhd_total 10    36      1     9   3.60
  reg                sdq_emo 10    36      3     9   3.60
  reg             snap_inatt 10    40      2     9   4.00
  reg              sdq_hyper 10    40      1    10   4.00
  reg            sdq_totdiff 10    46      0     8   4.60

  by track and k:
         ever            all24            half            ratio            
          min median max   min median max  min median max   min median  max
track k                                                                    
bin   5     9   20.5  28     0    1.0   3    3    4.0   5   1.8   4.10  5.6
      10   21   33.5  46     0    2.0   5    7    8.0  10   2.1   3.35  4.6
multi 5     6   24.0  37     0    1.0   4    3    4.0   5   1.2   4.80  7.4
      10   21   44.5  63     0    2.5   6    6    8.0  11   2.1   4.45  6.3
reg   5    12   19.0  23     0    1.0   2    4    4.5   5   2.4   3.80  4.6
      10   27   35.5  46     0    1.0   4    8    9.0  10   2.7   3.55  4.6

==============================================================================
[5] FIGURE 17 -- selection-frequency profile
==============================================================================
  wrote /Users/shiyu/Projects/adhd-segmentation/outputs/figures/fig17_selection_frequency_profile.png

==============================================================================
[6] FIGURE 18 -- fold x feature map for sdq_emo, ridge
==============================================================================
  ridge is a regression model, so the target is the continuous sdq_emo and
  the score function is f_regression. svr and rf give the same two panels.
  wrote /Users/shiyu/Projects/adhd-segmentation/outputs/figures/fig18_selection_folds_sdq_emo_ridge.png

  the two panels of fig 18, as numbers:

  k = 5: 18 features ever selected, of 608
    folds  feature
       24  act_bout_median_w0.5_p80
       24  act_bout_median_w1_p80
       21  switch_per_min_w10_p10
       16  stl_bout_median_w2_p80
        9  stl_bout_median_w5_p30
        6  frac_act_short_w5_p20
        5  act_bout_cv_w2_p20
        4  act_bout_cv_w0.5_p20
        2  act_bout_median_w2_p80
        1  gyMag_centroid
        1  gyMag_spread
        1  roll_kurt
        1  act_bout_cv_w1_p10
        1  act_bout_median_w1_p20
        1  act_bout_median_w1_p90
        1  act_bout_median_w2_p50
        1  act_bout_cv_w5_p40
        1  stl_bout_median_w10_p10

  k = 10: 36 features ever selected, of 608
    folds  feature
       24  act_bout_median_w0.5_p80
       24  act_bout_median_w1_p80
       24  switch_per_min_w10_p10
       23  act_bout_cv_w2_p20
       23  stl_bout_median_w2_p80
       21  act_bout_cv_w0.5_p20
       20  act_bout_cv_w1_p20
       20  stl_bout_median_w5_p30
       17  frac_act_short_w5_p20
        4  act_bout_cv_w5_p40
        3  gyMag_spread
        3  act_bout_cv_w1_p10
        3  act_bout_median_w2_p80
        3  act_bout_cv_w5_p30
        2  gyMag_bp_hf
        2  act_bout_median_w1_p20
        2  act_bout_median_w1_p70
        2  act_bout_cv_w2_p30
        2  act_bout_median_w5_p20
        2  stl_bout_median_w10_p10
        1  uaMag_bp_lf
        1  gyMag_centroid
        1  roll_std
        1  roll_kurt
        1  jerk_min
        1  jerk_range
        1  jerk_kurt
        1  jerk_dfa_alpha
        1  act_bout_cv_w0.5_p30
        1  switch_per_min_w0.5_p80
        1  act_bout_median_w1_p60
        1  act_bout_median_w1_p90
        1  frac_act_short_w2_p20
        1  act_bout_median_w2_p50
        1  stl_bout_cv_w2_p80
        1  stl_bout_median_w10_p20
```
