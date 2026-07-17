# Data Validation and Date Marking

## Data Integrity Issues

### Future Date Data Problem

**Symptom**: 
- Fund NAV data showing future dates (e.g., 2026-05-28, 2026-05-29 when current date is 2026-05-27)
- Reports show incorrect daily returns because they use future NAV data
- User reports positive returns but system shows negative

**Root Cause**:
- API returns incorrect future date NAV data
- `update_nav_curl.py` script inserts future date data without validation
- Database contains corrupted data with future dates

**Detection**:
```bash
# Check for future date data in database
sqlite3 data/fund_system.db "SELECT fund_code, nav_date, unit_nav, daily_return FROM fund_nav_history WHERE nav_date > date('now') ORDER BY nav_date DESC;"

# Check latest NAV dates per fund
sqlite3 data/fund_system.db "SELECT fund_code, MAX(nav_date) as latest_date FROM fund_nav_history GROUP BY fund_code;"
```

**Fix**:
1. **Delete future date data**:
```bash
# Delete all records with future dates
sqlite3 data/fund_system.db "DELETE FROM fund_nav_history WHERE nav_date > date('now');"
```

2. **Re-run NAV update**:
```bash
# Update with correct data
python scripts/update_nav_curl.py
```

3. **Verify fix**:
```bash
# Check that all dates are current or past
sqlite3 data/fund_system.db "SELECT COUNT(*) as future_count FROM fund_nav_history WHERE nav_date > date('now');"
# Should return 0
```

### Data Validation Script

Create a validation script to check data integrity:

```python
#!/usr/bin/env python3
"""
validate_data_integrity.py - Check for data integrity issues
"""
import sqlite3
from datetime import datetime, timedelta

def validate_nav_dates(db_path):
    """Check for future dates in NAV data"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    today = datetime.now().date()
    
    # Check for future dates
    cursor.execute('''
        SELECT COUNT(*) FROM fund_nav_history 
        WHERE nav_date > ?
    ''', (today,))
    
    future_count = cursor.fetchone()[0]
    
    if future_count > 0:
        print(f"❌ Found {future_count} records with future dates")
        
        # Show details
        cursor.execute('''
            SELECT fund_code, nav_date, unit_nav, daily_return 
            FROM fund_nav_history 
            WHERE nav_date > ? 
            ORDER BY nav_date DESC
        ''', (today,))
        
        for code, date, nav, ret in cursor.fetchall():
            print(f"  {code}: {date} (NAV={nav}, Return={ret}%)")
    else:
        print("✅ No future dates found in NAV data")
    
    conn.close()
    return future_count

if __name__ == "__main__":
    validate_nav_dates("data/fund_system.db")
```

## Date Marking in Reports

### Adding NAV Date Column

**User Requirement**: Display NAV date alongside daily returns to show data freshness.

**Implementation in `advisor.py`**:

```python
# In get_holdings_summary() function

# 1. Define column width for NAV date
COL_NAV_DATE = 10  # YYYY-MM-DD format

# 2. Add to table header
summary.append(f"{'基金代码':<{COL_CODE}}{'基金名称':<{COL_NAME}}{'持有份额':>{COL_SHARES}} {'净值日期':<{COL_NAV_DATE}}{'今日收益 (%)':>{COL_DAILY}}{'持仓市值':>{COL_VALUE}}")

# 3. Extract NAV date from data
if code in nav_data and len(nav_data[code]) >= 1:
    latest_nav = nav_data[code][0]
    nav_date = latest_nav.get('date', '')
    nav_date_str = str(nav_date)[:10] if nav_date else "N/A"
    
    # Format daily return
    daily_return_pct = latest_nav['return'] if latest_nav['return'] is not None else 0
    if daily_return >= 0:
        daily_str = f"+{daily_return:>.2f} ({daily_return_pct:>.2f}%)"
    else:
        daily_str = f"{daily_return:>.2f} ({daily_return_pct:>.2f}%)"

# 4. Add to data row with spacing
summary.append(f"{code:<{COL_CODE}}{name_display:<{COL_NAME}}{shares_str} {nav_date_str:<{COL_NAV_DATE}}{daily_str}{value_str}")
```

**Column Width Considerations**:
- `COL_NAV_DATE = 10` for YYYY-MM-DD format
- Add space after share count column for readability
- Left-align date for consistent display
- Include date even when data is missing (show "N/A")

### Report Header Date

In all report types, include the report generation date:

```python
# Morning briefing header
report_date = datetime.now().strftime("%Y-%m-%d")
report.append(f"🌅 **早安！今日投资简报** ({report_date})")
```

### Data Freshness Indicator

Add a data freshness indicator to show when NAV data was last updated:

```python
def get_data_freshness(db_path):
    """Get the most recent NAV date across all funds"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT MAX(nav_date) FROM fund_nav_history')
    latest_date = cursor.fetchone()[0]
    
    conn.close()
    
    if latest_date:
        today = datetime.now().date()
        if isinstance(latest_date, str):
            latest_date = datetime.strptime(latest_date, '%Y-%m-%d').date()
        
        days_old = (today - latest_date).days
        
        if days_old == 0:
            return "✅ 数据新鲜（今日）"
        elif days_old == 1:
            return "🟡 数据延迟1天"
        else:
            return f"⚠️ 数据延迟{days_old}天"
    
    return "❌ 无数据"
```

## Database Maintenance

### Regular Data Validation

Set up a cron job for data validation:

```bash
# Daily validation at 9:30 AM (after NAV update)
hermes cron create "30 9 * * *" \
  "[SILENT]" \
  --name "数据完整性检查" \
  --script "validate-data-cron.sh" \
  --no-agent true \
  --deliver "local"
```

Script content (`validate-data-cron.sh`):
```bash
#!/bin/bash
cd ~/.hermes/fund-advisor
python scripts/validate_data_integrity.py 2>&1 | grep -E "✅|❌|⚠️"
```

### Backup Before Cleanup

Always backup before deleting data:

```python
import shutil
import sqlite3
from datetime import datetime

def backup_database(db_path):
    """Create timestamped backup of database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    shutil.copy2(db_path, backup_path)
    return backup_path
```

## Common Data Issues

### QDII Fund Date Lag

**Issue**: QDII funds (like 022184) often have NAV dated 1 day earlier than domestic funds.

**Solution**: 
- Accept different dates for different funds
- Don't force all funds to have same NAV date
- In reports, show each fund's actual NAV date

### Weekend/Holiday Data

**Issue**: Weekend/holiday NAV data may not be available.

**Solution**:
- Use last trading day's NAV for calculations
- Show the actual date of the NAV used
- In reports, note if data is from previous trading day

### Data Source Inconsistencies

**Issue**: Different APIs may return different NAV values for same date.

**Solution**:
- Use primary source (天天基金网) as authoritative
- Cross-validate with secondary sources when possible
- Log discrepancies for investigation
- Always show data source in detailed reports

## Best Practices

1. **Always validate dates** after NAV updates
2. **Show NAV date** in all portfolio displays
3. **Check data freshness** before generating reports
4. **Backup before cleanup** operations
5. **Log data issues** for pattern detection
6. **User transparency** - show actual dates, don't assume "today"
7. **Different dates acceptable** for different fund types (QDII vs domestic)