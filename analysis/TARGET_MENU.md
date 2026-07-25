# 目标菜单(阶段2产物)

- 连续目标:`analysis/40_targets.py` → `analysis/targets.csv`(24 人 × 10 列,标准尺度)。
- 题目级标准分:`analysis/40_targets.py` → `analysis/items.csv`(24 人 × 50 列:SNAP 26 题 0–3、SDQ 24 题 0–2,反向题已翻转)。标签引擎按题计数(`symptom_count` 切法)时读它,不碰 `data/` 里的原始问卷。
- 分组标签:`analysis/43_target_labels.py` → `analysis/target_labels.csv`(24 人 × 31 列)。
  **TASK-8 起该脚本是规则表驱动的引擎,切点数字一个都不在代码里**:切法/切点/组数/出处全写在 `analysis/labels/rules.yaml`(规则表)、`analysis/labels/norms.csv`(常模数值表)、`analysis/labels/sources.csv`(出处表)。改切法 = 改这三张表,不动代码。
- 标签元数据:`analysis/target_labels_meta.csv`(每条规则一行:method、params、各组人数、`degenerate`/`constant` 标记、`source_id` 与文献全称)。"这列怎么切的、依据是谁"跟着数据走,不必回去读代码。下游 `44`/`45` 按其中的 `degenerate` 字段剔除退化列。
- 样本 = 24 人(同 features.csv)。标准计分见 CODEBOOK §1(数据 1-indexed,标准分=数据−1;SDQ 反向题 7/11/14/21/25 标准分=3−数据)。

---

## 0. 计分口径:本项目已对齐到量表规范标准分

**(1) 整个数据集已对齐到量表的规范标准分。** 原始 CSV 里问卷每题是从 1 起存的(SNAP-IV `a1`–`a26` 取值 1–4,SDQ `SDQ1`–`SDQ25` 取值 1–3;见 CODEBOOK §1)。本项目在 `analysis/40_targets.py` 里把每题**减 1**,回到量表规范的 0 起点(SNAP-IV 每题 0–3,SDQ 每题 0–2),SDQ 的 5 道反向计分题(SDQ7、11、14、21、25)再翻转为 `2−标准分`(等价于 `3−存储值`)。本文档第 1 节表格里的所有理论范围与实测值,以及第 3 节所有标签列,都是在这套标准分上算的。

**(2) 这与本项目复现的两篇论文的口径不同。** 两篇论文都用**原样存储值(as-stored)**、不减 1(CODEBOOK §3 已由复现其 published 数字确证):论文1 的 SNAP 总分是 1–4 尺度直接求和(≈43,本数据复现 44.16±10.28,而非减 1 后的 ~18);论文2 的 ADHD 分组阈值是"每题原始均值 ≥1.67"(在 0–3 标准分尺度上该阈值会变成 1,不成立)。所以**本项目的目标分数值不能与这两篇论文的数值直接对比**——同一个孩子的 SNAP 分数,本项目口径 = 论文口径 − 题数(总分 26 题即低 26 分,各子量表低 9/9/8 分),是固定偏移;SDQ 含反向题的子量表**不是固定偏移**(正向题 `x−1`、反向题 `3−x`,两者方向相反),两种口径下的分数无法用一个常数换算。第 2 节的 `__normT55` 切法用的是 T 分,T 分对整体平移不变,故该列不受口径差异影响。

**(3) 这样做是为了匹配现行研究通用的标准切点(threshold)。** 量表的常模切点都定义在规范标准分上,不减 1 就无法套用。这直接服务于后续要做的**中国常模切点分类**(另一路的 Q-2 / ISSUE-7 → TASK-9:按中国常模把样本分成"正常 / 高度疑似 ADHD / ADHD"三组;常模数值已收在 `analysis/chinese_norms.md`)。

> 已知的一个后果:按 `analysis/chinese_norms.md` 的"SDQ 多动子量表标准分 ≥8 = 异常"这条线,本样本 **0/24 人达标**,该切法退化、未生成标签列(见第 2 节被划掉的 `__norm8` 行)。

口径由 ISSUE-117 拍板(用户裁决=用标准计分),本节即 TASK-104 的落点。

---

## 1. 连续目标 y(10 个,回归直接用)

| 列名 | 量表 | 子量表 | 题目 | 每题分 | 理论范围 | 本样本实测(min–max, 中位) |
|---|---|---|---|---|---|---|
| `snap_inatt` | SNAP-IV | 注意力缺陷 | a1–a9(9题) | 0–3 | 0–27 | 1–19,中位 6.5 |
| `snap_hyper` | SNAP-IV | 多动/冲动 | a10–a18(9题) | 0–3 | 0–27 | **0–14**,中位 4 |
| `snap_odd` | SNAP-IV | 对立违抗 | a19–a26(8题) | 0–3 | 0–24 | 1–16,中位 6 |
| `snap_adhd_total` | SNAP-IV | ADHD 总分(注意力+多动) | a1–a18(18题) | 0–3 | 0–54 | 1–33,中位 12 |
| `sdq_hyper` | SDQ | 多动 | 2,10,15,21*,25* | 0–2 | 0–10 | 0–7,中位 3 |
| `sdq_emo` | SDQ | 情绪症状 | 3,8,13,16,24 | 0–2 | 0–10 | 0–5,中位 1.5 |
| `sdq_cond` | SDQ | 品行问题 | 5,7*,12,18,22 | 0–2 | 0–10 | 0–4,中位 2 |
| `sdq_peer` | SDQ | 同伴问题 | 6,11*,14*,23(**缺19**) | 0–2 | 0–8 | 0–3,中位 2 |
| `sdq_pro` | SDQ | 亲社会 | 1,4,9,17,20 | 0–2 | 0–10 | 2–10,中位 9 |
| `sdq_totdiff` | SDQ | 总困难 | 情绪+品行+多动+同伴 | — | 0–40(此处缺1题) | 3–16,中位 9 |

`*`=反向计分题。**`snap_hyper` 实测 0–14 = Daniel 说的"0 到 14 全范围回归"目标。**
`sdq_peer` 因数据缺 SDQ19,只有 4 题(理论 0–8)。

## 2. 切法后缀(标签列名 = `{目标}__{切法}`)

| 后缀 | 切法 | 组数 | 依据 | 可辩护性 |
|---|---|---|---|---|
| `__qbin` | 中位数二分 | 2 | 样本内中位数 | 相对排名,永远成立 |
| `__qter` | 三分位 | 3 | 样本内 33/67 百分位 | 相对排名 |
| `__qquar` | 四分位 | 4 | 样本内 25/50/75 百分位 | 相对排名 |
| ~~`__norm8`~~ | SDQ常模异常≥8 | — | 大陆家长版 22,108 人常模(PMC4054577) | **退化:0/24 达标 → 不写进 `target_labels.csv`**(规则的 `on_degenerate: skip`);但规则本身仍在 `rules.yaml` 里、并在 `target_labels_meta.csv` 留一行记着 `degenerate=true, group_sizes={0:24, 1:0}` |

分位数切法用 `pd.qcut(..., duplicates='drop')`:目标唯一值太少时并列会把边界丢掉,实际组数 < 目标组数(下表标出)。

`degenerate` 的判定口径(TASK-8 决定5):**声明要切 k 组、结果 0..k−1 里有组 0 人**。30 个分位列中有 6 列命中(`sdq_emo__qquar`、`sdq_cond__qter`、`sdq_peer__qter`、`sdq_peer__qquar`、`sdq_pro__qter`、`sdq_pro__qquar`),它们照常写进标签表并被标记;这 6 列没有一列是常数列,且本来就都不在 `44`/`45` 用的目标列表里,所以按 `degenerate` 过滤对现有建模结果是零影响。

> 2026-07-25 计数订正(执行 TASK-109 时实测):上一段原写"现有 31 列中有 6 列命中"。**"31 列"与"6 列"两个数都已过期**——现产出 39 列、命中 13 条规则。多出的 7 条命中全部来自下面「计数订正」提到的那 9 条新增规则:`sdq_hyper__cn2013band3`、`sdq_cond__cn2013band3`、`sdq_peer__cn2013band3`、`sdq_pro__cn2013band3`、`sdq_totdiff__cn2013band3`、`snap_hyper__dsm_count7`,外加一直存在但不写进标签表的 `sdq_hyper__norm8`。其中 `sdq_peer__cn2013band3`、`sdq_totdiff__cn2013band3`、`snap_hyper__dsm_count7`、`sdq_hyper__norm8` 是**常数列**。逐条实况以 `analysis/target_labels_meta.csv` 的 `degenerate`/`constant` 两列为准。

## 3. 实际生成的标签列(各组人数 / 退化标记)

> 2026-07-25 计数订正:本节标题原写"31 个标签列",实测 `43_target_labels.py` 现产出
> **39 列**(`analysis/target_labels.csv` 形状 24×39)。差额 9 列是冻结这张表之后新增的规则:
> `sdq_{hyper,emo,cond,peer,pro,totdiff}__cn2013band3`(6 列,TASK-9 中国常模三分组)与
> `snap_{inatt,hyper}__dsm_count7`、`snap_odd__dsm_count5`(3 列,Huang 2023 症状计数)。
> **下表只逐行列出 30 个分位列**,那 9 列未逐行补齐(补不补属另一件事,未在 TASK-109 范围内)。

| 标签列 | 切法 | 各组人数 | 备注 |
|---|---|---|---|
| `snap_inatt__qbin/qter/qquar` | 2/3/4 | 12·12 / 8·8·8 / 8·4·6·6 | 干净 |
| `snap_hyper__qbin/qter/qquar` | 2/3/4 | 13·11 / 11·6·7 / 11·2·7·4 | 干净(多动主目标) |
| `snap_odd__qbin/qter/qquar` | 2/3/4 | 15·9 / 8·10·6 / 7·8·3·6 | 干净 |
| `snap_adhd_total__qbin/qter/qquar` | 2/3/4 | 12·12 / 8·8·8 / 7·5·7·5 | 干净 |
| `sdq_hyper__qbin/qter/qquar` | 2/3/4 | 14·10 / 8·8·8 / 8·6·6·4 | 干净 |
| `sdq_totdiff__qbin/qter/qquar` | 2/3/4 | 15·9 / 9·8·7 / 7·8·5·4 | 干净 |
| `sdq_emo__qbin/qter` | 2/3 | 12·12 / 8·9·7 | 干净;**四分塌成3组** |
| `sdq_emo__qquar` | 4→3 | 12·6·6 | ⚠ 并列,只 3 组 |
| `sdq_cond__qbin` | 2 | 16·8 | 干净 |
| `sdq_cond__qter` | 3→2 | 16·8 | ⚠ 塌成 2 组 |
| `sdq_cond__qquar` | 4 | 6·10·7·1 | ⚠ 末组仅 1 人 |
| `sdq_peer__qbin` | 2 | 18·6 | 偏斜 |
| `sdq_peer__qter/qquar` | 3/4→2 | 18·6 | ⚠ 都塌成 2 组 |
| `sdq_pro__qbin` | 2 | 15·9 | 干净 |
| `sdq_pro__qter` | 3→2 | 11·13 | ⚠ 塌成 2 组 |
| `sdq_pro__qquar` | 4→3 | 6·9·9 | ⚠ 只 3 组 |

## 4. 阶段3 的用法约定(据本表)
- **多分类目标**只用能干净切出 k 组的:`snap_inatt/hyper/odd/adhd_total`、`sdq_hyper`、`sdq_totdiff`(与 `45_multivariate_cv.py` 的 `MULTI` 列表同名单)。
- **SDQ 情绪/品行/同伴/亲社会**:唯一值太少 → **只做二分 + 回归**,不做三/四分类(标注⚠的列不喂多分类)。
- **主目标 = 4 个**(ISSUE-116 于 2026-07-25 裁定;此前写的"主目标 = `snap_hyper`"是被本次裁决取代的旧口径):
  `snap_inatt`(SNAP 注意力,a1–a9)、`snap_hyper`(SNAP 多动冲动,a10–a18)、
  `sdq_hyper`(SDQ 多动/注意力,题 2/10/15/21*/25*)、`snap_adhd_total`(SNAP a1–a18,0–54)。
  其余 6 个(`snap_odd`、`sdq_emo`、`sdq_cond`、`sdq_peer`、`sdq_pro`、`sdq_totdiff`)**保留为对照/探索性**,
  不删——ISSUE-103 要判定"运动信号是 ADHD 专属还是跨子量表共病",必须有非 ADHD 子量表当对照。
  主家族检验规模:4 主目标 × 351 特征 = 1,404 次(TASK-108 完成后 4 × 571 = 2,284 次)。
- 负对照目标侧:所有分组都会和"打乱 y 的置换基线"比。
