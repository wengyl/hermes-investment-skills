# Industry Data and Fund Holdings

## Overview

This document covers how to fetch and display industry-level data for fund investment analysis, including:
- Industry capital flow (主力资金流向)
- Fund holdings and industry allocation (基金持仓和行业配置)
- Fallback strategies when APIs are unavailable

---

## Industry Capital Flow API

### EastMoney Industry Flow Endpoint

**URL**: `http://push2.eastmoney.com/api/qt/clist/get`

**Key Parameters**:
- `fid=f62`: 主力净流入 (main capital net inflow)
- `fs=m:90+t:2`: **申万行业分类** - CRITICAL: Use `m:90+t:2` for industries, NOT `fs=bk` (deprecated, returns rc:102 error), NOT `m:0+t:6` (which returns individual stocks)
- `fields=f12,f13,f14,f62,f63`: 代码，名称，净流入，净流出

**Example Request**:
```bash
curl -s 'http://push2.eastmoney.com/api/qt/clist/get?fid=f62&po=1&pz=50&pn=1&np=1&fltt=2&invt=2&fs=m:90+t:2&fields=f12,f13,f14,f62,f63'
```

**Response Format**:
```json
{
  "data": {
    "diff": [
      {
        "f12": "HK801001",      // 行业代码
        "f14": "半导体",         // 行业名称
        "f62": 64691300,        // 主力净流入 (元)
        "f63": 87654300         // 主力净流出 (元)
      }
    ]
  }
}
```

**Common Pitfall**: 
- ❌ Using `fs=m:0+t:6` returns **individual stocks**, not industries
- ❌ Using `fs=bk` is deprecated and returns rc:102 error
- ✅ Use `fs=m:90+t:2` for **申万行业分类** (31 industry sectors)

---

## Fund Holdings API

### EastMoney Fund Holdings Endpoint

**URL**: `http://api.fund.eastmoney.com/f10/stockposition`

**Parameters**:
- `fundcode`: 基金代码
- `pageIndex`: 页码
- `pageSize`: 每页数量 (max 10 for top holdings)

**Example Request**:
```bash
curl -s 'http://api.fund.eastmoney.com/f10/stockposition?fundcode=020692&pageIndex=1&pageSize=10'
```

**Expected Response**:
```json
{
  "Data": {
    "STOCKINFO": "贵州茅台|8.5;宁德时代|6.2;..."  // 股票名 | 比例; 分隔
  }
}
```

**Current Status**: ⚠️ **API often returns 404**
- Error: `{"Data":null,"ErrCode":4,"ErrMsg":"404"}`
- This is a known issue with EastMoney's API stability

---

## Fallback Strategy: Name-Based Industry Inference

When the holdings API fails, use fund name keywords to infer industry allocation.

### Implementation Pattern

```python
def _infer_industry_from_name(self, fund_name: str) -> Dict:
    """根据基金名称推断行业配置"""
    industry_keywords = {
        '通信': {'通信': 80, '科技': 10, '其他': 10},
        '畜牧': {'畜牧养殖': 85, '农业': 10, '其他': 5},
        '港股': {'金融': 40, '地产': 20, '消费': 20, '其他': 20},
        '科技': {'半导体': 30, '人工智能': 25, '互联网': 25, '其他': 20},
        '互联网': {'互联网': 60, '人工智能': 20, '其他': 20},
        '全球': {'互联网': 35, '半导体': 25, '人工智能': 20, '其他': 20},
        '沪深 300': {'金融': 30, '工业': 20, '消费': 20, '其他': 30},
        '创新': {'医药生物': 30, '科技': 25, '新能源': 20, '其他': 25},
        '驱动': {'科技': 35, '制造业': 25, '其他': 40},
        '红利': {'金融': 40, '能源': 20, '地产': 15, '其他': 25},
    }
    
    for keyword, industry_alloc in industry_keywords.items():
        if keyword in fund_name:
            return {'industry_allocation': industry_alloc}
    
    return {'industry_allocation': {'其他': 100}}
```

### Supported Keywords

| Keyword | Primary Industries | Use Case |
|---------|-------------------|----------|
| 通信 | 通信 80%, 科技 10% | 通信设备指数基金 |
| 畜牧 | 畜牧养殖 85%, 农业 10% | 畜牧养殖 ETF |
| 港股 | 金融 40%, 地产 20%, 消费 20% | 港股通红利基金 |
| 科技 | 半导体 30%, AI 25%, 互联网 25% | 科技主题基金 |
| 互联网 | 互联网 60%, AI 20% | 互联网行业基金 |
| 全球 | 互联网 35%, 半导体 25%, AI 20% | QDII 全球科技基金 |
| 沪深 300 | 金融 30%, 工业 20%, 消费 20% | 宽基指数基金 |
| 创新 | 医药 30%, 科技 25%, 新能源 20% | 创新主题基金 |
| 驱动 | 科技 35%, 制造业 25% | 创新驱动基金 |
| 红利 | 金融 40%, 能源 20%, 地产 15% | 红利策略基金 |

---

## Display Best Practices

### Industry Allocation Table Format

```python
# Column widths for industry allocation
COL_FUND = 12      # 基金代码
COL_INDUSTRY = 10  # 行业名称
COL_RATIO = 10     # 配置比例

# Display top 3 industries per fund
sorted_industries = sorted(industries.items(), key=lambda x: x[1], reverse=True)[:3]
for industry, ratio in sorted_industries:
    summary.append(
        f"{code:<{COL_FUND}}{industry:<{COL_INDUSTRY}}{ratio:>{COL_RATIO-1}.1f}%"
    )
```

### Capital Flow Display

```python
# Show net inflow with sign
if net_inflow >= 0:
    net_str = f"+{net_inflow:,.1f}"
else:
    net_str = f"{net_inflow:,.1f}"

# Show ratio with sign
if ratio >= 0:
    ratio_str = f"+{ratio:.1f}%"
else:
    ratio_str = f"{ratio:.1f}%"
```

---

## Error Handling

### API Timeout Handling

```python
try:
    proc_result = subprocess.run(
        ['curl', '-s', '-A', 'Mozilla/5.0', '-m', '10', url],
        capture_output=True,
        text=True,
        timeout=15
    )
except subprocess.TimeoutExpired:
    print("API 请求超时，使用缓存数据")
    return cached_data
```

### 404 Error Handling

```python
data = json.loads(proc_result.stdout)
if data.get('Data') is None and data.get('ErrMsg') == '404':
    print(f"API 返回 404，使用名称推断")
    return self._infer_industry_from_name(fund_name)
```

---

## Alternative Data Sources

When EastMoney APIs are unavailable, consider:

1. **聚宽 (JoinQuant)**: Free tier available
   - API: `http://api.joinquant.com`
   - Requires registration

2. **Tushare**: Professional data source
   - API: `https://tushare.pro`
   - Requires token (free tier available)

3. **浏览器爬虫**: Last resort
   - URL: `https://fund.eastmoney.com/{fund_code}.html`
   - Parse HTML for holdings table

---

## Testing

### Test Industry Flow API

```bash
curl -s 'http://push2.eastmoney.com/api/qt/clist/get?fid=f62&fs=m:90+t:2&fields=f12,f14,f62,f63&pz=5' | jq '.data.diff[:3]'
```

### Test Fund Holdings API

```bash
curl -s 'http://api.fund.eastmoney.com/f10/stockposition?fundcode=020692&pageSize=10' | jq '.'
```

### Test Inference Logic

```python
from scripts.data_fetcher import FundDataFetcher
fetcher = FundDataFetcher()

# Test various fund names
test_names = [
    "博时中证全指通信设备指数 C",
    "招商中证畜牧养殖 ETF 联接 A",
    "富国全球科技互联网股票 (QDII)C",
]

for name in test_names:
    result = fetcher._infer_industry_from_name(name)
    print(f"{name}: {result['industry_allocation']}")
```

---

## Related References

- `references/api-endpoints.md`: Complete API documentation
- `references/code-block-formatting.md`: Table formatting standards
- `references/nav-api-troubleshooting.md`: Network restriction workarounds
