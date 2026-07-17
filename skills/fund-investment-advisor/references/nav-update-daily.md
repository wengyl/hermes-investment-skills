# Daily NAV Update Workflow

## Overview
Fund NAV (Net Asset Value) data must be updated daily after market close for accurate portfolio tracking and return calculations.

## Key Concepts

### NAV Timing
- **Domestic funds**: NAV typically available by 18:00-20:00 on trading days
- **QDII funds**: NAV may be delayed by 1-2 days (investing in overseas markets)
- **Holiday periods**: NAV updates may be delayed

### Today's Return vs. Yesterday's Return
**Important**: "今日收益" (Today's Return) in reports uses the **previous trading day's NAV** because:
1. Fund NAV is calculated after market close
2. Portfolio reports are often generated before NAV is finalized
3. This is industry standard - real-time returns are estimates only

For **real-time portfolio value**, use: `shares * latest_NAV`

## Daily Update Procedure

### 1. Manual Update (After Market Close)
```bash
cd ~/.hermes/fund-advisor

# Update all fund NAV data
python scripts/update_nav_curl.py

# Verify update
sqlite3 data/fund_system.db "
SELECT fund_code, nav_date, unit_nav, daily_return 
FROM fund_nav_history 
ORDER BY nav_date DESC 
LIMIT 9;
"
```

### 2. Automated Daily Update (Recommended)
Set up a cron job to run automatically after market close:

```bash
# Create update script
cat > ~/.hermes/scripts/update-nav-cron.sh << 'EOF'
#!/bin/bash
cd ~/.hermes/fund-advisor
python scripts/update_nav_curl.py 2>&1 | grep -E "更新完成|处理："
EOF
chmod +x ~/.hermes/scripts/update-nav-cron.sh

# Schedule: 15:30 (30 min after market close)
hermes cron create "30 15 * * 1-5" \
  "[SILENT]" \
  --name "基金净值每日更新" \
  --script "update-nav-cron.sh" \
  --no-agent true \
  --deliver "local"
```

**Schedule Notes**:
- `30 15 * * 1-5`: 15:30 Monday-Friday (30 min after 15:00 market close)
- No weekends/holidays: Funds don't update NAV on non-trading days
- `--deliver "local"`: Don't spam user with update notifications

### 3. Verification Checklist
After update, verify:

1. **Date progression**: Latest NAV date should be most recent trading day
2. **No gaps**: Shouldn't have missing dates in sequence
3. **Reasonable changes**: Daily returns typically ±5% (exceptions: volatile markets)
4. **QDII funds**: May have earlier dates than domestic funds

```bash
# Check date gaps
sqlite3 data/fund_system.db "
SELECT fund_code, 
       COUNT(DISTINCT nav_date) as date_count,
       MIN(nav_date) as earliest,
       MAX(nav_date) as latest
FROM fund_nav_history 
GROUP BY fund_code;
"
```

## Troubleshooting

### Issue: NAV Not Updating
**Symptoms**: 
- `update_nav_curl.py` runs but no new dates in database
- Stale NAV dates (more than 2 trading days old)

**Causes & Fixes**:
1. **Network restrictions**: Use `curl` instead of `requests`
2. **API changes**: Check `references/nav-api-troubleshooting.md`
3. **Market holidays**: Normal during extended holidays

### Issue: Today's Return Shows 0.00
**Symptoms**:
- Portfolio shows `+0.00 (0.00%)` for today's return
- NAV data exists but daily_return is NULL

**Fix**:
```bash
# Recalculate daily returns from NAV history
python -c "
import sqlite3
conn = sqlite3.connect('data/fund_system.db')
cursor = conn.cursor()
cursor.execute('''
    SELECT fund_code, nav_date, unit_nav,
           LAG(unit_nav) OVER (PARTITION BY fund_code ORDER BY nav_date) as prev_nav
    FROM fund_nav_history
    ORDER BY fund_code, nav_date
''')
for code, date, nav, prev in cursor.fetchall():
    if prev and prev > 0:
        ret = (nav - prev) / prev * 100
        cursor.execute('''
            UPDATE fund_nav_history 
            SET daily_return = ? 
            WHERE fund_code = ? AND nav_date = ?
        ''', (ret, code, date))
conn.commit()
print('Daily returns recalculated')
"
```

### Issue: QDII Funds Have Older Dates
**Symptoms**:
- QDII funds (like 022184) show NAV from 1-2 days ago
- Domestic funds show current date

**Explanation**: This is normal. QDII funds investing overseas may have delayed NAV due to:
- Time zone differences
- Overseas market trading hours
- Currency conversion delays

**Action**: No fix needed. Use each fund's latest NAV regardless of date.

## Data Validation

### Expected NAV Patterns
1. **Daily updates**: Each trading day should have new NAV
2. **Price continuity**: NAV shouldn't jump >20% in one day (except market crashes)
3. **Return consistency**: Daily returns should align with market indices

### Validation Script
```bash
# Run validation checks
python -c "
import sqlite3
conn = sqlite3.connect('data/fund_system.db')
cursor = conn.cursor()

# Check for large NAV jumps (potential data errors)
cursor.execute('''
    SELECT h1.fund_code, h1.nav_date, h1.unit_nav, 
           h2.nav_date, h2.unit_nav,
           ABS((h1.unit_nav - h2.unit_nav) / h2.unit_nav * 100) as change_pct
    FROM fund_nav_history h1
    JOIN fund_nav_history h2 ON h1.fund_code = h2.fund_code 
        AND h1.nav_date = date(h2.nav_date, '+1 day')
    WHERE ABS((h1.unit_nav - h2.unit_nav) / h2.unit_nav * 100) > 20
    ORDER BY change_pct DESC
''')

print('Large NAV jumps (>20%):')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]} ({row[2]:.4f}) -> {row[3]} ({row[4]:.4f}): {row[5]:.1f}%')
"
```

## Integration with Reports

### Morning Briefing (开盘前简报)
- Uses NAV from **previous trading day**
- Shows "今日收益" based on yesterday's close
- Includes disclaimer about data timing

### Evening Summary (盘后总结)  
- Should run **after** NAV update (16:30+)
- Includes latest NAV in portfolio valuation
- More accurate daily return calculation

### Cron Job Dependencies
```bash
# Order matters: Update NAV first, then generate reports
# 1. NAV Update: 15:30
# 2. Evening Report: 16:30
hermes cron update <nav_job_id> --schedule "30 15 * * 1-5"
hermes cron update <evening_job_id> --schedule "30 16 * * 1-5"
```

## Best Practices

1. **Regular monitoring**: Check NAV dates weekly
2. **Backup before updates**: `cp data/fund_system.db data/fund_system.db.backup`
3. **Holiday handling**: Skip updates on market holidays
4. **Data retention**: Keep at least 2 years of NAV history for backtesting

## Related Files
- `scripts/update_nav_curl.py` - Main NAV update script
- `references/nav-api-troubleshooting.md` - API issues and fixes
- `references/nav-update-via-curl.md` - Using curl for network-restricted environments
- `data/fund_system.db` - SQLite database with NAV history
