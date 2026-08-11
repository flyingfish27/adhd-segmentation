# -*- coding: utf-8 -*-
# =============================================================================
# 只读诊断:B 轨 sdq_totdiff 回归的【训练集表现】vs【留出表现】
# 〔2026-08-05 用户指定规格;不改变任何建模逻辑、不改随机种子、不做全样本预筛选〕
# =============================================================================
# 范围: variant=main, track=reg, target=sdq_totdiff, model∈{ridge,svr,rf}, k∈{5,10}
#
# 【为什么要手写 LOO 循环,而不是调 cross_val_predict】
#   生产脚本用的是 cross_val_predict,它只把【留出预测】还给调用方,
#   拿不到每一折 fit 好的 pipeline,因此也就拿不到【训练集上的预测】。
#   本脚本手写同一个 LOO 循环,好处是每折 fit 之后能同时 predict(train) 与 predict(test)。
#   ⚠ 这必须付出的代价是:手写循环有可能与生产流程不一致。故第 [4] 步把本脚本算出的
#     留出预测与已入库的 analysis/B_oof_predictions.csv 逐行核对,最大绝对差应为 0。
#
# 【管线定义不手抄】用 ast 从 analysis/45_multivariate_cv.py 原样抽出
#   reg_pipe / reg_skill / REG / KS 执行(同款先例:65_oof_predictions.py、
#   probe_outputs/perm_checkpoint_test.py)。45 改了本脚本跟着改,不会各自漂移。
#
# 【训练基线的口径】按用户指定:该折 23 名训练参与者 y_train 的【均值】,
#   即 train_baseline_rmse = sqrt(mean((y_train - mean(y_train))^2))。
#   注意它与生产的 reg_skill 分母【不同】——后者用全部 24 人的 y.mean()。
#   本脚本对留出侧仍调用抽出来的 reg_skill,保持与产物表同口径。
#
# 用法: .venv/bin/python analysis/probe_outputs/b_reg_train_vs_oof_probe.py
#   输入全部已入版本控制,任何 checkout 里直接跑,不要设 ADHD_ROOT。
# =============================================================================
import ast, os, pathlib, sys, warnings
warnings.filterwarnings("ignore"); os.environ["PYTHONWARNINGS"] = "ignore"
import numpy as np, pandas as pd
np.seterr(all="ignore")
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_regression, f_classif, VarianceThreshold
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.svm import SVR, SVC
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import LeaveOneOut
from scipy.stats import pearsonr, spearmanr

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC  = ROOT / "analysis/45_multivariate_cv.py"
TARGET, VARIANT, TRACK = "sdq_totdiff", "main", "reg"

# ---------------------------------------------------------------- [1] 抽生产定义
WANT_F, WANT_N = {"reg_pipe", "reg_skill"}, {"REG", "KS"}
picked = []
for node in ast.parse(SRC.read_text(encoding="utf-8")).body:
    if isinstance(node, ast.FunctionDef) and node.name in WANT_F:
        picked.append(node)
    elif isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in WANT_N for t in node.targets):
        picked.append(node)
got_f = {n.name for n in picked if isinstance(n, ast.FunctionDef)}
got_n = {t.id for n in picked if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
assert got_f == WANT_F and WANT_N <= got_n, f"抽取不全: 函数缺{WANT_F-got_f} 常量缺{WANT_N-got_n}"
NS = dict(np=np, Pipeline=Pipeline, StandardScaler=StandardScaler, SelectKBest=SelectKBest,
          f_regression=f_regression, f_classif=f_classif, VarianceThreshold=VarianceThreshold,
          Ridge=Ridge, SVR=SVR, SVC=SVC, LogisticRegression=LogisticRegression,
          RandomForestRegressor=RandomForestRegressor, RandomForestClassifier=RandomForestClassifier)
exec(compile(ast.fix_missing_locations(ast.Module(body=picked, type_ignores=[])), "<from-45>", "exec"), NS)
reg_pipe, reg_skill, REG, KS = NS["reg_pipe"], NS["reg_skill"], NS["REG"], NS["KS"]
print("=" * 100)
print("只读诊断:B 轨 %s 回归 —— 训练集表现 vs 留出表现" % TARGET)
print("=" * 100)
print("[1] 生产定义已从 %s 抽出:reg_pipe / reg_skill / REG=%s / KS=%s"
      % (SRC.name, sorted(REG), KS))

# ---------------------------------------------------------------- [2] 读输入
X = pd.read_csv(ROOT / "analysis/features.csv").set_index("subject")
y = pd.read_csv(ROOT / "analysis/targets.csv").set_index("subject")[TARGET].to_numpy(float)
SUBJ, Xv, loo = list(X.index), X.to_numpy(float), LeaveOneOut()
print("[2] X %s   y(%s) 范围 %.0f~%.0f  均值 %.3f" % (Xv.shape, TARGET, y.min(), y.max(), y.mean()))

# ---------------------------------------------------------------- [3] 逐折
rows = []
for mn, mk in REG.items():
    for k in KS:
        for tr, te in loo.split(Xv):
            pipe = reg_pipe(mk(), k)                 # 每折全新实例,与生产一致
            pipe.fit(Xv[tr], y[tr])                  # 只用 23 人 fit(含选特征与标准化)
            ptr, pte = pipe.predict(Xv[tr]), pipe.predict(Xv[te])
            ytr = y[tr]
            tr_rmse = float(np.sqrt(np.mean((ytr - ptr) ** 2)))
            tr_base = float(np.sqrt(np.mean((ytr - ytr.mean()) ** 2)))   # 基线=该折23人的均值
            rows.append(dict(
                model=mn, k=k, held_out_subject=SUBJ[te[0]],
                train_rmse=tr_rmse, train_baseline_rmse=tr_base,
                train_skill=1 - tr_rmse / tr_base if tr_base > 0 else np.nan,
                train_pearson_r=float(pearsonr(ytr, ptr)[0]) if np.std(ptr) > 0 else np.nan,
                train_spearman_rho=float(spearmanr(ytr, ptr).correlation) if np.std(ptr) > 0 else np.nan,
                y_test=float(y[te][0]), y_pred_test=float(pte[0])))
D = pd.DataFrame(rows)
print("[3] 逐折记录 %d 行 = %d 模型 × %d 个 k × %d 折" % (len(D), len(REG), len(KS), len(SUBJ)))

# ---------------------------------------------------------------- [4] 与已入库预测核对
P = pd.read_csv(ROOT / "analysis/B_oof_predictions.csv")
P = P[(P.variant == VARIANT) & (P.track == TRACK) & (P.target == TARGET)]
mg = D.merge(P[["model", "k", "subject", "y_pred"]],
             left_on=["model", "k", "held_out_subject"], right_on=["model", "k", "subject"], how="left")
assert mg.y_pred.notna().all(), "有折在 B_oof_predictions.csv 里找不到对应行"
maxdiff = float(np.abs(mg.y_pred_test - mg.y_pred).max())
print("[4] 与 analysis/B_oof_predictions.csv 逐行核对 %d 行  →  最大绝对差 = %.3e  %s"
      % (len(mg), maxdiff, "(未改变原流程)" if maxdiff < 1e-12 else "⚠ 流程已被改变!"))

# ---------------------------------------------------------------- [5] 汇总
out = []
for (mn, k), g in D.groupby(["model", "k"], sort=False):
    yt, yp = g.y_test.to_numpy(), g.y_pred_test.to_numpy()
    oof_rmse = float(np.sqrt(np.mean((yt - yp) ** 2)))
    out.append(dict(
        model=mn, k=k,
        mean_train_rmse=g.train_rmse.mean(), median_train_rmse=g.train_rmse.median(),
        mean_train_skill=g.train_skill.mean(), median_train_skill=g.train_skill.median(),
        mean_train_pearson_r=g.train_pearson_r.mean(),
        mean_train_spearman_rho=g.train_spearman_rho.mean(),
        oof_rmse=oof_rmse, oof_skill=float(reg_skill(yt, yp)),
        oof_pearson_r=float(pearsonr(yt, yp)[0]) if np.std(yp) > 0 else np.nan,
        oof_spearman_rho=float(spearmanr(yt, yp).correlation) if np.std(yp) > 0 else np.nan,
        max_oof_prediction_difference=float(np.abs(
            g.y_pred_test.to_numpy() - mg.loc[(mg.model == mn) & (mg.k == k), "y_pred"].to_numpy()).max())))
S = pd.DataFrame(out)
print()
print("=" * 100)
print("[5] 按 model × k 汇总")
print("=" * 100)
pd.set_option("display.width", 250)
print(S.to_string(index=False, float_format=lambda v: "%9.4f" % v))
print()
print("对照 analysis/B_multivariate.csv 已记的 skill(应与 oof_skill 一致):")
B = pd.read_csv(ROOT / "analysis/B_multivariate.csv")
B = B[(B.variant == VARIANT) & (B.track == TRACK) & (B.target == TARGET)][["model", "k", "skill", "rmse", "rho"]]
chk = S[["model", "k", "oof_skill", "oof_rmse", "oof_spearman_rho"]].merge(B, on=["model", "k"])
chk["skill偏差"] = (chk.oof_skill - chk.skill).abs()
chk["rmse偏差"] = (chk.oof_rmse - chk.rmse).abs()
chk["rho偏差"] = (chk.oof_spearman_rho - chk.rho).abs()
print(chk.to_string(index=False, float_format=lambda v: "%9.4f" % v))
print("  三项最大偏差: skill %.2e   rmse %.2e   rho %.2e"
      % (chk["skill偏差"].max(), chk["rmse偏差"].max(), chk["rho偏差"].max()))
print()
print("逐折明细共 %d 行,如需可另存;本脚本只读,未写任何文件。" % len(D))
sys.exit(0 if maxdiff < 1e-12 else 1)
