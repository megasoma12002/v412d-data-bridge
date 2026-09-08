# E45 C35 Dual-Monitor — Long-score + Tip-hygiene (**DRAFT / NOT OPEN**)

Date: 2026-09-08  
Status: **DESIGN DRAFT** — not OPERATING until human ACCEPT  
Ballot parent: `E45_FOUR_PATH_RECOVER_RESEARCH.md` (Path 2)  
Soft-Frozen **KEEP** · stitch **FORBIDDEN** · no live wire

## Twins

| Role | Book | Job | Tip (asof research) | Held-out |
|---|---|---|---|---:|
| **Long-score twin** | `M2_RELOC_BIL_FX_C35` | Track held-out / sealed / year MDD help | PAUSE / ALERT (expected) | **+1.81** |
| **Tip-hygiene twin (primary)** | `M2_C35_SOFT_A` | YTD / trailing-1y giveback gates | **PASS / PASS** | +0.83 |
| Tip-hygiene twin (strict) | `M2_C35_HARD_BEAR_CRISIS` | Stricter allow-list control | **PASS / PASS** | +0.72 |

## Month-end pack fields (proposed)

1. Long-score twin: held-out score, sealed score, year MDD help {2015,2018,2020,2022}  
2. Tip twin Soft_A: YTD giveback + gate, trailing-1y giveback + gate  
3. Optional strict twin HARD: same tip fields  
4. Conflict banner: long-score tip dirt **≠** Soft_A failure

## Ops rules

- Do **not** auto-flip the single observe lock from this design alone.  
- Optional companion ballot: `ACCEPT dual-monitor ungated + Soft_A` (paper ledgers only).  
- Promote / stitch still needs separate second ACCEPT + clean trailing on the **chosen** book.  
- Soft-Frozen / DEFAULT unchanged.

## Explicit non-actions

No live wire · no Soft-Frozen flip · no invent MDD · no silent lock swap.

## Human choices

| Choice | Effect |
|---|---|
| **HOLD DRAFT** (default) | Design only |
| **ACCEPT OPEN dual-monitor** | Add Soft_A (+ optional HARD) paper ledger alongside ungated C35; lock policy as ballot states |
| **REJECT** | Archive |

Label: `E45_C35_DUAL_MONITOR_DRAFT_2026-09-08__NOT_OPEN__STITCH_FORBIDDEN`
