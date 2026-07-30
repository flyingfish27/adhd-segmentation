# 证据快照:TASK-106 正式重跑(A 轨 + B 轨)与 NPERM 提高实验

- 运行日期: A 轨 2026-07-28(NPERM=5000)与 2026-07-29(NPERM=100000);B 轨 2026-07-28 19:36 → 2026-07-29 10:09
- 运行时仓库 commit: A 轨(5000 版)`c226242` · B 轨 `c3a4543` · A 轨(100000 版)`c3a4543` + 未提交的 NPERM 改动
- 产出脚本: `analysis/44_univariate_screen.py`(A 轨)· `analysis/45_multivariate_cv.py`(B 轨)
- 复现命令:
  ```bash
  .venv/bin/python analysis/44_univariate_screen.py     # A 轨，NPERM=100000 时 52 秒
  nohup caffeinate -i .venv/bin/python analysis/45_multivariate_cv.py > /tmp/b_track.log 2>&1 &   # B 轨
  ```
- 说明: 本文件是上述运行的**关键 stdout 摘录与实测对照**;完整原样日志同目录:
  `task106_a_track_nperm100k.log` · `task106_b_track.log`。勿手改,要更新就重跑覆盖。

## 一、实测耗时(推翻账本里的旧数)

| | 账本此前记的 | **实测** |
|---|---|---|
| A 轨(NPERM=5000) | 5.7 小时 / TASK-108 后 10.8 小时 | **5.0 秒**(`4.996 total`,135% cpu) |
| A 轨(NPERM=100000) | — | **52 秒**(`52.039 total`,103% cpu) |
| B 轨(NPERM=5000) | 约 14.7 小时 | **约 14.5 小时**(19:36 → 10:09) |

**账本里 A 轨那 5.7 / 10.8 小时全无实测来源**:引用链是循环的(`b_permutation_cost.md` 说出处是
`fdr_permutation_floor.md`,而后者不含任何耗时数字;TASK-106 条目又指回快照)。**已证伪。**

**A 轨为什么快**:置换零分布**每个目标只算一次、608 个特征共用**(脚本头部第 5 行明写),
且 `loo_simple_lr` 用闭式 PRESS 公式、不反复拟合。**A 轨没有并行(`n_jobs` 一处都没有),也不需要。**

**B 轨为什么慢**:每一次置换都要重跑一整轮 24 折留一 CV。实测单轮 CV 耗时
RandomForest **2.6 秒** vs ridge/svr **0.06 秒**(43 倍)。本次 43 个待检组合里 RF 占 16 个。

## 二、NPERM 提高前后的对照(A 轨)

| | NPERM=5000 | NPERM=100000 |
|---|---|---|
| 置换 p 下限 | 0.000200 | 0.000010 |
| q 天花板(m=608) | 0.1216 | 0.0061 |
| 打到下限的检验数 | 5 | 3 |
| 未校正 p<0.05 | 611(纯噪声期望 608) | 604(期望 608) |
| **BH-FDR q<0.05 存活** | **0** | **3** |
| q 最小值 | 0.06080 | 0.00608 |
| 耗时 | 5.0 秒 | 52 秒 |

**通过 FDR 的 3 条:**

```text
目标              特征                        类型   rho/AUC   perm_p     q_fdr
snap_adhd_total  frac_act_short_w10_p20    cont  +0.7718  0.000010  0.00608
snap_inatt       frac_act_short_w10_p20    cont  +0.7666  0.000010  0.00608
sdq_emo          act_bout_median_w0.5_p80  cont  +0.7720  0.000010  0.00608
```

**逐条查验(全部实测):**

- `snap_adhd_total` 与 `snap_inatt` **都是 ISSUE-116 预先锁定的 4 个确证主目标**;`sdq_emo` 属探索层。
- 前两条**是一个发现不是两个**:两目标间 ρ=+0.962(总分含注意力分)。`sdq_emo` 与它们 ρ=0.000 / −0.132,独立。
- `frac_act_short_w10_p20`:**24 人 22 个不同取值(非退化)**;与运动总量 `uaMag_median` 仅 ρ=−0.211;
  属**路径A**(每人自己的阈值)故 **R10 的合池泄漏问题不适用**。
- `act_bout_median_w0.5_p80`:**仅 4 个唯一取值、24 人里 14 人同值** —— ρ=0.772 很可能是并列驱动,**待单独核验**。
- **3 条的 perm_p 均仍卡在新下限 1e-5**:10 万次置换无一次超过它们,真实 p 可能更小。

## 三、B 轨结果(NPERM=5000,家族 m=192)

```text
main 臂 192 个组合   跑了置换 43 个   未跑 149 个(按 p=1 计入分母)
未校正 p<0.05 : 6      ★ BH-FDR q<0.05 : 0      q 最小值 = 1.0000
回归 skill>0 : 14/60   分类 bacc>0.5 : 29/132
```

**q 全为 1.0 的原因(算术)**:最小 p=0.0130,BH 给出 0.0130 × 192 ÷ 1 = 2.50 → 封顶 1.0。
要过 q<0.05 需最强 p ≤ 0.05/192 = 0.00026,**本次无一接近下限**。

**回归 top 3 / 分类 top 3:**

```text
sdq_emo          ridge  k=5   skill=+0.163  nc_skill=-0.061  skill_over_nc=+0.224  perm_p=0.0250  q=1.0
sdq_emo          ridge  k=10  skill=+0.155  nc_skill=-0.061  skill_over_nc=+0.215  perm_p=0.0206  q=1.0
snap_hyper       ridge  k=10  skill=+0.055  nc_skill=-0.070  skill_over_nc=+0.125  perm_p=0.0700  q=1.0

sdq_totdiff__qbin  rf   k=5   bacc=0.822  f1=0.822  perm_p=0.0130  q=1.0
sdq_totdiff__qbin  svm  k=5   bacc=0.767  f1=0.772  perm_p=0.0426  q=1.0
sdq_totdiff__qbin  logit k=5  bacc=0.689  f1=0.697  perm_p=0.0802  q=1.0
```

**断点续跑机制在本次运行中实际生效**:进度文件按 500 次一批更新,跑完后两个中间档被自动清除
(`.B_perm_progress.json` 与 `.B_multivariate.partial.csv` 均不存在 = 正常结束的确证)。

## 四、一处方法层记录:sklearn 的 matmul 警告是假警报

我在做计时测试时看到大量 `divide by zero / overflow / underflow / invalid value encountered in matmul`
(`sklearn/utils/extmath.py:203`),曾怀疑 608 列里有数值极端的列污染结果。**实测两条都不成立:**

1. **正式运行不产生这些警告**:`45_multivariate_cv.py` 第 50–52 行明确设了
   `warnings.filterwarnings("ignore")` + `np.seterr(all="ignore")`;
   14.5 小时那次的日志里警告数 **= 0**。警告是**我的测试脚本**没关掉才出现的。
2. **数据不极端**:标准化后全部 608 列的最大 |z| **只有 4.5**,|z|>10 的列 **0 个**。
   (我曾点名 `jerk_acf_tau_1e_s`(std=2.8e-06)—— 但 `StandardScaler` 是除以自己的标准差,
   原始尺度多小,除完都在同一量级。**这是我对标准化的理解错了。**)
3. **结果无污染**:ridge / svr 的预测**无 nan、无 inf**,范围分别 [1.16, 29.64] / [8.66, 14.86],
   落在真实 y 的 [1, 33] 内。
4. **触发模式说明它是平台假警报**:ridge 与 svr 各触发 96 条 = 24 折 × 4 种警告,
   **每折同时触发"除零+溢出+下溢+无效值"四种** —— 一次矩阵乘法不可能同时发生这四件事。
   判定为 **Apple Accelerate BLAS 置起 CPU 浮点异常标志位**、numpy 读到标志位报警,而计算结果正确。

**结论:不需要处置。** 但须知情:`45` 里那三行"关警告"在掩盖假警报的同时,**也会掩盖真问题**
—— 这是个知情的取舍,不是缺陷。
