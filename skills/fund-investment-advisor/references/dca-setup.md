# DCA (定投) Setup Reference

## Overview

Automated Dollar-Cost Averaging (定投) system for fund holdings. Tracks which funds are DCA'd, auto-updates shares daily, and marks DCA funds in reports.

## Components

### 1. Configuration: `scripts/user_config.py`

```python
@dataclass
class UserConfig:
    # DCA plans: {fund_code: {amount, method, note}}
    dca_plans: Dict = field(default_factory=lambda: {
        '022184': {
            'amount': 200,
            'method': '每日定投',
            'note': '富国全球科技(QDII)C'
        }
    })
```

### 2. Daily Update Script: `scripts/dca_update.py`

Runs after market close, updates holdings table:
- Gets latest NAV from `fund_nav_history`
- Calculates new shares: `200 / NAV`
- Updates `holdings` table: share_count, avg_cost, current_value, total_invested

```bash
# Manual run
/opt/homebrew/bin/python3 ~/.hermes/fund-advisor/scripts/dca_update.py

# Output:
# ✅ 富国全球科技互联网股票 (QDII)C (022184) 定投更新
#    日期: 2026-06-02
#    净值: 5.9319
#    定投: 200 元 → 买入 33.72 份
#    总份额: 559.08 → 592.80
#    均价: 5.1871 → 5.2294
```

### 3. Cron Job

Shell wrapper: `~/.hermes/scripts/dca-update-022184.sh`
```bash
#!/bin/bash
cd ~/.hermes/fund-advisor
/opt/homebrew/bin/python3 scripts/dca_update.py 2>&1
```

Cron schedule: `0 20 * * *` (daily at 20:00, after NAV is available)
Job ID: `29e8f6e83210`

### 4. Report Markers

DCA funds show 📅 marker in holdings table name column. Bottom of table shows DCA plan details.

**Report display:**
```
022184  📅全球科技互联网股票 (QDI..    592.80  2026-06-02   -22.15 (-0.63%)  3,516.43
...
─────────────────────────────────────────────────────────────────────────
📅 定投计划:
   富国全球科技(QDII)C | 每日定投 | 200元/日
```

**Implementation**: All 3 report scripts check `self.user_config.dca_plans`:
- `advisor.py` → `get_holdings_summary()` — name prefix 📅 + footer
- `morning_intraday.py` → `get_holdings_summary()` — same pattern
- `afternoon_intraday.py` → `get_holdings_summary()` — same pattern

**Name display logic:**
```python
dca_plans = getattr(self.user_config, 'dca_plans', {}) or {}
dca_info = dca_plans.get(code)
if dca_info and len(name) >= 2:
    name = "📅" + name[2:]  # replace first 2 chars with 📅
```

## Adding a New DCA Fund

1. Update `user_config.py` → `dca_plans` dict
2. Create or update shell wrapper in `~/.hermes/scripts/`
3. Create cron job via `cronjob(action='create', no_agent=True, script=...)`
4. Reports auto-pick up from `user_config.dca_plans` — no report code changes needed

## Pitfalls

1. **NAV timing**: Fund NAV available by 18:00-20:00. Cron at 20:00 is safe.
2. **QDII delay**: QDII funds (like 022184) may have 1-day NAV delay. The script uses whatever is latest in DB.
3. **Non-trading days**: Script runs daily but NAV doesn't change on weekends/holidays — harmless.
4. **avg_cost calculation**: Uses `total_invested / total_shares` (not weighted average). Matches the holdings table schema.
