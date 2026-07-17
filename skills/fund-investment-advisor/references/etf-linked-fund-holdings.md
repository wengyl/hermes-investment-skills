# ETF-Linked Fund Holdings Fetching

## Problem

联接基金 (ETF feeder funds) like 018388 (华泰柏瑞港股通红利ETF联接C) don't hold stocks directly — they invest in an ETF. Eastmoney's `FundArchivesDatas.aspx` returns `content:""` for these funds, so `get_fund_holdings()` falls back to name-based inference, which produces inaccurate industry allocation.

## Solution

Added `etf_map` lookup in `data_fetcher.py` → `get_fund_holdings()`:

```python
etf_map = {'018388': '513090'}  # 联接基金 → 对应ETF
```

When the primary API returns empty content for a fund in `etf_map`, the code fetches holdings from the corresponding ETF instead.

## ETF Holdings HTML Format (Eastmoney)

ETF holdings use a **different HTML structure** than regular funds:

```html
<tr>
  <td>1</td>
  <td><a href='//quote.eastmoney.com/unify/r/116.00388'>00388</a></td>
  <td class='tol'><a href='...'>香港交易所</a></td>
  <td class='tor'><span data-id='dq00388'></span></td>
  <td class='tor'><span data-id='zd00388'></span></td>
  ...
  <td class='tor'>16.75%</td>  <!-- 占净值比例 -->
</tr>
```

### Key differences from regular fund HTML:
1. **Single quotes** for attributes (`class='tol'` not `class="tol"`)
2. **Stock codes vary in length**: HK stocks are 4-5 digits (00388, 06030), A-shares are 6 digits
3. **Ratio is in `<td class='tor'>X.XX%</td>`**, not in the same `<td>` as stock name

## Regex Patterns

```python
# Extract code + name pairs (note: \d{4,6} for HK stocks)
code_name = re.findall(r">(\d{4,6})</a></td><td class=.tol.><a[^>]*>([^<]+)</a>", html)

# Extract ratios (ordered, match by position)
ratios = re.findall(r"class=.tor.>([\d.]+)%", html)

# Combine by index
rows = [(cn[0], cn[1], ratios[i] if i < len(ratios) else '0') 
        for i, cn in enumerate(code_name)]
```

## Pitfalls

1. **`\d{6}` fails for HK stocks** — HK exchange codes like 00388 are 5 digits. Must use `\d{4,6}`.
2. **Single vs double quotes** — Eastmoney HTML uses `class='tol'` (single quotes). Regex `class="tol"` won't match. Use `class=.tol.` for flexibility.
3. **Ratio position assumption** — Ratios are extracted as a flat list and matched to stocks by order. If the HTML has extra `<td class='tor'>` elements (e.g., price, change%), the ratios list will contain non-ratio values. Filter by checking if the value ends with `%`.
4. **GBK encoding** — Stock names (香港交易所) are in GBK. Decode with `html.decode('gbk')` or use `errors='replace'`.
5. **ETF code mapping must be maintained** — When adding new linked funds, add to `etf_map`. Currently only 018388→513090 is mapped.

## Testing

```bash
cd ~/.hermes/fund-advisor
export https_proxy=http://127.0.0.1:7897
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from data_fetcher import FundDataFetcher
f = FundDataFetcher()
result = f.get_fund_holdings('018388', '华泰柏瑞港股通红利')
holdings = result.get('top_holdings', [])
print(f'重仓股: {len(holdings)}只')
for h in holdings[:5]:
    print(f'  {h[\"name\"]} ({h[\"code\"]}): {h[\"ratio\"]}%')
"
```

Expected output:
```
📝 018388 是联接基金，尝试从ETF 513090 获取持仓
✓ 成功从ETF 513090 获取 10 只持仓
重仓股: 10只
  香港交易所 (00388): 16.75%
  中信证券 (06030): 13.36%
  ...
```

## Known Limitation

`_classify_stock_industry()` doesn't recognize HK stock names (港交所, 中信证券, etc.) — they all get classified as "其他". The industry_allocation will show `{'其他': 86.65}`. To fix properly, add HK stock name patterns to the classification function.
