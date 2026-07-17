# 盘中简报脚本说明

## ⚠️ MIGRATION NOTICE (2026-07-07)

`morning_intraday.py` and `afternoon_intraday.py` were **DELETED** during the 2026-07-06 optimization. Their functionality was merged into `advisor.py`. The intraday commands now route through `advisor.py`:

| Old (DELETED) | New |
|---|---|
| `python scripts/morning_intraday.py` | `python scripts/advisor.py morning_intraday` → calls `advisor.generate_morning_report()` |
| `python scripts/afternoon_intraday.py` | `python scripts/advisor.py afternoon_intraday` → calls `advisor.generate_afternoon_report()` |

The cron delivery layer (`cron_send_full_intraday.py`) was updated to call `advisor.py` subcommands instead of the deleted standalone scripts.

**⚠️ LESSON: When deleting/merging a script, audit ALL reference layers:**
1. Cron wrapper scripts (`~/.hermes/scripts/*.sh`)
2. Python delivery scripts (`cron_send_full_*.py`)
3. `advisor.py` main() import statements
4. Shell cron wrappers (`intra_*_cron.sh`)
5. This reference doc

A dangling reference in any layer causes the cron job to send the Python traceback as the "report" to Feishu, which is silent until the user sees garbage in their chat.

---

## 上午简报

**运行时间**: 10:30 (上午交易中段)

**Report Sections** (in order):
1. 【📈 A 股实时行情】 — code block table (指数/最新价/涨跌%/涨跌额)
2. 【💰 主力资金流向】 — code block table (行业/涨跌幅/成交额 or 净流入/占比)
3. 【🌡️ 市场情绪】 — sentiment score + up/down count
4. 【🛡️ 止盈止损监控】 — code block table (代码/名称/操作/紧急/原因)
5. 【📈 历史收益对比】 — code block table (代码/名称/近1周/近1月/近3月/最大回撤)
6. 【💼 持仓估值】 — code block table (代码/名称/净值(日期)/估值(时间)/涨跌%/涨跌额/估算市值)
7. 【📝 操作建议】 — data-driven advice (NOT generic filler)

## 下午简报

**运行时间**: 14:00 (下午开盘)

**Report Sections** (same as morning, except last section):
1-6: Same as morning
7. 【📝 尾盘操作建议】 — data-driven advice with 尾盘关注时段

---

## A股行情 Code Block Format (REQUIRED)

**⚠️ MUST use code block — NOT bullet points**

```python
report.append("```text")
COL_IDX = 12
COL_PRICE = 12
COL_PCT = 10
COL_AMT = 12
header = (self._pad('指数', COL_IDX, 'right') +
          self._pad('最新价', COL_PRICE, 'right') +
          self._pad('涨跌%', COL_PCT, 'right') +
          self._pad('涨跌额', COL_AMT, 'right'))
report.append(header)
report.append("─" * (COL_IDX + COL_PRICE + COL_PCT + COL_AMT))
for name, data in market.items():
    sign = "+" if data['change_pct'] >= 0 else ""
    price_s = f"{data['price']:.2f}"
    pct_s = f"{sign}{data['change_pct']:.2f}%"
    change = data.get('change', 0)  # ⚠️ field is 'change' NOT 'change_amt'
    amt_s = f"{sign}{change:.2f}" if change else "—"
    row = (self._pad(name, COL_IDX, 'right') +
           self._pad(price_s, COL_PRICE, 'right') +
           self._pad(pct_s, COL_PCT, 'right') +
           self._pad(amt_s, COL_AMT, 'right'))
    report.append(row)
report.append("```")
```

**⚠️ Tencent API field is `change` not `change_amt`** — `data.get('change_amt', 0)` silently returns 0!

---

## Data-Driven Investment Advice (REQUIRED)

**⚠️ Investment advice MUST be based on actual data, NOT generic filler text**

User complaint: "没有投资建议" when advice was hardcoded like "观察尾盘资金流向", "避免盲目追高杀跌"

**Pattern**: `_generate_advice(self, market, sentiment_data, smart_signals_text)`

```python
def _generate_advice(self, market, sentiment_data, smart_signals_text) -> str:
    lines = []
    
    # 1. Market trend analysis
    if market:
        sh_pct = market.get('上证指数', {}).get('change_pct', 0)
        if sh_pct > 1:
            lines.append("  📈 大盘强势上涨，注意追高风险")
        elif sh_pct > 0.3:
            lines.append("  📊 大盘温和上涨，可适当持有")
        elif sh_pct > -0.3:
            lines.append("  ➡️ 大盘窄幅震荡，观望为主")
        elif sh_pct > -1:
            lines.append("  📉 大盘小幅回调，关注支撑位")
        else:
            lines.append("  ⚠️ 大盘大幅下跌，谨慎操作")
    
    # 2. Sentiment analysis
    if sentiment_data:
        score = sentiment_data.get('score', 50)
        if score >= 70:
            lines.append("  🔥 市场情绪过热，注意止盈节奏")
        elif score >= 50:
            lines.append("  😊 市场情绪正常，保持策略纪律")
        elif score >= 30:
            lines.append("  😟 市场情绪偏弱，避免恐慌抛售")
        else:
            lines.append("  ❄️ 市场极度悲观，可能是左侧布局机会")
    
    # 3. Signal-based prioritization
    has_stop_loss = "止损" in smart_signals_text
    has_take_profit = "止盈" in smart_signals_text or "减仓" in smart_signals_text
    
    if has_stop_loss:
        lines.append("  🛡️ 有基金触发止损信号，优先处理风控")
    if has_take_profit:
        lines.append("  💰 有基金达到止盈档位，可考虑分批止盈")
    
    # 4. Action priority
    lines.append("")
    if has_stop_loss and has_take_profit:
        lines.append("  💡 今日重点：止损第一 > 止盈第二 > 观望")
    elif has_stop_loss:
        lines.append("  💡 今日重点：止损 > 止盈 > 新建仓")
    elif has_take_profit:
        lines.append("  💡 今日重点：止盈 > 持仓观察 > 新建仓")
    else:
        lines.append("  💡 今日重点：持仓观察，不急于操作")
    
    return "\n".join(lines)
```

**Wiring in report generation**:
```python
# In generate_intraday_morning_report() / generate_afternoon_report()
report.append("【📝 操作建议】")  # or 【📝 尾盘操作建议】
try:
    advice = self._generate_advice(market, sentiment_data, smart_signals)
    report.append(advice)
except Exception as e:
    report.append(f"  ⚠️ 建议生成失败: {e}")
```

---

## 持仓估值 Table Format

```text
代码    名称            净值(日期)    估值(时间)   涨跌%  涨跌额  估算市值
──────────────────────────────────────────────────────────────────────────
002112  德邦鑫星价.. 6.1293(05-28) 6.1303(10:32)  +0.02%      +1     5,708
...
合计                                              +0.15%      +9    21,900

⏰ 估值时间: 2026-05-29 10:32
```

**Column widths**: W_CODE(8) + W_NAME(12) + W_NAV(14) + W_EST(14) + W_PCT(8) + W_AMT(8) + W_VALUE(10)

---

## 止盈止损监控 Table Format

```text
代码      名称            操作        紧急    原因
────────────────────────────────────────────────────────────────────
020692  博时中证全指通信设备指数 C止盈        🟡     盈利87.5%，达到最高止盈档80%
002112  德邦鑫星价值灵活配置混合 C减仓        🟡     盈利73.8%，达到止盈档50%
```

---

## 历史收益对比 Table Format

```text
代码      名称                   近1周       近1月       近3月      最大回撤
──────────────────────────────────────────────────────────────
002112  德邦鑫星价值灵活配置混合 C    +2.20%    +1.34%    +1.71%   -15.17%
```

---

## Key Imports & Init

**⚠️ The standalone `IntradayAdvisor` and `AfternoonAdvisor` classes were in the deleted files.** The intraday commands now use `FundAdvisor` (from `advisor.py`) directly:

```python
# advisor.py main() handles routing:
# command == 'morning_intraday' → advisor.generate_morning_report()
# command == 'afternoon_intraday' → advisor.generate_afternoon_report()
# command == 'afternoon' → advisor.generate_afternoon_report()
```

---

## Cron 配置

**⚠️ Current setup (as of 2026-07-07): script-only mode + direct Feishu API**

The intraday cron jobs use `no_agent=true` with shell scripts that call `cron_send_full_intraday.py`, which runs `advisor.py` and sends the report directly to Feishu via POST API.

```bash
# 上午盘中简报 (10:30) - SCRIPT-ONLY MODE
# cron job 72f34a2e5e2f
# script: cron_send_full_intraday_morning.sh
# → calls: python scripts/cron_send_full_intraday.py morning
# → runs:  python scripts/advisor.py morning_intraday

# 下午盘中简报 (14:00) - SCRIPT-ONLY MODE
# cron job eadf563be502
# script: cron_send_full_intraday_afternoon.sh
# → calls: python scripts/cron_send_full_intraday.py afternoon
# → runs:  python scripts/advisor.py afternoon_intraday
```

**⚠️ MUST use script-only mode with direct Feishu API** — agent mode had delivery failures (see `references/cron-feishu-delivery.md`).

---

## 注意事项

1. **数据库路径**: 使用 `get_db_path()` 获取正确的数据库路径
2. **网络超时**: API 请求设置 timeout=5 秒
3. **QDII基金**: 如022184（富国全球科技）无盘中估值，显示"—"
4. **LOF基金**: 如501205（鹏华创新未来）无盘中估值，显示"—"
5. **Tencent API**: field is `change` NOT `change_amt`
6. **所有表格数据必须用代码块包裹** — 包括A股行情

---

## 脚本位置

- `~/.hermes/fund-advisor/scripts/advisor.py` (morning_intraday / afternoon_intraday subcommands)
- `~/.hermes/fund-advisor/scripts/cron_send_full_intraday.py` (Feishu delivery wrapper)

### Legacy shell wrappers (updated 2026-07-07)

These old shell wrappers now route to `advisor.py` subcommands:

```bash
# ~/.hermes/scripts/intra_morning_cron.sh
#!/bin/bash
cd ~/.hermes/fund-advisor
python scripts/advisor.py morning_intraday

# ~/.hermes/scripts/intra_afternoon_cron.sh
#!/bin/bash
cd ~/.hermes/fund-advisor
python scripts/advisor.py afternoon_intraday
```
