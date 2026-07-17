# Backtest Engine Reference

## OptimizedMAStrategy (integrated 2026-05-31)

Strategy parameters:
- Short MA: 10 days
- Long MA: 30 days
- Stop loss: -8%
- Take profit: +12%
- Max positions: 5 funds
- Position size: 15% of total value

Performance (2024-06 to 2026-05, 484 trading days):
- Total return: +42.65%
- Annualized: +30.72%
- Sharpe ratio: 1.91
- Max drawdown: 9.48%
- Total trades: 9
- Commission: 66.02 yuan

## Commission Settings (fixed 2026-05-31)

Old (buggy):
```python
self.commission_rate = 0.001  # 0.1%
self.min_commission = 5.0  # min 5 yuan
```

New (fixed):
```python
self.commission_rate = 0.0005  # 0.05%
self.min_commission = 0.0  # no minimum
```

## Cooldown Control (added 2026-05-31)

```python
self.last_trade_date = {}  # {fund_code: datetime}
self.cooldown_days = 7  # 7 days between trades

def can_trade(self, fund_code, current_date):
    if fund_code not in self.last_trade_date:
        return True
    days_since = (current_date - self.last_trade_date[fund_code]).days
    return days_since >= self.cooldown_days
```

## Historical Data Fetching

Script: `scripts/fetch_history_nav.py`
Update: `scripts/update_history_nav.py`

Uses AKShare: `ak.fund_open_fund_info_em(symbol=code, indicator='单位净值走势')`

Install: `pip3 install akshare`

Database stores in `fund_nav_history` table with columns:
- fund_code TEXT
- nav_date TEXT (YYYY-MM-DD)
- unit_nav REAL

## Report Integration (2026-05-31)

OptimizedMAStrategy signals are now displayed in advisor.py morning/evening reports as 【📈 均线策略信号】 section.

**Integration point**: `oof_strategy_advisor.py` → `get_ma_signals(db_path)` function.
- Called from advisor.py's `generate_morning_report()` and `generate_evening_report()`
- Runs a 60-day lookback backtest to extract recent trade signals
- Displays last 5 trades with emoji indicators (📈金叉, 📉死叉, 🛑止损, 🎯止盈)
- Silently skipped if no signals or on error (doesn't break main report)

**Signal format in report**:
```
【📈 均线策略信号】
📊 **均线策略信号** (OptimizedMAStrategy)
  策略参数: 10日/30日均线, 止损-8%, 止盈+12%

  📈 2026-05-15 买入 005165 富荣福锦混合 C: 金叉买入
  🛑 2026-05-29 卖出 005165 富荣福锦混合 C: 止损: -10.92%
```

**Pitfall**: `report.get('trades')` returns list of dicts, NOT Trade objects.
Access fields via `trade.get('date')`, `trade.get('type')`, `trade.get('reason')` etc.

## Multi-Period Backtest Results

| Period | Days | Total Return | Annualized | Max Drawdown | Sharpe | Trades |
|--------|------|-------------|------------|--------------|--------|--------|
| 近3个月 | 62 | +12.59% | +100.99% | 1.27% | 8.43 | 17 |
| 近6个月 | 119 | +2.22% | +6.96% | 5.30% | 0.30 | 13 |
| 近1年 | 242 | +18.06% | +28.46% | 8.02% | 1.56 | 14 |
| 近2年 | 484 | +42.65% | +30.72% | 9.48% | 1.91 | 9 |

Consistent positive returns across all time periods. Best Sharpe in long-term (1.91).

## Historical Data

Script: `scripts/fetch_history_nav.py` (initial fetch)
Update: `scripts/update_history_nav.py` (incremental daily)

Uses AKShare: `ak.fund_open_fund_info_em(symbol=code, indicator='单位净值走势')`
Install: `pip3 install akshare`

Current data: 3484 records, 2024-05-31 ~ 2026-05-29, 9 funds.

## ⚠️ PITFALL: Trailing Stop Underperforms with MA Strategies

Tested 2024-06 to 2026-05 (484 trading days, 100K initial capital):

| Strategy | Total Return | Sharpe | Max Drawdown | Trades |
|----------|-------------|--------|-------------|--------|
| **Fixed +12%/-8%** | **+42.65%** | **1.91** | 9.48% | 9 |
| Trailing 3%/-8% | +0.95% | -0.69 | 4.23% | 10 |
| Trailing 5%/-8% | +0.99% | -0.64 | 4.23% | 10 |
| Adaptive (15%→20% trailing) | +2.04% | -0.44 | 4.23% | 10 |

**Why trailing stop fails here:**
1. Fund NAVs have 5-10% normal volatility — trailing stop triggers on "fake pullbacks"
2. 7-day cooldown prevents re-entry after being shaken out
3. Capital sits idle for months after premature exit
4. MA strategy already has death-cross as trend exit — adding trailing stop = double filtering = too conservative

**Lesson:** Do NOT add trailing stop on top of trend-following strategies. The MA death-cross already handles trend reversals. Trailing stop is better suited for momentum strategies without built-in trend exits.

## Advisor Commands

```bash
python3 scripts/advisor.py backtest    # Run backtest with OptimizedMAStrategy
python3 scripts/advisor.py update_nav  # Update NAV data
python3 scripts/update_history_nav.py  # Fetch historical NAV via AKShare
python3 scripts/macro_dashboard.py     # Run macro signal dashboard
```
