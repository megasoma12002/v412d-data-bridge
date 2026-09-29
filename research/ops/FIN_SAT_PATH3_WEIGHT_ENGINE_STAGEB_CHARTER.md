# FIN_SAT_PATH3_WEIGHT_ENGINE_STAGEB_CHARTER

Date: 2026-09-29
Status: **Stage B — full COMP/SAT asof recon** · Soft-Frozen **KEEP** · emit/fill **ON** · broker **false** · cutover **BLOCKED**
Parents: 0ka8 `PROXY_WIRED_DEMO_OK` · 0ka7 observe θ=0.005 + T+0
Register: **0ka9**

## Question

Can Path3 emit **both** COMP→SAT and SAT→COMP flips with non-empty tagged `-P3T0` using asof recon policies matching paper books (COMP=OR_K9×HARD150 · SAT=RELAX KD), without Soft clip / CONF α / broker / cutover?

## Method

- Engine `P3_COMP_SAT_ASOF_RECON_B`
- Freeze Soft sleeve $ from live pos; rebuild FIN dest by policy; TEL equal; 0050 KEEP
- COMP: OR_K9 buy_ok ∧ HARD150 sell_ok · KD score tilt · HARD fail → dest 0
- SAT: base pre-ex buy_ok · KD score tilt · no HARD
- Paper sandbox demo only · e21 history not rewritten

## Non-goals

- Soft-Frozen flip-day coexistence mute
- live CONF α densify · broker · Path3 strategy cutover
- Cloning paper share ledgers (no daily pos SSOT)

Label: `FIN_SAT_PATH3_WEIGHT_ENGINE_STAGEB_CHARTER_2026-09-29__ASOF_RECON_B__NO_BROKER`
