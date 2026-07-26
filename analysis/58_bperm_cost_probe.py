# -*- coding: utf-8 -*-
# =============================================================================
# 58_bperm_cost_probe.py  —  B 轨置换阶段在 NPERM=5000 下要跑多久
# =============================================================================
# 这是什么(给未来任何一个不了解本项目的人):
#   这个文件【不是】生产管线的一部分,不产生任何特征、不写任何文件。
#   它是一只【探针(probe)】——把几个数字摊开供人拍板,跑完只在终端打印。
#   "探针"是本项目里一类脚本的固定叫法(见 analysis/32_、50_、51_、52_、53_、54_、57_)。
#
# 它回答什么:
#   TASK-113 把 B 轨(analysis/45_multivariate_cv.py)的置换次数 NPERM 由 500 提到 5000。
#   条目里写的成本论证是「置换只对赢过哑基线的少数组合跑,故提 10 倍的代价有界——
#   B 轨置换阶段耗时 ×10」,但【那个耗时的绝对值从未实测过】,条目里也没有。
#   而 TASK-106 的硬约束是"只跑一次"(A 轨置换实测 5.7 小时、TASK-108 后约 10.8 小时),
#   排期时需要知道 B 轨这一边到底要加多少。本探针就测这个。
#
# 怎么测(两步,都不依赖任何已有产物):
#   ① 现算【哪些组合会被送去跑置换】——复跑 45 号脚本 main 臂的主指标阶段,
#      按同一条规则筛选(回归 skill>0、分类 bacc>0.5)。这是两阶段设计的第一阶段,
#      本身很快(不含置换)。
#   ② 现测【每次置换要多久】——对 6 种模型各跑一批置换取平均。
#      RandomForest 比线性模型慢一到两个数量级,故必须【按模型分别计时再加权】,
#      拿单一均值乘组合数会严重失真。
#   然后 总耗时 ≈ Σ(该模型的组合数 × 每次置换耗时 × NPERM)。
#
# 口径与已知局限(读数前必看):
#   · 结果【依赖当前这份 analysis/features.csv】。前置批 A(TASK-108/115/116/10)会重建
#     特征表,届时"赢过哑基线的组合数"会变,本估计须重测。
#   · 是【墙钟时间】,依赖本机逻辑核数(脚本会打印)与当时的负载,换机器不可直接搬用。
#   · 置换用 joblib 并行,且每次置换内部的留一交叉验证也并行(嵌套并行)。批量小时
#     进程池启动开销会把单次耗时抬高,故本探针【先预热进程池】再计时。
#   · 只估【置换阶段】。主指标阶段(三个 variant 臂)与 A 轨的耗时不在此列。
#
# 复现:
#   ADHD_ROOT=<有 analysis/features.csv 的仓库根> .venv/bin/python analysis/58_bperm_cost_probe.py
# =============================================================================
import os, sys, time, pathlib, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore"); os.environ["PYTHONWARNINGS"] = "ignore"
np.seterr(all="ignore")
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_regression, f_classif, VarianceThreshold
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.svm import SVR, SVC
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import cross_val_predict, LeaveOneOut
from sklearn.metrics import balanced_accuracy_score
from joblib import Parallel, delayed

HERE = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path(os.environ.get("ADHD_ROOT", HERE.parent)).resolve()
if not (ROOT / "analysis/features.csv").is_file():
    sys.exit(f"找不到 {ROOT}/analysis/features.csv —— 该文件未入版本控制;"
             f"在 worktree 里跑请设 ADHD_ROOT 指向跑过 42_features_full.py 的检出。")

def banner(title, *notes):
    print("\n" + "#" * 80); print(f"# {title}")
    for n in notes: print(f"#   {n}")
    print("#" * 80)

NPERM_TARGET = 5000          # TASK-113 改后的值
N_TIME = 200                 # 每种模型计时用的置换次数
loo = LeaveOneOut()

X  = pd.read_csv(ROOT / "analysis/features.csv").set_index("subject")
Yc = pd.read_csv(ROOT / "analysis/targets.csv").set_index("subject")
Yl = pd.read_csv(ROOT / "analysis/target_labels.csv").set_index("subject")
Ylm= pd.read_csv(ROOT / "analysis/target_labels_meta.csv")
Xv = X.to_numpy(float); n = len(X); KS = [5, 10]
mag = X[["uaMag_median"]].to_numpy(float)

REG = {"ridge": lambda: Ridge(alpha=10.0), "svr": lambda: SVR(kernel="rbf", C=1.0),
       "rf": lambda: RandomForestRegressor(n_estimators=200, max_features="sqrt",
                                           min_samples_leaf=2, random_state=0, n_jobs=1)}
CLF = {"logit": lambda: LogisticRegression(penalty="l2", C=1.0, max_iter=2000),
       "svm": lambda: SVC(kernel="linear", C=1.0),
       "rf": lambda: RandomForestClassifier(n_estimators=200, max_features="sqrt",
                                            min_samples_leaf=2, random_state=0, n_jobs=1)}
def reg_pipe(m, k): return Pipeline([("vt", VarianceThreshold(0.0)), ("sel", SelectKBest(f_regression, k=k)),
                                     ("sc", StandardScaler()), ("m", m)])
def clf_pipe(m, k): return Pipeline([("vt", VarianceThreshold(0.0)), ("sel", SelectKBest(f_classif, k=k)),
                                     ("sc", StandardScaler()), ("m", m)])
def reg_skill(y, pred):
    return 1 - np.sqrt(np.mean((y - pred) ** 2)) / np.sqrt(np.mean((y - y.mean()) ** 2))
def cvp(pipe, data, y): return cross_val_predict(pipe, data, y, cv=loo, n_jobs=-1)

DEGEN = set(Ylm.loc[Ylm["degenerate"] == True, "label_name"])
BIN = [c for c in Yl.columns if c.endswith("__qbin") and c not in DEGEN]
MULTI = [f"{b}__{s}" for b in ["snap_inatt", "snap_hyper", "snap_odd", "snap_adhd_total",
                               "sdq_hyper", "sdq_totdiff"] for s in ["qter", "qquar"]
         if f"{b}__{s}" in Yl.columns
         and Yl[f"{b}__{s}"].nunique() == (3 if s == "qter" else 4) and f"{b}__{s}" not in DEGEN]

# =============================================================================
banner("探针1  哪些组合会被送去跑置换(复跑 main 臂主指标阶段,不含置换)",
       "规则与 45_multivariate_cv.py 一致:回归 skill>0、分类 bacc>0.5 才跑置换",
       f"main 臂 = {len(Yc.columns)} 连续 + {len(BIN)} 二分 + {len(MULTI)} 多分类,共 "
       f"{(len(Yc.columns)+len(BIN)+len(MULTI))*3*2} 个组合")
t0 = time.time()
qual = []          # (track, model) 会跑置换的组合
for t in Yc.columns:
    y = Yc[t].to_numpy(float)
    for mn, mk in REG.items():
        for k in KS:
            if reg_skill(y, cvp(reg_pipe(mk(), k), Xv, y)) > 0: qual.append(("reg", mn))
for tl, tr in [(BIN, "bin"), (MULTI, "multi")]:
    for t in tl:
        y = Yl[t].to_numpy(int)
        if len(np.unique(y)) < 2: continue
        for mn, mk in CLF.items():
            for k in KS:
                if balanced_accuracy_score(y, cvp(clf_pipe(mk(), k), Xv, y)) > 0.5:
                    qual.append(("clf", mn))
t_main = time.time() - t0
mix = pd.Series(qual).value_counts() if qual else pd.Series(dtype=int)
print(f"\n  主指标阶段(单臂)实测耗时 {t_main:.0f} 秒 = {t_main/60:.1f} 分钟")
print(f"  赢过哑基线、需跑置换的组合数 = {len(qual)}")
print("\n  按模型分:")
for (tr, mn), c in mix.items(): print(f"    {tr}/{mn:6} {c:3d} 个")

# =============================================================================
banner("探针2  每次置换要多久(按模型分别实测)",
       f"每种模型跑 {N_TIME} 次取平均;已先预热进程池以排除启动开销",
       "RandomForest 比线性模型慢一到两个数量级,故必须分模型计时、不能取单一均值")
Parallel(n_jobs=-1)(delayed(lambda i: i)(i) for i in range(10))     # 预热
per_ms = {}
y_reg = Yc[Yc.columns[0]].to_numpy(float)
y_clf = Yl[BIN[0]].to_numpy(int)
print(f"\n  逻辑核数 = {os.cpu_count()};计时用 k=10")
for tr, MODELS, pipe_of, yy in [("reg", REG, reg_pipe, y_reg), ("clf", CLF, clf_pipe, y_clf)]:
    for mn, mk in MODELS.items():
        p = pipe_of(mk(), 10)
        def one(s, _p=p, _y=yy):
            return cvp(_p, Xv, np.random.default_rng(s).permutation(_y))
        t = time.time(); Parallel(n_jobs=-1)(delayed(one)(int(s)) for s in range(N_TIME))
        d = (time.time() - t) / N_TIME
        per_ms[(tr, mn)] = d * 1000
        print(f"    {tr}/{mn:6} {d*1000:7.1f} ms/次  ->  NPERM={NPERM_TARGET} 单个组合 "
              f"{d*NPERM_TARGET/60:7.2f} 分钟")

# =============================================================================
banner("探针3  合计:B 轨置换阶段在 NPERM=5000 下的墙钟耗时估计",
       "总耗时 ≈ Σ(该模型的组合数 × 每次置换耗时 × NPERM)")
rows, tot = [], 0.0
for (tr, mn), c in sorted(mix.items()):
    mins = c * per_ms[(tr, mn)] / 1000 * NPERM_TARGET / 60
    tot += mins
    rows.append({"track/模型": f"{tr}/{mn}", "组合数": c,
                 "每次置换(ms)": round(per_ms[(tr, mn)], 1),
                 "单组合(分钟)": round(per_ms[(tr, mn)] / 1000 * NPERM_TARGET / 60, 2),
                 "小计(分钟)": round(mins, 1)})
print(); print(pd.DataFrame(rows).to_string(index=False))
print(f"\n  B 轨置换阶段合计 ≈ {tot:.0f} 分钟 = {tot/60:.1f} 小时")
print(f"  作为对照,NPERM=500(改动前)则约 {tot/10:.0f} 分钟 = {tot/10/60:.1f} 小时")
rf = sum(r["小计(分钟)"] for r in rows if r["track/模型"].endswith("/rf"))
if tot > 0:
    print(f"\n  其中 RandomForest 占 {rf:.0f} 分钟 = 总量的 {100*rf/tot:.0f}%"
          f"(RF 组合数只占 {sum(c for (tr,mn),c in mix.items() if mn=='rf')}/{len(qual)})")
    print("  读法:置换成本几乎【完全由 RandomForest 决定】。若要压缩这一项,")
    print("        可动的是 RF 的树数/组合数,而不是 NPERM——NPERM 是 TASK-113 的目的本身。")
print("\n  ⚠ 本估计绑定当前这份 features.csv。前置批 A 重建特征表后,'赢过哑基线的组合数'")
print("    会变,须重跑本探针。也不含主指标阶段(三个 variant 臂)与 A 轨的耗时。")

print("\n" + "=" * 80)
print("探针结束。本脚本未写任何文件。")
