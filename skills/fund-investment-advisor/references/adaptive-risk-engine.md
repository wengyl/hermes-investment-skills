# 多因子自适应风控引擎设计

## 核心思想

固定阈值止盈止损（盈利50%卖、亏损15%止损）忽略了行业基本面、估值、趋势等上下文。
多因子评分替代单一盈亏%，综合判断是否该卖。

## 5因子评分体系 (v2)

| 因子 | 权重 | 评分逻辑 |
|------|------|---------|
| 盈亏幅度 | 20% | 盈利80%→10分，盈利10-20%→60分，微亏→50分 |
| 行业趋势 | 20% | 来自市场主线热度，去掉+20基础分 |
| 主线匹配 | 15% | 是否在当前市场主线上 |
| 净值趋势 | 20% | MA5/MA20关系 + 近5天涨跌 |
| 估值水位 | 25% | NAV在90日区间位置，非线性映射 |

## 决策阈值 (v2)

| 综合分 | 建议 | 说明 |
|--------|------|------|
| ≥65 | 持有观望 | 基本面良好 |
| 50-65 | 持有+关注 | 整体尚可 |
| 35-50 | 考虑减仓 | 风险偏高 |
| <35 | 建议止损/止盈 | 风险较高 |

## 阈值触发机制

**关键设计**：不是每天都生成信号，而是跟踪分数变化，只有跨过阈值边界(35/50/65)时才触发。

```python
def get_zone(score):
    if score < 35: return 'sell'
    elif score < 50: return 'reduce'
    elif score < 65: return 'hold_watch'
    else: return 'hold'

# 只有跨过阈值才触发信号
if get_zone(prev_score) != get_zone(current_score):
    triggered = True
```

## 回测结果 (2026-03~2026-05, 9只基金)

| 指标 | 固定阈值 | 自适应v1(每天) | 自适应v2(阈值触发) |
|------|---------|---------------|-------------------|
| 信号总数 | 7次 | 58次 | 10次 |
| 准确率 | 86% | 86% | 90% |
| 覆盖基金 | 2只 | 9只 | 6只 |

## 评分因子详细逻辑

### 盈亏幅度 (_calc_profit_score)
- ≥80%: 10分（超高盈利，回调风险极大）
- 60-80%: 20分
- 40-60%: 35分
- 20-40%: 50分
- 10-20%: 60分
- 0-10%: 55分
- -5~0%: 50分
- -10~-5%: 40分
- -15~-10%: 25分
- <-15%: 10分

### 估值水位 (_calc_valuation_score)
非线性映射，放大低估/高估差异：
- NAV在90日区间<30%位置: 80-100分（低估区）
- 30-50%位置: 60-80分
- 50-70%位置: 40-60分
- >70%位置: 0-40分（高估区）

### 行业趋势 (_calc_industry_trend_score) — v2 updated 2026-07-06

Combines 60% theme heat + 40% NAV momentum:
- **Theme heat (0-60pts)**: `max(theme_heat.get(t, 0)) * 0.6`, default 30 if no themes
- **NAV momentum (0-40pts)**: `(MA5 - MA10) / MA10 * 100 * 4 + 20`, clamped [0, 40]
- If theme_heat lookup fails → returns theme_score=30 (neutral) + momentum from DB
- **Before fix**: returned 0 when theme not in hot list → 7/9 funds scored 0
- **After fix**: momentum provides differentiation even without theme data

### 主线匹配 (_calc_mainline_score) — v2 updated 2026-07-06

Tiered mapping instead of raw theme score:
- Hot themes (score≥50): `min(100, score + 20)` — bonus for being on-market-line
- Moderate (20-50): raw score
- Cold (<30): `max(15, score)` — floor at 15, never 0
- No themes mapped: returns 30
- theme_heat empty/failed: returns 40 (was 50, caused flat scoring)

### 净值趋势 (_calc_nav_trend_score)
- MA5 > MA20: +20分
- 价格 > MA5: +15分
- 近5天涨>3%: +10分

## 性能优化

`analyze_all()` 方法预加载主线数据（1次API调用），然后传给每只基金的分析函数，避免N次重复请求。
