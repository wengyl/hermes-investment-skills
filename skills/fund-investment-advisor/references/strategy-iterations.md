# Strategy Iterations Record

Historical record of strategy optimization experiments. See also `backtest-engine.md` for the final optimized strategy.

## Iteration History

### Iter 1: Basic MA Strategy (5/20 day)
- Return: -1.18%
- Trades: 9 (all buys, 0 sells)
- Problem: MA period too short, sell conditions never triggered

### Iter 2: Improved MA (10/30 + stop-loss/take-profit)
- Return: -1.95%
- Trades: 20 (12 buy, 8 sell)
- Stop-loss: -5%, Take-profit: +10%
- Problem: Stop-loss too tight, triggered frequently in choppy market

### Iter 3: Optimized (20/60 + market sentiment filter)
- Return: 0.00% (no trades)
- Problem: MA period too long, 52-day data insufficient for 60-day MA

### Iter 4: Adjusted (10/30 + relaxed stop-loss) ✅ Best
- Return: +0.90%
- Annualized: +6.51%
- Trades: 8
- Stop-loss: -8%, Take-profit: +12%
- Max positions: 5

## Key Findings

### Stop-Loss Sensitivity
| Stop-Loss | Return | Trades | Notes |
|-----------|--------|--------|-------|
| -5% | -1.95% | 20 | Too tight, frequent triggers |
| -8% | +0.90% | 8 | Optimal |
| -10% | TBD | - | May be better |

### MA Period Sensitivity
| Period | Return | Notes |
|--------|--------|-------|
| 5/20 | -1.18% | Too short, frequent trades |
| 10/30 | +0.90% | Optimal |
| 20/60 | 0.00% | Too long, insufficient data |

### Commission Impact
- Old: 0.1% + min 5 yuan → New: 0.05% + no minimum
- 52-day backtest savings: 44.99 yuan (50%)

## Lessons Learned

1. **Stop-loss must not be too tight** — -5% triggers frequently in choppy markets, -8% works better
2. **MA period must be moderate** — 5/20 too short (frequent trades), 20/60 too long (insufficient data), 10/30 optimal
3. **Cooldown period is essential** — Without cooldown, frequent trades accumulate commissions
4. **Position sizing matters** — Limit max positions (5) to reduce risk
5. **Data quantity determines backtest quality** — 52 days only validates short-term, 2 years needed for bull/bear coverage
6. **Commission settings must be realistic** — Fund subscription rate is 0.05%, not stock's 0.1%, minimum should be 0
7. **Check database path first** — fund_advisor.db (empty) vs fund_system.db (actual data), wrong path causes `no such table`
