# Adaptive Risk Engine Backtesting

## Problem: Signal Noise

Initial adaptive risk engine generated 58 signals in 3 months (vs 7 for fixed threshold). Most were correct (86%) but too frequent.

**Root cause**: Evaluated every day, triggered whenever score was in "reduce" zone (40-55).

## Solution: 阈值触发 (Threshold Crossing Trigger)

Only trigger when score **crosses a zone boundary**.

```python
def get_zone(score):
    if score < 35: return 'sell'
    elif score < 50: return 'reduce'
    elif score < 65: return 'hold_watch'
    else: return 'hold'

# Only signal when zone changes
if get_zone(current_score) != get_zone(prev_score):
    triggered = True
```

## Results

| Metric | Fixed | Adaptive v1 (daily) | Adaptive v2 (threshold) |
|--------|-------|---------------------|------------------------|
| Signals | 7 | 58 | **10** |
| Accuracy | 86% | 86% | **90%** |

## v2 Scoring Rules

Weights: profit_loss=20%, industry_trend=20%, mainline=15%, nav_trend=20%, valuation=25%

Key changes from v1:
- Profit/Loss: 10-30% profit = 60分 (was 80). Avoid "sell when profitable"
- Valuation: Non-linear mapping, weight raised to 25% (was 15%)
- Industry: Removed +20 base score
- Mainline: Reduced weight (overlaps with industry)

## Lessons

1. Threshold crossing > daily evaluation (reduces noise 5x)
2. Valuation is most important — undervalued = hold even with losses
3. Profit alone shouldn't drive selling
4. Correlated factors need combined weight reduction
