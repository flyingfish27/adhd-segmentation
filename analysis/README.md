# `analysis/` — script map

Scripts are numbered by pipeline stage. Letters (`55a`, `70b`, `74e`) are sub-steps of one
topic, so the sort order is the run order. Every script states its own inputs and outputs in
its header docstring; this file is only the index.

**Which scripts need the raw dataset.** The raw sensor files under `data/` (2.7 GB, from the
public dataset described in the top-level README) are **not** in this repository. Stages 00–36,
40–42, 46 and 50–57 read `data/` and cannot run from a bare clone. Everything from stage 43
onward, plus all of 60–74, runs from the committed CSV tables in this folder.

## Stage 00–11 · first look at the data (notebooks)

| file | what it does | needs `data/` |
|---|---|---|
| `00_explore.ipynb` | First read of a sensor file; x/y/z/magnitude traces | yes |
| `10_data_verify.ipynb` | Sampling-regularity check across every `_T` file; repair of 4 files that failed to load; duplicate-recording detection | yes |
| `11_activity_verify.ipynb` | Worn-vs-handheld check, per-subject placement fingerprint; original home of the temporal-feature code | yes |

## Stage 20–36 · codebook verification, questionnaire scoring, paper reproduction

| file | what it does | needs `data/` |
|---|---|---|
| `20_codebook_verify.py` | Re-derives every claim in `CODEBOOK.md` from the raw files as PASS/FAIL | yes |
| `21_rank_correlations.py` | All pairwise SDQ item correlations, ranked, no grouping assumed | yes |
| `22_cluster_items.py` | Hierarchical clustering of the 24 SDQ items (distance = 1 − \|ρ\|) | yes |
| `23_heatmap_subscales.py` | Item×item Spearman heatmap ordered by SDQ subscale → `figures/sdq_corr_heatmap.png` | yes |
| `24_heatmap_A_vs_B.py` | Two candidate item groupings compared by within/between correlation → `figures/sdq_corr_A_vs_B.png` | yes |
| `25_explore_rank_corrected.py` | Same as 21 after flipping reverse-scored items | yes |
| `26_explore_group_associations.py` | 5×5 subscale×subscale mean-ρ matrix → `figures/sdq_group_association_5x5.png` | yes |
| `27_reverse_stored_test.py` | Are SDQ reverse items stored pre- or post-flip? → `figures/reverse_items_stored_test.png` | yes |
| `28_tscore_label.py` | Recomputes paper 1's ADHD label rule (SNAP total → Z → T ≥ 55) step by step | yes |
| `29_explore_id_letter.py` | What the subject-ID prefix letter encodes; cross-check against paper 1's counts | yes |
| `30_paper1_table2_verify.py` | Recomputes paper 1, Table 2 (Wang, *Sensors* 2025) line by line | yes |
| `31_sensor_column_audit.py` | Column-by-column audit of the 58 sensor columns (range, examples, missingness) | yes |
| `32_motor_feature_probe.py` | Are tremor-band (3–12 Hz) / smoothness signals visible in the 100 Hz `_F` files? | yes |
| `33_tremor_in_still_segments.py` | Narrow tremor peaks in each child's stillest segments | yes |
| `34_sdq_total_bands_verify.py` | Do the SDQ Total-Difficulties bands reproduce on the local sample? | yes |
| `35_reproduce_papers.py` | Recomputes the published numbers of papers 1 and 2; settles the 1.67-threshold scale question | yes |
| `36_td_bands_local_vs_gao.py` | Shows the TD bands come from an external national norm (Gao et al. 2013), not this sample | yes |
| `chinese_norms.md` | Literature search for Chinese SNAP-IV / SDQ norms and cut-points | — |

## Stage 40–48 · targets, features, labels, and the two modelling tracks

| file | what it does | reads | writes | needs `data/` |
|---|---|---|---|---|
| `40_targets.py` | Continuous symptom targets (SNAP-IV / SDQ subscales + totals) for the 24 modelled children | clinical CSV, `figures/subject_audit.csv` | `targets.csv`, `items.csv` | yes |
| `42_features_full.py` | Full feature extraction: signal channel × recipe → 608 columns | `data/*_T.csv`, `targets.csv` | `features.csv` (24 × 609) | yes |
| `43_target_labels.py` | Rule-table-driven grouping engine; no cut-point lives in code | `targets.csv`, `items.csv`, `labels/` | `target_labels.csv`, `target_labels_meta.csv` | no |
| `44_univariate_screen.py` | **Track A**: one feature × one target at a time, permutation p, BH-FDR, LOO | the four tables above | `A_univariate.csv` (12,160 rows) | no |
| `45_multivariate_cv.py` | **Track B**: logistic / linear-SVM / RF, leave-one-out CV, selection inside the fold, permutation null | same (+ clinical CSV for the BMI arm) | `B_multivariate.csv` | BMI arm only |
| `46_duration_audit.py` | Recording length / sampling rate of the 24 subjects | `data/*_T.csv` | prints only | yes |
| `48_label_rules_equivalence.py` | Regression test: rule-table engine ≡ the frozen pre-refactor labels (`labels/baseline_target_labels.csv`) | committed tables | prints only | no |
| `labels/rules.yaml`, `labels/norms.csv`, `labels/sources.csv` | The rule table, norm bands, and citations behind every label | — | — | — |
| `FEATURE_MENU.md`, `TARGET_MENU.md`, `MODEL_MENU.md` | Human-readable decoding of feature names, targets/labels, and the A/B modelling design | — | — | — |

## Stage 50–58 · design and statistical-budget probes

Probes are not part of the production pipeline: each one prints, and its stdout is archived
verbatim under `probe_outputs/`.

| file | question it answers | needs `data/` |
|---|---|---|
| `50_temporal_design_probes.py` | Autocorrelation timescale; pooled-vs-per-subject threshold leakage | yes |
| `51_jerk_channel_audit.py` | Health check of the 21 jerk-channel columns | yes |
| `52_scan_compute_cost.py` | Compute cost of wider parameter scans / more feature classes | yes |
| `53_stat_budget_probes.py` | FDR cost of more features; power at n = 24; permutation resolution floor | no |
| `54_duration_confound_probe.py` | Is recording duration still a confound after equal-length truncation? | yes |
| `55a_cleaning_param_probe.py` / `55b_param_derivation_probe.py` / `55c_cleaning_vs_targets.py` | Data-driven choice of the three spike-cleaning parameters, and its effect on the target correlations | yes |
| `56_rec_duration_column_audit.py` | Behaviour of the `rec_dur_min` feature column | yes |
| `57_bmi_availability_probe.py` | BMI availability in the 24 modelled subjects | yes |
| `58_bperm_cost_probe.py` | Runtime of track B's permutation stage at NPERM = 5000 | no |
| `verify_temporal_provenance.py` | Provenance re-derivation of the temporal features and the pre-rewrite equivalence gate | yes |

## Stage 60–66 · results analysis (figures and tables under `outputs/`)

| file | what it does | writes |
|---|---|---|
| `60_results_inventory.py` | Inventory and integrity audit of every table the two tracks used or produced | `outputs/figures/fig01–02`, `outputs/tables/60_inventory.md` |
| `61_univariate_analysis.py` | Track A read-out: null comparison, per-target FDR, the surviving cells | `fig03–10`, `outputs/tables/61_univariate.md` |
| `62_multivariate_analysis.py` | Track B read-out and the A-vs-B comparison | `fig11–15`, `outputs/tables/62_multivariate.md` |
| `63_partial_vs_plain_diff.py` | Effect of partialling out total movement on the track-A statistics | `fig16`, `outputs/tables/63_…md` |
| `64_fig05b_standalone.py` | Panel b of fig05 on its own canvas | `fig05b_standalone.png` |
| `65_oof_predictions.py` | Saves track B's per-subject out-of-fold predictions | `B_oof_predictions.csv` |
| `66_selection_stability.py` | Does track B select a stable feature set across folds? | `fig17–18`, `outputs/tables/66_…md` |

The narrative that ties these together is `outputs/RESULTS_ANALYSIS.md`.

## Stage 70–74 · phase 2: feature-table reduction, K-grid screens, SFS, final models

None of these read `data/`; all run from the committed CSVs. Scripts 71/71b/72/73/74/74a
lift the model definitions out of `45_multivariate_cv.py` via `ast` rather than copying them.

| file | what it does | writes |
|---|---|---|
| `70_feature_inventory.py` | Read-only inventory of the 608-column feature table | `probe_outputs/feature_inventory.md` |
| `70a_cluster_representatives.py` | One representative per redundancy cluster at \|ρ\| ≥ 0.90 | `probe_outputs/cluster_representatives.md` |
| `70b_dedup_099.py` | Drop near-duplicates at \|ρ\| ≥ 0.99 (607 → 574) | `probe_outputs/dedup_099.md` |
| `70c_dedup_095_greedy.py` | Greedy pairwise dedup at \|ρ\| ≥ 0.95 (574 → 512) | `feature_keeplist_512.csv` |
| `71_kgrid_baseline.py` | F-test K-grid screen, K = 1…512, three classifiers, 10 binary targets — the frozen baseline | `kgrid_baseline_bin.csv` |
| `71a_kgrid_plot.py` · `71c_kgrid_compare_plot.py` · `71d_kgrid_mi_plot.py` | The K-grid figures | `outputs/figures/kgrid_*.png` |
| `71b_kgrid_mi.py` | Mutual-information twin of the K-grid screen | `kgrid_mi_bin.csv` |
| `72_sfs_logit.py` | Nested sequential forward selection with the locked logistic model, depth 1–20 | `sfs_logit_bin.csv`, `sfs_logit_paths.csv` |
| `72a_sfs_vs_filter_plot.py` · `72b_step1_stability_plot.py` | SFS vs filter baseline; first-pick agreement vs peak | `outputs/figures/sfs_*.png` |
| `73_reg_kgrid.py` · `73a_reg_kgrid_plot.py` | Regression twin of the K-grid screen, and its model-selection figure | `kgrid_reg.csv`, `outputs/figures/kgrid_reg_skill_curves.png` |
| `74_final_clf.py` | **Classification delivery**: 10 binary + 14 multiclass targets, nested-K logistic regression, full-sample refit, serialised models | `final_clf_metrics.csv`, `final_clf_features.csv`, `final_clf_folds.csv`, `outputs/models/` |
| `74a_final_reg.py` | **Regression delivery**: 10 continuous targets, nested-K ridge; mirrors 74 | `final_reg_metrics.csv`, `final_reg_features.csv`, `final_reg_folds.csv`, `outputs/models/` |
| `74b_delivery_figure.py` · `74c_carrier_scatter.py` · `74d_reg_rmse_figure.py` · `74e_clf_bacc_bars.py` | Delivery figures | `outputs/figures/final_*.png`, `carrier_features_scatter.png` |

## Committed tables in this folder

| file | shape | produced by |
|---|---|---|
| `targets.csv` | 24 × 10 continuous symptom scores | `40_targets.py` |
| `items.csv` | 24 × 50 item-level scores | `40_targets.py` |
| `features.csv` | 24 × 609 (608 features + `subject`) | `42_features_full.py` |
| `target_labels.csv`, `target_labels_meta.csv` | grouped labels and their provenance | `43_target_labels.py` |
| `A_univariate.csv` | 12,160 rows: every feature × target of track A | `44_univariate_screen.py` |
| `B_multivariate.csv` | 612 rows: every variant × target × model × k of track B | `45_multivariate_cv.py` |
| `B_oof_predictions.csv` | 14,280 rows: track B out-of-fold predictions | `65_oof_predictions.py` |
| `feature_keeplist_512.csv` | the 512 features kept after dedup | `70c_dedup_095_greedy.py` |
| `kgrid_baseline_bin.csv`, `kgrid_mi_bin.csv`, `kgrid_reg.csv` | K-grid sweeps | `71`, `71b`, `73` |
| `sfs_logit_bin.csv`, `sfs_logit_paths.csv` | SFS curves and per-fold paths | `72_sfs_logit.py` |
| `final_clf_*.csv`, `final_reg_*.csv` | delivered models: metrics, features, per-fold choices | `74`, `74a` |

## `probe_outputs/`

Verbatim stdout snapshots of the probes and of the phase-2 scripts, plus a few acceptance
scripts (`*_check.py`, `perm_checkpoint_test.py`, `b_reg_train_vs_oof_probe.py`). Each snapshot
names the script that produced it and the commit it was produced at. They are evidence, not
inputs: no pipeline script reads them.
