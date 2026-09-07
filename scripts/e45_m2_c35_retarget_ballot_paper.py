#!/usr/bin/env python3
"""E45 M2 C35 observe-retarget ballot pack (DRAFT only).

Reads optimize pack outputs — does not re-sim. Does NOT OPEN C35.
Does NOT change operating lock M2_RELOC_BIL_FX_C50.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e45_paper_harness import CLAIM_STATUS, ROOT
from e45_m1_state_signal_paper import pp, yn

RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"
OPT_CSV = ROOT / "repro/e45-m2-bil-fx-optimize/outputs/optimize_section2_qualification.csv"
OPT_MD = RESEARCH / "E45_M2_BIL_FX_OPTIMIZE.md"
FREEZE = RESEARCH / "E45_M2_C35_TWDCASH_HIGHBETA_V0_FROZEN.md"
OUT = ROOT / "repro/e45-m2-c35-retarget-ballot"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    q = pd.read_csv(OPT_CSV)
    cut = q[q.kind == "cut_grid"].copy()
    # Prefer lowest held giveback among §2 PASS (optimize freeze rule)
    pass_cut = cut[cut.qualifies_section2].sort_values("heldout_1x_giveback_pp")
    preferred = pass_cut.iloc[0].to_dict() if len(pass_cut) else None
    c50 = cut[cut.book == "M2_RELOC_BIL_FX_C50"].iloc[0].to_dict()
    c35 = cut[cut.book == "M2_RELOC_BIL_FX_C35"].iloc[0].to_dict()
    by_score = cut[cut.qualifies_section2].sort_values("heldout_1x_score", ascending=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "DRAFT_BALLOT_ONLY",
        "operating_lock_today": "M2_RELOC_BIL_FX_C50",
        "proposed_retarget": "M2_RELOC_BIL_FX_C35",
        "selection_rule": "among §2 PASS cut-grid books, lowest heldout_1x CAGR giveback",
        "preferred_by_giveback": preferred,
        "c35": c35,
        "c50": c50,
        "top_by_held_score": by_score.head(3).to_dict(orient="records"),
        "claim_status": CLAIM_STATUS,
        "freeze": str(FREEZE.relative_to(ROOT)),
        "optimize_paper": str(OPT_MD.relative_to(ROOT)),
        "hard_non_actions": [
            "Do not silent-swap operating C50 lock",
            "Do not OPEN from this draft alone",
            "Soft-Frozen / DEFAULT KEEP; stitch FORBIDDEN",
            "No invent MDD replacement",
        ],
    }
    (RESEARCH / "E45_M2_C35_RETARGET_BALLOT.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )
    (OUT / "reports" / "E45_M2_C35_RETARGET_BALLOT.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )

    md = f"""# E45 M2 C35 Observe Retarget — Evidence Pack (DRAFT)

Generated: `{payload['generated_at_utc']}`  
Status: **DRAFT BALLOT ONLY — NOT OPEN**  
Operating lock today: **`M2_RELOC_BIL_FX_C50`** (unchanged)  
Freeze: `{FREEZE.relative_to(ROOT)}`  
Source: `{OPT_MD.relative_to(ROOT)}`

## Selection rule

Among cut-grid §2 PASS books @ κ=1, prefer **lowest held-out CAGR giveback** vs BASE  
→ preferred: **`{preferred.get('book') if preferred else 'n/a'}`**

## C35 vs C50

| Book | §2 | Held score | Giveback pp | MDD improve pp |
|---|---|---:|---:|---:|
| `M2_RELOC_BIL_FX_C35` | {yn(bool(c35['qualifies_section2']))} | {pp(c35['heldout_1x_score'])} | {pp(c35['heldout_1x_giveback_pp'])} | {pp(c35['heldout_1x_mdd_improve_pp'])} |
| `M2_RELOC_BIL_FX_C50` | {yn(bool(c50['qualifies_section2']))} | {pp(c50['heldout_1x_score'])} | {pp(c50['heldout_1x_giveback_pp'])} | {pp(c50['heldout_1x_mdd_improve_pp'])} |

Note: highest held score among PASS cuts may differ (e.g. C60/C55); giveback rule is the frozen read for retarget.

## Human gate

See ballot: `research/ops/E45_M2_C35_OBSERVE_RETARGET_BALLOT_DRAFT.md`

- **HOLD DRAFT** (default): keep C50 operating  
- **ACCEPT OPEN C35**: separate PR to retarget operating lock + month-end pack  
- **REJECT**: archive; keep C50  

## Governance

- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN  
- Claimed MDD: `{CLAIM_STATUS}`  
- Do **not** silent-swap C50→C35 from this file alone  
"""
    (RESEARCH / "E45_M2_C35_RETARGET_BALLOT.md").write_text(md, encoding="utf-8")
    (OUT / "reports" / "E45_M2_C35_RETARGET_BALLOT.md").write_text(md, encoding="utf-8")

    ballot = f"""# E45 M2 BIL_FX Observe Retarget C35 — OPEN Ballot **DRAFT**

Status: **DRAFT ONLY — NOT OPEN**  
Proposed ballot name: `E45 OPEN M2 BIL_FX relocate observe retarget C35`  
Date: 2026-09-07  
Chinese mirror: `research/ops/E45_M2_C35_OBSERVE_RETARGET_BALLOT_DRAFT.zh-TW.md`  
Evidence: `research/e45/E45_M2_C35_RETARGET_BALLOT.md`

> Does **NOT** change the operating lock. Remains paper-only until separate human **ACCEPT OPEN C35**.  
> Current OPERATING observe stays **`M2_RELOC_BIL_FX_C50`**.

Soft-Frozen: **[0.50, 0.95] KEEP**  
Live DEFAULT: **`E22_v2s_tw` KEEP**  
Live stitch: **still FORBIDDEN**  
Parent sleeves OPERATING: FULL + A25 + A05 + FIN_A10 + **BIL_FX_C50**

## Proposal (if later ACCEPTed)

| Field | Value |
|---|---|
| Choice | Retarget M2 BIL_FX observe lock **C50 → C35** |
| New locked book | **`M2_RELOC_BIL_FX_C35`** |
| Prior lock | `M2_RELOC_BIL_FX_C50` (do not retire evidence; swap monitor lock only) |
| Sensor / actuator | M1 `s_{{t-1}}` · `RELOC_BIL_FX` · cut `c=0.35` |
| Why | Optimize giveback-min among §2 PASS cuts (held giveback ~{pp(c35['heldout_1x_giveback_pp'])} vs C50 ~{pp(c50['heldout_1x_giveback_pp'])}) |
| Live wire? | **No** |
| Soft-Frozen flip? | **No** |
| Stitch? | **No** |
| Auto-OPEN C75? | **No** |

## Human choices

| Choice | Effect |
|---|---|
| **HOLD DRAFT** (default) | Keep C50 OPERATING |
| **ACCEPT OPEN C35** | Separate PR: update OPEN docs + dual-ledger + month-end pack lock |
| **REJECT** | Archive; keep C50 |

## Explicit non-actions

1. Do not silent-swap C50→C35 without ACCEPT.  
2. Do not stitch / Soft-Frozen / DEFAULT flip.  
3. Do not invent MDD replacement.  
4. Do not label BIL_FX as TWD cash.

Label: `E45_M2_C35_OBSERVE_RETARGET_BALLOT_DRAFT_2026-09-07__NOT_OPEN__STITCH_FORBIDDEN`
"""
    (OPS / "E45_M2_C35_OBSERVE_RETARGET_BALLOT_DRAFT.md").write_text(ballot, encoding="utf-8")
    (OPS / "E45_M2_C35_OBSERVE_RETARGET_BALLOT_DRAFT.zh-TW.md").write_text(
        f"""# E45 M2 BIL_FX Observe 改鎖 C35 — OPEN 票 **DRAFT**

狀態：**DRAFT ONLY — 尚未 OPEN**  
現行 OPERATING 鎖定：**`M2_RELOC_BIL_FX_C50`**（不變）  
證據：`research/e45/E45_M2_C35_RETARGET_BALLOT.md`

| 選擇 | 效果 |
|---|---|
| **HOLD DRAFT**（預設） | 維持 C50 OPERATING |
| **ACCEPT OPEN C35** | 另 PR 改鎖雙帳本／月底監看 |
| **REJECT** | 封存；維持 C50 |

Soft-Frozen／DEFAULT **KEEP** · stitch **FORBIDDEN** · 不發明 MDD · 不把 BIL_FX 當台幣現金
""",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "preferred": preferred.get("book") if preferred else None, "c35_giveback": c35["heldout_1x_giveback_pp"], "c50_giveback": c50["heldout_1x_giveback_pp"]}, indent=2))


if __name__ == "__main__":
    main()
