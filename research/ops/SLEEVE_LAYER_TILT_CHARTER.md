# Sleeve-Layer Tilt — Research Charter (paper)

Date: 2026-09-10  
Status: **OPEN / PAPER ONLY**  
Human: **「直接起草 sleeve-layer tilt 的 research charter」**（建議順序②；Soft-assist observe 繼續跑月結）  
Prior paper seed: **`SLEEVE_BELOW_MA60_a01`** tip-clean beat-live in `KD_SOFT_TEL_SLEEVE_RESEARCH_SCREEN.md`  
Soft-Frozen **clips KEEP** · live **KD_OPT KEEP** · **TEL_EQUAL KEEP** · E45 stitch **OFF** · Soft-assist observe **UNCHANGED** (separate track)

## Question

Does a **sleeve-layer score tilt** on the Soft-Frozen router (boost/dampen Financial / Telecom / 0050 from **sleeve NAV indicators**, then Soft-Frozen clip + blend) tip-clean beat or coexist with **`LIVE_STACK`**, without changing within-sleeve KD/TEL policies or Soft-Frozen clip bounds?

**Not in scope:** Soft-assist name scores · KD season retune · TEL within-sleeve alloc · Soft-Frozen Class D clip flip · dry-powder cash reserve · E45 stitch.

## Why this charter (separate ask)

| Item | Note |
|---|---|
| Prior screen | Track C of soft/TEL/sleeve research: **7** sleeve beat-live books; best **`SLEEVE_BELOW_MA60_a01`** (held ≈0.615 · vs live Δ ≈+0.074 · tip PASS/PASS) |
| Soft-assist ballot | Explicitly **excluded** sleeve tilt (`SOFT_ASSIST_PROMOTE_BALLOT_OPEN.md` non-choice) |
| Soft-Frozen | Clips stay **[0.60, 0.90] / TEL / 0050** — tilt moves **score → cand**, not the box |
| Distinct actuator | Changes **sleeve weights** via router score; Soft-assist changes **within-FIN name scores** |

## Live baseline (do not modify)

| Layer | Live |
|---|---|
| Soft-Frozen | FINBAND **[0.60, 0.90]** · TEL **[0.03, 0.35]** · 0050 **[0.00, 0.35]** |
| FIN within-sleeve | **`KD_OPT`** (`KD_APR15_MAY15_Klt30_T15`) |
| TEL / 0050 | EQUAL |
| Books / capital / lot | `E22_v2s_tw` · 500M · board-lot 1000 |
| E45 | stitch **OFF** |
| Soft-assist | dual-paper observe **OPERATING** — do not wire or pause from this charter |

Paper challenger = **same live within-sleeve** + **tilted Soft-Frozen target schedule**. Report **full / heldout_2019_plus / sealed_2023_plus** CAGR+MDD and tip YTD+1y vs live.

## Mechanism (paper)

### Router score tilt

1. Build sleeve returns `Financial` / `Telecom` / `0050` (same as Soft-Frozen base).  
2. Causal sleeve signal `s_{t,sleeve} ∈ {0,1}` from lagged sleeve NAV (e.g. close &lt; MA60).  
3. `score' = score_soft_frozen + sign · α · s` (clip score inputs as in Soft-Frozen router).  
4. Rebuild daily targets: regime prior + score → **`apply_soft_frozen_clips`** → blend/`REBALANCE_L1_MIN` (same loop as `rebuild_targets_from_score` in `e16_kd_soft_tel_sleeve_research.py`).  
5. Simulate with `sleeve_weight_schedule` / rebuilt `target`, **`KD_OPT` + `TEL_EQUAL`** unchanged.

### Sign convention

| Signal family | Default sign | Intent |
|---|---|---|
| `SLEEVE_BELOW_MA60` · `SLEEVE_RSI14_LT30` · `SLEEVE_MOM20_NEG` | **+1** | Oversold / below-trend → **boost** that sleeve’s router score |
| `SLEEVE_ABOVE_MA60` · `SLEEVE_RSI14_GT70` · `SLEEVE_MOM20_POS` | **−1** | Overbought / above-trend → **dampen** |

## Finite Stage A screen

Confirm prior seed under **live-stack scoring** (not only vs `FIN_EQUAL`); keep book count small.

1. Baseline: **`LIVE_STACK`**.  
2. Seed champion: **`SLEEVE_BELOW_MA60_a01`** (α=0.10, sign=+1).  
3. Finite grid (cap **≤ ~24** challengers):

| Axis | Values |
|---|---|
| Signal | `BELOW_MA60` (required) · `RSI14_LT30` · `MOM20_NEG` · optional `BELOW_MA40` / `BELOW_MA120` sensitivity |
| α | **0.05 · 0.10 · 0.15 · 0.20** |
| Sign | default table above; no free sign search in Stage A |

4. Metrics: full / heldout / sealed CAGR+MDD; tip YTD+1y vs live; held-out score vs live.  
5. Verdict labels: `NO_LIFT` · `COEXIST_NO_LIFT` · `NEAR_NO_BEAT` · `BEATS_LIVE`.

Prior Track C numbers are **hypothesis only** — Stage A must re-score vs current `LIVE_STACK` and report sealed.

## Gates

| Gate | Rule |
|---|---|
| Tip | YTD + trailing 1y vs live: PASS (ALERT 3pp / PAUSE 5pp giveback) |
| Coexist | tip-clean **and** held-out score > 0 vs live |
| Beat-live | coexist **and** held-out score Δ > 0 vs live self |
| Sealed | report-only for Stage A (do not require sealed beat to OPEN observe) |

## Success → next step

If Stage A tip-clean beat-live or strong coexist → draft **OPEN observe** ballot (dual-paper `LIVE_STACK` ∥ champion sleeve tilt).  
Else → **STOP / archive**; keep Soft-Frozen router live unchanged.

**Observe cutover** (later) would still need a dedicated ACCEPT — Stage A green ≠ live wire.

## Artifacts (to create in Stage A)

| Role | Path |
|---|---|
| Charter | `research/ops/SLEEVE_LAYER_TILT_CHARTER.md` (this file) |
| Screen script | `scripts/e16_sleeve_layer_tilt_screen.py` (**not yet**) |
| Results | `research/ops/SLEEVE_LAYER_TILT_SCREEN.md` (+ `.json`) |
| Repro | `repro/sleeve-layer-tilt/` |

## Non-actions

- No Soft-Frozen clip bound flip  
- No live KD_OPT / TEL change  
- No Soft-assist live wire or observe pause  
- No auto-combine Soft-assist + sleeve tilt (needs new ballot after both coexist)  
- No E45 stitch  
- No re-open TEL within-sleeve / dry-powder / hard-indicator assists from this charter  

## Out of scope

- Cross product Soft-assist × sleeve tilt in Stage A  
- Searching Soft-Frozen lo/hi bounds  
- Name-level indicators inside FIN/TEL (covered elsewhere)

## Label

`SLEEVE_LAYER_TILT_CHARTER_2026-09-10__PAPER_ONLY__SEED_BELOW_MA60_a01__LIVE_KEEP`
