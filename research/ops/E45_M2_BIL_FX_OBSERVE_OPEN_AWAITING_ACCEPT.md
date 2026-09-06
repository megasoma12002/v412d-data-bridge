# E45 M2 BIL_FX observe OPEN — AWAITING HUMAN ACCEPT

**Status:** `AWAITING_HUMAN_ACCEPT` — **NOT OPEN** / **NOT OPERATING**

**Candidate (default lock):** `M2_RELOC_BIL_FX_C50`

**Related draft ballot:** `research/ops/E45_M2_RELOC_OBSERVE_OPEN_BALLOT_DRAFT.md`

## What is ready (prep only)

- Dual-ledger prep: `scripts/e45_m2_bil_fx_dual_paper_ledgers.py`
- Month-end monitor prep: `scripts/e45_m2_bil_fx_month_end_monitor.py`
- Improve pack paper: `research/e45/E45_M2_BIL_FX_IMPROVE.md`
- Freeze: `research/e45/E45_M2_BIL_FX_IMPROVE_V0_FROZEN.md`

## What is NOT done

- No human **ACCEPT OPEN** cast on the observe ballot
- Not added to `ops_month_end_paper_pack.py` live observe roster
- No Soft-Frozen / DEFAULT / stitch change
- `BIL_FX` remains FX-marked USD T-bill proxy — **not** TWD cash

## Human gate

Cast on the draft ballot (HOLD / ACCEPT OPEN / REJECT). Until **ACCEPT OPEN**,
this pack stays **AWAITING_HUMAN_ACCEPT**.
