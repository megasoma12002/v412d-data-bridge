# FIN Within-Sleeve Observe Posture — LOCKED

Date: 2026-09-08 · KD_OPT observe added 2026-09-09  
Status: **LOCKED** · Stage D **OPERATING OBSERVE**  
Soft-Frozen: **KEEP** · live wire **FORBIDDEN** · cutover needs dedicated **ACCEPT**

## Posture (4 books)

1. **Maintain OPERATING** — month-end refresh `FIN_EQUAL` ∥ `FIN_RS_SOFT_TILT_EXDIV` ∥ `MIX_L75` ∥ **`KD_OPT`** via `ops_month_end_paper_pack.py`; compare tip + held-out.
2. **No live wire** — Soft-Frozen **KEEP**; default live remains `FIN_EQUAL` until cutover ACCEPT.
3. **Choose after observe window** — tip-clean + held-out holds → prefer among `MIX_L75` / `KD_OPT` (both tip-clean on design); max MDD + tolerate tip PAUSE → consider pure RS_EXDIV.
4. **Do not** — reopen Stage B TOP1/TOP2; stitch / live `e21` on this line.

## Operating paths

| Role | Path |
|---|---|
| Pack | `scripts/ops_month_end_paper_pack.py` (`--refresh-ledgers` as needed) |
| Ledgers | `scripts/e16_fin_within_sleeve_dual_paper_ledgers.py` |
| Monitor | `scripts/e16_fin_within_sleeve_month_end_monitor.py` |

## Tip / held-out reading guide

| Book | Expect |
|---|---|
| **`MIX_L75`** | Tip YTD+1y stay PASS (≤3pp) and held-out score stays > 0 |
| **`KD_OPT`** | Tip YTD+1y PASS; held-out score ~+0.65 design (optimize coexist) |
| **`FIN_RS_SOFT_TILT_EXDIV`** | May tip PAUSE; held-out ~+0.54 design |

## Hard non-actions

- No Soft-Frozen flip  
- No live `e21` within-sleeve wire from month-end alone  
- No Stage B hard reopen  
- No E45 stitch on this FIN within-sleeve line  

Portfolio lock: active agenda = this FIN quartet (MIX_L75 + KD_OPT coexist candidates) + E45 A05/C35 + month-end gates — `RESEARCH_PORTFOLIO_KEEP_ARCHIVE.md`.

## Label

`FIN_WITHIN_SLEEVE_OBSERVE_POSTURE_LOCKED_2026-09-09__OPERATING__KD_OPT__LIVE_WIRE_FORBIDDEN`
