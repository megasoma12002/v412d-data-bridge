# tip Soft Exact T+1 LIVE_OVERRIDE Dual-Paper Observe — OPEN

Date: 2026-09-30
Status: **OPEN → OPERATING**
Register: **0kb2**
Human: `OPEN paper observe: TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3 (tip Soft Exact T+1 · 0kb1 MUTE_S3_SAT base · force LIVE when lag42 live leads champ by >0.5% for 3d · NOT hybrid T+0)`

| Book | ID | Role |
|---|---|---|
| Base | `BASE_LIVE_FUSE_COOL` | tip Soft Exact T+1 Soft+FUSE+COOL |
| Challenger | `OVERRIDE_LIVE_W42_M05_K3` | 3-state MUTE_S3_SAT + force LIVE on lag42 lead |

## Gates

- Exact T+1 only · hybrid Soft-core T+0 carve **FORBIDDEN**
- live_wire=false · cutover_authorized=false · Path4 OFF · broker false
- year-cut / lookahead promote **FORBIDDEN**

## Cadence

- Ledgers: `scripts/tipsoft_ip3_live_override_dual_paper_ledgers.py`
- Month-end: `scripts/tipsoft_ip3_live_override_month_end_monitor.py`

## Forward watch

- Override ON: short-window live ahead of 3-state
- Override OFF: 3-state / P3+P4 resumes on live-lag segments
- held / sealed / tip floors stay green

## Non-actions

- Soft-Frozen KEEP
- Path4 live OFF
- hybrid Soft-core T+0 carve FORBIDDEN
- Do not live-wire LIVE_OVERRIDE from this ballot
- Cutover BLOCKED until dedicated ACCEPT
- 0kaw NEARPEAK3 observe KEEP (not closed by this OPEN)

Label: `TIPSOFT_IP3_LIVE_OVERRIDE_DUAL_PAPER_OBSERVE_OPEN_2026-09-30__OPERATING__NO_LIVE_WIRE`
