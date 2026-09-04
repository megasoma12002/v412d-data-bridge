# Stage-7 Research Summary — Crisis Challenger

Draft only. **No E45 edit. No promotion. No held-out (no true crisis-profit winner). PR #19 stays draft.**

## Goal

User target: high profit, low risk, responsive trading, **good results in crashes**.

Stage-7 tests sleeve crisis controllers on frozen TECH2+C4 (not in-place E45).

## 7A — Vote≥2 crisis (13.8% of OOF days)

**Decision: `OOF_NO_NEW_CRISIS_CHALLENGER_DUAL_GATE_WINNER`**

| Finding | Detail |
|---|---|
| BASE_FULL crisis excess | Already **positive** on OOF under this def |
| Cash 0–50% in crisis | Fail bootstrap; utility worse |
| Defensive sleeve switch | Crisis compound turns **negative**; fail boot |
| Crisis-triggered rebalance | Makes crisis excess worse |

## 7B — Strict crisis (DD≤−15% or votes≥3; 12.1% days)

**Decision: `OOF_NO_NEW_STRICT_CRISIS_CHALLENGER_DUAL_GATE_WINNER`** (corrected)

| Challenger | Dual gate | Utility vs base | Crisis compound vs base |
|---|---|---|---|
| STRICT_CASH_090…070 | PASS | better | **worse** |
| STRICT_SLEEVE_DEF | FAIL | worse | worse |

Mild crisis cash helps overall utility/MDD (same pattern as Stage-6) but **does not improve crisis-period profitability** vs BASE_FULL when baseline crisis excess is already positive. Not locked / not held-out.

## Implication for “股災也還有好獲利”

1. On **OOF 2011–2018** with these market crisis defs, full-invest C4 already has positive crisis excess — cash/defensive overlays don’t beat it on crisis PnL while clearing gates.  
2. The painful failure remains **held-out 2021–2022**, which must not be used for selection.  
3. Sleeve cash is a **MDD tool**, not a **crisis-alpha tool**.  
4. True “crash profit” likely needs a **different return engine in stress** (separate long-defensive or relative-value sleeve with its own OOF proof), or an E45-class challenger with a higher process bar — still without editing frozen E45 in place.

Artifacts: `E50-A3-R1_STAGE7_CRISIS_CHALLENGER_OOF.md`, `E50-A3-R1_STAGE7B_STRICT_CRISIS_OOF.md`
