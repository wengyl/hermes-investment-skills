# 天天基金盘中估值 API

## API 端点

```
http://fundgz.1234567.com.cn/js/{fund_code}.js
```

返回 JSONP 格式:
```javascript
jsonpgz({"fundcode":"002112","name":"德邦鑫星价值灵活配置混合C","jzrq":"2026-05-28","dwjz":"6.1293","gsz":"6.0742","gszzl":"-0.90","gztime":"2026-05-29 10:18"});
```

## 字段说明

| 字段 | 含义 | 示例 |
|------|------|------|
| fundcode | 基金代码 | 002112 |
| name | 基金名称 | 德邦鑫星价值灵活配置混合C |
| jzrq | 净值日期 | 2026-05-28 |
| dwjz | 单位净值 | 6.1293 |
| gsz | 估算净值 | 6.0742 |
| gszzl | 估算涨跌幅% | -0.90 |
| gztime | 估值时间 | 2026-05-29 10:18 |

## 解析代码

```python
import subprocess, re, json

def get_fund_estimate(code: str) -> dict:
    result = subprocess.run(
        ['curl', '-s', '-A', 'Mozilla/5.0', '--connect-timeout', '3',
         f'http://fundgz.1234567.com.cn/js/{code}.js'],
        capture_output=True, timeout=5  # 不要用 text=True!
    )
    if result.returncode != 0 or not result.stdout:
        return {}
    
    text = result.stdout.decode('utf-8', errors='ignore')
    match = re.search(r'jsonpgz\((\{.*?\})\);', text, re.DOTALL)
    if not match:
        return {}
    
    try:
        data = json.loads(match.group(1))
        return {
            'gsz': float(data.get('gsz', 0)),
            'gszzl': float(data.get('gszzl', 0)),
            'gztime': data.get('gztime', ''),
            'dwjz': float(data.get('dwjz', 0)),
            'jzrq': data.get('jzrq', ''),
        }
    except (json.JSONDecodeError, ValueError):
        return {}
```

## ⚠️ Pitfalls

1. **不要用 `text=True`** - `subprocess.run(..., text=True)` 会导致中文字符编码问题，JSON解析失败。用 `capture_output=True` + 手动 `decode('utf-8', errors='ignore')`

2. **正则要用 `re.DOTALL`** - JSONP响应可能跨行，用 `r'jsonpgz\((\{.*?\})\);'` + `re.DOTALL`

3. **QDII/LOF基金可能无估值** - 022184(QDII)、501205(LOF) 等基金可能返回空数据

4. **交易时间** - 只在交易时段(9:30-15:00)有估值，盘前盘后返回空

5. **批量请求** - 循环请求多只基金时，异常处理只 catch `json.JSONDecodeError, ValueError`，不要用裸 `except Exception: continue`（会吞掉所有错误）
