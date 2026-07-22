# -*- coding: utf-8 -*-
"""
43_target_labels.py — 分组标签【引擎】(TASK-8)

作用:把连续症状分切成分组标签,喂给分类模型。
和 TASK-8 之前的版本的区别:切点、组数、阈值不再写在代码里,全部读规则表。
本文件里【没有任何切点数字】——要改切法,改 analysis/labels/rules.yaml,不动代码。

读:
  analysis/targets.csv        24 人 × 10 个连续症状分(由 40_targets.py 产出)
  analysis/items.csv          24 人 × 每道题的标准计分(由 40_targets.py 产出);
                              只有 method: symptom_count 的规则才用它,缺表时
                              其它规则照跑,用到它的规则会报错说清楚缺什么。
  analysis/labels/rules.yaml  规则表:一条 = 一个输出标签列
  analysis/labels/norms.csv   常模分档数值表(method: norm_band 查它)
  analysis/labels/sources.csv 出处表:文献、样本量、年龄段、评分人

写:
  analysis/target_labels.csv       24 人 × 各标签列,存整数组码 0..k-1
  analysis/target_labels_meta.csv  每个标签规则一行:method、params、各组人数、
                                   是否退化、是否常数列、出处 id 与文献全称。
                                   作用是让"这列怎么切的、依据是谁"跟着数据走,
                                   读表的人不必回来看代码。

退化列(声明切 k 组、结果某组 0 人)由规则自己的 on_degenerate 决定:
  keep = 照写进 target_labels.csv 并在 meta 标 degenerate=true
  skip = 不写这一列,但 meta 里仍留一行记下它退化了
两种情况下这条信息都落在文件里,不只活在终端输出。
下游 44/45 按 meta 的 degenerate 字段主动过滤,避免常数列进模型(重演 ISSUE-101)。

运行:  .venv/bin/python analysis/43_target_labels.py
"""
import copy, json, pathlib, sys
import numpy as np, pandas as pd, yaml

# ROOT = 数据根目录(targets.csv / items.csv / 输出都在这儿,均不入版本控制)。
# LABELS_DIR = 规则/常模/出处三张表,它们是【随脚本走的版本化配置】而不是数据产物,
# 所以按本脚本自身所在位置找,不按 ROOT 找——这样在任何 checkout 里跑,用的都是
# 那份 checkout 自己的规则表。(同样用 __file__ 定位的先例:30_paper1_table2_verify.py)
ROOT = pathlib.Path("/Users/shiyu/Projects/adhd-segmentation")
LABELS_DIR = pathlib.Path(__file__).resolve().parent / "labels"

# ---------------------------------------------------------------- 读输入
targets = pd.read_csv(ROOT / "analysis/targets.csv").set_index("subject")

items_path = ROOT / "analysis/items.csv"
items = pd.read_csv(items_path).set_index("subject") if items_path.exists() else None

with open(LABELS_DIR / "rules.yaml", encoding="utf-8") as f:
    rules_doc = yaml.safe_load(f)
RULES = rules_doc["rules"]

norms = pd.read_csv(LABELS_DIR / "norms.csv")
sources = pd.read_csv(LABELS_DIR / "sources.csv")
SOURCE_CITATION = dict(zip(sources["source_id"], sources["citation"]))


class RuleError(Exception):
    """规则表写错了。故意抛出中断,不静默跳过——静默跳过会让标签表少列而没人发现。"""


def need(params, key, label_name, method):
    if key not in params:
        raise RuleError(f"[{label_name}] method: {method} 缺少参数 params.{key}")
    return params[key]


def get_target(rule):
    """取这条规则要切的连续分列。"""
    name = rule.get("target")
    if name is None:
        raise RuleError(f"[{rule['label_name']}] method: {rule['method']} 需要 target,但写的是 null")
    if name not in targets.columns:
        raise RuleError(
            f"[{rule['label_name']}] target: {name} 不是 analysis/targets.csv 的列。"
            f"现有列:{list(targets.columns)}"
        )
    return targets[name]


# ================================================================
# method 词表 —— 每个 method 一个小函数。加新切法只需在这里加一个函数 +
# 注册到 METHODS,已有规则不受影响。函数返回 (组码 Series, 声明的组数 k)。
# 所有数字都从 params / norms.csv 里来,函数体内不出现切点常量。
# ================================================================

def m_quantile(rule, params):
    """样本内分位切。并列过多时按 duplicates 策略处理,实际组数可能少于 k。"""
    v = get_target(rule)
    k = need(params, "k", rule["label_name"], "quantile")
    dup = need(params, "duplicates", rule["label_name"], "quantile")
    return pd.qcut(v, k, labels=False, duplicates=dup), k


def m_zscore_cut(rule, params):
    """样本内 z 分换到 T 刻度后按 t_cut 二分。mean/sd 取自本样本,不是人群常模。"""
    v = get_target(rule)
    ln, mth = rule["label_name"], "zscore_cut"
    ddof = need(params, "ddof", ln, mth)
    z = (v - v.mean()) / v.std(ddof=ddof)
    t = z * need(params, "t_sd", ln, mth) + need(params, "t_mean", ln, mth)
    return (t >= need(params, "t_cut", ln, mth)).astype("int64"), 2


def m_raw_cut(rule, params):
    """绝对切点。cuts 升序;某人的组码 = 有几个切点 <= 他的取值。"""
    v = get_target(rule)
    cuts = list(need(params, "cuts", rule["label_name"], "raw_cut"))
    if cuts != sorted(cuts):
        raise RuleError(f"[{rule['label_name']}] params.cuts 必须升序,现在是 {cuts}")
    lab = pd.Series(0, index=v.index, dtype="int64")
    for c in cuts:
        lab = lab + (v >= c).astype("int64")
    return lab, len(cuts) + 1


def m_norm_band(rule, params):
    """查 norms.csv 取分档。每档一行,lower/upper 均为闭区间;落不进任何档记 NaN。"""
    v = get_target(rule)
    norm_id = need(params, "norm_id", rule["label_name"], "norm_band")
    band = norms[norms["norm_id"] == norm_id].sort_values("band_index")
    if band.empty:
        raise RuleError(
            f"[{rule['label_name']}] norms.csv 里没有 norm_id={norm_id} 的行。"
            f"现有 norm_id:{sorted(norms['norm_id'].dropna().unique().tolist())}"
        )
    lab = pd.Series(np.nan, index=v.index, dtype="float64")
    for _, r in band.iterrows():
        lab = lab.mask((v >= r["lower"]) & (v <= r["upper"]), r["band_index"])
    return lab, len(band)


def m_symptom_count(rule, params):
    """题目级症状计数:某题 >= item_min 记一个症状,症状数 >= n_min 判 1。"""
    ln, mth = rule["label_name"], "symptom_count"
    cols = list(need(params, "items", ln, mth))
    if items is None:
        raise RuleError(
            f"[{ln}] method: symptom_count 需要 analysis/items.csv,但该文件不存在。"
            f"先跑 analysis/40_targets.py 生成它。"
        )
    missing = [c for c in cols if c not in items.columns]
    if missing:
        raise RuleError(f"[{ln}] params.items 里这些列不在 analysis/items.csv 中:{missing}")
    cnt = (items[cols] >= need(params, "item_min", ln, mth)).sum(axis=1)
    lab = (cnt >= need(params, "n_min", ln, mth)).astype("int64")
    return lab.reindex(targets.index), 2


METHODS = {
    "quantile": m_quantile,
    "zscore_cut": m_zscore_cut,
    "norm_band": m_norm_band,
    "raw_cut": m_raw_cut,
    "symptom_count": m_symptom_count,
}

# ================================================================
# 跑规则表
# ================================================================
out = pd.DataFrame(index=targets.index)
meta_rows = []
seen = set()

for rule in RULES:
    for field in ("label_name", "method", "params", "group_names", "source_id", "on_degenerate"):
        if field not in rule:
            raise RuleError(f"规则缺字段 {field}:{rule}")
    name = rule["label_name"]
    if name in seen:
        raise RuleError(f"label_name 重复:{name}")
    seen.add(name)

    method = rule["method"]
    if method not in METHODS:
        raise RuleError(f"[{name}] 未知 method: {method}。已实现:{sorted(METHODS)}")
    on_deg = rule["on_degenerate"]
    if on_deg not in ("keep", "skip"):
        raise RuleError(f"[{name}] on_degenerate 只能是 keep 或 skip,现在是 {on_deg!r}")
    if rule["source_id"] not in SOURCE_CITATION:
        raise RuleError(
            f"[{name}] source_id={rule['source_id']} 不在 analysis/labels/sources.csv 里"
        )

    params = copy.deepcopy(rule["params"])   # YAML 锚点可能共享同一个对象,复制防改坏
    lab, k_declared = METHODS[method](rule, params)

    # 声明的 0..k-1 每组各几人(0 人的组也要出现,否则看不出退化)
    counts = lab.dropna().astype("int64").value_counts().to_dict()
    group_sizes = {g: int(counts.get(g, 0)) for g in range(int(k_declared))}
    n_unassigned = int(lab.isna().sum())      # norm_band 落不进任何档的人
    empty_groups = [g for g, s in group_sizes.items() if s == 0]
    degenerate = len(empty_groups) > 0
    constant = lab.dropna().nunique() < 2     # 常数列:进模型会重演 ISSUE-101
    written = not (degenerate and on_deg == "skip")

    if written:
        col = lab.astype("int64") if lab.notna().all() else lab
        out[name] = col

    meta_rows.append({
        "label_name": name,
        "target": rule.get("target"),
        "method": method,
        "params": json.dumps(params, ensure_ascii=False, sort_keys=True),
        "group_names": json.dumps(rule["group_names"], ensure_ascii=False),
        "k_declared": int(k_declared),
        "k_observed": int(lab.dropna().nunique()),
        "group_sizes": json.dumps(group_sizes, ensure_ascii=False),
        "n_unassigned": n_unassigned,
        "degenerate": degenerate,
        "empty_groups": json.dumps(empty_groups),
        "constant": constant,
        "on_degenerate": on_deg,
        "written": written,
        "source_id": rule["source_id"],
        "source_citation": SOURCE_CITATION[rule["source_id"]],
        "note": rule.get("note", ""),
    })

meta = pd.DataFrame(meta_rows)
out.to_csv(ROOT / "analysis/target_labels.csv")
meta.to_csv(ROOT / "analysis/target_labels_meta.csv", index=False)

# ================================================================
# 汇报
# ================================================================
print(f"规则表 analysis/labels/rules.yaml:{len(RULES)} 条规则")
print(f"标签表 -> analysis/target_labels.csv       形状:{out.shape}")
print(f"元数据 -> analysis/target_labels_meta.csv  形状:{meta.shape}")

print("\n每条规则(method / 声明k→实际组数 / 各组人数 / 是否退化 / 是否写进标签表):")
for r in meta_rows:
    flag = []
    if r["degenerate"]:
        flag.append(f"退化(空组{r['empty_groups']})")
    if r["constant"]:
        flag.append("常数列")
    if r["n_unassigned"]:
        flag.append(f"{r['n_unassigned']}人未落档")
    print(
        f"  {r['label_name']:26} {r['method']:14} "
        f"k={r['k_declared']}→{r['k_observed']} {r['group_sizes']:32} "
        f"{'写入' if r['written'] else '不写入'}  {' '.join(flag)}"
    )

deg = meta[meta["degenerate"]]
print(f"\n退化规则 {len(deg)}/{len(meta)} 条(声明的 k 组里有组 0 人):")
for _, r in deg.iterrows():
    print(f"  {r['label_name']:26} 空组{r['empty_groups']} 写入={r['written']} 常数列={r['constant']}")
print("  这些列在 meta 里 degenerate=true;44/45 按该字段过滤,不让它们进模型。")

print(f"\n出处分布(source_id → 规则数):{meta['source_id'].value_counts().to_dict()}")
print(f"生成的分组标签列数:{out.shape[1]}")
print("连续回归目标仍用 analysis/targets.csv 原列(%d 个)。" % targets.shape[1])
