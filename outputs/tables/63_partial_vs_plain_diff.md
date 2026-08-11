# 63_partial_vs_plain_diff.md -- verbatim stdout snapshot

**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.

- Producing script: `analysis/63_partial_vs_plain_diff.py`
- Repository HEAD when this snapshot was generated: `56575d5fd18e4de2448020aa36d565611989d4d1`
- Reproduce with: `.venv/bin/python analysis/63_partial_vs_plain_diff.py`
- Reads `analysis/A_univariate.csv` only. Nothing is refitted: both columns of
  every comparison are read from that file and subtracted.

```text

==============================================================================
[1] HOW MANY CELLS HAVE BOTH A PLAIN AND A PARTIAL VALUE
==============================================================================
  analysis/A_univariate.csv holds 12,160 rows in total.

  rho_partial_uamag (type=cont):
    non-NaN:           450
    NaN:            11,710
    features:           45
    targets:            10  (45 x 10 = 450)

  auc_partial_uamag (type=bin):
    non-NaN:           450
    NaN:            11,710
    features:           45
    targets:            10  (45 x 10 = 450)

==============================================================================
[2] RANGE OF THE SHIFT
==============================================================================
  Signed shift is partial minus plain. A negative value means partialling
  out total movement lowered the statistic.

  comparison                                min        max     median      |min|      |max|
  |rho_partial_uamag - rho|             -0.3246     0.3737    -0.0002     0.0001     0.3737
  |auc_partial_uamag - auc|             -0.2378     0.2014     0.0000     0.0000     0.2378

==============================================================================
[3] THE 30 LARGEST SHIFTS PER COMPARISON
==============================================================================

  |rho_partial_uamag - rho| -- top 30 of 450 cells
      feature          target       rho  rho_partial_uamag      diff  absdiff
  actfrac_p70         sdq_pro -0.104122           0.269593  0.373715 0.373715
  actfrac_p80         sdq_pro -0.022537           0.334264  0.356801 0.356801
  actfrac_p60 snap_adhd_total -0.201092          -0.525672 -0.324581 0.324581
  actfrac_p60      snap_hyper -0.217446          -0.530297 -0.312851 0.312851
  actfrac_p60         sdq_pro -0.208694           0.095725  0.304420 0.304420
switchmin_p90         sdq_pro  0.060850           0.358633  0.297782 0.297782
  actfrac_p60      snap_inatt -0.210992          -0.466429 -0.255437 0.255437
  actfrac_p50         sdq_pro -0.226548           0.023024  0.249572 0.249572
  actfrac_p60        snap_odd -0.092223          -0.337132 -0.244910 0.244910
  actfrac_p30         sdq_pro -0.190664           0.046507  0.237172 0.237172
  actfrac_p40         sdq_pro -0.223118           0.010721  0.233839 0.233839
  actfrac_p70 snap_adhd_total -0.263469          -0.494384 -0.230914 0.230914
  actfrac_p70      snap_hyper -0.286553          -0.514777 -0.228223 0.228223
  actfrac_p70         sdq_emo  0.092550           0.314824  0.222274 0.222274
  actfrac_p70        snap_odd -0.149586          -0.350451 -0.200864 0.200864
  actfrac_p20         sdq_pro -0.159112           0.036838  0.195950 0.195950
  actfrac_p10         sdq_pro -0.123053           0.067431  0.190484 0.190484
  actfrac_p90         sdq_pro  0.138378           0.327340  0.188961 0.188961
 actshort_p50         sdq_pro  0.061301          -0.124326 -0.185627 0.185627
switchmin_p70         sdq_pro -0.159112           0.024824  0.183936 0.183936
switchmin_p80         sdq_pro -0.244303          -0.061127  0.183176 0.183176
switchmin_p20         sdq_pro  0.172635          -0.009897 -0.182532 0.182532
switchmin_p80       sdq_hyper -0.074241           0.107826  0.182066 0.182066
  actfrac_p80 snap_adhd_total -0.321921          -0.503814 -0.181893 0.181893
  actfrac_p80      snap_hyper -0.334092          -0.502609 -0.168517 0.168517
 actshort_p20         sdq_pro  0.190664           0.026885 -0.163779 0.163779
switchmin_p10         sdq_pro  0.200581           0.036877 -0.163703 0.163703
 actshort_p40         sdq_pro  0.146492          -0.016264 -0.162756 0.162756
  actfrac_p80         sdq_emo  0.094338           0.247712  0.153374 0.153374
 actshort_p30         sdq_pro  0.218610           0.065366 -0.153245 0.153245

  |auc_partial_uamag - auc| -- top 30 of 450 cells
        feature                target      auc  auc_partial_uamag      diff  absdiff
    actfrac_p60      snap_hyper__qbin 0.447552           0.209790 -0.237762 0.237762
    actfrac_p40      snap_inatt__qbin 0.375000           0.576389  0.201389 0.201389
    actfrac_p40       sdq_hyper__qbin 0.321429           0.507143  0.185714 0.185714
    actfrac_p40 snap_adhd_total__qbin 0.506944           0.687500  0.180556 0.180556
    actfrac_p60        snap_odd__qbin 0.407407           0.237037 -0.170370 0.170370
    actfrac_p40        snap_odd__qbin 0.525926           0.688889  0.162963 0.162963
    actfrac_p70      snap_hyper__qbin 0.398601           0.244755 -0.153846 0.153846
    actfrac_p10       sdq_hyper__qbin 0.421429           0.557143  0.135714 0.135714
    actfrac_p30       sdq_hyper__qbin 0.335714           0.471429  0.135714 0.135714
    actfrac_p20       sdq_hyper__qbin 0.400000           0.535714  0.135714 0.135714
  switchmin_p10       sdq_hyper__qbin 0.600000           0.464286 -0.135714 0.135714
  switchmin_p10      snap_inatt__qbin 0.562500           0.430556 -0.131944 0.131944
    actfrac_p80      snap_hyper__qbin 0.370629           0.244755 -0.125874 0.125874
    actfrac_p60 snap_adhd_total__qbin 0.402778           0.277778 -0.125000 0.125000
    actfrac_p70        snap_odd__qbin 0.355556           0.237037 -0.118519 0.118519
    actfrac_p70         sdq_emo__qbin 0.555556           0.673611  0.118056 0.118056
  switchmin_p10         sdq_emo__qbin 0.569444           0.687500  0.118056 0.118056
actbout_med_p40       sdq_hyper__qbin 0.353571           0.471429  0.117857 0.117857
actbout_med_p30       sdq_hyper__qbin 0.300000           0.414286  0.114286 0.114286
    actfrac_p20         sdq_pro__qbin 0.533333           0.644444  0.111111 0.111111
    actfrac_p10      snap_inatt__qbin 0.423611           0.534722  0.111111 0.111111
    actfrac_p50        sdq_peer__qbin 0.537037           0.648148  0.111111 0.111111
   actshort_p20       sdq_hyper__qbin 0.628571           0.521429 -0.107143 0.107143
actbout_med_p20        sdq_peer__qbin 0.486111           0.592593  0.106481 0.106481
   actshort_p20      snap_inatt__qbin 0.569444           0.465278 -0.104167 0.104167
    actfrac_p40         sdq_emo__qbin 0.444444           0.340278 -0.104167 0.104167
actbout_med_p40      snap_inatt__qbin 0.430556           0.534722  0.104167 0.104167
    actfrac_p80        snap_odd__qbin 0.333333           0.229630 -0.103704 0.103704
actbout_med_p20         sdq_emo__qbin 0.385417           0.284722 -0.100694 0.100694
actbout_med_p20       sdq_hyper__qbin 0.392857           0.492857  0.100000 0.100000

==============================================================================
[4] FIGURE
==============================================================================
  wrote /Users/shiyu/Projects/adhd-segmentation/outputs/figures/fig16_partial_vs_plain_absdiff.png
```
