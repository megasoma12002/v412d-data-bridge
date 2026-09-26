# 民股 Gate V7 Bull+Side F05 Dual-Paper Observe — Ballot EXECUTED (OPEN)

Date: 2026-09-25  
Status: **EXECUTED**  
Human (exact):

```
OPEN observe: 民股 V7 Bull+Side F05 近持平
```

Evidence: Gate V7 Stage A **`PRIV_FINHC_SOFT`** — champion `V7_REG_BULL_SIDE_F05_KDMAY`  
held CAGR↑ **+0.18pp** (short of +0.20 HIT floor) · sealed MDD↑ **+0.14pp** · tip OK  
Soft-Frozen live membership **公股 R1 KEEP** · no Class D FinPriv expand from this ballot

## Effect

- New dual-paper observe track **OPERATING**: `BASE_LIVE_FUSE_COOL` ∥ `V7_REG_BULL_SIDE_F05_KDMAY`
- Challenger (paper only): gate `REG_BULL_SIDE` · `priv_frac=0.05` · FinPriv `PRIV_KD_MAY`
- Construction: Soft+Sleeve+**COOL** live twin + V7 gated FinPriv carve-out
- Month-end monitor wired into `ops_month_end_paper_pack.py` + `ops_alert_scan.py`
- **No live wire** — Soft-Frozen / e21 FinPriv membership needs dedicated Class D ACCEPT
- Default posture: **KEEP OBSERVE** · cutover **BLOCKED**

## Artifacts

- Observe OPEN: `PRIV_FINHC_V7_BULL_SIDE_F05_DUAL_PAPER_OBSERVE_OPEN.md`
- Operating: `PRIV_FINHC_V7_BULL_SIDE_F05_DUAL_PAPER_OBSERVE_OPERATING.md`
- Posture: `PRIV_FINHC_V7_BULL_SIDE_F05_OBSERVE_POSTURE.md`
- Cutover: `CUTOVER_CHECKLIST_PRIV_FINHC_V7_BULL_SIDE_F05.md` (**BLOCKED**)
- Ledgers: `scripts/priv_finhc_v7_bull_side_f05_dual_paper_ledgers.py`
- Monitor: `scripts/priv_finhc_v7_bull_side_f05_month_end_monitor.py`
- Repro: `repro/priv-finhc-v7-bull-side-f05-dual-paper-observe/`
- Parent Stage A: `PRIV_FINHC_CAGR_MDD_GATE_V7_DECISION_PACK.md`

## Label

`PRIV_FINHC_V7_BULL_SIDE_F05_OBSERVE_BALLOT_EXECUTED_2026-09-25__OPEN_NEAR_FLAT__NO_LIVE_WIRE`
