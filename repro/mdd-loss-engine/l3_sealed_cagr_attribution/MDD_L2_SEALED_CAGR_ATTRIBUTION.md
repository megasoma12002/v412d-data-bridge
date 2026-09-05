# L2 Sealed CAGR Attribution (for L3 charter)

Generated: `2026-09-05T02:11:39.639380+00:00`
Parent lock (frozen): `L2_FINCAP_ONLY` → `STOP_L2_HELDOUT_MIXED_KEEP_BASE`
Status: **RESEARCH_ONLY** — explains sealed CAGR giveback; does not reopen L2 cuts.

## Held-out sealed deltas (recomputed)

- Sealed CAGR giveback: **4.33 pp** (gate ≤3.0) → FAIL
- Sealed MDD improve: **4.41 pp**

## Mechanism

L2_FINCAP_ONLY has **no gross equity scale** and **no COMBO flag**. Giveback is from Financial hard clip `[0.35, 0.50]` vs BASE Soft-Frozen path (sealed mean Financial **78.9%** → **50.0%**).

Note: Equal-weight sleeve Δret is diagnostic only; authoritative metric is Exact T+1 NAV CAGR giveback. Proxy total can disagree with NAV because books use name-level fills.

## Sealed mean sleeve weights

| Sleeve | BASE | L2 FIN50 | Δ |
|---|---:|---:|---:|
| Financial | 78.9% | 50.0% | -28.9% |
| Telecom | 11.7% | 23.9% | +12.2% |
| 0050 | 9.4% | 26.1% | +16.7% |

## Sealed by year (NAV — authoritative)

| Year | BASE CAGR | L2 CAGR | Giveback pp | MDD Δpp |
|---:|---:|---:|---:|---:|
| 2023 | 7.48% | 11.34% | -3.86 | +0.67 |
| 2024 | 22.31% | 17.45% | +4.86 | -1.63 |
| 2025 | 19.19% | 14.00% | +5.18 | +0.27 |
| 2026 | 68.27% | 51.54% | +16.73 | +6.86 |

## Implications for L3

1. Failure mode ≠ L1: L1 was COMBO timing over-fire; L2 is **static FIN concentration**.
2. Giveback concentrated in **2024 / 2025 / 2026**; 2023 L2 beat BASE on CAGR.
3. L3 targets sealed CAGR retention with MDD ≥ +1 pp — without retuning L1 or reopening L2 lock.
4. Soft-Frozen live clip stays **[0.50, 0.95]**; FIN_CAP_50 dual-paper month-end continues.

See charter: `research/gaps/MDD_L3_SEALED_CAGR_CHARTER.md`
