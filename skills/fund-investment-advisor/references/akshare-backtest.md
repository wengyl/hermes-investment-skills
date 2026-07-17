# AKShare Backtesting Guide

## Overview

Use AKShare (`akshare`) for real historical fund NAV data to backtest strategies. This replaces the old synthetic data approach.

## Installation

```bash
pip install akshare
```

## Key API

```python
import akshare as ak

# Get fund NAV history (单位净值走势)
df = ak.fund_open_fund_info_em(symbol='002112', indicator='单位净值走势')
# Returns: DataFrame with columns ['净值日期', '单位净值', '日增长率']
# Data: 2500+ records per fund, going back to inception
```

## Backtest Script

Location: `~/.hermes/fund-advisor/scripts/akshare_backtest.py`

**Usage**:
```bash
cd ~/.hermes/fund-advisor/scripts
python3 akshare_backtest.py
```

**What it does**:
1. Fetches real NAV data for all 9 held funds via AKShare
2. Runs three strategy modes (bull/shock/bear) over the same period
3. Compares total return, max drawdown, trade count
4. Outputs detailed trade log

## Key Findings from 2-Year Backtest

**Period**: 2024-06-03 ~ 2026-05-28

| Metric | 🐂 Bull Mode | 📊 Shock Mode | 🐻 Bear Mode |
|--------|-------------|---------------|--------------|
| Final Value | ¥8,470 | ¥281 | ¥44 |
| Total Return | -30.37% | -97.69% | -99.63% |
| Max Drawdown | -51.21% | -97.69% | -99.64% |
| Trade Count | 5 | 83 | 79 |

**Critical Insight**: Bull mode performed dramatically better because:
- 020692 (博时通信): Captured **+104.2%** profit before trailing stop triggered
- Shock mode sold the same fund at **+31.2%** (too early!)
- Bear mode sold it at **-12.1%** (at a loss!)

## Pitfalls

1. **Cost basis**: When backtesting from a historical start date, use the NAV on the start date as cost basis, NOT the user's actual purchase cost. Otherwise the strategy immediately triggers stop-loss if the start NAV is below cost.

2. **Date matching**: `_get_nav_on_date()` must handle dates with no exact match. Use `<=` comparison and take the latest available NAV.

3. **SSL errors**: AKShare sometimes fails with SSL errors on specific funds. Skip those funds and continue.

4. **Missing data**: Some funds (like 027063) have very short history (40 days). The backtest will still run but results for those funds are less meaningful.

## Integration with Strategy Engine

The backtest uses `SmartStrategyEngine` from `smart_strategy.py`:
```python
from smart_strategy import SmartStrategyEngine, MarketEnv

engine = SmartStrategyEngine(MarketEnv.BULL)
signal = engine.analyze_fund(code, name, nav, cost, highest, days, weekly_change)
```
