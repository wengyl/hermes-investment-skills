# Adding a New Fund to the System

## Procedure (10 steps)

When user adds a new fund, update these files in order:

### 1. Fund List Scripts (2 files)
```python
# scripts/fetch_history_nav.py
HOLDINGS = {
    ...
    '257070': '国联安优选',  # ADD
}

# scripts/update_history_nav.py
HOLDINGS = {
    ...
    '257070': '国联安优选',  # ADD
}
```

### 2. Risk Engine: `scripts/adaptive_risk_v2.py` (2 places)
```python
# Theme mapping
FUND_THEME_MAP = {
    '257070': ['AI算力', '科技成长'],  # ADD based on holdings
}

# Risk profile mapping
# Options: 'tech', 'dividend', 'industry', 'hk', 'default'
RISK_PROFILE_MAP = {
    '257070': 'tech',  # ADD
}
```

### 3. Market Mainline: `scripts/market_mainline.py`
```python
FUND_THEME_MAP = {
    '257070': ['AI算力', '科技成长'],  # ADD
}
```

### 4. Fund Categories: `configs/fund_categories.yaml`
Add to appropriate category with optional fund-level overrides:
```yaml
科技主题基金:
  stop_loss: -15
  funds:
    - code: "257070"
      name: "国联安优选行业混合"
      industry: "半导体/AI"
      core_metrics: ["半导体景气度", "AI算力需求"]
      # stop_loss: -20  # optional fund-level override
```

### 5. Holdings Overlap: `scripts/holdings_overlap.py`
Add seed data (top 10 holdings + industry allocation):
```python
'257070': {
    'name': '国联安优选行业混合',
    'top_holdings': [
        {'name': '恒玄科技', 'ratio': 6.87},
        ...
    ],
    'industry_allocation': {'半导体': 35, '人工智能': 25, '电子': 20, '其他': 20}
},
```

### 6. Historical NAV Data
```bash
/opt/homebrew/bin/python3 -c "
import akshare as ak
import sqlite3

DB_PATH = str(Path.home() / '.hermes' / 'fund-advisor' / 'data' / 'fund_system.db')
df = ak.fund_open_fund_info_em(symbol='257070', indicator='单位净值走势')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
for _, row in df.iterrows():
    cursor.execute('INSERT OR IGNORE INTO fund_nav_history (fund_code, nav_date, unit_nav) VALUES (?, ?, ?)',
        ('257070', str(row.iloc[0])[:10], float(row.iloc[1])))
conn.commit()
conn.close()
"
```

### 7. Holdings Table (if user provides share data)
```sql
INSERT INTO holdings (fund_code, fund_name, share_count, avg_cost, current_value, total_invested)
VALUES ('257070', '国联安优选行业混合', shares, avg_cost, value, invested);
```

### 8. Backtest Script: `scripts/backtest_stop_loss.py`
```python
FUND_CODES = [
    '002112', '005165', '014414', '018388', '020692',
    '022184', '026211', '027063', '257070', '501205'  # ADD
]
```

### 9. Memory
Update user profile: "用户当前持有 N 只基金..."

### 10. Verification
```bash
/opt/homebrew/bin/python3 -c "
import sys; sys.path.insert(0, '~/.hermes/fund-advisor/scripts')
from adaptive_risk_v2 import AdaptiveRiskEngine
e = AdaptiveRiskEngine()
print(e.FUND_THEME_MAP.get('257070'))

from fund_categorizer import FundCategorizer
c = FundCategorizer()
info = c.get_fund_info('257070', 'test')
print(f'{info[\"category\"]}, SL={info[\"stop_loss\"]}%, TP={info[\"take_profit\"]}%')
"
```

## Pitfalls

1. **AKShare python**: Use `/opt/homebrew/bin/python3` (system), not hermes-agent venv (no akshare)
2. **Fund-level stop_loss override**: `fund_categorizer.py` checks `fund_detail.get('stop_loss')` before `category_info.get('stop_loss')`. Must be set in YAML under the fund entry, not just the category.
3. **Report scripts**: advisor.py, morning_intraday.py, afternoon_intraday.py DON'T have hardcoded fund lists — they read from DB. No changes needed there.
4. **Seed data for holdings_overlap**: Use actual AKShare holdings data, not guesses. Run `ak.fund_portfolio_hold_em(symbol=code, date='2025')` to get real data.
