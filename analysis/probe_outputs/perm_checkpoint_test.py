# -*- coding: utf-8 -*-
"""断点续跑机制的隔离测试。
用 ast 从【真实的 analysis/45_multivariate_cv.py】里抽出 _load_progress/_save_progress/
_seeds/_perm 四个函数与 PERM_BATCH/PROGRESS/PARTIAL 三个常量，在测试命名空间里执行，
配一个廉价的 one()。测的是真代码，不是副本。"""
import ast, io, json, hashlib, pathlib, sys, tempfile
import numpy as np

SRC = pathlib.Path("/Users/shiyu/Projects/adhd-segmentation/analysis/45_multivariate_cv.py")
tree = ast.parse(SRC.read_text(encoding="utf-8"))

WANT_FUNCS = {"_load_progress", "_save_progress", "_seeds", "_perm"}
picked = []
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in WANT_FUNCS:
        picked.append(node)
    if isinstance(node, ast.Assign):
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if any(n in ("PERM_BATCH",) for n in names):
            picked.append(node)
assert len({n.name for n in picked if isinstance(n, ast.FunctionDef)}) == 4, \
    "没抽全四个函数：%s" % sorted(n.name for n in picked if isinstance(n, ast.FunctionDef))

TMP = pathlib.Path(tempfile.mkdtemp(prefix="ckpt_test_"))
ns = {
    "json": json, "hashlib": hashlib, "np": np,
    "PROGRESS": TMP / "prog.json",
    "PARTIAL": TMP / "partial.csv",
    "say": lambda *a: None,
    "Parallel": lambda **kw: (lambda gen: list(gen)),
    "delayed": lambda f: (lambda *a, **k: f(*a, **k)),
}
mod = ast.Module(body=picked, type_ignores=[])
exec(compile(ast.fix_missing_locations(mod), "<extracted>", "exec"), ns)
NPERM_REAL = 5000

print("=" * 78)
print("测试 1：_seeds 是否与调用顺序无关（原实现依赖全局 rng 的消耗顺序）")
print("=" * 78)
ns["NPERM"] = 200
a1 = ns["_seeds"]("reg|snap_hyper|rf|10")
_ = ns["_seeds"]("clf|other|svm|5")           # 中间插一次别的调用
a2 = ns["_seeds"]("reg|snap_hyper|rf|10")
b1 = ns["_seeds"]("clf|other|svm|5")
print(f"  同一 tag 两次调用（中间夹了别的调用）完全相同: {np.array_equal(a1, a2)}")
print(f"  不同 tag 得到不同种子:                        {not np.array_equal(a1, b1)}")
print(f"  种子长度 == NPERM:                            {len(a1) == 200}")

print()
print("=" * 78)
print("测试 2：一口气跑完 vs 跑一半中断再续跑，结果是否逐位相同")
print("=" * 78)

def make_one(threshold):
    """廉价的假 one()：命中与否由种子决定，可复现。"""
    def one(seed):
        return (int(seed) % 1000) < threshold
    return one

for NP, BATCH, thr in [(200, 20, 300), (5000, 500, 137)]:
    ns["NPERM"] = NP
    ns["PERM_BATCH"] = BATCH
    tag = f"reg|test_target|rf|10"

    # (a) 一口气跑完
    ns["PROGRESS"].unlink(missing_ok=True)
    p_full = ns["_perm"](tag, make_one(thr))

    # (b) 中断：手工只跑前若干批，模拟被 kill
    ns["PROGRESS"].unlink(missing_ok=True)
    seeds = ns["_seeds"](tag)
    done, hits = 0, 0
    n_batches_before_kill = 3
    for _ in range(n_batches_before_kill):
        b = seeds[done:done + BATCH]
        hits += int(sum(make_one(thr)(int(s)) for s in b))
        done += len(b)
        prog = ns["_load_progress"](); prog[tag] = [done, hits]; ns["_save_progress"](prog)
    killed_at = done
    # (c) 续跑
    p_resume = ns["_perm"](tag, make_one(thr))

    same = (p_full == p_resume)
    print(f"  NPERM={NP:<5} BATCH={BATCH:<4} 断在第 {killed_at} 次   "
          f"一口气 p={p_full:.6f}  续跑 p={p_resume:.6f}   {'✓ 相同' if same else '✗ 不同!!'}")

print()
print("=" * 78)
print("测试 3：断多次（连续中断三回）仍与一口气跑完相同")
print("=" * 78)
ns["NPERM"] = 1000; ns["PERM_BATCH"] = 100
tag = "clf|multi_kill|svm|5"
ns["PROGRESS"].unlink(missing_ok=True)
p_full = ns["_perm"](tag, make_one(250))
ns["PROGRESS"].unlink(missing_ok=True)
seeds = ns["_seeds"](tag); done = hits = 0
for stop_after in (2, 3, 1):          # 三次中断，每次多跑几批
    for _ in range(stop_after):
        if done >= 1000: break
        b = seeds[done:done + 100]
        hits += int(sum(make_one(250)(int(s)) for s in b)); done += len(b)
        prog = ns["_load_progress"](); prog[tag] = [done, hits]; ns["_save_progress"](prog)
p_multi = ns["_perm"](tag, make_one(250))
print(f"  三次中断（累计断在第 {done} 次）  一口气 p={p_full:.6f}  多次续跑 p={p_multi:.6f}   "
      f"{'✓ 相同' if p_full == p_multi else '✗ 不同!!'}")

print()
print("=" * 78)
print("测试 4：进度文件损坏时的行为（不能让整个 14.7 小时挂掉）")
print("=" * 78)
ns["PROGRESS"].write_text("这不是合法 json{{{")
try:
    got = ns["_load_progress"]()
    print(f"  进度文件损坏 -> _load_progress() 返回 {got}（应为空字典，即从头跑，不抛异常）✓")
except Exception as e:
    print(f"  ✗ 抛了异常：{type(e).__name__}: {e}")
ns["PROGRESS"].unlink(missing_ok=True)
print()
print(f"（临时目录 {TMP}）")
