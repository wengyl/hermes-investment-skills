# Fund Advisor System API Endpoints

## EastMoney (东方财富) APIs

### Market Data — clist API (Stable ✅)

#### 行业资金流向
```python
url = "http://push2.eastmoney.com/api/qt/clist/get"
params = {
    'fid': 'f62',  # 资金净流入
    'po': '1', 'pz': '50', 'pn': '1', 'np': '1',
    'fltt': '2', 'invt': '2',
    'fs': 'm:90+t:2',  # 申万行业分类 (NOT fs=bk which is deprecated)
    'fields': 'f12,f13,f14,f62,f63'
}
```

#### 概念板块资金流向
```python
# Same as above but fs=m:90+t:3
'fs': 'm:90+t:3',  # 概念板块
```

#### 个股资金流向Top
```python
# fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23 (沪深A股)
'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
'fields': 'f12,f13,f14,f62',
```

### Market Data — stock/get API (⚠️ Unstable)

**⚠️ As of 2026-07-06, `push2.eastmoney.com/api/qt/stock/get` returns `data:null` for international indices (US stocks, HK stocks, FX). Use Sina APIs instead.**

The clist API remains stable. Only stock/get is unreliable.

### 北向资金 (kamt.kline API ✅)
```python
url = ('https://push2.eastmoney.com/api/qt/kamt.kline/get?'
       'fields1=f1,f3&fields2=f51,f52,f53,f54,f55,f56&klt=101&lmt=1&'
       'ut=b2884a393a59ad64002292a3e90d46a5')
# Returns: {"data": {"hk2sh": ["日期,净买入,累计,余额"], "hk2sz": [...]}}
# Note: Returns 0.00 on weekends/holidays
```

### 基金数据
```python
# 基金基本信息
url = "http://api.fund.eastmoney.com/f10/jjjj"
params = {'fundcode': '005165', 'pageIndex': 1, 'pageSize': 1}

# 基金净值历史
url = "http://api.fund.eastmoney.com/f10/lsjz"
params = {'fundcode': '005165', 'start': '20240101', 'end': '20241231'}
```

## Sina Finance APIs (✅ Stable)

### ⚠️ Critical: GBK Encoding

ALL Sina API responses are **GBK** encoded. When using subprocess:
```python
# WRONG — causes 'utf-8' codec can't decode error
proc = subprocess.run(['curl', '-s', url], capture_output=True, text=True)

# RIGHT — manually decode GBK
proc = subprocess.run(['curl', '-s', '-H', 'Referer: https://finance.sina.com.cn', '-m', '10', url],
                       capture_output=True, timeout=15)
stdout = proc.stdout.decode('gbk', errors='replace')
```

### 美股三大指数
```python
# URL: https://hq.sinajs.cn/list=gb_dji,gb_ixic,gb_inx
# Header: Referer: https://finance.sina.com.cn (required)
# Format: var hq_str_gb_dji="道琼斯,52900.07,1.14,...";
# fields[1] = price, fields[2] = change_pct
```

### 港股恒生指数
```python
# URL: https://hq.sinajs.cn/list=rt_hkHSI
# Format: var hq_str_rt_hkHSI="HSI,恒生指数,...,现价,...,涨跌幅,...";
# fields[6] = price, fields[8] = change_pct
```

### 美元/人民币汇率
```python
# URL: https://hq.sinajs.cn/list=USDCNY
# Format: var hq_str_USDCNY="时间,买价,卖价,...";
# rate = (float(fields[1]) + float(fields[2])) / 2  # 中间价
```

### COMEX黄金期货
```python
# URL: https://hq.sinajs.cn/list=hf_GC
# Format: var hq_str_hf_GC="现价,...,昨收,...";
# fields[0] = price, fields[7] = prev_close
# change_pct = (price - prev_close) / prev_close * 100
```

## ~~Yahoo Finance APIs~~ (❌ Dead as of 2026-07)

Yahoo Finance `query1.finance.yahoo.com/v8/finance/chart/{symbol}` no longer returns valid JSON.
Replaced by Sina Finance APIs for all US stock data.

## API 注意事项

1. **502 Bad Gateway** — EastMoney API 偶尔返回 502，重试或降级
2. **JSON 解析失败** — 检查响应是否为空或 HTML 错误页
3. **超时** — 设置合理 timeout (5-10 秒)
4. **东财 stock/get 不稳定** — 用新浪替代港股/美股/汇率/黄金
5. **新浪 GBK 编码** — 必须 `decode('gbk')`，不能用 `text=True`
6. **新浪 Referer header** — 必须传 `-H 'Referer: https://finance.sina.com.cn'`

## 测试命令

```bash
# 测试行业资金流向
curl -s "http://push2.eastmoney.com/api/qt/clist/get?fid=f62&po=1&pz=5&pn=1&np=1&fltt=2&invt=2&fs=m:90+t:2&fields=f12,f14,f62"

# 测试美股数据 (Sina)
curl -s -H "Referer: https://finance.sina.com.cn" "https://hq.sinajs.cn/list=gb_dji,gb_ixic,gb_inx"

# 测试港股 (Sina)
curl -s -H "Referer: https://finance.sina.com.cn" "https://hq.sinajs.cn/list=rt_hkHSI"

# 测试汇率 (Sina)
curl -s -H "Referer: https://finance.sina.com.cn" "https://hq.sinajs.cn/list=USDCNY"

# 测试北向资金
curl -s "https://push2.eastmoney.com/api/qt/kamt.kline/get?fields1=f1,f3&fields2=f51,f52,f53,f54,f55,f56&klt=101&lmt=1&ut=b2884a393a59ad64002292a3e90d46a5"
```
