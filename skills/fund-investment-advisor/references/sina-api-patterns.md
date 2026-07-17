# Sina Finance API Patterns

## Industry Boards (行业板块)
- **URL**: `http://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php`
- **Encoding**: GBK
- **Format**: `var S_Finance_bankuai_sinaindustry = {"key":"code,name,count,avg_price,change,change_pct,vol,amount,...",...}`
- **Key prefix**: `new_` (e.g., `new_blhy`, `new_cbzz`)

## Concept Boards (概念板块)
- **URL**: `http://money.finance.sina.com.cn/q/view/newFLJK.php?param=class`
- **Encoding**: GBK
- **Format**: `var S_Finance_bankuai_class = {"gn_key":"code,name,count,avg_price,change,change_pct,vol,amount,...",...}`
- **Key prefix**: `gn_` (e.g., `gn_hwqc`, `gn_BCdc`)

## Common Parsing Code
```python
import subprocess, re, json

def fetch_sina_board(url: str) -> list:
    result = subprocess.run(
        ['curl', '-s', '-A', 'Mozilla/5.0', '--connect-timeout', '5', url],
        capture_output=True, timeout=10
    )
    if result.returncode != 0 or not result.stdout:
        return []
    
    text = result.stdout.decode('gbk', errors='ignore')
    match = re.search(r'=\s*\{(.+)\}', text, re.DOTALL)
    if not match:
        return []
    
    boards = []
    entries = re.findall(r'"[^"]+":"([^"]+)"', match.group(1))
    
    for entry in entries:
        fields = entry.split(',')
        if len(fields) >= 6:
            boards.append({
                'name': fields[1],
                'code': fields[0],
                'count': int(fields[2]) if fields[2].isdigit() else 0,
                'avg_price': float(fields[3]) if fields[3] else 0,
                'change': float(fields[4]) if fields[4] else 0,
                'change_pct': float(fields[5]) if fields[5] else 0,
                'amount': float(fields[7]) if len(fields) > 7 and fields[7] else 0,
            })
    
    return boards
```

## Field Index (comma-separated)
| Index | Field | Example |
|-------|-------|---------|
| 0 | Internal code | `new_blhy`, `gn_hwqc` |
| 1 | Display name | `玻璃行业`, `华为汽车` |
| 2 | Stock count | `19` |
| 3 | Average price | `21.66` |
| 4 | Price change | `-0.53` |
| 5 | Change % | `-2.39` |
| 6 | Volume | `415433724` |
| 7 | Amount (元) | `9021460925` |
| 8 | Lead stock code | `sh600184` |
| 9-12 | Lead stock details | price, change, etc. |
| 13 | Lead stock name | `光电股份` |

## Real-Time Quote APIs (US Stocks, HK Stocks, FX, Gold) — added 2026-07-06

### Common Pattern
All Sina real-time quote APIs:
1. Return **GBK** encoded data
2. Require header: `Referer: https://finance.sina.com.cn`
3. Must use `capture_output=True` (NOT `text=True`) + manual GBK decode

```python
proc = subprocess.run(
    ['curl', '-s', '-H', 'Referer: https://finance.sina.com.cn', '-m', '10', url],
    capture_output=True, timeout=15)
stdout = proc.stdout.decode('gbk', errors='replace')
```

### US Stock Indices
- **URL**: `https://hq.sinajs.cn/list=gb_dji,gb_ixic,gb_inx`
- **Format**: `var hq_str_gb_dji="道琼斯,52900.07,1.14,...";`
- **Fields**: `fields[1]=price, fields[2]=change_pct`

### HK Hang Seng Index
- **URL**: `https://hq.sinajs.cn/list=rt_hkHSI`
- **Format**: `var hq_str_rt_hkHSI="HSI,恒生指数,...,现价,...,涨跌幅,...";`
- **Fields**: `fields[6]=price, fields[8]=change_pct`

### USD/CNY Exchange Rate
- **URL**: `https://hq.sinajs.cn/list=USDCNY`
- **Format**: `var hq_str_USDCNY="时间,买价,卖价,...";`
- **Calc**: `rate = (float(fields[1]) + float(fields[2])) / 2` (mid-price)

### COMEX Gold Futures
- **URL**: `https://hq.sinajs.cn/list=hf_GC`
- **Format**: `var hq_str_hf_GC="现价,...,昨收,...";`
- **Fields**: `fields[0]=price, fields[7]=prev_close`
- **Calc**: `change_pct = (price - prev_close) / prev_close * 100`

## Pitfalls
- **Encoding**: MUST use `.decode('gbk', errors='ignore')`, NOT UTF-8
- **Regex**: Use generic `"[^"]+":"([^"]+)"` pattern, NOT `"new_\w+":"([^"]+)"` (concept keys use `gn_` prefix)
- **Rate limiting**: Sina may throttle frequent requests; cache results with 10-min TTL
- **Referer header**: Real-time quote APIs (`hq.sinajs.cn`) require `-H 'Referer: https://finance.sina.com.cn'`
- **text=True trap**: Do NOT use `subprocess.run(..., text=True)` with Sina APIs — defaults to UTF-8 and fails on GBK data
