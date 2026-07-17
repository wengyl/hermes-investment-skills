# Personalized Strategy Recommendations

**Added**: 2026-05-21
**Purpose**: Generate per-fund action recommendations based on market data and portfolio status

---

## Overview

The personalized strategy recommendation system analyzes each fund in the user's portfolio and provides specific action recommendations (add position, hold, reduce, take profit, etc.) plus **concrete share/amount suggestions** based on three key dimensions:

1. **Industry Match** - Does the fund's holdings align with hot/cold sectors?
2. **Relative Strength** - Is the fund outperforming or underperforming the market?
3. **Profit/Loss Status** - What is the current P&L situation?

The system uses a **multi-strategy scoring engine** (value, trend, DCA, risk, allocation) that independently scores each action type, then picks the highest-scoring action. A **Decision Arbiter** can veto "add position" recommendations that conflict with higher-priority risk constraints.

---

## Implementation

### Core Function

Located in `scripts/advisor.py`:

```python
def generate_personalized_strategies(self, market: Dict) -> str:
    """
    Generate personalized strategy recommendations
    Based on: industry match, relative strength, profit/loss status
    """
```

### Three-Dimensional Analysis

#### 1. Industry Match Analysis

**Data Source**: Capital flow data from `market['capital_flow']['industries']`

**Logic**:
```python
# Build industry hotness mapping
hot_industries = {}  # industry_name -> net_inflow_ratio
for ind in industries:
    hot_industries[ind['name']] = ind['net_inflow_ratio']

# Check fund's industry allocation
fund_industries = list(industry_data[code].keys())

# Match against hot/cold sectors
matched_hot = [ind for ind in fund_industries 
               if ind in hot_industries and hot_industries[ind] > 20]
matched_cold = [ind for ind in fund_industries 
                if ind in hot_industries and hot_industries[ind] < -20]

if matched_hot:
    industry_match = "🔥 受益热点"  # Benefiting from hot sectors
elif matched_cold:
    industry_match = "❄️ 受冷行业"  # Affected by cold sectors
else:
    industry_match = "中性"  # Neutral
```

**Thresholds**:
- **Hot sector**: Net inflow ratio > +20%
- **Cold sector**: Net inflow ratio < -20%
- **Neutral**: Between -20% and +20%

#### 2. Relative Strength Analysis

**Calculation**:
```python
# Calculate market average return
market_avg_return = 0
if market.get('a_shares'):
    returns = [d.get('change_pct', 0) * 100 
               for d in market['a_shares'].values() 
               if 'price' in d]
    if returns:
        market_avg_return = sum(returns) / len(returns)

# Compare fund return to market average
if daily_return_pct > market_avg_return + 0.3:
    relative_strength = "📈 强于大盘"  # Stronger than market
elif daily_return_pct < market_avg_return - 0.3:
    relative_strength = "📉 弱于大盘"  # Weaker than market
else:
    relative_strength = "持平"  # Similar to market
```

**Thresholds**:
- **Strong**: Fund return > Market average + 0.3%
- **Weak**: Fund return < Market average - 0.3%
- **Neutral**: Within ±0.3% of market average

#### 3. Profit/Loss Status

**Calculation**:
```python
value = current if current else shares * cost
cost_value = shares * cost
profit = value - cost_value
profit_rate = (profit / cost_value * 100) if cost_value > 0 else 0
```

**Categories**:
- **High profit**: profit_rate > +20%
- **High loss**: profit_rate < -10%
- **Normal**: Between -10% and +20%

---

## Decision Logic

The system uses a **multi-strategy scoring engine** (not a simple decision tree). Each strategy independently evaluates the fund and votes on action types:

### Scoring Strategy Dimensions

| Dimension | Focus | Scoring |
|-----------|-------|---------|
| **价值投资 (Value)** | Valuation percentiles, P&L status | Low valuation (PB < 20%) → score for 加仓 |
| **趋势投资 (Trend)** | Capital flow, relative strength | Inflow + strong → score for 加仓 |
| **定投策略 (DCA)** | Holding time, cost advantage | Long holding + avg cost → score for 持有观望 |
| **风险管理 (Risk)** | Drawdown, concentration | Large drawdown → score for 减仓/止损 |
| **资产配置 (Allocation)** | Industry concentration | Over-concentrated → score for 减仓 |

### Final Action Selection

```python
# Each action accumulates scores from all strategies
action_scores = {"加仓": 0, "减仓": 0, "持有观望": 0}

# P1-3: Thresholds tuned to reduce daily noise false-positives
total_scores = sum(action_scores.values())
if total_scores == 0:
    final_action = "持有观望"
else:
    max_score = max(action_scores.values())
    if action_scores["加仓"] == max_score and action_scores["加仓"] >= 3:
        final_action = "可加仓"
    elif action_scores["减仓"] == max_score and action_scores["减仓"] >= 2:
        if profit_rate > 10:
            final_action = "止盈减仓"
        else:
            final_action = "考虑减仓"
    else:
        final_action = "持有观望"
```

**Thresholds** (tuned P1-3 to reduce daily noise false-positives):
- **加仓**: Requires score ≥ 3
- **减仓**: Requires score ≥ 2
- **止盈**: profit_rate > 10% triggers 止盈减仓 label

### Concrete Position Sizing (_calc_concrete_action)

After determining `final_action`, the system calculates specific share/amount recommendations:

| Action | Profit/Loss | Operation | Formula |
|--------|-------------|-----------|---------|
| **止盈减仓** | profit > 50% | 卖出1/2 | `shares × 0.5` |
| **止盈减仓** | profit > 30% | 卖出1/3 | `shares / 3` |
| **止盈减仓** | profit > 10% | 卖出1/4 | `shares / 4` |
| **止盈减仓** | profit ≤ 10% | 卖出1/5 | `shares / 5` |
| **考虑减仓** | loss > 15% | 止损卖出1/3 | `shares / 3` |
| **考虑减仓** | loss > 5% | 卖出1/4 | `shares / 4` |
| **考虑减仓** | normal | 卖出1/5 | `shares / 5` |
| **可加仓** | loss > 10% | 加仓≈市值10% | `value × 0.10` |
| **可加仓** | normal | 加仓≈市值5% | `value × 0.05` |
| **可加仓** | no value | 新建仓500-1000元 | Fixed range |
| **持有观望** | value < 100元 | 清仓(碎片仓位) | All |
| **持有观望** | normal | 持有不动 | — |

Implementation in `scripts/advisor.py`:
```python
def _calc_concrete_action(self, action, shares, cost, value, profit_rate):
    """Returns string like '卖出466份≈2531元(1/2)' or '持有不动'"""
```

### Decision Arbiter (P0-1 Arbitration)

After generating initial actions, a **DecisionArbiter** batch-processes all "可加仓" proposals and can veto them if higher-priority risk conditions are met (e.g., market-wide risk level is elevated, the fund has been repeatedly flagged):

```python
from decision_arbiter import DecisionArbiter
arbiter = DecisionArbiter(self.db_path)
proposed_actions = {r['code']: r['final_action'] for r in pending_rows}
arbitrated = arbiter.batch_arbitrate(proposed_actions)
```

When vetoed, the action is downgraded (e.g., 可加仓 → 考虑减仓) and `_calc_concrete_action` is **re-run** with the new action so the concrete amount stays consistent.

---

## Output Format

### Table Format (Current — with Concrete Actions)

```text
基金代码    基金名称            策略视角                  依据                                           建议  具体操作
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
002112  德邦鑫星价值灵活配置混合C   动量 + 盈亏止盈             超大盘7.5%；盈利54.2%                            止盈减仓  卖出466份≈2531元(1/2)
005165  富荣福锦混合C         趋势 + 风控               重仓汽车零部件；超大盘1.8%；亏损15.4%                     可加仓  加仓≈101元(补仓10%)
012922  易方达全球成长精选混合(QD..动量                    超大盘1.6%                                    持有观望  清仓(碎片仓位≈20元)
014414  招商中证畜牧养殖ETF联接A  动量                    超大盘1.1%                                    持有观望  持有不动
017731  嘉实全球产业升级股票发起式(..动量                    超大盘1.6%                                    持有观望  持有不动
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
```

### Column Specifications

| Column | Width | Description |
|--------|-------|-------------|
| **基金代码** | 8 | Fund code |
| **基金名称** | 16 | Fund name (truncated if long) |
| **策略视角** | 22 | Strategy dimension(s) triggered |
| **依据** | 35 | Evidence/reasoning (short format) |
| **建议** | 12 | Action recommendation (right-aligned) |
| **具体操作** | 28 | Concrete share count + amount + reason |

### Column Widths (Python constants)

```python
COL_CODE = 8
COL_NAME = 16
COL_STRATEGY = 22
COL_REASON = 35
COL_ACTION = 12
COL_CONCRETE = 28  # Added 2026-07-10
```

### Strategy Perspectives

Each fund's analysis shows which strategy dimensions triggered:

| Perspective | Icon | When Triggered |
|------------|------|----------------|
| **价值投资** | 价值 | Valuation percentile signals |
| **趋势投资** | 趋势 | Capital flow direction |
| **动量** | 动量 | Relative strength (超大盘) |
| **盈亏止盈** | 盈亏止盈 | profit_rate exceeds threshold |
| **定投** | 定投 | Holding time / cost advantage |
| **配置** | 配置 | Industry concentration risk |
| **风控** | 风控 | Drawdown or loss severity |
| **DCA** | DCA | DCA schedule active |

### Analysis Components

The **依据** column shows key evidence, separated by `；`:

1. **Relative vs market**: "超大盘X.X%" (outperforming) or "弱大盘X.X%" (underperforming)
2. **Profit/Loss**: "盈利X.X%" or "亏损X.X%"
3. **Industry signals**: "重仓XX行业", "资金流入/流出"
4. **Risk signals**: "行业集中"(concentrated)

---

## Recommendation Types (Current 4-Action System)

| Action | Meaning | Concrete Sizing |
|--------|---------|-----------------|
| **止盈减仓** | Take profit — reduce position | 1/2 (profit>50%), 1/3 (profit>30%), 1/4 (profit>10%), 1/5 (otherwise) |
| **考虑减仓** | Consider reducing / stop-loss | 1/3 (loss>15%), 1/4 (loss>5%), 1/5 (otherwise) |
| **可加仓** | Add position | 10% of value (loss>10%), 5% of value (normal), 500-1000元 (new) |
| **持有观望** | Hold & observe | 持有不动; 清仓 if value < 100元 (fragment cleanup) |

### Old Recommendation Types (Legacy — replaced by scoring engine)

~~可加仓, 持有观望, 持有待涨, 考虑减仓, 谨慎持有, 止盈或部分减仓, 考虑止损~~

---

## Integration Points

All three report generators (`morning`, `afternoon`, `evening`) call `generate_personalized_strategies()` and append the full table (including the `具体操作` column) to the report output. Example:

```python
# In any report generator:
report.append("\n【🎯 盘后策略建议】")
strategy_report = self.generate_personalized_strategies(market)
report.append(strategy_report)
```

---

## Data Requirements

### Required Data

1. **Fund holdings**: From `holdings` table
2. **Fund NAV history**: From `fund_nav_history` table (for daily return)
3. **Industry allocation**: From `fetcher.get_fund_holdings(code, name)`
4. **Capital flow**: From `market['capital_flow']['industries']`
5. **Market indices**: From `market['a_shares']` (for average calculation)

### Fallback Strategies

**If industry allocation unavailable**:
- Use name-based inference (existing in `data_fetcher.py`)
- Mark as "其他" (Other) with 100% allocation
- Skip industry match analysis, rely on relative strength and P&L

**If capital flow unavailable**:
- Skip industry match analysis
- Rely on relative strength and P&L only
- Show warning: "⚠️ 行业资金流向数据获取失败，使用模拟数据演示格式"

**If NAV data unavailable**:
- Use last known NAV
- Calculate daily return from NAV changes if available
- Show 0.00% if no data

---

## Testing

### Manual Test

```bash
cd ~/.hermes/fund-advisor
python scripts/advisor.py morning  # Check morning strategies
python scripts/advisor.py afternoon  # Check afternoon strategies
python scripts/advisor.py evening  # Check evening strategies
```

### Expected Output

Look for the `【🎯 个性化策略建议】` or `【🎯 开盘前策略建议】` or `【🎯 盘后策略建议】` section with:
- Table of all funds with analysis and recommendations
- Legend explaining the recommendation types
- Proper alignment and formatting

---

## Future Enhancements

### Potential Improvements

1. **Machine Learning**: Train model on historical data to predict sector rotation
2. **Risk Adjustment**: Factor in fund volatility and beta
3. **Correlation Analysis**: Consider fund correlations for diversification
4. **News Sentiment**: Incorporate news sentiment analysis
5. **Technical Indicators**: Add RSI, MACD, moving averages
6. **User Preferences**: Allow users to set risk tolerance and investment horizon
7. **Time Horizon**: Differentiate between short-term and long-term recommendations

### Advanced Features

1. **Portfolio Optimization**: Suggest overall portfolio rebalancing
2. **Scenario Analysis**: Show recommendations under different market scenarios
3. **Backtesting**: Test recommendation accuracy historically
4. **Confidence Scores**: Show confidence level for each recommendation
5. **Explainability**: Provide detailed reasoning for each recommendation

---

## References

- `scripts/advisor.py`: Main implementation (`generate_personalized_strategies`, `_calc_concrete_action`)
- `scripts/decision_arbiter.py`: Batch arbitration (vetoes "可加仓" under risk conditions)
- `scripts/data_fetcher.py`: Industry allocation and capital flow data
- `references/industry-data.md`: Industry data API patterns
- `references/code-block-formatting.md`: Table formatting standards
- `references/briefing-audit-fixes.md`: Fixes from audit (threshold tuning, etc.)

---

## Version History

**1.2.0** (2026-07-10)
- Concrete position sizing implemented: `_calc_concrete_action` computes share counts and amounts per fund
- Output format updated: new `具体操作` column (28 chars wide) added to strategy table
- Decision arbiter integration: re-runs concrete action calculation after arbitration veto
- Multi-strategy scoring engine replaces old decision tree
- Recommendation types simplified to 4 actions: 止盈减仓, 考虑减仓, 可加仓, 持有观望
- Strategy perspectives added (动量, 趋势, 价值, 盈亏止盈, 风控, 配置, 定投)
- P1-3 threshold tuning: 加仓 threshold raised from 2→3 to reduce daily noise false-positives

**1.1.0** (2026-06-xx)
- Decision arbiter integration (batch veto for "可加仓")
- Multi-strategy scoring engine (value, trend, DCA, risk, allocation)

**1.0.0** (2026-05-21)
- Initial implementation
- Three-dimensional analysis (industry, strength, P&L)
- 7 recommendation types
- Integration into morning/afternoon/evening reports
