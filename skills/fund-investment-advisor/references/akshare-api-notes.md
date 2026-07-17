# akshare API Notes for Fund Advisor System

## SSL Compatibility Fix (2026-06-11)

### Root Cause
`requests` library's `HTTPSConnectionPool` has TLS handshake incompatibility with eastmoney servers (`fundf10.eastmoney.com`). The connection works fine at socket level (both IPv4/IPv6) and with `urllib3.PoolManager` directly, but fails inside requests' connection pool.

Error: `SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol')`

**Affected**: macOS system Python 3.9.6 + LibreSSL 2.8.3, AND Homebrew Python 3.11 + OpenSSL 3.6.1. Both fail.

### Fix: ssl_patch.py
Create `scripts/ssl_patch.py` — monkey-patches `requests.adapters.HTTPAdapter.send` to fallback to `urllib3.PoolManager` on SSLError. Import it at the top of any script that calls akshare:

```python
import sys; sys.path.insert(0, 'scripts'); import ssl_patch
```

The patch is idempotent (safe to import multiple times).

### Why curl works but requests doesn't
curl uses its own TLS stack. urllib3.PoolManager creates fresh connections. requests' HTTPSConnectionPool reuses connections and has different SSL context initialization that triggers the EOF.

---

## Proxy Bypass for AKShare (macOS + Clash Verge)

### Problem
macOS system proxy (Clash Verge, port 7897) is picked up by Python `requests` library **even when `HTTP_PROXY`/`HTTPS_PROXY` env vars are empty**. macOS stores proxy in system preferences (`networksetup`), and `requests` reads it via `scutil --proxy`.

Error: `ProxyError('Unable to connect to proxy', RemoteDisconnected(...))`

### Why `NO_PROXY='*'` doesn't work
Setting `NO_PROXY='*'` and unsetting env vars doesn't help because `requests` on macOS uses `urllib3` which reads the macOS system proxy from `SystemConfiguration` framework, bypassing environment variables entirely.

### Fix: Use curl subprocess + direct East Money API
Bypass `requests` entirely by calling `curl --noproxy '*'` via `subprocess`:

```python
import subprocess, json

url = (
    "https://82.push2.eastmoney.com/api/qt/clist/get?"
    "pn=1&pz=500&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281"
    "&fltt=2&invt=2&fid=f6"
    "&fs=m%3A0+t%3A6%2Cm%3A0+t%3A80%2Cm%3A1+t%3A2%2Cm%3A1+t%3A23%2Cm%3A0+t%3A81+s%3A2048"
    "&fields=f2,f3,f6,f12,f14"
)
result = subprocess.run(['curl', '-s', '--noproxy', '*', url], capture_output=True, timeout=15)
data = json.loads(result.stdout)
```

### East Money Direct API Reference
Base: `https://82.push2.eastmoney.com/api/qt/clist/get`

| Param | Meaning |
|-------|---------|
| `pn` | Page number (1-indexed) |
| `pz` | Page size (max 500) |
| `fid=f6` | Sort by turnover (成交额) |
| `po=1` | Descending order |
| `fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048` | A-shares filter |

Field codes: `f2`=最新价, `f3`=涨跌幅, `f6`=成交额, `f12`=代码, `f14`=名称

### Pagination
Total count is in `data.total`. Loop `pn=1,2,3...` until `len(all_stocks) >= total`.

---

## Market Concentration (交易集中度)

Formula: `(Top N 个股成交额合计 ÷ 全市场总成交额) × 100%`

Typical reference levels (A-shares):
- Top 10: 5-10% → normal; >15% → heavy concentration
- Top 100: 30-40% → normal; >50% → extreme concentration

High concentration in specific sectors (e.g., all Top 20 are semiconductors) signals sector rotation / theme-driven market.

### General pattern
For ANY akshare function that fails with proxy errors, extract the underlying HTTP request and call it via `curl --noproxy '*'` subprocess instead.

---

## Index PE Data (stock_index_pe_lg)

Added 2026-07-11 to `advisor.py` as `_get_index_pe_summary()`.

Function: `ak.stock_index_pe_lg(symbol="沪深300", start_date="20250101", end_date="20260711")`

Returns a DataFrame with columns: `date`, `pe`, `pe_ttm`, `pb`, and cumulative percentile (historically ordered by date).

### Indices Available
- `沪深300` — 大盘价值 (large-cap value)
- `中证500` — 中盘成长 (mid-cap growth)
- `上证50` — 超大盘 (mega-cap)
- `中证100` — 宽基 (broad-based)

### Subprocess Pattern (SSL/Proxy workaround)

Since akshare's `requests` library may proxy through Clash Verge on macOS, call it in a subprocess:

```python
proc = subprocess.run(
    [sys.executable, '-c', f'''
import akshare as ak
df = ak.stock_index_pe_lg(symbol="{name}", start_date="20250101", end_date="{today}")
if not df.empty:
    df = df.sort_values("date")
    df["pct"] = df["pe_ttm"].rank(pct=True) * 100
    latest = df.iloc[-1]
    print(f"{{latest['pe_ttm']:.1f}}|{{latest['pct']:.1f}}")
'''],
    capture_output=True, timeout=15
)
```

### Critical: Handle ALL 3 subprocess cases
1. `proc.returncode != 0` → row shows `N/A`
2. `proc.returncode == 0` but `proc.stdout.strip()` empty → row shows `N/A`
3. Valid output → parse `pe|pct`

Always iterate `indices` list and produce exactly one row per index. Never skip indices — display N/A for failed ones.

### Valuation Ranges
- `pe_pct < 20` → 🟢低估 (undervalued)
- `20 <= pe_pct < 40` → 🔵偏低 (slightly low)
- `40 <= pe_pct < 60` → 🟢合理 (fair)
- `60 <= pe_pct < 80` → 🟡偏高 (slightly high)
- `pe_pct >= 80` → 🔴高估 (overvalued)

---

---

## Fund-Level PE from Holdings (`_get_fund_pe_summary()`)

Added 2026-07-11 to `advisor.py`. Computes fund-level PE(TTM) by weighting individual stock PE from each fund's top-10 holdings. This shows the "effective PE" of each fund — what valuation level its stock portfolio trades at.

### Why not direct fund PE?

Most Chinese mutual funds do NOT publish a "fund PE" metric. The only way to estimate it is:
1. Get fund's top 10 stock holdings (weight %)
2. Get each stock's PE(TTM) from valuation API
3. Compute weighted average: `Σ(holding_weight × stock_PE) / Σ(holding_weight)`

### Data Pipeline

```text
Fund Code
  → ak.fund_portfolio_hold_em(symbol=code, date='2026')    # top 10 holdings
  → A-share stocks: ak.stock_individual_valuation_baidu(stock=code)   # PE(TTM)
  → HK stocks:      ak.stock_hk_valuation_baidu(symbol=code)         # PE(TTM)
  → Weighted average by 占净值比例
  → Coverage ratio (what % of holdings had valid PE data)
```

### API: stock_individual_valuation_baidu

```python
df = ak.stock_individual_valuation_baidu(stock="600519")
```
Returns DataFrame with columns: `date`, `市盈率-动态`, `市净率`, `总市值`, `总股本`
- Sort by date descending; latest row is `df.iloc[0]`
- Call this in a subprocess (SSL/proxy workaround) — same pattern as index PE

### API: stock_hk_valuation_baidu (for QDII/HK holdings)

```python
df = ak.stock_hk_valuation_baidu(symbol="01810")
```
Same output columns as A-share Baidu PE. Use for HK-listed stocks in QDII funds.

### Subprocess pattern (SSL/Proxy workaround)

Since akshare uses `requests` and macOS Clash Verge proxy interferes:

```python
def _get_stock_pe_via_subprocess(stock_code: str) -> float:
    """Get PE(TTM) for a single stock via subprocess + akshare.\n    Returns float or None on failure."""
    if stock_code.startswith('6') or stock_code.startswith('0') or stock_code.startswith('3'):
        func = 'stock_individual_valuation_baidu'
        param = f'stock="{stock_code}"'
    else:
        func = 'stock_hk_valuation_baidu'
        param = f'symbol="{stock_code}"'
    
    code = (
        f'import akshare as ak; import pandas as pd; '
        f'df = ak.{func}({param}); '
        f'if not df.empty: print(df.sort_values("date", ascending=False).iloc[0]["市盈率-动态"])'
    )
    proc = subprocess.run(
        [sys.executable, '-c', code],
        capture_output=True, timeout=15
    )
    if proc.returncode == 0 and proc.stdout.strip():
        try:
            return float(proc.stdout.strip())
        except ValueError:
            return None
    return None
```

### Weighted computation

```python
total_weight = 0.0
weighted_pe_sum = 0.0
for _, row in holdings.iterrows():
    stock_code = str(row['股票代码']).strip()
    weight = float(row['占净值比例']) / 100.0
    pe = _get_stock_pe_via_subprocess(stock_code)
    if pe is not None:
        weighted_pe_sum += pe * weight
        total_weight += weight
```

### Critical pitfalls

1. **Batch in subprocess**: Each stock PE call is a separate subprocess. Total time = Σ(15s timeout per stock). With 10 funds × 10 stocks = 100 calls, this takes ~20-30s total. Acceptable for cron jobs; DO NOT call in interactive flows.

2. **ETF-linked funds (ETF联接)**: These funds (e.g. 014414 招商畜牧) hold ETF shares, not individual stocks. `fund_portfolio_hold_em` returns "本基金不持有股票" — skip them. They display `N/A` in the report.

3. **QDII/HK funds**: HK stock codes (e.g. 01810, 00700) use `stock_hk_valuation_baidu`. Some HK stocks may return `N/A` — that's expected (thin coverage). Use `stock_hk_valuation_baidu` fallback.

4. **Individual stock PE can be extreme**: Some stocks (like 300394 天孚通信 PE=136, 300136 信维通信 PE=130) have very high PE. This makes fund PE appear extremely high (e.g. 德邦鑫星 PE=240.6). This is the correct market-implied PE — do NOT clamp or cap it. Flag with context.

5. **Coverage ratio**: Always report `覆盖仓位 = total_weight_processed / total_top10_weight` as percentage. Low coverage (< 30%) means the PE is unreliable — note this in report.

6. **SSL patch required**: Import `ssl_patch` before any akshare call in the subprocess. Alternatively, skip the patch and accept some calls may return `None` (the fallback `N/A` row handles it gracefully).

### Valuation thresholds for fund PE

Unlike index PE (which uses historical percentile), fund PE uses direct absolute thresholds because there's no 10-year PE history for most stocks:

| PE Range | Label |
|---|---|
| PE < 20 | 🟢低估 |
| 20 ≤ PE < 35 | 🟢合理 |
| 35 ≤ PE < 50 | 🟡偏高 |
| PE ≥ 50 | 🔴极高 |

### Integration into reports

Fund PE section appears directly after index PE section in all 4 report types:
- Morning: section 3.6
- Afternoon: section 2.6  
- Evening: section 1.6
- Weekly: inside `print_weekly_report()`

It's called individually per report (NOT through `_format_global_market()`) because it uses akshare, not the market data APIs.

---

## Correct akshare Financial Functions

### ❌ Wrong (does not exist)
- `ak.stock_financial_benefit_ths()` — NOT a real akshare function
- `ak.stock_financial_debt_ths()` — NOT a real akshare function  
- `ak.stock_financial_cash_ths()` — NOT a real akshare function

### ✅ Correct (verified working 2026-06-11)
- `ak.stock_financial_abstract_ths(symbol=code)` — 同花顺财务摘要，含毛利率/营收增速/净利率等25个指标
- `ak.stock_financial_report_sina(stock=code, symbol='利润表')` — 新浪利润表，83列详细数据
- `ak.stock_financial_report_sina(stock=code, symbol='资产负债表')` — 新浪资产负债表
- `ak.stock_financial_report_sina(stock=code, symbol='现金流量表')` — 新浪现金流量表
- `ak.stock_financial_analysis_indicator(symbol=code)` — 东方财富财务指标（有时返回空）

### THS Data Format
THS data uses Chinese number formats that need special parsing:
- `3047.76万` → 30,477,600 (multiply by 1e4)
- `1.24亿` → 124,000,000 (multiply by 1e8)
- `48.48%` → 48.48 (strip %)
- `False` or `-` → 0 (missing data)

Helper function:
```python
def _parse_cn_number(val) -> float:
    s = str(val).strip()
    if s in ('', '-', 'False', 'None', 'nan'): return 0
    multiplier = 1
    if s.endswith('万'): s, multiplier = s[:-1], 1e4
    elif s.endswith('亿'): s, multiplier = s[:-1], 1e8
    s = s.replace('%', '').replace(',', '')
    try: return float(s) * multiplier
    except ValueError: return 0
```

### Key Column Names (stock_financial_abstract_ths)
- `销售毛利率` (not `毛利率`)
- `营业总收入同比增长率` (not `营收增速`)
- `销售净利率`
- `营业总收入`
- `净利润`
- `报告期` (date column)

### Fund Holdings
- `ak.fund_portfolio_hold_em(symbol=code, date='2026')` — fund portfolio holdings
- Returns columns: 序号, 股票代码, 股票名称, 占净值比例, 持股数, 持仓市值, 季度
- Date param is year string ('2025', '2026')

### Stock Market Data
- `ak.stock_zh_a_spot_em()` — A股实时行情（全量，含市值/PE/PB/换手率）
- Returns columns: 代码, 名称, 最新价, 涨跌幅, 总市值, 市盈率-动态, 市净率, 换手率, 成交量
