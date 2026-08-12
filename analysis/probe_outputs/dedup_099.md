# dedup_099.md -- verbatim stdout snapshot

**Do not hand-edit.** To update, re-run the producing script and let it overwrite this file.

- Producing script: `analysis/70b_dedup_099.py`
- Repository HEAD when this snapshot was generated: `2c9a7c02a0a37baed042f40a24c89cc5b7287542`
- Reproduce with: `.venv/bin/python analysis/70b_dedup_099.py`

```text

==============================================================================
[1] GROUPS AT |Spearman| >= 0.99
==============================================================================
  working set: 607 columns (FS-D1 already applied)
  pairs with |rho| >= 0.99: 40
  groups of near-duplicates: 26 (sizes [3, 3, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2])

==============================================================================
[2] KEEP / DROP PER GROUP (keep rule in the header comment)
==============================================================================
  D01 (internal min |rho| 0.997)  KEEP uaX_std (nunique=24)
        drop uaX_rms (nunique=24, |rho| vs kept = 0.997)
        drop uaX_var (nunique=24, |rho| vs kept = 1.000)
  D02 (internal min |rho| 0.998)  KEEP uaY_std (nunique=24)
        drop uaY_rms (nunique=24, |rho| vs kept = 0.998)
        drop uaY_var (nunique=24, |rho| vs kept = 1.000)
  D03 (internal min |rho| 0.997)  KEEP uaZ_std (nunique=24)
        drop uaZ_rms (nunique=24, |rho| vs kept = 0.997)
        drop uaZ_var (nunique=24, |rho| vs kept = 1.000)
  D04 (internal min |rho| 1.000)  KEEP gyX_std (nunique=24)
        drop gyX_rms (nunique=24, |rho| vs kept = 1.000)
        drop gyX_var (nunique=24, |rho| vs kept = 1.000)
  D05 (internal min |rho| 1.000)  KEEP gyY_std (nunique=24)
        drop gyY_rms (nunique=24, |rho| vs kept = 1.000)
        drop gyY_var (nunique=24, |rho| vs kept = 1.000)
  D06 (internal min |rho| 1.000)  KEEP gyZ_std (nunique=24)
        drop gyZ_rms (nunique=24, |rho| vs kept = 1.000)
        drop gyZ_var (nunique=24, |rho| vs kept = 1.000)
  D07 (internal min |rho| 1.000)  KEEP jerk_std (nunique=24)
        drop jerk_rms (nunique=24, |rho| vs kept = 1.000)
        drop jerk_var (nunique=24, |rho| vs kept = 1.000)
  D08 (internal min |rho| 0.994)  KEEP uaX_iqr (nunique=24)
        drop uaX_mad (nunique=24, |rho| vs kept = 0.994)
  D09 (internal min |rho| 1.000)  KEEP uaMag_std (nunique=24)
        drop uaMag_var (nunique=24, |rho| vs kept = 1.000)
  D10 (internal min |rho| 1.000)  KEEP uaMag_max (nunique=24)
        drop uaMag_range (nunique=24, |rho| vs kept = 1.000)
  D11 (internal min |rho| 1.000)  KEEP jerk_madiff (nunique=24)
        drop uaMag_madiff (nunique=24, |rho| vs kept = 1.000)
  D12 (internal min |rho| 1.000)  KEEP gyX_iqr (nunique=24)
        drop gyX_mad (nunique=24, |rho| vs kept = 1.000)
  D13 (internal min |rho| 0.999)  KEEP gyY_iqr (nunique=24)
        drop gyY_mad (nunique=24, |rho| vs kept = 0.999)
  D14 (internal min |rho| 0.995)  KEEP gyY_bp_hf (nunique=24)
        drop gyY_spread (nunique=24, |rho| vs kept = 0.995)
  D15 (internal min |rho| 1.000)  KEEP gyZ_iqr (nunique=24)
        drop gyZ_mad (nunique=24, |rho| vs kept = 1.000)
  D16 (internal min |rho| 0.990)  KEEP gyZ_bp_hf (nunique=24)
        drop gyZ_spread (nunique=24, |rho| vs kept = 0.990)
  D17 (internal min |rho| 1.000)  KEEP gyMag_std (nunique=24)
        drop gyMag_var (nunique=24, |rho| vs kept = 1.000)
  D18 (internal min |rho| 1.000)  KEEP gyMag_max (nunique=24)
        drop gyMag_range (nunique=24, |rho| vs kept = 1.000)
  D19 (internal min |rho| 1.000)  KEEP pitch_std (nunique=24)
        drop pitch_var (nunique=24, |rho| vs kept = 1.000)
  D20 (internal min |rho| 0.995)  KEEP pitch_max (nunique=24)
        drop pitch_range (nunique=24, |rho| vs kept = 0.995)
  D21 (internal min |rho| 0.997)  KEEP pitch_bp_hf (nunique=24)
        drop pitch_spread (nunique=24, |rho| vs kept = 0.997)
  D22 (internal min |rho| 1.000)  KEEP roll_std (nunique=24)
        drop roll_var (nunique=24, |rho| vs kept = 1.000)
  D23 (internal min |rho| 0.991)  KEEP roll_bp_hf (nunique=24)
        drop roll_spread (nunique=24, |rho| vs kept = 0.991)
  D24 (internal min |rho| 1.000)  KEEP yaw_std (nunique=24)
        drop yaw_var (nunique=24, |rho| vs kept = 1.000)
  D25 (internal min |rho| 0.998)  KEEP yaw_bp_hf (nunique=24)
        drop yaw_spread (nunique=24, |rho| vs kept = 0.998)
  D26 (internal min |rho| 0.999)  KEEP jerk_iqr (nunique=24)
        drop jerk_mad (nunique=24, |rho| vs kept = 0.999)

==============================================================================
[3] RESULT
==============================================================================
  columns dropped: 33
  working set after FS-D3: 607 - 33 = 574 columns
  negative control uaMag_median still present: True
  phase-1 FDR survivors untouched: True

  full drop list:
    gyMag_range
    gyMag_var
    gyX_mad
    gyX_rms
    gyX_var
    gyY_mad
    gyY_rms
    gyY_spread
    gyY_var
    gyZ_mad
    gyZ_rms
    gyZ_spread
    gyZ_var
    jerk_mad
    jerk_rms
    jerk_var
    pitch_range
    pitch_spread
    pitch_var
    roll_spread
    roll_var
    uaMag_madiff
    uaMag_range
    uaMag_var
    uaX_mad
    uaX_rms
    uaX_var
    uaY_rms
    uaY_var
    uaZ_rms
    uaZ_var
    yaw_spread
    yaw_var

  verification: max pairwise |rho| among the remaining 574 columns = 0.9878 (must be < 0.99)

```
