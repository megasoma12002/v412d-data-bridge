# META_DETECT_STACK_SELECT_STAGEA_DECISION_PACK

Date: 2026-09-30 · Verdict: **`META_DETECT_MDD_BLOCK`** · champion=**`DETECT_P3_THETA`**
Register: **0kat** · mech **`META_DETECT_STACK_SELECT`**

## Detect champion vs live

- held CAGR lift: **1.248** pp
- full CAGR lift: **0.487** pp
- sealed MDD improve: **-0.5026** pp
- tipY / tip1y: **2.8672** / **3.1765**

## Rule

- Soft shell always-on; FUSE / COOL / Path3 are detector-gated research blocks.
- Do not always-on stack every researched HIT onto live.

## Next

1. Meta rule: Soft shell always-on; FUSE/COOL/P3 are optional blocks gated by detectors
2. Detect champion `DETECT_P3_THETA` → MDD_BLOCK held 1.248 tipY 2.8672 sealedMDD -0.5026
3. Best static contrast `STATIC_L1_SOFT` → MDD_BLOCK held 1.5328 tipY 8.8607 sealedMDD -3.2544
4. DETECT_P3_THETA (live stack + Path3 only when |trail|≥θ) lifts held vs always-on P3 but sealed MDD still blocks
5. DETECT_FUSE_RISKON lifts tipY a lot vs always-on FUSE+COOL but sealed MDD still blocks
6. Oracle DIAG lookahead upper bound proves selection headroom — never promote
7. Path4 OFF · Soft KEEP · broker false · no live wire · next harden sealed-MDD detectors

Label: `META_DETECT_STACK_SELECT_STAGEA_DECISION_PACK_2026-09-30__META_DETECT_MDD_BLOCK__NO_LIVE`
