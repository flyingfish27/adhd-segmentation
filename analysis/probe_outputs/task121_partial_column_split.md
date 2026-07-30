# TASK-121 证据快照:把 `rho_partial_uamag` 拆成 `rho_partial_uamag` + `auc_partial_uamag`

> **勿手改。要更新就重跑下面的命令覆盖本文件。**
>
> - **产出脚本**:`analysis/probe_outputs/task121_partial_column_split_check.py`
> - **被验证的改动**:`analysis/44_univariate_screen.py`
> - **本快照产出时所在 commit(改动尚未提交,故为父提交)**:`d23e68d`
> - **复现命令**(在仓库任意检出里):
>   ```
>   .venv/bin/python analysis/44_univariate_screen.py    # 重跑 A 轨,约 60~80 秒(三次实测 59.9 / 63.7 / 77.1 秒,差值来自本机负载)
>   .venv/bin/python analysis/probe_outputs/task121_partial_column_split_check.py
>   ```
> - **比对基准**:脚本默认执行 `git show d23e68d:analysis/A_univariate.csv`。
>   **不另存归档件** —— 与 TASK-120 同理,该表已在 git 历史里且数值完全相同。

---

## 一、这是 TASK-120 那个毛病的第二处

TASK-120 拆的是 `rho` 列。`rho_partial_uamag` 列**有完全一样的问题**:

| 行的类型 | 改动前 `rho_partial_uamag` 里装的 | 无效应基准 | 实测取值范围 |
|---|---|---|---|
| `type=cont` | 控制 `uaMag_median`(运动总量)后的**偏相关** | **0** | −0.530 ~ +0.451 |
| `type=bin` | **残差化后的 AUC**(先扣总量、再用残差算 AUC) | **0.5** | 0.185 ~ 0.861 |

这一列**只有「路径B」那 45 个特征有值**(24 人合池共同阈值,最可能混进运动总量),
其余 563 个特征该格为空。全表 12,160 行里**有值的是 900 行**(45 特征 × 20 目标)。

## 二、实测:按 `|值|` 排序会错成什么样

拿这 900 个格子实测(**改动前的表**),假设有人按 `|值|` 从大到小排——最自然的动作:

- **前 50 名,50 个全是 `bin` 行;450 个 `cont` 行一个都进不去。**
  机制:`bin` 的数绕着 0.5 转,`|值|` 天然在 0.5 上下;`cont` 的数绕着 0 转,`|值|` 最大只 0.53。
  **排序变成了"先按行的类型分堆",不是按关系强弱排。**

| 这一条 | 正确口径的排名 | 按 `\|值\|` 排的排名 | 差 |
|---|---|---|---|
| `actfrac_p60` × `snap_hyper`(cont,值 −0.530) | **第 1 名** | 第 168 名 | 掉 167 位 |
| `actfrac_p90` × `snap_odd__qbin`(bin,值 0.185 ⇒ \|0.185−0.5\|=0.315) | 第 66 名 | **第 616 名** | 掉 550 位 |
| `actshort_p10` × `sdq_cond__qbin`(bin,值 0.719) | 第 161 名 | **第 8 名** | 升 153 位 |

> `actfrac_p90 × snap_odd__qbin` 那条要特别看:`bin` 行里**小于 0.5 是很强的反向关系**
> (高分组孩子这个特征反而更小)。0.185 离 0.5 有 0.315,是 `bin` 行里第二强的;
> 但因为 0.185 这个数**本身小**,按 `|值|` 排它掉到第 616 名——**最强的信号之一被排成倒数**。

## 三、验收:逐格比对的原样输出

```
==============================================================================
TASK-121 验收:rho_partial_uamag 拆成 rho_partial_uamag + auc_partial_uamag
==============================================================================
改动前: git show d23e68d:analysis/A_univariate.csv
        12160 行 x 11 列  列名 = ['target', 'type', 'feature', 'rho', 'auc', 'perm_p', 'loo_r2cv', 'loo_rmse', 'loo_mae', 'rho_partial_uamag', 'q_fdr']
改动后: /Users/shiyu/Projects/adhd-segmentation/analysis/A_univariate.csv
        12160 行 x 12 列  列名 = ['target', 'type', 'feature', 'rho', 'auc', 'perm_p', 'loo_r2cv', 'loo_rmse', 'loo_mae', 'rho_partial_uamag', 'auc_partial_uamag', 'q_fdr']

  [通过] 行数相同   12160 vs 12160
  [通过] 每一行的身份(target,type,feature)逐行相同、顺序也相同
  [通过] 改动后的列 = 改动前的列 + 一列 auc_partial_uamag   新增 ['auc_partial_uamag']  消失 []
  [通过] 连续行的 auc_partial_uamag 全为空   非空 0 个
  [通过] 二分行的 rho_partial_uamag 全为空   非空 0 个
  [通过] 两半有值的格子数加起来 == 改动前那一列有值的格子数   连续 450 + 二分 450 = 900  vs 改动前 900
  [通过] 合成后的一列 == 改动前的 rho_partial_uamag 列(逐格,含 NaN 位置)   不同 0 格
  [通过] 列 'target' 逐格相同   不同 0 格
  [通过] 列 'type' 逐格相同   不同 0 格
  [通过] 列 'feature' 逐格相同   不同 0 格
  [通过] 列 'rho' 逐格相同   不同 0 格
  [通过] 列 'auc' 逐格相同   不同 0 格
  [通过] 列 'perm_p' 逐格相同   不同 0 格
  [通过] 列 'loo_r2cv' 逐格相同   不同 0 格
  [通过] 列 'loo_rmse' 逐格相同   不同 0 格
  [通过] 列 'loo_mae' 逐格相同   不同 0 格
  [通过] 列 'q_fdr' 逐格相同   不同 0 格

==============================================================================
总判定:全部通过 —— 这次改动只改了列的组织方式,一个数都没变。
==============================================================================
退出码 = 0
```

**判定:17 项全部通过,0 格不同。** 其中包含对 TASK-120 拆出的 `rho` 与 `auc` 两列的逐格比对
——确认这次改动**没有回头碰到上一次的成果**。

重跑耗时:**77.13 秒**〔第五节补的那一节又跑了一次,**63.66 秒**;连同 TASK-120 那次 59.86 秒与 TASK-106 记的 52 秒,四次都在同量级〕(TASK-120 那次 59.86 秒、TASK-106 记 52 秒,三次同量级;差值来自本机负载,
拆列不增加任何计算)。

---

## 四、顺带查实并订正的一处假引用

脚本原第 273 行(`print` 那句)写着:二分目标那半报的是「残差化后的 AUC」,**「见下方单独一节」**。

**那一节根本不存在。** 实查全脚本的 6 个小节标题:

```
连续目标:各目标 top3(按 |ρ|)...
关键:留一 R²_cv > 0 的特征-目标数...
FDR q<0.05 的组合...
负对照 uaMag_median(总运动量)对各连续目标
TASK-106:路径B 45 列 扣掉运动总量后还剩多少(连续目标)
二分目标:各目标 top3(按 |AUC-0.5|)
```

没有任何一节报这一列的二分行。**故这 450 个格子从脚本诞生起就只写进 csv、从未被打印过一次。**

该句已改成实话(说明它写在 csv 的 `auc_partial_uamag` 列、基准 0.5、stdout 里不报)。
**要不要补上那一节,去向未定** —— 三个选项与后果记在 `working/task.md` 的 TASK-121 条目。

---

## 五、缺的那一节已补上(2026-07-30 同日,用户裁决=补)

第四节记的是「那一节根本不存在」。**用户当日裁决补上**,脚本小节数由 6 增至 7。

**新小节与既有的连续目标那一节同构**,但**有一处刻意不照抄,并在输出里明写**:

| | 连续目标那一节 | 新增的二分目标那一节 |
|---|---|---|
| 效应量 | `\|ρ\|` | `\|AUC−0.5\|` |
| 量程 | **[0, 1]** | **[0, 0.5]** |
| 无效应 | ρ=0 | AUC=0.5 |

**量程差一倍,所以同一个数值门槛在二分那节严一倍。** 故该节把**两套门槛的计数都打出来**
(①与连续节同数值 0.1/0.3 ②按量程折半 0.05/0.15),**不替读者选** —— 实测两套差别很大:
同数值门槛下「强关系」**1 个**、折半门槛下 **82 个**。若只打一套,读者会以为那就是唯一答案。

**本次是纯 stdout 改动,csv 逐字节未变**:改动前后 `analysis/A_univariate.csv` 的 md5 同为
`b55e277d0753bcd3731ef26c4912cb66`,`git diff --stat` 对该文件为空。**故未重跑第三节那个验收脚本**
——它比的是列结构与数值,这次两者都没动;改用 `cmp` 逐字节比对 + `git diff` 双重确认。

### 新小节的原样 stdout

```
========== TASK-121:路径B 45 列 扣掉运动总量后还剩多少(二分目标) ==========
  判读三种情形与上一节同构,只是效应量换成 |AUC-0.5|:
             大幅【缩小】⇒ 原关系是运动总量假象;【基本不变】⇒ 真结构信号;
             【反而变大】⇒ 抑制(suppression),结构信号原先被总量盖住。
  ⚠【量程与上一节差一倍,门槛不可直接套用】:|ρ| 住在 [0,1]、|AUC-0.5| 住在 [0,0.5]。
      故下面把两套门槛的计数都打出来:①与上一节同数值(0.1/0.3) ②按量程折半(0.05/0.15)。
  注:本列同样无 p 值、无 q 值,是效应量,不进多重比较的账。

  路径B二分组合共 450 个(45 列 × 10 二分目标)
  |AUC-0.5| 中位 0.085 -> 扣掉总量后中位 0.086  (中位缩小 -0.007)
  [门槛 同上一节数值:带宽 ±0.1、强 >0.3]  强关系 1 个 -> 扣掉总量后仍强 2 个  |  缩小>0.1 的 7 个 / 基本不变(±0.1) 的 428 个 / 变大>0.1 的 15 个
  [门槛 按量程折半:带宽 ±0.05、强 >0.15]  强关系 82 个 -> 扣掉总量后仍强 94 个  |  缩小>0.05 的 38 个 / 基本不变(±0.05) 的 358 个 / 变大>0.05 的 54 个

  缩小最多的 10 个(最像总量假象):
          target         feature   auc   eff auc_partial_uamag eff_partial
 sdq_hyper__qbin     actfrac_p40 0.321 0.179             0.507       0.007
 sdq_hyper__qbin     actfrac_p30 0.336 0.164             0.471       0.029
 sdq_hyper__qbin actbout_med_p40 0.354 0.146             0.471       0.029
 sdq_hyper__qbin actbout_med_p30 0.300 0.200             0.414       0.086
 sdq_hyper__qbin    actshort_p20 0.629 0.129             0.521       0.021
 sdq_hyper__qbin actbout_med_p20 0.393 0.107             0.493       0.007
 sdq_hyper__qbin   switchmin_p90 0.257 0.243             0.357       0.143
snap_inatt__qbin     actfrac_p30 0.361 0.139             0.458       0.042
snap_inatt__qbin actbout_med_p30 0.385 0.115             0.479       0.021
 sdq_hyper__qbin   switchmin_p80 0.321 0.179             0.414       0.086

  变大最多的 10 个(抑制:结构信号原先被总量盖住):
               target       feature   auc   eff auc_partial_uamag eff_partial
     snap_hyper__qbin   actfrac_p60 0.448 0.052             0.210       0.290
snap_adhd_total__qbin   actfrac_p40 0.507 0.007             0.688       0.188
       snap_odd__qbin   actfrac_p60 0.407 0.093             0.237       0.263
       snap_odd__qbin   actfrac_p40 0.526 0.026             0.689       0.189
     snap_hyper__qbin   actfrac_p70 0.399 0.101             0.245       0.255
     snap_hyper__qbin   actfrac_p80 0.371 0.129             0.245       0.255
snap_adhd_total__qbin   actfrac_p60 0.403 0.097             0.278       0.222
       snap_odd__qbin   actfrac_p70 0.356 0.144             0.237       0.263
        sdq_emo__qbin switchmin_p10 0.569 0.069             0.688       0.188
        sdq_emo__qbin   actfrac_p70 0.556 0.056             0.674       0.174

  扣掉总量后 |AUC-0.5| 仍最大的 10 个(最像真结构信号):
           target         feature   auc   eff auc_partial_uamag eff_partial
   sdq_peer__qbin actbout_med_p60 0.843 0.343             0.861       0.361
   snap_odd__qbin     actfrac_p90 0.230 0.270             0.185       0.315
   snap_odd__qbin   switchmin_p90 0.274 0.226             0.200       0.300
sdq_totdiff__qbin   switchmin_p20 0.763 0.263             0.793       0.293
 snap_hyper__qbin     actfrac_p60 0.448 0.052             0.210       0.290
   sdq_cond__qbin  actbout_cv_p10 0.766 0.266             0.789       0.289
 snap_hyper__qbin     actfrac_p90 0.273 0.227             0.217       0.283
 snap_hyper__qbin   switchmin_p90 0.322 0.178             0.224       0.276
   snap_odd__qbin     actfrac_p80 0.333 0.167             0.230       0.270
   snap_odd__qbin     actfrac_p60 0.407 0.093             0.237       0.263

  提醒:上面 auc / auc_partial_uamag 两栏里【小于 0.5 是反向关系】,
        强弱要看紧跟其后的 eff / eff_partial 两栏(=与 0.5 的距离)。
        这正是 TASK-121 把这一列从 rho_partial_uamag 拆出来的原因。

```
