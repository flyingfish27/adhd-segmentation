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
import os, pathlib, sys
import pandas as pd

# ROOT 定位(2026-07-26 改,原为写死的主检出绝对路径):按本脚本位置推算仓库根,
#   使本测试在任何 checkout/worktree 里都比对【它自己那份】产物;
#   环境变量 ADHD_ROOT 可覆盖。
HERE = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path(os.environ.get("ADHD_ROOT", HERE.parent)).resolve()

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

# ---- 2. 列名对齐:判据 =「旧 ⊆ 新」,不是「完全相等」----
# 为什么不是完全相等(2026-07-26 改,用户裁决):本项检查的职责是"旧引擎的每一列都还在、
#   且相对顺序没乱",而不是"新引擎不许多做事"。规则表驱动的引擎【被设计成可以加规则】——
#   TASK-9 就合法地加了 9 条(6 个中国常模三分组 + 3 个 Huang 2023 症状计数)。旧判据要求
#   完全相等,于是每次合法新增都误报"不等价",本脚本因此长期返回 1、退化成一盏永久红灯
#   (警报疲劳 alarm fatigue:永远是红的测试比没有测试更糟,真出回归时没人会看)。
#   新增列的回归保护由下面第 [6] 项(golden 基线)负责,不在本项。
old_mapped = [RENAMED.get(c, c) for c in old.columns]
missing  = [c for c in old_mapped if c not in list(new.columns)]
extra    = [c for c in list(new.columns) if c not in old_mapped]
kept_order = [c for c in list(new.columns) if c in old_mapped]
order_ok   = (kept_order == old_mapped)
if missing or not order_ok:
    if missing:
        fail.append(f"旧引擎的列在新引擎里缺失:{missing}")
    if not order_ok:
        fail.append(f"旧引擎那些列的相对顺序变了:期望 {old_mapped},实得 {kept_order}")
    print(f"[2] 旧列全在且相对顺序不变(改名后):不通过")
else:
    print(f"[2] 旧列全在且相对顺序不变(改名后):通过 —— 旧 {len(old_mapped)} 列全部对上")
    applied = [(o, n) for o, n in RENAMED.items() if o in old.columns]
    for o, n in applied:
        print(f"      改名 {o}  ->  {n}   (TASK-8 决定2)")
    if not applied:
        print("      本次无改名生效(RENAMED 表里的列已全部退出比对,见 [5])")
    if extra:
        print(f"      新引擎另有 {len(extra)} 个新增列(合法,不计入本项失败;"
              f"其回归保护见 [6]):")
        for c in extra:
            print(f"        + {c}")

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

# ---- 6. golden 基线回归:新引擎【全部】输出 vs 上次祝福的基线 ----
# 职责分工(2026-07-26 建立,用户裁决 c1):
#   [1]-[5] 管【历史等价】——冻结的旧算法 legacy_labels() vs 新引擎,证明规则表驱动没有
#           改变旧那 30 列的任何一格。它的参照是【算法】不是数据,故不随输入变化而腐烂。
#   [6]  管【持续回归】——把当前全部输出(含 TASK-9 之后新增的列)与一份显式冻结的
#        基线文件逐格比,抓"没人打算改、却被改掉了"的情况。这是 [1]-[5] 覆盖不到的部分。
# 基线文件:analysis/labels/baseline_target_labels.csv(入版本控制)。
#
# ★★ 重新祝福(re-bless)流程 —— 本项失败时怎么办 ★★
#   本项报红【不等于出错】,它的含义是"输出变了,请你审阅"。
#   ① 先看下面打印的差异明细,判断这次改变是【有意的】还是【意外的】;
#   ② 有意的(例如你新加了一条规则、或改了某个切点)→ 重新祝福基线:
#          cp analysis/target_labels.csv analysis/labels/baseline_target_labels.csv
#      并把基线文件与引起改变的那次改动【放进同一个 commit】,message 里写明基线为什么变;
#   ③ 意外的 → 这就是本项抓到的回归,去修代码,不要动基线。
#   绝对不要"因为它红了就更新基线"——那等于把安全网拆掉。
BASELINE = ROOT / "analysis/labels/baseline_target_labels.csv"
print(f"\n[6] golden 基线回归(全部 {len(new.columns)} 列 vs 上次祝福的基线):")
if not BASELINE.exists():
    print(f"    基线文件不存在:{BASELINE}")
    print(f"    首次建立请执行:cp {ROOT/'analysis/target_labels.csv'} {BASELINE}")
    fail.append(f"golden 基线文件缺失:{BASELINE}")
else:
    base = pd.read_csv(BASELINE).set_index("subject").sort_index()
    cur  = new.sort_index()
    b_miss = [c for c in base.columns if c not in cur.columns]
    b_new  = [c for c in cur.columns if c not in base.columns]
    if list(base.index) != list(cur.index):
        fail.append(f"[6] 受试者名单与基线不同:基线 {list(base.index)} vs 当前 {list(cur.index)}")
        print(f"    受试者名单与基线不同 —— 见结论")
    elif b_miss or b_new:
        if b_miss: fail.append(f"[6] 基线有、当前无的列:{b_miss}")
        if b_new:  fail.append(f"[6] 当前有、基线无的列:{b_new}")
        print(f"    列集合与基线不同:基线有当前无 {b_miss};当前有基线无 {b_new}")
        print(f"    → 若本次新增/删除列是【有意的】,按上方「重新祝福」流程更新基线。")
    else:
        shared = list(base.columns)
        ndiff, cols_diff = 0, []
        for c in shared:
            d = int((base[c].astype(str) != cur[c].astype(str)).sum())
            if d:
                ndiff += d
                cols_diff.append((c, d))
        if ndiff:
            fail.append(f"[6] 与基线有 {ndiff} 格取值不同,涉及 {len(cols_diff)} 列")
            print(f"    与基线不同:{ndiff} 格,涉及 {len(cols_diff)} 列")
            for c, d in cols_diff:
                print(f"      {c:34} {d:>4} 格")
            print(f"    → 若本次取值改变是【有意的】,按上方「重新祝福」流程更新基线。")
        else:
            print(f"    通过 —— 24 行 × {len(shared)} 列 = {24*len(shared)} 格与基线逐格一致")

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
