# -*- coding: utf-8 -*-
# =============================================================================
# 保存 B 轨每个组合的 24 个「留出预测」(out-of-fold predictions)
# 〔2026-08-05 用户裁决:方案B(独立脚本)+ 长表 + 编号 65;A 轨本轮不做〕
# =============================================================================
# 【为什么要单独一个脚本,而不是改 45_multivariate_cv.py】
#   45 号脚本把留出预测算完就丢:它只把 pred 喂给指标函数,rows.append 里存的是
#   rmse/mae/rho/skill/f1/acc/bacc 这些【汇总数】,pred 本身从未落盘(见 45 的
#   第 202-205 行与第 223-226 行)。要拿回逐人预测,只能重算。
#   而 45 的输出路径写死在它第 359 行 `R.to_csv(ROOT/"analysis/B_multivariate.csv")`,
#   跑它就会重写那张结果表——那张表背后是 23.7 小时的置换,不该为了取预测值而冒险重写。
#   故本脚本【完全不碰 45,也完全不碰 B_multivariate.csv】,只读、只写自己的新表。
#
# 【怎么保证算出来的就是产出那张表的那一批预测,而不是"另跑一次的近似"】
#   两道保险:
#   ① 管线与模型定义【不手抄】,用 ast 从 45_multivariate_cv.py 里原样抽出来执行
#      (reg_pipe / clf_pipe / REG / CLF / KS / reg_skill)。45 改了,这里跟着改,
#      不会各自漂移。同款做法的先例:analysis/probe_outputs/perm_checkpoint_test.py。
#   ② 算完之后【反推指标】,与 analysis/B_multivariate.csv 已有的每一行逐格比对。
#      全部对得上 ⇒ 这些预测确实就是产出那张表的那一批。对不上就报错退出。
#   之所以能指望对得上:整条链是确定性的——输入表已入版本控制、RandomForest 的
#   random_state=0、LeaveOneOut 无随机性、SelectKBest/StandardScaler/Ridge/SVR/
#   LogisticRegression/LinearSVC 均无随机性。
#
# 【输出】analysis/B_oof_predictions.csv,长表,一行 = 一个(组合 × 被试):
#   variant, track, target, model, k, subject, y_true, y_pred
#
# 【用法】.venv/bin/python analysis/65_oof_predictions.py
#   本脚本的输入全部已入版本控制,在任何 checkout / worktree 里直接跑即可,
#   【不要设 ADHD_ROOT】。唯一的例外是两个 BMI 探索臂需要 data/(未入库);
#   取不到就自动只算 main 臂并明确打印出来,不会静默少算。
# =============================================================================
import ast, os, pathlib, sys, warnings
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"
import numpy as np, pandas as pd
np.seterr(all="ignore")

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_regression, f_classif, VarianceThreshold
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.svm import SVR, SVC
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import cross_val_predict, LeaveOneOut
from sklearn.metrics import f1_score, accuracy_score, balanced_accuracy_score
from scipy.stats import spearmanr

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SRC  = HERE / "45_multivariate_cv.py"
OUT  = ROOT / "analysis/B_oof_predictions.csv"

# ---------------------------------------------------------------- 从 45 抽定义
WANT_FUNC = {"reg_pipe", "clf_pipe", "reg_skill"}
WANT_NAME = {"REG", "CLF", "KS"}
tree = ast.parse(SRC.read_text(encoding="utf-8"))
picked = []
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in WANT_FUNC:
        picked.append(node)
    elif isinstance(node, ast.Assign):
        if any(isinstance(t, ast.Name) and t.id in WANT_NAME for t in node.targets):
            picked.append(node)
got_f = {n.name for n in picked if isinstance(n, ast.FunctionDef)}
got_n = {t.id for n in picked if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
assert got_f == WANT_FUNC, f"没从 45 里抽全函数:缺 {WANT_FUNC - got_f}"
assert WANT_NAME <= got_n, f"没从 45 里抽全常量:缺 {WANT_NAME - got_n}"

NS = dict(np=np, Pipeline=Pipeline, StandardScaler=StandardScaler,
          SelectKBest=SelectKBest, f_regression=f_regression, f_classif=f_classif,
          VarianceThreshold=VarianceThreshold, Ridge=Ridge, SVR=SVR, SVC=SVC,
          LogisticRegression=LogisticRegression,
          RandomForestRegressor=RandomForestRegressor,
          RandomForestClassifier=RandomForestClassifier)
exec(compile(ast.fix_missing_locations(ast.Module(body=picked, type_ignores=[])),
             "<extracted-from-45>", "exec"), NS)
reg_pipe, clf_pipe, reg_skill = NS["reg_pipe"], NS["clf_pipe"], NS["reg_skill"]
REG, CLF, KS = NS["REG"], NS["CLF"], NS["KS"]
print(f"[1] 已从 {SRC.name} 抽出管线定义:reg_pipe / clf_pipe / reg_skill / REG / CLF / KS={KS}")
print(f"    回归模型 {sorted(REG)}   分类模型 {sorted(CLF)}")

# ---------------------------------------------------------------- 读输入
X   = pd.read_csv(ROOT / "analysis/features.csv").set_index("subject")
Yc  = pd.read_csv(ROOT / "analysis/targets.csv").set_index("subject")
Yl  = pd.read_csv(ROOT / "analysis/target_labels.csv").set_index("subject")
Ylm = pd.read_csv(ROOT / "analysis/target_labels_meta.csv")
assert list(X.index) == list(Yc.index) == list(Yl.index)
SUBJ = list(X.index)
Xv = X.to_numpy(float); n = len(X)
loo = LeaveOneOut()

# 目标选取:与 45 第 105-112 行同一套规则(只按 degenerate 过滤,不加写死名单)
DEGEN = set(Ylm.loc[Ylm["degenerate"] == True, "label_name"])
CONT  = list(Yc.columns)
BIN   = [c for c in Yl.columns if c.endswith("__qbin")]
BIN   = [c for c in BIN if c not in DEGEN]
MULTI = [c for c in Yl.columns if c.endswith(("__qter", "__qquar"))]
MULTI = [c for c in MULTI if c not in DEGEN]
print(f"[2] 目标:{len(CONT)} 连续 + {len(BIN)} 二分 + {len(MULTI)} 多分 "
      f"= {len(CONT)+len(BIN)+len(MULTI)} 个;× {len(REG)} 模型 × {len(KS)} 个 k "
      f"= {(len(CONT)+len(BIN)+len(MULTI))*len(REG)*len(KS)} 个组合/臂")

# ---------------------------------------------------------------- 三个臂(与 45 同)
DATA_ROOT = pathlib.Path(os.environ.get("ADHD_DATA_ROOT", ROOT)).resolve()
CLIN = DATA_ROOT / "data/Demographic and mental health data.csv"
bmi_s = None
if CLIN.is_file():
    clin = pd.read_csv(CLIN, encoding="utf-8-sig", dtype=str)
    clin.columns = [c.strip() for c in clin.columns]
    bmi_s = pd.to_numeric(clin.set_index("ID")["BMI"], errors="coerce").reindex(X.index)

ARMS = [("main", Xv, np.ones(n, bool))]
if bmi_s is not None:
    HAS = bmi_s.notna().to_numpy()
    if HAS.sum() >= 10 and not HAS.all():
        ARMS += [("nobmi_n23", Xv[HAS], HAS),
                 ("bmi_n23", np.hstack([Xv[HAS], bmi_s.to_numpy(float)[HAS, None]]), HAS)]
    elif HAS.all():
        ARMS += [("bmi_n23", np.hstack([Xv, bmi_s.to_numpy(float)[:, None]]), np.ones(n, bool))]
    print(f"[3] 三臂模式:data/ 可读({CLIN.name}),BMI 可得 {int(HAS.sum())}/{n} 人")
else:
    print(f"[3] ⚠ 只算 main 臂:找不到 {CLIN}(data/ 未入版本控制)。")
    print(f"    两个 BMI 探索臂需要它;要一并算,请设 ADHD_DATA_ROOT 指向有 data/ 的检出。")

# ---------------------------------------------------------------- 算留出预测
rows = []
for arm, data, m in ARMS:
    subj = [s for s, keep in zip(SUBJ, m) if keep]
    print(f"[4] [{arm}] n={data.shape[0]} 列={data.shape[1]}", flush=True)
    for t in CONT:
        y = Yc[t].to_numpy(float)[m]
        for mn, mk in REG.items():
            for k in KS:
                pred = cross_val_predict(reg_pipe(mk(), k), data, y, cv=loo, n_jobs=-1)
                rows += [dict(variant=arm, track="reg", target=t, model=mn, k=k,
                              subject=s, y_true=yt, y_pred=yp)
                         for s, yt, yp in zip(subj, y, pred)]
        print(f"      reg {t} 完成", flush=True)
    for tl, tr_name in ((BIN, "bin"), (MULTI, "multi")):
        for t in tl:
            y = Yl[t].to_numpy(int)[m]
            if len(np.unique(y)) < 2:
                continue
            for mn, mk in CLF.items():
                for k in KS:
                    pred = cross_val_predict(clf_pipe(mk(), k), data, y, cv=loo, n_jobs=-1)
                    rows += [dict(variant=arm, track=tr_name, target=t, model=mn, k=k,
                                  subject=s, y_true=int(yt), y_pred=int(yp))
                             for s, yt, yp in zip(subj, y, pred)]
            print(f"      {tr_name} {t} 完成", flush=True)

P = pd.DataFrame(rows)
P.to_csv(OUT, index=False)
print(f"\n[5] 已写出 {OUT.relative_to(ROOT)}  {P.shape[0]} 行 × {P.shape[1]} 列")
print(f"    = {P.groupby(['variant','track','target','model','k']).ngroups} 个组合 × 各自的被试数")

# ---------------------------------------------------------------- 自证:反推指标对账
print("\n[6] 自证:从这些预测反推指标,与 analysis/B_multivariate.csv 逐格比对")
B = pd.read_csv(ROOT / "analysis/B_multivariate.csv")
KEY = ["variant", "track", "target", "model", "k"]
rec = []
for key, g in P.groupby(KEY, sort=False):
    y, p = g.y_true.to_numpy(float), g.y_pred.to_numpy(float)
    d = dict(zip(KEY, key))
    if key[1] == "reg":
        d.update(rmse=float(np.sqrt(np.mean((y - p) ** 2))),
                 mae=float(np.mean(np.abs(y - p))),
                 rho=float(spearmanr(y, p).correlation) if np.std(p) > 0 else 0.0,
                 skill=float(reg_skill(y, p)))
    else:
        d.update(f1=float(f1_score(y, p, average="macro")),
                 acc=float(accuracy_score(y, p)),
                 bacc=float(balanced_accuracy_score(y, p)))
    rec.append(d)
Rc = pd.DataFrame(rec)
mg = B.merge(Rc, on=KEY, suffixes=("_表", "_反推"), how="inner")
print(f"    对上的组合:{len(mg)} / 表里 {len(B)} 行、本次算了 {len(Rc)} 个")
ok = len(mg) == len(Rc)
if len(mg) != len(Rc):
    print("    ⚠ 有组合在表里找不到对应行")
    ok = False
for c in ["rmse", "mae", "rho", "skill", "f1", "acc", "bacc"]:
    a, b = mg[c + "_表"].to_numpy(float), mg[c + "_反推"].to_numpy(float)
    both = ~np.isnan(a) & ~np.isnan(b)
    onlyone = np.isnan(a) ^ np.isnan(b)
    dev = np.abs(a[both] - b[both]).max() if both.any() else 0.0
    good = dev < 1e-9 and not onlyone.any()
    ok &= good
    print("    [%s] %-6s 比了 %4d 格,最大偏差 %.2e%s"
          % ("通过" if good else "未通过", c, int(both.sum()), dev,
             "" if not onlyone.any() else "  ⚠ 有 %d 格一边空一边有值" % int(onlyone.sum())))
print("\n总判定:" + ("通过 —— 这些留出预测就是产出 B_multivariate.csv 的那一批。"
                    if ok else "未通过 —— 反推指标与表对不上,不可当作同一批预测使用。"))
sys.exit(0 if ok else 1)
