# Alpha 3A — Feature Set Stop

Date: 2026-09-04  
Feature set: `z(oi_yoy) - z(amihud_20_lag1)` monthly top-20%  
Adversarial-lite: `repro/alpha3a-adversarial-lite-20260904/`

## Decision: `STOP_THIS_FEATURE_SET`

| Check | Result |
|---|---|
| Dev 2019–2024 gross excess | Slightly positive historically but fragile |
| Dev **net 40 bps** mean excess | **−0.15%/month** → fail |
| Consec neg / LOYO / cuts | Gates fail with cost |
| Sealed 2025+ net40 | Positive — **ignored for PASS** (dev failed first) |

## Binding rules (no cheating)

1. **Do not retune** this score (weights, top_k, amihud window) after seeing adversarial results.  
2. Next 3A attempt requires a **new feature family** (charter menu item not yet used, or external PIT-safe data).  
3. **No promotion**, no paper sleeve from this set.  
4. Old-panel TECH2/S9A1 remains forbidden (3B).

## Research posture after this stop

- Official path unchanged: **E22_v2** + core; E45 **B**; no hedge.  
- 3A track: **paused until new features**, not abandoned as a class.  
- Highest EV ops work remains running E22_v2 cleanly.
