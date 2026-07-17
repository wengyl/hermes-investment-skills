# Database Schema Reference

## Tables Overview

### 1. holdings (用户持仓表)

Stores current fund positions.

```sql
CREATE TABLE holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code TEXT UNIQUE NOT NULL,      -- 基金代码
    fund_name TEXT NOT NULL,             -- 基金名称
    share_count REAL DEFAULT 0,          -- 持有份额
    avg_cost REAL DEFAULT 0,             -- 平均成本
    current_value REAL DEFAULT 0,        -- 当前市值
    total_invested REAL DEFAULT 0,       -- 总投入
    total_withdrawn REAL DEFAULT 0,      -- 总赎回
    first_buy_date DATE,                 -- 首次买入日期
    last_update_date DATE,               -- 最后更新时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Common Queries**:

```sql
-- Get all current holdings
SELECT fund_code, fund_name, share_count, avg_cost, current_value
FROM holdings
WHERE share_count > 0;

-- Calculate total portfolio value
SELECT SUM(current_value) as total_value FROM holdings WHERE share_count > 0;

-- Get holdings with P&L
SELECT 
    fund_code,
    fund_name,
    share_count * avg_cost as cost_basis,
    current_value,
    current_value - (share_count * avg_cost) as pnl,
    (current_value - (share_count * avg_cost)) / (share_count * avg_cost) * 100 as pnl_pct
FROM holdings
WHERE share_count > 0;
```

### 2. transactions (交易记录表)

Records all buy/sell transactions.

```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code TEXT NOT NULL,
    trans_type TEXT NOT NULL,            -- 'buy' / 'sell' / 'redividend'
    trans_date DATE NOT NULL,
    amount REAL NOT NULL,                -- 金额
    price REAL NOT NULL,                 -- 单价
    shares REAL DEFAULT 0,               -- 份额
    fee REAL DEFAULT 0,                  -- 手续费
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_trans_date ON transactions(trans_date);
CREATE INDEX idx_trans_code ON transactions(fund_code);
```

**Common Queries**:

```sql
-- Get recent transactions
SELECT * FROM transactions 
ORDER BY created_at DESC 
LIMIT 20;

-- Get monthly summary
SELECT 
    strftime('%Y-%m', trans_date) as month,
    trans_type,
    COUNT(*) as count,
    SUM(amount) as total_amount
FROM transactions
GROUP BY month, trans_type
ORDER BY month DESC;

-- Get transaction history for specific fund
SELECT * FROM transactions 
WHERE fund_code = '159915'
ORDER BY trans_date DESC;
```

### 3. fund_nav_history (基金净值历史表)

Historical NAV data for backtesting and analysis.

```sql
CREATE TABLE fund_nav_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code TEXT NOT NULL,
    nav_date DATE NOT NULL,
    unit_nav REAL NOT NULL,              -- 单位净值
    accum_nav REAL,                      -- 累计净值
    daily_return REAL,                   -- 日收益率
    UNIQUE(fund_code, nav_date)
);

-- Indexes
CREATE INDEX idx_nav_date ON fund_nav_history(nav_date);
CREATE INDEX idx_nav_code ON fund_nav_history(fund_code);
```

**Common Queries**:

```sql
-- Get NAV series for a fund
SELECT nav_date, unit_nav, daily_return
FROM fund_nav_history
WHERE fund_code = '159915'
ORDER BY nav_date DESC
LIMIT 100;

-- Calculate moving average
SELECT 
    nav_date,
    unit_nav,
    AVG(unit_nav) OVER (ORDER BY nav_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as ma20
FROM fund_nav_history
WHERE fund_code = '159915'
ORDER BY nav_date;

-- Get max/min NAV in period
SELECT 
    fund_code,
    MIN(unit_nav) as min_nav,
    MAX(unit_nav) as max_nav,
    (MAX(unit_nav) - MIN(unit_nav)) / MIN(unit_nav) * 100 as range_pct
FROM fund_nav_history
WHERE nav_date BETWEEN '2024-01-01' AND '2024-12-31'
GROUP BY fund_code;
```

### 4. strategies (策略配置表)

Stores investment strategy configurations.

```sql
CREATE TABLE strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT UNIQUE NOT NULL,
    strategy_type TEXT,                  -- 'dca' / 'rebalance' / 'momentum'
    config_json TEXT,                    -- Strategy parameters as JSON
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Example Config JSON**:

```json
{
  "name": "价值定投策略",
  "type": "dca",
  "parameters": {
    "base_amount": 1000,
    "undervalued_multiplier": 1.5,
    "normal_multiplier": 1.0,
    "overvalued_multiplier": 0.5,
    "bubble_multiplier": 0
  },
  "rules": {
    "valuation_source": "沪深 300 市盈率分位",
    "rebalance_frequency": "monthly"
  }
}
```

### 5. review_reports (复盘报告表)

Stores periodic review reports.

```sql
CREATE TABLE review_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_type TEXT NOT NULL,           -- 'weekly' / 'monthly' / 'quarterly' / 'yearly'
    review_date DATE NOT NULL,
    period_start DATE,
    period_end DATE,
    total_return REAL,
    summary_text TEXT,
    analysis_json TEXT,                  -- Detailed analysis as JSON
    improvements TEXT,
    next_plan TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Analysis JSON Structure**:

```json
{
  "performance": {
    "total_return": 0.0567,
    "annualized_return": 0.1234,
    "benchmark_return": 0.0456,
    "alpha": 0.0111
  },
  "risk_metrics": {
    "max_drawdown": -0.1235,
    "volatility": 0.182,
    "sharpe_ratio": 0.74,
    "sortino_ratio": 1.02
  },
  "trading_stats": {
    "total_trades": 98,
    "win_rate": 0.582,
    "profit_factor": 1.85,
    "turnover_rate": 2.3
  },
  "holdings_analysis": {
    "concentration": 0.60,
    "sector_allocation": {...}
  }
}
```

### 6. market_data (市场数据表)

Stores market indices and macro data.

```sql
CREATE TABLE market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_type TEXT NOT NULL,             -- 'index' / 'sector' / 'macro'
    data_code TEXT NOT NULL,
    data_date DATE NOT NULL,
    value REAL NOT NULL,
    change_pct REAL,
    UNIQUE(data_type, data_code, data_date)
);
```

**Common Queries**:

```sql
-- Get index history
SELECT data_date, value, change_pct
FROM market_data
WHERE data_type = 'index' AND data_code = '000300'
ORDER BY data_date DESC
LIMIT 30;

-- Get sector performance
SELECT 
    data_code as sector,
    MAX(value) as latest_value,
    change_pct as latest_change
FROM market_data
WHERE data_type = 'sector'
AND data_date = (SELECT MAX(data_date) FROM market_data WHERE data_type = 'sector');
```

### 7. user_config (用户配置表)

Key-value store for user preferences.

```sql
CREATE TABLE user_config (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Default Configurations**:

```sql
INSERT OR REPLACE INTO user_config (key, value) VALUES
('risk_tolerance', 'moderate'),           -- conservative/moderate/aggressive
('investment_horizon', 'medium'),         -- short/medium/long
('max_position', '70'),                   -- Maximum position %
('stop_loss', '15'),                      -- Stop loss threshold %
('take_profit', '20'),                    -- Take profit threshold %
('dca_amount', '1000'),                   -- DCA amount
('dca_frequency', 'weekly');              -- daily/weekly/monthly
```

---

## Backup and Recovery

### Full Backup

```bash
# Backup database
sqlite3 data/fund_system.db ".backup 'data/fund_system.db.backup.$(date +%Y%m%d)'"

# Verify backup
sqlite3 "data/fund_system.db.backup.$(date +%Y%m%d)" "SELECT COUNT(*) FROM holdings;"
```

### Restore from Backup

```bash
# Stop all processes using the database
# Restore
cp "data/fund_system.db.backup.20240516" data/fund_system.db

# Verify
python scripts/advisor.py holdings
```

### Export to CSV

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/fund_system.db')

# Export all tables
tables = ['holdings', 'transactions', 'fund_nav_history', 'strategies']
for table in tables:
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    df.to_csv(f'reports/{table}_export.csv', index=False, encoding='utf-8-sig')

conn.close()
```

---

## Performance Optimization

### Indexes

Already created indexes:
- `idx_trans_date` on transactions(trans_date)
- `idx_trans_code` on transactions(fund_code)
- `idx_nav_date` on fund_nav_history(nav_date)
- `idx_nav_code` on fund_nav_history(fund_code)

### Vacuum Database

```bash
# Optimize database size
sqlite3 data/fund_system.db "VACUUM;"
```

### Analyze Tables

```bash
# Update query planner statistics
sqlite3 data/fund_system.db "ANALYZE;"
```

---

## Data Integrity

### Foreign Key Constraints

Enable foreign keys:

```sql
PRAGMA foreign_keys = ON;
```

### Check Constraints

Add validation:

```sql
-- Example: Ensure positive share count
ALTER TABLE holdings ADD CHECK (share_count >= 0);

-- Example: Valid transaction types
ALTER TABLE transactions ADD CHECK (trans_type IN ('buy', 'sell', 'redividend'));
```

### Regular Integrity Check

```bash
# Check database integrity
sqlite3 data/fund_system.db "PRAGMA integrity_check;"
```
