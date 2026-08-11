#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 轨结果理解流程 —— 全阶段共用配置区。

设计约束(来自用户在阶段 0 前给出的规格,第十六节 D):
  * 所有参数集中在本文件,后续阶段不得就地改参数;
  * 设随机种子;
  * 每一步保存中间结果、输出清晰文件名、保留日志;
  * 【不覆盖原始文件】—— 本流程只允许往 OUT_DIR / LOG_DIR 下写,
    由 assert_safe_write() 在每次写盘前强制检查。

本文件【不】决定"哪个 type 值代表连续目标"。用户规格明确要求:
  若 type 的实际标签不是 regression/continuous,须先展示唯一值、由用户确认筛选规则。
  故该规则留在 CONT_TYPE_LABEL,默认 None,阶段 0 不使用,待用户确认后填入。
"""
from pathlib import Path
import sys

# ===================== 路径 =====================
ROOT = Path(__file__).resolve().parents[2]          # 仓库根
WORK_DIR = Path(__file__).resolve().parent          # outputs/understand_results/

# 输入(全部只读;本流程绝不写这些路径)
PATH_A_UNIVARIATE = ROOT / "analysis" / "A_univariate.csv"
PATH_FEATURES     = ROOT / "analysis" / "features.csv"
PATH_TARGETS      = ROOT / "analysis" / "targets.csv"
PATH_FEATURE_MENU = ROOT / "analysis" / "FEATURE_MENU.md"
PATH_SCREEN_CODE  = ROOT / "analysis" / "44_univariate_screen.py"   # 产出 A 轨结果表的脚本
PATH_FEAT_CODE    = ROOT / "analysis" / "42_features_full.py"       # 产出特征表的脚本

# 输出(唯一允许写入的两个根)
OUT_DIR = WORK_DIR / "out"
LOG_DIR = WORK_DIR / "logs"
FIG_DIR = WORK_DIR / "figures"

# ===================== 常量 =====================
SEED = 20260804          # 随机种子。阶段 0 无随机成分,此处仅为后续阶段固定。
N_SUBJECTS_EXPECTED = 24 # 【预期值,仅用于比对报告,绝不用于改数据】
N_FEATURES_EXPECTED = 608
N_CONT_TARGETS_EXPECTED = 10

# 本次分析使用 / 排除的结果表字段(用户规格第三节)
COLS_USED = ["target", "type", "feature", "rho", "perm_p",
             "loo_r2cv", "loo_rmse", "loo_mae", "rho_partial_uamag", "q_fdr"]
COLS_EXCLUDED = ["auc", "auc_partial_uamag"]

# 连续目标的筛选规则 —— 待用户在阶段 1 确认后填写,阶段 0 不得使用。
CONT_TYPE_LABEL = None

# 数值列的合法范围(用户规格第七节第 7 条),阶段 1 使用
VALUE_RANGES = {
    "rho":                (-1.0, 1.0),
    "rho_partial_uamag":  (-1.0, 1.0),
    "perm_p":             (0.0, 1.0),
    "q_fdr":              (0.0, 1.0),
    "loo_rmse":           (0.0, None),
    "loo_mae":            (0.0, None),
}


# ===================== 工具 =====================
def ensure_dirs():
    for d in (OUT_DIR, LOG_DIR, FIG_DIR):
        d.mkdir(parents=True, exist_ok=True)


def assert_safe_write(path):
    """写盘前的硬护栏:只允许写到 OUT_DIR / LOG_DIR / FIG_DIR 之下。"""
    p = Path(path).resolve()
    if not any(str(p).startswith(str(d.resolve())) for d in (OUT_DIR, LOG_DIR, FIG_DIR)):
        raise RuntimeError(f"拒绝写入流程目录之外的路径(可能覆盖原始文件): {p}")
    return p


def save_table(df, name, stage):
    """保存中间结果。文件名形如 out/phase0/phase0__<name>.csv"""
    d = OUT_DIR / stage
    d.mkdir(parents=True, exist_ok=True)
    p = assert_safe_write(d / f"{stage}__{name}.csv")
    df.to_csv(p, index=False)
    return p.relative_to(ROOT)


class Tee:
    """把 stdout 同时写进日志文件,保证「屏幕上看到的」与「落盘的」逐字一致。"""
    def __init__(self, log_path):
        self.log_path = assert_safe_write(log_path)
        self.file = open(self.log_path, "w", encoding="utf-8")
        self.stdout = sys.stdout

    def write(self, s):
        self.stdout.write(s)
        self.file.write(s)

    def flush(self):
        self.stdout.flush()
        self.file.flush()

    def __enter__(self):
        sys.stdout = self
        return self

    def __exit__(self, *exc):
        sys.stdout = self.stdout
        self.file.close()


def rule(title, char="="):
    print("\n" + char * 78)
    print(title)
    print(char * 78)
