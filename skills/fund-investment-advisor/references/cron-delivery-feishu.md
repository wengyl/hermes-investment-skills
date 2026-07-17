# Cron Delivery to Feishu — Pitfalls & Solution

## Problem

All fund advisor cron jobs failed with:
```
delivery error: Feishu send failed: [99992402] field validation failed
```

## Root Cause (3 layers)

### 1. Cron system injects anti-send_message instruction
Every cron job's agent prompt gets this prepended:
```
[IMPORTANT: You are running as a scheduled cron job. DELIVERY: Your final
response will be automatically delivered to the user — do NOT use send_message
or try to deliver the output yourself. ...]
```

### 2. send_message tool is NOT in cron agent's toolset
The agent literally cannot call send_message. It confirms this in its response:
> "我无法使用 send_message 工具（该工具不在当前可用工具集中）"

### 3. Result: full report goes into final response
Even if the job prompt says "split via send_message, final response = one sentence",
the agent ignores it (can't use the tool + system injection overrides) and dumps
the full ~15KB report into final response → Feishu rejects it.

## Solution: no_agent=true + concise scripts

### Pattern
1. Create a Python script that:
   - Suppresses stdout during data fetching (SilentStdout pattern)
   - Generates a concise report (<1500 chars)
   - Uses code blocks for tables (user requirement)
   - Prints the final report to stdout

2. Create a wrapper `.sh` in `~/.hermes/scripts/`:
   ```bash
   #!/bin/bash
   cd ~/.hermes/fund-advisor && python scripts/cron_morning_brief.py
   ```

3. Configure cron job:
   ```json
   {
     "no_agent": true,
     "prompt": "[SILENT]",
     "script": "cron_morning_brief.sh"
   }
   ```

### Critical: script field is a FILE PATH, not a command
- ✅ `"script": "cron_morning_brief.sh"` → resolves to `~/.hermes/scripts/cron_morning_brief.sh`
- ❌ `"script": "cd ~/.hermes/fund-advisor && python scripts/cron_morning_brief.py"` →
  treated as filename `~/.hermes/scripts/cd ~/.hermes/fund-advisor && ...` → "Script not found"

### SilentStdout pattern
```python
class SilentStdout:
    """Suppress print() from imported modules during data fetching"""
    def __init__(self):
        self._real = sys.stdout
        self._buf = io.StringIO()
    def write(self, s): self._buf.write(s)
    def flush(self): pass
    def restore(self): sys.stdout = self._real

# Usage:
saver = SilentStdout()
sys.stdout = saver
# ... import modules, fetch data ...
saver.restore()
# ... print clean report ...
```

## Current Scripts (v2.0)

| Script | Cron Schedule | Output |
|--------|---------------|--------|
| `cron_morning_brief.py` | 08:30 | A股指数 + 持仓盈亏 + 情绪 + 风控 |
| `cron_intraday.py morning` | 10:30 | 实时行情 + 持仓概览 |
| `cron_intraday.py afternoon` | 14:00 | 实时行情 + 持仓概览 |
| `cron_evening.py` | 16:30 | A股收盘 + 持仓总结 + 风控 |
| `cron_weekly.py` | 周日20:00 | 持仓总览 + 本周交易 + 风控 |

## DB Schema Quick Reference

| Table | Key Columns | Notes |
|-------|-------------|-------|
| holdings | fund_code, fund_name, share_count, avg_cost | fund_name 直接在此表 |
| fund_nav_history | fund_code, unit_nav, nav_date | 列名是 unit_nav 不是 nav |
| transactions | fund_code, trans_type, trans_date, amount | trans_date/trans_type |

## Feishu send_message target format
- `target: "feishu"` → 需要配置 FEISHU_HOME_CHANNEL，否则报错
- `target: "feishu:oc_a6a554f98bdaea351d79ea539d700a0e"` → 直接指定 chat ID，可靠
