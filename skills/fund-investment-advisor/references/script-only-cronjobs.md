# Fund Advisor Cronjob Configuration

## ⚠️ DEPRECATED: Script-Only Mode (no_agent=true)

**Script-only mode is NOT recommended for fund advisor reports on Feishu.**

**Why it was deprecated (2026-05-29)**:
- Fund advisor reports are 10-15KB (200+ lines)
- Feishu single-message limit is ~4-5KB
- `no_agent=true` delivers stdout as one message → **silent truncation**
- User only sees first half of report, missing strategy advice and action items
- `no_agent` field cannot be toggled via `cronjob update` — must delete and recreate

**When script-only mode IS still appropriate**:
- Short outputs (< 3KB), e.g., NAV update status, data validation results
- Non-Feishu delivery targets with higher message limits
- `--deliver "local"` (no delivery, just save)

## Recommended: Agent Mode (no_agent=false)

Agent mode is the default. The LLM processes the output and can:
1. Filter out progress/debug lines (✓, 📝, ⚠️, 🔄)
2. Split long reports into multiple messages
3. Preserve formatting with explicit instructions

### Setup

No script files needed. The agent runs the commands directly.

```bash
# Morning briefing (8:30 AM) - AGENT MODE with send_message delivery
hermes cron create "30 8 * *" \
  "运行基金投资顾问开盘前简报脚本，然后将报告分段发送给用户。

步骤：
1. 运行 \`cd ~/.hermes/fund-advisor && python scripts/update_nav_cur.sh\`（更新净值，可能失败，忽略错误继续）
2. 运行 \`cd ~/.hermes/fund-advisor && python scripts/advisor.py morning\`
3. 过滤掉脚本输出中的进度日志（✓📝⚠️🔄开头的行）
4. 将报告内容用 send_message 工具分多条发送给用户（target: feishu）

分段规则：
- 每条消息必须 ≤ 2500 字符
- 按模块自然分段，每个section单独一条消息

重要：你必须用 send_message 工具逐段发送报告！最终回复只写"早报已发送"即可。" \
  --name "基金投资顾问 - 开盘前简报" \
  --deliver "origin"
```

### Prompt Template

Each cron job prompt should include:
1. **What script to run** (with full path)
2. **Filter instruction** (remove progress lines starting with ✓, 📝, ⚠️, 🔄)
3. **Use send_message for delivery** (must explicitly say to use `send_message(target='feishu')`)
4. **Split instruction** (each segment ≤ 2500 chars, split by module/section)
5. **Final response** (just a short confirmation like "XXX已发送")

Example prompt structure:
```
步骤：
1. 运行脚本 `cd ~/.hermes/fund-advisor && python scripts/advisor.py morning`
2. 过滤掉进度日志（✓📝⚠️🔄开头的行）
3. 用 send_message 工具分段发送（target: feishu），每段 ≤ 2500 字符

最终回复只写"早报已发送"即可。
```

### Pitfalls

1. **`no_agent` cannot be toggled via update** — must delete and recreate
2. **Agent may occasionally reformat** — add "保持原始的代码块格式和列对齐" to prompt
3. **Progress logs waste character budget** — always instruct agent to filter them
4. **Each message should be self-contained** — user may read messages out of order
5. **⚠️ CRITICAL: send_message contradiction (fixed 2026-06-01)** — The cron system injects `[IMPORTANT: ... do NOT use send_message ...]` into every prompt. If the agent follows this and puts the full report in its final response, the cron delivery system tries to send it as one Feishu message → `[99992402] field validation failed`. The job prompt MUST explicitly tell the agent to use `send_message(target='feishu')` for chunked delivery, and make the final response just a short confirmation like "已发送". This overrides the cron system's injected instruction.
6. **Max segment size**: ≤ 2500 characters per `send_message` call to Feishu.

## Script-Only Mode (Legacy, for short outputs only)

Use `no_agent=true` ONLY for short outputs that won't be truncated:

```bash
# NAV update (delivers ~200 chars) - OK for script-only
hermes cron create "0 9 * * *" \
  "[SILENT]" \
  --name "基金净值每日更新" \
  --script "update-nav-cron.sh" \
  --no-agent true \
  --deliver "local"
```

### Script File Setup

```bash
# Morning briefing script (still useful for manual testing)
cat > ~/.hermes/scripts/fund-morning-cron.sh << 'EOF'
#!/bin/bash
cd ~/.hermes/fund-advisor
python scripts/advisor.py morning
EOF
chmod +x ~/.hermes/scripts/fund-morning-cron.sh
```

### Cronjob Parameters

| Parameter | Description |
|-----------|-------------|
| `--no-agent true` | Disable LLM, deliver stdout verbatim |
| `--prompt "[SILENT]"` | Required placeholder when no_agent=true |
| `--script "file.sh"` | Script in `~/.hermes/scripts/` |
| `--deliver "origin"` | Deliver to current chat |

### When Script-Only Output is Truncated

**Detection**: `wc -c ~/.hermes/cron/output/<job_id>/<latest>.md` > 5000

**Fix**:
1. Delete: `hermes cron remove <job_id>`
2. Recreate without `--no-agent true` (agent mode is default)
3. Add split/filter instructions to prompt

## Related Resources

- `SKILL.md` - Main fund investment advisor skill (cron setup section)
- `references/code-block-formatting.md` - Table formatting standards
- `references/table-alignment-guide.md` - Column alignment best practices
