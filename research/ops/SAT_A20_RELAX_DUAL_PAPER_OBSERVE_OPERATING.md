# SAT_A20_RELAX dual-paper observe — OPERATING

- human_open: `OPEN paper observe: SAT_A20_RELAX (Stage A SAT_RELAX_HIT · tip-first densify)`
- status: **OBSERVE_CLOSED** · live_wire: false · cutover: **BLOCKED** · Soft-Frozen KEEP · live CONF α=0.10 KEEP
- books: `CTRL_LIVE_A10` (α=0.1) ∥ `SAT_A20_RELAX` (α=0.2)
- Stage A: `SAT_RELAX_HIT` · COMPOSITE observe **KEEP**
- held-out: CAGR↑ 0.3354 pp · MDD↑ -0.3084 pp
- tip ytd MDD↑ 0.021 · tip 1y MDD↑ 0.021
- tip ytd CAGR↑ 0.6873 · tip 1y CAGR↑ 0.7484

## Non-actions

- Soft-Frozen KEEP
- COMPOSITE COMP_H150_x_A20 observe KEEP (parallel tip-first track)
- Do not flip live CONF α to 0.20 from observe
- Cutover BLOCKED until dedicated ACCEPT

Repro: `repro/sat-a20-relax-dual-paper-observe/`

## CLOSED (2026-10-01)

- Policy `SAT_A20_RELAX` removed from month-end / alert queue
- Why: Path3 WITHIN + ledger already LIVE (paper SAT shadow)
- Batch: `OBSERVE_CLOSE_SUPERSEDED_2026-10-01`
- Evidence/scripts **KEEP** · reopen needs new human OPEN ballot
- Live Path3 WITHIN / T0 carve / ledger / DD_SWITCH tip apply **KEEP**

