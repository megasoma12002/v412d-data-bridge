# E50-A3-S1 Track B — Held-out

Date: 2026-09-05  
Locked (no retune): `S1-QRES` / `COMBO_VOL80_VAL00` / C4 shell / `SWITCH_S1_BOOK`  
Prior step: `ADV_LITE_PASS_READY_FOR_HELDOUT` (placebo util P≈0.25)

## Decision

| Field | Value |
|---|---|
| Label | `FAIL_HELDOUT` |
| Research decision | **`STOP_S1_HELDOUT_KEEP_TRACK_A`** |
| Replace Track A paper monitor? | **No** |
| Live wire? | **No** |
| Cut retune? | **Forbidden** (charter) |

## Windows

| Window | CAGR | MDD | TO | Boot | Stress ex | vs C4 stress | dual-gate |
|---|---:|---:|---:|---:|---:|---|---|
| val 2019–2022 | 17.3% | −29.7% | 2.07% | **0.334** | −0.000140 | **False** | **False** |
| sealed 2023–2026-08-28 | 42.2% | −31.8% | 1.95% | 0.965 | −0.000753 | **False** | True |

REF_C4 stress mean excess: val **+0.000362**, sealed **+0.001837**.  
S1 stress mean excess is **negative** on both held-out windows and worse than C4.

## Why FAIL (not MIXED)

Predeclared pass needs **both** windows: dual-gate (TO≤2.5% + boot≥0.70 EXPERIMENTAL) **and** stress mean excess ≥ REF_C4.

- Val fails bootstrap (0.334 ≪ 0.70) and fails stress vs C4.
- Sealed clears dual-gate but **still loses stress vs C4**.
- Both windows fail the full held-out rule → `FAIL_HELDOUT`.

OOF dual-gate + adv-lite did **not** transfer: residual quality book under COMBO_VOL80_VAL00 does not deliver held-out stress edge.

## Artifacts

- Decision JSON: `research/e50a/E50A_S1_HELDOUT_DECISION.json`
- Repro: `repro/e50a-dual-track/track_b_s1_heldout/`
- Harness: `scripts/e50a_s1_heldout.py`

## Aftermath

- **Keep Track A** S9A1 paper/monitor (`MIXED_HELDOUT` archive).
- **Stop S1 residual axis** — no cut retune, no detector re-grid on this family.
- Live remains **E16 + E18 + E22_v2s cutover-only**; no overlay.
- Next research focus (outside this axis): optional **FIN_CAP_50** promote (PR #39), or a **new MDD / loss-engine** charter — not Stage-8 TECH2 remix.
