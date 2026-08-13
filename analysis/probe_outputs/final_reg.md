# final_reg.md -- verbatim stdout snapshot

**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.

- Producing script: `analysis/74a_final_reg.py`
- Repository HEAD when this snapshot was generated: `ca7d74893fb800e932d01463cb2c11baabeb6c87`
- Reproduce with: `.venv/bin/python analysis/74a_final_reg.py`

```text

==============================================================================
[0] SETUP
==============================================================================
  model: ridge lifted from 45 (REG['ridge'])   targets: 10
  inner K grid: 1..20   pool: 512   SMOKE: False

==============================================================================
[V1] PRODUCTION REPRODUCTION -- ridge rows, reg main arm
==============================================================================
  20 combinations; max |diff| = 9.02e-17
  GATE PASSED

==============================================================================
[G2] FIXED-K EQUIVALENCE on the 512-column set
==============================================================================
  1 target x 3 K compared; mismatches = 0
  GATE PASSED

==============================================================================
[G3] DETERMINISM
==============================================================================
  fold 0 recomputed twice: identical -- GATE PASSED

==============================================================================
[S] NESTED DELIVERY RUN
==============================================================================
  snap_inatt           skill=+0.134 rmse=3.889 K*: med=1 range=1-2 K_final=1  (  0.8s)
  snap_hyper           skill=+0.047 rmse=4.044 K*: med=16 range=1-20 K_final=15  (  0.8s)
  snap_odd             skill=-0.190 rmse=4.235 K*: med=2 range=1-17 K_final=1  (  0.8s)
  snap_adhd_total      skill=+0.028 rmse=8.216 K*: med=1 range=1-20 K_final=1  (  0.8s)
  sdq_hyper            skill=-0.179 rmse=2.536 K*: med=2 range=1-14 K_final=4  (  0.8s)
  sdq_emo              skill=+0.277 rmse=1.234 K*: med=2 range=1-3 K_final=2  (  0.8s)
  sdq_cond             skill=-0.213 rmse=1.102 K*: med=6 range=1-20 K_final=5  (  0.8s)
  sdq_peer             skill=-0.148 rmse=0.965 K*: med=17 range=1-20 K_final=18  (  0.8s)
  sdq_pro              skill=-0.164 rmse=2.610 K*: med=19 range=1-20 K_final=19  (  0.8s)
  sdq_totdiff          skill=-0.432 rmse=4.552 K*: med=9 range=1-20 K_final=16  (  0.8s)
  total: 0.1 min

==============================================================================
[R] DELIVERY SUMMARY
==============================================================================
  written: final_reg_metrics.csv, final_reg_features.csv, final_reg_folds.csv, 10 joblib files

  DECLARATIONS: no significance testing; nested numbers cover the full f_regression-rank+auto-K+ridge procedure; skill <= 0 means the delivered model does not beat predicting the mean and is shipped as such; scale caveats as recorded for the classification delivery.

    sdq_emo              skill=+0.277  rmse=1.234  mae=1.008  rho=+0.538  K_final=2
    snap_inatt           skill=+0.134  rmse=3.889  mae=2.923  rho=+0.644  K_final=1
    snap_hyper           skill=+0.047  rmse=4.044  mae=3.211  rho=+0.431  K_final=15
    snap_adhd_total      skill=+0.028  rmse=8.216  mae=6.189  rho=+0.468  K_final=1
    sdq_peer             skill=-0.148  rmse=0.965  mae=0.755  rho=-0.006  K_final=18
    sdq_pro              skill=-0.164  rmse=2.610  mae=2.176  rho=-0.102  K_final=19
    sdq_hyper            skill=-0.179  rmse=2.536  mae=2.075  rho=-0.042  K_final=4
    snap_odd             skill=-0.190  rmse=4.235  mae=3.509  rho=-0.421  K_final=1
    sdq_cond             skill=-0.213  rmse=1.102  mae=0.853  rho=+0.131  K_final=5
    sdq_totdiff          skill=-0.432  rmse=4.552  mae=4.019  rho=-0.423  K_final=16

```
