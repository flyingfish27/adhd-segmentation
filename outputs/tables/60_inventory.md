# 60_inventory.md -- verbatim stdout snapshot

**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.

- Producing script: `analysis/60_results_inventory.py`
- Repository HEAD when this snapshot was generated: `beae3b047e50d885330542202a5df43384539c85`
- Reproduce with: `.venv/bin/python analysis/60_results_inventory.py`
- Figures written by the same run: `outputs/figures/fig01_label_group_sizes.png`, `outputs/figures/fig02_feature_families.png`

```text

==============================================================================
[1] FILE INVENTORY -- shape of every input table, measured not quoted
==============================================================================
name                      rows   cols  path
A_univariate             12160     12  analysis/A_univariate.csv
B_multivariate             576     18  analysis/B_multivariate.csv
features                    24    609  analysis/features.csv
targets                     24     11  analysis/targets.csv
target_labels               24     40  analysis/target_labels.csv
target_labels_meta          40     17  analysis/target_labels_meta.csv
items                       24     51  analysis/items.csv
subject_audit               58      8  figures/subject_audit.csv

Column lists of the two result tables (the objects of this analysis):
  A_univariate (12 cols): ['target', 'type', 'feature', 'rho', 'auc', 'perm_p', 'loo_r2cv', 'loo_rmse', 'loo_mae', 'rho_partial_uamag', 'auc_partial_uamag', 'q_fdr']
  B_multivariate (18 cols): ['variant', 'track', 'target', 'model', 'k', 'n', 'rmse', 'mae', 'rho', 'skill', 'nc_skill', 'skill_over_nc', 'perm_p', 'bmi_sel_frac', 'f1', 'acc', 'bacc', 'q_fdr']

Cross-check against the prose in the documentation:
  FEATURE_MENU.md line 3 states 'features.csv (24 subjects x 351 columns)'.
    measured: 24 rows x 609 columns (608 features + the subject key)  -> STALE by 257 feature columns
  TARGET_MENU.md line 5 states 'target_labels.csv (24 subjects x 31 columns)'.
    measured: 24 rows x 40 columns (39 label columns + the subject key)

==============================================================================
[2] SUBJECT-KEY CONSISTENCY -- do all subject-indexed tables hold the same 24 people
==============================================================================
reference = features: n=24
  features                           n= 24  OK
  targets                            n= 24  OK
  target_labels                      n= 24  OK
  items                              n= 24  OK
  subject_audit(usable & _T==yes)    n= 24  OK

  verdict: all five tables carry the identical 24 subjects in identical order

  subject_audit.csv record counts by status (this is the selection funnel):
    {'usable': np.int64(42), 'EXCLUDED': np.int64(16)}
    records with _T == 'yes'          : 33
    records with status == 'usable'   : 42
    both (the analysed cohort)        : 24
    exclusion reasons recorded in 'high_risk' among the 16 non-usable records:
        6  SDQ missing; SNAP missing
        4  duplicate _T
        3  SNAP missing
        2  SDQ missing
        1  SDQ missing; SDQ illegal value

==============================================================================
[3] FEATURE-NAME CROSS-CHECK -- A_univariate.feature vs the columns of features.csv
==============================================================================
  distinct feature names in A_univariate : 608
  feature columns in features.csv        : 608
  screened but absent from features.csv  : 0
  present in features.csv but never screened: 0
  verdict: the screened feature set and the feature table are the same set

==============================================================================
[4] TARGET AND LABEL CROSS-CHECK -- which targets each track actually ran
==============================================================================
  continuous target columns in targets.csv      : 10  ['snap_inatt', 'snap_hyper', 'snap_odd', 'snap_adhd_total', 'sdq_hyper', 'sdq_emo', 'sdq_cond', 'sdq_peer', 'sdq_pro', 'sdq_totdiff']
  label columns in target_labels.csv            : 39
  rows in target_labels_meta.csv                : 40   (written=True: 39, written=False: 1)
  meta rows flagged degenerate=True             : 13
  meta rows flagged constant=True               : 4
  meta rows with written=False (rule kept, column not emitted): ['sdq_hyper__norm8']

  A-track ran:
    continuous targets : 10  ['sdq_cond', 'sdq_emo', 'sdq_hyper', 'sdq_peer', 'sdq_pro', 'sdq_totdiff', 'snap_adhd_total', 'snap_hyper', 'snap_inatt', 'snap_odd']
    binary targets     : 10  ['sdq_cond__qbin', 'sdq_emo__qbin', 'sdq_hyper__qbin', 'sdq_peer__qbin', 'sdq_pro__qbin', 'sdq_totdiff__qbin', 'snap_adhd_total__qbin', 'snap_hyper__qbin', 'snap_inatt__qbin', 'snap_odd__qbin']
  B-track (variant=='main') ran:
    regression targets : 10
    binary targets     : 10
    multiclass targets : 12  ['sdq_hyper__qquar', 'sdq_hyper__qter', 'sdq_totdiff__qquar', 'sdq_totdiff__qter', 'snap_adhd_total__qquar', 'snap_adhd_total__qter', 'snap_hyper__qquar', 'snap_hyper__qter', 'snap_inatt__qquar', 'snap_inatt__qter', 'snap_odd__qquar', 'snap_odd__qter']

  consistency of the target names against their source tables:
    A cont    10 targets, all present in targets.csv columns: yes
    A bin     10 targets, all present in target_labels.csv columns: yes
    B reg     10 targets, all present in targets.csv columns: yes
    B bin     10 targets, all present in target_labels.csv columns: yes
    B multi   12 targets, all present in target_labels.csv columns: yes

  degenerate labels that nevertheless entered a track: none
  label columns never used by either track: 17  -> ['sdq_cond__cn2013band3', 'sdq_cond__qquar', 'sdq_cond__qter', 'sdq_emo__cn2013band3', 'sdq_emo__qquar', 'sdq_emo__qter', 'sdq_hyper__cn2013band3', 'sdq_peer__cn2013band3', 'sdq_peer__qquar', 'sdq_peer__qter', 'sdq_pro__cn2013band3', 'sdq_pro__qquar', 'sdq_pro__qter', 'sdq_totdiff__cn2013band3', 'snap_hyper__dsm_count7', 'snap_inatt__dsm_count7', 'snap_odd__dsm_count5']

==============================================================================
[5] RESULT-TABLE COMPOSITION -- does the row count decompose as the design says
==============================================================================
  A_univariate rows: 12160
    by type: {'cont': np.int64(6080), 'bin': np.int64(6080)}
    608 features x 10 continuous targets = 6080   (measured cont rows: 6080)
    608 features x 10 binary targets     = 6080   (measured bin rows : 6080)
    duplicate (target, feature) pairs: 0

  B_multivariate rows: 576
    by variant: {'main': np.int64(192), 'nobmi_n23': np.int64(192), 'bmi_n23': np.int64(192)}
    main arm rows: 192
    main arm by track x model x k:
      track model  k  rows
        bin logit  5    10
        bin logit 10    10
        bin    rf  5    10
        bin    rf 10    10
        bin   svm  5    10
        bin   svm 10    10
      multi logit  5    12
      multi logit 10    12
      multi    rf  5    12
      multi    rf 10    12
      multi   svm  5    12
      multi   svm 10    12
        reg    rf  5    10
        reg    rf 10    10
        reg ridge  5    10
        reg ridge 10    10
        reg   svr  5    10
        reg   svr 10    10
    main arm n per row: {24: np.int64(192)}
    other arms n per row: {23: np.int64(384)}
    duplicate (variant, track, target, model, k) rows: 0

==============================================================================
[6] MISSINGNESS PER COLUMN -- empty cells are structural here, not damage
==============================================================================
  A_univariate: a column is expected empty on the row type it does not describe.
  column                  non-null    null   non-null on cont / on bin
  target                     12160       0     6080 /   6080
  type                       12160       0     6080 /   6080
  feature                    12160       0     6080 /   6080
  rho                         6080    6080     6080 /      0
  auc                         6080    6080        0 /   6080
  perm_p                     12160       0     6080 /   6080
  loo_r2cv                    6080    6080     6080 /      0
  loo_rmse                    6080    6080     6080 /      0
  loo_mae                     6080    6080     6080 /      0
  rho_partial_uamag            450   11710      450 /      0
  auc_partial_uamag            450   11710        0 /    450
  q_fdr                      12160       0     6080 /   6080

  B_multivariate (main arm only, the only arm that carries perm_p and q_fdr):
  column                  non-null    null   non-null on reg / bin / multi
  variant                      192       0      60 /    60 /    72
  track                        192       0      60 /    60 /    72
  target                       192       0      60 /    60 /    72
  model                        192       0      60 /    60 /    72
  k                            192       0      60 /    60 /    72
  n                            192       0      60 /    60 /    72
  rmse                          60     132      60 /     0 /     0
  mae                           60     132      60 /     0 /     0
  rho                           60     132      60 /     0 /     0
  skill                         60     132      60 /     0 /     0
  nc_skill                      60     132      60 /     0 /     0
  skill_over_nc                 60     132      60 /     0 /     0
  perm_p                        43     149      14 /    28 /     1
  bmi_sel_frac                   0     192       0 /     0 /     0
  f1                           132      60       0 /    60 /    72
  acc                          132      60       0 /    60 /    72
  bacc                         132      60       0 /    60 /    72
  q_fdr                        192       0      60 /    60 /    72

  perm_p present on 43 of 192 main-arm combinations; absent on 149.
  MODEL_MENU.md section 4 trap 2: an absent perm_p means the combination never beat the dummy baseline and so was never permutation-tested. It does not mean 'tested and found not significant'.

==============================================================================
[7] LABEL GROUP SIZES -- metadata claim vs recomputation from target_labels.csv
==============================================================================
  label                              k_dec k_obs  sizes (recomputed)           deg cons  A Bb Bm
  snap_inatt__qbin                       2     2  0:12 1:12                     .   .   Y  Y  . 
  snap_inatt__qter                       3     3  0:8 1:8 2:8                   .   .   .  .  Y 
  snap_inatt__qquar                      4     4  0:8 1:4 2:6 3:6               .   .   .  .  Y 
  snap_hyper__qbin                       2     2  0:13 1:11                     .   .   Y  Y  . 
  snap_hyper__qter                       3     3  0:11 1:6 2:7                  .   .   .  .  Y 
  snap_hyper__qquar                      4     4  0:11 1:2 2:7 3:4              .   .   .  .  Y 
  snap_odd__qbin                         2     2  0:15 1:9                      .   .   Y  Y  . 
  snap_odd__qter                         3     3  0:8 1:10 2:6                  .   .   .  .  Y 
  snap_odd__qquar                        4     4  0:7 1:8 2:3 3:6               .   .   .  .  Y 
  snap_adhd_total__qbin                  2     2  0:12 1:12                     .   .   Y  Y  . 
  snap_adhd_total__qter                  3     3  0:8 1:8 2:8                   .   .   .  .  Y 
  snap_adhd_total__qquar                 4     4  0:7 1:5 2:7 3:5               .   .   .  .  Y 
  sdq_hyper__qbin                        2     2  0:14 1:10                     .   .   Y  Y  . 
  sdq_hyper__qter                        3     3  0:8 1:8 2:8                   .   .   .  .  Y 
  sdq_hyper__qquar                       4     4  0:8 1:6 2:6 3:4               .   .   .  .  Y 
  sdq_emo__qbin                          2     2  0:12 1:12                     .   .   Y  Y  . 
  sdq_emo__qter                          3     3  0:8 1:9 2:7                   .   .   .  .  . 
  sdq_emo__qquar                         4     3  0:12 1:6 2:6                  Y   .   .  .  . 
  sdq_cond__qbin                         2     2  0:16 1:8                      .   .   Y  Y  . 
  sdq_cond__qter                         3     2  0:16 2:8                      Y   .   .  .  . 
  sdq_cond__qquar                        4     4  0:6 1:10 2:7 3:1              .   .   .  .  . 
  sdq_peer__qbin                         2     2  0:18 1:6                      .   .   Y  Y  . 
  sdq_peer__qter                         3     2  0:18 1:6                      Y   .   .  .  . 
  sdq_peer__qquar                        4     2  0:18 2:6                      Y   .   .  .  . 
  sdq_pro__qbin                          2     2  0:15 1:9                      .   .   Y  Y  . 
  sdq_pro__qter                          3     2  0:11 1:13                     Y   .   .  .  . 
  sdq_pro__qquar                         4     3  0:6 1:9 2:9                   Y   .   .  .  . 
  sdq_totdiff__qbin                      2     2  0:15 1:9                      .   .   Y  Y  . 
  sdq_totdiff__qter                      3     3  0:9 1:8 2:7                   .   .   .  .  Y 
  sdq_totdiff__qquar                     4     4  0:7 1:8 2:5 3:4               .   .   .  .  Y 
  sdq_hyper__norm8                       2     1  not emitted                   Y   Y   .  .  . 
  sdq_hyper__cn2013band3                 3     2  0:23 1:1                      Y   .   .  .  . 
  sdq_emo__cn2013band3                   3     3  0:18 1:4 2:2                  .   .   .  .  . 
  sdq_cond__cn2013band3                  3     2  0:23 1:1                      Y   .   .  .  . 
  sdq_peer__cn2013band3                  3     1  0:24                          Y   Y   .  .  . 
  sdq_pro__cn2013band3                   3     2  0:23 2:1                      Y   .   .  .  . 
  sdq_totdiff__cn2013band3               3     1  0:24                          Y   Y   .  .  . 
  snap_inatt__dsm_count7                 2     2  0:23 1:1                      .   .   .  .  . 
  snap_hyper__dsm_count7                 2     1  0:24                          Y   Y   .  .  . 
  snap_odd__dsm_count5                   2     2  0:22 1:2                      .   .   .  .  . 

  rows where the recomputed group sizes disagree with target_labels_meta.csv: 0
  smallest group across the 39 emitted label columns: 1 subject(s)
  label columns whose smallest group is <= 2 subjects: ['sdq_cond__cn2013band3', 'sdq_cond__qquar', 'sdq_emo__cn2013band3', 'sdq_hyper__cn2013band3', 'sdq_pro__cn2013band3', 'snap_hyper__qquar', 'snap_inatt__dsm_count7', 'snap_odd__dsm_count5']

  wrote /Users/shiyu/Projects/adhd-segmentation/outputs/figures/fig01_label_group_sizes.png

==============================================================================
[8] FEATURE FAMILIES -- decoding the feature names with the rules in FEATURE_MENU.md
==============================================================================
  family                                            count
  time-structure path A (per-subject threshold)       275
  time-domain                                         167
  frequency-domain                                     84
  time-structure path B (pooled threshold)             45
  nonlinear / complexity (undocumented family)         36
  recording duration (screened as a feature)            1
  TOTAL                                               608

  features not decoded by any naming rule: 0

  where the documentation and the table disagree:
    FEATURE_MENU.md section 4 lists the path-A stems without a window-length term
      (e.g. 'switch_per_min_p{..}') and implies 55 columns. The table carries a
      window sweep as well: 275 columns of the form 'switch_per_min_w0.5_p10'.
      window lengths present (seconds): ['0.5', '1', '2', '5', '10']
    the nonlinear/complexity family (36 columns on channels ['gyMag', 'jerk', 'uaMag'])
      is not mentioned anywhere in FEATURE_MENU.md. Stems: ['acf_dom_peak', 'acf_dom_period_s', 'acf_tau_1e_s', 'dfa_alpha', 'hurst_rs', 'lz_c', 'peak_amp_cv', 'peak_amp_med', 'peak_ipi_cv', 'peak_ipi_med_s', 'peak_rate_min', 'permen_m3']
    'rec_dur_min' (recording duration) is present as a screened feature column.
      MODEL_MENU.md section 5 lists recording duration as an UNCONTROLLED confound
      ('duration correlates with sdq_totdiff, rho=-0.46; modelling does not control
      for it'). It is therefore both a listed confound and one of the 608 candidate
      predictors that SelectKBest may choose inside the B-track pipeline.

  movement-total control (partial correlation / residualised AUC) coverage:
    features carrying it, measured from A_univariate non-null cells: 45
    features matching the path-B naming stems                     : 45
    the two sets agree: yes
    features WITHOUT any movement-total control                   : 563  (92.6% of the screen)

  wrote /Users/shiyu/Projects/adhd-segmentation/outputs/figures/fig02_feature_families.png

==============================================================================
[9] FACTS ESTABLISHED HERE THAT THE LATER STAGES DEPEND ON
==============================================================================
  cohort size                                  n = 24
  features screened                                608
  A-track cells (feature x target)                 12160  = 608 x (10 continuous + 10 binary)
  A-track BH-FDR family size (per target)          608
  A-track permutation p floor (1/NPERM)            1.0e-05
  B-track main-arm combinations                    192
  B-track BH-FDR family size                       192
  B-track combinations actually permutation-tested 43
  B-track permutation p floor observed             8.2e-03
  features with a movement-total control           45 of 608
```
