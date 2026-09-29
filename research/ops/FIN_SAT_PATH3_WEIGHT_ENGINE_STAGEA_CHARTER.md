# FIN_SAT_PATH3_WEIGHT_ENGINE_STAGEA_CHARTER

Date: 2026-09-29  
Status: **Stage A CHARTER — COMP↔SAT weight engine (proxy)** · Soft-Frozen **KEEP** · emit/fill **ON** (0ka7) · broker **false** · cutover **BLOCKED** · no Soft clip / CONF α flip  
Parents: 0ka7 EXECUTED (θ=0.005 · fill/emit ON · weight engine **not wired**) · 0k9w emitter PREP · 0k9u fill PREP · 0k9r Path3 observe  
Register: **0ka8**

## Question

With Path3 emit/fill already ON, can we wire a **pragmatic `delta_shares` provider** that:

1. On Path3 flip days, produces a non-empty tagged `-P3T0` order plan  
2. Survives board-lot filter → same-bar MOC fill path (`T0_CARVE_FIN_SAT_SWITCH`)  
3. Uses **existing Soft-Frozen / e21 / emitter / fill** code — without rebuilding full COMP/SAT paper engines  
4. Leaves Soft-Frozen live sleeve KEEP · broker false · cutover BLOCKED  

## Findings that bind Stage A scope

### Soft-Frozen live target → shares (do not reinvent)

| Step | SSOT | Role |
|---|---|---|
| Sleeve targets | `e16_soft_frozen_base.build_soft_frozen_targets` → `tw` | Financial / Telecom / 0050 clips + L1 |
| Gap → trade $ | `sleeve_gap_trade.sleeve_trade_from_gap` via `live_rebalance_orders` | L1 gap → scaled trade |
| Name lots | `live_rebalance_orders.build_live_order_rows` → `within_sleeve_alloc.allocate_sleeve_orders` | KD_OPT / FinPriv / TEL T3 |
| Pipeline | `e21_forward_pipeline` | pos/cash/nav → Soft orders → **then** Path3 hook |
| Path3 hook today | `maybe_emit_switch_orders(..., delta_shares=None)` | fail-closed `weight_engine_not_wired` |

Live state sample (`forward/e21/`): `portfolio_state.json` has real `positions` + `last_nav`; `live_market.csv` has closes for Soft universe (`0050,2412,2880,2886,2892,3045,4904,5880,TAIEX`) through **2026-09-24**. Sufficient for paper-demo prices/pos.

### COMP / SAT paper books ≠ live share maps

| Book | What it is | Sleeve schedule vs Soft | Within-sleeve |
|---|---|---|---|
| Soft live / `CTRL_LIVE_A10` | e21 tip | Soft clips · CONF α=**0.10** | KD_OPT + FinPriv + TEL |
| `COMP_H150_x_A20` | paper observe | Soft clips · CONF α=**0.20** H=5 | **OR_K9 × HARD150** |
| `SAT_A20_RELAX` | paper observe | Soft clips · CONF α=**0.20** H=5 | **no** OR_K9/HARD (RELAX) |
| `P3_T0_STATE` | paper NAV blend | N/A — **return mix** of COMP/SAT NAV | **no positions** |

Measured: COMP vs SAT `schedule_*.csv` sleeve columns (`Financial/Telecom/0050/DEF`) are **byte-identical** (α=0.20 both). Divergence is path-dependent FIN name selection, not sleeve notional.

**Verdict on approximation:** Soft-Frozen live pos + CONF α difference **cannot** recover COMP↔SAT target shares.

- COMP−SAT α delta = **0** (both 0.20)  
- Soft live α=0.10 is a different axis (densify), not the Path3 flip  
- Path3 observe has NAV only — no share ledger to clone  
→ Full engine rebuild = Stage B. Stage A uses an **explicit named proxy**.

### Emitter / fill APIs (reuse)

```text
scripts/live_path3_t0_switch_emitter.py
  switch_meta_for_asof(asof) -> flip / book / book_prev / sat_lead
  build_tagged_switch_order_rows(signal_date, delta_shares, prices) -> (-P3T0 rows, meta)
  maybe_emit_switch_orders(asof, prices, delta_shares=..., authorized=...) -> fail-closed unless flip+deltas

scripts/t0_carve_fin_sat_switch.py
  tag_order / authorize_same_bar_fill / CARVE_OUT_ID=T0_CARVE_FIN_SAT_SWITCH

scripts/live_fill_core.py
  same-bar MOC via reference_close when fill flag ON + carve tag
```

Emitter note (keep): do **not** silently invent Path3 qty from Soft alone — Stage A proxy must be **named** in meta (`engine_id`).

## Stage A method (pragmatic — implement this)

### Engine ID: `P3_SOFT_SLEEVE_EQ_RECON_PROXY`

On flip (`book_prev` → `book`):

1. Take live `pos`, `prices`, `nav` (e21 or sandbox copy).  
2. Freeze Soft sleeve **dollar notionals** from current holdings (Financial / Telecom / 0050).  
3. Build two synthetic share maps by reallocating those dollars via `allocate_sleeve_orders`:
   - **SAT dest** (`SAT_A20_RELAX`): `FIN_EQUAL` + `TEL_EQUAL` (RELAX ≈ Soft names without HARD overlays).  
   - **COMP dest** (`COMP_H150_x_A20`): keep **current** within-sleeve shares for Soft sleeves (proxy for "KD/HARD path already encoded in live tip"), or KD_OPT scores if panel cheap — **not** a full OR_K9/HARD150 rebuild.  
4. `delta_shares = dest_shares[book] − pos` (destination − current). Board-lot via existing emitter.  
5. Pass explicit `delta_shares` into `maybe_emit_switch_orders`.  
6. **Paper demo** (sandbox state dir under `repro/…`, never rewrite `forward/e21` history): force or use last flip asof with e21 prices → expect non-empty `-P3T0` → same-bar fill path. Soft-Frozen KEEP · broker false.

Probe on live e21 (2026-09-24): FIN equal-recon vs current pos already yields multi-lot deltas on `2880/2886/2892/5880` → demo non-empty is feasible.

### Wire points

| File | Change |
|---|---|
| `scripts/live_path3_t0_weight_engine.py` | **NEW** — `plan_delta_shares(...)` + `engine_id` |
| `scripts/e21_forward_pipeline.py` | replace `delta_shares=None` with weight-engine plan when emit ON |
| `tests/test_path3_t0_weight_engine.py` | **NEW** — flip→non-empty tagged rows; no-flip empty; Soft KEEP |
| `scripts/fin_sat_path3_weight_engine_stagea.py` | paper-demo harness → charter/screen/decision artifacts |
| `research/ops/*` | CHARTER / SCREEN / DECISION_PACK |

### Explicit non-goals (Stage A)

- Full COMP OR_K9×HARD150 / SAT paper NAV engine rebuild  
- Soft-Frozen clip / CONF α / L1 flip  
- Broker SendOrder · Path3 strategy cutover  
- Inventing untagged Soft orders as Path3 qty  
- Rewriting `forward/e21` history  

## Verdict ladder

| Verdict | Meaning |
|---|---|
| `PROXY_WIRED_DEMO_OK` | Named proxy wired · paper sandbox non-empty `-P3T0` · same-bar fill path green · Soft KEEP · broker false |
| `PROXY_EMPTY_LOT` | Wired but demo asof lot-filters to empty (need asof/seed fix) |
| `PROXY_NO_FLIP` | Demo asof not a flip (signal/meta bug) |
| `FULL_ENGINE_REQUIRED` | Proxy insufficient for next human gate — promote Stage B full engines |
| `BLOCK` | Would require Soft mutation / broker / cutover — refuse |

HIT for Stage A exit = **`PROXY_WIRED_DEMO_OK`**. Fidelity to paper COMP/SAT holdings is **out of scope**; Stage B owns that.

## Accept posture after HIT

Weight engine Stage A HIT → PREP/OPERATING note + optional DRAFT ballot to keep proxy in live pipeline (still cutover BLOCKED). Full-engine cutover remains a **separate** ballot.

## Reproduce (after implement)

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_path3_weight_engine_stagea.py
```

Label: `FIN_SAT_PATH3_WEIGHT_ENGINE_STAGEA_CHARTER_2026-09-29__PROXY_EQ_RECON__NO_BROKER`
