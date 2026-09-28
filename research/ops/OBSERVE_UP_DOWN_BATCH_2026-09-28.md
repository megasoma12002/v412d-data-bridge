# Observe UP/DOWN batch — 2026-09-28

Status: **EXECUTED** · Soft-Frozen **KEEP** · live stack **KEEP** · no live wire from this batch  
Human (exact):

```
請把可上 與可下進行上下
```

Canonical effect: **OPEN** listed DRAFT observes · **CLOSE/ARCHIVE** listed OPERATING paper observes (month-end / alert queue off).

Label: `OBSERVE_UP_DOWN_BATCH_2026-09-28__HUMAN_UP_DOWN`

## UP (OPEN observe)

| Track | Human / executed line | Evidence |
|---|---|---|
| FIN both-quality `B_OR_K9_x_HARD150` | `OPEN paper observe: FIN both-quality B_OR_K9_x_HARD150` | Stage B `BOTH_QUALITY_HIT` · `FIN_BOTH_QUALITY_OBSERVE_BALLOT_EXECUTED_OPEN.md` |
| `SAT_A20_H5` | `OPEN paper observe: SAT_A20_H5 (00631L CONF densify α=0.20 H=5 under COOL)` | Stage A `MECH_HIT` · `SAT_A20_H5_OBSERVE_BALLOT_EXECUTED_OPEN.md` |

## DOWN (CLOSE / ARCHIVE observe)

Month-end pack + alert scan **skip** these paper tracks (scripts retained; evidence kept):

| Track | Why close |
|---|---|
| FIN buy-quality A/B/C | Superseded by both-quality HARD150 observe |
| Soft-assist `…__SELL_a05` | Declutter paper queue · live Soft-Frozen/SELL_a75 KEEP |
| Sleeve-tilt `RSI14_a0225` | Declutter |
| FUSE_ADDITIVE | Declutter · live FUSE/COOL KEEP |
| 民營 native `PRIV_*` dual-paper | Declutter · Class D V7 F05 live carve KEEP |
| FIN within-sleeve dual-paper | Declutter · posture lock unchanged |
| FINCAP BLEND_025 | Declutter paper queue · promote already BLOCKED |
| FIN_CAP_50 | Declutter · static cutover already REJECT |
| E45 dual-paper / sleeve-local / BLEND005 | Declutter · stitch still FORBIDDEN |
| E45 defend-handoff `DH_dd06` paper | Declutter · live COOL_c8 replaced DH |

## KEEP live (unchanged)

Soft-Frozen clips · Exact T+1 · FUSE · `SELL_a75` · `COOL_c8` · `CONF_RET3_A10_H5` live · Class D FinPriv V7 F05 · TEL T3 · β clip · tip books

## Binding

1. OPEN ≠ live. Both UP tracks cutover **BLOCKED**.  
2. CLOSE ≠ delete evidence/scripts; only remove from operating month-end/alert queue.  
3. Re-open any CLOSED observe needs **new human ballot**.  
4. No Soft-Frozen retune / loss-defer / tip rewrite from this batch.

## Wiring

- Month-end: `scripts/ops_month_end_paper_pack.py`  
- Alerts: `scripts/ops_alert_scan.py`  
- Portfolio note: `RESEARCH_PORTFOLIO_KEEP_ARCHIVE.md` (append 2026-09-28)
