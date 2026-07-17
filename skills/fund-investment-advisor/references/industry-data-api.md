# Industry Data API Patterns

获取行业级别数据（资金流向、基金配置）的 API 模式和 fallback 策略。

---

## 行业资金流向 API

### 东方财富行业资金流向

**API Endpoint:**
```
http://push2.eastmoney.com/api/qt/clist/get
```

**关键参数：**
- `fid=f62`: 主力净流入
- `fs=m:90+t:2`: **申万行业分类** - 这是关键！使用 `m:90+t:2` 获取行业板块数据
- `fields=f12,f13,f14,f62,f63`: 返回字段（f12=代码，f14=名称，f62=净流入，f63=净流出）

**重要更新（2026-05-25）**：
- 之前的 `fs=bk` 参数已失效，返回 `rc:102` 错误
- 现在使用 `fs=m:90+t:2` 获取申万行业分类数据
- 返回31个行业板块，包括半导体、电力、电子等

**示例请求（使用 curl）：**
```bash
# 使用申万行业分类 (fs=m:90+t:2)
curl -s 'http://push2.eastmoney.com/api/qt/clist/get?fid=f62&po=1&pz=50&pn=1&np=1&fltt=2&invt=2&fs=m:90+t:2&fields=f12,f13,f14,f62,f63'

# 或者使用更简洁的参数
curl -s 'http://push2.eastmoney.com/api/qt/clist/get?fid=f62&fs=m:90+t:2&fields=f12,f14,f62,f63'
```

**响应解析：**
```python
data = json.loads(response)
if data.get('data') and data['data'].get('diff'):
    industries = data['data']['diff']
    for ind in industries:
        name = ind.get('f14', '')  # 行业名称
        net_inflow = float(ind.get('f62', 0))  # 净流入（元）
        net_outflow = float(ind.get('f63', 0))  # 净流出（元）
```

**常见错误：**
- ❌ `fs=bk` - 已失效，返回 `rc:102` 错误（2026-05-25 更新）
- ❌ `fs=m:0+t:6` - 返回的是个股数据，不是行业
- ✅ `fs=m:90+t:2` - 返回申万行业分类数据（31个行业）

---

## 基金持仓 API

### 东方财富基金持仓

**API Endpoint:**
```
http://api.fund.eastmoney.com/f10/stockposition
```

**参数：**
```
fundcode=基金代码
pageIndex=1
pageSize=10
```

**响应格式：**
```json
{
  "Data": {
    "STOCKINFO": "股票名 1|8.5;股票名 2|7.2;..."
  }
}
```

**解析代码：**
```python
holdings = data['Data']['STOCKINFO']
for stock in holdings.split(';'):
    parts = stock.split('|')
    stock_name = parts[0]
    ratio = float(parts[1])
```

**Fallback 策略：**
当 API 返回 404 或失败时，使用基金名称关键词推断行业配置。

---

## 基金行业配置推断

基于基金名称关键词的行业映射：

```python
industry_keywords = {
    '通信': {'通信': 80, '科技': 10, '其他': 10},
    '畜牧': {'畜牧养殖': 85, '农业': 10, '其他': 5},
    '港股': {'金融': 40, '地产': 20, '消费': 20, '其他': 20},
    '科技': {'半导体': 30, '人工智能': 25, '互联网': 25, '其他': 20},
    '互联网': {'互联网': 60, '人工智能': 20, '其他': 20},
    '全球': {'互联网': 35, '半导体': 25, '人工智能': 20, '其他': 20},
    '沪深 300': {'金融': 30, '工业': 20, '消费': 20, '其他': 30},
    '创新': {'医药生物': 30, '科技': 25, '新能源': 20, '其他': 25},
    '驱动': {'科技': 35, '制造业': 25, '其他': 40},
    '红利': {'金融': 40, '能源': 20, '地产': 15, '其他': 25},
}
```

**推断逻辑：**
1. 遍历关键词字典
2. 如果基金名称包含关键词，返回对应行业配置
3. 默认返回 `{'其他': 100}`

---

## 策略建议生成

基于行业资金流向和基金配置的匹配：

```python
def generate_strategy(fund_industry, capital_flow):
    """
    生成策略建议
    """
    # 检查基金主要行业是否在资金流入前 3
    top_inflow_industries = [ind['name'] for ind in capital_flow['summary']['top_inflow']]
    top_outflow_industries = [ind['name'] for ind in capital_flow['summary']['top_outflow']]
    
    signals = []
    
    # 检查资金流入
    for industry, ratio in fund_industry.items():
        if ratio > 20 and industry in top_inflow_industries:
            signals.append('资金流入')
    
    # 检查资金流出
    for industry, ratio in fund_industry.items():
        if ratio > 20 and industry in top_outflow_industries:
            signals.append('资金流出')
    
    # 生成建议
    if '资金流入' in signals and '资金流出' not in signals:
        return '可加仓'
    elif '资金流出' in signals:
        return '谨慎持有'
    else:
        return '持有观望'
```

---

## 实现示例

### data_fetcher.py - 行业资金流向

```python
def get_industry_capital_flow(self) -> Dict:
    """获取行业主力资金流向 - 使用申万行业分类"""
    url = 'http://push2.eastmoney.com/api/qt/clist/get?fid=f62&po=1&pz=50&pn=1&np=1&fltt=2&invt=2&fs=m:90+t:2&fields=f12,f13,f14,f62,f63'
    
    proc_result = subprocess.run(
        ['curl', '-s', '-A', 'Mozilla/5.0', '-m', '10', url],
        capture_output=True, text=True, timeout=15
    )
    
    # 解析响应...
    # 返回格式：{
    #   'industries': [{'name': '半导体', 'net_inflow': 6469.13, ...}],
    #   'summary': {'total_net_inflow': 7694, 'top_inflow': [...], 'top_outflow': [...]}
    # }
```

### data_fetcher.py - 基金持仓

```python
def get_fund_holdings(self, fund_code: str, fund_name: str = "") -> Optional[Dict]:
    """获取基金持仓，API 失败时推断"""
    try:
        # 尝试 API...
        pass
    except:
        # Fallback: 名称推断
        return self._infer_industry_from_name(fund_name)
```

### advisor.py - 策略建议

```python
def generate_strategy_suggestions(self, holdings, industry_data, capital_flow):
    """生成个性化策略建议"""
    for code, name, shares, cost, current in holdings:
        if code in industry_data:
            fund_industry = industry_data[code]
            strategy = self._match_industry_with_flow(fund_industry, capital_flow)
            # 添加到建议列表...
```

---

## 调试技巧

### 测试行业资金流向 API

```bash
# 正确（申万行业分类）
curl -s 'http://push2.eastmoney.com/api/qt/clist/get?fs=m:90+t:2&fid=f62&fields=f12,f14,f62,f63' | jq '.data.diff[:3]'

# 错误（个股）
curl -s 'http://push2.eastmoney.com/api/qt/clist/get?fs=m:0+t:6&fid=f62&fields=f12,f14,f62,f63' | jq '.data.diff[:3]'

# 注意：fs=bk 参数已失效，会返回 rc:102 错误
```

### 测试基金持仓 API

```bash
curl -s 'http://api.fund.eastmoney.com/f10/stockposition?fundcode=020692&pageIndex=1&pageSize=10'
```

### 检查推断结果

```python
from scripts.data_fetcher import FundDataFetcher
fetcher = FundDataFetcher()
result = fetcher.get_fund_holdings('020692', '博时中证全指通信设备指数 C')
print(result['industry_allocation'])
# 输出：{'通信': 80, '科技': 10, '其他': 10}
```

---

## 版本历史

**2026-05-25**: 
- 修复：行业资金流向 API 参数从 `fs=bk` 更新为 `fs=m:90+t:2`
- 修复：`fs=bk` 参数已失效，返回 `rc:102` 错误
- 更新：使用申万行业分类数据（31个行业板块）
- 更新：文档中所有相关参数和示例

**2026-05-21**: 
- 添加行业资金流向 API (`fs=bk` 参数，现已失效)
- 添加基金持仓推断 fallback 机制
- 添加策略建议生成逻辑
- 修复：之前使用 `fs=m:0+t:6` 获取的是个股数据
