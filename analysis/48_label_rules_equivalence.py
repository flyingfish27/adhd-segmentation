# -*- coding: utf-8 -*-
"""
48_label_rules_equivalence.py — TASK-8 验收①:证明规则表驱动的标签引擎
与改造前那份"切点写死在代码里"的旧脚本【逐列逐格完全一致】。

怎么证:
  参照物 = 下面 legacy_labels() 里【原样冻结】的旧 43_target_labels.py 切分逻辑
  (2026-07-22 改造前的第 14-43 行,原封不动抄进来,包括那几个写死的数字 55 和 8)。
  被测物 = analysis/target_labels.csv,由新引擎 43_target_labels.py 读
  analysis/labels/rules.yaml 生成,代码里没有任何切点数字。
  两边都在同一份 analysis/targets.csv 上算,然后逐行逐列逐格比。

允许的列名差异只有一类:TASK-8 决定2 把 snap_total__normT55 改名成
snap_total__wang2025T55(旧名里的 "norm" 名不副实,mean/sd 取自这 24 个孩子自己,
不是任何人群常模)。本脚本按 RENAMED 映射对齐后比【取值】,取值必须完全相同。

===== TASK-110 补丁(2026-07-25):比对范围缩小,并把退出理由变成一条可跑的检查 =====
ISSUE-116 裁定删除列 snap_total(SNAP 全部 26 题之和;其中第 19-26 题测的是对立
违抗 ODD——DSM 里与 ADHD 并列的另一个独立疾病,故 snap_total 是"ADHD+ODD"混合量),
改用 snap_adhd_total(第 1-18 题)。执行见 TASK-109。这一删使本脚本第 54 行的
    v = t["snap_total"]
失去输入,原样跑会抛 KeyError、整个验收测试跑不起来。

选定的补丁形态 = 【①缩小比对范围】(task.md 的 TASK-110 列了①②两种,择一)。理由:
  (1) 比对的两端【同时】消失,不是单边失效。参照物侧:上游列 snap_total 被删,旧
      逻辑无输入;被测物侧:新引擎的对应规则 snap_total__wang2025T55 已从
      analysis/labels/rules.yaml 整条删除(TASK-109 第 5 项)。既然两端都没有这一列,
      就不存在"应当相等却不等"的风险可查,继续比对无对象。
  (2) 形态②(冻结历史基线)要把旧口径下的值固化成一份参照数据存进仓库——那等于把
      ISSUE-116 判定"不能代表 ADHD"的那个混合量,以另一种形式重新放回仓库,并且这
      份固化值一旦与 40_targets.py 的算法漂移就不会有人发现。
  (3) 用户对本任务的决策原话是「保持所有代码可复现本项目结果」。"本项目结果"指现行
      口径下的产物;形态①让本测试在现行口径下仍然可跑、仍然逐格判定引擎正确。而
      "历史结果可重建"这件事已由仓库本身保证:analysis/targets.csv 与
      analysis/target_labels.csv 都在版本控制内,旧口径的原值可用
      `git show <旧commit>:analysis/targets.csv` 原样取回,无需再存一份副本。
退出不是静默跳过:退出的列记进 RETIRED,并由下面第 [5] 项检查——要求新引擎侧也确实
没有生成它(标签表和 meta 表里都不许有)。若日后有人把那条规则加回 rules.yaml 而没
恢复上游列,这项检查会失败,不会被无声吞掉。

===== 计划外发现(2026-07-25 执行 TASK-110 时实测,先登记不处置)=====
本脚本在【本次改动之前的 HEAD=3f0fbc9 上就已经判定"不等价"、返回码 1】,与
TASK-109/110 无关。实测方法:把 HEAD 版的 targets.csv / target_labels.csv /
target_labels_meta.csv / 本脚本四个文件原样取出单独跑。原因是第 [2] 项检查要求
"参照物列名列表 == 被测物列名列表"【完全相等】,而在冻结参照(31 列)写下之后,
rules.yaml 又新增了 9 条规则、9 列标签:
  sdq_{hyper,emo,cond,peer,pro,totdiff}__cn2013band3  (TASK-9 中国常模三分组落地)
  snap_{inatt,hyper}__dsm_count7、snap_odd__dsm_count5 (Huang 2023 症状计数规则)
冻结参照里没有这 9 列,于是 [2] 报"新有旧无"。第 [3] 项(逐格比取值)始终 0 处不同。
改动前后这 9 列完全一致——本次改动没有增减这项差异。
处置(是否放宽 [2] 为"旧 ⊆ 新"、还是另立参照)属新决策,未在 TASK-109/110 范围内,
留给用户裁决;在裁决前本脚本行为保持原样,不擅自改判据。

运行(需先跑过 analysis/43_target_labels.py):
  .venv/bin/python analysis/48_label_rules_equivalence.py
返回码 0 = 等价;1 = 有差异(差异明细会打出来)。
"""
import pathlib, sys
import pandas as pd

ROOT = pathlib.Path("/Users/shiyu/Projects/adhd-segmentation")

# TASK-8 决定2 的改名:旧列名 -> 新列名。除此之外不允许有任何列名差异。
# TASK-110 附注:这张表目前不会命中——它唯一的条目 snap_total__normT55 已随
# ISSUE-116 删列而退出比对(见 RETIRED)。保留此表是为留住 TASK-8 那次改名的记录,
# 且将来再有改名时仍走这条通路。
RENAMED = {"snap_total__normT55": "snap_total__wang2025T55"}


def legacy_labels(t):
    """===== 以下为改造前 43_target_labels.py 的切分逻辑,原样冻结,勿改 =====
    (原第 14-43 行。保留其写死的 55 和 8,正因为要拿它当参照物。)"""
    out = pd.DataFrame(index=t.index)
    log = []
    retired = []          # TASK-110 新增:因上游列被删而退出比对的参照列

    def qcut_label(v, k, name):
        try:
            lab = pd.qcut(v, k, labels=False, duplicates="drop")
        except Exception as e:
            log.append((name, f"q{k}", "FAILED", str(e))); return None
        ng = lab.nunique()
        sizes = lab.value_counts().sort_index().to_dict()
        note = "" if ng == k else f"并列导致实际只有 {ng} 组(目标k={k})"
        log.append((name, f"q{k}", sizes, note))
        return lab

    for c in t.columns:
        v = t[c]
        for k, tag in [(2, "bin"), (3, "ter"), (4, "quar")]:
            lab = qcut_label(v, k, f"{c}__q{tag}")
            if lab is not None:
                out[f"{c}__q{tag}"] = lab

    # TASK-110:下面 if 体内的两行是旧脚本原文,一字未改;新增的只有这层 if/else
    # 守卫本身。上游列 snap_total 已由 ISSUE-116/TASK-109 删除,守卫命中 else 分支。
    if "snap_total" in t.columns:
        v = t["snap_total"]; z = (v - v.mean()) / v.std(ddof=1); T = z * 10 + 50
        out["snap_total__normT55"] = (T >= 55).astype(int)
    else:
        retired.append(("snap_total__normT55",
                        "上游列 snap_total 已由 ISSUE-116 裁定删除(执行:TASK-109);"
                        "新引擎侧对应规则 snap_total__wang2025T55 亦已从 rules.yaml 整条删除"))

    # 旧脚本对 SDQ 多动常模 >=8 只记日志、不生成列(0/24 退化)
    deg = int((t["sdq_hyper"] >= 8).sum())
    log.append(("sdq_hyper__norm8", "norm(>=8)", {"阳性": deg, "阴性": len(t) - deg},
                "退化:0/24 达到异常线 → 不生成此列"))
    return out, log, retired
    # ===== 冻结区结束 =====


t = pd.read_csv(ROOT / "analysis/targets.csv").set_index("subject")
old, old_log, RETIRED = legacy_labels(t)
new = pd.read_csv(ROOT / "analysis/target_labels.csv").set_index("subject")
meta = pd.read_csv(ROOT / "analysis/target_labels_meta.csv")

print("=" * 78)
print("TASK-8 验收① 等价性核验:旧硬编码切分  vs  规则表驱动引擎")
print("=" * 78)
print(f"输入          analysis/targets.csv          {t.shape[0]} 行 × {t.shape[1]} 列")
print(f"参照(旧逻辑)  legacy_labels() 冻结副本      {old.shape[0]} 行 × {old.shape[1]} 列")
print(f"被测(新引擎)  analysis/target_labels.csv    {new.shape[0]} 行 × {new.shape[1]} 列")
print(f"规则表        analysis/labels/rules.yaml    {len(meta)} 条规则 "
      f"(写进标签表 {int(meta['written'].sum())} 条,不写入 {int((~meta['written']).sum())} 条)")

fail = []

# ---- 1. 行(受试者)对齐 ----
if list(old.index) != list(new.index):
    fail.append(f"行不一致:旧 {list(old.index)} vs 新 {list(new.index)}")
print(f"\n[1] 24 名受试者顺序一致:{'通过' if not fail else '不通过'}")

# ---- 2. 列名对齐(允许 RENAMED 里的改名)----
old_mapped = [RENAMED.get(c, c) for c in old.columns]
if old_mapped != list(new.columns):
    only_old = [c for c in old_mapped if c not in new.columns]
    only_new = [c for c in new.columns if c not in old_mapped]
    fail.append(f"列名不一致:旧有新无 {only_old};新有旧无 {only_new};"
                f"或顺序不同 旧{old_mapped} 新{list(new.columns)}")
    print(f"[2] 列名与顺序一致(改名后):不通过")
else:
    print(f"[2] 列名与顺序一致(改名后):通过 —— {len(new.columns)} 列全部对上")
    applied = [(o, n) for o, n in RENAMED.items() if o in old.columns]
    for o, n in applied:
        print(f"      改名 {o}  ->  {n}   (TASK-8 决定2)")
    if not applied:
        print("      本次无改名生效(RENAMED 表里的列已全部退出比对,见 [5])")

# ---- 3. 逐格比取值 ----
print(f"\n[3] 逐列逐格比对(24 行 × {len(old.columns)} 列 = {24 * len(old.columns)} 格):")
print(f"    {'列名(新)':30} {'不同格数':>8}  各组人数(旧 == 新)")
total_diff = 0
for oc in old.columns:
    nc = RENAMED.get(oc, oc)
    if nc not in new.columns:
        continue
    a, b = old[oc], new[nc]
    ndiff = int((a.values != b.values).sum())
    total_diff += ndiff
    if ndiff:
        fail.append(f"{nc}: {ndiff} 格不同")
    sa = a.value_counts().sort_index().to_dict()
    sb = b.value_counts().sort_index().to_dict()
    mark = "OK " if ndiff == 0 and sa == sb else "差异"
    print(f"    {mark} {nc:30} {ndiff:>8}  {sa} {'==' if sa == sb else '!='} {sb}")
print(f"    合计不同格数:{total_diff}")

# ---- 4. 旧脚本未生成的列,新引擎也没生成 ----
print(f"\n[4] 旧脚本【记了日志但没生成】的列,新引擎是否也没生成:")
for name, scheme, sizes, note in old_log:
    if "不生成" in note:
        in_new_csv = name in new.columns
        in_new_meta = name in set(meta["label_name"])
        row = meta[meta["label_name"] == name]
        ok = (not in_new_csv) and in_new_meta
        if not ok:
            fail.append(f"{name}: 旧脚本不生成,新引擎 在标签表={in_new_csv} 在meta={in_new_meta}")
        print(f"    {'OK ' if ok else '差异'} {name:26} 旧:{note}")
        print(f"         新:在 target_labels.csv 中={in_new_csv}(应为 False);"
              f"在 target_labels_meta.csv 中={in_new_meta}(应为 True)")
        if len(row):
            r = row.iloc[0]
            print(f"         新 meta 记录:on_degenerate={r['on_degenerate']} "
                  f"degenerate={r['degenerate']} constant={r['constant']} "
                  f"group_sizes={r['group_sizes']} written={r['written']}")

# ---- 5. 退出比对的参照列:要求新引擎侧也确实没有生成(TASK-110)----
print(f"\n[5] 因上游列被删而退出比对的参照列(TASK-110 补丁形态①):")
if not RETIRED:
    print("    无 —— 冻结区里的参照列全部有输入,比对范围完整。")
for name, why in RETIRED:
    mapped = RENAMED.get(name, name)                 # 新引擎侧本应叫的名字
    hits = sorted({name, mapped} & (set(new.columns) | set(meta["label_name"])))
    ok = not hits
    if not ok:
        fail.append(f"{name}: 参照物侧已因上游列被删而退出,新引擎侧却仍产出 {hits}"
                    f"(两端不对称:要么把上游列加回 40_targets.py,要么把规则从 rules.yaml 删掉)")
    print(f"    {'OK ' if ok else '差异'} {name:26} 退出原因:{why}")
    print(f"         新引擎侧同名/改名后列({name} / {mapped})在 target_labels.csv 或 "
          f"target_labels_meta.csv 中出现:{hits if hits else '否(应为否)'}")

# ---- 结论 ----
print("\n" + "=" * 78)
if fail:
    print(f"结论:不等价,共 {len(fail)} 处差异")
    for f in fail:
        print("  - " + f)
    sys.exit(1)
_renamed_n = len([o for o in RENAMED if o in old.columns])
print("结论:等价。规则表驱动的引擎逐列逐格复现了旧硬编码脚本的全部 "
      f"{len(old.columns)} 列标签(其中 {_renamed_n} 列按 TASK-8 决定2 改名,取值不变),")
print("      且旧脚本因退化而不生成的 sdq_hyper__norm8 在新引擎里同样不写进标签表、")
print("      但在 target_labels_meta.csv 里留下了记录。")
if RETIRED:
    print(f"      比对范围已按 TASK-110 形态① 缩小:{len(RETIRED)} 列退出"
          f"({', '.join(n for n, _ in RETIRED)}),其上游列由 ISSUE-116 裁定删除;")
    print("      本脚本已逐列确认新引擎侧同样没有产出这些列,故两端对称、无未查的差异。")
print("=" * 78)
sys.exit(0)
