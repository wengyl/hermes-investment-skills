# AKShare Historical Data Fetching

## Installation

```bash
pip3 install akshare
```

## Initial Fetch

Script: `scripts/fetch_history_nav.py`

Fetches 2 years of NAV data for all holdings and stores in `fund_nav_history` table.

```bash
cd ~/.hermes/fund-advisor
python3 scripts/fetch_history_nav.py
```

Output:
```
✅ 002112 德邦鑫星: 484 条记录 (2024-05-31 ~ 2026-05-29)
✅ 005165 富荣福锦: 484 条记录 (2024-05-31 ~ 2026-05-29)
...
💾 数据库统计:
  总记录数: 3484 条
  日期范围: 2024-05-31 ~ 2026-05-29
```

## Incremental Update

Script: `scripts/update_history_nav.py`

Updates only new data since last fetch. Safe to run daily.

```bash
python3 scripts/update_history_nav.py
```

## API Pattern

```python
import akshare as ak

# Get fund NAV history
df = ak.fund_open_fund_info_em(symbol='002112', indicator='单位净值走势')

# Columns: 净值日期, 单位净值, 累计净值, 日增长率
# 净值日期 is datetime, 单位净值 is float
```

## Database Schema

```sql
CREATE TABLE fund_nav_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code TEXT NOT NULL,
    nav_date TEXT NOT NULL,      -- YYYY-MM-DD
    unit_nav REAL NOT NULL,
    acc_nav REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fund_code, nav_date)
);
```

## Data Coverage

| Fund | Records | Start | End |
|------|---------|-------|-----|
| 002112 德邦鑫星 | 484 | 2024-05-31 | 2026-05-29 |
| 005165 富荣福锦 | 484 | 2024-05-31 | 2026-05-29 |
| 014414 招商畜牧 | 484 | 2024-05-31 | 2026-05-29 |
| 018388 华泰港股红利 | 484 | 2024-05-31 | 2026-05-29 |
| 020692 博时通信 | 484 | 2024-05-31 | 2026-05-29 |
| 022184 富国全球科技 | 407 | 2024-09-18 | 2026-05-28 |
| 026211 平安科技 | 103 | 2025-12-12 | 2026-05-29 |
| 027063 鹏华创新 | 42 | 2026-03-27 | 2026-05-29 |
| 501205 鹏华创新未来 | 484 | 2024-05-31 | 2026-05-29 |

**Note**: Some funds have shorter history (newer funds). This is normal.

## Pitfall: Python Version

macOS system Python 3.9 works fine. Use `python3` not `python`.
If `pip` not found, use `pip3`.
