# feature_inventory.md -- verbatim stdout snapshot

**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.

- Producing script: `analysis/70_feature_inventory.py`
- Repository HEAD when this snapshot was generated: `b38d9a13537df86cfb35f41bbcdd2f5f1b03d152`
- Reproduce with: `.venv/bin/python analysis/70_feature_inventory.py`

```text

==============================================================================
[1] SHAPE / KEY / DTYPES
==============================================================================
  file: analysis/features.csv
  shape: 24 rows x 609 columns
  key column: 'subject' (24 unique of 24)
  feature columns: 608
  non-numeric feature columns: 0

==============================================================================
[2] FAMILY DECOMPOSITION BY NAMING RULE (asserted, not assumed)
==============================================================================
  channel_stat    251
  pathA_tstruct   275
  pathB_tstruct    45
  nonlinear        36
  rec_dur           1
  UNCLASSIFIED      0
  assertion passed: 251 + 275 + 45 + 36 + 1 = 608

  channel_stat columns per channel:
    uaX     21
    uaY     21
    uaZ     21
    uaMag   21
    gyX     21
    gyY     21
    gyZ     21
    gyMag   21
    pitch   21
    roll    21
    yaw     21
    jerk    20
  negative-control column present: True  ('uaMag_median')

==============================================================================
[3] MISSING VALUES
==============================================================================
  columns with any NaN: 0 of 608

==============================================================================
[4] DEGENERATE / DISCRETE COLUMNS
==============================================================================
  constant columns (1 unique value): 0
  columns with <=  2 unique values (of 24): 2
  columns with <=  3 unique values (of 24): 12
  columns with <=  4 unique values (of 24): 31
  columns with <=  5 unique values (of 24): 46
  columns with <= 10 unique values (of 24): 77

  the 46 columns with <= 5 unique values, by family:
    pathA_tstruct   46

  worst 15 (fewest unique values):
    stl_bout_median_w2_p10       2 unique   family=pathA_tstruct
    act_bout_median_w0.5_p90     2 unique   family=pathA_tstruct
    act_bout_median_w2_p90       3 unique   family=pathA_tstruct
    act_bout_median_w2_p80       3 unique   family=pathA_tstruct
    act_bout_median_w1_p90       3 unique   family=pathA_tstruct
    stl_bout_median_w2_p20       3 unique   family=pathA_tstruct
    stl_bout_median_w5_p10       3 unique   family=pathA_tstruct
    stl_bout_median_w2_p40       3 unique   family=pathA_tstruct
    act_bout_median_w0.5_p60     3 unique   family=pathA_tstruct
    stl_bout_median_w5_p30       3 unique   family=pathA_tstruct
    stl_bout_median_w0.5_p40     3 unique   family=pathA_tstruct
    stl_bout_median_w5_p40       3 unique   family=pathA_tstruct
    act_bout_median_w2_p40       4 unique   family=pathA_tstruct
    stl_bout_median_w2_p50       4 unique   family=pathA_tstruct
    act_bout_median_w5_p80       4 unique   family=pathA_tstruct

==============================================================================
[5] REDUNDANCY -- pairwise |Spearman| on the 24 subjects
==============================================================================
  computed on 608 columns (0 NaN-bearing columns excluded from the matrix, listed in [3])
  feature pairs total: 184528
  pairs with |rho| >= 0.999:     27
  pairs with |rho| >= 0.99 :     40
  pairs with |rho| >= 0.95 :    167
  pairs with |rho| >= 0.9  :    605
  pairs with |rho| >= 0.8  :   2621
  features having at least one partner |rho| >= 0.95: 162 of 608
  features having at least one partner |rho| >= 0.90: 310 of 608

  connected components at |rho| >= 0.95: 498 groups (from 608 features)
    singletons: 446   largest group: 26
    group-size distribution (size: how many groups): {1: np.int64(446), 2: np.int64(35), 3: np.int64(9), 4: np.int64(2), 5: np.int64(3), 6: np.int64(1), 10: np.int64(1), 26: np.int64(1)}

  connected components at |rho| >= 0.9: 347 groups (from 608 features)
    singletons: 298   largest group: 74
    group-size distribution (size: how many groups): {1: np.int64(298), 2: np.int64(22), 3: np.int64(14), 4: np.int64(2), 5: np.int64(1), 6: np.int64(5), 7: np.int64(1), 16: np.int64(1), 23: np.int64(1), 61: np.int64(1), 74: np.int64(1)}

==============================================================================
[6] EXACT-DUPLICATE CHECK (identical values, not just rank-identical)
==============================================================================
  exact duplicate column pairs: 0

```
