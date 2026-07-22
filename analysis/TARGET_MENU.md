# 目标菜单(阶段2产物)

- 连续目标:`analysis/40_targets.py` → `analysis/targets.csv`(24 人 × 10 列,标准尺度)。
- 题目级标准分:`analysis/40_targets.py` → `analysis/items.csv`(24 人 × 50 列:SNAP 26 题 0–3、SDQ 24 题 0–2,反向题已翻转)。标签引擎按题计数(`symptom_count` 切法)时读它,不碰 `data/` 里的原始问卷。
- 分组标签:`analysis/43_target_labels.py` → `analysis/target_labels.csv`(24 人 × 31 列)。
  **TASK-8 起该脚本是规则表驱动的引擎,切点数字一个都不在代码里**:切法/切点/组数/出处全写在 `analysis/labels/rules.yaml`(规则表)、`analysis/labels/norms.csv`(常模数值表)、`analysis/labels/sources.csv`(出处表)。改切法 = 改这三张表,不动代码。
- 标签元数据:`analysis/target_labels_meta.csv`(每条规则一行:method、params、各组人数、`degenerate`/`constant` 标记、`source_id` 与文献全称)。"这列怎么切的、依据是谁"跟着数据走,不必回去读代码。下游 `44`/`45` 按其中的 `degenerate` 字段剔除退化列。
- 样本 = 24 人(同 features.csv)。标准计分见 CODEBOOK §1(数据 1-indexed,标准分=数据−1;SDQ 反向题 7/11/14/21/25 标准分=3−数据)。

---

## 1. 连续目标 y(10 个,回归直接用)

| 列名 | 量表 | 子量表 | 题目 | 每题分 | 理论范围 | 本样本实测(min–max, 中位) |
|---|---|---|---|---|---|---|
| `snap_inatt` | SNAP-IV | 注意力缺陷 | a1–a9(9题) | 0–3 | 0–27 | 1–19,中位 6.5 |
| `snap_hyper` | SNAP-IV | 多动/冲动 | a10–a18(9题) | 0–3 | 0–27 | **0–14**,中位 4 |
| `snap_odd` | SNAP-IV | 对立违抗 | a19–a26(8题) | 0–3 | 0–24 | 1–16,中位 6 |
| `snap_total` | SNAP-IV | 总分 | a1–a26(26题) | 0–3 | 0–78 | 4–48,中位 15.5 |
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
| `__wang2025T55` | 样本内 z/T 分二分 | 2 | SNAP总分→T分,T≥55 | **论文1(Wang, Sensors 2025)的 ADHD 定义**(样本内重算,n=24≠论文 n=50)。TASK-8 决定2 由 `__normT55` 改名:mean/sd 取自这 24 个孩子自己、不是任何人群常模,"norm" 名不副实,实为样本内 z≥0.5 |
| ~~`__norm8`~~ | SDQ常模异常≥8 | — | 大陆家长版 22,108 人常模(PMC4054577) | **退化:0/24 达标 → 不写进 `target_labels.csv`**(规则的 `on_degenerate: skip`);但规则本身仍在 `rules.yaml` 里、并在 `target_labels_meta.csv` 留一行记着 `degenerate=true, group_sizes={0:24, 1:0}` |

分位数切法用 `pd.qcut(..., duplicates='drop')`:目标唯一值太少时并列会把边界丢掉,实际组数 < 目标组数(下表标出)。

`degenerate` 的判定口径(TASK-8 决定5):**声明要切 k 组、结果 0..k−1 里有组 0 人**。现有 31 列中有 6 列命中(`sdq_emo__qquar`、`sdq_cond__qter`、`sdq_peer__qter`、`sdq_peer__qquar`、`sdq_pro__qter`、`sdq_pro__qquar`),它们照常写进标签表并被标记;这 6 列没有一列是常数列,且本来就都不在 `44`/`45` 用的目标列表里,所以按 `degenerate` 过滤对现有建模结果是零影响。

## 3. 实际生成的 31 个标签列(各组人数 / 退化标记)

| 标签列 | 切法 | 各组人数 | 备注 |
|---|---|---|---|
| `snap_inatt__qbin/qter/qquar` | 2/3/4 | 12·12 / 8·8·8 / 8·4·6·6 | 干净 |
| `snap_hyper__qbin/qter/qquar` | 2/3/4 | 13·11 / 11·6·7 / 11·2·7·4 | 干净(多动主目标) |
| `snap_odd__qbin/qter/qquar` | 2/3/4 | 15·9 / 8·10·6 / 7·8·3·6 | 干净 |
| `snap_total__qbin/qter/qquar` | 2/3/4 | 12·12 / 8·8·8 / 6·6·7·5 | 干净 |
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
| `snap_total__wang2025T55` | 2 | 17·7 | 论文1 ADHD 口径(旧名 `snap_total__normT55`,TASK-8 决定2 改名,取值不变) |

## 4. 阶段3 的用法约定(据本表)
- **多分类目标**只用能干净切出 k 组的:`snap_inatt/hyper/odd/total`、`sdq_hyper`、`sdq_totdiff`。
- **SDQ 情绪/品行/同伴/亲社会**:唯一值太少 → **只做二分 + 回归**,不做三/四分类(标注⚠的列不喂多分类)。
- **主目标 = `snap_hyper`(多动,0–14)**;其余作共病对照,不预判"专属多动"。
- 负对照目标侧:所有分组都会和"打乱 y 的置换基线"比。
