# TIPSOFT_IP3_FILL_LOCK_STAGEA_SCREEN

Date: 2026-10-01 · Register: **0kb7** · Verdict: **`FILL_LOCK_BLOCK`**

Gate: `MUTE_S3_SAT_W63_T-0.01` · Path3-ON **9.8336%**

Tip Soft Soft-refill ceiling vs L4: held **+0.6702** · tipY **+3.1878** (FORBIDDEN)

| Arm | clock | held | tipY | sealedMDD | feasible | Soft FIN/TEL |
|---|---|---:|---:|---:|---|---|
| `TIP_L4_ALWAYS_WITHIN` | tipsoft_exact_t1 | -0.0 | -0.0 | 0.0 | Y | N |
| `TIP_CEIL_SOFT_REFILL_MUTE` | tipsoft_exact_t1 | 0.6702 | 3.1878 | 0.4503 | N | Y |
| `TIP_CEIL_OVERRIDE` | tipsoft_exact_t1 | 0.7661 | 3.1878 | 0.4503 | N | Y |
| `SC_MUTE_ALWAYS_WITHIN` | softcore_t0 | -0.0 | -0.0 | 0.0 | Y | N |
| `SC_MUTE_FREEZE` | softcore_t0 | -4.8107 | -6.7744 | -8.9413 | Y | N |
| `SC_MUTE_FT_TO_0050` | softcore_t0 | -7.0884 | 63.4817 | -63.9128 | Y | N |
| `SC_MUTE_FT_TO_CASH` | softcore_t0 | -10.7035 | -36.5872 | 2.6541 | Y | N |
| `SC_MUTE_SOFT_REFILL_DIAG` | softcore_t0 | -5.4606 | -8.7749 | -5.7713 | N | Y |
| `SC_NEAR_ALWAYS_WITHIN` | softcore_t0 | -0.0 | -0.0 | 0.0 | Y | N |
| `SC_NEAR_FREEZE` | softcore_t0 | -4.8536 | -6.7512 | -8.9911 | Y | N |
| `SC_NEAR_FT_TO_0050` | softcore_t0 | -7.0884 | 63.4817 | -63.9128 | Y | N |
| `SC_NEAR_FT_TO_CASH` | softcore_t0 | -10.8708 | -36.3653 | 2.457 | Y | N |
| `SC_NEAR_SOFT_REFILL_DIAG` | softcore_t0 | -5.4837 | -8.7627 | -5.7952 | N | Y |

## Optimize live

1. Question: which Path3 OFF-day FIN∪TEL fill unlocks ACCEPT under Soft FIN/TEL OFF?
2. Verdict `FILL_LOCK_BLOCK`: tip Soft Soft-refill ceiling vs L4 held **+0.6702** tipY **+3.1878** (FORBIDDEN under WITHIN KEEP)
3. Gate MUTE_S3_SAT Path3-ON only **9.8336%** (NEARPEAK3 **9.8633%**) — OFF ≈90%
4. Soft-core MUTE×FREEZE vs ALWAYS_WITHIN held **-4.8107** tipY **-6.7744** sealedMDD **-8.9413** · off **90.1459%**
5. Soft-core MUTE×FT→0050 held **-7.0884** tipY **63.4817** sealedMDD **-63.9128**
6. Soft-core MUTE×FT→CASH held **-10.7035** tipY **-36.5872** sealedMDD **2.6541**
7. Best feasible Soft-core fill: none — freeze/0050/cash all lose held vs ALWAYS_WITHIN
8. Lock: tip Soft tipY needs Soft FIN/TEL refill on OFF days; non-Soft fills under ~90% OFF destroy Soft-core held
9. Disposition: KEEP stamps · **no ACCEPT apply** — fill lock not cleared without Soft FIN/TEL
10. Soft KEEP · Path4 OFF · broker false · Soft FIN/TEL stay OFF · no live wire

Label: `TIPSOFT_IP3_FILL_LOCK_STAGEA_SCREEN_2026-10-01__FILL_LOCK_BLOCK`
