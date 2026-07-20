# -*- coding: utf-8 -*-
# A1 验证:用【当前 notebook 里的 temporal_features() 代码】在 24 人上重算,
# 与现存 temporal_features.csv 做【列级数值比对】,回答勘误 OPEN #5:
# 现存产物是否由当前版本的代码生成(mtime 显示 notebook 比 csv 晚 8.5h)。
# 只读 data/;不写任何文件,只打印比对结果。
import numpy as np, pandas as pd, pathlib
ROOT = pathlib.Path("/Users/shiyu/Projects/adhd-segmentation")
DATA = ROOT / "data"
RAW_ACC  = [f"accelerometerAcceleration{a}(G)" for a in "XYZ"]
USER_ACC = [f"motionUserAcceleration{a}(G)"    for a in "XYZ"]
REF_HEADER = [c.strip() for c in pd.read_csv(DATA/"H45_T.csv", sep=";", nrows=0).columns]

def sniff(path):
    with open(path) as f: line = f.readline()
    return ";" if line.count(";") > line.count(",") else ","

def load_T(path):                              # 复刻 notebook cell9 的 load_T
    df = pd.read_csv(path, sep=sniff(path), low_memory=False)
    cols = [c.strip() for c in df.columns]
    if "accelerometerTimestamp_sinceReboot(s)" not in cols:
        assert len(cols) == len(REF_HEADER)
        df.columns = REF_HEADER
    else:
        df.columns = cols
    t = df["accelerometerTimestamp_sinceReboot(s)"].astype(float).to_numpy(); t = t - t[0]
    fs = 1.0 / np.median(np.diff(t))
    raw = np.linalg.norm(df[RAW_ACC].astype(float).to_numpy(), axis=1)
    g = float(np.median(raw)); assert 0.9 < g < 1.1
    return df, fs, t

def temporal_features(mag, t, fs, win_s=10, step_s=5, pct=50):   # 复刻 notebook cell12,逐字
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

# --- 24 人名单(与 notebook 一致:figures/subject_audit.csv) ---
aud = pd.read_csv(ROOT/"figures/subject_audit.csv")
SUBJ = aud[(aud.status == "usable") & (aud._T.astype(str).str.lower() == "yes")].subject.tolist()
print(f"重算 n={len(SUBJ)} 人")

rows = []
for sid in SUBJ:
    df, fs, t = load_T(DATA/f"{sid}_T.csv")
    mag = np.linalg.norm(df[USER_ACC].astype(float).to_numpy(), axis=1)
    feats = temporal_features(mag, t, fs); feats["subject"] = sid
    rows.append(feats)
new = pd.DataFrame(rows).set_index("subject").sort_index()

old = pd.read_csv(ROOT/"temporal_features.csv").set_index("subject").sort_index()
cols = ["switch_per_min","act_bout_median","stl_bout_median","act_bout_cv","stl_bout_cv",
        "frac_act_short","within_win_sd","mag_median","dur_min","n_bouts"]

print(f"\n现存 temporal_features.csv 人数={len(old)}  重算人数={len(new)}")
print("subject 集合一致?", set(old.index) == set(new.index))
common = sorted(set(old.index) & set(new.index))
new = new.loc[common]; old = old.loc[common]

print("\n===== 列级数值比对(每列 最大绝对差 / 不一致人数) =====")
allmatch = True
for c in cols:
    a = pd.to_numeric(old[c], errors="coerce").to_numpy(float)
    b = pd.to_numeric(new[c], errors="coerce").to_numpy(float)
    diff = np.abs(a - b)
    both_nan = np.isnan(a) & np.isnan(b)
    diff = np.where(both_nan, 0.0, diff)
    maxd = np.nanmax(diff); nbad = int(np.nansum(diff > 1e-9))
    flag = "OK" if (maxd <= 1e-9 or np.isnan(maxd)) else "*** DIFF ***"
    if nbad: allmatch = False
    print(f"  {c:18} max|Δ|={maxd:.3e}  不一致={nbad:2}  {flag}")

print("\n结论:", "当前代码可完全复现现存 csv(逐列数值一致)" if allmatch
      else "当前代码【不能】完全复现 → 现存 csv 由不同版本代码生成")
