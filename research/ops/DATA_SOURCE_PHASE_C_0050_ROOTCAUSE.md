# Data-Source Phase C — `0050` Sealed C1 DRIFT Root-Cause

Generated: `2026-09-06T07:54:32.569739+00:00`
Status: **OPS DIAGNOSTIC** — Soft-Frozen **KEEP** · no e21 primary rewrite · Yahoo TAIEX failover **opt-in only**
Soft-Frozen clip: `[0.5, 0.95]` (import only; unchanged)

## Verdict

- Root class: **`UNADJUSTED_CLOSE_SPIKE`**
- Sealed C1 DRIFT on `0050` is **not** broad series rot.
- It is dominated by **1–2 unadjusted close spikes** that destroy Pearson corr while MAD stays small.
- **C2 adj-return already PASS** on sealed `0050` — CA/split-aware path is healthy.

## Headline metrics

| Slice | N | MAD | Corr | Note |
|---|---:|---:|---:|---|
| sealed all | 878 | 0.00091 | 0.5043 | reported DRIFT |
| sealed drop \|Δret\|>5% | 877 | 0.00005 | 0.9985 | recovers PASS |
| full all | 3585 | 0.00046 | 0.4679 | |
| full drop outliers | 3583 | 0.00004 | 0.9986 | |

## Outlier days (\|live−yahoo\| > 5pp)

| Date | ret_live | ret_yahoo | Δ | Side |
|---|---:|---:|---:|---|
| 2014-01-02 | -0.0026 | -0.7506 | +0.7481 | yahoo |
| 2025-06-18 | -0.7478 | +0.0086 | -0.7565 | live |

## Live OHLC around 2025-06-18 (unit/split break)

| Date | close | adj_close | volume |
|---|---:|---:|---:|
| 2025-06-02 | 175.90 | 42.7968 | 21228875 |
| 2025-06-03 | 177.15 | 43.1010 | 7697062 |
| 2025-06-04 | 181.30 | 44.1107 | 12228053 |
| 2025-06-05 | 181.65 | 44.1958 | 10845068 |
| 2025-06-06 | 181.95 | 44.2688 | 8750467 |
| 2025-06-09 | 183.70 | 44.6946 | 14115012 |
| 2025-06-10 | 188.65 | 45.8989 | 31483080 |
| 2025-06-18 | 47.57 | 46.2980 | 252639825 |
| 2025-06-19 | 47.10 | 45.8405 | 173652638 |
| 2025-06-20 | 47.03 | 45.7724 | 84926293 |
| 2025-06-23 | 46.64 | 45.3928 | 107319197 |
| 2025-06-24 | 47.49 | 46.2201 | 56021848 |
| 2025-06-25 | 48.18 | 46.8917 | 79951752 |
| 2025-06-26 | 48.24 | 46.9501 | 79097206 |
| 2025-06-27 | 48.29 | 46.9987 | 95810636 |
| 2025-06-30 | 48.36 | 47.0669 | 60476067 |

Read: raw `close` drops ~188 → ~47 while `adj_close` stays continuous — classic **split / unit change** day. C1 live return from raw close prints a false −75% day; Yahoo peer does not → corr collapses.

## Yearly corr (shows spike years only)

| Year | N | MAD | Corr |
|---:|---:|---:|---:|
| 2012 | 247 | 0.00007 | 0.9970 |
| 2013 | 244 | 0.00002 | 0.9990 |
| 2014 | 247 | 0.00304 | 0.1882 ← spike |
| 2015 | 244 | 0.00000 | 1.0000 |
| 2016 | 241 | 0.00010 | 0.9936 |
| 2017 | 243 | 0.00005 | 0.9969 |
| 2018 | 245 | 0.00002 | 0.9996 |
| 2019 | 241 | 0.00001 | 0.9996 |
| 2020 | 245 | 0.00000 | 1.0000 |
| 2021 | 243 | 0.00006 | 0.9970 |
| 2022 | 246 | 0.00002 | 0.9999 |
| 2023 | 238 | 0.00005 | 0.9961 |
| 2024 | 242 | 0.00003 | 0.9999 |
| 2025 | 237 | 0.00321 | 0.2807 ← spike |
| 2026 | 161 | 0.00013 | 0.9968 |

## Recommended ops actions (non-ballot)

1. **Do not** flip Soft-Frozen / DEFAULT / e21 primary on this DRIFT alone.
2. Prefer **adj_close** (or C2 path) for `0050` history QC; treat raw-close C1 as spike-sensitive.
3. Patch / quarantine the two outlier dates in C1 builder if regenerating probes.
4. Keep Yahoo TAIEX failover **opt-in helper only**.

## Non-actions

- No Soft-Frozen change · no DEFAULT change · no stitch · no Goodinfo/Wantgoo/CMoney reopen

Label: `DATA_SOURCE_PHASE_C_0050_ROOTCAUSE_2026-09-06__SOFT_FROZEN_KEEP`
