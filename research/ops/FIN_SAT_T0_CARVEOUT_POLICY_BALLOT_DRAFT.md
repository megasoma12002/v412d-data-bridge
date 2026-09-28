# Soft-Frozen Exact T+0 carve-out — Ballot DRAFT (Path3 only)

Date: 2026-09-28  
Status note: **SUPERSEDED 2026-09-28** by `FIN_SAT_T0_CARVEOUT_POLICY_BALLOT_EXECUTED_ACCEPT.md`  
Status (historical): **DRAFT — NOT AUTHORIZED** · do **not** treat as ACCEPT  
Parents: 0k9q `T0_ONLY_EDGE` · `FIN_SAT_T1_LAG_PATH3_VS_BASE.md` · Soft-Frozen clips **KEEP**

## Purpose

Human is considering **Path3** (`P3_T0_STATE`) and accepting a **narrow** change to Exact T+1 for that switch only.  
This ballot separates **policy carve-out** from observe／live wire.

## Scope (narrow)

| KEEP | CHANGE (only if ACCEPT) |
|---|---|
| Soft-Frozen F/T/E clips | Exact T+1 → **T+0 same-bar allowed** |
| COOL / FUSE / SELL_a75 / live CONF α=0.10 | **Only** for FIN×SAT **COMP↔SAT day-switch** book using `trail_rel_63` same-day `SAT_LEAD` |
| COMPOSITE + SAT_RELAX observes | Does **not** authorize other mechanisms to go T+0 |
| Global Exact T+1 for sleeves／fills／cash clocks | Carve-out ID: `T0_CARVE_FIN_SAT_SWITCH` |

## Evidence

- Path compare: SF 下無 HIT；**僅 T+0** `P3_T0_STATE` HIT-shaped（held↑+3.48 · tipY↑+2.73）
- vs live base: full +3.23 · held +3.48 · sealed +4.78 CAGR↑ · yearly **14–1**
- Lag-1 / FFT / lead **cannot** close the 1-day gap under Exact T+1

## Risks (accept knowingly)

1. Same-bar leakage precedent — must stay **named carve-out only**  
2. Paper close ≠ live fill — tip/held will shrink  
3. Sealed MDD slightly worse (−0.17pp) · 2022 loses base  
4. Cutover still **BLOCKED** until separate live ballot

## Reply with exactly one of

### A — ACCEPT policy carve-out (recommended next)

```
ACCEPT Soft-Frozen carve-out: Exact T+0 for FIN×SAT COMP↔SAT switch only (T0_CARVE_FIN_SAT_SWITCH · Path3 P3_T0_STATE)
```

Effect: policy note OPEN · enables Path3 **paper observe** ballot · does **not** wire live · does **not** flip Soft-Frozen clips.

### B — ACCEPT carve-out + OPEN observe in one line

```
ACCEPT T+0 carve-out + OPEN paper observe: P3_T0_STATE (FIN×SAT Path3 · T0_CARVE_FIN_SAT_SWITCH)
```

Effect: A + dual-paper observe OPEN for `P3_T0_STATE` · cutover BLOCKED · no live.

### C — DEFER

```
DEFER Soft-Frozen Exact T+0 carve-out (Path3)
```

### D — REJECT (keep Exact T+1)

```
REJECT Soft-Frozen Exact T+0 carve-out · KEEP Exact T+1
```

Effect: Path3 remains counterfactual only · prefer Path2 tip line under Soft-Frozen.

Label: `FIN_SAT_T0_CARVEOUT_POLICY_BALLOT_DRAFT_2026-09-28__AWAITING_HUMAN`
