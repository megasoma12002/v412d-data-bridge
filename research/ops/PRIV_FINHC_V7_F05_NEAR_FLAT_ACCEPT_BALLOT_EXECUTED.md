# 民股 Gate V7 Bull+Side F05 — Ballot EXECUTED (ACCEPT near-flat)

Date: 2026-09-25  
Status: **EXECUTED**  
Human (exact intent from ABCD authorize):

```
ACCEPT near-flat: V7_REG_BULL_SIDE_F05_KDMAY (CAGR floor +0.15)
```

Also covers research-order step **B**: lower HIT CAGR floor from **+0.20 → +0.15** for this V7 F05 observe champion only.

## Evidence

Stage A `PRIV_FINHC_SOFT` champion `V7_REG_BULL_SIDE_F05_KDMAY`:

| Window | Metric | vs BASE_LIVE_FUSE_COOL |
|---|---|---:|
| heldout | CAGR↑ | **+0.18pp** (≥ +0.15 floor) |
| sealed | MDD↑ | **+0.14pp** |
| heldout | MDD↑ | −0.19pp (within V7 near-flat tol −0.25) |
| tip YTD/1y | MDD↑ | **+0.14pp** OK |

Under **accepted floor +0.15**: book clears coexist-style HIT for **paper observe policy** (label `NEAR_FLAT_HIT`).

## Effect

1. Dual-paper observe track remains **OPERATING** (A): `BASE_LIVE_FUSE_COOL` ∥ `V7_REG_BULL_SIDE_F05_KDMAY`
2. Decision posture: Stage A SOFT → **NEAR_FLAT_ACCEPT** (floor +0.15) for this champion only
3. Soft-Frozen Financial membership stays **公股 R1 KEEP**
4. Cutover checklist stays **BLOCKED** — FinPriv live / Soft-Frozen topology still needs dedicated **Class D** ACCEPT string (not this ballot)
5. Do **not** retune V7 grid after sealed peek; V8 is the new-mechanism path

## Non-actions

- No tip history rewrite  
- No Soft-Frozen clip / universe expand from this ACCEPT  
- No broker live-write  

## Artifacts

- Observe OPEN/OPERATING: `PRIV_FINHC_V7_BULL_SIDE_F05_DUAL_PAPER_OBSERVE_*`  
- Posture: `PRIV_FINHC_V7_BULL_SIDE_F05_OBSERVE_POSTURE.md`  
- Cutover: `CUTOVER_CHECKLIST_PRIV_FINHC_V7_BULL_SIDE_F05.md` (**BLOCKED**)  
- Floor rescore: `PRIV_FINHC_V7_F05_NEAR_FLAT_FLOOR015_RESCORE.md`  
- Parent Stage A: `PRIV_FINHC_CAGR_MDD_GATE_V7_DECISION_PACK.md`  

## Label

`PRIV_FINHC_V7_F05_NEAR_FLAT_ACCEPT_2026-09-25__FLOOR_015__NO_LIVE_WIRE`
