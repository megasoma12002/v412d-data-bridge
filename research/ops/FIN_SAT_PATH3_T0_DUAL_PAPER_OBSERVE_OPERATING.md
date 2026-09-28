# P3_T0_STATE dual-paper observe — OPERATING

- human_accept: `ACCEPT T+0 carve-out + OPEN paper observe: P3_T0_STATE (FIN×SAT Path3 · T0_CARVE_FIN_SAT_SWITCH)`
- status: **OPERATING_OBSERVE** · live_wire: false · cutover: **BLOCKED** · Soft-Frozen clips KEEP
- carve-out: **`T0_CARVE_FIN_SAT_SWITCH`** (Exact T+0 for COMP↔SAT switch only) · global Exact T+1 KEEP elsewhere
- books: `CTRL_LIVE_A10` ∥ `P3_T0_STATE` (same-day SAT_LEAD→SAT else COMP · θ=0.01)
- Stage A parent: `T0_ONLY_EDGE` · COMPOSITE+SAT_RELAX observes **KEEP**
- held-out: CAGR↑ 3.4758 pp · MDD↑ 0.0996 pp
- tip ytd CAGR↑ 2.7325 · tip 1y CAGR↑ 1.7356
- % days SAT: 24.16

## Non-actions

- Soft-Frozen clips KEEP
- Do not expand T+0 carve-out to other mechanisms
- Do not wire live / flip CONF α from this observe
- Cutover BLOCKED until dedicated ACCEPT

Repro: `repro/fin-sat-path3-t0-dual-paper-observe/`

Label: `FIN_SAT_PATH3_T0_DUAL_PAPER_OBSERVE_OPERATING_2026-09-28__OPEN__NO_LIVE`
