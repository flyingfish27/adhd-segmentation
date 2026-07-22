# -*- coding: utf-8 -*-
# TASK-102 前置事实核查:24 个被试各自的记录长度、采样率、时长。
#   目的:核实 task.md 里"最短约 41 分钟 ≈ 前 73643 个采样点"这个数字,
#         并判定"截到相同采样点数"与"截到相同时长"是否等价(仅当各人 fs 相同才等价)。
#   只读 data/,不写任何文件。加载逻辑逐字照搬 42_features_full.py 的 load_T,
#   以保证测到的就是主管线实际会拿到的信号。
import numpy as np, pandas as pd, pathlib

ROOT = pathlib.Path("/Users/shiyu/Projects/adhd-segmentation")
DATA = ROOT / "data"
RAW_ACC = [f"accelerometerAcceleration{a}(G)" for a in "XYZ"]
REF_HEADER = [c.strip() for c in pd.read_csv(DATA / "H45_T.csv", sep=";", nrows=0).columns]


def sniff(path):
    with open(path) as f:
        line = f.readline()
    return ";" if line.count(";") > line.count(",") else ","


def load_T(path):                       # 与 42_features_full.py:26-38 相同
    df = pd.read_csv(path, sep=sniff(path), low_memory=False)
    cols = [c.strip() for c in df.columns]
    if "accelerometerTimestamp_sinceReboot(s)" not in cols:
        assert len(cols) == len(REF_HEADER), f"{path.name}: {len(cols)} cols"
        df.columns = REF_HEADER
    else:
        df.columns = cols
    t = df["accelerometerTimestamp_sinceReboot(s)"].astype(float).to_numpy()
    t = t - t[0]
    fs = 1.0 / np.median(np.diff(t))
    raw = np.linalg.norm(df[RAW_ACC].astype(float).to_numpy(), axis=1)
    g = float(np.median(raw))
    assert 0.9 < g < 1.1, f"{path.name}: |a| median={g:.3f}"
    return df, fs, t


aud = pd.read_csv(ROOT / "figures/subject_audit.csv")
SUBJ = sorted(aud[(aud.status == "usable") & (aud["_T"].astype(str).str.lower() == "yes")].subject.tolist())
assert len(SUBJ) == 24, f"名单不是 24 人,而是 {len(SUBJ)}"

rows = []
for i, s in enumerate(SUBJ, 1):
    df, fs, t = load_T(DATA / f"{s}_T.csv")
    n = len(t)
    dt = np.diff(t)
    rows.append({
        "subject": s,
        "n_samples": n,
        "fs_hz": fs,
        "dur_min_from_t": t[-1] / 60.0,        # 用时间戳末值算的时长
        "dur_min_from_n": n / fs / 60.0,       # 用 点数/fs 算的时长
        "dt_median_s": float(np.median(dt)),
        "dt_min_s": float(dt.min()),
        "dt_max_s": float(dt.max()),
        "gap_gt_1s": int((dt > 1.0).sum()),    # 有没有超过 1 秒的断档
    })
    print(f"[{i:2}/24] {s:5} n={n:7d} fs={fs:7.3f}Hz  dur={t[-1]/60.0:6.2f}min")

d = pd.DataFrame(rows).set_index("subject")

print("\n" + "=" * 78)
print("按时长排序(短 -> 长)")
print("=" * 78)
print(d.sort_values("dur_min_from_t")[
    ["n_samples", "fs_hz", "dur_min_from_t", "dur_min_from_n", "dt_median_s", "dt_max_s", "gap_gt_1s"]
].to_string(float_format=lambda v: f"{v:.4f}"))

print("\n" + "=" * 78)
print("采样率是否一致(决定'截点数'与'截时长'是否等价)")
print("=" * 78)
print(f"fs 最小 = {d.fs_hz.min():.6f} Hz")
print(f"fs 最大 = {d.fs_hz.max():.6f} Hz")
print(f"fs 极差 = {d.fs_hz.max() - d.fs_hz.min():.6f} Hz")
print(f"fs 唯一值个数(按小数点后 6 位) = {d.fs_hz.round(6).nunique()}")

print("\n" + "=" * 78)
print("两种截断口径的对照")
print("=" * 78)
n_min = int(d.n_samples.min())
who_n = d.n_samples.idxmin()
dur_min = float(d.dur_min_from_t.min())
who_d = d.dur_min_from_t.idxmin()
print(f"口径 P1 = 截到相同【采样点数】: N = {n_min} 点 (最短者 {who_n})")
print(f"口径 P2 = 截到相同【时长】    : D = {dur_min:.4f} 分钟 (最短者 {who_d})")
print(f"task.md 里记的数字是 73643 点 -> 与实测 n_min 之差 = {n_min - 73643} 点")

p2_counts = (d.fs_hz * dur_min * 60.0).round().astype(int)
print("\n若按 P2(相同时长)截,各人需保留的点数:")
print(f"  最少 {p2_counts.min()} 点, 最多 {p2_counts.max()} 点, 极差 {p2_counts.max()-p2_counts.min()} 点")
print(f"  P1 一律保留 {n_min} 点 -> 两口径保留点数最大相差 {int((p2_counts - n_min).abs().max())} 点")

print("\n" + "=" * 78)
print("时长分布(用于核对 task.md 说的'21 人约 60 分钟、3 人约 41-44 分钟')")
print("=" * 78)
print(f"  < 50 分钟的人数: {(d.dur_min_from_t < 50).sum()}  -> {sorted(d.index[d.dur_min_from_t < 50])}")
print(f"  >= 50 分钟的人数: {(d.dur_min_from_t >= 50).sum()}")
print(f"  时长中位数 = {d.dur_min_from_t.median():.2f} 分钟")
print(f"  截到 {dur_min:.2f} 分钟后,全体合计丢弃 {(d.dur_min_from_t - dur_min).sum():.1f} 分钟"
      f"(占原总时长 {100*(d.dur_min_from_t - dur_min).sum()/d.dur_min_from_t.sum():.1f}%)")
