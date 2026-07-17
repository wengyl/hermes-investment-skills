# 天天基金 API 端点状态

## 可靠的端点 (Reliable)

### 1. 基金净值 API ✅

**Endpoint**: `https://fundgz.1234567.com.cn/js/{code}.js`

**Method**: GET

**Returns**: JSONP format

**Example**:
```
GET /js/000001.js
```

**Response**:
```javascript
jsonpgz({
  "fundcode": "000001",
  "name": "华夏成长混合",
  "jzrq": "2026-05-14",
  "dwjz": "1.239",
  "gsz": "1.239",
  "gszzl": "-0.42",
  "gztime": "2026-05-15 15:00"
});
```

**Notes**:
- Returns JSONP, need to strip `jsonpgz(` and `);`
- Encoded in UTF-8
- Most reliable endpoint
- Works with http.client

---

### 2. 基金基本信息 API ✅

**Endpoint**: `https://api.fund.eastmoney.com/f10/jjjb`

**Method**: GET

**Params**:
- `fundcode`: 6-digit fund code

**Returns**: JSON (GBK encoded)

**Example**:
```
GET /f10/jjjb?fundcode=000001
```

**Response** (GBK decoded):
```json
{
  "Data": {
    "FUNDNAME": "华夏成长混合",
    "RZJJDWL": "混合型-偏股",
    "JJLM": "张荣",
    "JJCSRQ": "2001-12-18",
    "SCL": "123.45"
  },
  "ErrCode": 0
}
```

**Notes**:
- **Must decode as GBK**, not UTF-8
- Returns fund basic info

---

## 不稳定的端点 (Unstable)

### 3. 基金搜索 API ⚠️

**Endpoint**: `https://api.fund.eastmoney.com/FundGalaxy/GetFundSearchResult`

**Method**: GET

**Params**:
- `keyword`: Search keyword (基金名称)
- `pageIndex`: Page number
- `pageSize`: Results per page

**Returns**: JSON (GBK encoded)

**Example**:
```
GET /FundGalaxy/GetFundSearchResult?keyword=鹏华创新驱动&pageIndex=1&pageSize=5
```

**Response** (when works):
```json
{
  "Data": {
    "Fund": [
      {
        "FNDSCODE": "027063",
        "FUNDNAME": "鹏华创新驱动混合 C",
        "RZJJDWL": "混合型-偏股"
      }
    ]
  },
  "ErrCode": 0
}
```

**Response** (when fails):
```json
{
  "Data": null,
  "ErrCode": 1,
  "ErrMsg": "No route providing a controller name was found..."
}
```

**Notes**:
- **Often returns 404 or ErrCode 1**
- API endpoint may have changed
- Don't rely on this for production
- Try alternative: `/FundGlobe/FundSearch` (also unstable)

---

## 其他尝试过的端点 (Tested but Failed)

| Endpoint | Status | Error |
|----------|--------|-------|
| `/FundGlobe/FundSearch` | ❌ | "No route providing a controller" |
| `/FundSearch/GetFundSearchResult` | ❌ | Encoding error |
| `/Data/Fund/GS.aspx` | ❌ | 403 Forbidden |
| `/F10/FFPGL` | ✅ | Works but returns different data |

---

## 最佳实践

### 1. 优先使用净值 API

If you have the fund code, always use the NAV API:

```python
# Reliable way to get fund data
def get_fund_data(code):
    # Use fundgz.1234567.com.cn/js/{code}.js
    # This works 100% of the time
    pass
```

### 2. 搜索 API 不可靠

Don't rely on search APIs. If you need to search by name:
- Ask user to provide the code
- Use browser to search manually
- Maintain a local code lookup table

### 3. 编码处理

Always try multiple encodings:

```python
for encoding in ['gbk', 'gb2312', 'utf-8']:
    try:
        data = raw_data.decode(encoding)
        break
    except:
        continue
```

### 4. 使用 http.client

On macOS, use `http.client` instead of `requests`:

```python
import http.client
import ssl

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

conn = http.client.HTTPSConnection(host, 443, context=context)
```

---

### 3. 基金重仓股/持仓 API ✅ (2026-06 修复)

**旧 Endpoint (已失效 ❌)**: `https://api.fund.eastmoney.com/f10/stockposition`
- 返回 `ErrCode:4, ErrMsg:"404"` for all fund codes
- 2026-06 起完全不可用

**新 Endpoint ✅**: `https://fundf10.eastmoney.com/FundArchivesDatas.aspx`

**Params**:
- `type=jjcc` (基金持仓)
- `code`: 6-digit fund code
- `topline=10` (前N只重仓股)
- `year=` / `month=` (空=最新季报)
- `rt=0.123` (cache buster)

**Returns**: JavaScript variable assignment with HTML table
```
var apidata={ content:"<html table>..." }
```

**Required Header**: `Referer: https://fundf10.eastmoney.com/ccmx_{code}.html`

**HTML Table Columns** (critical — wrong index = wrong data!):
| Index | Column | Content |
|-------|--------|---------|
| cells[0] | 序号 | Row number |
| cells[1] | 股票代码 | Stock code |
| cells[2] | 股票名称 | Stock name |
| cells[3] | 最新价 | Latest price |
| cells[4] | 涨跌幅 | Change % |
| cells[5] | 相关资讯 | Links |
| **cells[6]** | **占净值比例** | **Net value ratio %** ← USE THIS |
| cells[7] | 持股数(万股) | Share count ← NOT this |
| cells[8] | 持仓市值(万元) | Market value |

**⚠️ PITFALL**: cells[6] is the ratio, cells[7] is share count. Using cells[7] produces nonsensical industry allocation sums (e.g. 1924% "其他").

**行业配置 API (type=jjhy)**: Returns empty. Only `type=jjcc` works.

**Test command**:
```bash
curl -s -A 'Mozilla/5.0' --connect-timeout 5 --max-time 8 \
  -H 'Referer: https://fundf10.eastmoney.com/ccmx_002112.html' \
  'https://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code=002112&topline=10&year=&month=&rt=0.123' \
  | head -c 500
```

---

## 更新日志

**2026-06-05**:
- Fund Holdings API: `api.fund.eastmoney.com/f10/stockposition` → ❌ 404 (decommissioned)
- Fund Holdings API: `fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc` → ✅ Working (HTML parse)
- Expanded `_classify_stock_industry()` from 10→17 categories, ~40→~120 keywords

**2026-05-16**: 
- NAV API: ✅ Working
- Search API: ❌ Returns "No route" error
- GBK encoding required for most APIs
- http.client works, requests fails on macOS

**Note**: APIs may change without notice. Always test before relying on them.
