# kgrid_baseline.md -- verbatim stdout snapshot

**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.

- Producing script: `analysis/71_kgrid_baseline.py`
- Repository HEAD when this snapshot was generated: `54078ee0f8eccf339d35b3f5f57fd88bdb31f3a4`
- Reproduce with: `.venv/bin/python analysis/71_kgrid_baseline.py`

```text

==============================================================================
[0] SETUP
==============================================================================
  models lifted from 45_multivariate_cv.py: ['logit', 'svm', 'rf']
  binary targets (10): ['snap_inatt__qbin', 'snap_hyper__qbin', 'snap_odd__qbin', 'snap_adhd_total__qbin', 'sdq_hyper__qbin', 'sdq_emo__qbin', 'sdq_cond__qbin', 'sdq_peer__qbin', 'sdq_pro__qbin', 'sdq_totdiff__qbin']
  full table (24, 608), keep-list set (24, 512)
  SMOKE mode: False

==============================================================================
[V1] PRODUCTION REPRODUCTION -- bin main arm of B_multivariate.csv
==============================================================================
  60 combinations recomputed in 9s; max |diff| vs committed table = 5.55e-17
  GATE PASSED

==============================================================================
[V2] LOOP EQUIVALENCE on the 512-column set
==============================================================================
  compared 2x6x3 combinations; mismatches = 0
  GATE PASSED

==============================================================================
[S] FULL SWEEP
==============================================================================
  grid: 10 targets x 3 models x 512 K values
  snap_inatt__qbin             done in  249.0s
  snap_hyper__qbin             done in  324.9s
  snap_odd__qbin               done in  373.2s
  snap_adhd_total__qbin        done in  362.9s
  sdq_hyper__qbin              done in  360.9s
  sdq_emo__qbin                done in  356.3s
  sdq_cond__qbin               done in  355.6s
  sdq_peer__qbin               done in  361.2s
  sdq_pro__qbin                done in  367.2s
  sdq_totdiff__qbin            done in  379.0s
  sweep total: 58.2 min

==============================================================================
[R] RESULT SUMMARY
==============================================================================
  written: analysis/kgrid_baseline_bin.csv  (15360 rows)

  best K per (target, model) by balanced accuracy (exploration numbers -- the max over this grid is selection-biased):
    snap_adhd_total__qbin        rf     k=  1  bacc=0.833  f1=0.832  acc=0.833
    snap_adhd_total__qbin        logit  k=  1  bacc=0.833  f1=0.832  acc=0.833
    sdq_totdiff__qbin            rf     k=  1  bacc=0.822  f1=0.822  acc=0.833
    sdq_emo__qbin                logit  k=  6  bacc=0.792  f1=0.791  acc=0.792
    sdq_peer__qbin               svm    k= 12  bacc=0.778  f1=0.778  acc=0.833
    sdq_cond__qbin               logit  k= 16  bacc=0.750  f1=0.758  acc=0.792
    sdq_cond__qbin               svm    k= 17  bacc=0.750  f1=0.733  acc=0.750
    sdq_emo__qbin                rf     k=  1  bacc=0.750  f1=0.733  acc=0.750
    sdq_emo__qbin                svm    k=  1  bacc=0.750  f1=0.733  acc=0.750
    snap_inatt__qbin             logit  k=  1  bacc=0.750  f1=0.750  acc=0.750
    snap_adhd_total__qbin        svm    k=  1  bacc=0.750  f1=0.750  acc=0.750
    sdq_totdiff__qbin            svm    k=  1  bacc=0.744  f1=0.758  acc=0.792
    sdq_totdiff__qbin            logit  k=  1  bacc=0.744  f1=0.758  acc=0.792
    snap_hyper__qbin             svm    k= 15  bacc=0.710  f1=0.708  acc=0.708
    snap_inatt__qbin             rf     k=  1  bacc=0.708  f1=0.708  acc=0.708
    sdq_hyper__qbin              svm    k=503  bacc=0.693  f1=0.695  acc=0.708
    sdq_cond__qbin               rf     k= 36  bacc=0.688  f1=0.697  acc=0.750
    snap_odd__qbin               svm    k=  7  bacc=0.678  f1=0.681  acc=0.708
    snap_hyper__qbin             logit  k= 28  bacc=0.671  f1=0.667  acc=0.667
    sdq_peer__qbin               logit  k= 12  bacc=0.667  f1=0.667  acc=0.750
    snap_inatt__qbin             svm    k=  1  bacc=0.667  f1=0.664  acc=0.667
    snap_odd__qbin               logit  k=  7  bacc=0.644  f1=0.644  acc=0.667
    sdq_hyper__qbin              rf     k=  8  bacc=0.643  f1=0.644  acc=0.667
    sdq_hyper__qbin              logit  k=368  bacc=0.643  f1=0.644  acc=0.667
    snap_odd__qbin               rf     k= 23  bacc=0.622  f1=0.625  acc=0.667
    sdq_peer__qbin               rf     k=  1  bacc=0.583  f1=0.587  acc=0.708
    snap_hyper__qbin             rf     k=379  bacc=0.580  f1=0.580  acc=0.583
    sdq_pro__qbin                rf     k=295  bacc=0.556  f1=0.495  acc=0.667
    sdq_pro__qbin                logit  k= 30  bacc=0.511  f1=0.497  acc=0.500
    sdq_pro__qbin                svm    k= 21  bacc=0.467  f1=0.467  acc=0.500

```
