# 回测引擎修复记录

## 问题诊断

### 1. 手续费过高
```python
# 原始配置
commission_rate = 0.001  # 0.1%
min_commission = 5.0     # 最低5元

# 问题：小额交易成本高达0.5%+
# 1000元交易手续费 = max(1000*0.001, 5) = 5元 = 0.5%
```

### 2. 无冷却期控制
- 每天检查所有基金买卖信号
- 没有交易间隔限制
- 震荡市可能频繁触发止损/止盈

### 3. 止损线过紧
- -5%止损在震荡市频繁触发
- 52天回测触发20次交易

## 修复方案

### 手续费优化
```python
commission_rate = 0.0005  # 0.05%（基金申购费率）
min_commission = 0.0      # 无最低消费
```

### 冷却期控制
```python
# 新增属性
self.last_trade_date = {}  # {fund_code: datetime}
self.cooldown_days = 7     # 交易后冷却7天

# 新增方法
def can_trade(self, fund_code: str, current_date: datetime) -> bool:
    if fund_code not in self.last_trade_date:
        return True
    days_since = (current_date - self.last_trade_date[fund_code]).days
    return days_since >= self.cooldown_days

def update_trade_date(self, fund_code: str, date: datetime):
    self.last_trade_date[fund_code] = date
```

### 交易方法修改
```python
def buy_fund(self, date, fund_code, amount, price, reason):
    if not self.can_trade(fund_code, date):
        return
    # ... 原有逻辑 ...
    self.update_trade_date(fund_code, date)

def sell_fund(self, date, fund_code, shares, price, reason):
    if not self.can_trade(fund_code, date):
        return
    # ... 原有逻辑 ...
    self.update_trade_date(fund_code, date)
```

## 修复效果

| 指标 | 修复前 | 修复后 | 改善 |
|------|--------|--------|------|
| 手续费率 | 0.1% | 0.05% | -50% |
| 最低手续费 | 5元 | 0元 | -100% |
| 冷却期 | 无 | 7天 | 新增 |
| 52天手续费 | 90元 | 45元 | -50% |
