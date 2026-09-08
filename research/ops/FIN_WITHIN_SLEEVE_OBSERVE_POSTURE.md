# FIN Within-Sleeve Observe Posture — LOCKED

Date: 2026-09-08  
Status: **LOCKED** · Stage D **OPERATING OBSERVE**  
Authority: human confirm of next-step posture (decision pack ballot **LOCK observe posture**)  
Soft-Frozen: **KEEP** · live wire: **FORBIDDEN**

## Posture (four locks)

1. **Maintain OPERATING** — month-end refresh `FIN_EQUAL` ∥ `FIN_RS_SOFT_TILT_EXDIV` ∥ `MIX_L75` via `ops_month_end_paper_pack.py`; compare tip + held-out.
2. **No live wire** — Soft-Frozen KEEP; cutover needs dedicated **ACCEPT**.
3. **Choose after observe window** — tip-clean + held-out holds → prefer `MIX_L75`; max MDD + tolerate tip PAUSE → consider pure RS_EXDIV.
4. **Do not** — reopen Stage B TOP1/TOP2; stitch / `e21` wire on this line.

## Cadence

| Item | Value |
|---|---|
| Pack | `scripts/ops_month_end_paper_pack.py` (`--refresh-ledgers` as needed) |
| Ledgers | `scripts/e16_fin_within_sleeve_dual_paper_ledgers.py` |
| Monitor | `scripts/e16_fin_within_sleeve_month_end_monitor.py` |
| Tip gates | ALERT > 3pp · PAUSE_REVIEW > 5pp (YTD / trailing-1y CAGR giveback vs EQUAL) |

## Selection rule (after window — not now)

| Preference | When |
|---|---|
| **`MIX_L75`** | Tip YTD+1y stay PASS (≤3pp) and held-out score stays > 0 |
| **`FIN_RS_SOFT_TILT_EXDIV`** | Need max MDD lift and accept tip PAUSE |
| **Stay EQUAL live** | Default until cutover ACCEPT |

## Explicit non-actions

- No Soft-Frozen flip  
- No live `e21` within-sleeve wire from month-end alone  
- No Stage B hard reopen  
- No E45 stitch on this FIN within-sleeve line  

## Label

`FIN_WITHIN_SLEEVE_OBSERVE_POSTURE_LOCKED_2026-09-08__OPERATING__LIVE_WIRE_FORBIDDEN`
