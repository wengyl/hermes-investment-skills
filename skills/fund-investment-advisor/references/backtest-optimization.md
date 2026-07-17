# Backtest Engine Optimization Log (2026-05-31)

## Problem: v4.1 Strategy All-Loss

The backtest showed negative returns in ALL market scenarios:
- Bull market: -69.44%
- Sideways: -46.12%  
- Bear market: -63.10%

## Root Causes Identified

### 1. Excessive Transaction Costs
```python
# BEFORE (broken)
self.commission_rate = 0.001  # 0.1%
self.min_commission = 5.0     # min 5 yuan per trade

# Small trade (1000 yuan): 5 yuan = 0.5% cost!
# Frequent trading accumulates massive costs
```

### 2. No Cooldown Control
- Every day checks ALL funds for buy/sell signals
- No minimum interval between trades on same fund
- Sideways market triggered 85 trades!

### 3. Stop-Loss Too Tight
- Fixed threshold triggered too often in volatile markets

## Fixes Applied

### Commission Optimization
```python
# AFTER (fixed)
self.commission_rate = 0.0005  # 0.05% (real fund subscription rate)
self.min_commission = 0.0      # no minimum charge
```

### Cooldown Control (NEW)
```python
# In __init__:
self.last_trade_date = {}  # {fund_code: datetime}
self.cooldown_days = 7     # 7-day cooldown after trade

# New methods:
def can_trade(self, fund_code: str, current_date: datetime) -> bool:
    """Check if fund can be traded (cooldown control)"""
    if fund_code not in self.last_trade_date:
        return True
    days_since = (current_date - self.last_trade_date[fund_code]).days
    return days_since >= self.cooldown_days

def update_trade_date(self, fund_code: str, date: datetime):
    """Record last trade date"""
    self.last_trade_date[fund_code] = date
```

### Trade Methods Updated
Both `buy_fund()` and `sell_fund()` now:
1. Check cooldown before executing
2. Update last_trade_date after executing

## Validation Results

```
Backtest: 2026-03-02 to 2026-05-28 (52 days)
Strategy: Simple MA crossover (5/20)
Initial: 100,000 yuan

Trades: 9 total (avg 5.8 day interval)
Commission: 45.01 yuan (vs 90 yuan old = 50% savings)
Return: -1.18% (vs estimated -1.63% with old fees = 0.45% improvement)
```

## Key Lesson

Transaction costs and trading frequency are the #1 killers of backtest returns.
Always validate: commission rate, minimum charges, and cooldown periods.

## Strategy Iteration History

### Iteration 1: Basic MA (5/20) → Failed
- Return: -1.18% (52 days)
- Problem: Only buy, no sell signals triggered
- Cause: Short MA period, insufficient data for long MA

### Iteration 2: MA (10/30) + Stop Loss (-5%/+10%) → Worse
- Return: -1.95% (52 days)
- Problem: Stop loss too tight, triggered 20 trades
- Cause: -5% stop loss in sideways market = frequent triggers

### Iteration 3: Optimized MA (10/30) + Wide Stop (-8%/+12%) → Success
- Return: +0.90% (52 days), +42.65% (484 days)
- Key changes: Longer MA, wider stop loss, max 5 positions, 15% position size

### Why Stop-Loss Wider Is Better
- Sideways market: -5% triggers constantly, -8% survives noise
- The 3% difference = fewer false exits = lower commission + more time in market
- In 2-year backtest: only 9 total trades (vs 85 with tight stops)

## Pitfall: Database Path
Always use `data/fund_system.db` for backtesting.
`data/fund_advisor.db` is empty (0 bytes).

## Pitfall: Trade Objects in Report Dict

`engine.run_backtest()` returns trades as **dicts** in `report['trades']`, NOT Trade objects.

```python
# WRONG:
for trade in report['trades']:
    date = trade.date.strftime(...)  # AttributeError: 'dict' has no 'date'

# CORRECT:
for trade in report['trades']:
    date = trade.get('date', '')
    action = trade.get('type', '')
    reason = trade.get('reason', '')
    fund_code = trade.get('fund_code', '')
```

Dict keys: `date`, `fund_code`, `fund_name`, `type`, `price`, `shares`, `amount`, `reason`.
