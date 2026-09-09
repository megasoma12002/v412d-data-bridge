# Telecom Pack Cutover — Ballot OPEN

Date: 2026-09-09  
Status: **OPEN** — live Telecom still **`TEL_EQUAL`** until ACCEPT  
Human trigger: **「另開 ballot」** (pack line, separate from async/KD **STOP**)  
Soft-Frozen: **FINBAND [0.60, 0.90] KEEP** · FIN within-sleeve **KD_OPT KEEP** · DEFAULT **`E22_v2s_tw` KEEP**

## Evidence

### A — Prior Stage C (2026-09-08, FIN held at `FIN_EQUAL`)

`TELECOM_WITHIN_SLEEVE_OPTIMIZE_STAGE_C.md` @ **500M**:  
**`TEL_DIVERSIFY_PACK`** held-out **+0.331** vs `TEL_EQUAL` (best pack).

### B — Ballot re-screen (2026-09-09, FIN held at live **`KD_OPT`**) — authoritative for live stack

`TELECOM_PACK_BALLOT_RESCREEN.md`:

| id | heldout vs EQUAL | tip YTD/1y |
|---|---:|---|
| **`TEL_DIVERSIFY_PACK`** | **−0.385** | PASS/PASS |
| `TEL_SCORE_LOT_PACK` | −0.465 | PASS/PASS |
| `TEL_MIN_LOT_PACK` | −0.945 | PASS/PASS |
| `TEL_TOP2_EQUAL` | −1.180 | PASS/PASS |
| `TEL_TOP1` | −2.916 | PAUSE/PAUSE |

Under the **current live stack** (FINBAND + KD_OPT), **no pack beats `TEL_EQUAL`**.

## Reply with exactly one of

### A — KEEP / REJECT cutover (**recommended**)

```
KEEP live TEL_EQUAL
```

or

```
REJECT telecom pack cutover
```

Effect: no live Telecom within-sleeve change; pack ballot closed this cycle.

### B — DEFER

```
DEFER telecom pack cutover
```

Effect: keep observe / evidence; no live wire.

### C — ACCEPT pack cutover (name the policy) — **not recommended on re-screen**

```
ACCEPT live TEL within-sleeve cutover: TEL_DIVERSIFY_PACK
```

```
ACCEPT live TEL within-sleeve cutover: TEL_SCORE_LOT_PACK
```

```
ACCEPT live TEL within-sleeve cutover: TEL_MIN_LOT_PACK
```

Effect: authorizes a **dedicated** forward-only PR wiring the named pack into live Telecom within-sleeve (`e21`).  
Soft-Frozen / FIN KD_OPT / DEFAULT / capital unchanged.  
**Warning:** re-screen under live FIN KD_OPT shows held-out **&lt; 0** for all packs vs EQUAL.

## What ACCEPT does **not** include

- Soft-Frozen clip flip  
- FIN within-sleeve change  
- E45 stitch  
- Async/KD Telecom policies (already **STOP**)  
- History rewrite  

## Recommendation

**`KEEP live TEL_EQUAL`** — Stage C lift does **not** survive live FIN=`KD_OPT` stack.  
Async/KD line already STOP; pack cutover also lacks positive re-screen evidence.

## Label

`TELECOM_PACK_CUTOVER_BALLOT_OPEN_2026-09-09__RESCREEN_NO_LIFT__RECOMMEND_KEEP_EQUAL`
