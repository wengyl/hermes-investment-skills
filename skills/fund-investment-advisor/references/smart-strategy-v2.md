# Smart Strategy Engine v2.0 - Implementation Reference

## Architecture

```
smart_strategy.py
├── FundType (enum) - 8 fund type classifications
├── MarketEnv (enum) - bull/bear/shock
├── StrategySignal (dataclass) - action/urgency/reason/amount/detail
└── SmartStrategyEngine
    ├── FUND_PARAMS - per-type stop-profit/loss parameters
    ├── MARKET_ADJUST - environment adjustment multipliers
    ├── FUND_TYPE_MAP - code→type mapping
    ├── analyze_fund() - main analysis entry point
    └── format_signal() - human-readable output
```

## Signal Priority (highest to lowest)

1. **STOP_LOSS** - Hard stop (loss > threshold)
2. **TRAILING_STOP** - Drawdown from high (profitable + drawdown > threshold)
3. **TAKE_PROFIT** / **REDUCE** - Tiered stop-profit (finds HIGHEST matching tier)
4. **WARNING** - Approaching stop-loss line
5. **ALERT** - Weekly drop > 5%
6. **HOLD_TRAIL** - Long-term profitable hold
7. **HOLD** - Default

## Critical Bug: Tiered Stop-Profit Must Find Highest Match

```python
# WRONG (returns first match):
for threshold, sell_pct in levels:
    if profit >= threshold:
        return REDUCE  # 25% tier returned even when profit is 70%!

# CORRECT (finds highest match):
matched = None
for threshold, sell_pct in levels:
    if profit >= threshold:
        matched = (threshold, sell_pct)
if matched:
    threshold, sell_pct = matched
    ...
```

## Market Environment Adjustments

| Environment | Trailing Stop Multiplier | Hard Stop Multiplier | Reduce Threshold |
|-------------|-------------------------|---------------------|------------------|
| BULL | 1.3x (relaxed) | 1.2x | 0.7x (higher bar) |
| BEAR | 0.8x (tighter) | 0.8x | 1.3x (lower bar) |
| SHOCK | 1.0x | 1.0x | 1.0x |

## Fund Type Classification

```python
FUND_TYPE_MAP = {
    '002112': FundType.FLEXIBLE,      # 德邦鑫星
    '005165': FundType.FLEXIBLE,      # 富荣福锦
    '014414': FundType.INDUSTRY_ETF,  # 招商畜牧
    '018388': FundType.DIVIDEND,      # 华泰港股红利
    '020692': FundType.INDUSTRY_ETF,  # 博时通信设备
    '022184': FundType.HK_GLOBAL,     # 富国全球科技
    '026211': FundType.TECH_FUND,     # 平安科技
    '027063': FundType.INNOVATION,    # 鹏华创新
    '501205': FundType.INNOVATION,    # 鹏华创新未来
}
```

## Testing

Run: `cd ~/.hermes/fund-advisor/scripts && python3 test_system.py`
21 tests, all should pass.
