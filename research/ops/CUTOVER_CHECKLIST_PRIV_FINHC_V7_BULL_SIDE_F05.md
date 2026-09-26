# Cutover Checklist — 民股 Gate V7 Bull+Side F05

Status: **AUTHORIZED · LIVE WIRED (2026-09-25/26)**  
Class D ACCEPT: `ACCEPT Class D: FinPriv V7 F05`  
Soft-Frozen 3-sleeve router KEEP · FinPriv within-Financial carve live

## Progress

- [x] Dual-paper observe OPEN/OPERATING
- [x] Human near-flat ACCEPT (`CAGR floor +0.15`) — paper policy
- [x] Human dedicated Class D ACCEPT string for FinPriv live carve-out
- [x] Forward-only tip hygiene (no history rewrite)
- [x] Live wire: `LIVE_FIN_PRIV_V7_F05=True` + gate fail-closed + QC allow PRIV
- [x] `private_fin_adjusted` tip refreshed to live asof (fail-closed lag ≤ 5d)
- [ ] Sustained month-end clean (held MDD ALERT expected near-flat; watch tip)
- [ ] Sealed MDD coexist re-check under ACCEPT window (ops cadence)

## Live recipe

| Item | Value |
|---|---|
| Gate | `REG_BULL_SIDE` (Bull + Sideways) |
| Carve | `priv_frac=0.05` · `PRIV_KD_MAY` |
| Gate off | force-sell PRIV |
| Soft-Frozen | 公股 features / β densify clips **KEEP** |

Ballot: `CLASSD_FINPRIV_V7_F05_CUTOVER_BALLOT_EXECUTED_ACCEPT.md`

## Non-actions

- Do **not** rewrite tip history  
- Do **not** broker live-write until separate ACCEPT  
- Do **not** flip Soft-Frozen to 4-sleeve topology  

## Label

`CUTOVER_CHECKLIST_PRIV_FINHC_V7_BULL_SIDE_F05_2026-09-25__AUTHORIZED_LIVE_WIRED`
