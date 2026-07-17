# Cron Job Delivery to Feishu — Lessons Learned

## Problem
The cron system's built-in `deliver: "origin"` mechanism consistently fails for Feishu with error `[99992402] field validation failed`. This happens regardless of message size — even 700-character messages fail.

## Root Causes
1. **Cron system injection**: The cron system injects `"do NOT use send_message"` into the agent's system prompt, and `send_message` is NOT in the cron agent's toolset. This makes agent-based message splitting impossible.
2. **`deliver: "origin"` broken for Feishu**: The delivery channel itself fails, even with `no_agent=true` and short messages.
3. **`msg_type: 'text'` doesn't support code blocks**: Plain text messages can't render markdown code blocks in Feishu.

## Solution: Direct Feishu REST API

### Architecture
```
cron job (no_agent=true, deliver: "local")
  → wrapper shell script (~/.hermes/scripts/cron_send_*.sh)
    → Python script (fund-advisor/scripts/cron_send_*.py)
      → Feishu REST API (POST rich text)
```

### Key Configuration
- `no_agent: true` — skip LLM, run script directly
- `deliver: "local"` — suppress cron's built-in delivery (script handles it)
- `script: "cron_send_morning.sh"` — relative path under `~/.hermes/scripts/`
- Shell scripts must be `chmod +x`

### Feishu POST Rich Text Format
```python
# msg_type: 'post' with code blocks
post = {
    "zh_cn": {
        "title": "🌅 早报标题",
        "content": [
            # Normal text line
            [{"tag": "text", "text": "普通文本"}],
            # Bold text
            [{"tag": "text", "text": "加粗文本", "style": ["bold"]}],
            # Code block (CRITICAL for tables) — MUST use code_block tag, NOT style:["code"]
            [{"tag": "code_block", "language": "plaintext", "text": "表格内容"}],
        ]
    }
}

# API endpoint
POST https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id
Headers: Authorization: Bearer {tenant_access_token}
Body: {receive_id, msg_type: 'post', content: json.dumps(post)}
```

### Getting tenant_access_token
```python
POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal
Body: {app_id, app_secret}  # from ~/.hermes/.env (FEISHU_APP_ID, FEISHU_APP_SECRET)
```

### Chat ID
`oc_a6a554f98bdaea351d79ea539d700a0e` (user's primary Feishu chat)

### Script Files (Full Version)
The full version runs `advisor.py`, parses output by 【】 sections, identifies ``` code blocks ```, and sends via Feishu POST API in multiple messages (≤3500 chars each).

| Report | Python Script | Shell Wrapper |
|--------|--------------|---------------|
| Morning | `cron_send_full.py morning` | `cron_send_full_morning.sh` |
| Intraday AM | `cron_send_full_intraday.py morning` | `cron_send_full_intraday_morning.sh` |
| Intraday PM | `cron_send_full_intraday.py afternoon` | `cron_send_full_intraday_afternoon.sh` |
| Evening | `cron_send_full.py evening` | `cron_send_full_evening.sh` |
| Weekly | `cron_send_full.py weekly` | `cron_send_full_weekly.sh` |

Legacy simplified versions (`cron_send_morning.py`, etc.) also exist but produce minimal output.

### Suppressing Progress Logs
Scripts use `SilentStdout` context manager to suppress import-time print statements from data_fetcher, market_sentiment, etc. Restore stdout before generating report output.

## Pitfalls
1. **Never use `msg_type: 'text'`** — no code block support, tables won't render
2. **Never use `style: ["code"]`** — must use `{"tag": "code_block", "language": "plaintext", "text": "..."}` for code blocks
3. **`script` field = file path**, not shell command. `cd ~/.hermes/fund-advisor && python ...` fails as a script path
4. **Old `last_delivery_error` persists** in cron job state even after successful runs — ignore it
5. **`deliver: "origin"` is broken for Feishu** — always use `deliver: "local"` + direct API
6. **Chinese character alignment** in code blocks requires `display_width()` function (Chinese = 2 width units)
7. **Progress log filtering** — advisor.py outputs progress lines starting with 🔄✓📝🤖🚀 that must be filtered before sending
8. **Title extraction** — first line like "🌅 正在生成开盘前报告..." is a progress log, not the title. Match `🌅 **早安！...**` pattern and strip `**`
9. **⚠️ NEVER change `deliver` to `"origin"` for script-based jobs** — When `no_agent=true` with a script that calls Feishu API directly, `deliver` MUST be `"local"`. Changing to `"origin"` causes the cron system to ALSO try delivering the script's stdout via Hermes `send_message`, which fails with `[99992402]`. The script handles delivery itself; Hermes delivery must be suppressed.
