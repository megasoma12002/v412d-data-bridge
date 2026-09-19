# ACCEPT — Cutover bundle (L4 / FIN50 / BLEND / Soft / Sleeve / priv / tax Stage-B / broker)

> **SUPERSEDED / NOT BINDING (2026-09-19)**  
> Prior ACCEPTED ballots on this PR are **wiped for live SSOT**. Binding status is **`FROZEN — do not merge`** — see `LIVE_CUTOVER_BUNDLE_257_FROZEN.md` · register row 0.  
> Live remains 公股 R1 + `KD_OPT` + `TEL_EQUAL` + `FUSE_ADDITIVE` + `DH_dd06`. Do **not** treat the ballots below as authorized.

Status: **SUPERSEDED by FROZEN** (was ACCEPTED on this PR; merge blocked)  
Date: 2026-09-19  
Human (historical): 「ACCEPT L4 / FIN50 / BLEND / Soft / Sleeve / priv live / tax Stage-B / broker的修正」  
Human (binding): 「先鎖住現況 live、凍結 #257；民股等新機制或你改門檻再談」

## Ballots (historical — not authorized to merge)

| # | Ballot |
|---|---|
| Soft | `ACCEPT live Soft-assist cutover: SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` — **satisfied by live FUSE** (no independent Soft wire) |
| Sleeve | `ACCEPT live Sleeve-tilt cutover: SLEEVE_RSI14_LT30_a0225` — **satisfied by live FUSE** (no independent Sleeve wire) |
| FIN50 | `ACCEPT FIN_CAP_50 as BLEND_025 component` — Soft-Frozen BASE clip **KEEP [0.60, 0.90]** (no static FIN50 clip flip) |
| BLEND | `ACCEPT live Soft-Frozen cutover: BLEND_025` |
| L4 | `ACCEPT live L4 cutover: L4_DD_PATH_08_50` |
| Priv | `ACCEPT live FIN 民營 native cutover: PRIV_KD_MAY_Klt25_T15` |
| Tax | `ACCEPT promote E22 books: E22_v3_recv_pay_tax10` (Stage-B; supersedes resident `promote_ready=false`) |
| Broker | `ACCEPT broker live-write: broker_live_write_accepted=True` (env `E21_BROKER_WRITE_LIVE=1` + ballot file still required for mutate) |

## Live stack this ACCEPT *would have* installed (not live)

1. Soft-Frozen BASE clip **[0.60, 0.90]** KEEP  
2. **FUSE_ADDITIVE** (Soft `…__SELL_a05` + Sleeve `RSI14_a0225`) KEEP  
3. **BLEND_025** (α=0.25 · FIN_CAP_50[0.35,0.50] + 0.75 · post-FUSE)  
4. **L4_DD_PATH_08_50** (when TAIEX DD≤−8%, switch to FIN_CAP_50; else keep BLEND)  
5. **DH_dd06** KEEP  
6. FIN universe **PRIV_R3R4** + within-sleeve **PRIV_KD_MAY_Klt25_T15** (market panel merges `private_fin_adjusted` when needed)  
7. Books DEFAULT **`E22_v3_recv_pay_tax10`**  
8. `broker_live_write_accepted=True` · default `fill_port` remains `paper` until ops sets broker port + env

## Explicit non-actions (binding)

- Do **not** merge `#257`  
- Do **not** treat this file as live authorization  
- See `LIVE_CUTOVER_BUNDLE_257_FROZEN.md` for reopen gates  

Label: `ACCEPT_2026-09-19_CUTOVER_BUNDLE_SUPERSEDED_BY_FROZEN`
