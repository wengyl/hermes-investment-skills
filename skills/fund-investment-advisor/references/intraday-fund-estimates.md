# Intraday Report with Fund Estimates

## Data Flow

1. Fetch A-share indices via MultiSourceAdapter (Tencent → Sina fallback)
2. Fetch industry capital flow (EastMoney → Sina fallback)
3. Fetch fund estimates from 天天基金 JSONP API
4. Combine with latest NAV from database
5. Display: `净值(日期)` + `估值(时间)` + `涨跌%` + `涨跌额` + `估算市值`

## 天天基金 JSONP API

```
GET http://fundgz.1234567.com.cn/js/{fund_code}.js
Response: jsonpgz({"fundcode":"002112","name":"...","gsz":"6.15","gszzl":"0.34","gztime":"2026-05-29 15:00","dwjz":"6.1293","jzrq":"2026-05-28"});
```

Fields:
- `gsz`: Estimated NAV (盘中估值)
- `gszzl`: Estimated change % (估值涨跌幅)
- `gztime`: Estimate time (估值时间)
- `dwjz`: Latest actual NAV (最新净值)
- `jzrq`: NAV date (净值日期)

## Critical Pitfalls

1. **DO NOT use `text=True`** in subprocess.run — causes encoding issues with Chinese names
2. **Use `capture_output=True`** then `result.stdout.decode('utf-8', errors='ignore')`
3. **Regex**: `r'jsonpgz\((\{.*?\})\);'` with `re.DOTALL`
4. **Only catch** `json.JSONDecodeError, ValueError` — NOT bare `except Exception`
5. QDII/LOF funds may return empty or stale estimates

## Sina Concept Boards API

```
GET http://money.finance.sina.com.cn/q/view/newFLJK.php?param=class
Encoding: GBK
Format: var S_Finance_bankuai_class = {"key":"code,name,count,avg,change,change_pct,vol,amount,...",...}
```

Same parsing logic as Sina industry boards — use `_fetch_sina_board()` shared method.

## User Preferences

- Always show estimate time at bottom: `⏰ 估值时间: YYYY-MM-DD HH:MM`
- QDII/LOF without estimates show "—" in all estimate columns
- Column alignment must use `_display_width()` / `_pad()` helpers for Chinese characters
