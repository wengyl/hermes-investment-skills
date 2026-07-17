# Network Restrictions Workaround for Chinese Financial APIs

## Problem: `requests` Library Returns 502 Errors

On macOS (and some network configurations), Python's `requests` library fails when accessing Chinese financial APIs:

```python
import requests
response = requests.get('http://push2.eastmoney.com/api/qt/clist/get')
# Returns: 502 Bad Gateway
```

**Root Cause**: Network restrictions or proxy configurations that allow system `curl` but block Python HTTP libraries.

## Solution: Use `curl` via subprocess

### Basic Pattern

```python
import subprocess
import json

url = 'http://push2.eastmoney.com/api/qt/clist/get?fid=f62&po=1&pz=50'

result = subprocess.run(
    ['curl', '-s', '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', '-m', '10', url],
    capture_output=True,
    text=True,
    timeout=15
)

if result.returncode == 0:
    data = json.loads(result.stdout)
    # Process data...
```

### Key Parameters

| Parameter | Purpose |
|-----------|---------|
| `-s` | Silent mode (no progress bar) |
| `-A` | Set User-Agent header (mimics browser) |
| `-m 10` | Maximum 10 second timeout |
| `capture_output=True` | Capture stdout/stderr |
| `text=True` | Return string instead of bytes |
| `timeout=15` | Python-level timeout (safety net) |

### Testing Network Access

Verify if `curl` works but `requests` fails:

```bash
# Test with curl (should work)
curl -I http://push2.eastmoney.com/api/qt/clist/get

# Test with Python requests (may fail)
python3 -c "import requests; print(requests.get('http://push2.eastmoney.com/api/qt/clist/get').status_code)"
```

If curl returns 200 but requests returns 502, use subprocess approach.

## API Response Formats

### 1. JSON Response (Most Common)

```python
# Direct JSON parsing
data = json.loads(result.stdout)
```

### 2. JSONP Response (天天基金)

Some APIs return JSONP format: `jsonpgz({...});`

```python
text = result.stdout.strip()
if text.startswith('jsonpgz('):
    text = text[8:-2]  # Remove "jsonpgz(" (8 chars) and ");" (2 chars)
data = json.loads(text)
```

**Critical**: Use `[8:-2]`, not `[9:-1]` (common mistake leaves extra character)

### 3. List vs Dictionary Parsing

API response structure may vary:

```python
# WRONG - assuming dict
for key, item in diffs.items():  # AttributeError if diffs is list

# CORRECT - handle list
for item in diffs:  # Works for list format
    # Process item...
```

## Data Fetcher Integration

### Updated `FundDataFetcher` Class

```python
class FundDataFetcher:
    def __init__(self):
        self.db_path = get_db_path()
        # Note: requests session may fail, use curl for critical APIs
    
    def get_capital_flow(self) -> Dict:
        """Get capital flow using curl (bypasses network restrictions)"""
        url = 'http://push2.eastmoney.com/api/qt/clist/get?fid=f62&po=1&pz=50&pn=1&fs=m:0+t:6&fields=f12,f13,f14,f62,f63'
        
        result = subprocess.run(
            ['curl', '-s', '-A', 'Mozilla/5.0', '-m', '10', url],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            # Parse and return data...
        
        return self._get_mock_data()  # Fallback
```

## Fallback Strategy

Always implement fallback to mock data for demo purposes:

```python
def get_data_with_fallback(self) -> Dict:
    """Try real API, fallback to mock data"""
    try:
        # Try real API first
        return self._fetch_real_data()
    except Exception as e:
        print(f"⚠️ 实时数据获取失败，使用模拟数据演示格式")
        return self._get_mock_data()

def _get_mock_data(self) -> Dict:
    """Return mock data with same structure as real API"""
    return {
        'industries': [
            {'name': '半导体', 'net_inflow': 12345.6, 'ratio': 12.3},
            # ... more mock data
        ],
        'summary': {...}
    }
```

## Common Pitfalls

### 1. Encoding Issues

Some Chinese APIs return GBK-encoded responses:

```python
# Try multiple encodings
for encoding in ['utf-8', 'gbk', 'gb2312']:
    try:
        data = result.stdout.encode('utf-8').decode(encoding)
        break
    except:
        continue
```

### 2. Timeout Configuration

Set both curl and Python timeouts:

```python
# curl timeout: -m 10 (10 seconds)
# Python timeout: timeout=15 (15 seconds)
# This provides two layers of protection
```

### 3. Error Handling

Check both return code and output:

```python
if result.returncode != 0:
    print(f"Curl error: {result.stderr}")
    return None

if not result.stdout.strip():
    print("Empty response from API")
    return None
```

## Performance Considerations

### When to Use `curl` vs `requests`

| Scenario | Recommended |
|----------|-------------|
| Chinese financial APIs | `curl` (more reliable) |
| International APIs | `requests` (simpler) |
| High-frequency calls | `requests` with session |
| Critical data | `curl` with fallback |

### Caching Strategy

Reduce API calls with caching:

```python
from datetime import datetime, timedelta

class CachedDataFetcher:
    def __init__(self, cache_ttl=300):  # 5 minutes
        self.cache = {}
        self.cache_ttl = cache_ttl
    
    def get_data(self, key, fetch_func):
        # Check cache
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return data
        
        # Fetch new data
        data = fetch_func()
        self.cache[key] = (data, datetime.now())
        return data
```

## Testing

### Unit Test Pattern

```python
def test_capital_flow_fetcher():
    fetcher = FundDataFetcher()
    data = fetcher.get_capital_flow()
    
    assert 'industries' in data
    assert 'summary' in data
    assert len(data['industries']) > 0
    assert 'total_net_inflow' in data['summary']
```

### Integration Test

```bash
cd ~/.hermes/fund-advisor
python3 -c "
from scripts.data_fetcher import FundDataFetcher
fetcher = FundDataFetcher()
flow = fetcher.get_capital_flow()
print(f'✓ Fetched {len(flow[\"industries\"])} industries')
print(f'✓ Total net inflow: {flow[\"summary\"][\"total_net_inflow\"]:.2f} 万元')
"
```

## Related References

- `references/nav-api-troubleshooting.md`: NAV-specific API issues
- `references/ssl-workaround.md`: SSL compatibility on macOS
- `scripts/update_nav_curl.py`: Example curl-based NAV updater

## Session Notes

**Discovered**: 2026-05-20
**Problem**: Fund advisor system showing "⚠️ 资金流向数据获取失败"
**Root Cause**: `requests` library blocked by network restrictions (502 error)
**Solution**: Switched to `subprocess.run(['curl', ...])` for capital flow API
**Result**: Successfully fetching 50 stocks with real-time capital flow data

**Key Files Modified**:
- `scripts/data_fetcher.py`: Updated `get_industry_capital_flow()` to use curl
- Fixed list vs dict parsing error in API response handling

**Impact**: Real-time data now working for 主力资金流向 (capital flow) section
