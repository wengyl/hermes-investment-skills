# SSL Compatibility Workaround for macOS Financial APIs

## Problem Statement

On macOS with Python 3.9+, the `requests` library fails to connect to Chinese financial APIs:

```
SSLError: HTTPSConnectionPool(host='fund.eastmoney.com', port=443): 
Max retries exceeded with url / (Caused by SSLError(SSLEOFError(8, 
'EOF occurred in violation of protocol (_ssl.c:1129)')))
```

## Root Cause

- macOS ships with **LibreSSL 2.8.3**
- `urllib3 v2.x` (used by `requests`) requires **OpenSSL 1.1.1+**
- Version mismatch causes SSL handshake to fail

## Diagnostic Steps

### 1. Check Python SSL version
```python
import ssl
print(ssl.OPENSSL_VERSION)  # Shows: LibreSSL 2.8.3
```

### 2. Verify network works
```bash
curl -v https://fund.eastmoney.com/  # Should work
ping <eastmoney-server-ip>  # Should respond
```

If `curl` works but Python fails, it's a library issue, not network.

### 3. Check urllib3 version
```python
import urllib3
print(urllib3.__version__)  # v2.x will fail
```

## Solutions

### Solution 1: Use `http.client` (Recommended)

Bypass `requests` entirely:

```python
import http.client
import ssl
import json

def fetch_fund_data(url_path):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    conn = http.client.HTTPSConnection(
        'api.fund.eastmoney.com',
        port=443,
        timeout=10,
        context=context
    )
    
    conn.request('GET', url_path)
    response = conn.getresponse()
    raw_data = response.read()
    conn.close()
    
    # Decode with GBK (common for Chinese APIs)
    for encoding in ['gbk', 'gb2312', 'utf-8']:
        try:
            return json.loads(raw_data.decode(encoding))
        except:
            continue
    
    raise ValueError("Failed to decode response")
```

**Advantages**:
- No dependency issues
- Works out of the box
- Full control over SSL context

### Solution 2: Downgrade urllib3

```bash
python3 -m pip install 'urllib3<2.0'
```

This installs `urllib3 v1.x` which is compatible with LibreSSL.

**Warning**: May affect other packages that depend on `urllib3 v2.x`

### Solution 3: Use requests with workaround

```python
import requests
from urllib3.util import ssl_

# Force use of older SSL context
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,
    pool_maxsize=10,
    max_retries=3
)
session.mount('https://', adapter)

# Try with verify=False (NOT recommended for production)
response = session.get('https://api.fund.eastmoney.com/...', verify=False)
```

**Warning**: Disabling SSL verification is a security risk.

## Testing

Verify the fix works:

```python
import http.client
import ssl

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

conn = http.client.HTTPSConnection(
    'fund.eastmoney.com',
    port=443,
    timeout=10,
    context=context
)

conn.request('GET', '/')
response = conn.getresponse()
print(f"Status: {response.status}")  # Should be 200
conn.close()
```

## Session Notes

- Date: 2026-05-16
- System: macOS 26.3.1, Python 3.9
- Target API: 天天基金 (fund.eastmoney.com)
- Resolution: Switched to `http.client` for all financial API calls

## Related

- See `api-encoding.md` for encoding issues
- See main SKILL.md for data integrity principles
