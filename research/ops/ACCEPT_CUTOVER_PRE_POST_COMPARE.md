# ACCEPT cutover — PRE vs POST live-stack paper compare

Generated: `2026-09-19T10:44:23.076533+00:00` · decomp overlay `2026-09-19`
Status: **RESEARCH / OPS** — Soft-Frozen KEEP · no forward rewrite

## Stacks

- **PRE (main):** `FUSE_ADDITIVE + DH_dd06 + KD_OPT(公股) + E22_v3_recv_pay_effdelay`
- **POST (#257 full):** `FUSE → BLEND_025 → L4_DD_PATH_08_50 → DH + PRIV_KD(民營) + E22_v3_recv_pay_tax10`
- Tip relative NAV (POST/PRE): **1.2760** (+27.6% end wealth)
- PRE end NAV: **2,175,065,600** · POST end NAV: **2,775,326,219**

## Full bundle (POST includes 公股→民營)

| Window | PRE CAGR | POST CAGR | Improve | PRE MDD | POST MDD | MDD improve |
|---|---:|---:|---:|---:|---:|---:|
| ytd | 57.23% | 83.93% | **+26.70 pp** | -11.07% | -8.63% | **+2.44 pp** |
| trailing_1y | 42.92% | 74.64% | **+31.71 pp** | -11.07% | -8.63% | **+2.44 pp** |
| sealed_2023_plus | 22.00% | 35.81% | **+13.81 pp** | -11.07% | -14.79% | **−3.72 pp** |
| heldout_2019_plus | 14.55% | 18.19% | **+3.64 pp** | -23.72% | -28.13% | **−4.41 pp** |
| full | 11.66% | 13.73% | **+2.06 pp** | -23.72% | -28.13% | **−4.41 pp** |

**Verdict (full bundle):** return **improves** across windows; tip NAV **+27.6%**. Drawdown **improves YTD/1y** but **worsens sealed/heldout** (deeper MDD). Dominant driver is **民營 universe**, not BLEND/L4 alone.

## Decomposition (same 公股 universe — isolate overlay + books)

POST_pub = PRE path + `BLEND_025` + `L4_DD_PATH` + `tax10` books · **no priv**.

| Window | Overlay giveback vs PRE | Overlay MDD improve | tax10-only giveback |
|---|---:|---:|---:|
| ytd | **−3.76** (overlay ahead) | +1.82 | −2.33 |
| trailing_1y | **−4.30** (overlay ahead) | +1.82 | +0.43 |
| sealed_2023_plus | **+1.38** (mild giveback) | +1.82 | +1.62 |
| heldout_2019_plus | −0.22 | +1.58 | +0.59 |
| full | +0.08 | +1.58 | +0.42 |

Tip rel NAV overlay-only vs PRE: **0.9909** (−0.9%).

**Verdict (overlay+books, no priv):** near-flat tip wealth; **MDD better ~+1.6–1.8 pp**; sealed CAGR mild giveback (~1.4 pp). Books tax10 alone is small vs overlay. This matches component month-end story (BLEND/L4 trade a little CAGR for better MDD) more than the full-bundle table.

## Read

- Merge **full #257** ≈ **return up, risk mixed** — mostly from **PRIV live**, not from BLEND/L4.
- Merge **strategy overlays only** (if priv were off) ≈ **slight tip drag, better MDD, sealed mild giveback**.
- Old dual-paper monitors vs Soft-Frozen **BASE** (no FUSE+DH) are not identical to this PRE baseline.

Repro: `PYTHONPATH=scripts python3 scripts/accept_cutover_pre_post_compare.py`  
Artifacts: `repro/accept-cutover-pre-post-compare/` · decomp `/opt/cursor/artifacts/accept_cutover_overlay_decomp.json`
