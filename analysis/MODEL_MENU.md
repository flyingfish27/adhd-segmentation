# 建模菜单(阶段3产物)

- A 轨(单变量筛查):`analysis/44_univariate_screen.py` → `analysis/A_univariate.csv`(5775 行)。
- B 轨(多变量模型):`analysis/45_multivariate_cv.py` → `analysis/B_multivariate.csv`(198 行)。
- 样本 = 24 人(同 features.csv / targets.csv);全程留一交叉验证(LOO,n=24)。
- 设计原则(因 n=24):探索性、报全指标、fold 内做一切依赖数据的步骤(防泄漏)、负对照、多重比较校正、不夸大。

---

## 1. 两轨的分工与思路

| | A 轨:单变量筛查 | B 轨:多变量模型 |
|---|---|---|
| 一次用几个特征 | **1 个** | **275 个**(fold 内选 top-k) |
| 想回答 | 每个特征单独,和目标有没有关系(最诚实、无多变量过拟合) | Daniel 点名的 logistic/SVM/ML 能不能组合出预测力 |
| 过拟合风险 | 低(单特征) | **高**(275≫24;靠 fold 内选择 + 置换兜底) |
| 定位 | **主力可信结果** | 佐证;结果显式标注过拟合风险 |

## 2. A 轨方法(单变量)

| 目标类型 | 效应量 | 泛化评估 | 显著性 |
|---|---|---|---|
| 连续(10 个) | Spearman ρ(特征 vs 目标) | 留一 `R²_cv`(闭式 PRESS:留一残差=e_i/(1−h_i))+ 留一 RMSE/MAE | 置换 5000 次 |
| 二分(11 个) | AUC(=Mann-Whitney,秩基,免拟合) | —— | 置换 5000 次 |

- **置换零分布共享**:对固定目标,打乱 y 的 Spearman 零分布只依赖 n(无并列时),AUC 零分布只依赖两组人数 → 每目标算一次,275 特征共用。既快又标准。
- 二分目标 = 10 个 `__qbin` + `snap_total__wang2025T55`(旧名 `snap_total__normT55`,TASK-8 决定2 改名,取值不变),再按 `analysis/target_labels_meta.csv` 的 `degenerate` 字段剔除退化列。
- **多重比较**:每个目标族内做 Benjamini–Hochberg FDR → `q_fdr`。判据 q<0.05。

### A_univariate.csv 字段

| 字段 | 含义 |
|---|---|
| `target` | 目标名 |
| `type` | `cont`(连续)/ `bin`(二分) |
| `feature` | 275 特征之一 |
| `rho` | 连续=Spearman ρ;二分=AUC |
| `perm_p` | 置换 p(下限 1/5000) |
| `loo_r2cv` | 留一 R²_cv(**≤0 = 单特征留一下不泛化**);二分为空 |
| `loo_rmse` `loo_mae` | 留一预测误差;二分为空 |
| `q_fdr` | 目标族内 BH-FDR q 值 |

## 3. B 轨方法(多变量)

**管线(封进 sklearn Pipeline,只在训练折 fit)**:
`VarianceThreshold(0)` → `SelectKBest(F值, k)` → `StandardScaler` → 模型
- **顺序特意是"先选再标准化"**:避免 fold 内常数特征(std=0)在标准化时除零 → inf 污染。F 检验尺度无关,可先做。
- k ∈ {5, 10}。

| 任务 | 模型 | 指标 |
|---|---|---|
| 回归(10 连续) | Ridge(α=10)、SVR(rbf, C=1)、RandomForest(200 树) | RMSE、MAE、Spearman ρ、`skill`=1−RMSE/哑基线RMSE |
| 二分(11) | Logistic(L2,C=1)、线性SVM(C=1)、RandomForest(200) | macro-F1、accuracy、balanced-accuracy |
| 多分(12) | 同二分 | 同二分 |

- **留一收集 24 个预测,再整体算指标**(逐折 1 样本,F1/ρ 不能逐折平均)。
- 多分类目标 = 能干净切出 k 组的 6 个(snap_inatt/hyper/odd/total、sdq_hyper、sdq_totdiff)× {qter, qquar}。
- **三条基线**:①哑基线(回归=预测均值,分类=多数类)②负对照 `mag_median`(仅此一特征走 StandardScaler+Ridge)③置换 500 次——**仅对"超过哑基线"的组合跑**(回归 skill>0、分类 bacc>0.5),其余 `perm_p=NaN`。p=(命中+1)/(500+1)。

### B_multivariate.csv 字段

| 字段 | 含义 |
|---|---|
| `track` | `reg` / `bin` / `multi` |
| `target` | 目标名 |
| `model` | ridge/svr/rf 或 logit/svm/rf |
| `k` | 选入特征数(5 或 10) |
| `rmse` `mae` `rho` `skill` | 回归指标(`skill`>0 才算超过哑基线) |
| `nc_skill` | 负对照(mag_median)的 skill,做对照 |
| `f1` `acc` `bacc` | 分类指标(macro-F1 / 准确率 / 平衡准确率) |
| `perm_p` | 置换 p;**NaN = 没超过哑基线、未跑置换(≠ 显著)** |

---

## 4. 读表必读的陷阱(否则会误读)

1. **A 轨 `rho` 不是泛化证据**。单特征线性回归的留一预测是特征的单调变换,故留一 ρ≈全样本 |ρ|。判泛化**只看 `loo_r2cv` 和 `perm_p`/`q_fdr`**。
2. **B 轨 `perm_p=NaN` 不等于不显著**,而是"没超过哑基线所以没跑置换"。真正要看的是 skill>0 / bacc>0.5 **且** perm_p 小。
3. **超参是拍的,没调**:α=10、C=1、RF 设置、k∈{5,10} 均为固定值,未在 fold 内再套调参层。是刻意为之(避免再加一层复杂度),但也因此**这些不是"最优模型",是"一组合理默认"**。
4. **置换阈值方向**:`perm_p` = 打乱 y 后 CV 指标 ≥ 观测值的比例,越小越可能真。

## 5. 已知局限(与问题清单挂钩,详见讨论)

- **n=24,功率 ~49%**:阴性不证明无关,阳性极脆。全轨探索性。
- **多重比较**:A 轨 within-target FDR 已 0 存活;B 轨原始 p<0.05 仅 3 个 ≈ 噪声期望,全局 FDR(阶段4)未做。
- **录制时长混淆**:时长与 sdq_totdiff(ρ=−0.46)相关,B 轨冒头目标疑受其污染 —— 建模未控制时长(待阶段5)。
- **特征侧遗留问题**:多阈值时间结构族有缺陷(actfrac 常数、原始采样抖动)、姿态角疑似佩戴伪迹、mag_median 与 uaMag_median 重复 —— 见 FEATURE_MENU 与讨论记录。

> 本菜单记录的是**已跑版本**的方法与字段。上面第 5 节的局限尚未修复;任何修复(重写特征、控时长、全局 FDR)都会刷新 A/B 结果,届时同步更新本表。
