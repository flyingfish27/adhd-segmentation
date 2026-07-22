# 特征菜单(阶段1产物)

由 `analysis/42_features_full.py` 生成 → `analysis/features.csv`(24 人 × 275 列)。
命名规则:`{通道}_{配方}`。只用 `_T`(任务态)文件;死通道(磁场/航向/GPS/电量)不参与。
样本=`figures/subject_audit.csv` 里 `status==usable & _T==yes` 的 24 人。

---

## 1. 信号通道(12 条)

| 前缀 | 来源列 | 含义 | 单位 |
|---|---|---|---|
| `uaX/uaY/uaZ` | motionUserAcceleration{X,Y,Z}(G) | 去重力后的线性加速度 3 轴 | G(1G≈9.8 m/s²) |
| `uaMag` | ‖userAccel‖ | 运动强度总幅值(=SVM,与重力无关) | G |
| `gyX/gyY/gyZ` | motionRotationRate{X,Y,Z}(rad/s) | 角速度 3 轴(手腕转动快慢) | rad/s |
| `gyMag` | ‖rotationRate‖ | 转动强度总幅值 | rad/s |
| `pitch/roll/yaw` | motionPitch/Roll/Yaw(rad) | 手腕姿态角(相对参考系的朝向) | rad |
| `jerk` | d‖userAccel‖/dt | 加速度变化率 = 动作"爆发性/急促度" | G/s |

**排除理由**:磁场(未校准漂移)、航向(GPS 派生、室内无效)、GPS 经纬度(隐私+森林覆盖)、电量(与运动无关)——见 CODEBOOK §4。

## 2. 时域配方(每通道 14 个)

在整段信号上算(mean/std 等与时长无关,可跨不同录制时长比较)。

| 后缀 | 含义 | 直觉 |
|---|---|---|
| `mean` | 均值 | 平均水平 |
| `std` `var` | 标准差 / 方差(ddof=1) | 波动大小 |
| `rms` | 均方根 √(mean(x²)) | 能量水平 |
| `min` `max` `range` | 最小/最大/极差 | 极端值跨度 |
| `median` `iqr` | 中位数 / 四分位距 | 稳健的中心与散布 |
| `mad` | 中位绝对偏差 median(|x−med|) | 抗离群的波动 |
| `skew` `kurt` | 偏度 / 峰度 | 分布不对称/尖峰重尾(爆发多则峰度高) |
| `zcr` | 过零率(去均值后符号翻转数/样本数) | 振荡频繁程度 |
| `madiff` | 相邻样本绝对差均值 mean(|Δx|) | 逐点抖动/粗糙度 |

## 3. 频域配方(每通道 7 个)

去均值 + Hann 窗 + rfft,功率谱去 DC 后归一。fs≈29.71Hz,Nyquist≈14.85Hz。

| 后缀 | 含义 | 直觉 |
|---|---|---|
| `domfreq` | 主频(功率最大处的频率,Hz) | 主要节律快慢 |
| `centroid` | 谱质心 Σf·P/ΣP(Hz) | 频谱"重心"高低 |
| `spread` | 谱展宽(围绕质心的标准差,Hz) | 频率分布宽窄 |
| `entropy` | 谱熵(归一,0=单频纯净,1=白噪) | 动作规律 vs 杂乱 |
| `bp_lf` | 低频带占比 0.5–3Hz | 慢动作能量份额 |
| `bp_mf` | 中频带占比 3–6Hz | 中速动作份额 |
| `bp_hf` | 高频带占比 6–Nyq | 快速抖动份额 |

## 4. 时间结构 × 多阈值(在 `uaMag` 上,阈值 p50/p75/p90)

对应 Daniel 树里"活动/静止分段 + 强度按时长归一化"。阈值=幅值的百分位;`>阈值`记为"活动"。

| 模板 | 含义(p 为阈值百分位) |
|---|---|
| `actfrac_p{50,75,90}` | 活动时间占比(高于该强度阈值的时长份额)= 强度归一化 |
| `switchmin_p{...}` | 每分钟活动↔静止切换次数 = 动作碎片化程度 |
| `actbout_med_p{...}` | 活动段中位时长(s) |
| `actbout_cv_p{...}` | 活动段时长变异系数(段长忽长忽短?) |
| `actshort_p{...}` | <1s 短爆发活动段占比 |

## 5. 复用的已验证时间结构特征(8 个,join 自 `temporal_features.csv`)

来自 `11_activity_verify.ipynb` 的 `temporal_features()`(滑窗 10s/步 5s,窗内 50 百分位二值化,run-length)。已在阶段1前独立验证过,保留:

`switch_per_min` `act_bout_median` `stl_bout_median` `act_bout_cv` `stl_bout_cv`
`frac_act_short` `within_win_sd` `mag_median`(**mag_median 作负对照**:代表"总运动量",用来区分发现来自"结构"还是"总量")。

---

## 后置分支(阶段1不做,留给后续)
- 小波系数能量(抓爆发式动作的时频局部化)。
- 离散域 / DTW / 编辑距离(配 kNN 的第二条路线,Daniel W4 讲义)。
- 通道间交叉特征(如姿态角 × 转动量的关联)。

## 注意(n=24 的方法学后果)
275 特征 ≫ 24 样本 → **必然有碰巧相关的**。阶段3/4 用留一 CV(fold 内做特征选择/标准化)+ 多重比较校正(FDR/置换)来防"把噪声当发现"。此表是"全做出来"的原料,不是结论。
