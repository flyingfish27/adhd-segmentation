# final_clf.md -- verbatim stdout snapshot

**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.

- Producing script: `analysis/74_final_clf.py`
- Repository HEAD when this snapshot was generated: `a9754a3ac4fb3fd8ade46e17ada6a1bfa613078d`
- Reproduce with: `.venv/bin/python analysis/74_final_clf.py`

```text

==============================================================================
[0] SETUP
==============================================================================
  targets: 10 bin + 14 multi = 24
  inner K grid: 1..20   pool: 512 columns   SMOKE: False

==============================================================================
[V1] PRODUCTION REPRODUCTION -- logit rows, bin AND multi main arm
==============================================================================
  48 combinations recomputed in 3s; max |diff| = 8.33e-17
  GATE PASSED

==============================================================================
[G2] FIXED-K EQUIVALENCE on the 512-column set
==============================================================================
  2 targets x 3 K compared; mismatches = 0
  GATE PASSED

==============================================================================
[G3] DETERMINISM
==============================================================================
  fold 0 recomputed twice: identical -- GATE PASSED

==============================================================================
[S] NESTED DELIVERY RUN
==============================================================================
  snap_inatt__qbin             bacc=0.667 K*: med=1 range=1-5 K_final=1  (  1.3s)
  snap_hyper__qbin             bacc=0.213 K*: med=2 range=1-20 K_final=15  (  1.3s)
  snap_odd__qbin               bacc=0.489 K*: med=2 range=1-17 K_final=4  (  1.4s)
  snap_adhd_total__qbin        bacc=0.750 K*: med=1 range=1-2 K_final=1  (  1.4s)
  sdq_hyper__qbin              bacc=0.314 K*: med=4 range=1-20 K_final=18  (  1.4s)
  sdq_emo__qbin                bacc=0.667 K*: med=1 range=1-8 K_final=1  (  1.3s)
  sdq_cond__qbin               bacc=0.500 K*: med=10 range=1-20 K_final=9  (  1.4s)
  sdq_peer__qbin               bacc=0.556 K*: med=12 range=1-20 K_final=12  (  1.4s)
  sdq_pro__qbin                bacc=0.300 K*: med=1 range=1-14 K_final=1  (  1.4s)
  sdq_totdiff__qbin            bacc=0.656 K*: med=1 range=1-10 K_final=1  (  1.4s)
  snap_inatt__qter             bacc=0.500 K*: med=2 range=1-6 K_final=3  (  1.7s)
  snap_inatt__qquar            bacc=0.323 K*: med=4 range=1-12 K_final=5  (  1.9s)
  snap_hyper__qter             bacc=0.307 K*: med=2 range=1-19 K_final=4  (  1.9s)
  snap_hyper__qquar            bacc=0.205 K*: med=1 range=1-3 K_final=4  (  2.1s)
  snap_odd__qter               bacc=0.242 K*: med=1 range=1-2 K_final=1  (  1.8s)
  snap_odd__qquar              bacc=0.250 K*: med=1 range=1-2 K_final=1  (  2.1s)
  snap_adhd_total__qter        bacc=0.458 K*: med=1 range=1-5 K_final=1  (  1.8s)
  snap_adhd_total__qquar       bacc=0.143 K*: med=2 range=1-20 K_final=1  (  2.0s)
  sdq_hyper__qter              bacc=0.292 K*: med=1 range=1-4 K_final=1  (  1.9s)
  sdq_hyper__qquar             bacc=0.167 K*: med=1 range=1-2 K_final=1  (  2.1s)
  sdq_emo__qter                bacc=0.585 K*: med=5 range=4-8 K_final=5  (  1.9s)
  sdq_cond__qquar              bacc=0.125 K*: med=1 range=1-7 K_final=1  (  2.2s)
  sdq_totdiff__qter            bacc=0.037 K*: med=1 range=1-15 K_final=1  (  1.9s)
  sdq_totdiff__qquar           bacc=0.359 K*: med=1 range=1-6 K_final=1  (  2.2s)
  total: 0.7 min

==============================================================================
[R] DELIVERY SUMMARY
==============================================================================
  written: final_clf_metrics.csv, final_clf_features.csv, final_clf_folds.csv, and 24 joblib files under outputs/models/

  DECLARATIONS: no significance testing in this delivery; nested numbers cover the full F-rank+auto-K+logit procedure; multiclass targets have 6-8 children per class; sdq_peer (4 of 5 items) and sdq_pro (reverse-scored control) carry scale caveats; yaw_bp_hf carries on-record wear-artifact and duration-confound caveats; track A is retired as a reference.

    snap_adhd_total__qbin        bin   bacc=0.750 (chance 0.50)  f1=0.750  K_final=1
    sdq_emo__qbin                bin   bacc=0.667 (chance 0.50)  f1=0.657  K_final=1
    snap_inatt__qbin             bin   bacc=0.667 (chance 0.50)  f1=0.667  K_final=1
    sdq_totdiff__qbin            bin   bacc=0.656 (chance 0.50)  f1=0.661  K_final=1
    sdq_emo__qter                multi bacc=0.585 (chance 0.33)  f1=0.582  K_final=5
    sdq_peer__qbin               bin   bacc=0.556 (chance 0.50)  f1=0.550  K_final=12
    snap_inatt__qter             multi bacc=0.500 (chance 0.33)  f1=0.479  K_final=3
    sdq_cond__qbin               bin   bacc=0.500 (chance 0.50)  f1=0.496  K_final=9
    snap_odd__qbin               bin   bacc=0.489 (chance 0.50)  f1=0.486  K_final=4
    snap_adhd_total__qter        multi bacc=0.458 (chance 0.33)  f1=0.452  K_final=1
    sdq_totdiff__qquar           multi bacc=0.359 (chance 0.25)  f1=0.329  K_final=1
    snap_inatt__qquar            multi bacc=0.323 (chance 0.25)  f1=0.288  K_final=5
    sdq_hyper__qbin              bin   bacc=0.314 (chance 0.50)  f1=0.314  K_final=18
    snap_hyper__qter             multi bacc=0.307 (chance 0.33)  f1=0.290  K_final=4
    sdq_pro__qbin                bin   bacc=0.300 (chance 0.50)  f1=0.273  K_final=1
    sdq_hyper__qter              multi bacc=0.292 (chance 0.33)  f1=0.283  K_final=1
    snap_odd__qquar              multi bacc=0.250 (chance 0.25)  f1=0.129  K_final=1
    snap_odd__qter               multi bacc=0.242 (chance 0.33)  f1=0.194  K_final=1
    snap_hyper__qbin             bin   bacc=0.213 (chance 0.50)  f1=0.207  K_final=15
    snap_hyper__qquar            multi bacc=0.205 (chance 0.25)  f1=0.141  K_final=4
    sdq_hyper__qquar             multi bacc=0.167 (chance 0.25)  f1=0.129  K_final=1
    snap_adhd_total__qquar       multi bacc=0.143 (chance 0.25)  f1=0.146  K_final=1
    sdq_cond__qquar              multi bacc=0.125 (chance 0.25)  f1=0.119  K_final=1
    sdq_totdiff__qter            multi bacc=0.037 (chance 0.33)  f1=0.032  K_final=1

```
