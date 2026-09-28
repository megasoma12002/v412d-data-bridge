# FIN HARD150 tip/near-window repair — Stage A Charter

Date: 2026-09-28
Status: **Stage A DONE — `LOCK_KEEP_NO_TIP_LIFT`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `SELL_a75` **KEEP** · no live wire
Parent: FIN both-quality `B_OR_K9_x_HARD150` OBSERVE OPEN · tip YTD/1y CAGR PAUSE

Human intent:

```
OPEN Stage A: FIN HARD150 tip/near-window repair · clear tip CAGR PAUSE · keep held HIT · paper only
```

Label: `FIN_HARD150_TIP_REPAIR_STAGEA_CHARTER_2026-09-28__DONE_LOCK_KEEP_NO_TIP_LIFT__NO_LIVE_WIRE`

## Question

Can a finite densify around HARD150 clear tip YTD/1y CAGR giveback (≥ -3.0pp ALERT / ≥ -5.0pp PAUSE) while held economic stays?

## Gates

- held CAGR↑ ≥ +0.15pp · MDD↑ ≥ -0.25pp · tip MDD↑ ≥ 0
- TIP_REPAIR_HIT: tip YTD & 1y CAGR↑ ≥ -3.0pp
- TIP_REPAIR_SOFT: tip CAGR ≥ -5.0pp OR beat LOCK by ≥ +3.0pp both windows

## Run

```bash
PYTHONPATH=scripts python3 scripts/fin_hard150_tip_repair_stagea.py
```
