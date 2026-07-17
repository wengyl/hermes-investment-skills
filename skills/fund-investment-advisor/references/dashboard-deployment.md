# Real-Time Fund Dashboard v2 (Web UI)

A Flask + Plotly web dashboard that displays portfolio data **with live market data** in real time.
All-in-one `app.py`, dark single-page SPA, Plotly from CDN, auto-refresh every 5 minutes.

## Architecture

```
~/.hermes/fund-advisor/dashboard/
  └── app.py          # Flask server (single file): routes, live data fetching, HTML/JS inline
```

**v2 consolidates** what used to be `data.py`, `charts.py`, and `templates/dashboard.html` into one file.
Everything — DB queries, real-time curl fetches, Plotly chart config, HTML/JS template — lives in `app.py`.

**Thin API layer**: `/api/data` returns full dashboard JSON; `/` renders HTML via `render_template_string`.
**No AJAX page loading**: all data fetched inline during server-render; JS renders Plotly charts client-side from the injected JSON.

## Live Data Sources (fetched inline per page-load via curl)

| Source | Data | API |
|--------|------|-----|
| eastmoney (天天基金) | Fund real-time estimated NAV | `http://fundgz.1234567.com.cn/js/{code}.js` |
| eastmoney push2 | A-share indices, Northbound flow | `https://push2.eastmoney.com/api/qt/ulist.np/get` & `kamt.kline/get` |
| Sina finance | US stocks, HK stocks, FX, Gold | `https://hq.sinajs.cn/list=gb_*,rt_hkHSI,USDCNY,hf_GC` |
| akshare (optional) | Macro signals: PMI, CPI, M2 | `ak.macro_china_pmi()`, `ak.macro_china_cpi()` (⚠️ use MONTHLY, NOT `macro_china_cpi_yearly()` — yearly returns stale data, stuck at ~2025-08 with 0.0%), `ak.macro_china_money_supply()` |

All data is fetched synchronously at page request time. No caching, no background jobs — always live.

## API Endpoints

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/` | GET | Full dashboard HTML (server-rendered with inline data) |
| `/health` | GET | `{"status":"ok","timestamp":"..."}` |
| `/api/data` | GET | Full dashboard JSON — holdings, metrics, realtime NAV, market indices, macro, alerts |

## Dashboard Layout (v2)

```
┌──────────────────────────────────────────────┐
│ 💰 投资看板          🟢 2026-07-13 16:28:11  │
├──────────────────────────────────────────────┤
│ 📊 Market Ticker                             │
│ 上证 3914 -2.06% │ 创业板 3724 -3.10% │ ...  │
│ 标普500 7575 +0.42% │ 恒指 24214 +0.16%│ ...  │
├──────────────────────────────────────────────┤
│ KPI Cards (live)                             │
│ 总市值 ¥17179 │ 净投入 ¥16066 │ 总盈亏 +1113  │
│ 今日预估 -455 (-2.65%) │ 11只 │ 4个主题│
├──────────────────────────────────────────────┤
│ 🎨 主题配置 (Themed Allocation Bar)          │
│ [红利低波 39.6%][AI算力 27.0%][畜牧 ...]     │
├──────────────────────────────────────────────┤
│ 📊 持仓明细表 (15 columns)                   │
│ 代码/名称│分类│主题│份额│净值│实时估值│今日涨幅│
│ 市值│盈亏│盈亏%│7日│30日│止损│止盈│仓位%│
├──────────────────┬───────────────────────────┤
│ 📈 净值走势(30天) │  🥧 仓位分布(饼图)       │
│  [Plotly line]   │       [Plotly pie]       │
├──────────────────┼───────────────────────────┤
│ 💸 盈亏分布(柱状) │  📅 DCA 定投记录         │
│  [Plotly bar]    │   (table)                │
├──────────────────┴───────────────────────────┤
│ 📊 宏观信号 (PMI / CPI / M2)                 │
├──────────────────────────────────────────────┤
│ 🔄 最近交易 (table)                          │
└──────────────────────────────────────────────┘
```

## Key v2 Features Added

1. **Real-time fund estimates** — per-fund estimated NAV + % change from eastmoney, with update timestamp
2. **Market ticker bar** — A-share 5 indices, US 3 indices, HK, FX, Gold, Northbound flow, all fetched live
3. **Fund category metadata** — each fund tagged with category (行业指数/科技主题/港股海外/灵活配置) and theme (AI算力/红利低波/畜牧农业/科技成长)
4. **Stop-loss / take-profit alerts** — per-fund thresholds from `fund_categorizer.py` config; alerts rendered as banner above the table when thresholds are breached or approached
5. **Theme allocation bar** — horizontal colored bar showing portfolio % per theme
6. **Macro signals panel** — PMI, CPI, M2 fetched from akshare with bullish/neutral/bearish coloring
7. **7-day / 30-day return columns** — per-fund short-term performance computed from NAV history
8. **Today's estimated P&L** — aggregate portfolio change based on real-time fund estimates

## v3: Multi-User + Manual Import

v3 adds login/register/auth, user-isolated data (holdings/transactions/dca by user_id), manual single and batch fund import, transaction recording, and admin user management.

See `references/dashboard-multi-user.md` for full API docs, auth pattern, custom password hashing, and schema changes.

## Key Technical Details

### Directory & Dependencies

```bash
# Dependencies (one-time)
pip3 install flask plotly akshare
```

### app.py Structure

The file is ~900 lines. Sections (in order):
1. **Imports & DB helpers**
2. **Data fetching** - `fetch_realtime_nav()`, `fetch_market_indices()`, `fetch_macro_signals()` — all use `subprocess.run` with `curl` for HTTP; akshare only for macro
3. **Fund category metadata** — hardcoded dict with code→{category, theme, stop_loss, take_profit}
4. **DB queries** — holdings, NAV history, transactions, DCA log, user_config
5. **Metrics computation** — portfolio-level and per-fund P&L, weight %, 7d/30d returns, stop-loss/take-profit alerts
6. **HTML template** — ~300 lines of Jinja2-style inline HTML + embedded JS for Plotly rendering
7. **Flask routes** — `/`, `/api/data`, `/health`

### Flask rendering technique

```python
from flask import render_template_string

@app.route('/')
def dashboard():
    data = build_dashboard_data()          # dict with all data
    data_json = json.dumps(data, ...)      # inline JSON
    return render_template_string(HTML_TEMPLATE, data_json=data_json)
# HTML_TEMPLATE references {{ data_json | safe }} and passes to JS via `const rawData = ...`
```

Use `| safe` Jinja2 filter to prevent Flask's auto-escape from converting JSON quotes to `&#34;`.

### Plotly Rendering (client-side, from inline data)

All four charts use `Plotly.newPlot('chartId', traces, layout, config)` called in `<script>` after the data is in `rawData`:

- **navChart** — one trace per fund, normalized to base=100, 30 days of data
- **pieChart** — holdings by current value, `hole: 0.6` for donut shape
- **pnlBar** — per-fund absolute P&L, green/red bars, sorted by value

All charts use:
- `paper_bgcolor: 'transparent'`, `plot_bgcolor: 'transparent'`
- `font.color: '#888'`
- `displayModeBar: false`
- Colors: `['#4facfe', '#00d68f', '#fa709a', '#a18cd1', '#ffd700', '#ff9a9e', '#43e97b', '#f093fb', '#fee140', '#00f2fe', '#f5576c']`

### Fund Category Metadata (hardcoded)

Keep an inline `FUND_CATEGORIES` dict in `app.py` with code→{category, theme, stop_loss, take_profit}.
When `fund_categorizer.py` config changes, sync this inline dict.

### Refresh Strategy

- Page auto-refreshes every 5 minutes with `setTimeout(() => location.reload(), 300000)`
- No meta refresh tag — avoids full browser reload flicker if JS fails

## Pitfalls

1. **Flask HTML entity escaping**: JSON data passed to `render_template_string` via `{{ data_json | safe }}` — without `| safe`, Flask converts `"` to `&#34;`, breaking all JavaScript. Always use `| safe` on the inline JSON variable.
2. **Fund estimate API closing time**: China fund estimates show as `0.00` outside trading hours (weekends, after 15:00). Check `gztime` field — if it's yesterday's date or outside 09:30-15:00 on a weekday, the estimate should be treated as stale and fall back to the DB's last NAV.
3. **akshare availability**: Some akshare endpoints (especially macro) fail occasionally due to upstream API changes. The dashboard treats macro fetch errors gracefully (shows "暂无宏观数据" card). Do not let akshare failures crash the page.
4. **Market data during non-trading hours**: A-share indices return stale values outside 09:30-15:00 CST. US/hk indices may be current if their market is open. The dashboard renders them all — user needs to know timezone context.
6. **Rate limiting**: Multiple curl calls per page load (~15-20) on every refresh. The 5-minute auto-refresh cadence is generous enough for eastmoney/sina, but keep an eye on connection latency. If page load becomes slow, consider caching market data for 60s.
7. **CPI data source: use macro_china_cpi() not macro_china_cpi_yearly()** — The yearly variant (`ak.macro_china_cpi_yearly()`) returns data stuck at 2025-08 with 0.0% CPI. The correct source is `ak.macro_china_cpi()` which returns monthly data and is current (e.g., 2026-06 with 1.0%). When CPI=0.0 appears on the dashboard, it's always this stale-data bug, not actual zero inflation.
8. **JS field name must match backend JSON key exactly** — When adding new frontend modules that consume `/api/data` JSON, the JavaScript field name MUST exactly match the Python dict key returned by `build_dashboard_data()`. Mismatch example: JS used `d.impact` but backend returned `d.impact_pct` → rendered as `undefined%`. Fix: grep both Python return dict keys and JS property accesses to confirm alignment before deploying.
9. **LaunchAgent KeepAlive re-spawns old code after manual kill** — When restarting via `kill $(lsof -ti :8787)`, the LaunchAgent's `KeepAlive=true` immediately restarts the process using the OLD `app.py` (still loaded in memory from the original launchd spawn). You must kill TWICE: first kill drops the manual process, launchd spawns the old code; second kill gets the launchd-spawned copy. Or use `launchctl bootout gui/$(id -u)/com.your-org.fund-dashboard 2>/dev/null; launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.your-org.fund-dashboard.plist` for clean restart.

## Dashboard Layout

```
┌─────────────────────────────────────────────┐
│ 💼 投资看板         2026-07-13 15:48:16      │
│                                             │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐        │
│ │总市值 │ │净投入 │ │总盈亏 │ │持仓数│        │
│ │¥18063│ │¥16066│ │+1997 │ │ 11只 │        │
│ │      │ │      │ │12.43%│ │      │        │
│ └──────┘ └──────┘ └──────┘ └──────┘        │
│                                             │
│ 持仓明细 (11只)                              │
│ 代码  名称        份额   净值  市值   盈亏%   │
│                                               │
│ ┌──────────────┐ ┌──────────────┐            │
│ │ 净值走势(30天)│ │ 仓位分布(饼图)│            │
│ │  [Plotly]    │ │  [Plotly]   │            │
│ └──────────────┘ └──────────────┘            │
│ ┌──────────────┐ ┌──────────────┐            │
│ │ 盈亏排行(柱) │ │ 定投/DCA记录 │            │
│ └──────────────┘ └──────────────┘            │
│ 最近交易                                      │
└─────────────────────────────────────────────┘
```

## Charts (Plotly)

All charts use `plotly.graph_objects` with a consistent dark theme (`plotly_dark` template).

### 净值走势图 (30-Day Trend)
- One line per holding fund
- Normalized to % change from t-30 for fair comparison
- Hover shows absolute NAV
- Color-coded per fund

### 仓位分布饼图 (Portfolio Allocation)
- Pie chart showing each fund's market value share
- Separate legend with exact percentages
- "其它" slice for <5% positions

### 盈亏排行柱状图 (P&L Ranking)
- Horizontal bar chart
- Green bars for profit, red for loss
- Sorted by P&L descending (best at top, worst at bottom)
- Shows both ¥amount and % on hover

## Deployment (macOS)

### Dependencies (installed once)
```bash
pip3 install flask plotly jinja2
```

### Manual Start
```bash
cd ~/.hermes/fund-advisor/dashboard && python3 app.py
# Serves on http://localhost:8787
```

### LaunchAgent (Auto-Start / Crash Recovery)
Plist at `~/Library/LaunchAgents/com.your-org.fund-dashboard.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.your-org.fund-dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>~/.hermes/fund-advisor/venv/bin/python3</string>
        <string>~/.hermes/fund-advisor/dashboard/app.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>~/.hermes/fund-advisor/dashboard</string>
    <key>KeepAlive</key>
    <true/>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/fund-dashboard.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/fund-dashboard.error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

**Commands:**
```bash
# Load / start
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.your-org.fund-dashboard.plist

# Unload / stop
launchctl bootout gui/$(id -u)/com.your-org.fund-dashboard 2>/dev/null

# Check status
launchctl list com.your-org.fund-dashboard

# View logs
tail -f /tmp/fund-dashboard.log
tail -f /tmp/fund-dashboard.error.log
```

### Cloudflare Tunnel Exposure

Use existing tunnel config (`~/.cloudflared/config.yaml`) to route a subdomain:

```yaml
tunnel: <tunnel-uuid>
credentials-file: ~/.cloudflared/<tunnel-uuid>.json
ingress:
  - hostname: invest.your-domain.com
    service: http://localhost:8787
  - hostname: your-domain.com
    service: http://localhost:3008
  - service: http_status:404
```

**DNS**: Add CNAME record `invest.your-domain.com → <tunnel-uuid>.cfargotunnel.com`

**Restart tunnel** after config change:
```bash
hermes gateway restart
# Or directly:
launchctl kickstart gui/$(id -u)/com.your-org.cloudflared 2>/dev/null
```

## Key Technical Details

### data.py — DB Queries

```python
from config import Config

def get_dashboard_data():
    """Return a dict of all dashboard data."""

    # 1. Holdings with latest NAV
    cursor.execute("""
        SELECT h.fund_code, h.fund_name, h.share_count, h.avg_cost,
               h.total_invested, h.total_withdrawn, h.current_value,
               n.unit_nav, n.nav_date
        FROM holdings h
        LEFT JOIN (
            SELECT fund_code, unit_nav, nav_date,
                   ROW_NUMBER() OVER (PARTITION BY fund_code ORDER BY nav_date DESC) as rn
            FROM fund_nav_history
        ) n ON h.fund_code = n.fund_code AND n.rn = 1
        WHERE h.share_count > 0 OR h.current_value > 0
        ORDER BY h.current_value DESC
    """)
    # ... compute market_value, pnl, pnl_pct per fund

    # 2. NAV history for charts (last 120 days)
    cursor.execute("""
        SELECT fund_code, nav_date, unit_nav
        FROM fund_nav_history
        WHERE nav_date >= date('now', '-120 days')
        ORDER BY nav_date
    """)

    # 3. Transactions (last 50)
    cursor.execute("""
        SELECT fund_code, fund_name, transaction_type, amount, shares,
               price, transaction_date
        FROM transactions
        ORDER BY transaction_date DESC
        LIMIT 50
    """)

    # 4. DCA plans
    cursor.execute("""
        SELECT fund_code, fund_name, amount, frequency, next_run_date
        FROM dca_plans WHERE status = 'active'
    """)
```

### charts.py — Plotly Generation

Always use `import plotly.graph_objects as go` (not `plotly.express`) for explicit control.

**Dark theme**:
```python
TEMPLATE = {
    'layout': {
        'template': 'plotly_dark',
        'paper_bgcolor': '#000000',
        'plot_bgcolor': '#111111',
        'font': {'color': '#e0e0e0', 'size': 11},
        'xaxis': {'gridcolor': '#2a2a2a'},
        'yaxis': {'gridcolor': '#2a2a2a'},
        'margin': {'l': 40, 'r': 20, 't': 30, 'b': 50},
    }
}
```

**Chart mode**:
```python
fig.update_layout(hovermode='x unified')  # single hover tooltip
```

**Pie chart colors**: Use `px.colors.sequential.Mint` for allocation pies — warm tones on pure black.

### app.py — Flask Server

- Port: `8787`
- Host: `0.0.0.0` (accessible from Cloudflare Tunnel)
- Debug off
- Single route: `/api/data` → JSON, `/` → rendered dashboard.html

**Key API endpoint** (aggregate metrics):
```python
@app.route('/api/data')
def api_data():
    data = get_dashboard_data()
    return jsonify({
        'holdings': data['holdings'],
        'metrics': {
            'total_current_live': sum(h['market_value'] for h in data['holdings']),
            'net_invested': sum(h['total_invested'] - h['total_withdrawn'] for h in data['holdings']),
            'total_pnl_live': sum(h['pnl'] for h in data['holdings']),
            'total_pnl_live_pct': sum(h['pnl'] for h in data['holdings']) / max(sum(h['total_invested'] - h['total_withdrawn'] for h in data['holdings']), 1) * 100,
        },
        'nav_history': data['nav_history'],
        'transactions': data['transactions'][:10],
        'dca_log': data['dca_plans'],
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    })
```

### dashboard.html Template

- Pure black background (`bg-black text-white`)
- No CSS frameworks (vanilla inline styles only)
- Plotly JS loaded from CDN: `https://cdn.plot.ly/plotly-2.35.2.min.js`
- Each chart rendered in a `<div id="chart-xxx">` with exact height/width
- Tables in `<pre>` blocks styled as code-block tables for Feishu-consistent readability
- Loading state: show `<p class="text-center text-gray-500">⏳ 加载中...</p>` until JSON fetch completes
- JSON fetch with `fetch('/api/data')` → split into holdings/nav_history/charts → render

## When to Use / Not Use

**Use when**: user asks for a live web view of portfolio, "看板", "dashboard", "实时监控页面"
**Do NOT use**: for cron-based text reports (those stay with advisor.py). The dashboard complements — does not replace — daily Morning/Evening reports.
**Alternative**: If no web deployment is wanted, use `advisor.py morning` or `advisor.py report` for terminal output.
