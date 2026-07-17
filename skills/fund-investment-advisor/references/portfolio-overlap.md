# Portfolio Overlap Analysis

## Purpose

Detect when multiple funds in the portfolio hold the same stocks, causing unintended concentration risk.

## Method

1. Fetch top 10 holdings for each fund via `ak.fund_portfolio_hold_em(symbol=code, date="2025")`
2. Build stock→fund mapping
3. Find stocks appearing in 2+ funds
4. Compute pairwise overlap matrix
5. Classify by sector and identify concentration

## AKShare API: fund_portfolio_hold_em

```python
import akshare as ak
df = ak.fund_portfolio_hold_em(symbol="020692", date="2025")
# Returns columns: 季度, 股票代码, 股票名称, 占净值比例, 持股数(万股), 持仓市值(万元)
# Latest quarter first
latest_date = df['季度'].iloc[0]
top10 = df[df['季度'] == latest_date][['股票名称', '占净值比例']].head(10)
```

### Pitfalls

1. **ETF联接基金 return empty data** — Funds like 014414 (畜牧ETF联接), 018388 (港股红利ETF联接) track an index and don't disclose individual stock holdings. Skip these in overlap analysis; classify them by their target index instead.

2. **Date parameter format** — Use year string like `"2025"`, not full date. The API returns all quarters for that year.

3. **Data freshness** — Holdings data lags by 1-3 months (quarterly disclosure). Note the reporting quarter in the analysis.

4. **Non-existent fund code** — Some codes may return no data. Wrap in try/except.

## Sector Classification (for overlap analysis)

Group stocks into sectors to detect thematic concentration:

```python
sectors = {
    '光通信/光模块': ['中际旭创', '新易盛', '太辰光', '天孚通信', '光库科技', '博创科技', '仕佳光子', '源杰科技', '致尚科技'],
    'AI/芯片': ['寒武纪', '中芯国际', '恒玄科技', '中科蓝讯', '英伟达', '台积电'],
    '通信设备': ['中兴通讯', '中天科技', '亨通光电', '信维通信', '移远通信'],
    'PCB/电子': ['胜宏科技', '景旺电子', '工业富联', '东山精密'],
    # Add more as portfolio evolves
}
```

## Finding: Portfolio Concentration (2026-06-03)

9 funds analyzed, 6 had individual stock data:

- **新易盛** appeared in 3 funds (博时通信, 平安科技, 德邦鑫星)
- **光通信/光模块** sector: 82.4% total exposure across 13 overlapping positions
- **Overlap rate**: 4/15 fund pairs (27%) share common holdings
- **Worst overlap**: 博时通信设备 ↔ 平安科技精选 (2 stocks: 新易盛, 中际旭创)

## Recommended Holdings (精简 from 9 to 6)

| Keep | Sector | Rationale |
|------|--------|-----------|
| 022184 富国全球科技 | 海外科技 | No overlap, covers US/HK tech |
| 005165 富荣福锦 | 机床智造 | No overlap, independent sector |
| 014414 招商畜牧 | 畜牧养殖 | ETF联接, independent |
| 018388 华泰港股红利 | 港股红利 | ETF联接, independent |
| 020692 博时通信设备 | 光通信 | Keep 1 light comm representative |
| 002112 德邦鑫星 | 光通信+AI | OR keep this, drop 博时 (higher alpha) |

**Candidates to sell**: 026211平安科技 (overlaps with 博时), 501205鹏华创新未来, 027063鹏华创新驱动

## Frequency

Run quarterly or after any new fund purchase. Script can be automated via cron.
