# CODEBOOK — ADHD 儿童运动/心理健康数据集数据字典

数据集:Zenodo `10.5281/zenodo.14875672`("Movement and Mental Health in Children", Lin Wang;Apple Watch Series 7 + SensorLog v5.2)。

**本文件的方法论(重要)**:每一条结论都从**原始数据 + 客观事实**推出,不采信任何二级结论(`week2.pptx`、notebook 评分代码、论文正文的文字口径)。可用 `.venv/bin/python 20_codebook_verify.py` 一键复算下列所有 PASS/数字。

**依据分层与置信度**
- `实证` — 原始数据里直接观测到。
- `自证` — 被列间物理/数学恒等式强制(BMI、加速度分解、模长、档数),无需任何外部文档。
- `仪器` — 由测量工具的固有结构决定(SDQ 问卷 3 档、SNAP-IV 4 档/26 题/3 子量表)。
- `复现` — 复现出某篇论文 published 的具体数字。
- 置信度:`confirmed`(满足以上任一) / `hypothesis` / `unresolved`。

**两篇使用本数据集的论文**
- **论文1** = Wang, *Sensors* 2025 **25(20):6459**(仓库 `literature/ViT-BiLSTM ....pdf`)。
- **论文2** = Zhang/Liu/Wu, *Biosensors* 2026 **16(6):323**(PMC13297289)。

---

## 0. 数据集概览

| 项 | 值 | 依据 |
|---|---|---|
| 受试者(临床表行数) | **58** | 实证(C1) |
| `_F` 传感器文件 | 50 | 实证 |
| `_T` 传感器文件 | 33(其中 25 人同时有 `_F` 和 `_T`) | 实证 |
| 传感器每文件列数 | **58**(论文2 称"55 列",以数据为准) | 实证/自证(S1) |
| 临床表列数 | 55(`ID,SEX,BMI,height,weight` + 24 个 SDQ + 26 个 SNAP) | 实证 |
| 有 ADHD 临床诊断金标准? | **否**。ADHD 全部由问卷分数派生 | 仪器/复现 |

---

## 1. 临床表 `data/Demographic and mental health data.csv`

一行一个孩子。列级定义:

| 列 | 含义 | 单位 | 实测取值 | 推导逻辑链 | 依据 | 置信度 |
|---|---|---|---|---|---|---|
| `ID` | 受试者编号(字母+数字) | — | 58 个,含 `Q27` | 直接读表。**注意**:临床用 `Q27`,传感器文件用 `Z27`,为**同一孩子**(见 §6) | 实证 | confirmed |
| `SEX` | 性别 | 文本 | `male`(33)/`female`(25),全小写 | 直接读表,仅两种取值。两篇论文各自编码成 0/1,属其派生,不是原始列含义 | 实证 | confirmed |
| `BMI` | 体质指数 | kg/m² | 11.7–22.8 | `BMI = weight/(height/100)²` 在全部 52 个有身高体重的行上吻合(误差≤0.1,0 例外)→ 自证此列即 BMI | 自证(C7) | confirmed |
| `height(cm)` | 身高 | **cm** | 120–162 | 同上恒等式成立即锁定单位为 cm | 自证(C7) | confirmed |
| `weight(kg)` | 体重 | **kg** | 20–59 | 同上恒等式成立即锁定单位为 kg | 自证(C7) | confirmed |
| `SDQ1`–`SDQ18`,`SDQ20`–`SDQ25` | SDQ 问卷各题原始作答(**缺 SDQ19**) | 序数 | `{1,2,3}`(唯一异常 S32/SDQ8=13) | 数据每题恰 3 个取值 ⇔ SDQ 问卷客观上 3 个作答档(不真实/有点/完全)⇒ **数据是 1-indexed,标准分 = 数据−1** | 实证+仪器(C2) | confirmed |
| `a1`–`a26` | SNAP-IV-26 各题原始作答 | 序数 | `{1,2,3,4}` | 数据每题恰 4 个取值 ⇔ SNAP-IV 客观上 4 个作答档(0–3)⇒ **数据是 1-indexed,标准分 = 数据−1** | 实证+仪器(C3) | confirmed |

> **关于"减 1"**:数据确为 1-indexed(上表已证)。但**两篇论文在算分/定标签时都未减 1、直接用原始 1–4 / 1–3**(见 §3 复现)。所以"要不要减 1"取决于你对齐谁:对齐问卷标准分→减 1;复现两篇论文→不减。

---

## 2. 子量表题号映射

### 2.1 SDQ 列 = 问卷**原始题号**(不是按子量表分块)——裁决 confirmed

数据只有列名与数字、无题目文本,故用三条客观证据裁决两个互斥假设(A=沿用问卷原始题号 / B=按子量表分块重排):

1. **结构**:数据恰好缺 `SDQ19`、保留 `SDQ20–25` 的跳号。若按子量表分块应是连续 1–24 无跳号;跳号落在 19 ⇒ **列保留了问卷原始题号**(第 19 题未采集)。
2. **内部一致性**:按原始题号,hyperactivity 五题(2,10,15,21*,25*)反向校正后平均题间相关 **+0.477**,为所有子量表最高、成团。
3. **收敛效度**:按原始题号算的 SDQ-hyperactivity 与 SNAP 的注意力+多动(a1–a18)相关 **ρ=+0.574**;按"SDQ11–15"只有 **+0.305**。A ≈ B 的两倍。

⇒ **SDQ 列按 Goodman 原始题号排列**,子量表如下(`*`=反向,1–3 编码下反向 = `4−x`):

| 子量表 | 题号(=列名) |
|---|---|
| Emotional 情绪 | SDQ3, 8, 13, 16, 24 |
| Conduct 品行 | SDQ5, 7*, 12, 18, 22 |
| **Hyperactivity/inattention 多动** | **SDQ2, 10, 15, 21\*, 25\*** |
| Peer 同伴 | SDQ6, 11*, 14*, **19(缺)**, 23 |
| Prosocial 亲社会 | SDQ1, 4, 9, 17, 20 |

缺失的 **SDQ19 = "被别的孩子欺负/取笑"(peer 子量表)**。

### 2.2 SNAP-IV 列(标准 SNAP-IV-26 结构)

| 子量表 | 题号(=列名) |
|---|---|
| Inattention 注意力缺陷(9 题) | a1–a9 |
| Hyperactivity/Impulsivity 多动冲动(9 题) | a10–a18 |
| Oppositional Defiant 对立违抗(8 题) | a19–a26 |

依据:仪器结构;a1–a18(注意力+多动)与 SDQ-hyperactivity 的收敛效度佐证(§2.1)。置信度 confirmed(前两子量表);a19–a26=ODD 为 `仪器`,论文未报 ODD 子量表统计,标 confirmed-by-structure。

---

## 3. 派生分数与 ADHD 标签(两篇论文各自怎么算的)

**关键:两篇都用原始尺度(SDQ 1–3、SNAP 1–4),都不减 1。** 且论文2 把"无问卷数据者按 0 计入"。以下均由复现其 published 数字确证。

| 量 | 定义(复现所得) | 复现证据 |
|---|---|---|
| 论文2 "SDQ 分" | 24 题原始(1–3)求和,**缺失→0**,在有人口学数据者上分性别统计 | 男 n=30 → **39.33±13.73, 中位43**,逐位命中 |
| 论文2 "SNAP 分" | 26 题原始(1–4)求和,**缺失→0** | 男 n=30 → **42.17±19.42**,逐位命中 |
| 论文2 ADHD 分组 | 每题原始均值(1–4 尺度)**≥1.67 → High-ADHD** | 若改减 1 的 0–3 尺度则 High=1,荒谬 ⇒ 阈值确在原始尺度 |
| 论文1 ADHD 标签 | SNAP 原始总分 → Z 分 → **T=Z·10+50,T≥55 → ADHD** | 复现 **ADHD=13**(命中论文的 13;非 ADHD 36 vs 37 仅因本数据 N=49 vs 论文 50) |
| 论文1 SNAP 总分 | 原始 1–4 之和(≈43),**非**减 1 后的 ~18 | 本数据 44.16±10.28 ≈ 论文 42.98±9.13 |

> T 分对尺度平移不变,故论文1 标签与"是否减 1"无关;但其报的总分 ~43 证明它按原始尺度求和。人口学(SEX/BMI/身高/体重)在论文2 Table 1 上**男性逐位精确复现**,彻底锁定这些列。

---

## 4. 传感器 CSV(`*_F.csv` / `*_T.csv`,58 列,iOS Core Motion / SensorLog 标准导出)

**自证恒等式(在 H1_F、H2_T 上验证,见 S2)**:
- `accelerometerAcceleration(X/Y/Z) ≈ motionUserAcceleration(X/Y/Z) + motionGravity(X/Y/Z)`(残差中位数 0.05–0.09 G ≈ 0)⇒ 自证:`accelerometer*`=**含重力原始加速度**、`motionUserAcceleration*`=**去重力用户加速度**、`motionGravity*`=**重力向量**。
- `‖motionGravity‖ = 1.0000`(单位向量,G)、`‖motionQuaternion‖ = 1.0000`(单位姿态四元数)。

列清单(单位取自表头括号):

| # | 列名 | 含义 | 单位 |
|---|---|---|---|
| 1 | loggingTime(txt) | 记录墙钟时间(ISO8601) | 文本 |
| 2 | locationTimestamp_since1970(s) | GPS 时间戳 | s |
| 3–4 | locationLatitude/Longitude(WGS84) | 经纬度 | 度 |
| 5 | locationAltitude(m) | 海拔 | m |
| 6–7 | locationSpeed/SpeedAccuracy(m/s) | 速度/精度 | m/s |
| 8–9 | locationCourse/CourseAccuracy(°) | 航向/精度 | 度 |
| 10–11 | locationVertical/HorizontalAccuracy(m) | 定位精度 | m |
| 12 | locationFloor(Z) | 楼层 | 整数 |
| 13 | accelerometerTimestamp_sinceReboot(s) | 加速度时间戳 | s |
| 14–16 | accelerometerAccelerationX/Y/Z(G) | **含重力**原始加速度 | G |
| 17 | motionTimestamp_sinceReboot(s) | 姿态时间戳 | s |
| 18–20 | motionYaw/Roll/Pitch(rad) | 欧拉角 | rad |
| 21–23 | motionRotationRateX/Y/Z(rad/s) | 角速度(陀螺) | rad/s |
| 24–26 | motionUserAccelerationX/Y/Z(G) | **去重力**用户加速度 | G |
| 27 | motionAttitudeReferenceFrame(txt) | 姿态参考系 | 文本 |
| 28–31 | motionQuaternionX/Y/Z/W(R) | 单位姿态四元数 | — |
| 32–34 | motionGravityX/Y/Z(G) | 重力向量 | G |
| 35–37 | motionMagneticFieldX/Y/Z(µT) | 磁场 | µT |
| 38 | motionHeading(°) | 磁航向 | 度 |
| 39 | motionMagneticFieldCalibrationAccuracy(Z) | 磁校准精度 | 枚举 |
| 40 | activityTimestamp_sinceReboot(s) | 活动分类时间戳 | s |
| 41 | activity(txt) | **Core Motion 活动分类**(walking/running/stationary/cycling/unknown) | 文本 |
| 42 | activityActivityConfidence(Z) | 分类置信度(0–2) | 枚举 |
| 43 | activityActivityStartDate(txt) | 分类起始时间 | 文本 |
| 44–52 | pedometer*(StartDate,NumberofSteps,AverageActivePace,CurrentPace,CurrentCadence,Distance,FloorAscended/Descended,EndDate) | 计步器输出 | 见括号 |
| 53–56 | altimeter*(Timestamp,Reset,RelativeAltitude,Pressure) | 气压高度计 | m / kPa |
| 57–58 | batteryState(N), batteryLevel(R) | 电池状态/电量 | 枚举 / 比例 |

`activity(txt)`:约 **89% 为 `unknown`**(实证,S5),是 Core Motion 分类器的固有行为,非数据损坏。

---

## 5. `_F` vs `_T` 文件

| | `_F` | `_T` |
|---|---|---|
| 数量 | 50 | 33 |
| 分隔符 | 逗号 `,` | 分号 `;`(4 个损坏文件例外) |
| 采样率(实测) | ≈ **99.5 Hz** | ≈ **29.7 Hz** |
| 时长 | ~1 分钟(activity fragment) | ~40–60 分钟 |
| 依据 | 实证(S3) | 实证(S3) |

> **F / T 两字母的字面含义 `unresolved`**:数据只能证明采样率/时长差异,无原始证据说明 F、T 分别代表什么(论文2 称 "F-task/T-task",week2 称"片段/一小时聚合",均为推测,不写入结论)。

---

## 6. 数据质量问题(全部从原始数据独立复算)

| 问题 | 事实 | 依据 |
|---|---|---|
| 字节级重复的 `_T` | **C28_T == Y54_T**、**Z5_T == Z14_T**(字节级 md5 重算相同,非仅信 md5sums.txt) | 自证(C9) |
| ID 不一致 | 临床表用 `Q27`,传感器文件用 `Z27` — 同一孩子 | 实证(C9) |
| 越界值 | S32 的 SDQ8 = 13(任何 SDQ 编码下都非法) | 实证(C2) |
| 问卷缺失(全有或全无) | 9 人无 SNAP、8–9 人无 SDQ;身高体重缺 6、BMI 缺 5(H46 有 BMI 无身高体重) | 实证(C8) |
| 损坏表头的 `_T` | L51/T20/X31/Z7 为逗号分隔且表头错乱(需按列位移植参考表头修复) | 见 `10_data_verify.ipynb`(待独立复算) |
| 列数口径 | 数据每文件 **58 列**;论文2 称"55 列" | 实证(以数据为准) |

---

## 7. 与二级结论(week2.pptx / notebook)的冲突裁决

| 主题 | 二级结论说 | 原始数据/复现说 | 裁决 |
|---|---|---|---|
| **SDQ hyperactivity 题号** | week2 slide6:"hyperactivity 子量表 = **SDQ11–SDQ15**,完整未受影响" | 收敛效度 A(2,10,15,21*,25*) ρ=+0.574 vs B(11–15) ρ=+0.305;缺号在 19 证明用原始题号 | **week2 错**。hyperactivity = SDQ2,10,15,21*,25*。`00_explore.ipynb` 用的是正确的 2,10,15,21,25 |
| SDQ 编码偏移 | week2:标准 0/1/2,数据 1/2/3,常数偏移可恢复 | 数据取值 `{1,2,3}` ⇔ 3 档 | **week2 对** |
| S32/SDQ8=13 异常 | week2:非法值,未做校验 | 实证确认 | **week2 对** |
| SNAP 尺度用于算分 | notebook/week2 倾向减 1 到 0–3 | 复现证明两篇论文都用原始 1–4、未减 1 | 取决于对齐对象(见 §3);做论文复现时**不减 1** |
| 分析用 n | week2 slide10:n=24 | 有 `_T` 且可用者 24;但临床/复现的 n 另计(见 §0、§3) | 语境不同,均成立 |

---

## 8. 已解决 / 未解决

**已解决(confirmed)**:BMI/身高/体重列及单位(自证);SDQ/SNAP 为 1-indexed 且标准分=数据−1;SDQ 列用原始题号、hyperactivity=2,10,15,21*,25*;SNAP 三子量表;两篇论文的算分/标签规则(均用原始尺度、论文2 缺失→0);传感器 raw/user/gravity/quaternion 各列(自证恒等式);`_F`/`_T` 采样率与时长;两对 `_T` 重复;Q27=Z27;S32 异常;58 列。

**未解决(unresolved)**:
- `F` / `T` 两字母的字面所指(仅知采样率/时长差异)。
- 论文2 "55 列"与数据 58 列的差异(可能丢弃了 3 个文本列,未在论文明确)。
- ID 首字母(H/Z/C…)是否编码站点/批次等信息 — 无原始证据。
- 论文各自 N(52 / 50)的确切纳入名单 — 论文未公布 roster,本数据可复现其统计量但 roster 有 ±1 出入。
- 损坏 `_T` 表头修复仅沿用 `10_data_verify.ipynb` 逻辑,尚未在本轮独立字节级复算。

---
*复算命令:`.venv/bin/python 20_codebook_verify.py`(全部 PASS / 与目标逐位一致)。*
