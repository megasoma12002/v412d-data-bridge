#!/usr/bin/env python3
"""Provisional par-value inventory for Soft-Frozen / E22 books universe.

Research / ops only. Soft-Frozen KEEP. Does not flip DEFAULT_BOOKS_VERSION.

Writes:
  data/corporate_actions/par_value_by_code.csv
  repro/par-value-inventory/PAR_VALUE_INVENTORY.{json,md}

Every equity row starts as LOOKUP_NEEDED with provisional_par=10.0 until a cited
source fills verified_par. See research/ops/PAR_VALUE_LOOKUP_CHARTER.md.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "data" / "corporate_actions" / "par_value_by_code.csv"
REPRO = ROOT / "repro" / "par-value-inventory"
OUT_JSON = REPRO / "PAR_VALUE_INVENTORY.json"
OUT_MD = REPRO / "PAR_VALUE_INVENTORY.md"
OPS_JSON = ROOT / "research" / "ops" / "PAR_VALUE_INVENTORY.json"
OPS_MD = ROOT / "research" / "ops" / "PAR_VALUE_INVENTORY.md"

# Soft-Frozen FIN + telecom/0050 used in E22 books path
UNIVERSE = [
    {"code": "2880", "role": "soft_frozen_fin", "instrument": "equity"},
    {"code": "2886", "role": "soft_frozen_fin", "instrument": "equity"},
    {"code": "2892", "role": "soft_frozen_fin", "instrument": "equity"},
    {"code": "5880", "role": "soft_frozen_fin", "instrument": "equity"},
    {"code": "2412", "role": "telecom", "instrument": "equity"},
    {"code": "3045", "role": "telecom", "instrument": "equity"},
    {"code": "4904", "role": "telecom", "instrument": "equity"},
    {"code": "0050", "role": "etf", "instrument": "etf"},
]

PROVISIONAL_PAR = 10.0


def main() -> int:
    REPRO.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for u in UNIVERSE:
        if u["instrument"] == "etf":
            rows.append(
                {
                    **u,
                    "provisional_par_twd": None,
                    "verified_par_twd": None,
                    "as_of": None,
                    "source": None,
                    "source_url": None,
                    "status": "ETF_RULES_LOOKUP_NEEDED",
                    "notes": "ETF stock-div / odd-lot path uncommon; confirm before TW CIL apply",
                }
            )
        else:
            rows.append(
                {
                    **u,
                    "provisional_par_twd": PROVISIONAL_PAR,
                    "verified_par_twd": None,
                    "as_of": None,
                    "source": None,
                    "source_url": None,
                    "status": "LOOKUP_NEEDED",
                    "notes": "Do not treat provisional 10 as verified; 彈性面額 possible",
                }
            )

    df = pd.DataFrame(rows)
    # Preserve any already-verified rows if file exists
    if OUT_CSV.exists():
        old = pd.read_csv(OUT_CSV, dtype={"code": str})
        if "verified_par_twd" in old.columns:
            verified = old[old["verified_par_twd"].notna()][
                ["code", "verified_par_twd", "as_of", "source", "source_url", "status", "notes"]
            ]
            if not verified.empty:
                df = df.drop(columns=["verified_par_twd", "as_of", "source", "source_url", "status", "notes"], errors="ignore")
                df = df.merge(verified, on="code", how="left")
                df["status"] = df["status"].fillna("LOOKUP_NEEDED")
                mask = df["verified_par_twd"].notna()
                df.loc[mask, "status"] = df.loc[mask, "status"].where(
                    df.loc[mask, "status"].astype(str).str.startswith("VERIFIED"),
                    "VERIFIED",
                )

    df.to_csv(OUT_CSV, index=False)

    n = len(df)
    n_lookup = int((df["status"] == "LOOKUP_NEEDED").sum())
    n_etf = int((df["status"] == "ETF_RULES_LOOKUP_NEEDED").sum())
    n_verified = int(df["status"].astype(str).str.startswith("VERIFIED").sum())
    equity = df[df["instrument"] == "equity"]
    coverage_ok = bool(len(equity) > 0 and n_verified == len(equity))

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "PAR_VALUE_INVENTORY",
        "soft_frozen_unchanged": True,
        "live_wire": False,
        "charter": "research/ops/PAR_VALUE_LOOKUP_CHARTER.md",
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "n_codes": n,
        "n_lookup_needed": n_lookup,
        "n_etf_lookup_needed": n_etf,
        "n_verified": n_verified,
        "provisional_par_twd": PROVISIONAL_PAR,
        "coverage_pass_for_promote": coverage_ok,
        "rows": df.to_dict(orient="records"),
        "do_not": [
            "Promote E22_v2s_tw default while LOOKUP_NEEDED remains on Soft-Frozen equities",
            "Silent Soft-Frozen flip",
            "Rewrite forward/e21 history when pars are corrected",
        ],
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    md = "\n".join(
        [
            "# PAR_VALUE_INVENTORY",
            "",
            f"- generated: `{payload['generated_at_utc']}`",
            f"- coverage_pass_for_promote: **{coverage_ok}**",
            f"- verified / lookup / etf: **{n_verified}** / **{n_lookup}** / **{n_etf}**",
            f"- provisional_par_twd: `{PROVISIONAL_PAR}` (unverified default only)",
            "",
            "| Code | Role | Provisional | Verified | Status | Source |",
            "|---|---|---:|---:|---|---|",
        ]
        + [
            f"| {r['code']} | {r['role']} | {r.get('provisional_par_twd')} | "
            f"{r.get('verified_par_twd')} | {r['status']} | {r.get('source') or '—'} |"
            for r in rows
        ]
        + [
            "",
            "Charter: `research/ops/PAR_VALUE_LOOKUP_CHARTER.md`",
            "",
            "Soft-Frozen KEEP. No DEFAULT_BOOKS_VERSION flip from this script.",
            "",
        ]
    )

    for path, body in (
        (OUT_JSON, text),
        (OPS_JSON, text),
        (OUT_MD, md),
        (OPS_MD, md),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    print(json.dumps({k: payload[k] for k in (
        "label", "n_verified", "n_lookup_needed", "n_etf_lookup_needed",
        "coverage_pass_for_promote", "csv",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
