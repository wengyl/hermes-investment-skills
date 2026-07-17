# 系统优化路线图

## P0 核心优化 ✅ (v1.3.0 - 2026-05-28)

### 1. 智能止盈止损引擎
- **问题**: 止盈逻辑过于简单（收益>80%就建议止盈），止损逻辑缺失
- **方案**: 分档止盈 + 移动止盈 + 硬止损 + 基金类型差异化
- **实现**: `smart_strategy.py` (12KB)

### 2. 数据源多源fallback+缓存
- **问题**: 东方财富push2 API被服务器屏蔽，数据获取失败
- **方案**: 多源fallback（腾讯→新浪）+ 内存/文件缓存 + 错误重试
- **实现**: `data_cache.py` (11KB)

## P1 体验优化 ✅

### 3. 报告精简+分级 / 4. 配置建议具体化 / 5. 历史对比 / 6. 市场情绪 / 7. 单元测试 / 8. 用户配置

## Round 2 Audit (2026-07-06) — All Fixed ✅

### P0 Fixes

1. **DCA didn't record transactions** — `dca_update.py` now writes to `transactions` table with dedup check.
2. **Strategy contradiction** — `_check_rebalance_needed()` skips funds with `action_level in ('sell', 'take_profit')`.
3. **Ghost fund 257070** — Deleted 3,636 orphan NAV records + removed from `FUND_THEME_MAP`.

### P1 Fixes

4. **Intraday/evening reports missing global data** — Extracted `_format_global_market()` reusable method, all 3 reports now show full global market data.
5. **NAV update gap** — Added 20:00 weekday cron for T-day NAV.
6. **Monthly evaluation cron: Broken pipe** — Switched to `no_agent=true` + script mode.
7. **018388 holdings always empty** — Fetch from corresponding ETF (513090) via `etf_map`. See `references/etf-linked-fund-holdings.md`.
8. **Risk scoring: near-zero differentiation** — Industry = 60% theme + 40% NAV momentum; mainline = tiered mapping.

### P2 Fixes

9. **Cleaned 44→33 scripts** — Removed 25 archive + 8 duplicate cron + 3 test + 3 old scripts.
10. **Backfilled 8 initial transactions** — All holdings now have transaction records.

## Round 3 Audit (2026-07-06) — All Fixed ✅

### P0 Fixes

11. **MA strategy signals misleading** — Signals were from backtest simulation, not actual positions. User saw "止损-9.57%" but actual PnL was -0.1%. **Fixed**: added "⚠️ 策略模拟信号，非实际持仓操作" label; stop-loss signals for funds with PnL > +30% auto-convert to "🎯 关注止盈" with actual PnL shown.

12. **No concentration analysis** — CR4=78% but no warnings. **Fixed**: added `_format_concentration_analysis()` method with CR4/CR8/HHI/主题集中度, active warnings for >30% single-fund and >50% theme concentration.

### P1 Fixes

13. **Risk action doesn't distinguish profit vs loss** — Low-score funds got "建议止损/止盈" regardless of PnL. **Fixed**: PnL > +30% → "建议止盈" (level=`take_profit`); PnL ≤ 0 → "建议止损/止盈" (level=`sell`).

14. **Generic daily suggestions** — "今日建议" was 3 static lines. **Fixed**: `_generate_personalized_suggestions()` generates 5-7 data-driven suggestions from risk results + market data + holdings.

15. **Rebalance skipped stop-loss funds entirely** — Funds flagged for stop-loss were excluded from risk-parity calculation. **Fixed**: all funds participate; stop-loss funds marked "🔴 优先处理" in suggestions.

16. **Non-trading hours showed 0.00亿** — Northbound data showed 0 on weekends/evenings. **Fixed**: auto-detects weekend/off-hours and labels "📋 以下为最近交易日数据（当前为周末休市/非交易时段）:".

### P2 Fixes

17. **HK stock industry classification** — `_classify_stock_industry()` didn't recognize HK stock names (港交所/中信证券等). **Fixed**: added 金融/能源/地产建筑/消费品/公用事业 categories with HK-specific keywords. 018388 industry now correctly shows 金融:83.2% instead of 其他:86%.

18. **print → logging migration** — 47 print statements in advisor.py(5)/data_fetcher.py(27)/investment_research.py(15) replaced with `logger.debug()`. Added `import logging` + `logger = logging.getLogger(__name__)` to each file.

## Recurring Audit Pattern

To audit the fund system for new issues:
1. Check database health: table sizes, NAV coverage per fund, transaction record coverage
2. Run full morning report: `python3 scripts/advisor.py morning` — check for contradictions between sections
3. Check cron jobs: `hermes cron list` — verify all jobs enabled, no delivery errors
4. Test data sources: curl each API endpoint (eastmoney/sina/1234567) for response
5. Check concentration: CR4 > 60% = warning, single fund > 30% = warning
6. Verify strategy signals: are they simulation or actual? Label clearly.
7. Check for ghost funds: NAV records for funds not in holdings
