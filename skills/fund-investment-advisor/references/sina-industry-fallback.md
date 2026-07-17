# 新浪财经行业数据 Fallback

## 问题背景

东方财富 push2.eastmoney.com API 从某些服务器访问时返回 HTTP 000（空响应），
即使添加正确的 User-Agent、Referer、Origin 头部也无法解决。

浏览器可以加载页面（data.eastmoney.com/bkzj/hy.html），但 curl/requests 无法访问底层 API。

## 解决方案

使用新浪财经行业数据作为 fallback：

### API 端点

```
http://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php
```

### 返回格式

- **编码**: GBK（需要 `decode('gbk', errors='ignore')`）
- **格式**: JavaScript 变量赋值
- **变量名**: `S_Finance_bankuai_sinaindustry`

```javascript
var S_Finance_bankuai_sinaindustry = {
  "new_blhy": "new_blhy,玻璃行业,19,22.19,0.75,3.49,1101440952,25548830572,sh603601,10.005,23.530,2.140,再升科技",
  ...
}
```

### 字段解析

逗号分隔的字段：
1. `code` - 板块代码
2. `name` - 行业名称
3. `stock_count` - 成分股数量
4. `avg_price` - 平均价
5. `price_change` - 价格变动
6. `change_pct` - 涨跌幅（%）
7. `volume` - 成交量
8. `amount` - 成交额（元）
9. `leading_stock_code` - 领涨股代码
10-12. 领涨股数据
13. `leading_stock_name` - 领涨股名称

### Python 解析代码

```python
import subprocess, re

def _fetch_sina_industry_data():
    url = 'http://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php'
    proc_result = subprocess.run(
        ['curl', '-s', '-A', 'Mozilla/5.0', '-m', '10', url],
        capture_output=True, timeout=15
    )
    
    if proc_result.returncode != 0 or not proc_result.stdout:
        return None
    
    text = proc_result.stdout.decode('gbk', errors='ignore')
    
    match = re.search(
        r'var\s+S_Finance_bankuai_sinaindustry\s*=\s*(\{.*?\})\s*;?\s*$',
        text, re.MULTILINE | re.DOTALL
    )
    if not match:
        return None
    
    data_str = match.group(1)
    entries = re.findall(r'"([^"]+)":"([^"]+)"', data_str)
    
    industries = []
    for key, value in entries:
        parts = value.split(',')
        if len(parts) >= 8:
            industries.append({
                'code': parts[0],
                'name': parts[1],
                'change_pct': float(parts[5]),
                'amount': int(parts[7]) / 10000,  # 转为万元
                'leading_stock': parts[12] if len(parts) > 12 else ''
            })
    
    industries.sort(key=lambda x: x['change_pct'], reverse=True)
    return industries
```

### 与东方财富数据的差异

| 维度 | 东方财富 push2 | 新浪财经 |
|------|---------------|---------|
| 数据类型 | 主力资金净流入/净流出 | 行业涨跌幅+成交额 |
| 时效性 | 实时 | 收盘后更新 |
| 覆盖范围 | 申万行业分类 | 新浪行业分类 |
| 编码 | UTF-8 | GBK |
| 可用性 | 可能被服务器屏蔽 | 稳定可用 |

### 报告适配

在 advisor.py 的 `_format_capital_flow_summary()` 中根据 `data_type` 字段区分显示：
- `capital_flow`: 显示净流入/净流出（原有格式）
- `change_pct`: 显示涨跌幅+成交额（新格式）

### 注意事项

1. 新浪行业分类与申万行业分类不完全一致
2. 涨跌幅不等于资金流向，但可作为趋势参考
3. 成交额可间接反映资金活跃度
4. 数据更新频率：收盘后一次
