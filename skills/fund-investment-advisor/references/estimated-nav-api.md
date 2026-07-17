# 天天基金盘中估值API

## API Endpoint

```
GET http://fundgz.1234567.com.cn/js/{fund_code}.js
```

- 无需认证，免费接口
- 返回JSONP格式
- 盘中实时更新（交易日9:30-15:00）
- 非交易时段返回上一交易日估值

## Response Format

```javascript
jsonpgz({
  "fundcode": "002112",
  "name": "德邦鑫星价值灵活配置混合C",
  "jzrq": "2026-05-28",      // 净值日期（最近确认净值的日期）
  "dwjz": "6.1293",           // 单位净值（最新确认值）
  "gsz": "6.0742",            // 估算净值（盘中实时）
  "gszzl": "-0.90",           // 估算涨跌幅（%，相对上一确认净值）
  "gztime": "2026-05-29 10:18" // 估值时间
})
```

## 字段说明

| 字段 | 含义 | 类型 | 示例 |
|------|------|------|------|
| fundcode | 基金代码 | string | "002112" |
| name | 基金名称 | string | "德邦鑫星..." |
| jzrq | 净值日期 | string | "2026-05-28" |
| dwjz | 单位净值 | string | "6.1293" |
| gsz | 估算净值 | string | "6.0742" |
| gszzl | 估算涨跌幅% | string | "-0.90" |
| gztime | 估值时间 | string | "2026-05-29 10:18" |

## 解析代码

```python
import subprocess
import json
import re

def get_fund_estimate(fund_code: str) -> dict:
    """获取单只基金盘中估值"""
    result = subprocess.run(
        ['curl', '-s', '-A', 'Mozilla/5.0', '--connect-timeout', '3',
         f'http://fundgz.1234567.com.cn/js/{fund_code}.js'],
        capture_output=True, text=True, timeout=5
    )
    if result.returncode == 0 and result.stdout:
        match = re.search(r'jsonpgz\((.+?)\)', result.stdout)
        if match:
            data = json.loads(match.group(1))
            return {
                'gsz': float(data.get('gsz', 0)),
                'gszzl': float(data.get('gszzl', 0)),
                'gztime': data.get('gztime', ''),
                'dwjz': float(data.get('dwjz', 0)),
                'jzrq': data.get('jzrq', ''),
            }
    return {}
```

## 限制

- **QDII基金**（如022184富国全球科技）：无盘中估值，API返回空
- **LOF基金**（如501205鹏华创新未来）：部分无估值
- **ETF联接基金**：一般有估值
- **估值精度**：估算值与实际净值可能有0.1-0.5%偏差
- **更新频率**：盘中约每30秒更新一次

## 已知可用基金类型

| 类型 | 有估值? | 示例 |
|------|---------|------|
| 普通开放式基金 | ✅ | 002112, 005165 |
| ETF联接基金 | ✅ | 014414, 018388 |
| 指数基金 | ✅ | 020692, 026211 |
| QDII基金 | ❌ | 022184 |
| LOF基金 | 部分 | 501205 |
