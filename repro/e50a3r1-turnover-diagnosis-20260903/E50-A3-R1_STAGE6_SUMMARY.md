# Stage-6 Research Summary — Raise Profit / Cut MDD

Draft only. **No retune. No E45 edit. No promotion. PR #19 stays draft.**

## Question

How to increase profitability and reduce MDD under causal E50-A3-R1 rules?

## Approach

Alpha (TECH2 + C4 names) frozen. New hypothesis class: **sleeve exposure / cash buffer overlays** (not another TECH2 tilt; not in-place E45).

Utility = `CAGR - 0.5*|MDD|`. Gates EXPERIMENTAL: turn ≤2.5%, boot ≥0.70. OOF-only selection.

## 6A — Aggressive overlays

**Decision: `OOF_NO_NEW_RISK_OVERLAY_DUAL_GATE_WINNER`**

| Overlay | OOF CAGR | OOF MDD | Utility | Boot | Both |
|---|---:|---:|---:|---:|---|
| BASE_FULL | 10.56% | −30.24% | −0.0456 | 0.807 | True |
| STATIC_070 | 8.11% | −21.94% | −0.0287 | 0.525 | False |
| STATIC_050 | 5.87% | −16.02% | −0.0214 | 0.258 | False |
| REGIME_OFF_050 | 7.33% | −16.41% | −0.0087 | 0.426 | False |

MDD/utility improve, but **market-proxy bootstrap collapses** (cash underperforms bullish OOF path).

## 6B — Mild overlays

**Decision: `OOF_NEW_MILD_OVERLAY_UTILITY_WINNER` → lock R6B1 = STATIC_085**

| Overlay | OOF CAGR | OOF MDD | Utility | Boot | Both |
|---|---:|---:|---:|---:|---|
| BASE_FULL | 10.56% | −30.24% | −0.0456 | 0.807 | True |
| **STATIC_085** | 9.74% | **−26.21%** | **−0.0337** | 0.729 | True |
| STATIC_090 | 10.12% | −27.59% | −0.0368 | 0.766 | True |
| STATIC_095 | 10.37% | −28.96% | −0.0411 | 0.788 | True |

## R6B1 held-out (one shot)

**Decision: `MIXED_HELDOUT`**

| | R6B1 Val | C4 Full Val | R6B1 Sealed | C4 Full Sealed |
|---|---:|---:|---:|---:|
| CAGR | 18.73% | 21.65% | (strong) | (strong) |
| MDD | **−27.57%** | −31.87% | **−18.04%** | −20.99% |
| Bootstrap | **0.374 FAIL** | 0.559 FAIL | 0.992 PASS | 0.998 PASS |

MDD improves on both windows; val CAGR slips under 20%; val bootstrap gets **worse**. Do not retune.

## Answer to “如何增加獲利然後減低 MDD”

Under current experimental dual gates:

1. **Cutting MDD via cash/exposure works mechanically** (OOF and held-out MDD fall).
2. **It trades away CAGR and vs-proxy bootstrap** — aggressive cuts fail OOF boot; mild 0.85 helps OOF utility but still `MIXED_HELDOUT`.
3. **Alpha packing (Stages 1–5) does not fix 2021–22 MDD/bootstrap**; risk overlays help MDD but do not deliver PASS_HELDOUT.
4. Path closer to **both** higher profit and ~10–15% MDD likely needs a **separate crisis/risk budget layer** (E45-class challenger with higher process bar), not more TECH2 tilts or a static 0.85 sleeve alone — and still must clear OOF then one held-out without gate promotion.

Artifacts: `E50-A3-R1_STAGE6_RISK_OVERLAY_OOF.md`, `E50-A3-R1_STAGE6B_MILD_OVERLAY_OOF.md`, `E50-A3-R1_STAGE6B_R6B1_HELDOUT.md`
