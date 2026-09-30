# tip Soft Exact T+1 NEARPEAK3 Dual-Paper Observe — OPEN

Date: 2026-09-30
Status: **OPEN → OPERATING**
Human: `OPEN paper observe: TIPSOFT_P3_THETA_NEARPEAK3 (tip Soft Exact T+1 · meta-detect Path3 near-peak3 · NOT hybrid T+0 carve)`

| Book | ID | Role |
|---|---|---|
| Base | `BASE_LIVE_FUSE_COOL` | tip Soft Exact T+1 Soft+FUSE+COOL |
| Challenger | `P3_THETA_NEARPEAK3` | same shell + Path3 near-peak3 gate |

## Gates

- Exact T+1 only · hybrid Soft-core T+0 carve **FORBIDDEN**
- live_wire=false · cutover_authorized=false · Path4 OFF · broker false

## Cadence

- Ledgers: `scripts/tipsoft_p3_nearpeak3_dual_paper_ledgers.py`
- Month-end: `scripts/tipsoft_p3_nearpeak3_month_end_monitor.py`

## Non-actions

- Soft-Frozen KEEP
- Path4 live OFF
- hybrid Soft-core T+0 carve FORBIDDEN for this observe
- Do not live-wire Path3 near-peak gate from this ballot
- Cutover BLOCKED until dedicated ACCEPT

Label: `TIPSOFT_P3_NEARPEAK3_DUAL_PAPER_OBSERVE_OPEN_2026-09-30__OPERATING__NO_LIVE_WIRE`
