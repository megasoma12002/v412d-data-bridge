# E45 Multi-Event Stress-Year Threshold Charter

Generated: `2026-09-06T04:26:26.694796+00:00`
Status: **PAPER GOVERNANCE RULE** — does not flip Soft-Frozen / DEFAULT / stitch

## Rule (binding for future paper ballots)

A challenger **qualifies** for a dedicated OPEN-observe ballot only if **all** hold:

1. **Multi-event:** MDD help > **0.25 pp** vs BASE in **≥ 2** distinct years among {2015, 2018, 2020, 2022}.
2. **Held-out score > 0** on `heldout_2019_plus` (score = MDD improve pp − 0.5·|CAGR giveback pp|).
3. **Sealed score > −1.0** on `sealed_2023_plus` (no catastrophic sealed giveback).

Rationale: block **2020-only** products from looking like general crisis protection.

## Scores (this batch)

| Book | Years helped | N | Multi≥2 | Held-out score | Sealed score | Qualifies? |
|---|---|---:|:---:|---:|---:|:---:|
| `BLEND_E45_A05` | [2020] | 1 | N | +0.22 | +2.07 | **NO** |
| `BLEND_E45_A25` | [2018, 2020] | 2 | Y | -0.91 | +2.59 | **NO** |
| `CHAL_E45_E3` | [2015, 2018, 2020, 2022] | 4 | Y | -1.00 | +0.03 | **NO** |
| `FIN_ONLY_A05` | [2020] | 1 | N | +0.26 | +1.79 | **NO** |
| `FIN_ONLY_A10` | [2020] | 1 | N | +0.29 | +2.52 | **NO** |
| `HIGH_BETA_A05` | [2020] | 1 | N | +0.23 | +1.95 | **NO** |
| `HIGH_BETA_A10` | [2020] | 1 | N | +0.20 | +2.54 | **NO** |
| `HIGH_BETA_A15` | [2018, 2020] | 2 | Y | -0.20 | +2.70 | **NO** |

**Qualifiers this batch:** _none_

## Non-goals

- Not a live stitch gate (stitch still needs second human ACCEPT + clean trailing).
- Not a Soft-Frozen / DEFAULT flip.
- Does not invent a replacement for the retired MDD narrative (`RETIRED_HISTORICAL_NARRATIVE`).

Label: `E45_MULTI_EVENT_THRESHOLD_2026-09-06__STITCH_FORBIDDEN`
