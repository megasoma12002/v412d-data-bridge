# E45 M2 — Frozen DEF Sleeve + Relocate Rule v0 (BEFORE any sealed metrics)

Date: 2026-09-06  
Status: **FROZEN FOR PAPER SCREEN** — Soft-Frozen **KEEP** · DEFAULT **KEEP** · stitch **FORBIDDEN**  
Parent: `E45_NEW_MECHANISM_CHARTER.md` (M2 actuator stage)  
Sensor input: `E45_M1_STATE_VECTOR_V0_FROZEN.md` intensity `s_t` (lag-1) — M1 §2 FAIL does **not** block M2  
Claimed MDD narrative: **`RETIRED_HISTORICAL_NARRATIVE`** — do not invent a replacement

## Honesty bound

`forward/e21/live_market.csv` has **no** cash ETF / short-duration / gov-bond proxy.  
v0 therefore cannot claim a true risk-free or duration hedge.

| DEF destination | What it is | Honesty limit |
|---|---|---|
| `DEF_TEL` | Soft-Frozen **Telecom** sleeve `{2412,3045,4904}` | Defensive **equity** proxy only — still equity beta |
| `DEF_CASH0` | Uninvested cash residual @ **0%** yield | Economically ≡ equity-shrink; control ablation, not a hedge edge |

Primary challenger destination: **`DEF_TEL`**.  
`DEF_CASH0` is the shrink-control twin (must not be sold as “cash carry”).

## Intensity (frozen, from M1)

Use M1 equal-weight intensity `s_t` exactly as frozen in `E45_M1_STATE_VECTOR_V0_FROZEN.md`.  
Actuator lag: **`u_t = c · s_{t-1}`**, `c ∈ {0.50, 0.75}`, `u_t` clipped to `[0,1]`.

Do **not** retune M1 features inside this pack.

## Soft-Frozen base sleeve weights

Daily Soft-Frozen targets `w = (w_FIN, w_TEL, w_0050)` from E16 early-stack (unchanged).  
Modes rewrite targets only; Exact T+1 fills / E22 books / cost-× unchanged.

## Modes (frozen)

### (a) `SHRINK` — equity-shrink-only (E45-like actuator)

```
w_i' = w_i · (1 − u_t)   for i ∈ {FIN, TEL, 0050}
```

Residual `1 − Σ w'` stays **cash @ 0%** (`DEF_CASH0`).

### (b) `RELOC_TEL` — relocate-to-DEF (primary M2)

```
move_FIN  = w_FIN  · u_t
move_0050 = w_0050 · u_t
w_FIN'  = w_FIN  − move_FIN
w_0050' = w_0050 − move_0050
w_TEL'  = w_TEL  + move_FIN + move_0050
```

Fully invested in equities; no cash residual from the overlay.  
Sources: FIN + 0050 only (leave baseline TEL untouched except as destination).

### (c) `HYBRID_TEL` — 50/50 shrink + relocate

```
w_i^s = w_i · (1 − 0.5·u_t)           # all sleeves
move_FIN  = w_FIN  · 0.5·u_t
move_0050 = w_0050 · 0.5·u_t
w_FIN'  = w_FIN^s  − move_FIN
w_0050' = w_0050^s − move_0050
w_TEL'  = w_TEL^s  + move_FIN + move_0050
```

## Book IDs

| Book | Mode | `c` |
|---|---|---|
| `M2_SHRINK_C50` | SHRINK | 0.50 |
| `M2_SHRINK_C75` | SHRINK | 0.75 |
| `M2_RELOC_TEL_C50` | RELOC_TEL | 0.50 |
| `M2_RELOC_TEL_C75` | RELOC_TEL | 0.75 |
| `M2_HYBRID_TEL_C50` | HYBRID_TEL | 0.50 |
| `M2_HYBRID_TEL_C75` | HYBRID_TEL | 0.75 |

## References (always run)

- `BASE_E16_E18_E22_v2s`
- `BLEND_E45_A05`
- `SLEEVE_FIN_ONLY_A10` (observe OPERATING id — reference only)
- Best M1 shrink peer `M1_EQW_C75` (optional cross-ref; not retuned)

## Explicit non-actions

- Do **not** open Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballots
- Do **not** densify E45 mild-α as a substitute for M2
- Do **not** treat `DEF_TEL` as cash or duration hedge
- Do **not** invent RF carry on cash without a dated data ingest + new freeze
- Do **not** change these formulas after seeing sealed scores (amendment = new `v1` freeze)

## Qualification

Inherit charter §2 rules 1–6.  
**M2 pass (unlock M3):** best `RELOC_TEL` / `HYBRID_TEL` beats matched `SHRINK` on COVID-ex held-out score **and** meets §2 rule 4 **or** 5; else publish autopsy (DEF proxy too weak / actuator insufficient).

Label: `E45_M2_DEF_SLEEVE_V0_FROZEN_2026-09-06__PAPER_ONLY__STITCH_FORBIDDEN`
