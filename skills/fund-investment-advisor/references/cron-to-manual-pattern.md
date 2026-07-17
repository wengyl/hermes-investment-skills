# Cron-to-Manual Pattern: Replace Push with Pull

This user explicitly chose to replace automated cron-briefing push delivery with a
manual "生成总结" button in the dashboard. The pattern applies whenever cron-based
daily reports are too noisy or the user prefers on-demand summaries.

## When to Apply

The user says "移除播报" or reports that daily cron briefings are "太零散了" (too
scattered). This is a PREFERENCE signal, not a bug — document the decision in
`user_config.py` and convert cron jobs to manual buttons.

## Conversion Steps

### 1. Remove cron jobs

```bash
# List all cron jobs
hermes cron list

# Remove each briefing cron
hermes cron remove <job_id_1>
hermes cron remove <job_id_2>
# ... repeat for all briefing jobs
```

### 2. Add Flask API endpoint

In the dashboard `app.py`, add a `/api/briefing` endpoint that calls the advisor CLI:

```python
@app.route('/api/briefing', methods=['POST'])
def api_briefing():
    if not session.get('logged_in'):
        return jsonify({'error': 'Not logged in'}), 401
    data = request.get_json()
    report_type = data.get('type', 'evening')
    # Map type to advisor.py arg
    type_map = {
        'morning': 'morning',
        'morning_intraday': 'morning_intraday',
        'evening': 'evening',
        'weekly': 'weekly',
    }
    arg = type_map.get(report_type, 'evening')
    try:
        import subprocess, sys
        result = subprocess.run(
            ['python3', 'scripts/advisor.py', arg],
            capture_output=True, text=True, timeout=180,
            cwd=DASHBOARD_DIR
        )
        output = result.stdout or result.stderr
        return jsonify({
            'content': output,
            'title': TIME_TITLES.get(report_type, '投资报告'),
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

Key design choices:
- Non-blocking: runs in a thread to avoid timeout
- Returns JSON with `content` (HTML/markdown), `title`, `generated_at`
- No cron logic — one-shot execution only

### 3. Add frontend button + modal

Insert a button in the dashboard header area:

```html
<button onclick="openBriefingModal()" style="...">📊 生成总结</button>
```

Modal with:
- Type selector (盘后总结 / 开盘前简报 / 盘中简报 / 周度复盘)
- Loading state with rotating spinner
- Content area with rendered report
- Close button

### 4. JS fetch function

```javascript
async function generateBriefing(type) {
    showLoading(true);
    try {
        const resp = await fetch('/api/briefing', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({type: type})
        });
        const data = await resp.json();
        if (data.error) { showError(data.error); return; }
        renderBriefing(data);
    } catch(e) { showError(e.message); }
    showLoading(false);
}
```

### 5. Keep non-briefing cron jobs

Only remove the report-delivery cron jobs. Keep infrastructure cron jobs:
- NAV data updates (09:00, 20:00)
- DCA execution (20:00)
- Monthly/weekly strategy evaluations (these are internal, not user-facing)

## Trade-offs

| Aspect | Cron Push | Manual Button |
|--------|-----------|---------------|
| Effort | Zero (every day) | Click + 10-30s wait |
| Timeliness | Fixed schedule | On demand |
| Signal/noise | 1 report/day whether useful or not | Only when user wants it |
| Maintenance | 5 cron jobs to maintain | 1 button, 1 API endpoint |
| Gateway impact | Must survive delivery failures | Returns within HTTP timeout |

## Pitfalls

- **Cron remnants**: After removing briefings, check `hermes cron list` for any stale
  delivery-only jobs that reference deleted scripts
- **Login required**: The `/api/briefing` endpoint must check `session.get('logged_in')` —
  unauthenticated access returns 401
- **Timeout**: advisor.py can take 30-180s. Set a generous HTTP timeout or use streaming
- **Modal positioning**: On mobile/Feishu, modals may not scroll properly. Use
  `overflow-y: auto` and `max-height: 80vh`
