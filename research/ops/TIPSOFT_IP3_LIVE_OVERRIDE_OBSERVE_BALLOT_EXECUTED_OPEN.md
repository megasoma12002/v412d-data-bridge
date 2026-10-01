# TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3 — Ballot EXECUTED (OPEN observe)

Date: 2026-09-30
Status: **EXECUTED** · Soft KEEP · Path4 OFF · hybrid T+0 carve **FORBIDDEN** · live wire **false** · cutover **BLOCKED**
Register: **0kb2**
Human (exact):

```
OPEN paper observe: TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3 (tip Soft Exact T+1 · 0kb1 MUTE_S3_SAT base · force LIVE when lag42 live leads champ by >0.5% for 3d · NOT hybrid T+0)
```

## Evidence

- 0kb2 Stage A **`IP3_LIVE_STACK_RACE_HIT`** · arm `OVERRIDE_LIVE_W42_M0005_K3`
- held vs live **+1.6136** · held vs 0kb1 **+0.0959** · sealed MDD **−0.0523** · tipY **+6.0402**
- year regret↑ vs 0kb1 **+0.233** · beats_live **8**/15 (parent 7)
- 0kb4 2020 defend knife **`IP3_Y2020_DEFEND_NO_EDGE`** · `stop_freeze_0kb2=true` — residual paper stacks closed
- Draft superseded: `TIPSOFT_IP3_LIVE_STACK_RACE_OBSERVE_BALLOT_DRAFT.md`

## Effect

- Dual-paper **OPERATING**: `BASE_LIVE_FUSE_COOL` ∥ `OVERRIDE_LIVE_W42_M05_K3` (Exact T+1)
- Gate: default 0kb1 MUTE_S3_SAT 3-state; force LIVE when lag-1 42d cumret(live−champ) > 0.005 for K=3 days
- Month-end monitor wired (frozen NAV)
- Cutover **BLOCKED** — do **not** live-wire LIVE_OVERRIDE from this ballot
- 0kaw NEARPEAK3 observe **KEEP OPERATING** (parent; not replaced by this OPEN)

## Artifacts

- Operating: `TIPSOFT_IP3_LIVE_OVERRIDE_DUAL_PAPER_OBSERVE_OPERATING.md`
- Ledgers: `scripts/tipsoft_ip3_live_override_dual_paper_ledgers.py`
- Monitor: `scripts/tipsoft_ip3_live_override_month_end_monitor.py`
- Repro: `repro/tipsoft-ip3-live-override-paper-observe/`
- Cutover: `CUTOVER_CHECKLIST_TIPSOFT_IP3_LIVE_OVERRIDE.md` (**BLOCKED**)

Label: `TIPSOFT_IP3_LIVE_OVERRIDE_OBSERVE_BALLOT_EXECUTED_OPEN_2026-09-30__OPEN__NO_LIVE`
