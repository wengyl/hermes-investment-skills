# Multi-Source API Patterns for Chinese Financial Data

## Critical Discovery (2026-05-20)

### Problem: requests Library Returns 502 Errors

**Symptom**: Python `requests` library fails to access 东方财富 APIs
```python
import requests
response = requests.get('http://push2.eastmoney.com/api/qt/clk/get')
# Returns: 502 Bad Gateway
```

**Root Cause**: Network restrictions block Python requests but allow system curl

**Solution**: Use `subprocess.run(['curl', ...])` instead
```python
import subprocess
result = subprocess.run(
    ['curl', '-s', '-A', 'Mozilla/5.0', '-m', '10', url],
    capture_output=True,
    text=True,
    timeout=15
)
data = json.loads(result.stdout)
# Success! ✅
```

## Multi-Source Architecture

### Priority-Based Fallback System

```python
class MultiSourceAdapter:
    """Multi-source API adapter with automatic fallback"""
    
    def __init__(self):
        self.data_sources = {
            'a_shares_index': [
                {'name': 'tencent', 'priority': 1, 'func': self._get_tencent},
                {'name': 'eastmoney', 'priority': 2, 'func': self._get_eastmoney},
                {'name': 'sina', 'priority': 3, 'func': self._get_sina},
            ]
        }
    
    def get_a_shares_index(self) -> Dict:
        """Auto-fallback to best available source"""
        for source in self.data_sources['a_shares_index']:
            try:
                result = source['func']()
                if result:
                    print(f"✓ Using {source['name']} data source")
                    return result
            except Exception as e:
                print(f"⚠️ {source['name']} failed: {e}")
                continue
        return {}  # All sources failed
```

## API Source Details

### 1. 腾讯财经 (Primary - Most Stable) ✅

**Endpoint**: `http://qt.gtimg.cn/q={code}`

**Status**: ✅ Most reliable for A 股指数

**Encoding**: GBK (critical!)

**Response Format**:
```javascript
v_sh000001="1~上证指数~000001~4162.18~4169.54~4152.70~624152035~...~-7.36~-0.18~..."
```

**Parsing**:
```python
# Decode GBK
raw_data = proc_result.stdout.decode('gbk', errors='ignore')

# Extract content between quotes
content = raw_data.split('="')[1].rstrip('"')
parts = content.split('~')

# Field mapping
# parts[3] = current price
# parts[31] = change (absolute)
# parts[32] = change percentage
price = float(parts[3])
change = float(parts[31])
change_pct = float(parts[32])
```

**Supported Indices**:
- `sh000001`: 上证指数
- `sh000300`: 沪深 300
- `sz399001`: 深证成指
- `sz399006`: 创业板指

### 2. 东方财富 (Secondary - Use curl)

**Endpoint**: `http://push2.eastmoney.com/api/qt/clk/get`

**Status**: ⚠️ Works with curl, fails with requests

**Parameters**:
```python
params = {
    'secids': 'sh000001,sh000300,sz399001,sz399006',
    'fields': 'f12,f13,f14,f15,f16'
}
```

**Implementation**:
```python
import subprocess
import json

url = 'http://push2.eastmoney.com/api/qt/clk/get'
params_str = 'secids=sh000001,sh000300&fields=f12,f13'
full_url = f"{url}?{params_str}"

result = subprocess.run(
    ['curl', '-s', '-A', 'Mozilla/5.0', '-m', '5', full_url],
    capture_output=True,
    text=True,
    timeout=10
)

data = json.loads(result.stdout)
if data.get('data') and data['data'].get('diff'):
    diffs = data['data']['diff']
    # Parse diff array...
```

### 3. 新浪财经 (Fallback)

**Endpoint**: `http://hq.sinajs.cn/list={code}`

**Status**: ⚠️ Slow but reliable fallback

**Encoding**: GBK

**Response Format**:
```javascript
var hq_str_sh000001="上证指数，4169.85,4169.54,4162.18,..."
```

**Parsing**:
```python
raw_data = proc_result.stdout.decode('gbk', errors='ignore')
if 'hq_str_' in raw_data:
    content = raw_data.split('=')[1].strip(';')
    parts = content.split(',')
    
    # parts[2] = current price
    # parts[3] = yesterday close
    current_price = float(parts[2])
    yesterday_close = float(parts[3])
    change = current_price - yesterday_close
```

## Complete Implementation Example

See `scripts/multi_source_adapter.py` for full implementation:

```python
from scripts.multi_source_adapter import MultiSourceAdapter

adapter = MultiSourceAdapter()

# Auto-fallback to best available source
indices = adapter.get_a_shares_index()

for name, data in indices.items():
    sign = "+" if data['change'] >= 0 else ""
    print(f"{name}: {data['price']:.2f} {sign}{data['change_pct']:.2f}%")
```

## Error Handling Patterns

### 1. Graceful Degradation

```python
def get_with_fallback(primary_func, fallback_func, mock_data):
    """Try primary, fallback, then mock data"""
    try:
        result = primary_func()
        if result:
            return result
    except Exception as e:
        print(f"⚠️ Primary source failed: {e}")
    
    try:
        result = fallback_func()
        if result:
            return result
    except Exception as e:
        print(f"⚠️ Fallback source failed: {e}")
    
    print("⚠️ Using mock data")
    return mock_data
```

### 2. Error Isolation

```python
# Don't let single failure break entire batch
results = {}
for code, name in indices:
    try:
        results[name] = fetch_single(code)
    except Exception as e:
        print(f"⚠️ {name} failed, continuing...")
        continue  # Skip failed item, continue with others
```

### 3. Timeout Handling

```python
# Always set reasonable timeouts
result = subprocess.run(
    ['curl', '-m', '10', url],  # 10s timeout
    timeout=15,  # Python timeout (5s buffer)
    ...
)
```

## Performance Optimization

### 1. Parallel Requests (Optional)

```python
from concurrent.futures import ThreadPoolExecutor

def fetch_all_indices(indices):
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(fetch_single, indices)
    return dict(zip(indices, results))
```

### 2. Caching (Recommended)

```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def get_index_cached(code, timestamp_minute):
    """Cache for 1 minute"""
    return fetch_single(code)

# Usage
now = int(time.time() / 60)  # Minute-level granularity
data = get_index_cached('sh000001', now)
```

## Testing Checklist

Before deploying multi-source adapter:

- [ ] Primary source returns valid data
- [ ] Fallback activates when primary fails
- [ ] All sources use correct encoding (GBK vs UTF-8)
- [ ] Timeouts are reasonable (5-10s)
- [ ] Error messages are informative
- [ ] Mock data has same structure as real data
- [ ] Single failure doesn't break entire batch

## Real-World Results

**Before Multi-Source** (2026-05-20):
```
⚠️ 实时数据获取失败，使用模拟数据演示格式
A 股指数成功率：0%
```

**After Multi-Source**:
```
✓ 使用 tencent 数据源获取 A 股指数
✓ 成功获取 4 个指数数据
A 股指数成功率：100%
数据获取时间：0.1-0.5s (was 5-10s)
```

## Related Files

- `scripts/multi_source_adapter.py`: Full implementation (262 lines)
- `scripts/data_fetcher.py`: Integration example
- `docs/optimization-report.md`: Complete optimization report
