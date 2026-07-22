# -*- coding: utf-8 -*-
"""
48_label_rules_equivalence.py — TASK-8 验收①:证明规则表驱动的标签引擎
与改造前那份"切点写死在代码里"的旧脚本【逐列逐格完全一致】。

怎么证:
  参照物 = 下面 legacy_labels() 里【原样冻结】的旧 43_target_labels.py 切分逻辑
  (2026-07-22 改造前的第 14-43 行,原封不动抄进来,包括那几个写死的数字 55 和 8)。
  被测物 = analysis/target_labels.csv,由新引擎 43_target_labels.py 读
  analysis/labels/rules.yaml 生成,代码里没有任何切点数字。
  两边都在同一份 analysis/targets.csv 上算,然后 24 行 × 31 列逐格比。

唯一允许的差异是【列名】:TASK-8 决定2 把 snap_total__normT55 改名成
snap_total__wang2025T55(旧名里的 "norm" 名不副实,mean/sd 取自这 24 个孩子自己,
不是任何人群常模)。本脚本按 RENAMED 映射对齐后比【取值】,取值必须完全相同。

运行(需先跑过 analysis/43_target_labels.py):
  .venv/bin/python analysis/48_label_rules_equivalence.py
返回码 0 = 等价;1 = 有差异(差异明细会打出来)。
"""
import pathlib, sys
import pandas as pd

ROOT = pathlib.Path("/Users/shiyu/Projects/adhd-segmentation")

# TASK-8 决定2 的改名:旧列名 -> 新列名。除此之外不允许有任何列名差异。
RENAMED = {"snap_total__normT55": "snap_total__wang2025T55"}


def legacy_labels(t):
    """===== 以下为改造前 43_target_labels.py 的切分逻辑,原样冻结,勿改 =====
    (原第 14-43 行。保留其写死的 55 和 8,正因为要拿它当参照物。)"""
    out = pd.DataFrame(index=t.index)
    log = []

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

    v = t["snap_total"]; z = (v - v.mean()) / v.std(ddof=1); T = z * 10 + 50
    out["snap_total__normT55"] = (T >= 55).astype(int)

    # 旧脚本对 SDQ 多动常模 >=8 只记日志、不生成列(0/24 退化)
    deg = int((t["sdq_hyper"] >= 8).sum())
    log.append(("sdq_hyper__norm8", "norm(>=8)", {"阳性": deg, "阴性": len(t) - deg},
                "退化:0/24 达到异常线 → 不生成此列"))
    return out, log
    # ===== 冻结区结束 =====


t = pd.read_csv(ROOT / "analysis/targets.csv").set_index("subject")
old, old_log = legacy_labels(t)
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
    for o, n in RENAMED.items():
        print(f"      改名 {o}  ->  {n}   (TASK-8 决定2)")

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

# ---- 结论 ----
print("\n" + "=" * 78)
if fail:
    print(f"结论:不等价,共 {len(fail)} 处差异")
    for f in fail:
        print("  - " + f)
    sys.exit(1)
print("结论:等价。规则表驱动的引擎逐列逐格复现了旧硬编码脚本的全部 "
      f"{len(old.columns)} 列标签(其中 1 列按 TASK-8 决定2 改名,取值不变),")
print("      且旧脚本因退化而不生成的 sdq_hyper__norm8 在新引擎里同样不写进标签表、")
print("      但在 target_labels_meta.csv 里留下了记录。")
print("=" * 78)
sys.exit(0)
