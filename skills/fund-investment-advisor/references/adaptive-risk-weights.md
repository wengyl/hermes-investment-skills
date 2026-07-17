# Adaptive Risk Engine — Per-Fund Weight Profiles

## Design Rationale

Different fund types are driven by different factors. A one-size-fits-all weight scheme mis-scores funds:

- **科技基金** (020692, 026211, 027063, 501205): Trend is king. Tech stocks move on momentum and industry catalysts. Valuation matters less because growth premiums are justified. → Higher `nav_trend` (30%) and `industry_trend` (25%).

- **红利基金** (002112, 018388): Valuation is the anchor. Dividend stocks mean-revert; buying cheap is the primary edge. Trend signals are noisy for low-vol stocks. → Higher `valuation` (35%) and `profit_loss` (20%).

- **行业指数** (014414 畜牧): Sector cycles dominate. Pork prices, supply/demand, and industry heat matter most. → Higher `industry_trend` (30%) and `valuation` (20%).

- **港股/QDII** (022184): Valuation and cross-border capital flows. HK stocks are cheaper on average, so valuation percentile is more meaningful. → Higher `valuation` (30%) and `industry_trend` (25%).

- **灵活配置/默认** (005165): Balanced across all factors. → Default weights (20/20/25/20/15).

## Weight Matrix

| Factor | tech | dividend | industry | hk | default |
|--------|------|----------|----------|----|---------|
| profit_loss | 0.15 | 0.20 | 0.15 | 0.15 | 0.20 |
| industry_trend | 0.25 | 0.15 | 0.30 | 0.25 | 0.20 |
| mainline | 0.15 | 0.15 | 0.15 | 0.15 | 0.15 |
| nav_trend | 0.30 | 0.15 | 0.20 | 0.15 | 0.20 |
| valuation | 0.15 | 0.35 | 0.20 | 0.30 | 0.25 |

All rows sum to 1.00.

## Adding a New Fund

1. Determine the fund's category from `configs/fund_categories.yaml`
2. Map to a weight profile in `FUND_WEIGHT_MAP` in `adaptive_risk.py`
3. If no existing profile fits, add a new profile to `FUND_WEIGHT_PROFILES`

## Impact on Scoring

The same raw factor scores produce different weighted totals depending on profile:
- A fund with `nav_trend=60, valuation=25`:
  - As `tech`: 0.30×60 + 0.15×25 = 21.75 (trend-weighted)
  - As `dividend`: 0.15×60 + 0.35×25 = 17.75 (valuation-weighted)

This means the same market conditions can produce different risk signals for different fund types — which is the intended behavior.
