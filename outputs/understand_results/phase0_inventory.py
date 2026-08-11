#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段 0:读取文件、建立数据字典。

【本阶段做什么】只清点与描述。用户规格明确:"阶段 0 不解释哪些 feature 表现好。"
故本脚本不排序、不筛选、不评价任何特征或目标。

【本阶段产出】
  stdout / logs/phase0.log                     逐字一致的运行日志
  out/phase0/phase0__file_overview.csv         每个文件的行列数与状态
  out/phase0/phase0__schema_<file>.csv         每个文件的列名 / dtype / 缺失计数
  out/phase0/phase0__head5_<file>.csv          每个文件前 5 行(完整列,不截断)
  out/phase0/phase0__type_counts.csv           type 唯一值与行数
  out/phase0/phase0__target_counts.csv         target 唯一值与行数(含 type)
  out/phase0/phase0__capability_matrix.csv     哪些文件支持哪类分析
  out/phase0/phase0__data_dictionary.csv       数据字典

运行:  .venv/bin/python outputs/understand_results/phase0_inventory.py
"""
import subprocess

import numpy as np
import pandas as pd

import config as C

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 60)
pd.set_option("display.max_colwidth", 60)

C.ensure_dirs()
np.random.seed(C.SEED)          # 阶段 0 无随机成分,仅为流程一致性而设


def git_provenance(path):
    """返回 (最后一次改动该文件的 commit, 工作区是否有未提交改动)。"""
    try:
        last = subprocess.run(["git", "log", "-1", "--format=%h %ad", "--date=short", "--", str(path)],
                              cwd=C.ROOT, capture_output=True, text=True, timeout=20).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", str(path)],
                               cwd=C.ROOT, capture_output=True, text=True, timeout=20).stdout.strip()
        if not last:
            return "(未入版本控制)", bool(dirty)
        return last, bool(dirty)
    except Exception as e:                                  # noqa: BLE001
        return f"(git 查询失败: {e})", False


with C.Tee(C.LOG_DIR / "phase0.log"):

    # =========================================================================
    C.rule("PHASE 0 · STEP 0 — 运行环境与观测基线")
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=C.ROOT,
                          capture_output=True, text=True).stdout.strip()
    main = subprocess.run(["git", "rev-parse", "--short", "main"], cwd=C.ROOT,
                          capture_output=True, text=True).stdout.strip()
    branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=C.ROOT,
                            capture_output=True, text=True).stdout.strip()
    print(f"repo root      : {C.ROOT}")
    print(f"branch         : {branch}")
    print(f"HEAD           : {head}")
    print(f"main           : {main}")
    print(f"pandas / numpy : {pd.__version__} / {np.__version__}")
    print(f"seed (unused in phase 0): {C.SEED}")

    # =========================================================================
    C.rule("PHASE 0 · STEP 1 — 文件清点(存在性 + 出处)")
    CANDIDATES = [
        ("A_univariate.csv", C.PATH_A_UNIVARIATE, "table", "A 轨结果表(用户上一轮明确指定)"),
        ("features.csv",     C.PATH_FEATURES,     "table", "feature matrix(仓库内找到,待用户确认是否纳入)"),
        ("targets.csv",      C.PATH_TARGETS,      "table", "连续 target 表(仓库内找到,待用户确认是否纳入)"),
        ("FEATURE_MENU.md",  C.PATH_FEATURE_MENU, "doc",   "feature 说明文档(仓库内找到,待用户确认)"),
        ("44_univariate_screen.py", C.PATH_SCREEN_CODE, "code", "产出 A 轨结果表的脚本"),
        ("42_features_full.py",     C.PATH_FEAT_CODE,   "code", "产出 feature matrix 的脚本"),
    ]
    ov = []
    for name, path, kind, note in CANDIDATES:
        exists = path.exists()
        commit, dirty = git_provenance(path) if exists else ("", False)
        ov.append(dict(file=name, kind=kind, exists=exists,
                       bytes=path.stat().st_size if exists else np.nan,
                       last_commit=commit,
                       uncommitted_changes=dirty,
                       note=note))
    ov = pd.DataFrame(ov)
    print(ov.to_string(index=False))
    print("\n>> 保存:", C.save_table(ov, "file_overview", "phase0"))

    # 缺失文件类:逐 participant 的 LOOCV prediction / residual
    print("\n[缺失文件的显式声明]")
    print("  用户规格第二节第 6 项列出的『LOOCV 逐个 participant prediction 或 residual 文件』:")
    print("  仓库内【不存在】。已用 find 在 .venv 之外全仓库搜 *resid* / *oof* / *pred* / *loo*,无命中。")
    print("  代码层佐证:44_univariate_screen.py 的 loo_simple_lr() 只 return (r2, rmse, mae) 三个标量,")
    print("  留一残差向量 loo 是函数内的局部变量,从未落盘。")

    # =========================================================================
    C.rule("PHASE 0 · STEP 2 — 每个表的行列数 / 列名 / dtype / 前5行 / 缺失计数")

    def profile_table(name, path, show_cols=None):
        df = pd.read_csv(path)
        print(f"\n---------- {name} ----------")
        print(f"path   : {path.relative_to(C.ROOT)}")
        print(f"shape  : {df.shape[0]} rows x {df.shape[1]} cols")

        schema = pd.DataFrame({
            "column": df.columns,
            "dtype": [str(t) for t in df.dtypes],
            "n_missing": df.isna().sum().values,
            "pct_missing": (df.isna().mean().values * 100).round(2),
            "n_unique": [df[c].nunique(dropna=True) for c in df.columns],
        })
        if df.shape[1] <= 30:
            print("\n[schema · 全部列]")
            print(schema.to_string(index=False))
        else:
            print(f"\n[schema · 共 {df.shape[1]} 列,屏幕上只显示前 8 与后 4 列;完整表已存 CSV]")
            print(pd.concat([schema.head(8), schema.tail(4)]).to_string(index=False))
            print("\n[dtype 汇总]")
            print(schema["dtype"].value_counts().to_string())
            print("\n[缺失汇总]  含缺失的列数:",
                  int((schema.n_missing > 0).sum()), " / 总列数:", df.shape[1])

        print("\n[前 5 行]" + ("" if df.shape[1] <= 14 else
              f"(共 {df.shape[1]} 列,屏幕上只显示指定的少数列;完整前 5 行已存 CSV)"))
        disp = df.head(5) if df.shape[1] <= 14 else df.head(5)[show_cols]
        print(disp.to_string(index=False))

        p1 = C.save_table(schema, f"schema_{name.replace('.csv', '')}", "phase0")
        p2 = C.save_table(df.head(5), f"head5_{name.replace('.csv', '')}", "phase0")
        print(f"\n>> 保存: {p1}")
        print(f">> 保存: {p2}")
        return df

    A = profile_table("A_univariate.csv", C.PATH_A_UNIVARIATE)
    Xf = profile_table("features.csv", C.PATH_FEATURES,
                       show_cols=["subject"] + list(pd.read_csv(C.PATH_FEATURES, nrows=1)
                                                    .columns[1:5]))
    Yt = profile_table("targets.csv", C.PATH_TARGETS)

    # =========================================================================
    C.rule("PHASE 0 · STEP 3 — A_univariate.csv 的 type:唯一值与行数")
    tc = (A.groupby("type", dropna=False)
            .agg(n_rows=("type", "size"),
                 n_targets=("target", "nunique"),
                 n_features=("feature", "nunique"))
            .reset_index())
    print(tc.to_string(index=False))
    print("\n【注意】用户规格要求:若 type 的实际标签不是 'regression' 或 'continuous',")
    print("       须展示唯一值并由用户确认筛选规则,不得自行猜测。实际唯一值如上。")
    print("       本脚本【没有】使用任何 type 筛选,config.CONT_TYPE_LABEL 目前为", C.CONT_TYPE_LABEL)
    print("\n>> 保存:", C.save_table(tc, "type_counts", "phase0"))

    # =========================================================================
    C.rule("PHASE 0 · STEP 4 — A_univariate.csv 的 target:唯一值与行数")
    gc = (A.groupby(["target", "type"], dropna=False)
            .agg(n_rows=("feature", "size"), n_unique_features=("feature", "nunique"))
            .reset_index()
            .sort_values(["type", "target"]))
    # 每个 target 各字段的非空计数,用来看哪些指标只在某类 target 上有值
    nn = (A.groupby(["target", "type"])[["rho", "perm_p", "loo_r2cv", "loo_rmse",
                                         "loo_mae", "rho_partial_uamag", "q_fdr"]]
            .apply(lambda g: g.notna().sum()).reset_index())
    gc = gc.merge(nn, on=["target", "type"], how="left")
    print(gc.to_string(index=False))
    print(f"\ntarget 唯一值个数: {A['target'].nunique()}")
    print("\n>> 保存:", C.save_table(gc, "target_counts", "phase0"))

    # =========================================================================
    C.rule("PHASE 0 · STEP 5 — feature 计数")
    print(f"A_univariate.csv 的 feature 列:总行数 {len(A)},唯一 feature 数 {A['feature'].nunique()}")
    per_t = A.groupby("target")["feature"].nunique()
    print(f"每个 target 的唯一 feature 数: min={per_t.min()}  max={per_t.max()}")
    print(f"所有 target 是否共用同一 feature 集合(阶段 1 会正式校验,此处仅计数): "
          f"{'计数一致' if per_t.nunique() == 1 else '计数不一致'}")
    fx = [c for c in Xf.columns if c != "subject"]
    print(f"\nfeatures.csv 的特征列数(去掉 subject): {len(fx)}")
    inter = set(fx) & set(A['feature'].unique())
    print(f"features.csv 特征名 与 A 表 feature 名的交集大小: {len(inter)}")
    print(f"  只在 features.csv 里出现: {sorted(set(fx) - set(A['feature'].unique()))}")
    print(f"  只在 A 表里出现          : {sorted(set(A['feature'].unique()) - set(fx))}")
    print(f"\ntargets.csv 的目标列数(去掉 subject): {len([c for c in Yt.columns if c != 'subject'])}")
    print(f"targets.csv 列名: {[c for c in Yt.columns if c != 'subject']}")

    # =========================================================================
    C.rule("PHASE 0 · STEP 6 — 哪些文件能支持哪类分析")
    cap = [
        dict(analysis="结果表分析 (association / perm / FDR / LOOCV 指标的分布与排名)",
             required="A_univariate.csv",
             status="可做", detail="12160 行结果表齐备"),
        dict(analysis="target distribution (24 人的分数分布 / ties / skewness)",
             required="targets.csv",
             status="可做(待你确认纳入)", detail="仓库内存在,24 行 x 10 个连续目标"),
        dict(analysis="feature-family analysis",
             required="FEATURE_MENU.md 或 feature-family mapping",
             status="待确认", detail="FEATURE_MENU.md 是散文式文档,不是机器可读 mapping;"
                                     "映射规则须先给你审后才能用"),
        dict(analysis="residual-level analysis (逐 participant 的 LOO 残差 / 预测)",
             required="逐 participant prediction 或 residual 文件",
             status="不可做", detail="仓库内不存在该文件;44 号脚本未落盘残差向量"),
        dict(analysis="feature 与 target 的原始散点 / 重算 LOO 残差",
             required="features.csv + targets.csv",
             status="可做(需你授权重算)", detail="两表齐备,可闭式重算单变量 LOO 残差;"
                                                "但这属于【重新计算】,不是读取已有结果"),
    ]
    cap = pd.DataFrame(cap)
    print(cap.to_string(index=False))
    print("\n>> 保存:", C.save_table(cap, "capability_matrix", "phase0"))

    # =========================================================================
    C.rule("PHASE 0 · STEP 7 — 数据字典(仅本次使用的字段)")
    DICT = [
        ("target", "本行结果对应的症状量表分数(结果表的分组键之一)", "标识列",
         "字符串", "10 个连续目标 + 10 个 __qbin 二分目标",
         "连续与二分是不同的 target 名,故互不混行"),
        ("type", "本行属于连续目标还是二分目标", "标识列",
         "字符串", "见 STEP 3 的唯一值",
         "决定哪些指标列有值:cont 行有 rho/loo_*,bin 行有 auc"),
        ("feature", "本行结果对应的腕部信号特征(结果表的分组键之一)", "标识列",
         "字符串", "608 个", "与 features.csv 的列名一一对应"),
        ("rho", "特征与目标的 Spearman 秩相关系数 = association effect size",
         "效应量", "[-1, 1]",
         "spearman(rank(x), rank(y)),44 号脚本 spearman() 函数",
         "秩相关,只刻画【单调】关系;不是线性拟合优度,也不含任何预测含义"),
        ("perm_p", "置换检验 p 值:把目标分数随机打乱 100000 次后,|rho| 达到或超过实测值的比例",
         "统计检验结果", "[1e-5, 1]",
         "NPERM=100000,零分布收集 |spearman|;pval 下限被 clip 到 1/NPERM",
         "【与 rho 不是两项独立证据】:它就是同一个 rho 在零分布里的极端程度。"
         "下限 1e-5 意味着更小的真实 p 无法分辨"),
        ("q_fdr", "对 perm_p 做 Benjamini-Hochberg 多重比较校正后的 FDR q 值",
         "统计检验结果", "[0, 1]",
         "44 号脚本 bh() 函数,按 R.groupby('target') 分族计算",
         "族的定义 = 每个 target 各自一族(m=该 target 的行数)。"
         "同样【不是】独立于 perm_p 的第三项证据,是 perm_p 的单调变换"),
        ("loo_r2cv", "留一交叉验证的 R²_cv = 1 - PRESS_model / PRESS_baseline",
         "模型表现", "(-inf, 1]",
         "loo_simple_lr();baseline = 留一均值预测",
         "【可为负】,负值代表该单特征线性模型的留一误差比『只用均值』还大。"
         "这是内部重抽样,【不是】独立 test set;> 0 【不等于】统计显著"),
        ("loo_rmse", "留一预测的均方根误差 = sqrt(PRESS/n)", "模型表现", "[0, +inf)",
         "loo_simple_lr(),n=24", "单位 = 该量表分数的单位,故【不可跨 target 直接比较】"),
        ("loo_mae", "留一预测的平均绝对误差 = mean(|loo residual|)", "模型表现", "[0, +inf)",
         "loo_simple_lr(),n=24", "同上,不可跨 target 直接比较"),
        ("rho_partial_uamag",
         "扣掉『运动总量』(uaMag_median)之后,特征与目标还剩多少秩相关 = 效应量的敏感性分析",
         "效应量(敏感性分析)", "[-1, 1]",
         "对特征秩与目标秩各自对 rank(uaMag_median) 回归取残差,再求两残差的相关",
         "【只对路径B的 45 列计算】,其余列为空 —— 空值代表 not applicable,不代表失败。"
         "此列【没有】配套的 p、q 或 LOOCV,故不能据此说『控制后显著』"),
    ]
    dd = pd.DataFrame(DICT, columns=["column", "统计含义", "证据层级", "取值范围",
                                     "由哪段代码产生", "读它时必须知道的口径"])
    for _, r in dd.iterrows():
        print(f"\n  [{r['column']}]  证据层级: {r['证据层级']}   取值范围: {r['取值范围']}")
        print(f"      含义   : {r['统计含义']}")
        print(f"      产生自 : {r['由哪段代码产生']}")
        print(f"      口径   : {r['读它时必须知道的口径']}")
    print("\n[本次排除的字段]")
    print(f"  {C.COLS_EXCLUDED}  —— 用户规格第三节明确排除;")
    print("  另:所有 type=bin 的行本次不分析。")
    print("\n>> 保存:", C.save_table(dd, "data_dictionary", "phase0"))

    C.rule("PHASE 0 完成 —— 本阶段不对任何 feature 的表现作评价", "=")
