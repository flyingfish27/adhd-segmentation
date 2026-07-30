# -*- coding: utf-8 -*-
"""TASK-121 的验收脚本:确认「把 rho_partial_uamag 拆成 rho_partial_uamag + auc_partial_uamag」
这次改动【一个数都没改】。

与 TASK-120 的验收脚本(task120_column_split_check.py)结构相同,只是被拆的列不同。
两个脚本【故意不合并成一个带参数的通用脚本】:TASK-120 那份是已落账的证据,
其输出被 task120_column_split.md 引用;改动它会让那份快照的复现命令指向变过的代码。

要验的硬性质:
    改动前的 rho_partial_uamag 列
      == 改动后的 rho_partial_uamag(连续行) 与 auc_partial_uamag(二分行) 拼起来,
    其余每一列每一格【逐格相同】。

【改动前的那份表从哪来】不新建归档件,直接从 git 历史取:commit d23e68d
(TASK-120 合并进 main 那次)里的版本。理由同 TASK-120——数值完全相同,没有新的存证价值。

用法(在仓库任意检出里):
    .venv/bin/python analysis/probe_outputs/task121_partial_column_split_check.py
    ADHD_A_BEFORE_REF=<别的 commit> ...   # 换成跟别的版本比
    ADHD_A_BEFORE=<某个 csv 路径> ...      # 直接给文件,跳过 git
"""
import io, os, pathlib, subprocess, sys
import numpy as np, pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path(os.environ.get("ADHD_ROOT", HERE.parent.parent)).resolve()

BEFORE_REF = os.environ.get("ADHD_A_BEFORE_REF", "d23e68d")
BEFORE_PATH = os.environ.get("ADHD_A_BEFORE")
AFTER = ROOT / "analysis/A_univariate.csv"

OLD_COL = "rho_partial_uamag"      # 改动前装两种量的那一列
NEW_CONT = "rho_partial_uamag"     # 改动后:连续行的偏相关(沿用原名)
NEW_BIN = "auc_partial_uamag"      # 改动后:二分行的残差化 AUC(新列)

if not AFTER.is_file():
    sys.exit(f"找不到 {AFTER}")

if BEFORE_PATH:
    src = BEFORE_PATH
    b = pd.read_csv(BEFORE_PATH)
else:
    src = f"git show {BEFORE_REF}:analysis/A_univariate.csv"
    r = subprocess.run(["git", "-C", str(ROOT), "show",
                        f"{BEFORE_REF}:analysis/A_univariate.csv"], capture_output=True)
    if r.returncode != 0:
        sys.exit(f"取不到改动前的表({src}):{r.stderr.decode(errors='replace').strip()}")
    b = pd.read_csv(io.BytesIO(r.stdout))

a = pd.read_csv(AFTER)

print("=" * 78)
print("TASK-121 验收:rho_partial_uamag 拆成 rho_partial_uamag + auc_partial_uamag")
print("=" * 78)
print(f"改动前: {src}")
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


KEY = ["target", "type", "feature"]
check("行数相同", len(b) == len(a), f"{len(b)} vs {len(a)}")
same_key = len(b) == len(a) and (b[KEY].values == a[KEY].values).all()
check("每一行的身份(target,type,feature)逐行相同、顺序也相同", bool(same_key))

check(f"改动后的列 = 改动前的列 + 一列 {NEW_BIN}",
      set(a.columns) - set(b.columns) == {NEW_BIN} and set(b.columns) - set(a.columns) == set(),
      f"新增 {sorted(set(a.columns) - set(b.columns))}  消失 {sorted(set(b.columns) - set(a.columns))}")

is_cont = a["type"].values == "cont"
is_bin = a["type"].values == "bin"

# 这一列【只有路径B的 45 列有值】,其余特征两半都该是空 —— 故不能像 TASK-120 那样
# 要求"连续行的该列全有值",只能要求"不该有值的地方一定没值"。
check(f"连续行的 {NEW_BIN} 全为空", bool(a.loc[is_cont, NEW_BIN].isna().all()),
      f"非空 {int(a.loc[is_cont, NEW_BIN].notna().sum())} 个")
check(f"二分行的 {NEW_CONT} 全为空", bool(a.loc[is_bin, NEW_CONT].isna().all()),
      f"非空 {int(a.loc[is_bin, NEW_CONT].notna().sum())} 个")

n_cont_val = int(a.loc[is_cont, NEW_CONT].notna().sum())
n_bin_val = int(a.loc[is_bin, NEW_BIN].notna().sum())
n_old_val = int(b[OLD_COL].notna().sum())
check("两半有值的格子数加起来 == 改动前那一列有值的格子数",
      n_cont_val + n_bin_val == n_old_val,
      f"连续 {n_cont_val} + 二分 {n_bin_val} = {n_cont_val + n_bin_val}  vs 改动前 {n_old_val}")

# 核心:合成回一列,与改动前逐格比
merged = np.where(is_cont, a[NEW_CONT].to_numpy(float), a[NEW_BIN].to_numpy(float))
old = b[OLD_COL].to_numpy(float)
eq = (merged == old) | (np.isnan(merged) & np.isnan(old))
nbad = int((~eq).sum())
check(f"合成后的一列 == 改动前的 {OLD_COL} 列(逐格,含 NaN 位置)", nbad == 0, f"不同 {nbad} 格")
if nbad:
    for i in np.flatnonzero(~eq)[:10]:
        print(f"        行{i} {tuple(b.loc[i, KEY])}  改动前 {old[i]!r}  合成后 {merged[i]!r}")

# 其余每一列逐格比(含 TASK-120 拆出的 rho / auc,确认这次没碰到它们)
for c in [c for c in b.columns if c != OLD_COL]:
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
