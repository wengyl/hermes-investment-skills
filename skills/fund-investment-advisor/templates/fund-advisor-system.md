# Fund Investment Advisor System Template

## Overview

Complete Python-based fund investment advisor system with:
- SQLite database for holdings and transactions
- Automated daily reports (morning, intraday, evening)
- Weekly review reports
- Data fetching from Chinese financial APIs
- Cron job scheduling via Hermes

## Project Structure

```
~/.hermes/fund-advisor/
├── data/
│   └── fund_system.db          # SQLite database
├── scripts/
│   ├── db_init.py              # Database initialization
│   ├── data_fetcher.py         # Financial data API client
│   ├── advisor.py              # Main advisor logic
│   └── morning_cron.sh         # Cron job wrapper
├── configs/
│   └── settings.yaml           # User configuration
├── logs/                       # Runtime logs
├── reports/                    # Generated reports
└── README.md                   # Documentation
```

## Quick Start

### 1. Initialize Database

```bash
cd ~/.hermes/fund-advisor
python scripts/db_init.py
```

Creates tables:
- `holdings` - Current fund positions
- `transactions` - Buy/sell history
- `fund_nav_history` - Historical NAV data
- `strategies` - Investment strategy configs
- `review_reports` - Weekly/monthly reviews
- `user_config` - User preferences

### 2. Test Data Fetching

```bash
python scripts/data_fetcher.py
```

Tests:
- Real-time fund NAV
- Market indices (A-shares, US stocks)
- Global market summary

### 3. Generate Reports

```bash
# Morning briefing (8:30 AM)
python scripts/advisor.py morning

# Evening summary (4:30 PM)
python scripts/advisor.py evening

# View holdings
python scripts/advisor.py holdings

# Record transaction
python scripts/advisor.py buy <fund_code> <amount>
python scripts/advisor.py sell <fund_code> <amount>
```

### 4. Set Up Cron Jobs

```bash
# Morning briefing (daily 8:30)
hermes cron create "30 8 * * *" \
  "cd ~/.hermes/fund-advisor && python scripts/advisor.py morning" \
  --name "开盘前简报"

# Intraday (10:30 and 14:00)
hermes cron create "30 10 * * *" \
  "cd ~/.hermes/fund-advisor && python scripts/advisor.py morning" \
  --name "盘中上午简报"

hermes cron create "0 14 * * *" \
  "cd ~/.hermes/fund-advisor && python scripts/advisor.py morning" \
  --name "盘中下午简报"

# Evening summary (daily 16:30)
hermes cron create "30 16 * * *" \
  "cd ~/.hermes/fund-advisor && python scripts/advisor.py evening" \
  --name "盘后总结"

# Weekly review (Sunday 20:00)
hermes cron create "0 20 * * 0" \
  "cd ~/.hermes/fund-advisor && python scripts/advisor.py evening" \
  --name "周复盘报告"
```

## Database Schema

### holdings
```sql
CREATE TABLE holdings (
    id INTEGER PRIMARY KEY,
    fund_code TEXT UNIQUE,
    fund_name TEXT,
    share_count REAL,
    avg_cost REAL,
    current_value REAL,
    total_invested REAL,
    total_withdrawn REAL,
    first_buy_date DATE,
    last_update_date DATE
);
```

### transactions
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    fund_code TEXT,
    trans_type TEXT,  -- 'buy' or 'sell'
    trans_date DATE,
    amount REAL,
    price REAL,
    shares REAL,
    fee REAL,
    remark TEXT
);
```

### fund_nav_history
```sql
CREATE TABLE fund_nav_history (
    id INTEGER PRIMARY KEY,
    fund_code TEXT,
    nav_date DATE,
    unit_nav REAL,
    accum_nav REAL,
    daily_return REAL,
    UNIQUE(fund_code, nav_date)
);
```

## Configuration (settings.yaml)

```yaml
# User preferences
risk_tolerance: moderate  # conservative/moderate/aggressive
investment_horizon: medium  # short/medium/long
max_position: 70  # Maximum position %
stop_loss: 15  # Stop loss threshold %
take_profit: 20  # Take profit threshold %

# DCA (Dollar Cost Averaging)
dca:
  enabled: true
  amount: 1000
  frequency: weekly  # daily/weekly/monthly
  day: 1  # For monthly

# Notifications
notifications:
  morning:
    enabled: true
    time: "08:30"
  intraday:
    enabled: true
    times: ["10:30", "14:00"]
  evening:
    enabled: true
    time: "16:30"
  weekly_review:
    enabled: true
    day: sunday
    time: "20:00"

# Watched funds
watched_funds:
  - code: "159915"
    name: "华夏沪深 300ETF"
    target_weight: 20
```

## Key Scripts

### db_init.py
- Initializes SQLite database
- Creates all required tables
- Sets default user configurations

### data_fetcher.py
- Fetches real-time fund NAV from 天天基金
- Gets market indices (A-shares, US stocks)
- Handles GBK encoding for Chinese APIs
- Uses `http.client` to avoid SSL issues

### advisor.py
- Generates morning/evening reports
- Records transactions
- Calculates portfolio metrics
- Sends notifications via Feishu

## Common Issues

### SSL Errors on macOS
Use `http.client` instead of `requests`:
```python
import http.client
import ssl

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
```

### GBK Encoding
Chinese APIs return GBK-encoded responses:
```python
for encoding in ['gbk', 'gb2312', 'utf-8']:
    try:
        data = raw_data.decode(encoding)
        break
    except:
        continue
```

### Fund Code Verification
**Never guess fund codes**. Ask user to provide verified codes from:
- 支付宝/蚂蚁财富
- 天天基金 APP
- Official fund company websites

## Extensions

### Add Visualization
```python
import plotly.graph_objects as go

def generate_equity_curve(nav_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=nav_data['date'],
        y=nav_data['total_value']
    ))
    fig.write_html("reports/equity_curve.html")
```

### Add Backtesting
```python
class BacktestEngine:
    def __init__(self, initial_capital=100000):
        self.cash = initial_capital
        self.positions = {}
    
    def run_strategy(self, strategy, fund_codes, start_date, end_date):
        # Implement strategy backtesting
        pass
```

### Add Risk Metrics
```python
def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    excess_returns = returns - risk_free_rate / 252
    return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)

def calculate_max_drawdown(nav_series):
    rolling_max = nav_series.expanding().max()
    drawdown = (nav_series - rolling_max) / rolling_max
    return drawdown.min()
```

## Session Notes

- Created: 2026-05-16
- Purpose: Complete fund investment advisor with automated reporting
- Key learnings: SSL compatibility, GBK encoding, data integrity
- Next steps: Add visualization, backtesting, risk metrics

## Related Skills

- `python-financial-api` - Financial API handling
- `data-science` - Data analysis and visualization
