#!/usr/bin/env python3
"""Forecast Polymarket's "Next CEO of NVIDIA?" Yes prices, 4 hours ahead.

Reads every <id>.in case in the input directory (env MAKEFUN_INPUT_DIR,
else /input) and writes /output/<id>.out (env MAKEFUN_OUTPUT_DIR, else
/output): {"forecasts": [{"id": <conditionId>, "q": [[q05, q25, q50, q75,
q95] x 240 rows]}]}.

Method (per market, Python standard library only, deterministic, no
network, no model calls). Chosen on the six practice cases (see README.md):
  * Median: persistence -- the last price. Prediction-market prices are
    close to a martingale, and every drift / mean-reversion / snap-back
    variant tried on the practice cases made the median worse.
  * Spread: q_tau(h) = clamp(x0 + z_tau * sigma * h**0.45, 0, 1), where
    z_tau are Student-t(4) quantiles (fatter tails than normal: prices sit
    still for minutes, then jump) and sigma is per-market, from the recent
    realised volatility:
        sigma = 0.0003 + 0.9 * mean|1-minute return| over the last 360 min
    The 0.0003 floor keeps a market that has not moved at all from getting
    a zero-width forecast; the 0.9 factor converts the jump-dominated mean
    absolute return into a scale the pinball loss likes (a plain return
    standard deviation is far too wide: history is full of one-off
    repricing jumps that do not repeat inside a 4-hour window).
  * Rows are clamped to [0, 1], sorted non-decreasing, rounded to 6 dp.
"""

import json
import math
import os
import sys

TAUS = (0.05, 0.25, 0.5, 0.75, 0.95)
# Student-t (df=4) quantiles at TAUS.
Z = (-2.13184678632665, -0.740697536529312, 0.0,
     0.740697536529312, 2.13184678632665)

# Mean absolute 1-minute return is measured over this many recent minutes.
VOL_WINDOW = 360
# sigma = VOL_FLOOR + VOL_K * mean|return|.
VOL_FLOOR = 0.0003
VOL_K = 0.9
# Spread grows like h ** ALPHA (0.45, slightly slower than a random walk's
# 0.5: realised 4-hour moves grow a touch slower than sqrt(h) here).
ALPHA = 0.45


def _sigma(prices):
    """Per-market 1-minute volatility scale from recent absolute returns."""
    n = len(prices)
    if n < 2:
        return VOL_FLOOR
    seg = prices[-VOL_WINDOW - 1:] if n > VOL_WINDOW + 1 else prices
    total = 0.0
    count = 0
    for i in range(len(seg) - 1):
        d = seg[i + 1] - seg[i]
        total += d if d >= 0 else -d
        count += 1
    if count == 0:
        return VOL_FLOOR
    return VOL_FLOOR + VOL_K * (total / count)


def _clean(v):
    v = min(1.0, max(0.0, v))
    r = round(v, 6)
    return 0.0 if r == 0 else r  # never -0.0


def forecast_market(prices, horizon):
    """Return `horizon` rows of 5 quantiles for one market's prices."""
    if not prices:
        raise ValueError("market has no prices")
    x0 = prices[-1]
    sigma = _sigma(prices)
    rows = []
    for h in range(1, horizon + 1):
        s = sigma * (h ** ALPHA)
        row = sorted(_clean(x0 + z * s) for z in Z)
        rows.append(row)
    return rows


def forecast_case(case):
    horizon = case["horizon_minutes"]
    forecasts = [
        {"id": m["id"], "q": forecast_market(m["prices"], horizon)}
        for m in case["markets"]
    ]
    return {"forecasts": forecasts}


def main():
    input_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(output_dir, exist_ok=True)
    files = sorted(f for f in os.listdir(input_dir) if f.endswith(".in"))
    if not files:
        print("no .in files in %s" % input_dir, file=sys.stderr)
        return 1
    for fname in files:
        case_id = fname[:-3]
        with open(os.path.join(input_dir, fname), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        out = forecast_case(case)
        data = json.dumps(out, separators=(",", ":")) + "\n"
        with open(os.path.join(output_dir, case_id + ".out"), "w",
                  encoding="utf-8") as fh:
            fh.write(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
