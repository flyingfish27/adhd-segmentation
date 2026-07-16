# -*- coding: utf-8 -*-
# 目的:对传感器 CSV 的 58 列逐列做实证审计——取值范围/样例/缺失,
# 用来佐证 CODEBOOK §4 里每列的含义(不靠猜,用数据本身对齐)。只读 data/。
import numpy as np, pandas as pd
D="/Users/shiyu/Projects/adhd-segmentation/data/"
def audit(f, sep, nrows=60000):
    df=pd.read_csv(D+f, sep=sep, nrows=nrows)
    print(f"\n{'='*90}\n{f}  (前{len(df)}行, {df.shape[1]}列)\n{'='*90}")
    for c in df.columns:
        s=df[c]
        nn=s.notna().sum()
        if s.dtype==object:
            uq=pd.unique(s.dropna())
            show=list(uq[:5])
            print(f"  {c:42} 文本  非空{nn:6}  取值≈{show}")
        else:
            print(f"  {c:42} 数值  非空{nn:6}  min={np.nanmin(s):.4g}  max={np.nanmax(s):.4g}  样例={s.dropna().iloc[len(s.dropna())//2]:.4g}")

audit("H1_F.csv", ",")
audit("H2_T.csv", ";")
