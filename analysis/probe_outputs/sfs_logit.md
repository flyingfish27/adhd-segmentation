# sfs_logit.md -- verbatim stdout snapshot

**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.

- Producing script: `analysis/72_sfs_logit.py`
- Repository HEAD when this snapshot was generated: `ea7e2cee38fd90107974a920a544e272a1146ea7`
- Reproduce with: `.venv/bin/python analysis/72_sfs_logit.py`

```text

==============================================================================
[0] SETUP
==============================================================================
  model: logit lifted from 45 (CLF['logit'])   pool: 512 columns
  depth D = 20   targets: 10   inner CV: LOO-23, log-loss   SMOKE: False

==============================================================================
[G1] DETERMINISM GATE
==============================================================================
  fold 0 recomputed twice: identical -- GATE PASSED

==============================================================================
[G2] LIBRARY EQUIVALENCE GATE (hand log-loss vs sklearn pipeline)
==============================================================================
  5 candidates compared; max |diff| = 2.22e-16
  GATE PASSED

==============================================================================
[S] NESTED SFS
==============================================================================
  snap_inatt__qbin             done in  556.0s
  snap_hyper__qbin             done in  655.1s
  snap_odd__qbin               done in  826.4s
  snap_adhd_total__qbin        done in  763.2s
  sdq_hyper__qbin              done in  743.4s
  sdq_emo__qbin                done in  999.1s
  sdq_cond__qbin               done in  986.8s
  sdq_peer__qbin               done in  844.2s
  sdq_pro__qbin                done in  862.7s
  sdq_totdiff__qbin            done in 1038.2s
  total: 137.9 min

==============================================================================
[R] RESULT SUMMARY
==============================================================================
  written: analysis/sfs_logit_bin.csv (200 rows), analysis/sfs_logit_paths.csv (4800 rows)

  best depth per target by bacc (exploration; max over the path):
    snap_adhd_total__qbin        d= 1  bacc=0.833  f1=0.832  acc=0.833
    snap_odd__qbin               d= 2  bacc=0.789  f1=0.782  acc=0.792
    sdq_cond__qbin               d=19  bacc=0.781  f1=0.798  acc=0.833
    sdq_emo__qbin                d= 1  bacc=0.750  f1=0.733  acc=0.750
    snap_inatt__qbin             d= 1  bacc=0.708  f1=0.708  acc=0.708
    sdq_totdiff__qbin            d= 1  bacc=0.689  f1=0.697  acc=0.750
    sdq_peer__qbin               d= 9  bacc=0.639  f1=0.658  acc=0.792
    sdq_pro__qbin                d= 2  bacc=0.589  f1=0.590  acc=0.625
    snap_hyper__qbin             d=16  bacc=0.580  f1=0.580  acc=0.583
    sdq_hyper__qbin              d=14  bacc=0.486  f1=0.486  acc=0.500

  step-1 pick per target (folds agreeing on the most-chosen feature):
    snap_inatt__qbin             frac_act_short_w10_p20 (22/24)
    snap_hyper__qbin             pitch_kurt (10/24)
    snap_odd__qbin               stl_bout_median_w5_p30 (23/24)
    snap_adhd_total__qbin        frac_act_short_w10_p20 (24/24)
    sdq_hyper__qbin              uaZ_skew (7/24)
    sdq_emo__qbin                act_bout_median_w0.5_p80 (24/24)
    sdq_cond__qbin               gyX_min (16/24)
    sdq_peer__qbin               stl_bout_cv_w10_p10 (18/24)
    sdq_pro__qbin                uaZ_skew (19/24)
    sdq_totdiff__qbin            yaw_bp_hf (23/24)

```
