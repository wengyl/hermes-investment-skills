# 基金投资分析标准流程

**日期**: 2026-05-22  
**用途**: 对用户持仓进行深度分析，提供投资建议

---

## 分析维度

### 1. 总体表现分析

```python
# 计算指标
total_value = sum(h["value"] for h in holdings)  # 持仓总市值
total_cost = sum(h["cost"] for h in holdings)    # 持仓总成本
total_profit = total_value - total_cost          # 总盈亏
total_profit_pct = total_profit / total_cost * 100  # 总收益率

# 今日收益
total_daily = sum(h["daily"] for h in holdings)
total_daily_pct = total_daily / total_value * 100
```

### 2. 收益排名

**排序依据**: 按总收益金额降序

```python
sorted_by_profit = sorted(holdings, key=lambda x: x["profit"], reverse=True)
```

**输出格式**:
```
🏆 收益排名
排名  基金名称              总收益       收益率
1     博时通信设备         +3,049.69   +718.05%
2     富国全球科技         +2,254.40   +77.74%
...
```

### 3. 今日收益排名

**排序依据**: 按今日收益金额降序

```python
sorted_by_daily = sorted(holdings, key=lambda x: x["daily"], reverse=True)
```

### 4. 亏损基金分析

**筛选条件**: `profit < 0`

```python
loss_funds = [h for h in holdings if h["profit"] < 0]
```

**输出格式**:
```
⚠️ 亏损基金
基金名称                 亏损额       亏损率      建议
招商畜牧养殖           -2,912.59   -78.56%    立即止损
华泰港股红利           -2,562.24   -65.07%    等待反弹
```

### 5. 行业配置分析

**分类规则** (根据基金名称推断):
- 科技/半导体: "科技"、"半导体"、"通信"、"计算机"、"人工智能"
- 医药生物: "医药"、"生物"、"医疗"、"创新"
- 畜牧养殖: "畜牧"、"养殖"、"农业"
- 港股红利: "港股"、"红利"、"香港"
- 价值配置: "价值"、"灵活配置"
- 消费: "消费"、"白酒"、"食品"
- 新能源: "新能源"、"光伏"、"锂电"
- 其他: 不匹配以上类别

**行业表现计算**:
```python
industry_value = sum(h["value"] for h in industry_funds)
industry_weight = industry_value / total_value * 100
industry_profit = sum(h["profit"] for h in industry_funds)
```

### 6. 持仓集中度分析

**计算方法**:
```python
# 按市值排序
sorted_by_value = sorted(holdings, key=lambda x: x["value"], reverse=True)

# 前 3 大持仓占比
top3_value = sum(h["value"] for h in sorted_by_value[:3])
top3_pct = top3_value / total_value * 100

# 判断标准
if top3_pct > 60:
    risk = "⚠️  集中度较高，建议分散投资"
elif top3_pct > 40:
    risk = "📊 集中度适中"
else:
    risk = "✅ 集中度较低，风险分散"
```

### 7. 风险评估

**最大回撤基金**:
```python
max_loss_fund = min(holdings, key=lambda x: x["pct"])
```

**行业相关性风险**:
- 科技类占比超过 40%：⚠️ 行业轮动风险
- 单一行业占比超过 30%：⚠️ 集中风险

### 8. 投资建议

#### 止盈策略

| 收益率范围 | 建议 |
|-----------|------|
| > 100% | **分批止盈**，保留底仓 |
| > 50% | **部分止盈**，锁定利润 |
| > 20% | **持有观望**，设止损线 |
| < 20% | **继续持有** |

#### 止损策略

| 亏损率范围 | 建议 |
|-----------|------|
| < -70% | **立即止损**，换仓 |
| < -50% | **评估止损**，关注基本面 |
| < -30% | **谨慎持有**，等待反弹 |
| > -30% | **继续持有** |

#### 调仓建议

1. **减仓条件**:
   - 行业占比 > 40%
   - 收益率 > 50%
   - 基本面恶化

2. **加仓条件**:
   - 行业占比 < 20%
   - 收益率 > 0% 且 < 30%
   - 基本面良好

3. **换仓条件**:
   - 亏损率 > 50%
   - 连续下跌超过 3 个月
   - 行业前景不佳

---

## 分析报告模板

```python
def generate_investment_analysis(holdings_data, industry_mapping):
    """
    生成投资分析报告
    
    Args:
        holdings_data: 基金持仓数据列表
        industry_mapping: 行业分类映射
    
    Returns:
        分析报告文本
    """
    report = []
    
    # 1. 总体表现
    report.append("📊 总体表现")
    report.append(f"持仓总市值：{total_value:,.2f} 元")
    report.append(f"总盈亏：{total_profit:+,.2f} 元 ({total_profit_pct:+.2f}%)")
    
    # 2. 收益排名
    report.append("\n🏆 收益排名")
    for i, h in enumerate(sorted_by_profit[:6], 1):
        report.append(f"{i} {h['name']}: {h['profit']:+,.2f} ({h['pct']:+.2f}%)")
    
    # 3. 亏损基金
    report.append("\n⚠️ 亏损基金")
    for h in loss_funds:
        suggestion = get_loss_suggestion(h['pct'])
        report.append(f"- {h['name']}: {h['profit']:+,.2f} ({h['pct']:+.2f}%) {suggestion}")
    
    # 4. 行业配置
    report.append("\n🏭 行业配置")
    for industry, funds in industry_mapping.items():
        weight = sum(f['value'] for f in funds) / total_value * 100
        profit = sum(f['profit'] for f in funds)
        report.append(f"{industry} ({weight:.1f}%): {profit:+,.2f}")
    
    # 5. 风险评估
    report.append("\n⚠️ 风险评估")
    report.append(f"前 3 大持仓占比：{top3_pct:.1f}%")
    if top3_pct > 60:
        report.append("⚠️  集中度较高，建议分散投资")
    
    # 6. 投资建议
    report.append("\n💡 投资建议")
    report.extend(generate_suggestions(holdings_data))
    
    return "\n".join(report)
```

---

## 自动化分析脚本

### `scripts/investment_analysis.py`

```python
#!/usr/bin/env python3
"""
基金投资分析脚本
用法: python3 investment_analysis.py
"""
import sqlite3
from datetime import datetime

# 数据库路径
DB_PATH = "~/.hermes/fund-advisor/data/fund_system.db"

# 行业分类关键词
INDUSTRY_KEYWORDS = {
    "科技/半导体": ["科技", "半导体", "通信", "计算机", "人工智能", "芯片"],
    "医药生物": ["医药", "生物", "医疗", "创新"],
    "畜牧养殖": ["畜牧", "养殖", "农业"],
    "港股红利": ["港股", "红利", "香港"],
    "价值配置": ["价值", "灵活配置"],
    "消费": ["消费", "白酒", "食品"],
    "新能源": ["新能源", "光伏", "锂电"],
}

def classify_industry(fund_name):
    """根据基金名称分类行业"""
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in fund_name:
                return industry
    return "其他"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 查询持仓数据
    cursor.execute('''
        SELECT h.fund_code, h.fund_name, h.share_count, h.avg_cost, 
               n.nav, n.daily_change_pct
        FROM holdings h
        LEFT JOIN fund_nav_history n ON h.fund_code = n.fund_code
        ORDER BY h.fund_code
    ''')
    
    holdings = []
    for row in cursor.fetchall():
        code, name, shares, avg_cost, nav, daily_pct = row
        
        if nav and shares:
            current_value = nav * shares
            cost_value = avg_cost * shares
            profit = current_value - cost_value
            profit_pct = (profit / cost_value * 100) if cost_value > 0 else 0
            
            holdings.append({
                "code": code,
                "name": name,
                "value": current_value,
                "cost": cost_value,
                "profit": profit,
                "pct": profit_pct,
                "daily": current_value * (daily_pct / 100) if daily_pct else 0,
                "daily_pct": daily_pct or 0,
                "industry": classify_industry(name)
            })
    
    conn.close()
    
    # 生成分析报告
    if holdings:
        print("📊 基金投资分析报告")
        print("=" * 70)
        # ... 其余分析逻辑
    else:
        print("❌ 无持仓数据")

if __name__ == "__main__":
    main()
```

---

## 更新日志

**2026-05-22**: 初始版本
- 定义投资分析标准流程
- 行业分类规则
- 止盈止损策略
- 风险评估方法
- 报告生成模板
