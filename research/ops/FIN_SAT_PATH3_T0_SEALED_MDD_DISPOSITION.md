# P3_T0_STATE — sealed MDD delta disposition

Date: 2026-09-28  
Status: **HUMAN DISPOSITION** · observe KEEP · cutover still **BLOCKED** · no live  
Register: 0k9r

## Human

> sealed MDD 已比 base 差约 −0.17pp 這個數值可接受 因為sealed的mdd數值比full held小很多

## Numbers (asof 2026-09-24)

| Window | base MDD | chal MDD | Δ pp |
|---|---:|---:|---:|
| full / heldout | −14.42% | −14.32% | **+0.10** (better) |
| sealed 2023+ | −6.20% | −6.37% | **−0.17** (worse) |

Absolute sealed |MDD| ≈ 6.2–6.4% ≪ full/held ≈ 14.3–14.4%.

## Effect

- Month-end alert `sealed_2023_plus MDD worse than CTRL` marked **ACCEPTABLE** for observe continuation
- Cutover checklist gate item “sealed MDD alert reviewed” → **YES** (disposition only)
- Does **not** authorize live cutover · Soft-Frozen KEEP · carve-out narrow KEEP

Label: `FIN_SAT_PATH3_T0_SEALED_MDD_DISPOSITION_2026-09-28__ACCEPTABLE__NO_LIVE`
