# E22_v3 Tax / Receivable — Stage B Status (refresh)


> **HISTORICAL / SSOT:** Soft-Frozen FIN was **[0.50, 0.95]** when early Stage-B notes were written.
> **Live today (2026-09-19+):** FIN **[0.60, 0.90]** · **KD_OPT** · **TEL_EQUAL** · **FUSE → BLEND → L4 → DH** · **500M**.
> See `research/ops/OPS_STATUS.md`. Do not treat `[0.50, 0.95]` below as current live.

Date: 2026-09-19  
Status: **ACCEPT Stage-B promote** — live DEFAULT `E22_v3_recv_pay_tax10`  
Soft-Frozen FIN: **[0.60, 0.90] KEEP**  
Live DEFAULT books: **`E22_v3_recv_pay_tax10`** (flat 10% withhold; receivable on effective ex; cash on effective pay)  
Ballot: `research/ops/ACCEPT_CUTOVER_BUNDLE_2026-09-19.md`

## Sandbox axes

| Version | Role | Status |
|---|---|---|
| `E22_v3_recv_pay` | Receivable on ex; cash on pay; TAX0; stock=TW | **SANDBOX** (routable) |
| `E22_v3_tax10` | Ex cash × 0.90; stock=TW | **SANDBOX** (routable) |
| `E22_v3_tax20` | Ex cash × 0.80; stock=TW | **SANDBOX** (routable) |
| `E22_v3_recv_pay_effdelay` | Stage-E TAX0 timing sibling | **ROUTABLE** (superseded as DEFAULT) |
| `E22_v3_recv_pay_tax10` | Combined recv+flat 10% withhold + effective snaps | **LIVE DEFAULT** (ACCEPT 2026-09-19) |
| `E22_v3_recv_pay_tax20` | Combined recv+flat 20% withhold | **SANDBOX** (routable) |
| Resident/non-resident tax appendix | Historical promote gate | **SUPERSEDED** by human Stage-B ACCEPT (cutover bundle) |

## Latest sealed evidence

See `research/ops/E22_V3_STAGE_B_SEALED_COMPARE.md`.

## Explicit non-actions

- Soft-Frozen FIN clip KEEP · no forward/e21 history rewrite · no E45 stitch · tip lag ≠ second DEFAULT

Label: `E22_V3_TAX_RECV_STAGE_B_2026-09-19__ACCEPT`
