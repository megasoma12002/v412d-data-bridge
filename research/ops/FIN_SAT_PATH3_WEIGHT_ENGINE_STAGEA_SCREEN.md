# FIN_SAT_PATH3_WEIGHT_ENGINE_STAGEA_SCREEN

Date: 2026-09-29 · `2026-09-29T11:23:16Z` · Verdict **`PROXY_WIRED_DEMO_OK`**
Engine `P3_SOFT_SLEEVE_EQ_RECON_PROXY` · demo asof **2026-06-12** (last COMP→SAT flip) · e21 state asof 2026-09-24

## Demo

- plan reason: `sat_equal_recon` · n_delta_names: **6**
- emit reason: `emitted` · n_orders: **6**
- tagged `-P3T0`: True · carve `T0_CARVE_FIN_SAT_SWITCH`: True
- same-bar fill: ok=True · n_fills=3 · policy=T0_CARVE_MOC_REF_CLOSE

### delta_shares

| code | Δ shares |
|---|---:|
| 2412 | -3000 |
| 2880 | -101000 |
| 2886 | +108000 |
| 2892 | -168000 |
| 4904 | +2000 |
| 5880 | +221000 |

### Controls

- no-flip @2026-09-24: `no_flip` (must not invent Soft qty)
- COMP identity @2026-05-20: `comp_identity_proxy_no_delta` · n_delta=0
- equal-recon probe n_delta_names=6

Soft-Frozen KEEP · broker false · cutover BLOCKED · e21 history not rewritten

Repro: `repro/fin-sat-path3-weight-engine-stagea/`

