# Path3 observe θ=0.005 + T+0 fill/emit — Ballot EXECUTED (ACCEPT)

Date: 2026-09-29  
Status: **EXECUTED ACCEPT** · Soft-Frozen Exact T+1 **KEEP** elsewhere · Path3 observe **OPERATING** · broker write **false** · strategy cutover **BLOCKED**

Register: **0ka7** · Parents: 0k9r carve/observe · 0k9u fill PREP · 0k9w emit PREP · 0ka3–0ka6 θ/window research

## Human (exact)

```
ACCEPT Path3 observe retune: SAT_LEAD θ=0.005 (P3_T0_STATE · T0_CARVE_FIN_SAT_SWITCH · parents 0ka3–0ka6)
ACCEPT Live fill carve-out: T0_CARVE_FIN_SAT_SWITCH same-bar (Path3 P3_T0_STATE only · Soft-Frozen Exact T+1 KEEP elsewhere)
ACCEPT Live Path3 switch emitter: T0_CARVE_FIN_SAT_SWITCH tagged orders (P3_T0_STATE · Soft-Frozen Exact T+1 KEEP elsewhere · cutover still BLOCKED)
```

## What changed

| Item | Before | After ACCEPT |
|---|---|---|
| Observe `SAT_LEAD` θ | 0.01 | **0.005** |
| Dual-paper `P3_T0_STATE` NAV/signal | θ=0.01 | **regenerated θ=0.005** |
| `LIVE.live_t0_carve_fin_sat_switch_fill` | False | **True** |
| `LIVE.live_t0_carve_fin_sat_switch_emit` | False | **True** |
| Tagged `-P3T0` same-bar MOC | blocked | **allowed when tagged** |
| COMP↔SAT `delta_shares` weight engine | not wired | **still not wired** (emit fail-closed without plan) |
| Soft-Frozen global Exact T+1 | KEEP | **KEEP** |
| Broker SendOrder / Path3 router cutover | BLOCKED | **BLOCKED** |

## Evidence (0ka6 window pack)

- θ=0.005 vs BASE: full↑ +3.56 · held↑ +3.77 · sealed↑ +4.75 · sealed MDD↑ −0.17 (ACCEPTABLE)
- vs θ=0.01: tipY↑ +2.88 · yearly ret W–L 13–2 (adds 2024) · MDD W–L 9–6

## Non-actions

- Do not expand T+0 beyond `T0_CARVE_FIN_SAT_SWITCH`
- Do not flip Soft-Frozen clips / CONF α
- Do not enable broker live-write from this ballot

Supersedes DRAFT: `LIVE_T0_CARVE_FIN_SAT_SWITCH_FILL_BALLOT_DRAFT.md` · `LIVE_PATH3_T0_SWITCH_EMITTER_BALLOT_DRAFT.md`

Label: `FIN_SAT_PATH3_OBSERVE_THETA005_T0_LIVE_BALLOT_EXECUTED_2026-09-29__ACCEPT__NO_BROKER`
