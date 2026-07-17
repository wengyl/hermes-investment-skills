# SSL Workaround for macOS LibreSSL

## Problem

On macOS, Python uses LibreSSL 2.8.3, but `urllib3 v2.x` requires OpenSSL 1.1.1+:

```
urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'
SSLError: SSLEOFError(8, 'EOF occurred in violation of protocol (_ssl.c:1129)')
```

## Solutions

### Solution 1: Downgrade urllib3 (Recommended)

```bash
python3 -m pip install 'urllib3<2.0' --upgrade
```

This downgrades from v2.6.3 to v1.26.20, which works with LibreSSL.

**Status**: ✅ Works for most cases, but some APIs still fail.

### Solution 2: Use http.client Directly (Most Reliable)

Bypass `requests` entirely and use Python's built-in `http.client`:

```python
import http.client
import ssl
import json

def make_request(host, path):
    """Make HTTPS request with relaxed SSL verification"""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    conn = http.client.HTTPSConnection(
        host,
        port=443,
        timeout=15,
        context=context
    )
    
    conn.request('GET', path, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    })
    
    response = conn.getresponse()
    status = response.status
    raw_data = response.read()
    conn.close()
    
    # Decode with multiple encodings
    for encoding in ['utf-8', 'gbk', 'gb2312']:
        try:
            data = raw_data.decode(encoding)
            return status, data
        except:
            continue
    
    return status, raw_data
```

**Status**: ✅ Works reliably for all fund APIs.

### Solution 3: Update certifi

```bash
python3 -m pip install --upgrade certifi
```

Then use system certificates:

```python
import requests
response = requests.get('https://...', verify='/etc/ssl/cert.pem')
```

**Status**: ⚠️ Doesn't fully fix the issue on macOS.

## Test Code

```python
# Test if SSL is working
import requests

try:
    response = requests.get('https://fund.eastmoney.com/', timeout=10)
    print(f"✅ Success! Status: {response.status_code}")
except Exception as e:
    print(f"❌ Failed: {e}")
    print("→ Use http.client instead of requests")
```

## Environment Details

- **macOS**: 26.3.1 (from session)
- **Python**: 3.9
- **SSL**: LibreSSL 2.8.3
- **urllib3**: Downgrade to <2.0
- **certifi**: Latest version

## Session Evidence

From the debugging session:
- `curl` works fine (network is OK)
- `requests` fails with SSLEOFError
- `http.client` works perfectly
- API endpoints are accessible, just SSL handshake fails

## Recommendation

**Always use `http.client` for Chinese fund APIs on macOS.**

The `requests` library has too many SSL compatibility issues with LibreSSL. The workaround is simple and reliable.
