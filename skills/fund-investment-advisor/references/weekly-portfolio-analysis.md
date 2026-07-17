# Weekly Portfolio-Level Analysis (周度组合级分析补充)

**Created**: 2026-07-05

The built-in `weekly_review.py` does per-fund analysis only (weekly return,
volatility, max drawdown, win rate). It does NOT compute portfolio-level
metrics that are critical for weekly review:

1. **Portfolio weekly P&L** — total week profit/loss in ¥ and %
2. **Effective industry exposure** — cross-fund weighted industry allocation
3. **Position concentration** — check vs risk profile limits (20%/30%)
4. **Cross-fund industry overlap** — detect hidden concentration

## When to Use

Run `weekly_portfolio_analysis.py` AFTER `weekly_review.py` to get the
complete picture. The built-in script answers "which funds did well/badly?";
this supplement answers "how did the PORTFOLIO as a whole do, and where are
the hidden risks?"

## Script

`scripts/weekly_portfolio_analysis.py` — runnable directly:

```bash
cd ~/.hermes/fund-advisor
python3 scripts/weekly_portfolio_analysis.py
# Or with custom week start:
python3 scripts/weekly_portfolio_analysis.py --week-start 2026-06-26
```

## Key Metrics Computed

### 1. Portfolio Weekly P&L

```
总市值: ¥27,476
总成本: ¥25,538
总盈亏: +¥1,938 (+7.6%)
本周盈亏: -¥1,465 (-5.06%)  ← KEY METRIC not in built-in report
```

### 2. Position Concentration

Checks each fund's portfolio weight against:
- 🔴 >30%: exceeds balanced profile limit — immediate action
- 🟡 >20%: exceeds conservative profile limit — warning
- ✅ ≤20%: within limits

### 3. Industry Exposure (Weighted)

This is the most important missing analysis. Example from 2026-07-05:

```
行业暴露（按组合权重加权）:
  半导体          17.7%  🟡 超配
  通信            14.5%
  畜牧养殖        11.5%
  电子             8.9%
  互联网           5.8%
  ──────────────────────
  科技相关合计:    46.9%  🔴 严重集中
```

**How to build the `industry_map`**: Query fund holdings via the EastMoney
API (used in `advisor.py holdings`), or fall back to name-based inference
(see `references/industry-data.md`). The map structure is:

```python
industry_map = {
    '002112': [('通信', 32.8), ('电子', 28.4)],
    '005165': [('电子', 37.1), ('电力设备', 13.8)],
    # ... one entry per fund
}

# Then weight by portfolio position:
for code, industries in industry_map.items():
    weight = fund_value / total_value * 100
    for ind, pct in industries:
        industry_exposure[ind] += weight * pct / 100
```

## Findings from 2026-07-05 Session

Key problems identified by portfolio-level analysis that the built-in
`weekly_review.py` missed:

1. **Hidden tech concentration**: 46.9% of the portfolio was exposed to
   tech/semiconductor/telecom across 6 different funds. No single fund
   looked extreme, but the AGGREGATE exposure was dangerously high. This
   only surfaces when you weight industry allocations by portfolio position.

2. **Profit giveback**: High-profit funds (002112 +60%, 020692 +84%) had
   large weekly drawdowns (-11% and -10%) that eroded significant unrealized
   gains. The adaptive risk engine gave them mid-range scores because the
   "盈亏" (profit/loss) factor scored high profit as low risk — but at
   extreme profit levels, the risk of giveback is actually HIGH.

3. **Concentration risk**: 022184 at 34.6% portfolio weight — the single
   largest risk. A -6.7% week on this fund alone cost -2.3% of the entire
   portfolio.

## Limitations

- Industry exposure section requires manually populating `industry_map`
  from the holdings API output. Future enhancement: auto-fetch and cache.
- Does not calculate Sharpe ratio or benchmark alpha — use `backtest_main.py`
  for those metrics.
