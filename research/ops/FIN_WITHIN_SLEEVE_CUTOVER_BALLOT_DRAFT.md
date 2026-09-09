# FIN Within-Sleeve Live Cutover — Ballot Draft

Date: 2026-09-09  
Status: **DRAFT / NOT OPEN** — do **not** treat as ACCEPT  
Checklist: `CUTOVER_CHECKLIST_FIN_WITHIN_SLEEVE.md` (**DRAFTED — NOT AUTHORIZED**)  
Soft-Frozen: **KEEP** · DEFAULT **`E22_v2s_tw` KEEP** · stitch **FORBIDDEN** · live capital **500M** (separate ACCEPT)

## Purpose

Provide the **exact human reply strings** that would open a dedicated live cutover PR for Financial within-sleeve allocation.  
Observe tip PASS on MIX / KD is **necessary but not sufficient**.

## Pre-ballot (operator)

1. Refresh ledgers + month-end monitor.  
2. Confirm chosen book tip YTD+1y **PASS** and held-out score **> 0**.  
3. Confirm checklist gates 1–13 reviewed.  
4. Confirm capital-500M and KD_OPT observe evidence are on the branch you will wire from.

## Reply with exactly one of

### A — Cutover ACCEPT (pick one policy)

```
ACCEPT live FIN within-sleeve cutover: MIX_L75
```

```
ACCEPT live FIN within-sleeve cutover: KD_OPT
```

```
ACCEPT live FIN within-sleeve cutover: FIN_RS_SOFT_TILT_EXDIV
```

Effect: opens / authorizes a **dedicated** cutover PR that wires the named policy into live Financial within-sleeve (forward-only).  
`FIN_RS_SOFT_TILT_EXDIV` implies **explicit acceptance of tip PAUSE** (currently PAUSE asof 2026-09-08).

### B — Defer

```
DEFER live FIN within-sleeve cutover
```

Effect: keep OPERATING observe; no live wire; Soft-Frozen unchanged.

### C — Reject this cycle

```
REJECT live FIN within-sleeve cutover
```

Effect: close cutover agenda this cycle; live stays `FIN_EQUAL` within-sleeve.

## What ACCEPT does **not** include

- Soft-Frozen clip flip  
- E45 live stitch  
- Telecom within-sleeve change  
- DEFAULT books flip  
- Live capital change (already separate ballot)  
- Bundling FIN50 / L4 / BLEND cutovers  

## Recommended default when ready

If tip stays clean and operator wants max held-out among tip-PASS books → prefer:

```
ACCEPT live FIN within-sleeve cutover: KD_OPT
```

If tip stays clean and operator wants conservative mix continuity → prefer:

```
ACCEPT live FIN within-sleeve cutover: MIX_L75
```

## Label

`FIN_WITHIN_SLEEVE_CUTOVER_BALLOT_DRAFT_2026-09-09__NOT_OPEN`
