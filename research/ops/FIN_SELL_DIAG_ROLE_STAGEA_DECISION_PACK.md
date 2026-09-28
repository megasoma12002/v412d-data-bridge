# FIN_SELL_DIAG_ROLE_STAGEA_DECISION_PACK

Date: 2026-09-28 · Generated `2026-09-28T06:56:06Z`
Status: **DIAG_SIGNAL** · Soft-Frozen **KEEP** · SELL_a75 **KEEP** · `fin_sell_ok` **OFF** · live wire **false**

Charter: `FIN_SELL_DIAG_ROLE_STAGEA_CHARTER.md`
Screen: `FIN_SELL_DIAG_ROLE_STAGEA_SCREEN.md`

## Verdict

**`DIAG_SIGNAL`**

Role: **diagnostic label only** — no portfolio challenger, no hard sell gate.
Base sell WR 34.96% (n=924, H=21).

Top SIGNAL: `A_BREAK5` · WR↑ **3.8188pp** · n=98 · cov=10.6061% · WR=38.7755%

Follow-up allowed: paper **monitor/log** attribute on live fills — **not** `fin_sell_ok` gate, **not** observe promote from this pack alone.

## Binding

1. Soft-Frozen / tip / Exact T+1 / **SELL_a75** KEEP
2. **`fin_sell_ok` not applied** and not authorized by DIAG_*
3. DIAG_SIGNAL ≠ observe ≠ live; separate charter needed to act
4. Hard-gate sell tracks remain STOP / MDD_BLOCK (quality + new-mech)
5. Sell loss-defer remains REJECTED

Label: `FIN_SELL_DIAG_ROLE_STAGEA_DECISION_PACK_2026-09-28__DIAG_SIGNAL__NO_GATE__NO_LIVE`
