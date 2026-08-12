# cluster_representatives.md -- verbatim stdout snapshot

**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.

- Producing script: `analysis/70a_cluster_representatives.py`
- Repository HEAD when this snapshot was generated: `91c9b0845dadbcd77af9eac89b4017ddce904f54`
- Reproduce with: `.venv/bin/python analysis/70a_cluster_representatives.py`

```text

==============================================================================
[1] INPUT SET AFTER FS-D1
==============================================================================
  features.csv feature columns: 608
  dropped by FS-D1: rec_dur_min  (for the record, its strongest
  partner among the other 607 was act_bout_cv_w0.5_p90, |rho| = 0.666)
  working set: 607 columns

==============================================================================
[2] CONNECTED COMPONENTS AT |Spearman| >= 0.90 (construction = 70 [5])
==============================================================================
  groups: 346  =  297 singletons + 49 clusters
  (70 [5] measured on 608 columns: 347 = 298 + 49; the difference is rec_dur_min itself)
  cluster sizes, descending: [74, 61, 23, 16, 7, 6, 6, 6, 6, 6, 5, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
  would-be column count after picking 1 per cluster: 297 + 49 = 346

==============================================================================
[3] PER-CLUSTER VERDICT ON THE THREE CRITERIA
==============================================================================
  C1 = most unique values | C2 = most central parameters | C3 = no
  on-record interpretability caveat.  'ALL-3' = one column wins all
  three at once (as asked: reported first, conflicts called out).

  G01 size=74 in|rho| min=0.00 med=0.71  [actfrac[pathB]x9, within_win_sdx5, switchmin[pathB]x3, actshort[pathB]x3, uaX_std, uaX_var, uaX_rms, uaX_iqr, uaX_mad, uaX_madiff, uaY_std, uaY_var, uaY_rms, uaY_iqr, uaY_mad, uaY_madiff, uaZ_std, uaZ_var, uaZ_rms, uaZ_iqr, uaZ_mad, uaZ_madiff, uaMag_mean, uaMag_std, uaMag_var, uaMag_rms, uaMag_median, uaMag_iqr, uaMag_mad, uaMag_madiff, gyX_std, gyX_var, gyX_rms, gyX_madiff, gyY_iqr, gyY_mad, gyZ_std, gyZ_var, gyZ_rms, gyZ_iqr, gyZ_mad, gyZ_madiff, gyMag_mean, gyMag_rms, gyMag_median, gyMag_mad, gyMag_madiff, pitch_madiff, jerk_std, jerk_var, jerk_rms, jerk_iqr, jerk_mad, jerk_madiff, uaMag_peak_amp_med, gyMag_peak_amp_med, jerk_peak_amp_med, actbout_med[pathB]]
       -> ALL-3 tie (54): gyMag_mad, gyMag_madiff, gyMag_mean, gyMag_median, gyMag_peak_amp_med, gyMag_rms, gyX_madiff, gyX_rms, gyX_std, gyX_var, gyY_iqr, gyY_mad, gyZ_iqr, gyZ_mad, gyZ_madiff, gyZ_rms, gyZ_std, gyZ_var, jerk_iqr, jerk_mad, jerk_madiff, jerk_peak_amp_med, jerk_rms, jerk_std, jerk_var, pitch_madiff, uaMag_iqr, uaMag_mad, uaMag_madiff, uaMag_mean, uaMag_median, uaMag_peak_amp_med, uaMag_rms, uaMag_std, uaMag_var, uaX_iqr, uaX_mad, uaX_madiff, uaX_rms, uaX_std, uaX_var, uaY_iqr, uaY_mad, uaY_madiff, uaY_rms, uaY_std, uaY_var, uaZ_iqr, uaZ_mad, uaZ_madiff, uaZ_rms, uaZ_std, uaZ_var, within_win_sd_w2  [contains negative control uaMag_median]
  G02 size=61 in|rho| min=0.01 med=0.71  [switch_per_minx28, frac_act_shortx17, switchmin[pathB]x4, uaMag_zcr, uaMag_hurst_rs, uaMag_lz_c, uaMag_acf_dom_peak, uaMag_peak_ipi_med_s, uaMag_peak_ipi_cv, gyMag_dfa_alpha, gyMag_hurst_rs, gyMag_lz_c, gyMag_acf_tau_1e_s, gyMag_peak_ipi_cv, actshort[pathB]]
       -> ALL-3 tie (12): frac_act_short_w2_p50, gyMag_acf_tau_1e_s, gyMag_dfa_alpha, gyMag_hurst_rs, gyMag_lz_c, gyMag_peak_ipi_cv, switch_per_min_w2_p50, uaMag_acf_dom_peak, uaMag_hurst_rs, uaMag_lz_c, uaMag_peak_ipi_cv, uaMag_zcr
  G03 size=23 in|rho| min=0.09 med=0.78  [act_bout_cvx12, switch_per_minx6, frac_act_shortx5]
       -> ALL-3 tie (2): act_bout_cv_w1_p50, act_bout_cv_w2_p60
  G04 size=16 in|rho| min=0.42 med=0.82  [uaY_centroid, uaY_spread, uaY_entropy, uaY_bp_mf, uaY_bp_hf, uaZ_spread, uaZ_bp_lf, uaZ_bp_hf, uaMag_skew, uaMag_kurt, gyX_centroid, gyX_spread, gyX_entropy, gyX_bp_lf, gyX_bp_mf, gyX_bp_hf]
       -> ALL-3 tie (16): gyX_bp_hf, gyX_bp_lf, gyX_bp_mf, gyX_centroid, gyX_entropy, gyX_spread, uaMag_kurt, uaMag_skew, uaY_bp_hf, uaY_bp_mf, uaY_centroid, uaY_entropy, uaY_spread, uaZ_bp_hf, uaZ_bp_lf, uaZ_spread
  G05 size= 7 in|rho| min=0.74 med=0.91  [roll_zcr, roll_centroid, roll_spread, roll_entropy, roll_bp_lf, roll_bp_mf, roll_bp_hf]
       -> ALL-3 tie (7): roll_bp_hf, roll_bp_lf, roll_bp_mf, roll_centroid, roll_entropy, roll_spread, roll_zcr
  G06 size= 6 in|rho| min=0.84 med=0.92  [gyY_zcr, gyY_centroid, gyY_spread, gyY_entropy, gyY_bp_mf, gyY_bp_hf]
       -> ALL-3 tie (6): gyY_bp_hf, gyY_bp_mf, gyY_centroid, gyY_entropy, gyY_spread, gyY_zcr
  G07 size= 6 in|rho| min=0.70 med=0.93  [pitch_centroid, pitch_spread, pitch_entropy, pitch_bp_lf, pitch_bp_mf, pitch_bp_hf]
       -> ALL-3 tie (6): pitch_bp_hf, pitch_bp_lf, pitch_bp_mf, pitch_centroid, pitch_entropy, pitch_spread
  G08 size= 6 in|rho| min=0.85 med=0.96  [yaw_std, yaw_var, yaw_rms, yaw_iqr, yaw_mad, yaw_kurt]
       -> ALL-3 tie (6): yaw_iqr, yaw_kurt, yaw_mad, yaw_rms, yaw_std, yaw_var
  G09 size= 6 in|rho| min=0.78 med=0.90  [yaw_centroid, yaw_spread, yaw_entropy, yaw_bp_lf, yaw_bp_mf, yaw_bp_hf]
       -> ALL-3 tie (6): yaw_bp_hf, yaw_bp_lf, yaw_bp_mf, yaw_centroid, yaw_entropy, yaw_spread
  G10 size= 6 in|rho| min=0.54 med=0.84  [actbout_cv[pathB]x6]
       -> ALL-3: actbout_cv_p50  [every member carries an on-record caveat]
  G11 size= 5 in|rho| min=0.89 med=0.95  [gyZ_centroid, gyZ_spread, gyZ_entropy, gyZ_bp_mf, gyZ_bp_hf]
       -> ALL-3 tie (5): gyZ_bp_hf, gyZ_bp_mf, gyZ_centroid, gyZ_entropy, gyZ_spread
  G12 size= 4 in|rho| min=0.82 med=0.92  [uaMag_centroid, uaMag_spread, uaMag_bp_hf, jerk_dfa_alpha]
       -> ALL-3 tie (4): jerk_dfa_alpha, uaMag_bp_hf, uaMag_centroid, uaMag_spread
  G13 size= 4 in|rho| min=0.81 med=0.90  [stl_bout_cvx4]
       -> ALL-3: stl_bout_cv_w2_p50
  G14 size= 3 in|rho| min=0.88 med=0.90  [uaX_spread, uaX_entropy, uaX_bp_hf]
       -> ALL-3 tie (3): uaX_bp_hf, uaX_entropy, uaX_spread
  G15 size= 3 in|rho| min=0.90 med=0.90  [gyX_max, gyMag_max, gyMag_range]
       -> ALL-3 tie (3): gyMag_max, gyMag_range, gyX_max
  G16 size= 3 in|rho| min=1.00 med=1.00  [gyY_std, gyY_var, gyY_rms]
       -> ALL-3 tie (3): gyY_rms, gyY_std, gyY_var
  G17 size= 3 in|rho| min=0.85 med=0.94  [gyMag_centroid, gyMag_entropy, gyMag_bp_mf]
       -> ALL-3 tie (3): gyMag_bp_mf, gyMag_centroid, gyMag_entropy
  G18 size= 3 in|rho| min=0.92 med=0.93  [pitch_mean, pitch_rms, pitch_median]
       -> ALL-3 tie (3): pitch_mean, pitch_median, pitch_rms
  G19 size= 3 in|rho| min=0.89 med=0.92  [roll_mean, roll_median, roll_skew]
       -> ALL-3 tie (3): roll_mean, roll_median, roll_skew
  G20 size= 3 in|rho| min=0.86 med=0.90  [roll_iqr, roll_mad, roll_kurt]
       -> ALL-3 tie (3): roll_iqr, roll_kurt, roll_mad
  G21 size= 3 in|rho| min=0.94 med=0.95  [yaw_mean, yaw_median, yaw_skew]
       -> ALL-3 tie (3): yaw_mean, yaw_median, yaw_skew
  G22 size= 3 in|rho| min=0.88 med=0.92  [jerk_min, jerk_max, jerk_range]
       -> ALL-3 tie (3): jerk_max, jerk_min, jerk_range
  G23 size= 3 in|rho| min=0.82 med=0.90  [uaMag_peak_amp_cv, jerk_hurst_rs, jerk_peak_amp_cv]
       -> ALL-3 tie (3): jerk_hurst_rs, jerk_peak_amp_cv, uaMag_peak_amp_cv
  G24 size= 3 in|rho| min=0.80 med=0.92  [act_bout_cvx3]
       -> ALL-3: act_bout_cv_w2_p40
  G25 size= 3 in|rho| min=0.84 med=0.90  [act_bout_cvx2, frac_act_short]
       -> ALL-3: act_bout_cv_w1_p90
  G26 size= 3 in|rho| min=0.84 med=0.93  [stl_bout_cvx3]
       -> ALL-3 tie (2): stl_bout_cv_w2_p70, stl_bout_cv_w5_p60
  G27 size= 3 in|rho| min=0.86 med=0.91  [stl_bout_cvx3]
       -> ALL-3 tie (2): stl_bout_cv_w10_p60, stl_bout_cv_w5_p70
  G28 size= 2 in|rho| min=0.91 med=0.91  [uaZ_min, uaZ_range]
       -> ALL-3 tie (2): uaZ_min, uaZ_range
  G29 size= 2 in|rho| min=0.91 med=0.91  [uaZ_kurt, jerk_kurt]
       -> ALL-3 tie (2): jerk_kurt, uaZ_kurt
  G30 size= 2 in|rho| min=0.93 med=0.93  [uaZ_entropy, uaZ_bp_mf]
       -> ALL-3 tie (2): uaZ_bp_mf, uaZ_entropy
  G31 size= 2 in|rho| min=1.00 med=1.00  [uaMag_max, uaMag_range]
       -> ALL-3 tie (2): uaMag_max, uaMag_range
  G32 size= 2 in|rho| min=1.00 med=1.00  [gyX_iqr, gyX_mad]
       -> ALL-3 tie (2): gyX_iqr, gyX_mad
  G33 size= 2 in|rho| min=1.00 med=1.00  [gyMag_std, gyMag_var]
       -> ALL-3 tie (2): gyMag_std, gyMag_var
  G34 size= 2 in|rho| min=0.97 med=0.97  [gyMag_skew, gyMag_kurt]
       -> ALL-3 tie (2): gyMag_kurt, gyMag_skew
  G35 size= 2 in|rho| min=0.97 med=0.97  [gyMag_spread, gyMag_bp_hf]
       -> ALL-3 tie (2): gyMag_bp_hf, gyMag_spread
  G36 size= 2 in|rho| min=1.00 med=1.00  [pitch_std, pitch_var]
       -> ALL-3 tie (2): pitch_std, pitch_var
  G37 size= 2 in|rho| min=0.99 med=0.99  [pitch_max, pitch_range]
       -> ALL-3 tie (2): pitch_max, pitch_range
  G38 size= 2 in|rho| min=0.97 med=0.97  [pitch_iqr, pitch_mad]
       -> ALL-3 tie (2): pitch_iqr, pitch_mad
  G39 size= 2 in|rho| min=1.00 med=1.00  [roll_std, roll_var]
       -> ALL-3 tie (2): roll_std, roll_var
  G40 size= 2 in|rho| min=0.91 med=0.91  [jerk_entropy, jerk_bp_lf]
       -> ALL-3 tie (2): jerk_bp_lf, jerk_entropy
  G41 size= 2 in|rho| min=0.90 med=0.90  [uaMag_dfa_alpha, uaMag_acf_tau_1e_s]
       -> ALL-3 tie (2): uaMag_acf_tau_1e_s, uaMag_dfa_alpha
  G42 size= 2 in|rho| min=0.91 med=0.91  [stl_bout_cvx2]
       -> ALL-3: stl_bout_cv_w1_p10
  G43 size= 2 in|rho| min=0.92 med=0.92  [stl_bout_cvx2]
       -> ALL-3 tie (2): stl_bout_cv_w0.5_p40, stl_bout_cv_w1_p30
  G44 size= 2 in|rho| min=0.91 med=0.91  [stl_bout_cvx2]
       -> ALL-3: stl_bout_cv_w1_p90
  G45 size= 2 in|rho| min=0.92 med=0.92  [switch_per_minx2]
       -> ALL-3: switch_per_min_w2_p10
  G46 size= 2 in|rho| min=0.94 med=0.94  [stl_bout_cvx2]
       -> ALL-3 tie (2): stl_bout_cv_w1_p40, stl_bout_cv_w2_p30
  G47 size= 2 in|rho| min=0.91 med=0.91  [stl_bout_cvx2]
       -> ALL-3: stl_bout_cv_w2_p60
  G48 size= 2 in|rho| min=0.92 med=0.92  [switch_per_min, frac_act_short]
       -> ALL-3: switch_per_min_w5_p90
  G49 size= 2 in|rho| min=0.95 med=0.95  [act_bout_median, frac_act_short]
       -> ALL-3: frac_act_short_w10_p60

==============================================================================
[4] CLUSTERS NEEDING A CALL (no unique ALL-3, or caveats)
==============================================================================
  G01  (74 cols; internal |rho| min 0.00 med 0.71)  members by stem: actfrac[pathB]x9, within_win_sdx5, switchmin[pathB]x3, actshort[pathB]x3, uaX_std, uaX_var, uaX_rms, uaX_iqr, uaX_mad, uaX_madiff, uaY_std, uaY_var, uaY_rms, uaY_iqr, uaY_mad, uaY_madiff, uaZ_std, uaZ_var, uaZ_rms, uaZ_iqr, uaZ_mad, uaZ_madiff, uaMag_mean, uaMag_std, uaMag_var, uaMag_rms, uaMag_median, uaMag_iqr, uaMag_mad, uaMag_madiff, gyX_std, gyX_var, gyX_rms, gyX_madiff, gyY_iqr, gyY_mad, gyZ_std, gyZ_var, gyZ_rms, gyZ_iqr, gyZ_mad, gyZ_madiff, gyMag_mean, gyMag_rms, gyMag_median, gyMag_mad, gyMag_madiff, pitch_madiff, jerk_std, jerk_var, jerk_rms, jerk_iqr, jerk_mad, jerk_madiff, uaMag_peak_amp_med, gyMag_peak_amp_med, jerk_peak_amp_med, actbout_med[pathB]
      C1 (nunique=24): actfrac_p10, actfrac_p20, actfrac_p30, actfrac_p40, actfrac_p60, actfrac_p70, actfrac_p80, actfrac_p90, actshort_p20, actshort_p60, actshort_p70, gyMag_mad, gyMag_madiff, gyMag_mean, gyMag_median, gyMag_peak_amp_med, gyMag_rms, gyX_madiff, gyX_rms, gyX_std, gyX_var, gyY_iqr, gyY_mad, gyZ_iqr, gyZ_mad, gyZ_madiff, gyZ_rms, gyZ_std, gyZ_var, jerk_iqr, jerk_mad, jerk_madiff, jerk_peak_amp_med, jerk_rms, jerk_std, jerk_var, pitch_madiff, switchmin_p10, switchmin_p80, switchmin_p90, uaMag_iqr, uaMag_mad, uaMag_madiff, uaMag_mean, uaMag_median, uaMag_peak_amp_med, uaMag_rms, uaMag_std, uaMag_var, uaX_iqr, uaX_mad, uaX_madiff, uaX_rms, uaX_std, uaX_var, uaY_iqr, uaY_mad, uaY_madiff, uaY_rms, uaY_std, uaY_var, uaZ_iqr, uaZ_mad, uaZ_madiff, uaZ_rms, uaZ_std, uaZ_var, within_win_sd_w0.5, within_win_sd_w1, within_win_sd_w10, within_win_sd_w2, within_win_sd_w5
      C2 (min grid dist 0): actfrac_p50, gyMag_mad, gyMag_madiff, gyMag_mean, gyMag_median, gyMag_peak_amp_med, gyMag_rms, gyX_madiff ...
      C3 excluded: actbout_med_p20[R10], actfrac_p10[R10], actfrac_p20[R10], actfrac_p30[R10], actfrac_p40[R10], actfrac_p50[R10], actfrac_p60[R10], actfrac_p70[R10], actfrac_p80[R10], actfrac_p90[R10], actshort_p20[R10], actshort_p60[R10], actshort_p70[R10], switchmin_p10[R10], switchmin_p80[R10], switchmin_p90[R10]
      C1&C2 = gyMag_mad, gyMag_madiff, gyMag_mean, gyMag_median, gyMag_peak_amp_med, gyMag_rms, gyX_madiff, gyX_rms, gyX_std, gyX_var, gyY_iqr, gyY_mad, gyZ_iqr, gyZ_mad, gyZ_madiff, gyZ_rms, gyZ_std, gyZ_var, jerk_iqr, jerk_mad, jerk_madiff, jerk_peak_amp_med, jerk_rms, jerk_std, jerk_var, pitch_madiff, uaMag_iqr, uaMag_mad, uaMag_madiff, uaMag_mean, uaMag_median, uaMag_peak_amp_med, uaMag_rms, uaMag_std, uaMag_var, uaX_iqr, uaX_mad, uaX_madiff, uaX_rms, uaX_std, uaX_var, uaY_iqr, uaY_mad, uaY_madiff, uaY_rms, uaY_std, uaY_var, uaZ_iqr, uaZ_mad, uaZ_madiff, uaZ_rms, uaZ_std, uaZ_var, within_win_sd_w2

  G02  (61 cols; internal |rho| min 0.01 med 0.71)  members by stem: switch_per_minx28, frac_act_shortx17, switchmin[pathB]x4, uaMag_zcr, uaMag_hurst_rs, uaMag_lz_c, uaMag_acf_dom_peak, uaMag_peak_ipi_med_s, uaMag_peak_ipi_cv, gyMag_dfa_alpha, gyMag_hurst_rs, gyMag_lz_c, gyMag_acf_tau_1e_s, gyMag_peak_ipi_cv, actshort[pathB]
      C1 (nunique=24): actshort_p10, frac_act_short_w0.5_p30, frac_act_short_w0.5_p40, frac_act_short_w0.5_p50, frac_act_short_w1_p50, frac_act_short_w1_p70, frac_act_short_w2_p40, frac_act_short_w2_p50, frac_act_short_w2_p60, frac_act_short_w2_p70, frac_act_short_w5_p50, frac_act_short_w5_p70, gyMag_acf_tau_1e_s, gyMag_dfa_alpha, gyMag_hurst_rs, gyMag_lz_c, gyMag_peak_ipi_cv, switch_per_min_w0.5_p20, switch_per_min_w0.5_p30, switch_per_min_w0.5_p40, switch_per_min_w0.5_p50, switch_per_min_w0.5_p60, switch_per_min_w0.5_p70, switch_per_min_w10_p50, switch_per_min_w10_p60, switch_per_min_w10_p70, switch_per_min_w10_p80, switch_per_min_w1_p20, switch_per_min_w1_p30, switch_per_min_w1_p40, switch_per_min_w1_p50, switch_per_min_w1_p60, switch_per_min_w1_p70, switch_per_min_w2_p20, switch_per_min_w2_p30, switch_per_min_w2_p40, switch_per_min_w2_p50, switch_per_min_w2_p60, switch_per_min_w2_p70, switch_per_min_w5_p30, switch_per_min_w5_p40, switch_per_min_w5_p50, switch_per_min_w5_p60, switch_per_min_w5_p70, switch_per_min_w5_p80, switchmin_p40, switchmin_p50, switchmin_p60, switchmin_p70, uaMag_acf_dom_peak, uaMag_hurst_rs, uaMag_lz_c, uaMag_peak_ipi_cv, uaMag_zcr
      C2 (min grid dist 0): frac_act_short_w2_p50, gyMag_acf_tau_1e_s, gyMag_dfa_alpha, gyMag_hurst_rs, gyMag_lz_c, gyMag_peak_ipi_cv, switch_per_min_w2_p50, switchmin_p50 ...
      C3 excluded: actshort_p10[R10], switchmin_p40[R10], switchmin_p50[R10], switchmin_p60[R10], switchmin_p70[R10]
      C1&C2 = frac_act_short_w2_p50, gyMag_acf_tau_1e_s, gyMag_dfa_alpha, gyMag_hurst_rs, gyMag_lz_c, gyMag_peak_ipi_cv, switch_per_min_w2_p50, switchmin_p50, uaMag_acf_dom_peak, uaMag_hurst_rs, uaMag_lz_c, uaMag_peak_ipi_cv, uaMag_zcr

  G03  (23 cols; internal |rho| min 0.09 med 0.78)  members by stem: act_bout_cvx12, switch_per_minx6, frac_act_shortx5
      C1 (nunique=24): act_bout_cv_w0.5_p50, act_bout_cv_w0.5_p60, act_bout_cv_w0.5_p70, act_bout_cv_w0.5_p80, act_bout_cv_w1_p50, act_bout_cv_w1_p60, act_bout_cv_w1_p70, act_bout_cv_w1_p80, act_bout_cv_w2_p60, act_bout_cv_w2_p70, act_bout_cv_w2_p80, act_bout_cv_w5_p70, frac_act_short_w2_p80, switch_per_min_w0.5_p80, switch_per_min_w0.5_p90, switch_per_min_w1_p80, switch_per_min_w1_p90, switch_per_min_w2_p80, switch_per_min_w2_p90
      C2 (min grid dist 1): act_bout_cv_w1_p50, act_bout_cv_w2_p60
      C3 excluded: none
      C1&C2 = act_bout_cv_w1_p50, act_bout_cv_w2_p60

  G04  (16 cols; internal |rho| min 0.42 med 0.82)  members by stem: uaY_centroid, uaY_spread, uaY_entropy, uaY_bp_mf, uaY_bp_hf, uaZ_spread, uaZ_bp_lf, uaZ_bp_hf, uaMag_skew, uaMag_kurt, gyX_centroid, gyX_spread, gyX_entropy, gyX_bp_lf, gyX_bp_mf, gyX_bp_hf
      C1 (nunique=24): gyX_bp_hf, gyX_bp_lf, gyX_bp_mf, gyX_centroid, gyX_entropy, gyX_spread, uaMag_kurt, uaMag_skew, uaY_bp_hf, uaY_bp_mf, uaY_centroid, uaY_entropy, uaY_spread, uaZ_bp_hf, uaZ_bp_lf, uaZ_spread
      C2 (no swept params -- C2 unconstraining): gyX_bp_hf, gyX_bp_lf, gyX_bp_mf, gyX_centroid, gyX_entropy, gyX_spread, uaMag_kurt, uaMag_skew ...
      C3 excluded: none
      C1&C2 = gyX_bp_hf, gyX_bp_lf, gyX_bp_mf, gyX_centroid, gyX_entropy, gyX_spread, uaMag_kurt, uaMag_skew, uaY_bp_hf, uaY_bp_mf, uaY_centroid, uaY_entropy, uaY_spread, uaZ_bp_hf, uaZ_bp_lf, uaZ_spread

  G05  (7 cols; internal |rho| min 0.74 med 0.91)  members by stem: roll_zcr, roll_centroid, roll_spread, roll_entropy, roll_bp_lf, roll_bp_mf, roll_bp_hf
      C1 (nunique=24): roll_bp_hf, roll_bp_lf, roll_bp_mf, roll_centroid, roll_entropy, roll_spread, roll_zcr
      C2 (no swept params -- C2 unconstraining): roll_bp_hf, roll_bp_lf, roll_bp_mf, roll_centroid, roll_entropy, roll_spread, roll_zcr
      C3 excluded: none
      C1&C2 = roll_bp_hf, roll_bp_lf, roll_bp_mf, roll_centroid, roll_entropy, roll_spread, roll_zcr

  G06  (6 cols; internal |rho| min 0.84 med 0.92)  members by stem: gyY_zcr, gyY_centroid, gyY_spread, gyY_entropy, gyY_bp_mf, gyY_bp_hf
      C1 (nunique=24): gyY_bp_hf, gyY_bp_mf, gyY_centroid, gyY_entropy, gyY_spread, gyY_zcr
      C2 (no swept params -- C2 unconstraining): gyY_bp_hf, gyY_bp_mf, gyY_centroid, gyY_entropy, gyY_spread, gyY_zcr
      C3 excluded: none
      C1&C2 = gyY_bp_hf, gyY_bp_mf, gyY_centroid, gyY_entropy, gyY_spread, gyY_zcr

  G07  (6 cols; internal |rho| min 0.70 med 0.93)  members by stem: pitch_centroid, pitch_spread, pitch_entropy, pitch_bp_lf, pitch_bp_mf, pitch_bp_hf
      C1 (nunique=24): pitch_bp_hf, pitch_bp_lf, pitch_bp_mf, pitch_centroid, pitch_entropy, pitch_spread
      C2 (no swept params -- C2 unconstraining): pitch_bp_hf, pitch_bp_lf, pitch_bp_mf, pitch_centroid, pitch_entropy, pitch_spread
      C3 excluded: none
      C1&C2 = pitch_bp_hf, pitch_bp_lf, pitch_bp_mf, pitch_centroid, pitch_entropy, pitch_spread

  G08  (6 cols; internal |rho| min 0.85 med 0.96)  members by stem: yaw_std, yaw_var, yaw_rms, yaw_iqr, yaw_mad, yaw_kurt
      C1 (nunique=24): yaw_iqr, yaw_kurt, yaw_mad, yaw_rms, yaw_std, yaw_var
      C2 (no swept params -- C2 unconstraining): yaw_iqr, yaw_kurt, yaw_mad, yaw_rms, yaw_std, yaw_var
      C3 excluded: none
      C1&C2 = yaw_iqr, yaw_kurt, yaw_mad, yaw_rms, yaw_std, yaw_var

  G09  (6 cols; internal |rho| min 0.78 med 0.90)  members by stem: yaw_centroid, yaw_spread, yaw_entropy, yaw_bp_lf, yaw_bp_mf, yaw_bp_hf
      C1 (nunique=24): yaw_bp_hf, yaw_bp_lf, yaw_bp_mf, yaw_centroid, yaw_entropy, yaw_spread
      C2 (no swept params -- C2 unconstraining): yaw_bp_hf, yaw_bp_lf, yaw_bp_mf, yaw_centroid, yaw_entropy, yaw_spread
      C3 excluded: none
      C1&C2 = yaw_bp_hf, yaw_bp_lf, yaw_bp_mf, yaw_centroid, yaw_entropy, yaw_spread

  G10  (6 cols; internal |rho| min 0.54 med 0.84)  members by stem: actbout_cv[pathB]x6
      C1 (nunique=24): actbout_cv_p20, actbout_cv_p30, actbout_cv_p40, actbout_cv_p50, actbout_cv_p60, actbout_cv_p70
      C2 (min grid dist 0): actbout_cv_p50
      C3 excluded: actbout_cv_p20[R10], actbout_cv_p30[R10], actbout_cv_p40[R10], actbout_cv_p50[R10], actbout_cv_p60[R10], actbout_cv_p70[R10]
      C1&C2 = actbout_cv_p50

  G11  (5 cols; internal |rho| min 0.89 med 0.95)  members by stem: gyZ_centroid, gyZ_spread, gyZ_entropy, gyZ_bp_mf, gyZ_bp_hf
      C1 (nunique=24): gyZ_bp_hf, gyZ_bp_mf, gyZ_centroid, gyZ_entropy, gyZ_spread
      C2 (no swept params -- C2 unconstraining): gyZ_bp_hf, gyZ_bp_mf, gyZ_centroid, gyZ_entropy, gyZ_spread
      C3 excluded: none
      C1&C2 = gyZ_bp_hf, gyZ_bp_mf, gyZ_centroid, gyZ_entropy, gyZ_spread

  G12  (4 cols; internal |rho| min 0.82 med 0.92)  members by stem: uaMag_centroid, uaMag_spread, uaMag_bp_hf, jerk_dfa_alpha
      C1 (nunique=24): jerk_dfa_alpha, uaMag_bp_hf, uaMag_centroid, uaMag_spread
      C2 (no swept params -- C2 unconstraining): jerk_dfa_alpha, uaMag_bp_hf, uaMag_centroid, uaMag_spread
      C3 excluded: none
      C1&C2 = jerk_dfa_alpha, uaMag_bp_hf, uaMag_centroid, uaMag_spread

  G14  (3 cols; internal |rho| min 0.88 med 0.90)  members by stem: uaX_spread, uaX_entropy, uaX_bp_hf
      C1 (nunique=24): uaX_bp_hf, uaX_entropy, uaX_spread
      C2 (no swept params -- C2 unconstraining): uaX_bp_hf, uaX_entropy, uaX_spread
      C3 excluded: none
      C1&C2 = uaX_bp_hf, uaX_entropy, uaX_spread

  G15  (3 cols; internal |rho| min 0.90 med 0.90)  members by stem: gyX_max, gyMag_max, gyMag_range
      C1 (nunique=24): gyMag_max, gyMag_range, gyX_max
      C2 (no swept params -- C2 unconstraining): gyMag_max, gyMag_range, gyX_max
      C3 excluded: none
      C1&C2 = gyMag_max, gyMag_range, gyX_max

  G16  (3 cols; internal |rho| min 1.00 med 1.00)  members by stem: gyY_std, gyY_var, gyY_rms
      C1 (nunique=24): gyY_rms, gyY_std, gyY_var
      C2 (no swept params -- C2 unconstraining): gyY_rms, gyY_std, gyY_var
      C3 excluded: none
      C1&C2 = gyY_rms, gyY_std, gyY_var

  G17  (3 cols; internal |rho| min 0.85 med 0.94)  members by stem: gyMag_centroid, gyMag_entropy, gyMag_bp_mf
      C1 (nunique=24): gyMag_bp_mf, gyMag_centroid, gyMag_entropy
      C2 (no swept params -- C2 unconstraining): gyMag_bp_mf, gyMag_centroid, gyMag_entropy
      C3 excluded: none
      C1&C2 = gyMag_bp_mf, gyMag_centroid, gyMag_entropy

  G18  (3 cols; internal |rho| min 0.92 med 0.93)  members by stem: pitch_mean, pitch_rms, pitch_median
      C1 (nunique=24): pitch_mean, pitch_median, pitch_rms
      C2 (no swept params -- C2 unconstraining): pitch_mean, pitch_median, pitch_rms
      C3 excluded: none
      C1&C2 = pitch_mean, pitch_median, pitch_rms

  G19  (3 cols; internal |rho| min 0.89 med 0.92)  members by stem: roll_mean, roll_median, roll_skew
      C1 (nunique=24): roll_mean, roll_median, roll_skew
      C2 (no swept params -- C2 unconstraining): roll_mean, roll_median, roll_skew
      C3 excluded: none
      C1&C2 = roll_mean, roll_median, roll_skew

  G20  (3 cols; internal |rho| min 0.86 med 0.90)  members by stem: roll_iqr, roll_mad, roll_kurt
      C1 (nunique=24): roll_iqr, roll_kurt, roll_mad
      C2 (no swept params -- C2 unconstraining): roll_iqr, roll_kurt, roll_mad
      C3 excluded: none
      C1&C2 = roll_iqr, roll_kurt, roll_mad

  G21  (3 cols; internal |rho| min 0.94 med 0.95)  members by stem: yaw_mean, yaw_median, yaw_skew
      C1 (nunique=24): yaw_mean, yaw_median, yaw_skew
      C2 (no swept params -- C2 unconstraining): yaw_mean, yaw_median, yaw_skew
      C3 excluded: none
      C1&C2 = yaw_mean, yaw_median, yaw_skew

  G22  (3 cols; internal |rho| min 0.88 med 0.92)  members by stem: jerk_min, jerk_max, jerk_range
      C1 (nunique=24): jerk_max, jerk_min, jerk_range
      C2 (no swept params -- C2 unconstraining): jerk_max, jerk_min, jerk_range
      C3 excluded: none
      C1&C2 = jerk_max, jerk_min, jerk_range

  G23  (3 cols; internal |rho| min 0.82 med 0.90)  members by stem: uaMag_peak_amp_cv, jerk_hurst_rs, jerk_peak_amp_cv
      C1 (nunique=24): jerk_hurst_rs, jerk_peak_amp_cv, uaMag_peak_amp_cv
      C2 (no swept params -- C2 unconstraining): jerk_hurst_rs, jerk_peak_amp_cv, uaMag_peak_amp_cv
      C3 excluded: none
      C1&C2 = jerk_hurst_rs, jerk_peak_amp_cv, uaMag_peak_amp_cv

  G26  (3 cols; internal |rho| min 0.84 med 0.93)  members by stem: stl_bout_cvx3
      C1 (nunique=24): stl_bout_cv_w1_p80, stl_bout_cv_w2_p70, stl_bout_cv_w5_p60
      C2 (min grid dist 2): stl_bout_cv_w2_p70, stl_bout_cv_w5_p60
      C3 excluded: none
      C1&C2 = stl_bout_cv_w2_p70, stl_bout_cv_w5_p60

  G27  (3 cols; internal |rho| min 0.86 med 0.91)  members by stem: stl_bout_cvx3
      C1 (nunique=24): stl_bout_cv_w10_p60, stl_bout_cv_w10_p70, stl_bout_cv_w5_p70
      C2 (min grid dist 3): stl_bout_cv_w10_p60, stl_bout_cv_w5_p70
      C3 excluded: none
      C1&C2 = stl_bout_cv_w10_p60, stl_bout_cv_w5_p70

  G28  (2 cols; internal |rho| min 0.91 med 0.91)  members by stem: uaZ_min, uaZ_range
      C1 (nunique=24): uaZ_min, uaZ_range
      C2 (no swept params -- C2 unconstraining): uaZ_min, uaZ_range
      C3 excluded: none
      C1&C2 = uaZ_min, uaZ_range

  G29  (2 cols; internal |rho| min 0.91 med 0.91)  members by stem: uaZ_kurt, jerk_kurt
      C1 (nunique=24): jerk_kurt, uaZ_kurt
      C2 (no swept params -- C2 unconstraining): jerk_kurt, uaZ_kurt
      C3 excluded: none
      C1&C2 = jerk_kurt, uaZ_kurt

  G30  (2 cols; internal |rho| min 0.93 med 0.93)  members by stem: uaZ_entropy, uaZ_bp_mf
      C1 (nunique=24): uaZ_bp_mf, uaZ_entropy
      C2 (no swept params -- C2 unconstraining): uaZ_bp_mf, uaZ_entropy
      C3 excluded: none
      C1&C2 = uaZ_bp_mf, uaZ_entropy

  G31  (2 cols; internal |rho| min 1.00 med 1.00)  members by stem: uaMag_max, uaMag_range
      C1 (nunique=24): uaMag_max, uaMag_range
      C2 (no swept params -- C2 unconstraining): uaMag_max, uaMag_range
      C3 excluded: none
      C1&C2 = uaMag_max, uaMag_range

  G32  (2 cols; internal |rho| min 1.00 med 1.00)  members by stem: gyX_iqr, gyX_mad
      C1 (nunique=24): gyX_iqr, gyX_mad
      C2 (no swept params -- C2 unconstraining): gyX_iqr, gyX_mad
      C3 excluded: none
      C1&C2 = gyX_iqr, gyX_mad

  G33  (2 cols; internal |rho| min 1.00 med 1.00)  members by stem: gyMag_std, gyMag_var
      C1 (nunique=24): gyMag_std, gyMag_var
      C2 (no swept params -- C2 unconstraining): gyMag_std, gyMag_var
      C3 excluded: none
      C1&C2 = gyMag_std, gyMag_var

  G34  (2 cols; internal |rho| min 0.97 med 0.97)  members by stem: gyMag_skew, gyMag_kurt
      C1 (nunique=24): gyMag_kurt, gyMag_skew
      C2 (no swept params -- C2 unconstraining): gyMag_kurt, gyMag_skew
      C3 excluded: none
      C1&C2 = gyMag_kurt, gyMag_skew

  G35  (2 cols; internal |rho| min 0.97 med 0.97)  members by stem: gyMag_spread, gyMag_bp_hf
      C1 (nunique=24): gyMag_bp_hf, gyMag_spread
      C2 (no swept params -- C2 unconstraining): gyMag_bp_hf, gyMag_spread
      C3 excluded: none
      C1&C2 = gyMag_bp_hf, gyMag_spread

  G36  (2 cols; internal |rho| min 1.00 med 1.00)  members by stem: pitch_std, pitch_var
      C1 (nunique=24): pitch_std, pitch_var
      C2 (no swept params -- C2 unconstraining): pitch_std, pitch_var
      C3 excluded: none
      C1&C2 = pitch_std, pitch_var

  G37  (2 cols; internal |rho| min 0.99 med 0.99)  members by stem: pitch_max, pitch_range
      C1 (nunique=24): pitch_max, pitch_range
      C2 (no swept params -- C2 unconstraining): pitch_max, pitch_range
      C3 excluded: none
      C1&C2 = pitch_max, pitch_range

  G38  (2 cols; internal |rho| min 0.97 med 0.97)  members by stem: pitch_iqr, pitch_mad
      C1 (nunique=24): pitch_iqr, pitch_mad
      C2 (no swept params -- C2 unconstraining): pitch_iqr, pitch_mad
      C3 excluded: none
      C1&C2 = pitch_iqr, pitch_mad

  G39  (2 cols; internal |rho| min 1.00 med 1.00)  members by stem: roll_std, roll_var
      C1 (nunique=24): roll_std, roll_var
      C2 (no swept params -- C2 unconstraining): roll_std, roll_var
      C3 excluded: none
      C1&C2 = roll_std, roll_var

  G40  (2 cols; internal |rho| min 0.91 med 0.91)  members by stem: jerk_entropy, jerk_bp_lf
      C1 (nunique=24): jerk_bp_lf, jerk_entropy
      C2 (no swept params -- C2 unconstraining): jerk_bp_lf, jerk_entropy
      C3 excluded: none
      C1&C2 = jerk_bp_lf, jerk_entropy

  G41  (2 cols; internal |rho| min 0.90 med 0.90)  members by stem: uaMag_dfa_alpha, uaMag_acf_tau_1e_s
      C1 (nunique=24): uaMag_acf_tau_1e_s, uaMag_dfa_alpha
      C2 (no swept params -- C2 unconstraining): uaMag_acf_tau_1e_s, uaMag_dfa_alpha
      C3 excluded: none
      C1&C2 = uaMag_acf_tau_1e_s, uaMag_dfa_alpha

  G43  (2 cols; internal |rho| min 0.92 med 0.92)  members by stem: stl_bout_cvx2
      C1 (nunique=24): stl_bout_cv_w0.5_p40, stl_bout_cv_w1_p30
      C2 (min grid dist 3): stl_bout_cv_w0.5_p40, stl_bout_cv_w1_p30
      C3 excluded: none
      C1&C2 = stl_bout_cv_w0.5_p40, stl_bout_cv_w1_p30

  G46  (2 cols; internal |rho| min 0.94 med 0.94)  members by stem: stl_bout_cvx2
      C1 (nunique=24): stl_bout_cv_w1_p40, stl_bout_cv_w2_p30
      C2 (min grid dist 2): stl_bout_cv_w1_p40, stl_bout_cv_w2_p30
      C3 excluded: none
      C1&C2 = stl_bout_cv_w1_p40, stl_bout_cv_w2_p30

==============================================================================
[5] SUMMARY
==============================================================================
  clusters with a unique all-three column: 10 of 49
  clusters where several columns tie on all three: 39
  clusters where no column satisfies all three: 0

==============================================================================
[6] FULL MEMBERSHIP (for the record)
==============================================================================
  G01 (74): actbout_med_p20, actfrac_p10, actfrac_p20, actfrac_p30, actfrac_p40, actfrac_p50, actfrac_p60, actfrac_p70, actfrac_p80, actfrac_p90, actshort_p20, actshort_p60, actshort_p70, gyMag_mad, gyMag_madiff, gyMag_mean, gyMag_median, gyMag_peak_amp_med, gyMag_rms, gyX_madiff, gyX_rms, gyX_std, gyX_var, gyY_iqr, gyY_mad, gyZ_iqr, gyZ_mad, gyZ_madiff, gyZ_rms, gyZ_std, gyZ_var, jerk_iqr, jerk_mad, jerk_madiff, jerk_peak_amp_med, jerk_rms, jerk_std, jerk_var, pitch_madiff, switchmin_p10, switchmin_p80, switchmin_p90, uaMag_iqr, uaMag_mad, uaMag_madiff, uaMag_mean, uaMag_median, uaMag_peak_amp_med, uaMag_rms, uaMag_std, uaMag_var, uaX_iqr, uaX_mad, uaX_madiff, uaX_rms, uaX_std, uaX_var, uaY_iqr, uaY_mad, uaY_madiff, uaY_rms, uaY_std, uaY_var, uaZ_iqr, uaZ_mad, uaZ_madiff, uaZ_rms, uaZ_std, uaZ_var, within_win_sd_w0.5, within_win_sd_w1, within_win_sd_w10, within_win_sd_w2, within_win_sd_w5
  G02 (61): actshort_p10, frac_act_short_w0.5_p30, frac_act_short_w0.5_p40, frac_act_short_w0.5_p50, frac_act_short_w0.5_p60, frac_act_short_w10_p80, frac_act_short_w1_p40, frac_act_short_w1_p50, frac_act_short_w1_p60, frac_act_short_w1_p70, frac_act_short_w2_p40, frac_act_short_w2_p50, frac_act_short_w2_p60, frac_act_short_w2_p70, frac_act_short_w5_p50, frac_act_short_w5_p60, frac_act_short_w5_p70, frac_act_short_w5_p80, gyMag_acf_tau_1e_s, gyMag_dfa_alpha, gyMag_hurst_rs, gyMag_lz_c, gyMag_peak_ipi_cv, switch_per_min_w0.5_p20, switch_per_min_w0.5_p30, switch_per_min_w0.5_p40, switch_per_min_w0.5_p50, switch_per_min_w0.5_p60, switch_per_min_w0.5_p70, switch_per_min_w10_p50, switch_per_min_w10_p60, switch_per_min_w10_p70, switch_per_min_w10_p80, switch_per_min_w1_p20, switch_per_min_w1_p30, switch_per_min_w1_p40, switch_per_min_w1_p50, switch_per_min_w1_p60, switch_per_min_w1_p70, switch_per_min_w2_p20, switch_per_min_w2_p30, switch_per_min_w2_p40, switch_per_min_w2_p50, switch_per_min_w2_p60, switch_per_min_w2_p70, switch_per_min_w5_p30, switch_per_min_w5_p40, switch_per_min_w5_p50, switch_per_min_w5_p60, switch_per_min_w5_p70, switch_per_min_w5_p80, switchmin_p40, switchmin_p50, switchmin_p60, switchmin_p70, uaMag_acf_dom_peak, uaMag_hurst_rs, uaMag_lz_c, uaMag_peak_ipi_cv, uaMag_peak_ipi_med_s, uaMag_zcr
  G03 (23): act_bout_cv_w0.5_p50, act_bout_cv_w0.5_p60, act_bout_cv_w0.5_p70, act_bout_cv_w0.5_p80, act_bout_cv_w1_p50, act_bout_cv_w1_p60, act_bout_cv_w1_p70, act_bout_cv_w1_p80, act_bout_cv_w2_p60, act_bout_cv_w2_p70, act_bout_cv_w2_p80, act_bout_cv_w5_p70, frac_act_short_w0.5_p70, frac_act_short_w0.5_p80, frac_act_short_w1_p80, frac_act_short_w2_p80, frac_act_short_w2_p90, switch_per_min_w0.5_p80, switch_per_min_w0.5_p90, switch_per_min_w1_p80, switch_per_min_w1_p90, switch_per_min_w2_p80, switch_per_min_w2_p90
  G04 (16): gyX_bp_hf, gyX_bp_lf, gyX_bp_mf, gyX_centroid, gyX_entropy, gyX_spread, uaMag_kurt, uaMag_skew, uaY_bp_hf, uaY_bp_mf, uaY_centroid, uaY_entropy, uaY_spread, uaZ_bp_hf, uaZ_bp_lf, uaZ_spread
  G05 (7): roll_bp_hf, roll_bp_lf, roll_bp_mf, roll_centroid, roll_entropy, roll_spread, roll_zcr
  G06 (6): gyY_bp_hf, gyY_bp_mf, gyY_centroid, gyY_entropy, gyY_spread, gyY_zcr
  G07 (6): pitch_bp_hf, pitch_bp_lf, pitch_bp_mf, pitch_centroid, pitch_entropy, pitch_spread
  G08 (6): yaw_iqr, yaw_kurt, yaw_mad, yaw_rms, yaw_std, yaw_var
  G09 (6): yaw_bp_hf, yaw_bp_lf, yaw_bp_mf, yaw_centroid, yaw_entropy, yaw_spread
  G10 (6): actbout_cv_p20, actbout_cv_p30, actbout_cv_p40, actbout_cv_p50, actbout_cv_p60, actbout_cv_p70
  G11 (5): gyZ_bp_hf, gyZ_bp_mf, gyZ_centroid, gyZ_entropy, gyZ_spread
  G12 (4): jerk_dfa_alpha, uaMag_bp_hf, uaMag_centroid, uaMag_spread
  G13 (4): stl_bout_cv_w0.5_p60, stl_bout_cv_w1_p50, stl_bout_cv_w1_p60, stl_bout_cv_w2_p50
  G14 (3): uaX_bp_hf, uaX_entropy, uaX_spread
  G15 (3): gyMag_max, gyMag_range, gyX_max
  G16 (3): gyY_rms, gyY_std, gyY_var
  G17 (3): gyMag_bp_mf, gyMag_centroid, gyMag_entropy
  G18 (3): pitch_mean, pitch_median, pitch_rms
  G19 (3): roll_mean, roll_median, roll_skew
  G20 (3): roll_iqr, roll_kurt, roll_mad
  G21 (3): yaw_mean, yaw_median, yaw_skew
  G22 (3): jerk_max, jerk_min, jerk_range
  G23 (3): jerk_hurst_rs, jerk_peak_amp_cv, uaMag_peak_amp_cv
  G24 (3): act_bout_cv_w0.5_p40, act_bout_cv_w1_p40, act_bout_cv_w2_p40
  G25 (3): act_bout_cv_w0.5_p90, act_bout_cv_w1_p90, frac_act_short_w1_p90
  G26 (3): stl_bout_cv_w1_p80, stl_bout_cv_w2_p70, stl_bout_cv_w5_p60
  G27 (3): stl_bout_cv_w10_p60, stl_bout_cv_w10_p70, stl_bout_cv_w5_p70
  G28 (2): uaZ_min, uaZ_range
  G29 (2): jerk_kurt, uaZ_kurt
  G30 (2): uaZ_bp_mf, uaZ_entropy
  G31 (2): uaMag_max, uaMag_range
  G32 (2): gyX_iqr, gyX_mad
  G33 (2): gyMag_std, gyMag_var
  G34 (2): gyMag_kurt, gyMag_skew
  G35 (2): gyMag_bp_hf, gyMag_spread
  G36 (2): pitch_std, pitch_var
  G37 (2): pitch_max, pitch_range
  G38 (2): pitch_iqr, pitch_mad
  G39 (2): roll_std, roll_var
  G40 (2): jerk_bp_lf, jerk_entropy
  G41 (2): uaMag_acf_tau_1e_s, uaMag_dfa_alpha
  G42 (2): stl_bout_cv_w0.5_p10, stl_bout_cv_w1_p10
  G43 (2): stl_bout_cv_w0.5_p40, stl_bout_cv_w1_p30
  G44 (2): stl_bout_cv_w0.5_p90, stl_bout_cv_w1_p90
  G45 (2): switch_per_min_w1_p10, switch_per_min_w2_p10
  G46 (2): stl_bout_cv_w1_p40, stl_bout_cv_w2_p30
  G47 (2): stl_bout_cv_w1_p70, stl_bout_cv_w2_p60
  G48 (2): frac_act_short_w5_p90, switch_per_min_w5_p90
  G49 (2): act_bout_median_w10_p60, frac_act_short_w10_p60

```
