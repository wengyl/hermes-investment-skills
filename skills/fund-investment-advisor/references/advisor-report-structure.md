# Advisor.py Report Structure

## Morning Report (`advisor.py morning`)

Sections in order (updated 2026-07-11v2):
1. 【🌍 全球市场】 — US stocks (Sina), HK stocks (Sina), USD/CNY (Sina), COMEX Gold (Sina)
2. 【📈 A 股指数】 — A-share indices with change %
3. 【🚀 北向资金】 — Northbound flow: 沪股通/深股通/合计 (East Money kamt.kline)
4. 【💰 主力资金流向】 — Capital flow by industry (code block table, East Money clist)
5. 【🎯 概念板块资金流向】 — Concept board capital flow Top5 (East Money clist m:90+t:3)
6. 【🔥 个股资金流向 Top5】 — Stock capital flow Top5 (East Money clist)
7. 【📐 指数估值(PE)】 — Major index PE/TTM + historical percentile (akshare stock_index_pe_lg)
8. 【📐 持仓基金PE估值】 — Fund-level PE via weighted holdings (akshare fund_portfolio_hold_em → stock_individual_valuation_baidu / stock_hk_valuation_baidu)
9. 【🌡️ 市场情绪】 — Sentiment score + up/down count
9. 【🧭 市场主线】 — Market mainline themes (code block table)
9. 【💼 持仓概览】 — Holdings summary (code block table)
10. 【🏭 行业配置】 — Industry allocation (code block table)
11. 【🛡️ 智能风控】 — Multi-factor risk signals (adaptive_risk_v2)
12. 【📊 场外基金操作建议】 — OOF strategy advice (移动止盈/配置/定投)
13. 【📈 均线策略信号】 — MA crossover signals (OptimizedMAStrategy)
14. 【💡 今日建议】 — Action advice
15. 【⚠️ 风险提示】 — Disclaimer

## Data Source Routing (2026-07-06)

| Data | Source | API | Status |
|------|--------|-----|--------|
| A股指数 | tencent | `qt.gtimg.cn` | ✅ Primary |
| 美股指数 | Sina | `hq.sinajs.cn/list=gb_dji,gb_ixic,gb_inx` | ✅ |
| 港股恒生 | Sina | `hq.sinajs.cn/list=rt_hkHSI` | ✅ |
| USD/CNY | Sina | `hq.sinajs.cn/list=USDCNY` | ✅ |
| COMEX黄金 | Sina | `hq.sinajs.cn/list=hf_GC` | ✅ |
| 北向资金 | East Money | `push2.eastmoney.com/api/qt/kamt.kline/get` | ✅ |
| 行业资金流向 | East Money | `push2.eastmoney.com/api/qt/clist/get?fs=m:90+t:2` | ✅ |
| 概念资金流向 | East Money | `push2.eastmoney.com/api/qt/clist/get?fs=m:90+t:3` | ✅ |
| 个股资金流向 | East Money | `push2.eastmoney.com/api/qt/clist/get?fs=m:0+t:6,...` | ✅ |
| ~~美股~~ | ~~Yahoo Finance~~ | ~~`query1.finance.yahoo.com`~~ | ❌ Dead |
| ~~港股/汇率/国债~~ | ~~East Money stock/get~~ | ~~`push2.eastmoney.com/api/qt/stock/get`~~ | ❌ Unstable |

### ⚠️ Sina API encoding pitfall

Sina returns **GBK** encoded data. When using `subprocess.run(['curl', ...])`:
- Do NOT use `text=True` (defaults to UTF-8, causes `'utf-8' codec can't decode` error)
- Use `capture_output=True` then manually decode: `proc.stdout.decode('gbk', errors='replace')`
- Always pass header: `-H 'Referer: https://finance.sina.com.cn'`

## Evening Report (`advisor.py evening`)

As of 2026-07-11v2, evening report uses the **same global market data** as morning via `_format_global_market()`:
- 【📊 今日复盘】 — calls `_format_global_market(market)` → shows US/HK/A-shares/northbound/capital flow/concepts/stocks
- 【📐 指数估值(PE)】 — Major index PE/TTM + historical percentile (akshare stock_index_pe_lg)
- 【📐 持仓基金PE估值】 — Fund-level PE via weighted holdings (akshare fund_portfolio_hold_em → stock_individual_valuation_baidu / stock_hk_valuation_baidu)
- 【🌡️ 市场情绪】 — Sentiment score
- 【🧭 市场主线】 — Market mainline themes
- 【💼 持仓更新】 — Holdings summary
- 【📈 历史收益对比】 — 1W/1M/3M returns + max drawdown
- 【🎯 盘后策略建议】 — Strategy advice table
- 均线策略信号 section

## Afternoon Report (`advisor.py afternoon`)

As of 2026-07-11v2, afternoon report also uses `_format_global_market()`:
- 【⏰ 下午开盘提醒】 — Fixed text reminders
- 【📈 市场概况】 — calls `_format_global_market(market)` → full global market data
- 【📐 指数估值(PE)】 — Major index PE/TTM + historical percentile (akshare stock_index_pe_lg)
- 【📐 持仓基金PE估值】 — Fund-level PE via weighted holdings (akshare fund_portfolio_hold_em → stock_individual_valuation_baidu / stock_hk_valuation_baidu)
- 【🔮 全天走势预测】 — Fixed text
- 【💼 持仓表现】 — Holdings
- 【🎯 个性化策略建议】 — Strategy
- 【💡 尾盘操作建议】 — Fixed text

## `_format_global_market()` — Reusable Market Data Block

Extracted from morning report on 2026-07-06. All three reports (morning/afternoon/evening) call this method to display the same set of market data:

```python
def _format_global_market(self, market: Dict) -> list:
    """Returns list of formatted strings for:
    - US stocks (Sina gb_dji/ixic/inx)
    - HK stocks (Sina rt_hkHSI)
    - USD/CNY (Sina USDCNY)
    - COMEX Gold (Sina hf_GC)
    - A-share indices (tencent)
    - Northbound flow (East Money kamt.kline)
    - Industry capital flow (East Money clist m:90+t:2)
    - Concept board capital flow Top5 (East Money clist m:90+t:3)
    - Stock capital flow Top5 (East Money clist)
    """
```

**Pattern**: Never duplicate market data formatting across reports. Always extend `_format_global_market()` and all three reports get the new data automatically.

## 均线策略信号 Integration

```python
# In generate_morning_report():
try:
    from oof_strategy_advisor import get_ma_signals
    ma_signals = get_ma_signals(self.db_path)
    if ma_signals and "暂无" not in ma_signals:
        report.append("\n【📈 均线策略信号】")
        report.append(ma_signals)
except Exception as e:
    pass  # Don't break main report if MA signals fail
```

**get_ma_signals()** in `oof_strategy_advisor.py`:
- Runs 60-day lookback backtest with OptimizedMAStrategy
- Returns last 5 trades with emoji indicators
- Returns "📭 暂无均线信号" if no recent trades

## Cron Jobs (Agent Mode)

```
08:30  advisor.py morning     — 开盘前简报
10:30  morning_intraday.py    — 盘中上午
14:00  afternoon_intraday.py  — 盘中下午
16:30  advisor.py evening     — 盘后总结
```

All cron jobs MUST use agent mode (no_agent=false) — Feishu truncates >2800 chars.

## Index PE Section (`_get_index_pe_summary()`)

Added 2026-07-11, called directly in each report generation method (NOT through `_format_global_market()` — PE data comes from akshare, not the same curl/Sina/East Money APIs).

### How it's called in each report

**Morning/Afternoon/Evening**: called directly after `_format_global_market()` output:
```python
report.append("\n【📐 指数估值(PE)】")
report.append(self._get_index_pe_summary())
```

**Weekly**: called in `weekly_review.py` `WeeklyReviewer.print_weekly_report()`:
```python
print("\n【📐 指数估值(PE)】")
review.advisor._get_index_pe_summary()  # displayed inline
```

### Output format (code block table)
```text
指数      风格         PE(TTM)    百分位      估值
──────────────────────────────────────────────────
沪深300   大盘价值        13.6     64.4%     🟡偏高
中证500   中盘成长        32.0     67.6%     🟡偏高
上证50    超大盘          11.3     58.2%     🟢合理
中证100   宽基            16.7     83.1%     🔴高估
──────────────────────────────────────────────────
  百分位=当前PE在历史中的分位，>80%高估，<20%低估
```

### Layout pattern
Unlike `_format_global_market()` which is reused identically in all 3 reports, `_get_index_pe_summary()` returns a single code block string. No list/join wrapping needed. Each report individually appends it in its own section order.

### Data source
akshare `stock_index_pe_lg()` — see `references/akshare-api-notes.md` for full API reference.

## Fund PE Section (`_get_fund_pe_summary()`)

Added 2026-07-11. Computes fund-level PE(TTM) by weighting each holding stock's individual PE (using `ak.share.stock_individual_valuation_baidu` for A-shares, `ak.stock_hk_valuation_baidu` for HK stocks). ETF-linked funds (without stock holdings) show N/A.

### How it's called in each report

Same pattern as index PE — called individually in each report method, NOT through `_format_global_market()`:

**Morning/Afternoon/Evening**: called directly after index PE:
```python
# 3.6 / 2.6 / 1.6 持仓基金PE
fund_pe_report = self._get_fund_pe_summary()
if fund_pe_report:
    report.append(f"\n{fund_pe_report}")
```

**Weekly**: in `weekly_review.py` `WeeklyReviewer.print_weekly_report()`:
```python
fund_pe_report = _adv._get_fund_pe_summary()
if fund_pe_report:
    print(f"\n{fund_pe_report}")
```

### Output format (code block table)
```text
代码      基金名称           PE(TTM)  覆盖仓位      估值
────────────────────────────────────────────────────────
002112    德邦鑫星             240.6       58%     🔴极高
005165    富荣福锦             110.9       51%     🔴极高
014414    招商畜牧               N/A         —         —
017731    嘉实全球产业          22.9        6%     🟢合理
018388    华泰港股红利           N/A         —         —
020692    博时通信              60.8       55%     🔴极高
025687    国泰半导体           186.7       63%     🔴极高
027063    鹏华创新驱动           N/A         —         —
257070    国联安优选           167.6       40%     🔴极高
501205    鹏华创新未来         124.7       40%     🔴极高
────────────────────────────────────────────────────────
  PE=持仓股加权市盈率(TTM)，覆盖仓位=top10权重占比
  判断线: <20低估 20-35合理 35-50偏高 >50极高
```

### Valuation thresholds
Unlike index PE (percentile-based), fund PE uses absolute thresholds:
| PE Range | Label |
|----------|-------|
| < 20 | 🟢低估 |
| 20–35 | 🟢合理 |
| 35–50 | 🟡偏高 |
| ≥ 50 | 🔴极高 |

### Data source
See `references/akshare-api-notes.md` → "Fund-Level PE from Holdings" for full API reference and pitfalls.
