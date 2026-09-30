# TIPSOFT_IP3_T0_GAP_ATTRIB_STAGEA_SCREEN

Date: 2026-09-30 · Verdict: **`T0_NOT_DRIVER`**
Register: **0kb5** · live base = L3_LIVE_FUSE_COOL (Exact T+1)

## Arms vs L3 (research − live; + = research ahead)

| Arm | clock | heldΔ | sealedMDDΔ | tipY | ahead? |
|---|---|---:|---:|---:|---|
| L3_LIVE_FUSE_COOL | exact_t1 | -0.0 | 0.0 | -0.0 | False |
| L4_LIVE_P3_WITHIN | exact_t1 | 0.8475 | -0.5026 | 2.8524 | True |
| P3_THETA_NEARPEAK3 | exact_t1 | 1.4473 | -0.0434 | 5.6789 | True |
| OVERRIDE_LIVE_W42_M05_K3 | exact_t1 | 1.6136 | -0.0523 | 6.0402 | True |
| R0_T0_P3_WITHIN | exact_t0 | -2.5148 | -7.028 | 1.923 | False |
| HYBRID_P3_NEARPEAK3 | hybrid_t1_overlay_t0_carve | -2.2498 | -3.0616 | -5.7831 | False |

## Same-clock residual

- OVERRIDE vs L4_P3_WITHIN held **0.7661** · tipY **3.1878**

## Live T+0 flags (context)

- Path3 cutover WITHIN: **ON** · T0 carve fill/emit: **ON**
- Live has narrow Path3 T+0 carve ON, but tip Soft research books (NEARPEAK3 / LIVE_OVERRIDE) are Exact T+1 twins vs L3; gap vs L3 is stack alpha on same clock.

## Optimize / disposition

1. Question: does T+0 cause live to lag tip Soft research?
2. Verdict `T0_NOT_DRIVER`: tip Soft Exact T+1 OVERRIDE held vs L3 **+1.6136** tipY **+6.0402** (same clock as live Soft+FUSE+COOL)
3. Soft-core Exact T+0 R0 held vs L3 **-2.5148** tipY **1.923** — T+0 Soft-core is **behind** live, cannot explain live lagging research
4. Hybrid T+1 overlay + T+0 carve NEARPEAK3 held **-2.2498** tipY **-5.7831** — MDD/TIP block (0kav); T+0 hybrid worsens tip
5. Same-clock stack residual OVERRIDE vs L4_P3_WITHIN held **0.7661** tipY **3.1878** — mute+override alpha, not clock
6. L4 tipSoft P3 alone vs L3 held **+0.8475** — part of live Path3 cutover story; still below OVERRIDE
7. Disposition: do **not** chase live↔research tip Soft gap via more T+0; gap close = ACCEPT wire 0kb2 Exact T+1 LIVE_OVERRIDE (cutover separate)
8. Soft KEEP · Path4 OFF · broker false · no live wire this pack

Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_t0_gap_attrib_stagea.py`

Label: `TIPSOFT_IP3_T0_GAP_ATTRIB_STAGEA_SCREEN_2026-09-30__T0_NOT_DRIVER`
