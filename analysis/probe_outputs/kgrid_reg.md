# kgrid_reg.md -- verbatim stdout snapshot

**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.

- Producing script: `analysis/73_reg_kgrid.py`
- Repository HEAD when this snapshot was generated: `f4ba968b7b7664f6bb886350aba44598ce8619b4`
- Reproduce with: `.venv/bin/python analysis/73_reg_kgrid.py`

```text

==============================================================================
[0] SETUP
==============================================================================
  models lifted from 45: ['ridge', 'svr', 'rf']   continuous targets: 10
  full table (24, 608), keep-list set (24, 512)   SMOKE: False

==============================================================================
[V1] PRODUCTION REPRODUCTION -- reg main arm of B_multivariate.csv
==============================================================================
  60 combinations recomputed in 17s; max |diff| vs committed table = 4.44e-16
  GATE PASSED

==============================================================================
[V2] LOOP EQUIVALENCE on the 512-column set
==============================================================================
  compared 2x6x3; mismatches = 0
  GATE PASSED

==============================================================================
[S] FULL SWEEP
==============================================================================
  grid: 10 targets x 3 models x 512 K values
  snap_inatt           done in  362.7s
  snap_hyper           done in  355.5s
  snap_odd             done in  399.8s
  snap_adhd_total      done in  335.1s
  sdq_hyper            done in  362.5s
  sdq_emo              done in  346.1s
  sdq_cond             done in  350.3s
  sdq_peer             done in  321.4s
  sdq_pro              done in  329.4s
  sdq_totdiff          done in  348.8s
  sweep total: 58.5 min

==============================================================================
[R] RESULT SUMMARY
==============================================================================
  written: analysis/kgrid_reg.csv  (15360 rows)

  best K per (target, model) by skill (exploration numbers; skill > 0 = beats predicting the mean):
    sdq_emo              rf     k=  1  skill=+0.335  rmse=1.136  mae=0.875  rho=+0.407
    sdq_emo              ridge  k=  2  skill=+0.320  rmse=1.161  mae=0.907  rho=+0.555
    sdq_emo              svr    k=  1  skill=+0.305  rmse=1.187  mae=0.825  rho=+0.748
    snap_hyper           ridge  k= 15  skill=+0.195  rmse=3.413  mae=2.597  rho=+0.619
    snap_adhd_total      svr    k=  1  skill=+0.174  rmse=6.985  mae=5.471  rho=+0.693
    snap_adhd_total      ridge  k=  1  skill=+0.170  rmse=7.017  mae=5.470  rho=+0.715
    snap_inatt           svr    k=  1  skill=+0.168  rmse=3.735  mae=2.811  rho=+0.680
    snap_inatt           ridge  k=  1  skill=+0.166  rmse=3.744  mae=2.824  rho=+0.713
    snap_inatt           rf     k=  1  skill=+0.142  rmse=3.854  mae=2.916  rho=+0.626
    snap_adhd_total      rf     k=  1  skill=+0.129  rmse=7.363  mae=5.405  rho=+0.624
    snap_hyper           svr    k=  1  skill=+0.119  rmse=3.739  mae=2.958  rho=+0.572
    sdq_cond             svr    k= 19  skill=+0.073  rmse=0.842  mae=0.665  rho=+0.438
    snap_hyper           rf     k=  1  skill=+0.072  rmse=3.937  mae=3.110  rho=+0.541
    sdq_cond             rf     k= 36  skill=+0.067  rmse=0.848  mae=0.648  rho=+0.431
    sdq_pro              ridge  k= 27  skill=+0.028  rmse=2.179  mae=1.689  rho=+0.380
    sdq_cond             ridge  k=  5  skill=+0.017  rmse=0.894  mae=0.671  rho=+0.423
    sdq_hyper            rf     k=  1  skill=-0.023  rmse=2.201  mae=1.699  rho=+0.298
    snap_odd             svr    k=  1  skill=-0.030  rmse=3.667  mae=2.719  rho=-0.226
    sdq_pro              svr    k= 38  skill=-0.033  rmse=2.315  mae=1.988  rho=-0.252
    sdq_pro              rf     k=471  skill=-0.035  rmse=2.321  mae=1.973  rho=-0.080
    snap_odd             rf     k=  1  skill=-0.049  rmse=3.731  mae=3.016  rho=+0.059
    sdq_hyper            svr    k=  1  skill=-0.051  rmse=2.260  mae=1.764  rho=+0.155
    sdq_peer             rf     k=402  skill=-0.056  rmse=0.888  mae=0.666  rho=-0.149
    sdq_peer             svr    k=402  skill=-0.060  rmse=0.891  mae=0.646  rho=-0.099
    sdq_totdiff          svr    k=504  skill=-0.062  rmse=3.378  mae=2.684  rho=-0.767
    sdq_peer             ridge  k= 23  skill=-0.087  rmse=0.914  mae=0.725  rho=+0.095
    snap_odd             ridge  k=  1  skill=-0.097  rmse=3.905  mae=2.947  rho=-0.126
    sdq_totdiff          rf     k=338  skill=-0.098  rmse=3.492  mae=2.889  rho=-0.303
    sdq_hyper            ridge  k=  4  skill=-0.101  rmse=2.367  mae=1.979  rho=+0.014
    sdq_totdiff          ridge  k= 16  skill=-0.242  rmse=3.951  mae=3.310  rho=-0.144

```
