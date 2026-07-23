# DOC_SYSTEM.md — 本项目的文档与工作流体系

> 本文件是**自足的说明书**：给未来的我、或任何**没有上下文的 agent**，一次讲清这个项目"用哪些文件、按什么规则记录问题/任务/决策、怎么流转与归档"。
> 读完这一篇，就能接手维护本项目的文档体系，无需追溯聊天记录。
> 建于 2026-07-20。

---

## 0. 一句话

用**三层文件**把工作留痕，使**每一个决策和改动都可追溯**——将来任何人问"这里当时为什么这么做"，都能从文件里清楚讲出，而不靠记忆或翻聊天记录。

核心原则：**在做决定的当下就把"为什么"写进进版本库的文件；只进不出（append-only）；关闭的条目沉底，第一屏永远是"还欠什么"。**

---

## 1. 三层功能模型（按功能分，不按"做没做完"分）

```
┌─ 追踪层 (tracker) ── 每天动，回答"我还欠什么" ──────────────────┐
│   working/issue.md      问题清单（等裁决）                        │
│   working/task.md       任务清单（执行进度的唯一真相源）           │
│   working/backlog.md    推迟项 + 未排期的建设工作                  │
└──────────────────────────────────────────────────────────────┘
┌─ 知识层 (docs) ── 长期活着、原地更新，"是什么 / 为什么这么定" ────┐
│   README.md             （待建）清单本身的知识（从 INVENTORY 拆出）│
│   docs/decisions/*.md   （待定）ADR：方向性、约束未来的决定        │
│   INVENTORY.md          清册 + 勘误决策日志（收割时拆解，见 §6）    │
│   DOC_SYSTEM.md         本文件：体系说明                           │
└──────────────────────────────────────────────────────────────┘
┌─ 历史层 (git) ── 自动审计，每次改动的完整轨迹 ──────────────────┐
│   commit + message      改动动机（"为什么这么改"）                │
│   CHANGELOG（可选）     从 git 人工提炼的可读切片 = "更新日志"     │
└──────────────────────────────────────────────────────────────┘

冻结 (archival)：只有"每轮收割快照"才冻结，靠 git tag，或存 archive/2026-07-round1.md。
知识层不是 archival——它是活的、原地更新的。
```

**关键澄清**：常见误区是把"归档(冻结)"和"知识(长期)"混为一谈。知识层长期**活着**；真正冻结不动的只有"每轮清单快照"。

---

## 2. 两种条目 · 两种生命周期

项目里的"事情"分两类，各有独立文件、独立状态词汇（**零重合**）。

### 2.1 问题（Issue）— `working/issue.md`

**使命**：等用户裁决。**拍板即关闭**——裁决一出立即关闭、沉入 Resolved，**不跟踪后续执行**。

**生命周期**：`待确认` → `待拍板` → `已裁决`

`已裁决` 的 6 种 resolution（借 Jira 并按本项目扩展）：

| resolution | 含义 | 落点 | 是否生任务 |
|---|---|---|---|
| **Fixed** | 拍板=修 | `TASK-m` | **是**（当即关闭，不回填进度）|
| **Won't Fix** | 决定不修 | — | 否（裁决理由留档，防日后重新恐慌）|
| **Duplicate** | 与某条重复 | `ISSUE-x` | 否 |
| **Cannot Reproduce** | 复现不了 | — | 否 |
| **Works as Designed** | 本来如此，不是 bug 是特性 | — | 否 |
| **Deferred** | 推迟 | `backlog` | 否 |

> **要点**：Fixed 的 issue 落点填 `TASK-m` 后**立即关闭、永不回填**。执行进度的**唯一真相源是 task.md**。issue 上**不得出现** `待做/进行中/已解决` 这些任务词汇。

### 2.2 任务（Task）— `working/task.md`

**使命**：跟踪"要做的活"，是**执行进度的唯一真相源**。

**生命周期**：`待做` → `进行中` → `已解决`，终局另有 `取消`（取消须写原因）。

**两种来源**：
1. 某个 issue 拍板=Fixed 转来（`来源: ISSUE-n`）；
2. **主动规划的建设工作**（如 inventory / 代码分层 / 切依赖 / 做 pipeline）——不是因为"错了"，而是主动建设，**无裁决态，只需排期执行**。

> **为什么分两个文件**：问题不一定变任务（Won't Fix 也要留裁决档）；任务不一定来自问题（建设工作）。两种不同生命周期，两个文件，状态词汇零重合。

---

## 3. 编号与追溯链

- **编号前缀式**：`ISSUE-1`、`TASK-1`（回链不混淆）。
- **追溯链单向**：`ISSUE → TASK → commit`。
  - issue 关闭时，落点写 `TASK-m`（一次，不回填）；
  - task 有 `来源: ISSUE-n`（回指来源）；
  - task 关闭时，落点写 `commit <hash>`（一次）。
- 于是：从 task 能找到来源 issue 与落地 commit；追 `ISSUE→commit` 就走 `ISSUE→TASK→commit`。**每环只在自己关闭时写一次自己的落点。**

---

## 4. 条目模板（copy-paste）

**issue.md 条目**：
```
### [ISSUE-n] 一句话标题
- 状态: 待确认 | 待拍板 | 已裁决(<resolution>)
- 问题: 原始发现，永不修改
- 结论: 怎么裁决的 / 为什么
- 落点: TASK-m / ISSUE-x / backlog / 无需改动
```

**task.md 条目**：
```
### [TASK-m] 一句话标题
- 状态: 待做 | 进行中 | 已解决 | 取消
- 来源: ISSUE-n / 主动规划
- 落点: commit <hash> / 取消原因
```

---

## 5. 纪律与流转规则

1. **只进不出（append-only）**：条目一旦写入不删除；`issue` 的「问题」原文永不修改。这是可追溯性的根基。
2. **标完结果后移入 Resolved 区**：每个清单文件**顶部只放未关闭条目**（issue: 待确认/待拍板；task: 待做/进行中），关闭的移到底部 `## Resolved`。**打开文件第一屏永远是"我还欠什么"** —— 这是清单可用性的关键。
3. **决策日志同规**：`INVENTORY.md` 的「勘误记录」是决策日志，同样只增不删——结论被推翻也是**新写一条引用旧的**，绝不覆盖原文。

---

## 6. 每轮收割（harvest）与冻结

一轮工作结束时做一次**收割**，给每个条目一个"生命周期出口"：

1. 扫 Resolved 区，逐条问 **"这个结论以后还会被问起吗？"**
2. 会被问起的，**按类型分层沉淀**（不是所有结论都配写 ADR）：
   - **行级事实** → **代码注释**（写在相关那一行旁，如"此阈值单位是秒、换采样率无需改"）；
   - **改动动机** → **已在 commit message**，不用再动；
   - **方向性、约束未来的结论** → 此时才提炼成 **ADR**。
3. **冻结（双做）**：整份清单靠 **git tag** 冻结当轮状态；并可另存人读快照 `archive/2026-07-round1.md`。下一轮**开新清单文件**。

---

## 7. 每轮工作流（角色）

```
用户：打基线 commit（"checkpoint: 分流前"）
  ↓
agent：搭结构（建 working/ 三件套等）
  ↓
用户带领：逐条分流 —— 用户拍板，agent 落条目、连编号（ISSUE-/TASK-）
  ↓
用户：收官 commit（描述本轮成果）
  ↓
（轮末）收割 + 冻结
```

> 分流是**用户主导**：agent 不替用户裁决问题，只负责把裁决**准确落成条目**并维护链接。

---

## 8. 文件现状一览（2026-07-20）

| 文件 | 层 | 状态 |
|---|---|---|
| `working/issue.md` | 追踪 | 已建，空壳待分流 |
| `working/task.md` | 追踪 | 已建，空壳待分流 |
| `working/backlog.md` | 追踪 | 已建（原根目录 `BACKLOG.md` 移入），含未决事项与待定项 |
| `INVENTORY.md` | 知识/待拆 | 清册 + 勘误决策日志；收割时拆成 README（参考）+ ADR/决策 + archive（分析发现）|
| `DOC_SYSTEM.md` | 知识 | 本文件 |
| `README.md` | 知识 | **待建**（INVENTORY 拆解后的参考部分）|
| `docs/decisions/` | 知识 | **待定**（ADR 落地方式）|
| `archive/` | 冻结 | **待用**（每轮快照，或靠 git tag）|
| `CLAUDE.md` | 配置 | **待建/待配**（把本约定写给后续 agent，本轮不配）|

**已进 backlog 的体系类待定项**：ADR 落地方式、INVENTORY 拆解方案、CLAUDE.md 配置、`archive/PROBLEM_REGISTER.md` 与本体系的关系（该文件至今未读）。

---

## 9. 术语速查

- **issue / 问题**：待裁决的事；拍板即关闭。
- **task / 任务**：要做的活；执行进度唯一真相源。
- **resolution**：issue 关闭方式（Fixed/Won't Fix/Duplicate/Cannot Reproduce/Works as Designed/Deferred）。
- **落点**：一个条目关闭时指向的去处（TASK-m / ISSUE-x / commit / backlog / 无需改动）。
- **收割 (harvest)**：轮末把 Resolved 结论分层沉淀（注释/commit/ADR）再归档。
- **只进不出 (append-only)**：条目/决策不删不改原文，只追加。
- **ADR**：Architecture/Any Decision Record，记"方向性、约束未来"的决定；社区惯例放 `docs/decisions/`。

---

## 10. 仓库物理结构 —— 目标蓝图（理想态）

**心智模型（全局观）**：项目 = **一条流水线（数据→代码→结果）** + **三样支撑（文档·过程·存档）**。仓库里**每个文件只属于下面 6 类之一**；"乱"= 这 6 类物理上混在一起。

### 目标树

```
adhd-segmentation/
├── data/                    # ① 原料：原始只读(已隔离，不动)
├── src/                     # ② 代码：生产 pipeline(重构后)
│   ├── data_prep/           #     L1 清洗/QC/24人名单(现 10_* notebook)
│   ├── features/            #     L2 特征(现 42)
│   ├── targets/             #     L3 目标/标签(现 40,43)
│   └── modeling/            #     L3 A/B 轨(现 44,45)
├── exploration/             #    L0 一次性探针/验证(00,20–34,consistency,verify_*)
├── outputs/                 # ③ 产物：可重生成
│   ├── tables/              #     features/targets/labels/A/B/temporal/fingerprints/subject_audit
│   └── figures/             #     *.png
├── docs/                    # ④ 文档：知识层
│   ├── CODEBOOK.md  PAPER_DATA_USAGE.md
│   ├── menus/               #     FEATURE/MODEL/TARGET_MENU  chinese_norms
│   ├── decisions/           #     ADR(待建)
│   ├── literature/  refs/   #     文献 + ref
├── working/                 # ⑤ 过程：追踪层(issue·task·backlog·checkpoint)
├── archive/                 # ⑥ 存档：废弃脚本(41) + 孤儿 + 每轮快照
├── presentation/            #    汇报件(pptx / 一页概览)
├── INVENTORY.md  DOC_SYSTEM.md  README.md   # 顶层导航
└── requirements.txt
```

### 现状 vs 目标

- **已到位**：`data/`、`working/`、`presentation/`。
- **未建**：`src/`、`exploration/`、`outputs/`、`docs/`、`archive/`。

### 为什么不能一次搬到位（关键约束）

移动**代码/产物**会**静默打断硬编码路径**（脚本里路径写死、且不一致：有的绝对、`20_*` 用 `__file__` 相对）。故整理**分两批**：

- **安全批**（无代码依赖，可随时手动搬）：`literature/`、`ref/`、`CODEBOOK`、`PAPER_DATA_USAGE`、`*_MENU`、`chinese_norms` → `docs/`；`consistency_explained.py`、`fingerprints.csv` → `archive/`。
- **耦合批**（会断路径，须随 **pipeline 重构 + 路径参数化** 一起搬）：主链路代码 → `src/`；所有产物 csv → `outputs/`；`figures/subject_audit.csv` 挪位；`INVENTORY/DOC_SYSTEM/working` 若搬须同步改交叉链接。

详细"能搬/不能搬"清单见 `working/backlog.md` §2「仓库结构整理」与 `working/checkpoint-2026-07-20.md`。

