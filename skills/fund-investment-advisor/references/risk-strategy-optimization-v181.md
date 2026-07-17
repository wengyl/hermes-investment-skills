# Risk Strategy Optimization v1.8.1

## Overview

Unified trailing stop approach with volatility adaptation, valuation percentile, and concentration control.

## Key Files

- `scripts/smart_strategy_v4.py` - Unified trailing stop engine
- `scripts/adaptive_risk_v2.py` - Multi-factor risk control with v2.0 enhancements

## Smart Strategy v4.0 Changes

### Removed
- ❌ Fixed stop-profit tiers (25%/50%/80%)
- ❌ Market environment modes (bull/shock/bear)
- ❌ `MarketEnv` enum and `MARKET_ADJUST` dict

### Added
- ✅ `calculate_volatility_adjustment(nav_history)` - Returns 0.7-1.5 multiplier
- ✅ `calculate_valuation_adjustment(current_nav, nav_history)` - Returns 0.8-1.2 multiplier
- ✅ Portfolio concentration check (>20% warning, >30% reduce)
- ✅ `trigger_nav` field in StrategySignal (exact NAV that triggers stop)

### Formula
```python
final_threshold = base_threshold × volatility_adjustment × valuation_adjustment
# Clamped to 6%-25% range
```

### Volatility Adjustment Logic
```python
# Based on 30-day standard deviation of daily returns
volatility = statistics.stdev(returns)
adjustment = 0.8 + (volatility - 2) * 0.1
# volatility 2% → 0.9 (more sensitive)
# volatility 4% → 1.0 (baseline)
# volatility 6% → 1.1 (more tolerant)
# Clamped to 0.7-1.5
```

### Valuation Adjustment Logic
```python
# Based on percentile in historical range (90 days)
percentile = (current_nav - low) / (high - low) * 100
adjustment = 1.0 - (percentile - 50) * 0.003
# percentile 90% → 0.85 (more sensitive, high valuation risk)
# percentile 50% → 1.0 (baseline)
# percentile 10% → 1.15 (more tolerant, low valuation opportunity)
# Clamped to 0.85-1.15
```

## Adaptive Risk v2.0 Changes

### Added
- ✅ `calculate_volatility(nav)` - Returns volatility percentage
- ✅ `calculate_volatility_adjustment(nav)` - Adjusts profit/loss score
- ✅ `calculate_valuation_adjustment(current_nav, nav)` - Adjusts valuation score
- ✅ `calculate_concentration(fund_value, portfolio_total)` - Returns (%, level)
- ✅ Dynamic thresholds based on concentration level
- ✅ Fund-type-specific weight profiles

### Concentration Levels
```python
if concentration > 30:
    return concentration, 'critical'  # 严重集中
elif concentration > 20:
    return concentration, 'high'      # 高度集中
elif concentration > 15:
    return concentration, 'medium'    # 中度集中
else:
    return concentration, 'low'       # 正常
```

### Dynamic Threshold Adjustment
```python
if concentration_level == 'critical':
    hold_threshold = 70      # 更严格
    watch_threshold = 55
    reduce_threshold = 40
elif concentration_level == 'high':
    hold_threshold = 68
    watch_threshold = 53
    reduce_threshold = 38
else:
    hold_threshold = 65      # 默认
    watch_threshold = 50
    reduce_threshold = 35
```

## Integration Pattern

When updating report scripts to use new risk engines:

```python
# In advisor.py, morning_intraday.py, afternoon_intraday.py
from adaptive_risk_v2 import AdaptiveRiskEngine  # NOT adaptive_risk

# In __init__
self.risk_engine = AdaptiveRiskEngine(self.db_path)

# In report generation
results = self.risk_engine.analyze_all()
report.append(self.risk_engine.format_report(results))
```

## Backtest Results

### 020692 博时通信设备 (盈利87.5%)
- Base trailing stop: 10% (industry_etf)
- Volatility adjustment: 1.0 (volatility 3.9%)
- Valuation adjustment: 0.69 (percentile 86.7%)
- Final threshold: 6.9%
- Trigger NAV: 3.6682 (from high 3.9444)
- Current NAV: 3.8819 (drawdown -1.58%, NOT triggered)

### Key Insight
High valuation (86.7% percentile) significantly reduces trailing stop threshold, making the strategy more sensitive to pullbacks. This prevents holding through large corrections in overvalued positions.

## Migration Notes

### From v3.0 to v4.0
1. Remove `MarketEnv` import and usage
2. Remove `market_env` parameter from `SmartStrategyEngine()`
3. Add `nav_history`, `portfolio_total`, `fund_value` to `analyze_fund()` calls
4. Update signal handling: `TAKE_PROFIT` and `REDUCE` no longer generated

### From adaptive_risk v1.0 to v2.0
1. Update import: `from adaptive_risk_v2 import AdaptiveRiskEngine`
2. Add `portfolio_total` parameter to `analyze_fund()` if called directly
3. Update report parsing: new fields `volatility`, `concentration`, `concentration_level`
