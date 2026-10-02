# TIPSOFT LIVE / Observe Inventory — 2026-10-02

Status: **INVENTORY** · Soft-Frozen **KEEP** · broker **false** · Path4 **OFF** · Soft FIN/TEL Exact T+1 **OFF**  
Parents: CLOSE superseded `OBSERVE_CLOSE_SUPERSEDED_2026-10-01` · ACCEPT DD_SWITCH tip apply `0kbd` · stabilize `0kbe` · soak gate `0kbf`

## LIVE (wired)

| Layer | State | Notes |
|---|---|---|
| Soft clips + 0050 + COOL/FUSE/SELL_a75/CONF/TEL | KEEP | Soft-Frozen shell |
| Soft FIN/TEL Exact T+1 | **OFF** | WITHIN cutover |
| Path3 `WITHIN_SLEEVE_PATH3` | LIVE | strategy cutover ACCEPT |
| Path3 T0 carve fill/emit + ledger | LIVE | mute superseded when WITHIN ON |
| tip Soft `LIVE_OVERRIDE` | LIVE stamps-only | no return-blend on tip Soft |
| tip Soft `DD_SWITCH` tip apply | **LIVE** | `path3_gate_ft_cash_apply` · not stamps-only |
| Path4 | OFF | freeze until SOAK_PASS |
| Broker / live-write | false | freeze until SOAK_PASS |

Orchestration: `live_day_overlays` (PR #408) — WITHIN → T0 plan → **DD_SWITCH apply** → emit → stamps.

## Observe KEEP (operating)

| Policy | Reg | Role |
|---|---|---|
| `TIPSOFT_P3_TRAIL42_L4_DD_SWITCH` | 0kbc→0kbd | Dual-paper twin of LIVE tip apply · month-end monitor |
| `TIPSOFT_LIVE_OVERRIDE` dual-paper | 0kb2 | Stamps / gate telemetry twin (KEEP) |

## Observe CLOSED (superseded 2026-10-01)

| Policy | Reg | Why |
|---|---|---|
| `TIPSOFT_P3_THETA_NEARPEAK3` | 0kaw | Absorbed by DD_SWITCH LIVE |
| `TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH` | 0kba | Absorbed by DD_SWITCH LIVE |
| `TIPSOFT_P3_TRAIL42_FT_CASH` | 0kbb | Twin leg → DD_SWITCH LIVE |
| `COMP_H150_x_A20` | 0k9b | Path3 WITHIN already LIVE |
| `SAT_A20_RELAX` | 0k9d | Path3 WITHIN already LIVE |
| `P3_T0_STATE` | 0k9r | T0 carve already LIVE |

Historical `*_DUAL_PAPER_OBSERVE_OPEN` JSON may still say OPEN; **canonical** status is CLOSED via `OBSERVE_CLOSE_SUPERSEDED_2026-10-01` + matching `*_OPERATING` = `OBSERVE_CLOSED`.

## Soak gate (blocks next ballots)

| Item | State |
|---|---|
| Ballot | `TIPSOFT_DD_SWITCH_SOAK_GATE` · **SOAK_OPEN** · register **0kbf** |
| Tip days since ACCEPT (2026-10-01) | **2** / floor 20 |
| Calendar days | **1** / floor 28 |
| Live↔paper overlap_n | **18** / floor 60 |
| DD_SWITCH monitor pause | none (PASS) |
| Soft FIN/TEL · Path4 · broker · year-switch · new tip Soft Stage A | **CLOSED** until SOAK_PASS |

Cadence: daily tip → dual-paper ledgers → month-end monitor → `tipsoft_dd_switch_soak_gate.py`.

## After SOAK_PASS (separate ballots only)

1. Optional Soft FIN/TEL Exact T+1 carve on Path3 OFF days  
2. Optional broker EXECUTE (PREP already filed)  
3. Optional 2020 MDD research only if held+ ∧ y2020 improve (else KEEP residual)

## Engineering open

| Item | State |
|---|---|
| PR #408 modularize Stage A / dual-paper DRY / e21 overlays | MERGEABLE · CI green · DD_SWITCH tip apply in overlays |
| Yearmix / year-oracle Stage A WIP | **NOT OPEN** (soak freeze) · leave untracked |

## Explicit non-actions

- Does not merge #408 (needs human)  
- Does not reopen CLOSED observes  
- Does not flip Soft-Frozen / broker / Path4  
- Does not rewrite forward/e21 history  

Label: `TIPSOFT_LIVE_OBSERVE_INVENTORY_2026-10-02__SOAK_OPEN__DD_SWITCH_LIVE`
