# dedup_095.md -- verbatim stdout snapshot

**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.

- Producing script: `analysis/70c_dedup_095_greedy.py`
- Repository HEAD when this snapshot was generated: `90e0e9e288342e53b298bd25baa502c7b82160c4`
- Reproduce with: `.venv/bin/python analysis/70c_dedup_095_greedy.py`

```text

==============================================================================
[1] INPUT SET AFTER FS-D1 + FS-D3
==============================================================================
  working set: 574 columns (608 - 1 - 33)
  consistency with FS-D3: max pairwise |rho| = 0.9878 (< 0.99)
  pairs at |rho| >= 0.95: 106

==============================================================================
[2] GREEDY SCAN IN THE DECLARED PRIORITY ORDER
==============================================================================
  scanned 574 columns; kept 512, dropped 62

  every dropped column with its kept partner:
    drop act_bout_cv_w1_p70           kept twin act_bout_cv_w0.5_p60         |rho|=0.963
    drop act_bout_cv_w2_p70           kept twin act_bout_cv_w2_p60           |rho|=0.963
    drop actbout_cv_p60               kept twin actbout_cv_p50               |rho|=0.950
    drop actfrac_p10                  kept twin jerk_iqr                     |rho|=0.977
    drop actfrac_p20                  kept twin jerk_iqr                     |rho|=0.960
    drop actfrac_p40                  kept twin gyZ_iqr                      |rho|=0.970
    drop actfrac_p50                  kept twin gyZ_iqr                      |rho|=0.964
    drop actfrac_p60                  kept twin uaMag_median                 |rho|=0.955
    drop actfrac_p70                  kept twin uaMag_mean                   |rho|=0.957
    drop actfrac_p80                  kept twin uaMag_mean                   |rho|=0.974
    drop actfrac_p90                  kept twin actshort_p60                 |rho|=0.950
    drop frac_act_short_w0.5_p60      kept twin frac_act_short_w1_p60        |rho|=0.950
    drop frac_act_short_w5_p80        kept twin switch_per_min_w5_p80        |rho|=0.968
    drop gyMag_entropy                kept twin gyMag_centroid               |rho|=0.956
    drop gyMag_hurst_rs               kept twin gyMag_dfa_alpha              |rho|=0.964
    drop gyMag_kurt                   kept twin gyMag_skew                   |rho|=0.966
    drop gyMag_median                 kept twin uaMag_median                 |rho|=0.965
    drop gyMag_peak_amp_med           kept twin gyMag_mad                    |rho|=0.955
    drop gyMag_spread                 kept twin gyMag_bp_hf                  |rho|=0.974
    drop gyX_entropy                  kept twin gyX_bp_lf                    |rho|=0.975
    drop gyX_madiff                   kept twin gyMag_madiff                 |rho|=0.959
    drop gyX_spread                   kept twin gyX_bp_hf                    |rho|=0.967
    drop gyY_centroid                 kept twin gyY_bp_hf                    |rho|=0.962
    drop gyZ_centroid                 kept twin gyZ_bp_mf                    |rho|=0.955
    drop gyZ_entropy                  kept twin gyZ_bp_mf                    |rho|=0.953
    drop jerk_madiff                  kept twin uaMag_mean                   |rho|=0.955
    drop jerk_peak_amp_med            kept twin uaMag_median                 |rho|=0.965
    drop jerk_range                   kept twin jerk_min                     |rho|=0.986
    drop pitch_centroid               kept twin pitch_bp_lf                  |rho|=0.953
    drop pitch_entropy                kept twin pitch_bp_lf                  |rho|=0.955
    drop pitch_mad                    kept twin pitch_iqr                    |rho|=0.967
    drop roll_bp_mf                   kept twin roll_bp_hf                   |rho|=0.973
    drop roll_centroid                kept twin roll_bp_hf                   |rho|=0.983
    drop roll_entropy                 kept twin roll_zcr                     |rho|=0.954
    drop switch_per_min_w0.5_p30      kept twin switch_per_min_w0.5_p40      |rho|=0.957
    drop switch_per_min_w0.5_p50      kept twin switch_per_min_w1_p50        |rho|=0.960
    drop switch_per_min_w0.5_p60      kept twin switch_per_min_w1_p50        |rho|=0.954
    drop switch_per_min_w1_p30        kept twin switch_per_min_w0.5_p40      |rho|=0.958
    drop switch_per_min_w1_p70        kept twin switch_per_min_w1_p60        |rho|=0.957
    drop switch_per_min_w2_p60        kept twin frac_act_short_w2_p60        |rho|=0.952
    drop switch_per_min_w2_p70        kept twin frac_act_short_w2_p70        |rho|=0.963
    drop switchmin_p50                kept twin uaMag_lz_c                   |rho|=0.976
    drop switchmin_p90                kept twin uaMag_peak_amp_med           |rho|=0.964
    drop uaMag_centroid               kept twin uaMag_bp_hf                  |rho|=0.973
    drop uaMag_kurt                   kept twin uaMag_skew                   |rho|=0.954
    drop uaX_iqr                      kept twin uaMag_median                 |rho|=0.963
    drop uaX_spread                   kept twin uaX_bp_hf                    |rho|=0.959
    drop uaY_iqr                      kept twin uaMag_median                 |rho|=0.959
    drop uaY_mad                      kept twin gyZ_iqr                      |rho|=0.954
    drop uaY_spread                   kept twin uaY_bp_hf                    |rho|=0.951
    drop uaZ_iqr                      kept twin uaMag_median                 |rho|=0.984
    drop uaZ_mad                      kept twin gyZ_iqr                      |rho|=0.965
    drop uaZ_spread                   kept twin uaZ_bp_hf                    |rho|=0.973
    drop within_win_sd_w0.5           kept twin uaMag_median                 |rho|=0.951
    drop within_win_sd_w1             kept twin within_win_sd_w2             |rho|=0.952
    drop within_win_sd_w5             kept twin within_win_sd_w2             |rho|=0.967
    drop yaw_bp_mf                    kept twin yaw_bp_hf                    |rho|=0.987
    drop yaw_centroid                 kept twin yaw_bp_hf                    |rho|=0.957
    drop yaw_iqr                      kept twin yaw_std                      |rho|=0.977
    drop yaw_mad                      kept twin yaw_kurt                     |rho|=0.966
    drop yaw_rms                      kept twin yaw_std                      |rho|=0.956
    drop yaw_skew                     kept twin yaw_median                   |rho|=0.983

==============================================================================
[3] RESULT
==============================================================================
  working set after FS-D4: 574 - 62 = 512 columns
  dropped-vs-kept |rho|: min=0.950 median=0.962 max=0.987
  dropped, by family: {'pathA': 14, 'pathB': 11, 'channel': 34, 'nonlinear': 3}
  remaining, by family: {'channel': 184, 'pathA': 261, 'nonlinear': 33, 'pathB': 34}
  protected column still present: uaMag_median: True
  protected column still present: frac_act_short_w10_p20: True
  protected column still present: act_bout_median_w0.5_p80: True
  verification: max pairwise |rho| among kept = 0.9496 (must be < 0.95)

```
