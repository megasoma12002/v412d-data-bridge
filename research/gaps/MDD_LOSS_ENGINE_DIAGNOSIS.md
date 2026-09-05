# MDD Loss-Engine Diagnosis (E22_v2s formal)

Generated: `2026-09-05T01:07:00.165602+00:00`
Status: **RESEARCH_ONLY** — no live-wire, no Soft-Frozen edit.

## Overall gap

| Metric | Value | vs target |
|---|---:|---|
| CAGR | 13.78% | target ≥20% → **-6.2 pp** |
| MDD | -22.64% | target ≤15% depth → **-7.6 pp** (neg=deeper) |
| Mean tgt Financial | 79.8% | structural concentration |
| Mean E45 equity scale | 1.000 | existing crisis scaler |

## Top drawdown episodes (≥8% depth)

| Peak | Trough | Depth | Mean fin | Mean eq | Mean E45 | Crisis share |
|---|---|---:|---:|---:|---:|---:|
| 2020-01-20 | 2020-03-19 | -22.6% | 84.7% | 99.1% | 1.000 | 13.9% |
| 2015-04-28 | 2016-01-21 | -17.4% | 68.9% | 99.6% | 1.000 | 48.9% |
| 2022-04-13 | 2022-10-19 | -16.7% | 66.3% | 99.7% | 1.000 | 66.7% |
| 2026-02-26 | 2026-05-27 | -14.5% | 72.5% | 99.4% | 1.000 | 32.8% |
| 2025-03-27 | 2025-04-07 | -9.2% | 70.3% | 100.0% | 1.000 | 33.3% |

## Regime conditional (daily)

| Regime | N | Mean ret | Mean fin | Mean eq | Mean E45 |
|---|---:|---:|---:|---:|---:|
| Bear | 381 | -0.00018 | 72.1% | 99.6% | 1.000 |
| Bull | 2442 | 0.00082 | 83.6% | 99.4% | 1.000 |
| Crisis | 423 | -0.00050 | 64.1% | 99.7% | 1.000 |
| Sideways | 104 | 0.00099 | 82.1% | 99.2% | 1.000 |

## Finance × Crisis (descriptive)

- Crisis days: **423**
- Crisis & fin≥80%: n=4, mean ret=-0.008231600486883525
- Crisis & fin≤60%: n=86, mean ret=0.0005572666800745615

## Proxy overlays (NOT Exact T+1 — hypothesis only)

| Proxy | CAGR | MDD | MDD Δpp vs base | CAGR giveback pp |
|---|---:|---:|---:|---:|
| PROXY_CRISIS_EQ_SCALE_70 | 14.45% | -18.88% | +3.76 | -0.67 |
| PROXY_CRISIS_EQ_SCALE_50 | 14.87% | -16.29% | +6.34 | -1.09 |
| PROXY_CRISIS_EQ_SCALE_30 | 15.28% | -14.86% | +7.78 | -1.50 |

## Implications for L1 charter

1. Core MDD will not hit ≤15% via Stage-8 TECH2 remix or Track B S1 cut retune (both closed).
2. FIN_CAP_50 helps ~3pp but leaves ~−19.6% held MDD — need **additional** crisis/exposure loss engine.
3. Proxy crisis equity scales that improve MDD must be rebuilt as Exact T+1 challengers with frozen OOF→held-out gates.
4. Keep BASE_E16 / E22_v2s ledgers; any promote is cutover-only dual paper books.

See charter: `research/gaps/MDD_LOSS_ENGINE_CHARTER.md`
