# kgrid_mi.md -- verbatim stdout snapshot

**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.

- Producing script: `analysis/71b_kgrid_mi.py`
- Repository HEAD when this snapshot was generated: `1c49d8919131880134095a380ec3a0114043b0b7`
- Reproduce with: `.venv/bin/python analysis/71b_kgrid_mi.py`

```text

==============================================================================
[0] SETUP
==============================================================================
  selector: permutation-z of mixed-estimator MI, P=200/fold
  discrete mask: 77 of 512 columns (<= 10 unique values)
  models: ['logit', 'svm', 'rf']   targets: 10   SMOKE: False
  fold-constant check: no fold of the 512-column set drops a column

==============================================================================
[G] DETERMINISM GATE
==============================================================================
  same (target, fold) computed twice: identical -- GATE PASSED

==============================================================================
[S] FULL SWEEP
==============================================================================
  grid: 10 targets x 3 models x 512 K values
  snap_inatt__qbin             done in  677.0s
  snap_hyper__qbin             done in 1743.6s
  snap_odd__qbin               done in  833.6s
  snap_adhd_total__qbin        done in 5004.6s
  sdq_hyper__qbin              done in 7312.0s
  sdq_emo__qbin                done in  438.5s
  sdq_cond__qbin               done in  470.7s
  sdq_peer__qbin               done in  670.7s
  sdq_pro__qbin                done in  419.3s
  sdq_totdiff__qbin            done in  570.5s
  sweep total: 302.3 min

==============================================================================
[R] RESULT SUMMARY
==============================================================================
  written: analysis/kgrid_mi_bin.csv  (15360 rows)

  best K per (target, model) by balanced accuracy (exploration numbers -- max over the grid is selection-biased, and this is the SECOND selector swept):
    snap_odd__qbin               svm    k=  7  bacc=0.756  f1=0.743  acc=0.750
    snap_odd__qbin               logit  k=  4  bacc=0.756  f1=0.743  acc=0.750
    sdq_peer__qbin               svm    k=339  bacc=0.750  f1=0.795  acc=0.875
    sdq_cond__qbin               rf     k= 25  bacc=0.750  f1=0.758  acc=0.792
    sdq_cond__qbin               logit  k= 84  bacc=0.750  f1=0.758  acc=0.792
    sdq_cond__qbin               svm    k= 99  bacc=0.750  f1=0.758  acc=0.792
    sdq_totdiff__qbin            logit  k=  4  bacc=0.733  f1=0.733  acc=0.750
    sdq_totdiff__qbin            rf     k=  2  bacc=0.733  f1=0.733  acc=0.750
    sdq_hyper__qbin              svm    k=340  bacc=0.729  f1=0.733  acc=0.750
    sdq_hyper__qbin              logit  k=415  bacc=0.729  f1=0.733  acc=0.750
    snap_odd__qbin               rf     k=  7  bacc=0.700  f1=0.695  acc=0.708
    sdq_totdiff__qbin            svm    k=  5  bacc=0.700  f1=0.695  acc=0.708
    snap_hyper__qbin             logit  k=485  bacc=0.671  f1=0.667  acc=0.667
    snap_adhd_total__qbin        logit  k= 39  bacc=0.667  f1=0.664  acc=0.667
    snap_inatt__qbin             svm    k=432  bacc=0.667  f1=0.664  acc=0.667
    snap_adhd_total__qbin        svm    k= 53  bacc=0.667  f1=0.664  acc=0.667
    sdq_emo__qbin                svm    k=  4  bacc=0.667  f1=0.664  acc=0.667
    sdq_emo__qbin                logit  k=  4  bacc=0.667  f1=0.664  acc=0.667
    sdq_hyper__qbin              rf     k=457  bacc=0.643  f1=0.644  acc=0.667
    snap_hyper__qbin             svm    k= 10  bacc=0.640  f1=0.619  acc=0.625
    snap_inatt__qbin             logit  k= 20  bacc=0.625  f1=0.624  acc=0.625
    sdq_pro__qbin                rf     k=  2  bacc=0.589  f1=0.590  acc=0.625
    snap_inatt__qbin             rf     k= 43  bacc=0.583  f1=0.583  acc=0.583
    sdq_peer__qbin               logit  k=168  bacc=0.583  f1=0.582  acc=0.792
    snap_adhd_total__qbin        rf     k=  2  bacc=0.583  f1=0.580  acc=0.583
    snap_hyper__qbin             rf     k=432  bacc=0.580  f1=0.580  acc=0.583
    sdq_peer__qbin               rf     k= 12  bacc=0.500  f1=0.429  acc=0.750
    sdq_emo__qbin                rf     k= 13  bacc=0.500  f1=0.500  acc=0.500
    sdq_pro__qbin                svm    k=  1  bacc=0.500  f1=0.385  acc=0.625
    sdq_pro__qbin                logit  k=451  bacc=0.500  f1=0.499  acc=0.542

```
