# Adaptive Risk Engine - Data Structure & Pitfalls

## analyze_all() 返回结构

⚠️ `analyze_all()` 返回 list[dict]，每个 dict 的 key 是 `code`，**不是** `fund_code`：

```python
results = engine.analyze_all()
for r in results:
    # ✅ 正确: r['code']
    # ❌ 错误: r['fund_code']  → KeyError
    print(r['code'], r['name'], r['pnl_pct'], r['weighted_score'], r['action'])
    
    # 5因子评分明细
    print(r['scores']['profit_loss'])
    print(r['scores']['industry_trend'])
    print(r['scores']['mainline'])
    print(r['scores']['nav_trend'])
    print(r['scores']['valuation'])
    
    # 人类可读原因
    for reason in r['reasons']:
        print(f"  - {reason}")
```

## 完整字段列表

| Key | Type | Description |
|-----|------|-------------|
| code | str | 基金代码 (⚠️ 不是 fund_code) |
| name | str | 基金名称 |
| shares | float | 持有份额 |
| avg_cost | float | 平均成本 |
| current_nav | float | 当前净值 |
| pnl_pct | float | 盈亏百分比 (87.53 = +87.53%) |
| scores | dict | 5因子评分明细 |
| weighted_score | float | 加权综合分 |
| action | str | 建议操作 (中文) |
| action_level | str | 操作级别: sell/reduce/hold_watch/hold |
| reasons | list[str] | 原因列表 |

## Holdings 表 Schema 易错点

holdings 表的份额列是 `share_count`，**不是** `shares`：

```python
# ✅ 正确
cursor.execute("SELECT share_count, avg_cost, current_value, total_invested FROM holdings WHERE fund_code=?", (code,))

# ❌ 错误: SELECT shares ...  → OperationalError: no such column: shares
```

## 数据库 Schema 快速参考

```sql
-- holdings 表
CREATE TABLE holdings (
    id INTEGER PRIMARY KEY,
    fund_code TEXT,
    fund_name TEXT,
    share_count REAL,      -- ⚠️ 不是 shares
    avg_cost REAL,
    current_value REAL,
    total_invested REAL,
    total_withdrawn REAL,
    first_buy_date DATE,
    last_update_date DATE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```
