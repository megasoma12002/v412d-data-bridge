# TIPSOFT_IP3_T0_GAP_ATTRIB_STAGEA_DECISION_PACK

Date: 2026-09-30 · Verdict: **`T0_NOT_DRIVER`**
Register: **0kb5** · Parents: 0kb2, 0kar, 0kav, 0kaq

## Answer

**No — T+0 is not what makes live lag tip Soft research.**

- tip Soft Exact T+1 `OVERRIDE_LIVE_W42_M05_K3` vs L3: held **+1.6136** · tipY **+6.0402** (same clock)
- Soft-core Exact T+0 vs L3: held **-2.5148** · tipY **1.923** (behind live)
- Hybrid T+0 carve NEARPEAK3 vs L3: held **-2.2498** · tipY **-5.7831** (blocked)
- Same-clock OVERRIDE vs L4: held **+0.7661** — stack mute+override, not clock

## Disposition

- Do not use more T+0 research to close live↔0kb2 gap
- Close gap by ACCEPT wiring Exact T+1 LIVE_OVERRIDE (separate ballot; cutover now BLOCKED)
- Live's existing Path3 T+0 carve stays narrow (`T0_CARVE_FIN_SAT_SWITCH`); unrelated to tip Soft observe lead
- Soft KEEP · Path4 OFF · no live wire this pack

## Next

1. Question: does T+0 cause live to lag tip Soft research?
2. Verdict `T0_NOT_DRIVER`: tip Soft Exact T+1 OVERRIDE held vs L3 **+1.6136** tipY **+6.0402** (same clock as live Soft+FUSE+COOL)
3. Soft-core Exact T+0 R0 held vs L3 **-2.5148** tipY **1.923** — T+0 Soft-core is **behind** live, cannot explain live lagging research
4. Hybrid T+1 overlay + T+0 carve NEARPEAK3 held **-2.2498** tipY **-5.7831** — MDD/TIP block (0kav); T+0 hybrid worsens tip
5. Same-clock stack residual OVERRIDE vs L4_P3_WITHIN held **0.7661** tipY **3.1878** — mute+override alpha, not clock
6. L4 tipSoft P3 alone vs L3 held **+0.8475** — part of live Path3 cutover story; still below OVERRIDE
7. Disposition: do **not** chase live↔research tip Soft gap via more T+0; gap close = ACCEPT wire 0kb2 Exact T+1 LIVE_OVERRIDE (cutover separate)
8. Soft KEEP · Path4 OFF · broker false · no live wire this pack

Label: `TIPSOFT_IP3_T0_GAP_ATTRIB_STAGEA_DECISION_PACK_2026-09-30__T0_NOT_DRIVER__NO_LIVE`
