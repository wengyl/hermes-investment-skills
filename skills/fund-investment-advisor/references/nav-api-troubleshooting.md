# NAV API Troubleshooting

## Network Restrictions Workaround

### Problem
Python `requests` library returns 502 errors when accessing fund APIs:
```python
import requests
response = requests.get("http://fundgz.1234567.com.cn/js/005165.js")  # 502 error
```

### Solution: Use `curl` via subprocess
Network restrictions may block Python requests but allow curl:

```python
import subprocess
import json

url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"

result = subprocess.run(
    ['curl', '-s', '-A', 'Mozilla/5.0', url],
    capture_output=True,
    text=True,
    timeout=10
)

# Parse response
text = result.stdout.strip()
if text.startswith('jsonpgz('):
    text = text[8:-2]  # Remove "jsonpgz(" and ");"

data = json.loads(text)
```

## API Response Format

### 天天基金网 Real-time Valuation API

**Endpoint**: `http://fundgz.1234567.com.cn/js/{fund_code}.js`

**Response Format**:
```javascript
jsonpgz({"fundcode":"005165","name":"富荣福锦混合 C","jzrq":"2026-05-18","dwjz":"2.5577","gsz":"2.5561","gszzl":"-0.06","gztime":"2026-05-19 14:26"});
```

**Field Mapping**:
- `fundcode`: 基金代码
- `name`: 基金名称
- `jzrq`: 净值日期 (NAV date)
- `dwjz`: 单位净值 (unit NAV) - **use this for confirmed NAV**
- `gsz`: 估值 (estimated NAV) - use when dwjz not available
- `gszzl`: 估值涨幅 % (daily return percentage)
- `gztime`: 估值时间 (valuation timestamp)

**Parsing Logic**:
```python
# Remove wrapper: "jsonpgz(" (8 chars) and ");" (2 chars)
if text.startswith('jsonpgz('):
    text = text[8:-2]

data = json.loads(text)

# Use confirmed NAV if available, otherwise use estimate
unit_nav = float(data.get('dwjz', data.get('gsz', 0)))
daily_return = float(data.get('gszzl', 0))
nav_date = data.get('jzrq', '')
```

## Daily NAV Update Workflow

When `fund_nav_history` table is empty:

1. **Update latest NAV**:
   ```bash
   cd ~/.hermes/fund-advisor
   python scripts/update_nav_curl.py
   ```

2. **Verify holdings show 今日收益**:
   ```bash
   python scripts/advisor.py holdings
   ```

3. **Set up daily cron job**:
   ```bash
   hermes cron create "0 9 * * *" \
     "[SILENT]" \
     --name "基金净值每日更新" \
     --script "fund-nav-update.sh" \
     --no-agent true
   ```

## Common Issues

### JSON Parse Error: "Extra data: line 1 column 11"
**Cause**: Incorrect wrapper removal (using `[9:-1]` instead of `[8:-2]`)

**Fix**: 
```python
# Wrong
text = text[9:-1]  # Leaves extra character

# Correct
text = text[8:-2]  # "jsonpgz(" is 8 chars, ");" is 2 chars
```

### Database Column Missing: `last_nav`, `last_nav_date`
**Cause**: Old database schema

**Fix**: Don't reference these columns in UPDATE statements:
```python
# Wrong
cursor.execute("UPDATE holdings SET last_nav = ? WHERE fund_code = ?", (nav, code))

# Correct - only update current_value
cursor.execute("UPDATE holdings SET current_value = ?, updated_at = CURRENT_TIMESTAMP WHERE fund_code = ?", (value, code))
```

### 今日收益 Shows +0.00
**Cause**: `fund_nav_history` table is empty

**Diagnosis**:
```bash
sqlite3 data/fund_system.db "SELECT COUNT(*) FROM fund_nav_history;"
```

**Fix**: Run `python scripts/update_nav_curl.py` to populate NAV data

## Testing Network Access

Test if curl works but requests fails:
```bash
# Test with curl
curl -I http://fundgz.1234567.com.cn/js/005165.js

# Test with Python requests
python3 -c "import requests; print(requests.get('http://fundgz.1234567.com.cn/js/005165.js').status_code)"
```

If curl returns 200 but requests returns 502, use subprocess approach.
