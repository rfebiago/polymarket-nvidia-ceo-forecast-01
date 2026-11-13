# Polymarket NVIDIA CEO forecast — make.fun entry

Forecasts the Yes price of every market of Polymarket's "Next CEO of
NVIDIA?" event, minute by minute, 4 hours ahead, as five quantiles
(5/25/50/75/95%), for the bounty
`polymarket-nvidia-ceo-forecast-01` ($250, deadline 2026-11-13 21:00 UTC).

## Entry

- `main.py` — the program (Python 3.13, standard library only, no network,
  no model calls, deterministic). Reads every `<id>.in` in
  `$MAKEFUN_INPUT_DIR` (else `/input`) and writes `<id>.out` to
  `$MAKEFUN_OUTPUT_DIR` (else `/output`).
- `LICENSE` — MIT (copied from the kit's starter, as the kit instructs).

Only `main.py` + `LICENSE` (+ this README) go into the public GitHub repo.
`kit/` (downloaded bounty kit) and `eval/` (local evaluation harness) are
build-time scratch, not part of the submission.

## Model

Per market, with `x0` the last price and `h = 1..240` minutes ahead:

- **Median: persistence**, `q50(h) = x0`. Prediction-market prices are
  close to a martingale; drift, EWMA mean-reversion and snap-back variants
  all made the practice median worse.
- **Spread:** `q_tau(h) = clamp(x0 + z_tau * sigma * h**0.45, 0, 1)` where
  `z_tau` are Student-t(4) quantiles (fat tails: prices sit still, then
  jump) and `sigma` is per-market recent volatility:
  `sigma = 0.0003 + 0.9 * mean|1-minute return|` over the last 360 minutes
  (or all history when shorter). The floor keeps never-moved markets from
  getting a zero-width forecast.
- Rows are clamped to [0, 1], sorted non-decreasing, rounded to 6 decimals.

## What was tried and rejected (practice cases)

- Full-history empirical multi-step change quantiles: much worse
  (0.58–0.78) — the 72 h history is full of one-off repricing jumps and
  market launches that do not repeat inside a 4 h window.
- Return standard deviation as sigma: far too wide (jump-dominated).
- EWMA mean-reversion / snap-back medians: worse median error.
- Sum-of-probabilities normalisation: no-op once the median is persistence.
- Asymmetric up/down tails: helped one case, hurt another — dropped.
- Level scaling `sqrt(p(1-p))`: within noise of the chosen model — dropped
  for simplicity.

## Practice evaluation (local, not the server grade)

Ground truth for the six practice cases was rebuilt from Polymarket's
public price history (`GET /clob.polymarket.com/prices-history`, fidelity
1 min), forward-filled onto the 1-minute grid exactly as the rules describe
(see `eval/build_answers.py`; raw fetches in `eval/future_prices.json`).
Mean pinball loss, percentage points:

| case | this entry | house baseline (σ=0.0025) |
|------|-----------|---------------------------|
| p00  | 0.4539    | 0.5361 |
| p01  | 0.3118    | 0.3804 |
| p02  | 0.3598    | 0.4084 |
| p03  | 0.2604    | 0.3686 |
| p04  | 0.2080    | 0.2988 |
| p05  | 0.1123    | 0.2382 |
| **overall** | **0.2739** | **0.3636** |

Median absolute error 0.77 pp; 90% coverage 0.891 (honest ≈ 0.90).
Per the bounty text the practice pays nothing and is no guide to the final,
which is scored on 12 unseen cases recorded after the deadline — but the
entry beats the house baseline by ~25% on practice, which is the bar a
prize needs (must also beat the house AI model and rank top 100 of 2,074
entries; that cannot be checked locally).

## Local verification (2026-11-13)

- Output shape: `{"forecasts": [{"id", "q": 240×5}]}` for every market in
  the case, exactly one key; all values finite, in [0, 1], non-decreasing.
- Output size 188–247 KB per case (limit 1,048,576 bytes).
- Runtime ≈ 0.10 s per case on this VM (limit 8 s, 1 CPU); peak RSS
  ≈ 11 MB (limit 1024 MB).
- Determinism: two runs on the same case are byte-identical.
- Edge cases pass: 1-price market, constant prices, all-0 / all-1 prices,
  very short history.
- No network / subprocess / non-stdlib use in `main.py` (grep-verified).

Run locally:

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=kit/input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## Still needed to submit (NOT done — needs Bosque)

1. **Bosque's GitHub username** — the repo must be created after the
   competition opened (2026-11-13 09:00 UTC) under his own GitHub account,
   public, OSI-approved license. No repo was created or pushed (username
   unknown; hard limit in the task).
2. **make.fun login / API key + wallet signature** — entry requires a
   make.fun account (Solana keypair = account/payout wallet) and a signed
   entry message; the escrow prize is claimed in USDC on Solana.
   Needs Bosque's approval/link flow — not done here.
3. **Transcripts** — the bundle tool needs this build session's log.
   This session is a Muse subagent session; the parent agent must run
   `bundle --dry-run` (and `--muse-usage` if required) from the kit CLI
   before submitting, and upload every session that worked on the entry.
4. Submit via the kit CLI / site before **2026-11-13 21:00 UTC**
   (04:00 WIB 2026-11-14). Max 10 submissions total; the last one before
   the deadline is the final entry.
