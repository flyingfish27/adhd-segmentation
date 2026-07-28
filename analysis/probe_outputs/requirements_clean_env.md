# 证据快照:requirements.txt 在干净环境里的完整性验证

- 验证日期: 2026-07-28
- 验证时仓库 commit: `c56b134`
- 被验对象: 项目根目录 `requirements.txt`（7 个锁版本依赖，填于 commit `9e989c6`）
- 起因: `working/backlog.md` §2 登记「该文件从未在干净环境验证过，即"是否漏列了某个直接依赖"未经检验」。
  用户 2026-07-28 裁决＝**现在验**。
- 说明: 本文件是下列命令的**原样 stdout 快照**，勿手改；要更新就重跑覆盖本文件。

## 复现命令

```bash
# 1) 建一个干净 venv（不继承本机站点包），确认它确实是空的
python3 -m venv /tmp/cleanenv
/tmp/cleanenv/bin/python -c "import pandas"     # 应报 ModuleNotFoundError

# 2) 只按 requirements.txt 安装
/tmp/cleanenv/bin/pip install -r requirements.txt

# 3) 用 ast 解析出全仓库 .py 直接 import 的第三方包（不能用正则：
#    43_target_labels.py 写的是 import numpy as np, pandas as pd, yaml —— 一行三个包）
/tmp/cleanenv/bin/python - <<'PY'
import ast, pathlib
files = sorted(pathlib.Path("analysis").glob("*.py")) + sorted(pathlib.Path("archive").glob("*.py"))
mods = {}
for f in files:
    for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Import):
            for a in n.names: mods.setdefault(a.name.split(".")[0], set()).add(f.name)
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            mods.setdefault(n.module.split(".")[0], set()).add(f.name)
print(sorted(mods))
PY

# 4) 在干净环境里逐个 import；再跑 golden 基线回归做端到端验证
/tmp/cleanenv/bin/python -c "import joblib, matplotlib, numpy, pandas, scipy, sklearn, yaml"
/tmp/cleanenv/bin/python analysis/48_label_rules_equivalence.py
```

## 结果:通过

**① 干净环境确认为空**（装 requirements 之前 `import pandas` 报 `ModuleNotFoundError`），Python **3.9.6**。

**② 安装成功**，exit 0。pip 解析出的完整环境（含间接依赖）：

```text
Package             Version
------------------- ------------
contourpy           1.3.0
cycler              0.12.1
fonttools           4.60.2
importlib_resources 6.5.2
joblib              1.5.3
kiwisolver          1.4.7
matplotlib          3.9.4
numpy               2.0.2
packaging           26.2
pandas              2.3.3
pillow              11.3.0
pip                 21.2.4
pyparsing           3.3.2
python-dateutil     2.9.0.post0
pytz                2026.3.post1
PyYAML              6.0.3
scikit-learn        1.6.1
scipy               1.13.1
setuptools          58.0.4
six                 1.17.0
threadpoolctl       3.6.0
tzdata              2026.3
zipp                3.23.1
```

**③ 全仓库 `.py` 直接 import 的第三方包（`ast` 解析，共 7 个）与出处：**

```text
joblib	45_multivariate_cv.py,58_bperm_cost_probe.py
matplotlib	23_heatmap_subscales.py,24_heatmap_A_vs_B.py,26_explore_group_associations.py,27_reverse_stored_test.py
numpy	20_codebook_verify.py,21_rank_correlations.py,22_cluster_items.py,23_heatmap_subscales.py,24_heatmap_A_vs_B.py,25_explore_rank_corrected.py,26_explore_group_associations.py,27_reverse_stored_test.py,28_tscore_label.py,29_explore_id_letter.py,30_paper1_table2_verify.py,31_sensor_column_audit.py,32_motor_feature_probe.py,33_tremor_in_still_segments.py,34_sdq_total_bands_verify.py,35_reproduce_papers.py,36_td_bands_local_vs_gao.py,40_targets.py,41_features_min.py,42_features_full.py,43_target_labels.py,44_univariate_screen.py,45_multivariate_cv.py,46_duration_audit.py,47_truncation_impact.py,50_temporal_design_probes.py,51_jerk_channel_audit.py,52_scan_compute_cost.py,53_stat_budget_probes.py,54_duration_confound_probe.py,55a_cleaning_param_probe.py,55b_param_derivation_probe.py,55c_cleaning_vs_targets.py,56_rec_duration_column_audit.py,57_bmi_availability_probe.py,58_bperm_cost_probe.py,consistency_explained.py,verify_temporal_provenance.py
pandas	20_codebook_verify.py,21_rank_correlations.py,22_cluster_items.py,23_heatmap_subscales.py,24_heatmap_A_vs_B.py,25_explore_rank_corrected.py,26_explore_group_associations.py,27_reverse_stored_test.py,28_tscore_label.py,29_explore_id_letter.py,30_paper1_table2_verify.py,31_sensor_column_audit.py,32_motor_feature_probe.py,33_tremor_in_still_segments.py,34_sdq_total_bands_verify.py,35_reproduce_papers.py,36_td_bands_local_vs_gao.py,40_targets.py,41_features_min.py,42_features_full.py,43_target_labels.py,44_univariate_screen.py,45_multivariate_cv.py,46_duration_audit.py,47_truncation_impact.py,48_label_rules_equivalence.py,50_temporal_design_probes.py,51_jerk_channel_audit.py,52_scan_compute_cost.py,53_stat_budget_probes.py,54_duration_confound_probe.py,55b_param_derivation_probe.py,55c_cleaning_vs_targets.py,56_rec_duration_column_audit.py,57_bmi_availability_probe.py,58_bperm_cost_probe.py,consistency_explained.py,verify_temporal_provenance.py
scipy	20_codebook_verify.py,22_cluster_items.py,26_explore_group_associations.py,27_reverse_stored_test.py,30_paper1_table2_verify.py,32_motor_feature_probe.py,33_tremor_in_still_segments.py,42_features_full.py,44_univariate_screen.py,45_multivariate_cv.py,47_truncation_impact.py,50_temporal_design_probes.py,53_stat_budget_probes.py,54_duration_confound_probe.py,55a_cleaning_param_probe.py,55b_param_derivation_probe.py,55c_cleaning_vs_targets.py,56_rec_duration_column_audit.py,57_bmi_availability_probe.py
sklearn	45_multivariate_cv.py,58_bperm_cost_probe.py
yaml	43_target_labels.py
```

**④ 逐个 import 结果：7 个全部成功**

```text
✓ joblib   ✓ matplotlib   ✓ numpy   ✓ pandas   ✓ scipy   ✓ sklearn   ✓ yaml
```

**⑤ 端到端验证：golden 基线回归在干净环境里通过**

跑 `analysis/48_label_rules_equivalence.py`（它同时用到 pandas + yaml + 真实标签数据），
exit 0，第 [6] 项：**24 行 × 39 列 = 936 格与冻结基线逐格一致**。
运行后 `git status` 无新增改动，确认该脚本本次运行为只读、未污染仓库。

## 结论

**`requirements.txt` 清单完整** —— 没有漏列任何直接依赖；且在只装这份清单的干净环境里，
主链路脚本 `48_label_rules_equivalence.py` 能跑到底并通过全部断言。

## 一条方法层记录（本次验证自身出过的错，供后来者避坑）

第一次提取 import 用的是正则 `^\s*(import|from) (\w+)`，**漏掉了 `yaml`** ——
因为 `analysis/43_target_labels.py` 写的是 `import numpy as np, pandas as pd, yaml`，
**一行三个包，正则只抓到第一个**。另外过滤标准库时用了 `sys.stdlib_module_names`，
而该属性 **Python 3.10 才有**，在本项目的 3.9.6 上返回空集合，导致过滤整个失效。
改用 `ast` 解析后两个问题都消失。这与 `ENGINEERING_NOTES.md` 第 5 节记的
「任何靠单行正则判断依赖的做法都会漏」是同一条教训的又一个实例。
