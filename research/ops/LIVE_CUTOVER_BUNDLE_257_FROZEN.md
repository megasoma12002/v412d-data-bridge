# Live cutover bundle `#257` — FROZEN

Date: 2026-09-19  
Status: **FROZEN — do not merge**  
Human: **「先鎖住現況 live、凍結 #257；民股等新機制或你改門檻再談」**

## Binding live (unchanged)

| Item | Value |
|---|---|
| Soft-Frozen | FIN **[0.60, 0.90]** · 公股 R1 · `KD_OPT` · `TEL_EQUAL` |
| Overlay | **`FUSE_ADDITIVE` + `DH_dd06`** |
| Path | `forward/e21/` · 500M · lot 1000 |
| Books DEFAULT (main) | `E22_v3_recv_pay_effdelay` (tip may lag) |
| Broker mutate | **off** (fill_port paper) |

## Why `#257` is frozen

Prior ACCEPT ballots on `#257` (L4 / BLEND / priv-replace / tax / broker) are **superseded for merge** by Stage-A evidence:

| Track | Result | Ref |
|---|---|---|
| 公股＋民營並存 × MDD | **STOP** — 0 sealed-MDD coexist | `#258` · `PUB_PRIV_COEXIST_MDD_DECISION_PACK.md` |
| 四類 SF4 + DH/L4 防禦 × MDD | **STOP** — 0 sealed-MDD coexist | `#259` · `SF4_DEFENCE_MDD_DECISION_PACK.md` |

Priv-**replace** is not 並存 and is **not** authorized as a substitute while 並存 fails sealed MDD.

## PR triage (2026-09-19)

| PR | Action |
|---|---|
| `#257` | **FROZEN / blocked** — leave draft · **do not merge** · **無民股小包暫不拆**（要拆再說） |
| `#258` | **STOP research archive** — close after freeze SSOT lands (decision packs on `#260`) |
| `#259` | **STOP research archive** — close after freeze SSOT lands (decision packs on `#260`) |
| `#260` | Freeze SSOT + archived STOP packs → merge to keep main aligned |

## Allowed next (only)

1. Keep operating current live (forward / QC / tip books align).  
2. Merge `#260` for freeze + STOP archive on main; then **close** `#258`/`#259`.  
3. Re-open cutover only after: **new mechanism** charter (≠ retune frozen SF4 cell) **or** human-accepted **sealed-gate change**.  
4. Optional later: split `#257` into **無民股** (BLEND/L4/tax only) — **not authorized now**.

## Explicit non-actions

- Do **not** merge `#257`  
- Do **not** live-expand 民股 / 四類 Soft-Frozen  
- Do **not** soften sealed MDD from research peek  
- Do **not** enable broker live-write from `#257`  
- Do **not** split/merge「無民股小包」until a separate human ask  

Label: `LIVE_CUTOVER_BUNDLE_257_FROZEN_2026-09-19__KEEP_PUB_FUSE_DH`
