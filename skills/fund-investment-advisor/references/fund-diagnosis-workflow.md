# Individual Fund Diagnosis Workflow

When user asks "what should I do with fund X" or "should I sell/hold/add", follow this structured analysis:

## Step 1: Position Data

```sql
SELECT fund_code, fund_name, share_count, avg_cost,
       (SELECT unit_nav FROM fund_nav_history WHERE fund_code=? ORDER BY nav_date DESC LIMIT 1) as latest_nav
FROM holdings WHERE fund_code=?
```

Calculate:
- Market value = share_count × latest_nav
- Cost basis = share_count × avg_cost
- P&L = market_value - cost_basis
- P&L% = (latest_nav - avg_cost) / avg_cost × 100
- Portfolio weight = market_value / total_portfolio_value

## Step 2: Multi-Period Returns

```sql
-- Query NAV at different lookback dates
SELECT unit_nav FROM fund_nav_history 
WHERE fund_code=? AND nav_date >= date('now', '-30 days') ORDER BY nav_date LIMIT 1
```

Show: near 1 month, 3 months, 6 months, 1 year returns.

**Key signal**: If 1-month return is dramatically worse than 3-month (e.g., -12% vs -14%), the fund is in **accelerated decline** — different treatment than gradual decline.

## Step 3: Historical Percentile

```sql
SELECT MIN(unit_nav), MAX(unit_nav) FROM fund_nav_history WHERE fund_code=?
```

Position = (current - min) / (max - min) × 100%
- < 20%: near historical low (potential value)
- 20-50%: below average
- 50-80%: above average  
- > 80%: near historical high (consider taking profit)

## Step 4: Holdings Analysis

Query `fund_holdings_cache` for top holdings and industry allocation.
Identify: sector concentration, cyclical vs growth, single-stock risk.

## Step 5: Action Scenarios

Always present 3 options in a table:
| Option | Action | Reasoning |
|--------|--------|-----------|
| A. Hold | Do nothing | [context-specific] |
| B. Reduce | Sell half | [context-specific] |
| C. Exit | Sell all | [context-specific] |

Then give your **recommendation** with clear reasoning.

## Decision Framework

| Condition | Recommendation |
|-----------|---------------|
| P&L% > -5%, weight < 15% | Hold, normal fluctuation |
| P&L% -5% to -15%, cyclical sector | Hold, wait for cycle turn |
| P&L% -5% to -15%, growth sector, fundamentals broken | Reduce or exit |
| P&L% < -15%, any sector | Evaluate if thesis still valid |
| Historical percentile < 20%, long-term thesis intact | Hold or add cautiously |
| Historical percentile > 80% | Consider partial profit-taking |

## Cyclical Fund Special Treatment

Cyclical funds (livestock, commodities, energy, materials):
- -10% to -15% drawdowns are **normal** during sector rotation
- Don't apply tight stop-losses (-8%)
- Use position sizing as risk control (< 15% of portfolio)
- Decision driver: **commodity price cycle**, not NAV price action
- Exit signal: cycle peak indicators, not percentage decline

## Output Format

User prefers code-block wrapped fixed-width tables for data. Use display_width() for Chinese character alignment. Show both % and absolute yuan amounts for P&L.


---

# Portfolio-Wide Diagnosis (Multi-Fund + Today's Market)

When user asks for full portfolio review or combines "how about other positions today", do NOT analyze funds in isolation. Follow this composite workflow:

## Phase 1: Batch All-Fund Data Pull

Fetch ALL holdings in one query, then compute metrics programmatically:

```python
# SQL: get all holdings
SELECT fund_code, fund_name, share_count, avg_cost, current_value, total_invested, total_withdrawn
FROM holdings ORDER BY current_value DESC

# For each fund (loop):
#   Fetch latest 120 NAVs from fund_nav_history
#   Fetch latest today's NAV from akshare: fund_open_fund_info_em()
```

Compute per-fund:
- `weight% = value / total_value * 100`
- `pnl = value - total_invested + total_withdrawn`
- `pnl_pct = pnl / total_invested * 100`
- `ma60 = avg(last 60 NAVs)` / `ma120 = avg(last 120 NAVs)`
- `above_ma60 = latest_nav > ma60` / `above_ma120 = latest_nav > ma120`
- `range_pos = (latest - min) / (max - min) * 100` (0=bottom, 100=top)
- `r5 = 5-day return`, `r20 = 20-day return` from NAV history dates
- `volatility = annualized 30-day sigma * 100`

Also fetch today's real-time NAVs from akshare to get daily_change% for each fund.

## Phase 2: Scoring System (0-100)

Combine multiple factors into a single comparable score:

| Factor | +Points | -Points |
|--------|---------|---------|
| PnL% > +50% | +15 | — |
| PnL% > +10% | +10 | — |
| PnL% > 0% | +5 | — |
| PnL% < -20% | — | -15 |
| PnL% < -10% | — | -10 |
| PnL% < 0% | — | -5 |
| Above 60MA | +5 | -5 (below) |
| Above 120MA | +5 | -5 (below) |
| 5-day > +3% | +5 | -5 (< -5%) |
| 20-day > 0% | +5 | -5 (< -10%) |
| Range < 30% (near bottom) | +5 | -5 (> 80%, near top) |

Base = 50. Score = max(0, min(100, 50 + sum)). Low score = problem fund.

## Phase 3: Cross-Fund Comparison Table

Output a single table with ALL funds sorted by weight descending:

```
代码     名称          权重    净值   成本     日涨    5日    20日    盈亏%    MA60  区间%  评分
```

Add visual markers: `◀◀` for funds being discussed, color-coded range.

## Phase 4: Problem Diagnosis

After the table, identify **structural issues** as numbered points:

```
问题1: 通信/光模块严重过度集中
  002112(29%) + 501205(14%) + 020692(4%) = 47%
  近5日全在暴跌(-12%~-14%)，高度同涨同跌

问题2: 005165富荣福锦暴跌
  今日-8.47%，亏损-61%，评分最低(25)
  是组合最大拖累
```

## Phase 5: Per-Fund Recommendation Table

Every fund gets one row with: `建议 | 理由 | 份额操作`

```
                    建议             理由
002112 德邦鑫星     止盈减仓         +235%但近20日跌11%，
  29.0%权重        卖1000份          回调刚开始，高位巨震

005165 富荣福锦     止损清仓         -61%，今日再跌-8.47%
  5.8%权重                          机器人板块整体走弱
```

## Phase 6: Operation Priority (P0/P1/P2)

```
优先级   操作           预计回笼
P0      005165清仓      +1,074元
P1      002112减仓      +5,437元
P2      014028加仓      -158元
──────────────────────
净回笼                  +6,353元
```

## Phase 7: Before/After Portfolio Projection

Show what the portfolio looks like after proposed changes:

```
          调仓前              调仓后
总价值     17,472             17,472 (不变)
通信集中度  47%               34% (降13%)
亏损基金数  6只               4只 (减2只)
组合质量   +7.88%             ~+12% (预估)
```

## Phase 8: Concise Summary

```
立即执行：
  → 005165 全部清仓
  → 002112 减仓1000份

持有不动：
  → 014414畜牧（等周期反转）
  → 020692通信/027063创新（趋势未破）

已操作：
  → 018388港股红利 已减半，等1.30再减
```

## Special: Combining with "Today's Market" Context

When user asks "结合今天的市场..." specifically:

1. Fetch all today's NAVs from akshare (daily return)
2. Fetch sector performance data (top/bottom 5 industries today)
3. Correlate each fund's sector with today's hot/cold sectors
4. Identify which positions are: (a) outperforming the market → hold/add, (b) underperforming in a good sector → investigate, (c) in the worst sectors → reduce

**Key signal**: A fund that's up today while most are down is showing relative strength — consider adding. A fund that's down -8% in a single day (like 005165 at -8.47%) is alarming — consider emergency stop-loss regardless of PnL%.
