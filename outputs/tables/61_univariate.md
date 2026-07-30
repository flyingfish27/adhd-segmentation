# 61_univariate.md -- verbatim stdout snapshot

**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.

- Producing script: `analysis/61_univariate_analysis.py`
- Repository HEAD when this snapshot was generated: `558177fc103baccb6b74ef91a2ecc8fb2dfcf858`
- Reproduce with: `.venv/bin/python analysis/61_univariate_analysis.py`
- Permutation nulls rebuilt here use 100,000 draws per target, seed 20260730. The screen
  itself used seed 20260717, so permutation p-values agree only to Monte-Carlo error.

```text

==============================================================================
[1] REBUILDING THE PERMUTATION NULLS USED BY THE SCREEN
==============================================================================
  cohort n = 24;  permutations per null = 100,000;  seed = 20260730
  One null per target. The null depends on the target only (through ties or
  group sizes), never on the feature -- that is why 608 features share it.

  target                   kind   null p95  null p99  null max  detail
  sdq_cond                 cont      0.403     0.515     0.758  5 distinct values of 24, 19 tied
  sdq_emo                  cont      0.406     0.522     0.820  6 distinct values of 24, 18 tied
  sdq_hyper                cont      0.406     0.520     0.770  8 distinct values of 24, 16 tied
  sdq_peer                 cont      0.405     0.516     0.755  4 distinct values of 24, 20 tied
  sdq_pro                  cont      0.407     0.522     0.847  6 distinct values of 24, 18 tied
  sdq_totdiff              cont      0.405     0.521     0.805  11 distinct values of 24, 13 tied
  snap_adhd_total          cont      0.407     0.518     0.752  15 distinct values of 24, 9 tied
  snap_hyper               cont      0.406     0.520     0.766  9 distinct values of 24, 15 tied
  snap_inatt               cont      0.405     0.521     0.784  11 distinct values of 24, 13 tied
  snap_odd                 cont      0.407     0.522     0.792  11 distinct values of 24, 13 tied
  sdq_cond__qbin           bin       0.250     0.320     0.500  group sizes 16 / 8
  sdq_emo__qbin            bin       0.236     0.306     0.486  group sizes 12 / 12
  sdq_hyper__qbin          bin       0.236     0.307     0.471  group sizes 14 / 10
  sdq_peer__qbin           bin       0.269     0.343     0.500  group sizes 18 / 6
  sdq_pro__qbin            bin       0.241     0.315     0.463  group sizes 15 / 9
  sdq_totdiff__qbin        bin       0.241     0.307     0.485  group sizes 15 / 9
  snap_adhd_total__qbin    bin       0.236     0.306     0.479  group sizes 12 / 12
  snap_hyper__qbin         bin       0.234     0.304     0.479  group sizes 13 / 11
  snap_inatt__qbin         bin       0.236     0.299     0.486  group sizes 12 / 12
  snap_odd__qbin           bin       0.241     0.315     0.463  group sizes 15 / 9

==============================================================================
[2] VERIFICATION -- recomputing published cells from features.csv and the targets
==============================================================================
  20 randomly chosen continuous cells and 20 binary cells are recomputed here
  with an independent implementation of the same statistic.

  target                 feature                         published  recomputed       diff
  sdq_pro                uaZ_range                       -0.055441   -0.055441   6.94e-18
  snap_adhd_total        stl_bout_cv_w0.5_p30             0.317559    0.317559   5.55e-17
  sdq_cond               gyMag_bp_hf                     -0.235276   -0.235276   0.00e+00
  sdq_hyper              act_bout_median_w5_p20          -0.233319   -0.233319   0.00e+00
  snap_inatt             stl_bout_cv_w2_p80               0.126508    0.126508   8.33e-17
  snap_adhd_total        gyMag_bp_lf                      0.209816    0.209816   2.78e-17
  snap_hyper             act_bout_median_w10_p40         -0.026335   -0.026335   6.94e-18
  snap_odd               act_bout_median_w5_p20          -0.237043   -0.237043   2.78e-17
  snap_odd               act_bout_cv_w0.5_p20            -0.170767   -0.170767   2.78e-17
  snap_odd               roll_min                         0.135025    0.135025   0.00e+00
  sdq_peer               stl_bout_median_w0.5_p80         0.101567    0.101567   4.16e-17
  sdq_cond               uaMag_max                       -0.508233   -0.508233   0.00e+00
  snap_inatt             uaZ_entropy                      0.259581    0.259581   0.00e+00
  sdq_totdiff            switch_per_min_w5_p60            0.005277    0.005277   8.67e-19
  sdq_pro                frac_act_short_w1_p60           -0.050043   -0.050043   0.00e+00
  sdq_pro                actfrac_p10                     -0.123053   -0.123053   5.55e-17
  snap_odd               actbout_med_p70                 -0.111539   -0.111539   8.33e-17
  sdq_pro                gyX_std                          0.119447    0.119447   0.00e+00
  snap_odd               gyZ_madiff                      -0.318588   -0.318588   0.00e+00
  sdq_cond               frac_act_short_w2_p20            0.196217    0.196217   0.00e+00
  sdq_pro__qbin          uaZ_range                        0.466667    0.466667   0.00e+00
  snap_adhd_total__qbin  stl_bout_cv_w0.5_p30             0.576389    0.576389   0.00e+00
  sdq_cond__qbin         gyMag_bp_hf                      0.234375    0.234375   0.00e+00
  sdq_hyper__qbin        act_bout_median_w5_p20           0.342857    0.342857   5.55e-17
  snap_inatt__qbin       stl_bout_cv_w2_p80               0.541667    0.541667   0.00e+00
  snap_adhd_total__qbin  gyMag_bp_lf                      0.618056    0.618056   0.00e+00
  snap_hyper__qbin       act_bout_median_w10_p40          0.524476    0.524476   0.00e+00
  snap_odd__qbin         act_bout_median_w5_p20           0.403704    0.403704   5.55e-17
  snap_odd__qbin         act_bout_cv_w0.5_p20             0.274074    0.274074   0.00e+00
  snap_odd__qbin         roll_min                         0.592593    0.592593   0.00e+00
  sdq_peer__qbin         stl_bout_median_w0.5_p80         0.537037    0.537037   0.00e+00
  sdq_cond__qbin         uaMag_max                        0.218750    0.218750   0.00e+00
  snap_inatt__qbin       uaZ_entropy                      0.659722    0.659722   0.00e+00
  sdq_totdiff__qbin      switch_per_min_w5_p60            0.474074    0.474074   0.00e+00
  sdq_pro__qbin          frac_act_short_w1_p60            0.592593    0.592593   0.00e+00
  sdq_pro__qbin          actfrac_p10                      0.562963    0.562963   0.00e+00
  snap_odd__qbin         actbout_med_p70                  0.374074    0.374074   5.55e-17
  sdq_pro__qbin          gyX_std                          0.555556    0.555556   0.00e+00
  snap_odd__qbin         gyZ_madiff                       0.318519    0.318519   5.55e-17
  sdq_cond__qbin         frac_act_short_w2_p20            0.554688    0.554688   0.00e+00

  largest disagreement, Spearman rho cells : 8.33e-17
  largest disagreement, AUC cells          : 5.55e-17
  verdict: the published effect sizes reproduce from the committed inputs

  The permutation p-values are also recomputed, from this script's own nulls.
  Exact equality is not expected: perm_p is a Monte-Carlo quantity and this
  script draws a fresh sample with a different seed. What is checked is that
  the two agree to within Monte-Carlo error.
    cells compared                     : 12160
    identical                          : 23
    differing by <= 0.002              : 8909
    largest difference                 : 0.02786
    Spearman correlation of the two    : 0.999934
    cells on the same side of p < 0.05 : 12152 of 12160

==============================================================================
[3] CONTINUOUS TARGETS -- 6,080 observed |Spearman rho| against the null
==============================================================================
  target                   median |rho|  null med  max |rho|   >p95   exp  ratio   >p99   exp
  sdq_cond                        0.148     0.143      0.668     57    30   1.87     19     6
  sdq_emo                         0.158     0.144      0.772     23    30   0.76      5     6
  sdq_hyper                       0.146     0.144      0.590     16    30   0.53      3     6
  sdq_peer                        0.127     0.145      0.618     17    30   0.56      6     6
  sdq_pro                         0.148     0.143      0.572     20    30   0.66      3     6
  sdq_totdiff                     0.142     0.144      0.528     15    30   0.49      1     6
  snap_adhd_total                 0.160     0.144      0.772     43    30   1.41      8     6
  snap_hyper                      0.161     0.144      0.720     44    30   1.45      8     6
  snap_inatt                      0.135     0.143      0.767     25    30   0.82      2     6
  snap_odd                        0.125     0.144      0.538      7    30   0.23      1     6
  TOTAL                           0.145     0.144      0.772    267   304   0.88     56    61

  'exp' is the count expected if every cell were drawn from the null.
  The 608 features are strongly correlated with one another (same channel,
  adjacent percentile and window settings), so these counts are NOT 608
  independent trials. The null curve is the correct reference for the shape and
  location of the observed distribution, not for a count-based significance test.

  wrote /Users/shiyu/Projects/adhd-segmentation/outputs/figures/fig03_effect_vs_null_continuous.png

==============================================================================
[4] BINARY TARGETS -- 6,080 observed |AUC - 0.5| against per-target nulls
==============================================================================
  Kept separate from the continuous half for two reasons:
    1. the null depends on the group sizes, which differ from target to target
       (12/12 up to 18/6), so one pooled reference line would be wrong;
    2. |AUC - 0.5| lives in [0, 0.5] while |rho| lives in [0, 1] -- the two
       axes are not interchangeable and are never drawn on a shared scale here.

  target                     split  med |AUC-.5|  null med     max   >p95   exp  ratio   >p99
  sdq_cond__qbin              16/8         0.104     0.086   0.414     84    30   2.76     21
  sdq_emo__qbin              12/12         0.069     0.083   0.333     11    30   0.36      2
  sdq_hyper__qbin            14/10         0.086     0.086   0.350     49    30   1.61      4
  sdq_peer__qbin              18/6         0.074     0.093   0.389     26    30   0.86      6
  sdq_pro__qbin               15/9         0.063     0.085   0.307     10    30   0.33      0
  sdq_totdiff__qbin           15/9         0.081     0.085   0.396     33    30   1.09      6
  snap_adhd_total__qbin      12/12         0.090     0.083   0.396     17    30   0.56      1
  snap_hyper__qbin           13/11         0.108     0.080   0.318     26    30   0.86      2
  snap_inatt__qbin           12/12         0.076     0.083   0.368     32    30   1.05      1
  snap_odd__qbin              15/9         0.085     0.085   0.367     28    30   0.92      1
  TOTAL                                                               316   304   1.04     44

  wrote /Users/shiyu/Projects/adhd-segmentation/outputs/figures/fig04_effect_vs_null_binary.png

==============================================================================
[5] MULTIPLE COMPARISONS -- BH-FDR within each target family
==============================================================================
  family definition, read off the data: one family per target, m = 608 features, 20 families.
  verification of the published q_fdr column against an independent BH
    implementation: largest disagreement over all 12160 cells = 5.462e-14
    verdict: reproduces exactly

  permutation resolution: the smallest p the screen can report is 1/NPERM = 1.0e-05
  cells sitting exactly on that floor: 3
  best attainable q for a single cell = floor * m / 1 = 0.0061  (so one cell alone can pass q < 0.05)

  target                    min perm_p  min q_fdr  q<0.05  q<0.10  p<0.05   exp
  sdq_cond                     5.5e-04     0.2310       0       0      57    30
  sdq_emo                      1.0e-05     0.0061       1       1      21    30
  sdq_hyper                    2.9e-03     0.9217       0       0      17    30
  sdq_peer                     1.4e-03     0.8330       0       0      17    30
  sdq_pro                      4.2e-03     0.9159       0       0      20    30
  sdq_totdiff                  8.8e-03     0.9753       0       0      15    30
  snap_adhd_total              1.0e-05     0.0061       1       1      44    30
  snap_hyper                   1.0e-04     0.0608       0       1      45    30
  snap_inatt                   1.0e-05     0.0061       1       1      25    30
  snap_odd                     7.4e-03     0.9937       0       0      10    30
  sdq_cond__qbin               3.8e-04     0.1271       0       0      91    30
  sdq_emo__qbin                3.8e-03     0.9639       0       0      11    30
  sdq_hyper__qbin              2.5e-03     0.5039       0       0      49    30
  sdq_peer__qbin               3.0e-03     0.5423       0       0      28    30
  sdq_pro__qbin                1.0e-02     0.9797       0       0      10    30
  sdq_totdiff__qbin            6.9e-04     0.2098       0       0      33    30
  snap_adhd_total__qbin        3.8e-04     0.2310       0       0      20    30
  snap_hyper__qbin             5.8e-03     0.6746       0       0      27    30
  snap_inatt__qbin             1.1e-03     0.6688       0       0      36    30
  snap_odd__qbin               1.9e-03     0.8837       0       0      28    30
  TOTAL                                                 3       4     604   608

  cells surviving BH-FDR at q < 0.05: 3 of 12160
  target                   type  feature                           rho     auc    perm_p    q_fdr  loo_r2cv
  snap_inatt               cont  frac_act_short_w10_p20          0.767       -   1.0e-05   0.0061     0.376
  snap_adhd_total          cont  frac_act_short_w10_p20          0.772       -   1.0e-05   0.0061     0.381
  sdq_emo                  cont  act_bout_median_w0.5_p80        0.772       -   1.0e-05   0.0061     0.611

  Every surviving cell sits on the permutation floor, meaning 100,000 shuffles
  never produced an effect as large. The true p is smaller than 1e-5 but by how
  much is not resolved by this many permutations.

  wrote /Users/shiyu/Projects/adhd-segmentation/outputs/figures/fig05_fdr_per_target.png

==============================================================================
[6] GENERALISATION -- leave-one-out R^2 against in-sample |rho| (continuous half)
==============================================================================
  MODEL_MENU.md section 4 trap 1: rho is not generalisation evidence, because the
  leave-one-out prediction of a single-feature linear fit is a monotone transform of
  the feature. Generalisation is carried by loo_r2cv (closed-form PRESS) alone, and
  the binary half has no loo_r2cv at all, so this section covers the continuous half.

  Null for loo_r2cv built by permuting the target against 40 randomly chosen
  features per target, 2,000 permutations each. The leverage profile differs
  from feature to feature, so the null is sampled across features rather than one.

  target                    null P(R2cv>0)  null p95  null p99
  sdq_cond                          0.1835     0.091     0.199
  sdq_emo                           0.1941     0.099     0.206
  sdq_hyper                         0.1876     0.097     0.208
  sdq_peer                          0.1705     0.084     0.191
  sdq_pro                           0.1954     0.092     0.197
  sdq_totdiff                       0.1852     0.091     0.203
  snap_adhd_total                   0.1852     0.088     0.197
  snap_hyper                        0.1932     0.096     0.207
  snap_inatt                        0.1811     0.080     0.195
  snap_odd                          0.1662     0.072     0.180
  POOLED                            0.1842     0.090     0.199

  observed cells with loo_r2cv > 0            : 1226 of 6080   (20.16%)
  expected under the null                     : 1120   (18.42%)
  observed cells above the null 95th pct      : 254   (expected 304)
  largest loo_r2cv anywhere in the screen     : 0.6115
    attained by act_bout_median_w0.5_p80 on sdq_emo  (rho +0.772, perm_p 1.0e-05, q_fdr 0.006)
  median loo_r2cv across the continuous half  : -0.0555

  wrote /Users/shiyu/Projects/adhd-segmentation/outputs/figures/fig06_effect_vs_generalization.png

==============================================================================
[7] THE THREE CELLS THAT SURVIVED THE CORRECTION -- how robust are they
==============================================================================
  These three are the entire positive yield of the univariate track, so each is
  examined directly rather than reported as a row in a table. Three questions:
    (a) what does the relationship look like, and is it carried by the whole cohort?
    (b) how much does it move when any single subject is removed (n = 24)?
    (c) do the neighbouring settings of the same feature family agree with it?
        Path-A features form a grid over window length x percentile threshold.
        A real structural signal should vary smoothly across that grid; an isolated
        spike surrounded by nothing is what selecting the maximum of many noisy
        cells looks like.

  target correlations among the three targets involved (nested targets are not independent findings):
    sdq_emo            vs snap_adhd_total    Spearman rho = -0.132
    sdq_emo            vs snap_inatt         Spearman rho = +0.000
    snap_adhd_total    vs snap_inatt         Spearman rho = +0.962
    snap_adhd_total is by construction the sum of the SNAP inattention and
    hyperactivity items, so it contains snap_inatt; the two cells that share the
    feature frac_act_short_w10_p20 are one finding measured twice, not two.

  snap_inatt x frac_act_short_w10_p20
    full-sample rho +0.767;  drop-one range +0.739 .. +0.817
    subjects whose removal pushes rho below the null 95th percentile (0.405): none
    feature has 22 distinct values across 24 subjects
    neighbourhood: the frac_act_short grid on snap_inatt has 45 cells, median |rho| 0.062, max 0.767; cells above the null 95th pct: 2

  snap_adhd_total x frac_act_short_w10_p20
    full-sample rho +0.772;  drop-one range +0.747 .. +0.827
    subjects whose removal pushes rho below the null 95th percentile (0.407): none
    feature has 22 distinct values across 24 subjects
    neighbourhood: the frac_act_short grid on snap_adhd_total has 45 cells, median |rho| 0.113, max 0.772; cells above the null 95th pct: 2

  sdq_emo x act_bout_median_w0.5_p80
    full-sample rho +0.772;  drop-one range +0.737 .. +0.807
    subjects whose removal pushes rho below the null 95th percentile (0.406): none
    feature has 4 distinct values across 24 subjects
    neighbourhood: the act_bout_median grid on sdq_emo has 45 cells, median |rho| 0.225, max 0.772; cells above the null 95th pct: 6

  wrote /Users/shiyu/Projects/adhd-segmentation/outputs/figures/fig07_surviving_cells.png

==============================================================================
[8] TIED FEATURES AND THE SHARED NULL
==============================================================================
  44_univariate_screen.py builds one null per target by correlating shuffles of the
  target against the FIXED rank vector 0..n-1. Its own comment on that line records
  the assumption: 'equivalent to the null distribution of any feature WITHOUT ties'.
  Sharing one null across 608 features is what makes the screen fast, and it is exact
  for a feature whose 24 values are all distinct. A feature with tied values has a
  different null, because ties coarsen the set of attainable correlations.
  This section measures how many features are tied and what happens to the p-values
  when each feature is tested against its own null instead of the shared one.

  distinct values per feature across the 24 subjects:
          1 distinct :    0 features
        2-4 distinct :   31 features
        5-9 distinct :   42 features
      10-17 distinct :   17 features
      18-23 distinct :   47 features
         24 distinct :  471 features   (no ties: the shared null is exact)
  features with at least one tie : 137 of 608
  median distinct values         : 24

  recomputing all 12,160 permutation p-values against feature-specific nulls
  (100,000 permutations per target, every feature scored on the same shuffles)

  group                                cells  median p published  median p own null
  all cells                            12160              0.4990             0.4893
  cells whose feature has no ties       9420              0.4834             0.4802
  cells whose feature is tied           2740              0.5442             0.5223
  cells with <= 8 distinct values       1300              0.5468             0.5058

  direction of the change, cells with p_published < 0.05:
    own null gives a LARGER p (shared null was anti-conservative): 320 of 604
    own null gives a SMALLER p                                  : 280 of 604
    unchanged                                                   : 4 of 604

  raw p < 0.05 : 604 cells with the shared null, 642 with feature-specific nulls   (expected under the null: 608)
  BH-FDR q < 0.05 within target: 3 cells published, 11 recomputed

==============================================================================
[8b] THE TAIL CONVENTION -- the two tracks do not use the same one
==============================================================================
  44_univariate_screen.py:  p = #{null STRICTLY > observed} / NPERM, floored at 1/NPERM
      (the line 'pval=1-np.searchsorted(null,abs(rho),side="right")/NPERM')
  45_multivariate_cv.py:    p = (1 + #{null >= observed}) / (1 + NPERM)
      (the line 'return (hits+1)/(NPERM+1)' with the test written as '>= obs')
  For a continuous null the two agree to within 1/NPERM. They separate when the null
  places mass exactly on the observed value, which is what a tied feature produces:
  the attainable correlations become a short discrete list, and the observed value is
  frequently the largest entry in it. Then #{null > observed} is 0 -- reported as the
  floor 1e-5 -- while #{null >= observed} is a substantial count.

  group                                cells  median p (>)  median p (>=,+1)
  all cells                            12160        0.4893            0.5144
  feature has no ties                   9420        0.4802            0.4973
  feature is tied                       2740        0.5223            0.5493
  feature has <= 8 distinct values      1300        0.5058            0.5537

  cells reported at the 1e-5 floor under the strictly-greater convention: 10
    of those, the add-one convention gives p > 0.05 for 6 and p > 0.001 for 8
    their distinct-value counts: min 3, median 3, max 22

  survivors at q < 0.05 under each combination:
    published (shared null, strictly greater)        : 3
    feature-specific null, strictly greater          : 11
    feature-specific null, add-one and >=            : 3

  every cell that reaches q < 0.05 under any of the three, side by side:
  target               type  feature                    dist    p pub    p own     p +1    q pub    q own     q +1
  sdq_emo              cont  act_bout_median_w0.5_p80      4  1.0e-05  1.0e-05  1.0e-05   0.0061   0.0030   0.0061
  snap_inatt           cont  frac_act_short_w10_p20       22  1.0e-05  1.0e-05  2.0e-05   0.0061   0.0061   0.0122
  snap_adhd_total      cont  frac_act_short_w10_p20       22  1.0e-05  2.0e-05  3.0e-05   0.0061   0.0122   0.0182
  sdq_emo__qbin        bin   act_bout_median_w0.5_p80      4  3.8e-03  1.0e-05  2.1e-03   0.9639   0.0020   1.0000
  sdq_emo__qbin        bin   act_bout_median_w2_p70        4  6.9e-02  1.0e-05  3.6e-02   0.9639   0.0020   1.0000
  sdq_emo              cont  act_bout_median_w2_p90        3  5.0e-02  1.0e-05  5.8e-02   0.8805   0.0030   0.8764
  sdq_cond__qbin       bin   act_bout_median_w2_p90        3  4.9e-01  1.0e-05  4.7e-01   0.7986   0.0061   0.8385
  sdq_totdiff__qbin    bin   act_bout_median_w2_p90        3  4.8e-01  1.0e-05  4.9e-01   0.9302   0.0061   0.9940
  snap_hyper__qbin     bin   act_bout_median_w2_p90        3  4.9e-01  1.0e-05  5.2e-01   0.7883   0.0061   0.8444
  snap_adhd_total__qbin bin   act_bout_median_w2_p90        3  5.1e-01  1.0e-05  5.2e-01   0.8962   0.0061   0.9330
  sdq_emo__qbin        bin   act_bout_median_w2_p90        3  5.1e-01  1.0e-05  5.2e-01   0.9639   0.0020   1.0000

  What the three columns together show:
   - The published p-values are computed against an untied null, which is a
     continuous distribution, so the strictly-greater convention costs nothing and
     the published numbers are not distorted by it.
   - Correcting the null to respect each feature's ties WITHOUT also correcting the
     tail convention produces floor-level p-values for cells with no effect at all:
     8 of the 10 cells that land on the 1e-5 floor have an add-one p above 0.001,
     and 6 of them above 0.05. Those are an artefact of a discrete null, not results.
   - Correcting both together leaves the same three cells the screen already
     reported, at q = 0.0061, 0.0122 and 0.0182. The published positive yield of the
     univariate track therefore stands under a correctly specified test.

  wrote /Users/shiyu/Projects/adhd-segmentation/outputs/figures/fig08_tie_corrected_pvalues.png
```
