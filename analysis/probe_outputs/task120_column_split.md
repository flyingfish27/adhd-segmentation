# TASK-120 证据快照:把 `A_univariate.csv` 的 `rho` 列拆成 `rho` + `auc`

> **勿手改。要更新就重跑下面的命令覆盖本文件。**
>
> - **产出脚本**:`analysis/probe_outputs/task120_column_split_check.py`
> - **被验证的改动**:`analysis/44_univariate_screen.py`(拆列)
> - **本快照产出时所在 commit(改动尚未提交,故为父提交)**:`c0cc6ff`
> - **复现命令**(在仓库任意检出里):
>   ```
>   .venv/bin/python analysis/44_univariate_screen.py      # 重跑 A 轨,约 60 秒
>   .venv/bin/python analysis/probe_outputs/task120_column_split_check.py
>   ```
> - **比对基准**:脚本默认执行 `git show c0cc6ff:analysis/A_univariate.csv`
>   取改动前那份表。**不另存归档件** —— 它已在 git 历史里,且与本次产物数值完全相同,
>   没有新的存证价值(与 `archive/A_univariate__608feat_NPERM5000.csv` 不同:那一份的
>   数值【真的不一样】,因为置换次数变了)。

---

## 一、这次改的是什么

改动前 `analysis/A_univariate.csv` 有一列叫 `rho`,它**装两种不同的量**:

| 行的类型 | `rho` 列里装的 | 无效应基准 | 取值范围 |
|---|---|---|---|
| `type=cont`(连续目标) | Spearman ρ | **0** | [−1, +1] |
| `type=bin`(二分目标) | AUC | **0.5** | [0, 1] |

改动后拆成两列,各只在对应的行有值、另一半留空(NaN):`rho` 只在连续行、`auc` 只在二分行。

**为什么必须改(有实证)**:2026-07-29 管理窗口查「目前最好的结果是什么」,按 `|rho|` 排序
取前 5 条,**排出来的是错的** —— 二分行 AUC=0.12(即 |AUC−0.5|=0.38,很强的**反向**关系)
被排到末尾,而 AUC=0.55(几乎无效应)排在它前面。任何人用 Excel 打开这张表按 `rho` 排序
都会重演这个错误。**文档保护不了文件**——这是选「改列名」而不是「加文档警告」的理由。

---

## 二、验收:逐格比对的原样输出

性质要求:**改动前的 `rho` 列 == 改动后的 `rho`(连续行)与 `auc`(二分行)拼起来,其余每列逐格相同。**
若不满足,说明改动意外碰到了数值路径,那就不是表达层改动。

```
==============================================================================
TASK-120 验收:rho 列拆成 rho + auc,数值是否一格未变
==============================================================================
改动前: git show c0cc6ff:analysis/A_univariate.csv
        12160 行 x 10 列  列名 = ['target', 'type', 'feature', 'rho', 'perm_p', 'loo_r2cv', 'loo_rmse', 'loo_mae', 'rho_partial_uamag', 'q_fdr']
改动后: /Users/shiyu/Projects/adhd-segmentation/.claude/worktrees/task-120-rho-auc/analysis/A_univariate.csv
        12160 行 x 11 列  列名 = ['target', 'type', 'feature', 'rho', 'auc', 'perm_p', 'loo_r2cv', 'loo_rmse', 'loo_mae', 'rho_partial_uamag', 'q_fdr']

  [通过] 行数相同   12160 vs 12160
  [通过] 每一行的身份(target,type,feature)逐行相同、顺序也相同
  [通过] 改动后的列 = 改动前的列 + 一列 auc   新增 ['auc']  消失 []
  [通过] 连续行的 auc 全为空   非空 0 个
  [通过] 二分行的 rho 全为空   非空 0 个
  [通过] 连续行的 rho 全有值   为空 0 个
  [通过] 二分行的 auc 全有值   为空 0 个
  [通过] 合成后的一列 == 改动前的 rho 列(逐格,含 NaN 位置)   不同 0 格
  [通过] 列 'target' 逐格相同   不同 0 格
  [通过] 列 'type' 逐格相同   不同 0 格
  [通过] 列 'feature' 逐格相同   不同 0 格
  [通过] 列 'perm_p' 逐格相同   不同 0 格
  [通过] 列 'loo_r2cv' 逐格相同   不同 0 格
  [通过] 列 'loo_rmse' 逐格相同   不同 0 格
  [通过] 列 'loo_mae' 逐格相同   不同 0 格
  [通过] 列 'rho_partial_uamag' 逐格相同   不同 0 格
  [通过] 列 'q_fdr' 逐格相同   不同 0 格

==============================================================================
总判定:全部通过 —— 这次改动只改了列的组织方式,一个数都没变。
==============================================================================
退出码 = 0
```

**判定:17 项全部通过,0 格不同。** 这次改动只改了列的组织方式,一个数都没变。

---

## 三、重跑耗时(实测)

```
/Users/shiyu/Projects/adhd-segmentation/.venv/bin/python analysis/44_univariate_screen.py
  59.86s user 0.96s system 102% cpu 59.059 total
```

与 TASK-106 记录的 52 秒同量级(那次也是 `NPERM=100000`)。差值来自本机当时的负载,
不来自改动 —— 拆列不增加任何计算。

**A 轨为什么置换 10 万次也只要 1 分钟**:置换零分布**每个目标只算一次、608 个特征共用**
(`44_univariate_screen.py` 头部第 5 行明写),所以零分布总共只算 **20 次**(10 连续 + 10 二分),
不是 12,160 次;且连续目标的留一用闭式 PRESS 公式,不反复拟合。

---

## 四、在 worktree 里跑通,顺带证伪了脚本注释里的一句话

本次在 worktree `task-120-rho-auc` 里跑,**没有设 `ADHD_ROOT`**,直接跑通。

这**证伪**了 `44_univariate_screen.py` 原注释里的一句话:「`analysis/features.csv` 未入版本控制、
只存在于主检出;在 worktree 里跑请用环境变量指过去」。**该句已过期** —— `features.csv`
已于 2026-07-28(TASK-5,commit `b135aae`)入版本控制,故它在每个 worktree 里都在位。
实测桌上 `features.csv` 的 md5 与主检出一致:`6d36ee888f6d73647609b91eb85025e5`。
脚本注释与 assert 的提示语已在本次一并订正(原文保留 + 内联括注)。

---

## 五、本次【没有】处理的一件,知情保留

`rho_partial_uamag` 这一列**有和拆列前的 `rho` 完全一样的双含义问题**:

| 行的类型 | `rho_partial_uamag` 里装的 | 无效应基准 |
|---|---|---|
| `type=cont` | 控制运动总量后的偏相关 | **0** |
| `type=bin` | 残差化后的 AUC | **0.5** |

**按这一列排序,会重演 TASK-120 刚修掉的那个错误。**

本次**没拆**,因为 TASK-120 的登记范围只写了 `rho` 列。**去向未定**,选项与各自后果记在
`working/task.md` 的 TASK-120 条目里。
