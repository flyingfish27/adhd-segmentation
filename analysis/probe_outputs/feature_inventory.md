# feature_inventory.md -- verbatim stdout snapshot

**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.

- Producing script: `analysis/70_feature_inventory.py`
- Repository HEAD when this snapshot was generated: `5a89d4bcf21e8e08357f269b33230d09752f3bd4`
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
[4b] NEAR-CONSTANT: MODE DOMINANCE (exact ties among the 24 values)
==============================================================================
  'mode_n' = subjects sharing the single most frequent value (of 24).
  a constant column would be mode_n = 24; measured max is 22.

  distribution:
    columns with mode_n >= 24:   0
    columns with mode_n >= 23:   0
    columns with mode_n >= 22:   1
    columns with mode_n >= 20:   4
    columns with mode_n >= 18:   9
    columns with mode_n >= 16:  20
    columns with mode_n >= 14:  32
    columns with mode_n >= 12:  44

  full list of the 44 columns with mode_n >= 12 (most frequent value shared by half the sample or more):
    column                       mode_n  nunique   mode value  family
    act_bout_median_w2_p90         22/24        3            2  pathA_tstruct
    act_bout_median_w1_p90         20/24        3            1  pathA_tstruct
    stl_bout_median_w5_p10         20/24        3            5  pathA_tstruct
    act_bout_median_w5_p80         20/24        4            5  pathA_tstruct
    stl_bout_median_w10_p30        19/24        4           10  pathA_tstruct
    act_bout_median_w0.5_p90       19/24        2          0.5  pathA_tstruct
    act_bout_median_w10_p70        18/24        4           10  pathA_tstruct
    stl_bout_median_w10_p20        18/24        5           10  pathA_tstruct
    act_bout_median_w2_p70         18/24        4            3  pathA_tstruct
    stl_bout_median_w0.5_p10       17/24        5         0.75  pathA_tstruct
    stl_bout_median_w2_p40         17/24        3            3  pathA_tstruct
    stl_bout_median_w5_p20         17/24        5            5  pathA_tstruct
    stl_bout_median_w5_p40         17/24        3          7.5  pathA_tstruct
    act_bout_median_w2_p80         17/24        3            2  pathA_tstruct
    stl_bout_median_w5_p50         16/24        4          7.5  pathA_tstruct
    act_bout_median_w5_p70         16/24        4            5  pathA_tstruct
    act_bout_median_w5_p90         16/24        6            5  pathA_tstruct
    frac_act_short_w0.5_p90        16/24        9            1  pathA_tstruct
    act_bout_median_w10_p80        16/24        5           10  pathA_tstruct
    stl_bout_median_w1_p40         16/24        4          1.5  pathA_tstruct
    stl_bout_median_w5_p30         15/24        3            5  pathA_tstruct
    stl_bout_median_w10_p10        15/24        5           10  pathA_tstruct
    act_bout_median_w10_p90        15/24        5           10  pathA_tstruct
    stl_bout_median_w0.5_p30       15/24        4         0.75  pathA_tstruct
    stl_bout_median_w0.5_p40       15/24        3         0.75  pathA_tstruct
    stl_bout_median_w1_p10         15/24        4          1.5  pathA_tstruct
    act_bout_median_w1_p70         14/24        5          1.5  pathA_tstruct
    stl_bout_median_w2_p30         14/24        5            3  pathA_tstruct
    stl_bout_median_w2_p20         14/24        3            3  pathA_tstruct
    stl_bout_median_w2_p10         14/24        2            2  pathA_tstruct
    act_bout_median_w5_p40         14/24        7           10  pathA_tstruct
    act_bout_median_w0.5_p80       14/24        4         0.75  pathA_tstruct
    stl_bout_median_w10_p70        13/24        5           20  pathA_tstruct
    act_bout_median_w0.5_p70       13/24        5         0.75  pathA_tstruct
    act_bout_median_w5_p60         13/24        6          7.5  pathA_tstruct
    frac_act_short_w1_p90          13/24       12            1  pathA_tstruct
    act_bout_median_w2_p50         13/24        4            4  pathA_tstruct
    stl_bout_median_w1_p20         12/24        4          1.5  pathA_tstruct
    stl_bout_median_w2_p50         12/24        4            3  pathA_tstruct
    act_bout_median_w1_p80         12/24        4          1.5  pathA_tstruct
    act_bout_median_w5_p50         12/24        6          7.5  pathA_tstruct
    stl_bout_median_w0.5_p60       12/24        6            1  pathA_tstruct
    act_bout_median_w0.5_p60       12/24        3         0.75  pathA_tstruct
    act_bout_median_w2_p60         12/24        4            3  pathA_tstruct

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
