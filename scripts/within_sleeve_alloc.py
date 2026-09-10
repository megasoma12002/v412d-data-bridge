#!/usr/bin/env python3
"""Generic within-sleeve name allocation (paper research + optional live).

Used for Financial / Telecom multi-name sleeves under board-lot 1000.
Soft-Frozen *sleeve clips* are unchanged — this only splits sleeve trade dollars
across member codes.
"""
from __future__ import annotations

from tw_share_lots import BOARD_LOT, board_lots

POLICY_EQUAL = "EQUAL"
POLICY_MIN_LOT_PACK = "MIN_LOT_PACK"
POLICY_SCORE_LOT_PACK = "SCORE_LOT_PACK"
POLICY_DIVERSIFY_PACK = "DIVERSIFY_PACK"
POLICY_TOP1 = "TOP1"
POLICY_TOP2_EQUAL = "TOP2_EQUAL"
POLICY_RS_SOFT_TILT = "RS_SOFT_TILT"
POLICY_EXDIV_SKIP_BUY = "EXDIV_SKIP_BUY"
POLICY_RS_SOFT_TILT_EXDIV = "RS_SOFT_TILT_EXDIV"
POLICY_MIX_EQUAL_RS_EXDIV = "MIX_EQUAL_RS_EXDIV"
POLICY_MIX_EQUAL_PRE_EXDIV_KD = "MIX_EQUAL_PRE_EXDIV_KD"
POLICY_PRE_EXDIV_KD = "PRE_EXDIV_KD"
POLICY_POST_EXDIV_KD = "POST_EXDIV_KD"
POLICY_DUAL_PUB_PRIV = "DUAL_PUB_PRIV"
POLICY_SUFFIXES = (
    POLICY_EQUAL,
    POLICY_MIN_LOT_PACK,
    POLICY_SCORE_LOT_PACK,
    POLICY_DIVERSIFY_PACK,
    POLICY_TOP1,
    POLICY_TOP2_EQUAL,
    POLICY_RS_SOFT_TILT,
    POLICY_EXDIV_SKIP_BUY,
    POLICY_RS_SOFT_TILT_EXDIV,
    POLICY_MIX_EQUAL_RS_EXDIV,
    POLICY_MIX_EQUAL_PRE_EXDIV_KD,
    POLICY_PRE_EXDIV_KD,
    POLICY_POST_EXDIV_KD,
    POLICY_DUAL_PUB_PRIV,
)

# Predeclared ids (Stage B + Stage C)
FIN_EQUAL = "FIN_EQUAL"
FIN_MIN_LOT_PACK = "FIN_MIN_LOT_PACK"
FIN_TOP1 = "FIN_TOP1"
FIN_TOP2_EQUAL = "FIN_TOP2_EQUAL"
FIN_RS_SOFT_TILT = "FIN_RS_SOFT_TILT"
FIN_EXDIV_SKIP_BUY = "FIN_EXDIV_SKIP_BUY"
FIN_RS_SOFT_TILT_EXDIV = "FIN_RS_SOFT_TILT_EXDIV"
FIN_MIX_EQUAL_RS_EXDIV = "FIN_MIX_EQUAL_RS_EXDIV"
FIN_MIX_EQUAL_PRE_EXDIV_KD = "FIN_MIX_EQUAL_PRE_EXDIV_KD"
FIN_PRE_EXDIV_KD = "FIN_PRE_EXDIV_KD"
FIN_POST_EXDIV_KD = "FIN_POST_EXDIV_KD"
# Paper-only: Soft-Frozen Financial dollars split into 金融公 + 金融民 (coexist).
FIN_DUAL_PUB_PRIV = "FIN_DUAL_PUB_PRIV"
FIN_ALLOC_POLICIES = (
    FIN_EQUAL,
    FIN_MIN_LOT_PACK,
    FIN_TOP1,
    FIN_TOP2_EQUAL,
    FIN_RS_SOFT_TILT,
    FIN_EXDIV_SKIP_BUY,
    FIN_RS_SOFT_TILT_EXDIV,
    FIN_MIX_EQUAL_RS_EXDIV,
    FIN_MIX_EQUAL_PRE_EXDIV_KD,
    FIN_PRE_EXDIV_KD,
    FIN_POST_EXDIV_KD,
    FIN_DUAL_PUB_PRIV,
)

TEL_EQUAL = "TEL_EQUAL"
TEL_MIN_LOT_PACK = "TEL_MIN_LOT_PACK"
TEL_SCORE_LOT_PACK = "TEL_SCORE_LOT_PACK"
TEL_DIVERSIFY_PACK = "TEL_DIVERSIFY_PACK"
TEL_TOP1 = "TEL_TOP1"
TEL_TOP2_EQUAL = "TEL_TOP2_EQUAL"
TEL_RS_SOFT_TILT = "TEL_RS_SOFT_TILT"
TEL_EXDIV_SKIP_BUY = "TEL_EXDIV_SKIP_BUY"
TEL_RS_SOFT_TILT_EXDIV = "TEL_RS_SOFT_TILT_EXDIV"
TEL_MIX_EQUAL_RS_EXDIV = "TEL_MIX_EQUAL_RS_EXDIV"
TEL_PRE_EXDIV_KD = "TEL_PRE_EXDIV_KD"
TEL_MIX_EQUAL_PRE_EXDIV_KD = "TEL_MIX_EQUAL_PRE_EXDIV_KD"
TEL_ALLOC_POLICIES = (
    TEL_EQUAL,
    TEL_MIN_LOT_PACK,
    TEL_SCORE_LOT_PACK,
    TEL_DIVERSIFY_PACK,
    TEL_TOP1,
    TEL_TOP2_EQUAL,
    TEL_RS_SOFT_TILT,
    TEL_EXDIV_SKIP_BUY,
    TEL_RS_SOFT_TILT_EXDIV,
    TEL_MIX_EQUAL_RS_EXDIV,
    TEL_PRE_EXDIV_KD,
    TEL_MIX_EQUAL_PRE_EXDIV_KD,
)


def policy_kind(policy_id: str) -> str:
    if policy_id in (FIN_EQUAL, TEL_EQUAL):
        return POLICY_EQUAL
    if policy_id == FIN_DUAL_PUB_PRIV:
        return POLICY_DUAL_PUB_PRIV
    if policy_id.endswith("_SCORE_LOT_PACK"):
        return POLICY_SCORE_LOT_PACK
    if policy_id.endswith("_DIVERSIFY_PACK"):
        return POLICY_DIVERSIFY_PACK
    if policy_id.endswith("_MIN_LOT_PACK"):
        return POLICY_MIN_LOT_PACK
    if policy_id.endswith("_TOP1"):
        return POLICY_TOP1
    if policy_id.endswith("_TOP2_EQUAL"):
        return POLICY_TOP2_EQUAL
    if policy_id.endswith("_MIX_EQUAL_RS_EXDIV") or policy_id == FIN_MIX_EQUAL_RS_EXDIV:
        return POLICY_MIX_EQUAL_RS_EXDIV
    if (
        policy_id.endswith("_MIX_EQUAL_PRE_EXDIV_KD")
        or policy_id == FIN_MIX_EQUAL_PRE_EXDIV_KD
        or policy_id == TEL_MIX_EQUAL_PRE_EXDIV_KD
    ):
        return POLICY_MIX_EQUAL_PRE_EXDIV_KD
    if (
        policy_id.endswith("_PRE_EXDIV_KD")
        or policy_id == FIN_PRE_EXDIV_KD
        or policy_id == TEL_PRE_EXDIV_KD
    ):
        return POLICY_PRE_EXDIV_KD
    if policy_id.endswith("_POST_EXDIV_KD") or policy_id == FIN_POST_EXDIV_KD:
        return POLICY_POST_EXDIV_KD
    if policy_id.endswith("_RS_SOFT_TILT_EXDIV"):
        return POLICY_RS_SOFT_TILT_EXDIV
    if policy_id.endswith("_RS_SOFT_TILT"):
        return POLICY_RS_SOFT_TILT
    if policy_id.endswith("_EXDIV_SKIP_BUY"):
        return POLICY_EXDIV_SKIP_BUY
    raise ValueError(f"unknown within-sleeve policy id: {policy_id}")


def held_board_qty(pos: dict, code: str, lot_size: int = BOARD_LOT) -> int:
    held = float(pos.get(code, 0.0))
    if lot_size <= 1:
        return int(held)
    return board_lots(held) if lot_size == BOARD_LOT else int(held // lot_size) * lot_size


def lot_qty_from_notional(value: float, price: float, lot_size: int = BOARD_LOT) -> int:
    if price <= 0 or lot_size < 1:
        return 0
    raw = int(abs(float(value)) / float(price))
    if lot_size == 1:
        return raw
    return (raw // lot_size) * lot_size


def _coalesce_orders(rows: list[tuple[str, str, int]]) -> list[tuple[str, str, int]]:
    acc: dict[tuple[str, str], int] = {}
    for code, side, qty in rows:
        if qty < 1:
            continue
        key = (code, side)
        acc[key] = acc.get(key, 0) + int(qty)
    side_rank = {"SELL": 0, "BUY": 1}
    keys = sorted(acc.keys(), key=lambda k: (side_rank.get(k[1], 9), k[0]))
    return [(c, s, acc[(c, s)]) for c, s in keys]


def allocate_equal_notional(
    codes: list[str] | tuple[str, ...],
    sleeve_dollars: float,
    closes: dict[str, float],
    pos: dict,
    *,
    lot_size: int = BOARD_LOT,
) -> list[tuple[str, str, int]]:
    out: list[tuple[str, str, int]] = []
    if abs(sleeve_dollars) < 1e-9 or not codes:
        return out
    per = float(sleeve_dollars) / len(codes)
    side = "BUY" if per > 0 else "SELL"
    for c in codes:
        px = float(closes[c])
        qty = lot_qty_from_notional(per, px, lot_size=lot_size)
        if side == "SELL":
            qty = min(qty, held_board_qty(pos, c, lot_size))
        if qty < (1 if lot_size == 1 else lot_size):
            continue
        out.append((c, side, int(qty)))
    return out


def _score_map(
    names: list[str], scores: dict[str, float] | None
) -> dict[str, float]:
    out = {c: 0.0 for c in names}
    if scores:
        for c in names:
            if c in scores and scores[c] is not None:
                out[c] = float(scores[c])
    return out


def soft_tilt_weights(names: list[str], score_map: dict[str, float]) -> dict[str, float]:
    """Soft RS weights: w ∝ exp(0.5 · clip(score, −3, 3)). Not hard concentration."""
    import math

    if not names:
        return {}
    raw = {
        c: math.exp(0.5 * max(-3.0, min(3.0, float(score_map.get(c, 0.0)))))
        for c in names
    }
    s = sum(raw.values())
    if s <= 0:
        return {c: 1.0 / float(len(names)) for c in names}
    return {c: raw[c] / s for c in names}


def allocate_weighted_notional(
    codes: list[str] | tuple[str, ...],
    sleeve_dollars: float,
    closes: dict[str, float],
    pos: dict,
    weights: dict[str, float],
    *,
    lot_size: int = BOARD_LOT,
) -> list[tuple[str, str, int]]:
    out: list[tuple[str, str, int]] = []
    if abs(sleeve_dollars) < 1e-9 or not codes:
        return out
    side = "BUY" if sleeve_dollars > 0 else "SELL"
    for c in codes:
        w = float(weights.get(c, 0.0))
        if w <= 0:
            continue
        per = float(sleeve_dollars) * w
        px = float(closes[c])
        qty = lot_qty_from_notional(per, px, lot_size=lot_size)
        if side == "SELL":
            qty = min(qty, held_board_qty(pos, c, lot_size))
        if qty < (1 if lot_size == 1 else lot_size):
            continue
        out.append((c, side, int(qty)))
    return out


def _buy_eligible(
    names: list[str], buy_ok: dict[str, bool] | None
) -> list[str]:
    if buy_ok is None:
        return list(names)
    return [c for c in names if bool(buy_ok.get(c, True))]



def _pack_one_lot_then_dump(
    names: list[str],
    sleeve_dollars: float,
    closes: dict[str, float],
    *,
    lot_size: int,
    order_names: list[str],
    dump_equal: bool,
) -> list[tuple[str, str, int]]:
    """≥1 張 along order_names; remainder dump to first or equal-split among bought."""
    out: list[tuple[str, str, int]] = []
    remaining = float(sleeve_dollars)
    bought: list[str] = []
    for c in order_names:
        px = float(closes[c])
        lot_cost = px * lot_size
        if lot_cost <= 0 or remaining + 1e-9 < lot_cost:
            continue
        out.append((c, "BUY", int(lot_size)))
        remaining -= lot_cost
        bought.append(c)
    positives = [float(closes[c]) for c in names if float(closes[c]) > 0]
    if positives and remaining < lot_size * min(positives):
        return out
    if dump_equal and bought:
        out.extend(
            allocate_equal_notional(bought, remaining, closes, {c: 0 for c in bought}, lot_size=lot_size)
        )
        return out
    refill = bought if bought else order_names
    for c in refill:
        px = float(closes[c])
        if px <= 0:
            continue
        extra = lot_qty_from_notional(remaining, px, lot_size=lot_size)
        if extra < lot_size:
            continue
        out.append((c, "BUY", int(extra)))
        remaining -= extra * px
    return out


def allocate_mix_equal_rs_exdiv(
    sleeve_dollars: float,
    closes: dict[str, float],
    pos: dict,
    *,
    codes: list[str] | tuple[str, ...],
    lot_size: int = BOARD_LOT,
    scores: dict[str, float] | None = None,
    buy_ok: dict[str, bool] | None = None,
    sell_ok: dict[str, bool] | None = None,
    sell_scores: dict[str, float] | None = None,
    mix_lambda: float = 0.5,
) -> list[tuple[str, str, int]]:
    """Blend notionals: λ·EQUAL + (1−λ)·RS_SOFT_TILT_EXDIV, then board-lot.

    λ=1 → pure equal-split; λ=0 → pure RS+exdiv skip-buy.
    Optional ``sell_ok`` / ``sell_scores`` apply on the sell leg (paper soft-assist).
    """
    names = list(codes)
    if not names or abs(sleeve_dollars) < 1e-9:
        return []
    lam = float(mix_lambda)
    if lam < 0.0 or lam > 1.0:
        raise ValueError(f"mix_lambda must be in [0,1], got {lam}")

    eq_each = float(sleeve_dollars) / float(len(names))
    eq = {c: eq_each for c in names}

    score_map = _score_map(names, scores)
    if sleeve_dollars < 0:
        holders = [c for c in names if held_board_qty(pos, c, lot_size) > 0] or names
        if sell_ok is not None:
            holders = [c for c in holders if bool(sell_ok.get(c, False))]
            if not holders:
                return []
        if sell_scores is not None and holders:
            sell_map = _score_map(holders, sell_scores)
            w = soft_tilt_weights(holders, sell_map)
            rs = {c: (float(sleeve_dollars) * w[c] if c in holders else 0.0) for c in names}
        else:
            rs_each = float(sleeve_dollars) / float(len(holders))
            rs = {c: (rs_each if c in holders else 0.0) for c in names}
    else:
        eligible = _buy_eligible(names, buy_ok)
        rs = {c: 0.0 for c in names}
        if eligible:
            w = soft_tilt_weights(eligible, score_map)
            for c in eligible:
                rs[c] = float(sleeve_dollars) * w[c]

    mix = {c: lam * eq[c] + (1.0 - lam) * rs[c] for c in names}
    out: list[tuple[str, str, int]] = []
    for c, dollars in mix.items():
        if abs(dollars) < 1e-9:
            continue
        side = "BUY" if dollars > 0 else "SELL"
        px = float(closes[c])
        qty = lot_qty_from_notional(dollars, px, lot_size=lot_size)
        if side == "SELL":
            qty = min(qty, held_board_qty(pos, c, lot_size))
        if qty < (1 if lot_size == 1 else lot_size):
            continue
        out.append((c, side, int(qty)))
    return _coalesce_orders(out)


def allocate_dual_pub_priv(
    sleeve_dollars: float,
    closes: dict[str, float],
    pos: dict,
    *,
    pub_codes: list[str] | tuple[str, ...],
    priv_codes: list[str] | tuple[str, ...],
    pub_share: float,
    lot_size: int = BOARD_LOT,
    scores: dict[str, float] | None = None,
    buy_ok: dict[str, bool] | None = None,
    sell_ok: dict[str, bool] | None = None,
    sell_scores: dict[str, float] | None = None,
    pub_policy: str = FIN_PRE_EXDIV_KD,
    priv_policy: str = FIN_EQUAL,
) -> list[tuple[str, str, int]]:
    """Split Financial trade dollars into 金融公 / 金融民, then within-group policy.

    ``pub_share`` ∈ [0,1] is the fraction of Financial sleeve dollars for 公股.
    Soft-Frozen Financial *weight* is unchanged; this only splits that sleeve.
    """
    share = float(pub_share)
    if share < 0.0 or share > 1.0:
        raise ValueError(f"pub_share must be in [0,1], got {share}")
    pub = list(pub_codes)
    priv = list(priv_codes)
    if not pub and not priv:
        return []
    d_pub = float(sleeve_dollars) * share
    d_priv = float(sleeve_dollars) * (1.0 - share)
    out: list[tuple[str, str, int]] = []
    if pub and abs(d_pub) >= 1e-9:
        out.extend(
            allocate_sleeve_orders(
                d_pub,
                closes,
                pos,
                policy_id=pub_policy,
                codes=pub,
                lot_size=lot_size,
                scores=scores,
                buy_ok=buy_ok,
                sell_ok=sell_ok,
                sell_scores=sell_scores,
            )
        )
    if priv and abs(d_priv) >= 1e-9:
        out.extend(
            allocate_sleeve_orders(
                d_priv,
                closes,
                pos,
                policy_id=priv_policy,
                codes=priv,
                lot_size=lot_size,
                scores=scores,
                buy_ok=buy_ok,
                sell_ok=sell_ok,
                sell_scores=sell_scores,
            )
        )
    return _coalesce_orders(out)


def allocate_sleeve_orders(
    sleeve_dollars: float,
    closes: dict[str, float],
    pos: dict,
    *,
    policy_id: str,
    codes: list[str] | tuple[str, ...],
    lot_size: int = BOARD_LOT,
    scores: dict[str, float] | None = None,
    buy_ok: dict[str, bool] | None = None,
    sell_ok: dict[str, bool] | None = None,
    sell_scores: dict[str, float] | None = None,
    mix_lambda: float | None = None,
    dual_pub_codes: list[str] | tuple[str, ...] | None = None,
    dual_priv_codes: list[str] | tuple[str, ...] | None = None,
    dual_pub_policy: str = FIN_PRE_EXDIV_KD,
    dual_priv_policy: str = FIN_EQUAL,
) -> list[tuple[str, str, int]]:
    """Allocate one sleeve's trade dollars across member codes.

    Returns coalesced (code, side, qty) rows (board-lot).

    Stage C:
      - RS_SOFT_TILT: buy dollars soft-tilted by momentum scores; sells equal among holders
      - EXDIV_SKIP_BUY: buys only among buy_ok names; sells equal among holders
      - RS_SOFT_TILT_EXDIV: soft-tilt buys among buy_ok only
      - PRE_EXDIV_KD: Yahoo K9 season tilt + pre-ex T-10..ex skip-buy (same mechanics)
      - POST_EXDIV_KD: Yahoo K9 autumn post-ex season tilt + ex-day skip-buy
      - Optional ``sell_ok`` / ``sell_scores`` (paper): gate or soft-tilt sells on
        high-exit signals; empty sell_ok pool → skip sell (hold through)
    Mix:
      - MIX_EQUAL_RS_EXDIV: λ·EQUAL + (1−λ)·RS_SOFT_TILT_EXDIV notionals
      - MIX_EQUAL_PRE_EXDIV_KD: λ·EQUAL + (1−λ)·PRE_EXDIV_KD notionals
        (same blend helper; KD scores + pre-ex buy_ok supplied by caller)
    Dual (paper):
      - DUAL_PUB_PRIV: mix_lambda = 金融公 share of Financial dollars; nested policies
    """
    names = list(codes)
    kind = policy_kind(policy_id)
    if kind == POLICY_DUAL_PUB_PRIV:
        if mix_lambda is None:
            raise ValueError("mix_lambda (pub_share) required for FIN_DUAL_PUB_PRIV")
        pub = list(dual_pub_codes or [])
        priv = list(dual_priv_codes or [])
        if not pub and not priv:
            raise ValueError("dual_pub_codes / dual_priv_codes required for FIN_DUAL_PUB_PRIV")
        return allocate_dual_pub_priv(
            sleeve_dollars,
            closes,
            pos,
            pub_codes=pub,
            priv_codes=priv,
            pub_share=float(mix_lambda),
            lot_size=lot_size,
            scores=scores,
            buy_ok=buy_ok,
            sell_ok=sell_ok,
            sell_scores=sell_scores,
            pub_policy=dual_pub_policy,
            priv_policy=dual_priv_policy,
        )
    if kind in (POLICY_MIX_EQUAL_RS_EXDIV, POLICY_MIX_EQUAL_PRE_EXDIV_KD):
        lam = 0.5 if mix_lambda is None else float(mix_lambda)
        return allocate_mix_equal_rs_exdiv(
            sleeve_dollars,
            closes,
            pos,
            codes=names,
            lot_size=lot_size,
            scores=scores,
            buy_ok=buy_ok,
            sell_ok=sell_ok,
            sell_scores=sell_scores,
            mix_lambda=lam,
        )
    if kind == POLICY_EQUAL:
        return allocate_equal_notional(names, sleeve_dollars, closes, pos, lot_size=lot_size)

    score_map = _score_map(names, scores)

    # --- Stage C: per-name timing (ex-div / RS) ---
    if kind in (
        POLICY_RS_SOFT_TILT,
        POLICY_EXDIV_SKIP_BUY,
        POLICY_RS_SOFT_TILT_EXDIV,
        POLICY_PRE_EXDIV_KD,
        POLICY_POST_EXDIV_KD,
    ):
        if abs(sleeve_dollars) < 1e-9:
            return []
        if sleeve_dollars < 0:
            holders = [c for c in names if held_board_qty(pos, c, lot_size) > 0]
            if sell_ok is not None:
                holders = [c for c in holders if bool(sell_ok.get(c, False))]
                if not holders:
                    return []  # refuse sell when no high-exit name
            if sell_scores is not None and holders:
                sell_map = _score_map(holders, sell_scores)
                w = soft_tilt_weights(holders, sell_map)
                return allocate_weighted_notional(
                    holders, sleeve_dollars, closes, pos, w, lot_size=lot_size
                )
            return allocate_equal_notional(
                holders or names, sleeve_dollars, closes, pos, lot_size=lot_size
            )
        eligible = (
            _buy_eligible(names, buy_ok)
            if kind
            in (
                POLICY_EXDIV_SKIP_BUY,
                POLICY_RS_SOFT_TILT_EXDIV,
                POLICY_PRE_EXDIV_KD,
                POLICY_POST_EXDIV_KD,
            )
            else list(names)
        )
        if not eligible:
            return []
        if kind == POLICY_EXDIV_SKIP_BUY:
            return allocate_equal_notional(
                eligible, sleeve_dollars, closes, pos, lot_size=lot_size
            )
        w = soft_tilt_weights(eligible, score_map)
        return allocate_weighted_notional(
            eligible, sleeve_dollars, closes, pos, w, lot_size=lot_size
        )

    out: list[tuple[str, str, int]] = []
    if kind == POLICY_TOP1:
        active = [max(names, key=lambda c: (score_map[c], -float(closes[c]), c))]
    elif kind == POLICY_TOP2_EQUAL:
        active = sorted(names, key=lambda c: (score_map[c], -float(closes[c]), c), reverse=True)[:2]
    elif kind in (POLICY_MIN_LOT_PACK, POLICY_SCORE_LOT_PACK, POLICY_DIVERSIFY_PACK):
        active = None
    else:
        raise ValueError(f"unsupported policy kind: {kind}")

    if active is not None:
        for c in names:
            if c in active:
                continue
            q = held_board_qty(pos, c, lot_size)
            if q >= (1 if lot_size == 1 else lot_size):
                out.append((c, "SELL", int(q)))

    if abs(sleeve_dollars) < 1e-9:
        return _coalesce_orders(out)

    if sleeve_dollars < 0:
        holders = [c for c in names if held_board_qty(pos, c, lot_size) > 0]
        sell_pool = [c for c in (active or holders) if c in holders] or holders
        out.extend(
            allocate_equal_notional(sell_pool, sleeve_dollars, closes, pos, lot_size=lot_size)
        )
        return _coalesce_orders(out)

    if kind in (POLICY_TOP1, POLICY_TOP2_EQUAL):
        out.extend(
            allocate_equal_notional(active, sleeve_dollars, closes, pos, lot_size=lot_size)
        )
        return _coalesce_orders(out)

    if kind == POLICY_SCORE_LOT_PACK:
        order_names = sorted(names, key=lambda c: (score_map[c], -float(closes[c]), c), reverse=True)
        out.extend(
            _pack_one_lot_then_dump(
                names, sleeve_dollars, closes, lot_size=lot_size, order_names=order_names, dump_equal=False
            )
        )
        return _coalesce_orders(out)

    if kind == POLICY_DIVERSIFY_PACK:
        order_names = sorted(names, key=lambda c: (float(closes[c]), c))
        out.extend(
            _pack_one_lot_then_dump(
                names, sleeve_dollars, closes, lot_size=lot_size, order_names=order_names, dump_equal=True
            )
        )
        return _coalesce_orders(out)

    # MIN_LOT_PACK (cheapest-first)
    order_names = sorted(names, key=lambda c: (float(closes[c]), c))
    out.extend(
        _pack_one_lot_then_dump(
            names, sleeve_dollars, closes, lot_size=lot_size, order_names=order_names, dump_equal=False
        )
    )
    return _coalesce_orders(out)


def build_exdiv_buy_ok(
    calendar_index,
    dividends,
    codes: list[str] | tuple[str, ...],
    *,
    also_stock_ex: bool = True,
):
    """Boolean panel (date × code): False on cash/stock ex-date → skip buy that name.

    Causal: ex-date is known by open of ex-date (TW listing convention). Signal day
    uses today's mask; fill is T+1 — skip-buy applies when the *signal* day is an
    ex-date for that name (avoid initiating buys into ex-day gap).
    """
    import pandas as pd

    idx = pd.DatetimeIndex(pd.to_datetime(calendar_index)).sort_values().unique()
    names = list(codes)
    ok = pd.DataFrame(True, index=idx, columns=names)
    if dividends is None or len(dividends) == 0:
        return ok
    d = dividends.copy()
    d["code"] = d["code"].astype(str)
    cols = ["cash_ex_date"] + (["stock_ex_date"] if also_stock_ex else [])
    for c in names:
        sub = d[d["code"] == c]
        for col in cols:
            if col not in sub.columns:
                continue
            dates = pd.to_datetime(sub[col], errors="coerce").dropna()
            for dt in dates:
                if dt in ok.index:
                    ok.loc[dt, c] = False
    return ok


def build_pre_exdiv_window_buy_ok(
    calendar_index,
    dividends,
    codes: list[str] | tuple[str, ...],
    *,
    pre_days: int = 10,
    also_stock_ex: bool = True,
):
    """Skip buy on cash-ex T-``pre_days``..T0 (and stock ex-date).

    Extends ex-date skip into the pre-ex local-high window from the KD probe.
    """
    import pandas as pd

    if pre_days < 0:
        raise ValueError("pre_days must be >= 0")
    idx = pd.DatetimeIndex(pd.to_datetime(calendar_index)).sort_values().unique()
    names = list(codes)
    ok = pd.DataFrame(True, index=idx, columns=names)
    if dividends is None or len(dividends) == 0:
        return ok
    pos = {dt: i for i, dt in enumerate(idx)}
    d = dividends.copy()
    d["code"] = d["code"].astype(str)
    for c in names:
        sub = d[d["code"] == c]
        cash = pd.to_datetime(sub.get("cash_ex_date"), errors="coerce").dropna()
        for ex0 in cash:
            # first calendar session on/after listed ex-date
            later = idx[idx >= pd.Timestamp(ex0)]
            if len(later) == 0:
                continue
            ex = later[0]
            i_ex = pos[ex]
            lo = max(0, i_ex - int(pre_days))
            for i in range(lo, i_ex + 1):
                ok.iat[i, ok.columns.get_loc(c)] = False
        if also_stock_ex and "stock_ex_date" in sub.columns:
            stock = pd.to_datetime(sub["stock_ex_date"], errors="coerce").dropna()
            for dt in stock:
                if dt in ok.index:
                    ok.loc[dt, c] = False
    return ok


def build_kd_season_tilt_scores(
    market,
    dividends,
    codes: list[str] | tuple[str, ...],
    *,
    k_thresh: float = 25.0,
    season_start: tuple[int, int] = (5, 15),
    season_end: tuple[int, int] = (6, 10),
    pre_days: int = 10,
    active_score: float = 1.5,
):
    """Yahoo K9 season accumulation scores for ``FIN_PRE_EXDIV_KD``.

    Per name/year: first day in [May15, Jun10] with K9 < ``k_thresh`` starts
    accumulation until the day before cash-ex T-``pre_days`` (pre-ex skip window).
    Score = ``active_score`` while accumulating, else 0 (soft-tilt → near-equal).
    """
    import pandas as pd
    from tw_yahoo_kd import yahoo_kd

    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    m["code"] = m["code"].astype(str)
    for col in ("high", "low", "close"):
        m[col] = pd.to_numeric(m[col], errors="coerce")

    cal = pd.DatetimeIndex(m["date"].drop_duplicates().sort_values())
    names = list(codes)
    scores = pd.DataFrame(0.0, index=cal, columns=names)

    d = dividends.copy() if dividends is not None and len(dividends) else pd.DataFrame()
    if len(d):
        d["code"] = d["code"].astype(str)
        d["cash_ex_date"] = pd.to_datetime(d["cash_ex_date"], errors="coerce")

    pos = {dt: i for i, dt in enumerate(cal)}
    for c in names:
        g = m[m["code"] == c].sort_values("date").drop_duplicates("date").set_index("date")
        if g.empty:
            continue
        kd = yahoo_kd(g["high"], g["low"], g["close"], n=9)
        k = kd["k"].reindex(cal)
        ex_list = []
        if len(d):
            ex_list = sorted(
                pd.to_datetime(d.loc[d["code"] == c, "cash_ex_date"], errors="coerce")
                .dropna()
                .unique()
            )
        # map each season year → next cash ex on/after season start
        years = sorted({dt.year for dt in cal})
        for year in years:
            start = pd.Timestamp(year, season_start[0], season_start[1])
            end = pd.Timestamp(year, season_end[0], season_end[1])
            # cash ex after season start (typical Aug FIN ex)
            ex = None
            for ex0 in ex_list:
                if pd.Timestamp(ex0) >= start:
                    later = cal[cal >= pd.Timestamp(ex0)]
                    if len(later):
                        ex = later[0]
                        break
            if ex is None:
                continue
            i_ex = pos[ex]
            i_pre0 = max(0, i_ex - int(pre_days))  # first skip day T-pre_days
            # season mask for K trigger
            season_mask = (cal >= start) & (cal <= end) & (cal < ex)
            if not bool(season_mask.any()):
                continue
            seg = k.loc[season_mask]
            hit = seg[seg < float(k_thresh)].dropna()
            if hit.empty:
                continue
            sig = hit.index[0]
            i_sig = pos[sig]
            # accumulate sig .. day before pre-ex window
            i_end = i_pre0 - 1
            if i_end < i_sig:
                continue
            scores.iloc[i_sig : i_end + 1, scores.columns.get_loc(c)] = float(active_score)
    return scores


def build_kd_post_exdiv_season_tilt_scores(
    market,
    dividends,
    codes: list[str] | tuple[str, ...],
    *,
    k_thresh: float = 25.0,
    season_start: tuple[int, int] = (10, 20),
    season_end: tuple[int, int] = (12, 10),
    active_score: float = 1.5,
    hold_days: int = 40,
):
    """Yahoo K9 autumn post-ex accumulation for ``FIN_POST_EXDIV_KD``.

    Per name/year: require a cash-ex **before** the autumn window; then first day
    in [Oct20, Dec10] (after ex) with K9 < ``k_thresh`` starts soft-tilt
    accumulation for up to ``hold_days`` sessions (capped at season_end).
    """
    import pandas as pd
    from tw_yahoo_kd import yahoo_kd

    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    m["code"] = m["code"].astype(str)
    for col in ("high", "low", "close"):
        m[col] = pd.to_numeric(m[col], errors="coerce")

    cal = pd.DatetimeIndex(m["date"].drop_duplicates().sort_values())
    names = list(codes)
    scores = pd.DataFrame(0.0, index=cal, columns=names)

    d = dividends.copy() if dividends is not None and len(dividends) else pd.DataFrame()
    if len(d):
        d["code"] = d["code"].astype(str)
        d["cash_ex_date"] = pd.to_datetime(d["cash_ex_date"], errors="coerce")

    pos = {dt: i for i, dt in enumerate(cal)}
    for c in names:
        g = m[m["code"] == c].sort_values("date").drop_duplicates("date").set_index("date")
        if g.empty:
            continue
        kd = yahoo_kd(g["high"], g["low"], g["close"], n=9)
        k = kd["k"].reindex(cal)
        ex_list = []
        if len(d):
            ex_list = sorted(
                pd.to_datetime(d.loc[d["code"] == c, "cash_ex_date"], errors="coerce")
                .dropna()
                .unique()
            )
        years = sorted({dt.year for dt in cal})
        for year in years:
            start = pd.Timestamp(year, season_start[0], season_start[1])
            end = pd.Timestamp(year, season_end[0], season_end[1])
            # last cash ex strictly before season end, preferably before/at season start
            ex = None
            for ex0 in reversed(ex_list):
                if pd.Timestamp(ex0) < end:
                    later = cal[cal >= pd.Timestamp(ex0)]
                    if len(later) and later[0] < end:
                        ex = later[0]
                        break
            if ex is None or ex >= end:
                continue
            # autumn window starts at max(season_start, day after ex)
            win_start = max(start, ex + pd.Timedelta(days=1))
            # align win_start to calendar
            later = cal[cal >= win_start]
            if len(later) == 0:
                continue
            win_start = later[0]
            if win_start > end:
                continue
            season_mask = (cal >= win_start) & (cal <= end)
            if not bool(season_mask.any()):
                continue
            seg = k.loc[season_mask]
            hit = seg[seg < float(k_thresh)].dropna()
            if hit.empty:
                continue
            sig = hit.index[0]
            i_sig = pos[sig]
            i_end_cap = pos.get(end)
            if i_end_cap is None:
                # last calendar day on/before season end
                before = cal[cal <= end]
                if len(before) == 0:
                    continue
                i_end_cap = pos[before[-1]]
            i_end = min(i_sig + int(hold_days) - 1, i_end_cap)
            if i_end < i_sig:
                continue
            scores.iloc[i_sig : i_end + 1, scores.columns.get_loc(c)] = float(active_score)
    return scores


def build_name_scores(market, codes: list[str] | tuple[str, ...]):
    """Causal within-sleeve name scores from adj_close momentum (TOP1/TOP2)."""
    import numpy as np
    import pandas as pd

    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    adj = (
        m.pivot(index="date", columns="code", values="adj_close")
        .sort_index()
        .ffill()
    )
    for c in codes:
        if c not in adj.columns:
            raise ValueError(f"missing code {c} in market adj_close")
    panel = adj[list(codes)]
    rets = panel.pct_change()
    m20 = rets.rolling(20, min_periods=10).mean()
    m60 = rets.rolling(60, min_periods=20).mean()

    def _xz(df: pd.DataFrame) -> pd.DataFrame:
        mu = df.mean(axis=1)
        sd = df.std(axis=1).replace(0.0, np.nan)
        return df.sub(mu, axis=0).div(sd, axis=0).fillna(0.0)


    return (0.5 * _xz(m20) + 0.5 * _xz(m60)).clip(-3.0, 3.0)


__all__ = [
    "POLICY_EQUAL",
    "POLICY_MIN_LOT_PACK",
    "POLICY_SCORE_LOT_PACK",
    "POLICY_DIVERSIFY_PACK",
    "POLICY_TOP1",
    "POLICY_TOP2_EQUAL",
    "POLICY_RS_SOFT_TILT",
    "POLICY_EXDIV_SKIP_BUY",
    "POLICY_RS_SOFT_TILT_EXDIV",
    "POLICY_MIX_EQUAL_RS_EXDIV",
    "POLICY_MIX_EQUAL_PRE_EXDIV_KD",
    "POLICY_PRE_EXDIV_KD",
    "POLICY_POST_EXDIV_KD",
    "FIN_EQUAL",
    "FIN_MIN_LOT_PACK",
    "FIN_TOP1",
    "FIN_TOP2_EQUAL",
    "FIN_RS_SOFT_TILT",
    "FIN_EXDIV_SKIP_BUY",
    "FIN_RS_SOFT_TILT_EXDIV",
    "FIN_MIX_EQUAL_RS_EXDIV",
    "FIN_MIX_EQUAL_PRE_EXDIV_KD",
    "FIN_PRE_EXDIV_KD",
    "FIN_POST_EXDIV_KD",
    "FIN_ALLOC_POLICIES",
    "TEL_EQUAL",
    "TEL_MIN_LOT_PACK",
    "TEL_SCORE_LOT_PACK",
    "TEL_DIVERSIFY_PACK",
    "TEL_TOP1",
    "TEL_TOP2_EQUAL",
    "TEL_RS_SOFT_TILT",
    "TEL_EXDIV_SKIP_BUY",
    "TEL_RS_SOFT_TILT_EXDIV",
    "TEL_MIX_EQUAL_RS_EXDIV",
    "TEL_PRE_EXDIV_KD",
    "TEL_MIX_EQUAL_PRE_EXDIV_KD",
    "TEL_ALLOC_POLICIES",
    "policy_kind",
    "held_board_qty",
    "lot_qty_from_notional",
    "allocate_equal_notional",
    "allocate_weighted_notional",
    "allocate_mix_equal_rs_exdiv",
    "soft_tilt_weights",
    "allocate_sleeve_orders",
    "build_name_scores",
    "build_exdiv_buy_ok",
    "build_pre_exdiv_window_buy_ok",
    "build_kd_season_tilt_scores",
    "build_kd_post_exdiv_season_tilt_scores",
]
