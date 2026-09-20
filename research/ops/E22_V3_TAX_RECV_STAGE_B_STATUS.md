# E22_v3 Tax / Receivable — Stage B Status (refresh)


> **HISTORICAL / SSOT:** Soft-Frozen FIN was **[0.50, 0.95]** when this note was written.
> **Live today (2026-09-13+):** FIN **[0.60, 0.90]** · **KD_OPT** · **TEL_EQUAL** · **FUSE_ADDITIVE** · **DH_dd06** · **500M**.
> See `research/ops/OPS_STATUS.md`. Do not treat `[0.50, 0.95]` below as current live.

Date: 2026-09-16  
Status: **ACCEPT Stage-E promote** — live DEFAULT `E22_v3_recv_pay_effdelay`; Stage B tax sandboxes remain open  
Soft-Frozen FIN: **[0.60, 0.90] KEEP**  
Live DEFAULT books: **`E22_v3_recv_pay_effdelay`** (TAX0; receivable on effective ex; cash on effective pay)

## Sandbox axes

| Version | Role | Status |
|---|---|---|
| `E22_v3_recv_pay` | Receivable on ex; cash on pay; TAX0; stock=TW | **SANDBOX OPEN** + sealed compare DONE |
| `E22_v3_tax10` | Ex cash × 0.90; stock=TW | **SANDBOX OPEN** + sealed compare DONE |
| `E22_v3_tax20` | Ex cash × 0.80; stock=TW | **SANDBOX OPEN** + sealed compare DONE |
| `E22_v3_recv_pay_tax10` / `tax20` (`taxW`) | Combined recv+flat withhold | **SANDBOX OPEN** + sealed compare DONE |
| `E22_v3_recv_pay_effdelay_nhi211` | Stage-E timing + NHI 2.11% if single cash-div ≥20k | **SANDBOX OPEN** · cashflow-precision · `promote_ready=false` · `TAX_FOR_CASHFLOW_PURPOSE.md` |
| Resident/non-resident tax appendix | Promote gate | **BALLOT A KEEP TAX0** (2026-09-20) — 本國人＋慣例；年終所得稅 outside NAV；**不** 推 after-tax DEFAULT；sandbox tax10/20 research-only；NHI separate · `E22_V3_WITHHOLDING_RESIDENT_NOTE.md` |
## Latest sealed evidence

See `research/ops/E22_V3_STAGE_B_SEALED_COMPARE.md`.

## Explicit non-actions

- No DEFAULT flip · no Soft-Frozen flip · no forward/e21 rewrite · no E45 stitch

Label: `E22_V3_TAX_RECV_STAGE_B_2026-09-06__OPEN`
