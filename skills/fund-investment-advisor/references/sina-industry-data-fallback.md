# Industry Data API - Sina Finance Fallback

## Problem: EastMoney push2 API Blocked

**Symptom**: `curl` to `push2.eastmoney.com` returns empty response with exit code 52 (curl: Empty reply from server). Even with proper headers (User-Agent, Referer, Origin), the API returns nothing.

**Root Cause**: The push2.eastmoney.com API appears to block requests from certain server IPs or regions. The browser can load the page but the data table remains empty because the API call fails client-side too.

**Test**:
```bash
# This returns HTTP 000 / exit 52 from many servers
curl -s --max-time 10 'https://push2.eastmoney.com/api/qt/clist/get?fid=f62&po=1&pz=50&pn=1&np=1&fltt=2&invt=2&fs=m:90+t:2&fields=f12,f14,f62,f184'
```

**Note**: The API uses `fs=m:90+t:2` for 申万行业分类 (NOT `fs=bk` which is deprecated, NOT `fs=m:0+t:6` which returns stocks). But even with correct parameters, the API may be blocked.

## Solution: Sina Finance Industry Data

**Working URL**: `http://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php`

**Key characteristics**:
- Returns **GBK encoding** (not UTF-8) — must decode with `text.decode('gbk', errors='ignore')`
- Returns a JavaScript variable assignment: `var S_Finance_bankuai_sinaindustry = {...}`
- Each entry format: `"key":"key,行业名称,股票数,均价,价格变动,涨跌幅,成交量,成交额,领涨股代码,领涨股价,领涨股涨跌,领涨股涨跌幅,领涨股名称"`

**Parsing code**:
```python
import re, subprocess

result = subprocess.run(
    ['curl', '-s', '-A', 'Mozilla/5.0', '-m', '10',
     'http://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php'],
    capture_output=True, timeout=15
)
text = result.stdout.decode('gbk', errors='ignore')

match = re.search(
    r'var\s+S_Finance_bankuai_sinaindustry\s*=\s*(\{.*?\})\s*;?\s*$',
    text, re.MULTILINE | re.DOTALL
)
data_str = match.group(1)
entries = re.findall(r'"([^"]+)":"([^"]+)"', data_str)

for key, value in entries:
    parts = value.split(',')
    # parts[1]=行业名, parts[5]=涨跌幅, parts[7]=成交额(元), parts[12]=领涨股
```

**Field indices** (0-based):
- 0: code (e.g., "new_blhy")
- 1: 行业名称
- 2: 股票数量
- 3: 平均价
- 4: 价格变动
- 5: 涨跌幅 (%)
- 6: 成交量 (股)
- 7: 成交额 (元)
- 8: 领涨股代码
- 9: 领涨股价
- 10: 领涨股涨跌
- 11: 领涨股涨跌幅
- 12: 领涨股名称

## Data Type Adaptation

Sina provides **行业涨跌幅** (industry change %) instead of **资金流向** (capital flow). The display format must adapt:

- EastMoney data: shows "净流入 (万元)" and "净流入占比"
- Sina data: shows "涨跌幅" and "成交额(亿)"

In `advisor.py`, the `_format_capital_flow_summary()` method checks `data_type` field to determine display format. When `data_type == 'change_pct'`, it shows industry change percentages.

## Related Sina APIs

```bash
# Concept sectors (概念板块)
http://vip.stock.finance.sina.com.cn/q/view/newFLJK.php?param=class

# Regional sectors (地域板块)  
http://vip.stock.finance.sina.com.cn/q/view/newFLJK.php?param=area
```

Both return the same GBK-encoded JavaScript variable format.
