# -*- coding: utf-8 -*-
"""TASK-120 的验收脚本:确认「把 rho 列拆成 rho + auc」这次改动【一个数都没改】。

为什么需要这个脚本:TASK-120 的改动理由是"一列装两种量会让读者误读",属于【表达层】
改动;算法一行未动、rng 种子仍是 20260717。所以它必须满足一条硬性质:
    改动前的 rho 列 == 改动后的 rho 列(连续行) 与 auc 列(二分行) 拼起来,
    其余每一列每一格【逐格相同】。
若不满足,说明改动意外碰到了数值路径 —— 那就不是表达层改动,必须查。

【改动前的那份表从哪来】不新建归档件,直接从 git 历史取:改动前的 A_univariate.csv
就是 commit c0cc6ff(TASK-106 关账那次)里的版本,内容与本次产物在数值上应完全相同,
【没有新的存证价值】,故不按归档纪律另存一份 1.4 MB 的文件。本脚本默认执行
    git show c0cc6ff:analysis/A_univariate.csv
把它读进内存比对,因此以后任何时候都能重跑,不依赖任何临时文件。

用法(在仓库任意检出里):
    .venv/bin/python analysis/probe_outputs/task120_column_split_check.py
    ADHD_A_BEFORE_REF=<别的 commit> ...   # 换成跟别的版本比
    ADHD_A_BEFORE=<某个 csv 路径> ...      # 直接给文件,跳过 git
改动后的表固定读 analysis/A_univariate.csv(即当前产物)。
"""
import io, os, pathlib, subprocess, sys
import numpy as np, pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path(os.environ.get("ADHD_ROOT", HERE.parent.parent)).resolve()

BEFORE_REF = os.environ.get("ADHD_A_BEFORE_REF", "c0cc6ff")
BEFORE_PATH = os.environ.get("ADHD_A_BEFORE")      # 给了就用文件,不给就走 git
AFTER = ROOT / "analysis/A_univariate.csv"

if not AFTER.is_file():
    sys.exit(f"找不到 {AFTER}")

if BEFORE_PATH:
    src = BEFORE_PATH
    b = pd.read_csv(BEFORE_PATH)
else:
    src = f"git show {BEFORE_REF}:analysis/A_univariate.csv"
    r = subprocess.run(["git", "-C", str(ROOT), "show",
                        f"{BEFORE_REF}:analysis/A_univariate.csv"],
                       capture_output=True)
    if r.returncode != 0:
        sys.exit(f"取不到改动前的表({src}):{r.stderr.decode(errors='replace').strip()}")
    b = pd.read_csv(io.BytesIO(r.stdout))

BEFORE = src
a = pd.read_csv(AFTER)

print("=" * 78)
print("TASK-120 验收:rho 列拆成 rho + auc,数值是否一格未变")
print("=" * 78)
print(f"改动前: {BEFORE}")
print(f"        {b.shape[0]} 行 x {b.shape[1]} 列  列名 = {list(b.columns)}")
print(f"改动后: {AFTER}")
print(f"        {a.shape[0]} 行 x {a.shape[1]} 列  列名 = {list(a.columns)}")
print()

ok = True


def check(label, cond, detail=""):
    global ok
    print(f"  [{'通过' if cond else '未通过'}] {label}" + (f"   {detail}" if detail else ""))
    if not cond:
        ok = False


# ---- 1. 行数与行的身份(target/type/feature 三元组)必须完全一致、顺序一致 ----
KEY = ["target", "type", "feature"]
check("行数相同", len(b) == len(a), f"{len(b)} vs {len(a)}")
same_key = len(b) == len(a) and (b[KEY].values == a[KEY].values).all()
check("每一行的身份(target,type,feature)逐行相同、顺序也相同", bool(same_key))

# ---- 2. 列结构:改动后应恰好多出 auc 这一列 ----
check("改动后的列 = 改动前的列 + 一列 auc",
      set(a.columns) - set(b.columns) == {"auc"} and set(b.columns) - set(a.columns) == set(),
      f"新增 {sorted(set(a.columns) - set(b.columns))}  消失 {sorted(set(b.columns) - set(a.columns))}")

# ---- 3. 拆分的完整性:rho 只在 cont 有值、auc 只在 bin 有值 ----
is_cont = a["type"].values == "cont"
is_bin = a["type"].values == "bin"
check("连续行的 auc 全为空", bool(a.loc[is_cont, "auc"].isna().all()),
      f"非空 {int(a.loc[is_cont, 'auc'].notna().sum())} 个")
check("二分行的 rho 全为空", bool(a.loc[is_bin, "rho"].isna().all()),
      f"非空 {int(a.loc[is_bin, 'rho'].notna().sum())} 个")
check("连续行的 rho 全有值", bool(a.loc[is_cont, "rho"].notna().all()),
      f"为空 {int(a.loc[is_cont, 'rho'].isna().sum())} 个")
check("二分行的 auc 全有值", bool(a.loc[is_bin, "auc"].notna().all()),
      f"为空 {int(a.loc[is_bin, 'auc'].isna().sum())} 个")

# ---- 4. 核心:把拆开的两列重新合成一列,与改动前的 rho 列逐格比 ----
#      np.where 而非 fillna:后者遇到"两列同一行都有值"会静默偏向其中一个,
#      而这里必须让那种情形也暴露出来(上面第 3 项已单独查过)。
merged = np.where(is_cont, a["rho"].to_numpy(float), a["auc"].to_numpy(float))
old_rho = b["rho"].to_numpy(float)
eq = (merged == old_rho) | (np.isnan(merged) & np.isnan(old_rho))
nbad = int((~eq).sum())
check("合成后的一列 == 改动前的 rho 列(逐格,含 NaN 位置)", nbad == 0, f"不同 {nbad} 格")
if nbad:
    idx = np.flatnonzero(~eq)[:10]
    print("      前 10 处不同:")
    for i in idx:
        print(f"        行{i} {tuple(b.loc[i, KEY])}  改动前 {old_rho[i]!r}  合成后 {merged[i]!r}")

# ---- 5. 其余每一列逐格比 ----
others = [c for c in b.columns if c != "rho"]
for c in others:
    if b[c].dtype == object or a[c].dtype == object:
        e = (b[c].astype(str).values == a[c].astype(str).values)
    else:
        bv, av = b[c].to_numpy(float), a[c].to_numpy(float)
        e = (bv == av) | (np.isnan(bv) & np.isnan(av))
    nb = int((~e).sum())
    check(f"列 {c!r} 逐格相同", nb == 0, f"不同 {nb} 格")

print()
print("=" * 78)
print("总判定:" + ("全部通过 —— 这次改动只改了列的组织方式,一个数都没变。"
                   if ok else "有未通过项 —— 改动意外碰到了数值路径,必须查。"))
print("=" * 78)
sys.exit(0 if ok else 1)
