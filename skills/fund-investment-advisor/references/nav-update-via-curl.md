# Fund NAV Update via curl

## Problem

Python `requests` library may be blocked by network restrictions when accessing fund data APIs (e.g., 天天基金网), returning 502 errors. However, `curl` command-line tool can successfully access the same endpoints.

## Solution

Use `subprocess` to call `curl` instead of `requests`:

```python
import subprocess
import json

def get_fund_nav_curl(fund_code: str) -> dict:
    """使用 curl 获取基金最新净值"""
    url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
    
    try:
        # 使用 curl 获取数据
        result = subprocess.run(
            ['curl', '-s', '-A', 'Mozilla/5.0', url],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"curl 错误：{result.stderr}")
            return None
        
        # 解析返回的 JSON 数据（去掉函数调用包装）
        text = result.stdout.strip()
        if text.startswith('jsonpgz('):
            text = text[8:-2]  # 去掉 "jsonpgz(" 和 ");"
        
        data = json.loads(text)
        
        # 字段映射：jzrq=净值日期，dwjz=单位净值，gsz=估值，gszzl=估值涨幅，gztime=估值时间
        return {
            'fund_code': fund_code,
            'nav_date': data.get('jzrq', data.get('gsrq', '')),
            'unit_nav': float(data.get('dwjz', data.get('gsz', 0))),
            'daily_return': float(data.get('gszzl', 0)),
            'timestamp': data.get('gztime', data.get('timestamp', ''))
        }
    except Exception as e:
        print(f"获取 {fund_code} 净值失败：{e}")
        return None
```

## API Response Format

天天基金网返回 JSONP 格式：

```javascript
jsonpgz({"fundcode":"005165","name":"富荣福锦混合 C","jzrq":"2026-05-18","dwjz":"2.5577","gsz":"2.5561","gszzl":"-0.06","gztime":"2026-05-19 14:26"});
```

**字段说明**：
- `fundcode`: 基金代码
- `name`: 基金名称
- `jzrq`: 净值日期 (YYYY-MM-DD)
- `dwjz`: 单位净值 (已确认)
- `gsz`: 估值净值 (盘中估算)
- `gszzl`: 估值涨幅百分比 (如 -0.06 表示 -0.06%)
- `gztime`: 估值时间

**解析要点**：
1. 去掉 `jsonpgz(` 前缀（8 个字符）
2. 去掉 `);` 后缀（2 个字符）
3. 使用 `json.loads()` 解析剩余 JSON

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS fund_nav_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code TEXT NOT NULL,
    nav_date DATE NOT NULL,
    unit_nav REAL NOT NULL,
    daily_return REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fund_code, nav_date)
);

CREATE INDEX IF NOT EXISTS idx_nav_date ON fund_nav_history(nav_date);
CREATE INDEX IF NOT EXISTS idx_nav_code ON fund_nav_history(fund_code);
```

## Update Script

See `scripts/update_nav_curl.py` for a complete implementation that:
- Fetches NAV for all holdings
- Updates `fund_nav_history` table
- Updates `holdings.current_value` based on latest NAV
- Handles duplicate dates (UPDATE vs INSERT)

## Cron Job Setup

```bash
# Daily NAV update at 9:00 AM
hermes cron create "0 9 * * *" \
  "[SILENT]" \
  --name "基金净值每日更新" \
  --script "fund-nav-update.sh" \
  --no-agent true
```

Where `fund-nav-update.sh`:
```bash
#!/bin/bash
cd ~/.hermes/fund-advisor
python scripts/update_nav_curl.py 2>&1 | grep -E "更新完成 | 处理："
```

## Troubleshooting

**curl returns empty response**:
- Check network connectivity
- Verify fund code is valid
- Try with verbose mode: `curl -v <url>`

**JSON parsing fails**:
- Print raw response: `print(result.stdout[:100])`
- Check for JSONP wrapper variations
- Validate JSON structure with `jq`

**Database errors**:
- Ensure UNIQUE constraint on `(fund_code, nav_date)`
- Use UPSERT logic: check if record exists, then UPDATE or INSERT

## Related

- `references/database-schema.md`: Full database schema
- `scripts/update_nav_curl.py`: Complete update script
- `scripts/advisor.py`: Holdings display with NAV data