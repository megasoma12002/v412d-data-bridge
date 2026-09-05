#!/usr/bin/env python3
"""Par-value inventory for Soft-Frozen / E22 books — extensible per-code lookup.

Research / ops only. Soft-Frozen KEEP. Does not flip DEFAULT_BOOKS_VERSION.

Universe sources (merged, first role wins on conflict):
  1. data/corporate_actions/par_value_watchlist.csv  (editable watchlist)
  2. --add-codes CODE[,CODE...]                     (ad-hoc expansion)
  3. Existing rows already in par_value_by_code.csv (preserved)

Lookup:
  --fetch-twse   Pull 普通股每股面額 from TWSE openapi t187ap03_L for equities
                 in the merged universe (skips ETF / already VERIFIED unless
                 --refetch).

Writes:
  data/corporate_actions/par_value_by_code.csv
  repro/par-value-inventory/PAR_VALUE_INVENTORY.{json,md}
  research/ops/PAR_VALUE_INVENTORY.{json,md}

Promote gate: every *promote_gate* equity (soft_frozen_fin + telecom roles, or
instrument=equity with role not starting with expand_) must be VERIFIED.
Expansion codes (role=expand / future_*) do not block promote.

See research/ops/PAR_VALUE_LOOKUP_CHARTER.md.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WATCHLIST = ROOT / "data" / "corporate_actions" / "par_value_watchlist.csv"
OUT_CSV = ROOT / "data" / "corporate_actions" / "par_value_by_code.csv"
REPRO = ROOT / "repro" / "par-value-inventory"
OUT_JSON = REPRO / "PAR_VALUE_INVENTORY.json"
OUT_MD = REPRO / "PAR_VALUE_INVENTORY.md"
OPS_JSON = ROOT / "research" / "ops" / "PAR_VALUE_INVENTORY.json"
OPS_MD = ROOT / "research" / "ops" / "PAR_VALUE_INVENTORY.md"

TWSE_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
TWSE_SOURCE = "TWSE_openapi_t187ap03_L"
PROVISIONAL_PAR = 10.0

# Roles that must be VERIFIED before odd-lot DEFAULT promote
PROMOTE_GATE_ROLES = {"soft_frozen_fin", "telecom"}

# Built-in seed if watchlist missing (same as historical minimum universe)
SEED_UNIVERSE = [
    {"code": "2880", "role": "soft_frozen_fin", "instrument": "equity"},
    {"code": "2886", "role": "soft_frozen_fin", "instrument": "equity"},
    {"code": "2892", "role": "soft_frozen_fin", "instrument": "equity"},
    {"code": "5880", "role": "soft_frozen_fin", "instrument": "equity"},
    {"code": "2412", "role": "telecom", "instrument": "equity"},
    {"code": "3045", "role": "telecom", "instrument": "equity"},
    {"code": "4904", "role": "telecom", "instrument": "equity"},
    {"code": "0050", "role": "etf", "instrument": "etf"},
]


def _norm_code(raw: str) -> str:
    return str(raw or "").strip().zfill(4) if str(raw or "").strip().isdigit() else str(raw or "").strip()


def load_watchlist(path: Path = WATCHLIST) -> list[dict]:
    if not path.exists():
        return [dict(u) for u in SEED_UNIVERSE]
    df = pd.read_csv(path, dtype={"code": str})
    rows = []
    for _, r in df.iterrows():
        code = _norm_code(r.get("code", ""))
        if not code:
            continue
        rows.append(
            {
                "code": code,
                "role": str(r.get("role") or "expand").strip() or "expand",
                "instrument": str(r.get("instrument") or "equity").strip() or "equity",
                "notes": str(r.get("notes") or "").strip(),
            }
        )
    return rows or [dict(u) for u in SEED_UNIVERSE]


def merge_universe(
    watchlist: list[dict],
    add_codes: list[str],
    existing: pd.DataFrame | None,
) -> list[dict]:
    by_code: dict[str, dict] = {}
    for u in watchlist:
        by_code[u["code"]] = dict(u)
    for code in add_codes:
        c = _norm_code(code)
        if not c:
            continue
        if c not in by_code:
            by_code[c] = {
                "code": c,
                "role": "expand",
                "instrument": "equity",
                "notes": "Ad-hoc expansion via --add-codes; not promote-gate",
            }
    if existing is not None and not existing.empty:
        for _, r in existing.iterrows():
            c = _norm_code(r.get("code", ""))
            if not c or c in by_code:
                continue
            by_code[c] = {
                "code": c,
                "role": str(r.get("role") or "expand"),
                "instrument": str(r.get("instrument") or "equity"),
                "notes": str(r.get("notes") or "Preserved from prior inventory"),
            }
    # Stable: promote-gate first, then expand, then etf
    order = {"soft_frozen_fin": 0, "telecom": 1, "expand": 2, "etf": 3}
    return sorted(
        by_code.values(),
        key=lambda u: (order.get(u["role"], 9), u["code"]),
    )


def blank_row(u: dict) -> dict:
    if u["instrument"] == "etf":
        return {
            **{k: u[k] for k in ("code", "role", "instrument")},
            "provisional_par_twd": None,
            "verified_par_twd": None,
            "as_of": None,
            "source": None,
            "source_url": None,
            "status": "ETF_RULES_LOOKUP_NEEDED",
            "notes": u.get("notes")
            or "ETF stock-div / odd-lot path uncommon; confirm before TW CIL apply",
        }
    return {
        **{k: u[k] for k in ("code", "role", "instrument")},
        "provisional_par_twd": PROVISIONAL_PAR,
        "verified_par_twd": None,
        "as_of": None,
        "source": None,
        "source_url": None,
        "status": "LOOKUP_NEEDED",
        "notes": u.get("notes")
        or "Do not treat provisional 10 as verified; 彈性面額 possible",
    }


def parse_par_field(raw: str | None) -> float | None:
    if raw is None:
        return None
    text = str(raw)
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", text.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def roc_date_to_iso(raw: str | None) -> str | None:
    """TWSE 出表日期 like 1150904 → 2026-09-04."""
    if not raw:
        return None
    s = re.sub(r"\D", "", str(raw))
    if len(s) != 7:
        return None
    try:
        y = int(s[:3]) + 1911
        mo = int(s[3:5])
        d = int(s[5:7])
        return f"{y:04d}-{mo:02d}-{d:02d}"
    except ValueError:
        return None


def fetch_twse_par_map() -> dict[str, dict]:
    """Return code -> {par, as_of, notes} from TWSE listed-company profile."""
    req = urllib.request.Request(
        TWSE_URL,
        headers={"User-Agent": "v412d-par-inventory/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    out: dict[str, dict] = {}
    for row in data:
        code = _norm_code(row.get("公司代號") or row.get("Code") or "")
        if not code:
            continue
        par = parse_par_field(row.get("普通股每股面額"))
        if par is None:
            continue
        as_of = roc_date_to_iso(row.get("出表日期")) or datetime.now(timezone.utc).date().isoformat()
        out[code] = {
            "par": par,
            "as_of": as_of,
            "notes": f"普通股每股面額={row.get('普通股每股面額')}; 出表日期={row.get('出表日期')}",
        }
    return out


def is_promote_gate(row: dict | pd.Series) -> bool:
    role = str(row.get("role") or "")
    inst = str(row.get("instrument") or "")
    return inst == "equity" and role in PROMOTE_GATE_ROLES


def apply_verified_merge(df: pd.DataFrame, old: pd.DataFrame | None) -> pd.DataFrame:
    """Overlay previously verified equity pars onto a fresh universe frame."""
    merged = df.copy()
    if old is not None and not old.empty and "verified_par_twd" in old.columns:
        keep_cols = [
            "code",
            "verified_par_twd",
            "as_of",
            "source",
            "source_url",
            "status",
            "notes",
        ]
        verified = old[old["verified_par_twd"].notna()][
            [c for c in keep_cols if c in old.columns]
        ].copy()
        verified["code"] = verified["code"].map(_norm_code)
        if not verified.empty:
            by = verified.set_index("code")
            for i, row in merged.iterrows():
                code = _norm_code(row["code"])
                if code not in by.index:
                    continue
                if str(row.get("instrument")) == "etf":
                    continue
                hit = by.loc[code]
                if isinstance(hit, pd.DataFrame):
                    hit = hit.iloc[0]
                merged.at[i, "verified_par_twd"] = hit["verified_par_twd"]
                for col in ("as_of", "source", "source_url", "notes"):
                    if col in hit.index and pd.notna(hit[col]):
                        merged.at[i, col] = hit[col]
                status = str(hit.get("status") or "VERIFIED")
                merged.at[i, "status"] = (
                    status if status.startswith("VERIFIED") else "VERIFIED"
                )
    # ETF rows always keep ETF status (never LOOKUP_NEEDED)
    etf_mask = merged["instrument"].astype(str) == "etf"
    merged.loc[etf_mask, "status"] = "ETF_RULES_LOOKUP_NEEDED"
    return merged


def apply_twse(df: pd.DataFrame, twse: dict[str, dict], refetch: bool) -> pd.DataFrame:
    out = df.copy()
    for i, row in out.iterrows():
        if row.get("instrument") == "etf":
            continue
        code = _norm_code(row["code"])
        if not refetch and str(row.get("status", "")).startswith("VERIFIED"):
            continue
        hit = twse.get(code)
        if not hit:
            continue
        out.at[i, "verified_par_twd"] = hit["par"]
        out.at[i, "provisional_par_twd"] = (
            row.get("provisional_par_twd") if pd.notna(row.get("provisional_par_twd")) else PROVISIONAL_PAR
        )
        out.at[i, "as_of"] = hit["as_of"]
        out.at[i, "source"] = TWSE_SOURCE
        out.at[i, "source_url"] = TWSE_URL
        out.at[i, "status"] = "VERIFIED"
        out.at[i, "notes"] = hit["notes"]
    return out


def coverage_pass(df: pd.DataFrame) -> bool:
    gate = df[df.apply(is_promote_gate, axis=1)]
    if gate.empty:
        return False
    return bool((gate["status"].astype(str).str.startswith("VERIFIED")).all())


def write_artifacts(df: pd.DataFrame, method: str) -> dict:
    REPRO.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    n = len(df)
    n_lookup = int((df["status"] == "LOOKUP_NEEDED").sum())
    n_etf = int((df["status"] == "ETF_RULES_LOOKUP_NEEDED").sum())
    n_verified = int(df["status"].astype(str).str.startswith("VERIFIED").sum())
    n_expand = int((df["role"] == "expand").sum())
    ok = coverage_pass(df)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "PAR_VALUE_INVENTORY",
        "soft_frozen_unchanged": True,
        "live_wire": False,
        "charter": "research/ops/PAR_VALUE_LOOKUP_CHARTER.md",
        "watchlist": str(WATCHLIST.relative_to(ROOT)),
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "method": method,
        "extensible": True,
        "n_codes": n,
        "n_promote_gate": int(df.apply(is_promote_gate, axis=1).sum()),
        "n_expand": n_expand,
        "n_lookup_needed": n_lookup,
        "n_etf_lookup_needed": n_etf,
        "n_verified": n_verified,
        "provisional_par_twd": PROVISIONAL_PAR,
        "coverage_pass_for_promote": ok,
        "how_to_expand": [
            "Edit data/corporate_actions/par_value_watchlist.csv (role=expand for non-gate)",
            "Or: python scripts/e22_par_value_inventory.py --add-codes 2330,2303 --fetch-twse",
        ],
        "rows": df.to_dict(orient="records"),
        "do_not": [
            "Promote E22_v2s_tw default while promote-gate equities remain LOOKUP_NEEDED",
            "Silent Soft-Frozen flip",
            "Rewrite forward/e21 history when pars are corrected",
            "Treat expansion codes as promote blockers",
        ],
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    md_lines = [
        "# PAR_VALUE_INVENTORY",
        "",
        f"- generated: `{payload['generated_at_utc']}`",
        f"- coverage_pass_for_promote: **{ok}**",
        f"- verified / lookup / etf / expand: **{n_verified}** / **{n_lookup}** / **{n_etf}** / **{n_expand}**",
        f"- method: `{method}`",
        f"- extensible: watchlist `{WATCHLIST.relative_to(ROOT)}` + `--add-codes` + `--fetch-twse`",
        "",
        "| Code | Role | Provisional | Verified | Status | Source | As-of |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for _, r in df.iterrows():
        md_lines.append(
            f"| {r['code']} | {r['role']} | {r.get('provisional_par_twd')} | "
            f"{r.get('verified_par_twd')} | {r['status']} | {r.get('source') or '—'} | "
            f"{r.get('as_of') or '—'} |"
        )
    md_lines += [
        "",
        "Charter: `research/ops/PAR_VALUE_LOOKUP_CHARTER.md`",
        "",
        "Item 1 (odd-lot): Soft-Frozen FIN + telecom equity pars are the promote gate.",
        "Future codes: add to watchlist or `--add-codes` — does not auto-flip DEFAULT.",
        "",
        "Soft-Frozen KEEP. No DEFAULT_BOOKS_VERSION flip from this script.",
        "",
    ]
    md = "\n".join(md_lines)
    for path, body in (
        (OUT_JSON, text),
        (OPS_JSON, text),
        (OUT_MD, md),
        (OPS_MD, md),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--add-codes",
        default="",
        help="Comma-separated extra equity codes (role=expand; not promote-gate)",
    )
    ap.add_argument(
        "--fetch-twse",
        action="store_true",
        help="Fetch/verify pars from TWSE openapi t187ap03_L",
    )
    ap.add_argument(
        "--refetch",
        action="store_true",
        help="With --fetch-twse, overwrite already-VERIFIED rows",
    )
    args = ap.parse_args()

    add_codes = [c.strip() for c in args.add_codes.split(",") if c.strip()]
    old = pd.read_csv(OUT_CSV, dtype={"code": str}) if OUT_CSV.exists() else None
    universe = merge_universe(load_watchlist(), add_codes, old)
    df = pd.DataFrame([blank_row(u) for u in universe])
    df = apply_verified_merge(df, old)

    method = "watchlist + preserved verified rows"
    if args.fetch_twse:
        twse = fetch_twse_par_map()
        df = apply_twse(df, twse, refetch=args.refetch)
        method = f"TWSE openapi t187ap03_L field 普通股每股面額 (+ watchlist)"

    # Persist expansion codes into watchlist (role=expand) so future runs keep them
    if add_codes and WATCHLIST.exists():
        wl = pd.read_csv(WATCHLIST, dtype={"code": str})
        existing_codes = {_norm_code(c) for c in wl["code"].tolist()}
        extra = []
        for c in add_codes:
            code = _norm_code(c)
            if code in existing_codes:
                continue
            extra.append(
                {
                    "code": code,
                    "role": "expand",
                    "instrument": "equity",
                    "notes": "Future expansion; not Soft-Frozen promote-gate",
                }
            )
        if extra:
            wl = pd.concat([wl, pd.DataFrame(extra)], ignore_index=True)
            wl.to_csv(WATCHLIST, index=False)

    payload = write_artifacts(df, method)
    print(
        json.dumps(
            {
                k: payload[k]
                for k in (
                    "label",
                    "n_verified",
                    "n_lookup_needed",
                    "n_etf_lookup_needed",
                    "n_expand",
                    "coverage_pass_for_promote",
                    "csv",
                    "watchlist",
                    "how_to_expand",
                )
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
