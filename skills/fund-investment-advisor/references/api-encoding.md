# Chinese Financial API Encoding Patterns

## Overview

Chinese financial data APIs (天天基金，东方财富，etc.) commonly use **GBK** or **GB2312** encoding instead of UTF-8, even for JSON responses.

## Common Encodings

| Encoding | Usage | Notes |
|----------|-------|-------|
| `GBK` | Most common | Superset of GB2312, supports more characters |
| `GB2312` | Older APIs | Legacy standard |
| `UTF-8` | Rare | Some newer endpoints |

## Detection & Handling

### Method 1: Try Multiple Encodings

```python
raw_data = response.read()

for encoding in ['gbk', 'gb2312', 'utf-8']:
    try:
        data = raw_data.decode(encoding)
        # Validate it's valid JSON
        json.loads(data)
        print(f"✅ Decoded with {encoding}")
        break
    except:
        continue
```

### Method 2: Check Response Headers

Some APIs indicate encoding in headers:
```python
headers = response.getheaders()
content_type = dict(headers).get('Content-Type', '')

# Look for charset parameter
if 'charset=' in content_type:
    encoding = content_type.split('charset=')[1].strip()
```

**Warning**: Headers are often wrong or missing. Always try multiple encodings.

## Common Failure Signs

### UTF-8 decode error
```
'utf-8' codec can't decode byte 0xd5 in position 248: 
invalid continuation byte
```

**Fix**: Try GBK encoding.

### Garbled text in response
```json
{"Data": "楣忓崕鍒涙柊椹卞姩"}  // Should be Chinese text
```

**Fix**: Response was decoded with wrong encoding.

## API-Specific Patterns

### 天天基金 (East Money)

**Endpoints**:
- `api.fund.eastmoney.com/FundGalaxy/GetFundSearchResult`
- `fundapi.eastmoney.com/FundSearch/GetFundSearchResult`

**Encoding**: GBK for both request parameters and response

**Example**:
```python
import urllib.parse

# Encode keyword in GBK
keyword = "鹏华创新驱动"
encoded_keyword = keyword.encode('gbk')

params = urllib.parse.urlencode({
    'keyword': keyword,
    'pageIndex': 1,
    'pageSize': 5
})

# Response should be decoded with GBK
raw_data = response.read()
data = raw_data.decode('gbk')
```

### 常见问题

**Error**: `No route providing a controller name was found`

**Cause**: URL parameters were UTF-8 encoded, but API expects GBK.

**Fix**: Ensure parameters are GBK-encoded before URL encoding.

## Best Practices

1. **Always try multiple encodings** - Don't assume UTF-8
2. **Validate decoded data** - Check if JSON parses successfully
3. **Log encoding used** - For debugging future issues
4. **Test with known data** - Use a fund you know exists

## Testing

```python
def test_encoding(url, expected_fund_name):
    """Test if encoding works correctly"""
    raw_data = fetch_url(url)
    
    for encoding in ['gbk', 'gb2312', 'utf-8']:
        try:
            data = raw_data.decode(encoding)
            json_data = json.loads(data)
            
            # Check if response contains expected data
            if expected_fund_name in data:
                print(f"✅ {encoding} works correctly")
                return True
        except:
            continue
    
    print("❌ No encoding worked")
    return False
```

## Session Notes

- Date: 2026-05-16
- Discovered during: Fund code lookup for 鹏华创新驱动混合 C
- API: 天天基金搜索 API
- Resolution: Switched to GBK encoding for all API calls

## Related

- See `ssl-workaround.md` for SSL issues
- See main SKILL.md for data integrity principles
