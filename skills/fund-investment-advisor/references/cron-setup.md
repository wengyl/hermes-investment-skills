# Cron Job Setup for Fund Advisor

## Standard Schedule

Based on A-share market hours (9:30-11:30, 13:00-15:00 CST):

| Time | Event | Cron Expression | Job Name |
|------|-------|----------------|----------|
| 08:30 | Morning briefing | `30 8 * * *` | 开盘前简报 |
| 10:30 | Mid-morning update | `30 10 * * *` | 盘中上午简报 |
| 14:00 | Afternoon update | `0 14 * * *` | 盘中下午简报 |
| 16:30 | Evening summary | `30 16 * * *` | 盘后总结 |
| 20:00 Sunday | Weekly review | `0 20 * * 0` | 周复盘报告 |

## Cron Syntax Notes

**Important**: Hermes cron uses standard cron format: `minute hour day month weekday`

- Use `30 8` for 8:30 AM (NOT `0 8:30`)
- Use `30 16` for 4:30 PM (NOT `0 16:30`)
- Minutes and hours are separate fields

## Creating Jobs

### Morning Briefing (8:30 AM)

```bash
hermes cron create "30 8 * * *" \
  "cd ~/.hermes/fund-advisor && python scripts/advisor.py morning" \
  --name "基金投资顾问 - 开盘前简报" \
  --deliver "origin"
```

**What it does**:
- Fetches global market data (US stocks close)
- Shows A-share indices (if available)
- Displays portfolio overview
- Provides today's suggestions
- Includes risk warnings

### Mid-Day Updates (10:30 AM & 2:00 PM)

```bash
# 10:30 AM
hermes cron create "30 10 * * *" \
  "cd ~/.hermes/fund-advisor && python scripts/advisor.py morning" \
  --name "基金投资顾问 - 盘中上午简报"

# 2:00 PM
hermes cron create "0 14 * * *" \
  "cd ~/.hermes/fund-advisor && python scripts/advisor.py morning" \
  --name "基金投资顾问 - 盘中下午简报"
```

**What it does**:
- Real-time market movements
- Sector performance
- Portfolio fund alerts
- Trading period reminders

### Evening Summary (4:30 PM)

```bash
hermes cron create "30 16 * * *" \
  "cd ~/.hermes/fund-advisor && python scripts/advisor.py evening" \
  --name "基金投资顾问 - 盘后总结"
```

**What it does**:
- Daily market review
- Portfolio NAV updates
- P&L calculation
- Tomorrow's outlook

### Weekly Review (Sunday 8PM)

```bash
hermes cron create "0 20 * * 0" \
  "cd ~/.hermes/fund-advisor && python scripts/advisor.py weekly-review" \
  --name "基金投资顾问 - 周复盘报告"
```

**What it does**:
- Weekly P&L summary
- Transaction history
- Strategy performance
- Issues and improvements
- Next week's plan

## Managing Jobs

### List All Jobs

```bash
hermes cron list
```

Output example:
```
Found 5 jobs:
1. 基金投资顾问 - 开盘前简报 (d0e60a17e138) - Next: 2026-05-17 08:30
2. 基金投资顾问 - 盘中上午简报 (ccdf4a37866c) - Next: 2026-05-16 10:30
3. 基金投资顾问 - 盘中下午简报 (86acc3b150d1) - Next: 2026-05-16 14:00
4. 基金投资顾问 - 盘后总结 (3f5d576b84ab) - Next: 2026-05-16 16:30
5. 基金投资顾问 - 周复盘报告 (70b63b557233) - Next: 2026-05-17 20:00
```

### Test Job Immediately

```bash
# Run morning briefing now (for testing)
hermes cron run d0e60a17e138
```

### Pause/Resume Jobs

```bash
# Pause a job (e.g., during holidays)
hermes cron pause d0e60a17e138

# Resume later
hermes cron resume d0e60a17e138
```

### Remove Job

```bash
# Delete a job
hermes cron remove d0e60a17e138
```

## ⚠️ CRITICAL: Feishu Delivery Pattern

**Problem**: Cron jobs that produce large reports (>~4000 chars) will FAIL delivery to Feishu with `[99992402] field validation failed`.

**Root cause**: The cron system injects `[IMPORTANT: ... do NOT use send_message or try to deliver the output yourself ...]` into every cron prompt. If the agent follows this and puts the full report in its final response, the cron delivery system tries to send it as one Feishu message → API rejects it.

**Solution**: The job prompt MUST explicitly tell the agent to use `send_message` for chunked delivery. Example prompt structure:

```
步骤：
1. 运行脚本获取报告
2. 过滤掉进度日志（✓📝⚠️🔄开头的行）
3. 用 send_message 工具分段发送（target: feishu）

分段规则：
- 每条消息 ≤ 2500 字符
- 按模块分段，每段单独 send_message

最终回复只写"XXX已发送"即可。
```

**Why this works**: The agent uses `send_message` tool to deliver each chunk directly, bypassing the cron delivery system. The final response ("已发送") is tiny, so cron delivery succeeds trivially.

**Monitoring**: Run `hermes cron list` periodically to check for `⚠ Delivery failed` warnings.

## Delivery Options

### Send to Current Chat (Recommended)

```bash
--deliver "origin"
```

Sends to the current conversation where you created the job.

### Send to Specific Channel

```bash
# Feishu/Lark
--deliver "feishu:oc_a6a554f98bdaea351d79ea539d700a0e"

# Telegram
--deliver "telegram:-1001234567890:17585"

# All connected platforms
--deliver "all"
```

## Troubleshooting

### Job Not Running

**Check**:
```bash
# Verify job exists and is enabled
hermes cron list

# Check job status
hermes cron status
```

**Fix**:
- Verify cron syntax is correct
- Ensure command path is correct
- Check delivery channel is configured
- Review logs: `~/.hermes/logs/`

### Test Command Manually

```bash
# Run the exact command the cron job would run
cd ~/.hermes/fund-advisor && python scripts/advisor.py morning
```

### Check Logs

```bash
# View recent cron job logs
tail -50 ~/.hermes/logs/gateway.log | grep -i "cron\|fund"

# Check for errors
grep -i "error\|failed" ~/.hermes/logs/gateway.log | tail -20
```

## Holiday Handling

**During market holidays** (weekends, Chinese holidays):
- Morning/evening jobs still run but show "market closed"
- Consider pausing jobs during extended holidays:

```bash
# Pause all fund advisor jobs before holiday
hermes cron pause d0e60a17e138  # Morning
hermes cron pause ccdf4a37866c  # Mid-morning
hermes cron pause 86acc3b150d1  # Afternoon
hermes cron pause 3f5d576b84ab  # Evening

# Resume after holiday
hermes cron resume d0e60a17e138
hermes cron resume ccdf4a37866c
hermes cron resume 86acc3b150d1
hermes cron resume 3f5d576b84ab
```

**Note**: Weekly review (Sunday) should remain active.

## Performance Tips

1. **Cache Data**: Fetch market data once per day, reuse for multiple reports
2. **Rate Limiting**: Add delays between API calls to avoid being blocked
3. **Error Handling**: Gracefully handle API failures with fallback data
4. **Logging**: Log all cron job executions for debugging
5. **Notifications**: Only send on significant changes to avoid spam

## Example: Complete Setup Script

```bash
#!/bin/bash
# scripts/setup-all-crons.sh

cd ~/.hermes/fund-advisor

echo "Setting up fund advisor cron jobs..."

# Morning briefing
hermes cron create "30 8 * * *" \
  "cd ~/.hermes/fund-advisor && python scripts/advisor.py morning" \
  --name "基金投资顾问 - 开盘前简报" \
  --deliver "origin"

# Mid-day updates
hermes cron create "30 10 * * *" \
  "cd ~/.hermes/fund-advisor && python scripts/advisor.py morning" \
  --name "基金投资顾问 - 盘中上午简报" \
  --deliver "origin"

hermes cron create "0 14 * * *" \
  "cd ~/.hermes/fund-advisor && python scripts/advisor.py morning" \
  --name "基金投资顾问 - 盘中下午简报" \
  --deliver "origin"

# Evening summary
hermes cron create "30 16 * * *" \
  "cd ~/.hermes/fund-advisor && python scripts/advisor.py evening" \
  --name "基金投资顾问 - 盘后总结" \
  --deliver "origin"

# Weekly review
hermes cron create "0 20 * * 0" \
  "cd ~/.hermes/fund-advisor && python scripts/advisor.py weekly-review" \
  --name "基金投资顾问 - 周复盘报告" \
  --deliver "origin"

echo "✅ All cron jobs created!"
hermes cron list
```

## Related

- See `SKILL.md` for full fund advisor documentation
- See `references/database-schema.md` for data storage details
- See `scripts/advisor.py` for report generation logic
