# Briefing System Audit & Fix Patterns

Lessons from auditing and fixing the fund-advisor briefing system (2026-07-08).
Each pattern is a recurring trap that will bite again if not encoded.

## 1. `WHERE share_count > 0` Excludes Screenshot-Synced Funds

**Symptom**: Funds synced via screenshots (fund-holdings-sync skill) have
`share_count = 0` but `current_value > 0`, because the screenshot shows
market value, not share count. SQL queries filtering on `share_count > 0`
silently drop these funds from the report.

**Affected files** (found in 2026-07-08 audit):
- `scripts/advisor.py` (3 queries)
- `scripts/adaptive_risk_v2.py`
- `scripts/data_fetcher.py`
- `scripts/holdings_overlap.py`
- `scripts/oof_strategy_advisor.py`
- `scripts/update_nav_curl.py`
- `scripts/weekly_review.py`

**Fix**: Every holdings query must use:
```sql
WHERE share_count > 0 OR current_value > 0
```

**Audit command** (find all instances):
```bash
grep -rn "share_count > 0" scripts/*.py | grep -v "INSERT\|UPDATE\|SET "
```

## 2. Stale nav_history for Cleared Positions → Phantom MA Signals

**Symptom**: After clearing a position (e.g., selling all of 022184),
the `fund_nav_history` table still has old NAV entries. The MA strategy
engine reads nav_history independently of holdings, so it generates
"sell" signals for funds you no longer own.

**Fix**: When a position is fully closed, delete its nav_history:
```python
c.execute("DELETE FROM fund_nav_history WHERE fund_code IN ('022184','026211')")
```

**Pitfall**: The MA signal section will also show "基金022184" (missing name)
because the holdings table no longer has the fund_name. Always clean both
tables together.

## 3. Hardcoded Fund References Become Stale

**Symptom**: `advisor.py` had hardcoded suggestions like:
```python
suggestions.append("🔴 022184仓位偏重(34.9%)，建议分批减仓至20%以下分散风险")
suggestions.append("📅 022184每日定投200元持续中，当前亏损-0.1%，低位积累筹码")
```
These became stale the moment the user changed positions or DCA plans.

**Fix**: Read DCA info from `dca_plans` table (or `user_config.dca_plans` dict).
Read position warnings from the actual holdings_summary string via regex,
not hardcoded fund codes.

```python
# Dynamic DCA from DB
cursor.execute("SELECT fund_code, fund_name, daily_amount FROM dca_plans WHERE active=1")
```

## 4. New Position Risk Scoring Exemption

**Symptom**: A fund held for only 2 weeks (e.g., 017731 just started DCA)
gets a risk score of 36 and suggestion "考虑减仓" — nonsensical for a
position that just started.

**Fix**: Add `_is_new_position(fund_code)` check in `adaptive_risk_v2.py`:
if the earliest nav_history entry is <90 days ago, override the suggestion
to "新建仓观察期" with `hold_watch` level instead of "考虑减仓" or "建议止盈".

```python
def _is_new_position(self, fund_code: str) -> bool:
    cursor.execute("""
        SELECT MIN(nav_date) FROM fund_nav_history WHERE fund_code = ?
    """, (fund_code,))
    result = cursor.fetchone()
    if result and result[0]:
        from datetime import datetime
        first_date = datetime.strptime(result[0], '%Y-%m-%d')
        return (datetime.now() - first_date).days < 90
    return False
```

## 5. Emoji in Fund Names Breaks Column Alignment

**Symptom**: Prepending 📅 to a fund name in the holdings table output
shifts all subsequent columns out of alignment, because `east_asian_width()`
counts emoji as width-1 but terminals render them as width-2.

**Fix**: Never prepend emoji to data fields in code-block tables. Put DCA
indicators in a separate "定投计划" section below the table, or append a
suffix marker that doesn't affect alignment.

## 6. Moving Stop-Profit Wording Confusion

**Symptom**: "触发移动止盈（阈值8.0%）" was interpreted as "sell everything
now", causing panic. The user actually needs to understand this is a
"first step" signal.

**Fix**: Change wording to:
```
触发分批止盈信号（从高点回撤>8%，建议减仓1/3锁定利润）
```
Key words: "分批" (in batches), "1/3" (specific amount), "锁定利润" (lock profit).

## 7. MA Signal Labeling

**Symptom**: Simulated MA strategy signals appeared alongside real
operation suggestions with identical formatting, making them
indistinguishable.

**Fix**: Add prominent warning at section start and annotate each signal:
```
⚠️ 以下为技术面模拟信号，仅供参考，非实际操作建议
```
Each "卖出" action gets: `卖出（模拟信号，非实际操作建议）`

## 8. Benchmark Comparison (沪深300)

**Pattern**: Portfolios without a benchmark comparison are meaningless.
The `_get_benchmark_comparison()` method compares 30-day portfolio return
against 沪深300 (fund_code='000300' in fund_nav_history).

Falls back to aggregating holdings' NAV-weighted returns if the
`portfolio_snapshots` table doesn't exist.

## 9. Valuation Percentile Warning

**Pattern**: For each holding fund, show PB/PE percentile:
- 🔴 PB > 95%: "估值处于历史最高5%区间，杀估值风险极大"
- 🟡 PB 85-95%: "估值偏高，关注季度毛利率变化"
- 🟢 PB < 50%: normal

Key trigger: "环比降>3pp即减仓信号" — quarterly gross margin drop >3pp
is the sell signal for high-valuation positions.

## 10. Overlap-Driven Operation Suggestions

**Pattern**: The overlap analysis already identifies cross-fund holdings
(e.g., 天孚通信 held by 4 funds at 27% combined), but previously didn't
generate actionable suggestions.

**Fix**: For severe overlap (3+ funds), generate:
```
→ 建议在盈利最多的基金中减仓1/3，降低单一个股集中度
```
Link to the specific fund with highest profit for actionable guidance.

11. **Monthly Evaluation: Real Portfolio vs Virtual Backtest**

**Symptom**: Monthly evaluation ran a virtual 100K backtest that produced
all-zeros (0 trades, 0 return) because the strategy never triggered.
Meanwhile the actual portfolio was up/down significantly.

**Fix**: Add `evaluate_real_portfolio(start_date, end_date)` that:
1. Queries actual holdings from `holdings` table
2. Gets month-start and month-end NAV from `fund_nav_history`
3. Calculates weighted portfolio return = Σ(fund_value × fund_return) / total_value
4. Includes this alongside (not replacing) the virtual backtest

## 12. Portfolio-Level Industry Aggregation

**Pattern**: The industry allocation section showed per-fund breakdown
("002112 通信32.8%, 005165 电子37.1%") but never aggregated into
portfolio-level exposure.

**Fix**: During the per-fund industry loop, accumulate weighted exposure:
```python
portfolio_industry[industry] += fund_val * ratio / 100 / total_port_value * 100
```
After the loop, print a "组合穿透" summary with top-5 industries and
🔴>30% / 🟡>15% markers.

## 13. Risk-Parity vs Risk Engine Contradiction

**Symptom**: The risk-parity rebalancing engine generated "📈 增持9.1%"
for fund 018388 while the risk engine simultaneously warned "仓位偏重20.6%，
注意分散".

**Fix**: Before generating a BUY suggestion, check current weight:
```python
current_weight = current_weights.get(code, 0) * 100
if info['action'] == 'BUY' and current_weight > 20:
    actions.append(f"  ⚠️ {code} {name}: 风险平价建议增持，"
                   f"但当前仓位{current_weight:.1f}%已偏重，维持观察")
```

## 14. Backfill share_count from current_value / NAV

**Symptom**: After screenshot sync, funds have `share_count=0` but
`current_value>0`. Even after fixing the `WHERE` filter, daily return
calculation `shares * nav * nav_change` returns 0 because shares=0.

**Fix**: One-time DB backfill after every screenshot sync:
```sql
-- For each fund where share_count=0 AND current_value>0:
UPDATE holdings SET share_count = current_value / (
    SELECT unit_nav FROM fund_nav_history
    WHERE fund_code = holdings.fund_code
    ORDER BY nav_date DESC LIMIT 1
) WHERE share_count = 0 AND current_value > 0;
-- Also backfill avg_cost if total_invested is available:
UPDATE holdings SET avg_cost = total_invested / share_count
WHERE share_count > 0 AND total_invested > 0 AND avg_cost = 0;
```

## Audit Checklist (run when positions change)

When the user changes positions (buys/sells/DCA switches), run this checklist:

1. **Holdings table**: Confirm new funds are in `holdings` with correct names
2. **nav_history**: Delete entries for cleared funds; fetch history for new funds
3. **Hardcoded refs**: `grep -rn "OLD_FUND_CODE" scripts/*.py` — replace with dynamic DB reads
4. **share_count filter**: Ensure all queries use `share_count > 0 OR current_value > 0`
5. **DCA plans**: Update `user_config.py` dca_plans dict + `dca_plans` DB table
6. **theme_map**: Update fund→theme mappings in advisor.py and adaptive_risk_v2.py
7. **FUND_NAMES fallback**: Add new fund codes to the fallback dict in weekly_review.py
8. **Cron jobs**: Stop old DCA crons, create new ones for the new DCA fund
9. **Run verification**: `python3 scripts/advisor.py morning 2>/dev/null | grep "FUND_CODE"`
