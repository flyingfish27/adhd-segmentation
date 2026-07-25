# -*- coding: utf-8 -*-
# 本脚本现在做【两件事】,共用同一次数据读取(24 个 _T 文件,每个约 10 万行,读一次很贵)。
#
# ── PASS A(旧用途,保留)：A1 溯源验证 ────────────────────────────────────
#   用【notebook analysis/10_activity_verify.ipynb 里 temporal_features() 的逐字复刻件】
#   在 24 人上重算,与现存 temporal_features.csv 做列级数值比对。
#   当初要回答的问题:现存产物是否由当前版本的 notebook 代码生成
#   (文件修改时间显示 notebook 比 csv 晚 8.5 小时)。历史结论:10 列全部零差异。
#
# ── PASS B(新用途)：TASK-1 的「先证等价」回归闸门 ──────────────────────
#   TASK-102 裁决③ 规定:TASK-1 的等价证明必须在【未截断】信号上跑,基准是
#   temporal_features.BACKUP.csv,参数 pct=50, win_s=10, step_s=5, short_s=10。
#   本 PASS 直接 import analysis/42_features_full.py 里的【生产函数 time_structure()】
#   来跑——测的是生产代码本身,不是它的一份副本(这一点与 PASS A 不同:PASS A 测的
#   就是一份副本)。未截断 = 调用 load_T(path, n_max=None),绕开 N_TRUNC=73643。
#
# ── PASS C ──────────────────────────────────────────────────────────────
#   顺带比 复刻件 vs 生产函数 的逐值差,确认两者是同一套算术。
#
# 只读 data/;不写任何文件,只打印比对结果。
import importlib.util
import numpy as np, pandas as pd, pathlib

ROOT = pathlib.Path("/Users/shiyu/Projects/adhd-segmentation")
DATA = ROOT / "data"
USER_ACC = [f"motionUserAcceleration{a}(G)" for a in "XYZ"]

# --- import 生产脚本 ---
# 路径按【本文件自身所在目录】解析,不用上面那个写死的 ROOT。
#   原因:ROOT 是写死的绝对路径 /Users/shiyu/Projects/adhd-segmentation,在 git worktree
#   里跑时它指向【主检出】,会 import 到主检出那份旧脚本、而不是当前分支这份——那样
#   验证的就不是当前分支的代码。data/ 与几份 csv 仍走 ROOT(它们不随分支变化)。
# 42_features_full.py 的主流程在 __main__ 保护下,所以 import 不会触发全量跑。
HERE = pathlib.Path(__file__).resolve().parent
_target = HERE/"42_features_full.py"
_spec = importlib.util.spec_from_file_location("features_full", _target)
FF = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(FF)
print(f"被测生产脚本: {_target}")

# --- TASK-102 裁决③ 指定的参照参数,一处定义,下面两个 PASS 共用 ---
REF_PARAMS = dict(win_s=10, step_s=5, pct=50, short_s=10)

# --- notebook cell12 temporal_features() 的逐字复刻件(PASS A 用,勿动) ---
def temporal_features_notebook(mag, t, fs, win_s=10, step_s=5, pct=50):
    win, step = int(win_s * fs), int(step_s * fs)
    idx = range(0, len(mag) - win, step)
    w_mean = np.array([mag[s:s+win].mean() for s in idx])
    w_sd   = np.array([mag[s:s+win].std()  for s in idx])
    thr    = np.percentile(w_mean, pct)
    active = w_mean > thr
    edges = np.concatenate([[0], np.where(np.diff(active.astype(int)) != 0)[0] + 1, [len(active)]])
    durs   = np.diff(edges) * step_s
    states = active[edges[:-1]]
    act = durs[states]; stl = durs[~states]
    dur_min = t[-1] / 60
    def cv(x): return float(x.std() / x.mean()) if len(x) > 1 and x.mean() > 0 else np.nan
    return {
        "switch_per_min": round((len(durs) - 1) / dur_min, 3),
        "act_bout_median": round(float(np.median(act)), 1) if len(act) else np.nan,
        "stl_bout_median": round(float(np.median(stl)), 1) if len(stl) else np.nan,
        "act_bout_cv": round(cv(act), 3),
        "stl_bout_cv": round(cv(stl), 3),
        "frac_act_short": round(float((act <= 10).mean()), 3) if len(act) else np.nan,
        "within_win_sd": round(float(np.median(w_sd)), 4),
        "mag_median": round(float(np.median(mag)), 4),
        "dur_min": round(dur_min, 1),
        "n_bouts": len(durs),
    }

# --- 每列在 csv 里被存成几位小数(即 notebook 写盘时 round() 的位数) ---
NDIGITS = {"switch_per_min":3, "act_bout_median":1, "stl_bout_median":1,
           "act_bout_cv":3, "stl_bout_cv":3, "frac_act_short":3,
           "within_win_sd":4, "mag_median":4, "dur_min":1, "n_bouts":None}
COLS = list(NDIGITS)
# TASK-1 验收要求「逐列复现旧的 8 列」——即被 42_features_full.py join 进
# features.csv 的那 8 列。dur_min / n_bouts 不在这 8 列内,但 BACKUP 里有,顺便一起比。
EIGHT = ["switch_per_min","act_bout_median","stl_bout_median","act_bout_cv",
         "stl_bout_cv","frac_act_short","within_win_sd","mag_median"]

# --- 24 人名单(与 notebook 一致:figures/subject_audit.csv) ---
aud = pd.read_csv(ROOT/"figures"/"subject_audit.csv")
SUBJ = aud[(aud.status == "usable") & (aud._T.astype(str).str.lower() == "yes")].subject.tolist()
print(f"重算 n={len(SUBJ)} 人 | 参照参数 {REF_PARAMS}")
print(f"生产脚本 42_features_full.py 的 N_TRUNC={FF.N_TRUNC};"
      f"本脚本一律用 load_T(..., n_max=None) 读【未截断】全长信号\n")

rows_nb, rows_prod = [], []
for sid in SUBJ:
    df, fs, t, n_full = FF.load_T(DATA/f"{sid}_T.csv", n_max=None)   # 未截断
    assert len(df) == n_full, f"{sid}: 期望未截断,实得 {len(df)}/{n_full}"
    mag = np.linalg.norm(df[USER_ACC].astype(float).to_numpy(), axis=1)

    a = temporal_features_notebook(mag, t, fs, win_s=REF_PARAMS["win_s"],
                                   step_s=REF_PARAMS["step_s"], pct=REF_PARAMS["pct"])
    a["subject"] = sid; rows_nb.append(a)

    b = FF.time_structure(mag, t, fs, **REF_PARAMS)
    b["subject"] = sid; rows_prod.append(b)
    print(f"  ok {sid:5s} n={n_full:6d} 点 ({t[-1]/60:5.2f} min) fs={fs:.3f}")

nb   = pd.DataFrame(rows_nb).set_index("subject").sort_index()
prod = pd.DataFrame(rows_prod).set_index("subject").sort_index()   # 未取整的原始值


def compare(new, ref, cols, title, do_round):
    """逐列比 new 与 ref。do_round=True 时先按 NDIGITS 给 new 取整再比。"""
    print(f"\n===== {title} =====")
    print("(每列:最大绝对差 / 24 人中不一致的人数;阈值 1e-9)")
    allmatch = True
    for c in cols:
        x = pd.to_numeric(new[c], errors="coerce").to_numpy(float)
        if do_round and NDIGITS[c] is not None:
            x = np.array([np.nan if not np.isfinite(v) else round(float(v), NDIGITS[c]) for v in x])
        y = pd.to_numeric(ref[c], errors="coerce").to_numpy(float)
        d = np.abs(x - y)
        d = np.where(np.isnan(x) & np.isnan(y), 0.0, d)
        maxd = np.nanmax(d); nbad = int(np.nansum(d > 1e-9))
        if nbad: allmatch = False
        print(f"  {c:18} max|Δ|={maxd:.3e}  不一致={nbad:2}  {'OK' if nbad==0 else '*** DIFF ***'}")
    return allmatch


# ══════ PASS A:notebook 复刻件 vs 现存 temporal_features.csv(旧用途) ══════
old_live = pd.read_csv(ROOT/"temporal_features.csv").set_index("subject").sort_index()
print(f"\n现存 temporal_features.csv 人数={len(old_live)}  重算人数={len(nb)}"
      f"  subject 集合一致? {set(old_live.index)==set(nb.index)}")
okA = compare(nb, old_live.loc[nb.index], COLS,
              "PASS A  notebook 逐字复刻件  vs  temporal_features.csv", do_round=False)

# ══════ PASS B:生产函数 time_structure vs temporal_features.BACKUP.csv(TASK-1 闸门) ══════
bak = pd.read_csv(ROOT/"temporal_features.BACKUP.csv").set_index("subject").sort_index()
print(f"\n基准 temporal_features.BACKUP.csv 人数={len(bak)}"
      f"  subject 集合一致? {set(bak.index)==set(prod.index)}")
bak = bak.loc[prod.index]
# B-1:生产函数原始(未取整)值 vs csv 里存的(已取整)值 —— 差应只有取整残差
print("\n--- B-1:未取整的生产函数输出 vs BACKUP 里存的已取整值 ---")
print("    (差值应 ≤ 该列存储精度的半个单位,即纯取整残差;这里只看量级,不作判定)")
for c in COLS:
    x = prod[c].to_numpy(float); y = pd.to_numeric(bak[c], errors="coerce").to_numpy(float)
    d = np.abs(x - y); d = np.where(np.isnan(x) & np.isnan(y), 0.0, d)
    half = 0.5*10**(-NDIGITS[c]) if NDIGITS[c] is not None else 0.0
    print(f"  {c:18} max|Δ|={np.nanmax(d):.3e}   该列存储精度半单位={half:.3e}"
          f"   {'在取整残差内' if np.nanmax(d) <= half + 1e-12 else '>>> 超出取整残差 <<<'}")
# B-2:施加与 notebook 相同的取整后,要求逐值完全一致 —— 这是 TASK-1 的判定
okB8   = compare(prod, bak, EIGHT, "PASS B-2  生产函数 time_structure(取整后)  vs  BACKUP 的【那 8 列】", do_round=True)
okBall = compare(prod, bak, COLS,  "PASS B-2b 同上,扩到 BACKUP 里全部 10 列", do_round=True)

# ══════ PASS C:复刻件 vs 生产函数 ══════
okC = compare(prod, nb, COLS, "PASS C  生产函数(取整后)  vs  notebook 复刻件", do_round=True)

print("\n" + "="*72)
print("PASS A  现存 csv 可否由 notebook 当前代码复现 :", "是(逐列零差异)" if okA else "否")
print("PASS B  TASK-1 等价闸门(8 列 vs BACKUP)      :", "通过(逐列零差异)" if okB8 else "未通过")
print("        同上扩到 10 列                       :", "通过(逐列零差异)" if okBall else "未通过")
print("PASS C  生产函数与 notebook 复刻件是否同一算术:", "是(逐列零差异)" if okC else "否")
print("="*72)
print("判定口径:PASS B/C 把生产函数的原始输出按 BACKUP 各列的存储精度取整后再比,"
      "\n          要求 max|Δ| = 0(阈值 1e-9)。取整位数见本脚本 NDIGITS。")
