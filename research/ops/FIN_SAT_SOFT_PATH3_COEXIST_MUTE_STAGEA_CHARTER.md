# FIN_SAT_SOFT_PATH3_COEXIST_MUTE_STAGEA_CHARTER

Date: 2026-09-29  
Status: **Stage A CHARTER — Soft↔Path3 flip-day coexistence mute** · Soft-Frozen clips / Exact T+1 **KEEP** elsewhere · Path3 emit/fill **ON** (0ka7) · weight engine Stage B **ON** (0ka9) · broker **false** · cutover **BLOCKED**  
Parents: 0ka9 `FULL_ENGINE_BOTH_OK` · 0ka8 `PROXY_WIRED_DEMO_OK` · 0ka7 observe θ=0.005 + T+0 · 0k9r carve `T0_CARVE_FIN_SAT_SWITCH`  
Register: **0kaa**

## Question

On Path3 **flip** days, can e21 **mute Soft-Frozen sleeve rebalance orders** so they do not coexist with tagged `-P3T0` same-bar switch orders — without flipping Soft clips / CONF α / Exact T+1 globally, and without broker or Path3 strategy cutover?

## Why this is open

Today `e21_forward_pipeline` builds orders in this order:

1. Soft Exact T+1 — `build_live_order_rows` (FIN / TEL / 0050 sleeve gap → within-sleeve lots)  
2. Optional CONF_RET3 `00631L` satellite  
3. Path3 T0 — `plan_or_none_for_pipeline` → `maybe_emit_switch_orders` → append `-P3T0`

On flip days Stage B recon (`P3_COMP_SAT_ASOF_RECON_B`) already owns **FIN+TEL** share moves (demo: 6–7 names spanning Soft universe; **0050 KEEP** in Path3). Soft Exact T+1 on the same names creates:

| Conflict | Effect |
|---|---|
| Same-code dual intent | Soft T+1 lot + Path3 T0 lot on `2880/2886/…/2412/…` |
| Clock clash | Soft Exact **T+1** vs carve **same-bar MOC** (`T0_CARVE_FIN_SAT_SWITCH`) |
| Dest fight | Soft sleeve-gap toward Soft clips · Path3 dest toward COMP/SAT within-sleeve policy |

Carve policy (0k9r) said Soft Exact T+1 **KEEP elsewhere** — it did **not** define flip-day Soft mute. Weight-engine Stage A/B left this as the next gap.

## Binding findings (pre-registered)

| Fact | SSOT |
|---|---|
| Path3 flip + non-empty deltas → Soft universe codes | Stage B demo / probe: COMP→SAT @2026-06-12 · SAT→COMP @2026-05-20 · codes ⊆ FIN∪TEL |
| Path3 **0050 KEEP** | `live_path3_t0_weight_engine.py` |
| Soft still Exact T+1 outside carve | `e21_forward_pipeline` Exact T+1 audit · Soft rows untagged |
| Emit/fill/weight already ON | `LiveConfig.live_t0_carve_fin_sat_switch_{emit,fill}=True` · engine B wired |
| Broker / cutover still false / BLOCKED | register 0ka7–0ka9 |

## Stage A method (implement next)

### Mechanism ID: `SOFT_PATH3_FLIP_MUTE`

**Default policy candidate (Stage A):** `MUTE_SOFT_FIN_TEL`

When **all** of:

1. `live_soft_path3_coexist_mute` flag **ON** (default **OFF** until HIT + ACCEPT)  
2. Path3 emit flag ON  
3. `switch_meta_for_asof` → `flip=True`  
4. Weight engine returns non-empty `delta_shares` (or emitted `n_orders>0`)

Then:

- **Mute** Soft orders whose `code ∈ FIN ∪ TEL` (drop from Soft `order_rows` before Path3 append)  
- **KEEP** Soft **0050** Exact T+1 (Path3 does not move 0050)  
- **KEEP** CONF_RET3 / COOL / FUSE / FinPriv satellites (outside Path3 recon sleeve)  
- **KEEP** Path3 `-P3T0` path unchanged  
- Soft clips / CONF α=0.10 / Exact T+1 on non-flip days **unchanged**

### Policy ladder (compare in screen; pick one HIT)

| Policy ID | Mute scope on flip+Path3-hit |
|---|---|
| `MUTE_SOFT_FIN_TEL` | FIN+TEL Soft only · 0050 Soft KEEP (**default**) |
| `MUTE_SOFT_ALL_SLEEVES` | FIN+TEL+0050 Soft |
| `MUTE_OVERLAP_CODES` | Soft rows whose code ∈ Path3 `delta_shares` only |
| `MUTE_SOFT_ON_FLIP_META` | Mute FIN+TEL whenever `flip=True` even if Path3 empty (stricter fail-closed) |

### Wire points

| File | Change |
|---|---|
| `scripts/live_config.py` | NEW `live_soft_path3_coexist_mute: bool = False` + ballot string |
| `scripts/live_soft_path3_coexist_mute.py` | NEW — `should_mute(...)` + `filter_soft_orders(...)` |
| `scripts/e21_forward_pipeline.py` | After Soft build (and optional CONF_RET3): apply mute when Path3 will emit |
| `tests/test_soft_path3_coexist_mute.py` | NEW — flip+deltas → Soft FIN/TEL empty · non-flip Soft intact · 0050 KEEP · Path3 still tagged |
| `scripts/fin_sat_soft_path3_coexist_mute_stagea.py` | Paper demo harness → screen/decision |

### Demo plan (paper sandbox — no e21 history rewrite)

1. Load e21 `pos` / prices.  
2. Pick last COMP→SAT and SAT→COMP flips.  
3. Build Soft rows (or stub) + Path3 plan with mute OFF vs ON.  
4. Assert mute ON: Soft FIN/TEL count↓ · Path3 `-P3T0` count KEEP · 0050 Soft policy per chosen ladder · Exact T+1 audit still green for Soft remainder.  
5. Non-flip control: Soft rows unchanged.

## Non-goals

- Broker SendOrder · Path3 strategy cutover  
- Soft clip / CONF α densify / L1 flip  
- Expanding T+0 carve beyond `T0_CARVE_FIN_SAT_SWITCH`  
- Muting COOL / FUSE / CONF_RET3 / FinPriv on flip days  
- Cloning paper COMP/SAT share ledgers  
- Rewriting `forward/e21` history

## Verdict ladder

| Verdict | Meaning |
|---|---|
| `MUTE_WIRED_DEMO_OK` | Flag+filter wired · flip demo Soft FIN/TEL muted · Path3 `-P3T0` intact · non-flip Soft KEEP · Soft clips KEEP · broker false |
| `MUTE_NO_FLIP` | Demo asof not a flip |
| `MUTE_SOFT_ALREADY_EMPTY` | Soft had nothing to mute (inconclusive) |
| `MUTE_PATH3_REGRESSED` | Mute accidentally emptied / broke Path3 tags |
| `POLICY_AMBIGUOUS` | Ladder policies disagree on HIT — need human pick |
| `BLOCK` | Would require Soft clip / broker / cutover — refuse |

HIT for Stage A exit = **`MUTE_WIRED_DEMO_OK`** under default `MUTE_SOFT_FIN_TEL`.

## Accept posture after HIT

Stage A HIT → DRAFT ballot to flip `live_soft_path3_coexist_mute=True` (still cutover BLOCKED · broker false). Live wire only via dedicated ACCEPT line.

## Label

`FIN_SAT_SOFT_PATH3_COEXIST_MUTE_STAGEA_CHARTER_2026-09-29__MUTE_SOFT_FIN_TEL__NO_BROKER`
