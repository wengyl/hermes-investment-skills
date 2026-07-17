# Stop-Loss Backtest Reference

## Stop-Loss Comparison (2026-06-04)

Backtested user's 9 funds, last year (2025-06-04 ~ 2026-06-02, 243 trading days, 100K initial):

| Strategy | Total Return | Annualized | Max Drawdown | Sharpe | Trades |
|----------|-------------|------------|-------------|--------|--------|
| **Pure holding (control)** | **+21.87%** | +11.04% | 3.50% | **0.53** | 0 |
| Stop-loss -8% / TP +20% | +14.17% | +0.67% | **1.01%** | -0.17 | 8 |
| Stop-loss -10% / TP +20% | +14.12% | +0.61% | 1.04% | -0.17 | 7 |
| Stop-loss -12% / TP +20% | +14.43% | +1.02% | 1.03% | -0.14 | 7 |
| Stop-loss -15% / TP +20% | +14.43% | +1.02% | 1.03% | -0.14 | 7 |
| Stop-loss -20% / TP +20% | +14.43% | +1.02% | 1.03% | -0.14 | 7 |
| **Dynamic SL (base -12%, bearish → -18%)** | **+21.67%** | +10.78% | 3.29% | **0.52** | 1 |

### Key Findings

1. All fixed stop-loss strategies underperform pure holding by ~7%
2. Capital sits idle after premature exit — no re-entry mechanism
3. Stop-loss -8% triggers on 005165 (富荣福锦) at -11%, but it recovers to +21% by September
4. Only 027063 (鹏华创新, -34%) is truly broken — ALL stop-loss levels catch it
5. 014414 (招商畜牧) at -8.6% triggers only at -8% level — it's cyclical normal volatility

### Dynamic Stop-Loss Logic

```python
class DynamicStopLossStrategy(BacktestStrategy):
    def __init__(self, base_stop_loss=-0.12):
        self.base_stop_loss = base_stop_loss
    
    def should_sell(self, ...):
        sentiment = self._calc_sentiment(fund_code, current_price)  # 20-day momentum → 0-100
        
        if sentiment < 30:  # bearish
            dynamic_sl = self.base_stop_loss * 1.5  # widen to -18%
        else:
            dynamic_sl = self.base_stop_loss  # normal -12%
        
        if profit_pct <= dynamic_sl:
            return True, f"止损({label})"
```

### Recommendation

- Set stop-loss at **-20%** as safety net, or use **dynamic approach**
- Daily -8%~15% swings are normal breathing room for funds
- Use multi-factor risk scoring (adaptive_risk_v2.py) instead of single threshold
- Script: `scripts/backtest_stop_loss.py`

### Trade Details (Stop-loss -8%)

| Date | Fund | Action | Reason |
|------|------|--------|--------|
| 2025-06-18 | 002112 | Sell | TP: +21.1% |
| 2025-06-20 | 005165 | Sell | SL: -11.0% ← recovered later! |
| 2025-07-15 | 020692 | Sell | TP: +23.5% |
| 2025-07-21 | 501205 | Sell | TP: +20.1% |
| 2025-09-09 | 022184 | Sell | TP: +20.6% |
| 2026-02-12 | 026211 | Sell | TP: +21.0% |
| 2026-03-27 | 027063 | Sell | SL: -34.1% |
| 2026-05-27 | 014414 | Sell | SL: -8.6% ← cyclical normal |
