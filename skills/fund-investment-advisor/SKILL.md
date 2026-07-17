---
name: fund-investment-advisor
description: Build and operate an intelligent fund investment advisor system with Hermes Agent
version: "2.7.0"
author: User + Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [finance, investment, fund, automation, cron, data-analysis]
    related_skills: [cronjob, terminal, file]
---

# Fund Investment Advisor System

Build a personalized fund investment advisor using Hermes Agent that provides market data, portfolio tracking, automated reports, strategy backtesting, and investment recommendations.

**What this skill covers**:
- Setting up the project structure and database
- Fetching fund and market data (A-shares, US stocks, indices)
- Creating automated reports (morning briefing, evening summary)
- Recording and tracking transactions
- Implementing investment strategies (DCA, rebalancing, stop-profit)
- Setting up cron jobs for定时推送
- Building backtesting engine
- Generating periodic review reports (weekly/monthly/quarterly/yearly)
- Real-time dashboard v4 (Flask + Plotly, 16 modules: market ticker/KPI/holdings/charts/macro/ai-berkshire 4-master analysis, multi-user auth, manual import, LaunchAgent auto-restart)e, auto-refresh) — see references/dashboard-deployment.md
- Full-portfolio diagnosis (scoring system + cross-fund comparison + operation priority + before/after projection) — see references/fund-diagnosis-workflow.md section "Portfolio-Wide Diagnosis"
- Real-time market context integration (today's NAVs + sector performance) — same reference
- **Code: 27 modules**
- **Refs**: `references/backtest-engine.md`, `references/holdings-overlap.md`, `references/akshare-api-notes.md`, `references/market-data-sources.md`, `references/briefing-audit-fixes.md`, `references/report-modules.md`, `references/dashboard-deployment.md`, `references/fund-diagnosis-workflow.md`, `references/pitfalls.md`
- **AKShare: `pip3 install akshare`**

**Use this skill when**:
- Building a fund investment tracking system
- Automating investment reports and alerts
- Implementing and testing investment strategies
- Setting up periodic portfolio reviews

---

## Quick Start

### 1. Initialize the System

```bash
# Create project structure
mkdir -p ~/.hermes/fund-advisor/{data,scripts,configs,reports,logs}
cd ~/.hermes/fund-advisor

# Initialize database
python scripts/db_init.py

# Test the system
python scripts/advisor.py morning
python scripts/advisor.py holdings

# Run investment analysis
python scripts/investment_analysis.py
```

### 2. Record a Transaction

```bash
# Buy fund
python scripts/advisor.py buy <fund_code> <amount>

# Example:
python scripts/advisor.py buy 159915 1000

# Sell fund
python scripts/advisor.py sell <fund_code> <amount>

# Update NAV data (critical for 今日收益 to show correctly)
python scripts/update_nav_curl.py  # Uses curl to bypass network restrictions

# Validate data integrity (recommended after updates)
python scripts/validate_nav_data.py
```

### 3. Set Up Automated Reports

**⚠️ Use AGENT mode** (`no_agent=false`, the default) for ALL fund advisor cronjobs.

**Why NOT script-only mode (`no_agent=true`)?**
- ❌ Script output (10-15KB) exceeds Feishu single-message limit (~4-5KB)
- ❌ Progress logs (✓, 📝, ⚠️, 🔄) are included in output, wasting character budget
- ❌ Long reports get **truncated** — user only sees first half, missing strategy advice and action items
- ❌ Cannot split into multiple messages

**Why agent mode?**
- ✅ Agent filters out progress/debug lines (✓, 📝, ⚠️, 🔄, 🌅 prefix lines)
- ✅ Agent splits long reports into 2-3 messages, each under 3000 chars
- ✅ Each message is complete and readable
- ✅ Agent can adapt formatting if needed

**⚠️ Pitfall: `no_agent` cannot be toggled via update**
- `cronjob update` does NOT support changing `no_agent` from true to false
- Must delete and recreate the job to switch modes

```bash
# Morning briefing (8:30 AM) - AGENT MODE (no no_agent flag = default false)
hermes cron create "30 8 * * *" \
  "运行基金投资顾问开盘前简报脚本，然后将报告分段发送给用户。

步骤：
1. 运行 \`cd ~/.hermes/fund-advisor && python scripts/update_nav_curl.py 2>&1 | tail -1\` 更新净值
2. 运行 \`cd ~/.hermes/fund-advisor && python scripts/advisor.py morning 2>&1\` 获取完整输出
3. 从输出中提取报告内容（去掉所有以 ✓、📝、⚠️、🔄 开头的进度日志行，只保留从 \"🌅 **早安！\" 开始的正式报告内容）
4. 将报告分成2-3条消息发送：
   - 第1条：全球市场 + A股指数 + 资金流向 + 市场情绪 + 持仓概览
   - 第2条：行业配置 + 策略建议 + 止盈止损监控
   - 第3条：场外基金操作建议 + 今日建议 + 风险提示

直接输出报告内容，不要加任何额外解释。保持原始格式。" \
  --name "开盘前简报" \
  --deliver "origin"

# Intraday morning (10:30 AM) - AGENT MODE
hermes cron create "30 10 * * *" \
  "运行基金投资顾问盘中上午简报脚本，然后将报告分段发送给用户。

步骤：
1. 运行 \`cd ~/.hermes/fund-advisor && python scripts/morning_intraday.py 2>&1\` 获取完整输出
2. 从输出中去掉所有进度日志行（以 ✓、📝、⚠️、🔄 开头的行），只保留正式报告内容
3. 如果报告很长，分成2条消息发送，确保每条不超过3000字

直接输出报告内容，不要加任何额外解释。保持原始格式。" \
  --name "盘中上午简报"

# Intraday afternoon (2:00 PM) - AGENT MODE
hermes cron create "0 14 * * *" \
  "运行基金投资顾问盘中下午简报脚本，然后将报告分段发送给用户。

步骤：
1. 运行 \`cd ~/.hermes/fund-advisor && python scripts/afternoon_intraday.py 2>&1\` 获取完整输出
2. 从输出中去掉所有进度日志行（以 ✓、📝、⚠️、🔄 开头的行），只保留正式报告内容
3. 如果报告很长，分成2条消息发送，确保每条不超过3000字

直接输出报告内容，不要加任何额外解释。保持原始格式。" \
  --name "盘中下午简报"

# Evening summary (4:30 PM) - AGENT MODE
hermes cron create "30 16 * * *" \
  "运行基金投资顾问盘后总结脚本，然后将报告分段发送给用户。

步骤：
1. 运行 \`cd ~/.hermes/fund-advisor && python scripts/advisor.py evening 2>&1\` 获取完整输出
2. 从输出中去掉所有进度日志行（以 ✓、📝、⚠️、🔄 开头的行），只保留正式报告内容
3. 将报告分成2-3条消息发送，确保每条不超过3000字

直接输出报告内容，不要加任何额外解释。保持原始格式。" \
  --name "盘后总结"

# Weekly review (Sunday 8PM) - AGENT MODE
hermes cron create "0 20 * * 0" \
  "运行基金投资顾问周复盘报告脚本，然后将报告分段发送给用户。

步骤：
1. 运行 \`cd ~/.hermes/fund-advisor && python scripts/advisor.py weekly 2>&1\` 获取完整输出
2. 从输出中去掉所有进度日志行（以 ✓、📝、⚠️、🔄 开头的行），只保留正式报告内容
3. 将报告分成3-4条消息发送，确保每条不超过3000字

直接输出报告内容，不要加任何额外解释。保持原始格式。" \
  --name "周复盘报告"
```

**Note on formatting**: Agent mode may occasionally reformat code blocks. If this happens, add explicit instructions in the prompt: "保持原始的代码块格式和列对齐，不要修改表格内容"。

**⚠️ Pitfall: Inline cron scripts are unreliable**
- Inline scripts (stored directly in the cron job `script` field) can have encoding issues, grep pattern mismatches, and are hard to debug
- **Always use proper script files** under `~/.hermes/scripts/` instead
- Example: Create `~/.hermes/scripts/update-nav-cron.sh` with proper shebang and content, then reference it by filename in the cron job

**Update existing cronjob to script-only**:
```bash
# Find job ID
hermes cron list

# Update to script-only mode
hermes cron update <job_id> \
  --script "fund-morning-cron.sh" \
  --no-agent true \
  --prompt "[SILENT]"
```

**Manage cron jobs**:
```bash
# List all jobs
hermes cron list

# Pause a job
hermes cron pause <job_id>

# Resume a job
hermes cron resume <job_id>

# Test immediately
hermes cron run <job_id>

# Remove a job
hermes cron remove <job_id>
```

See `references/script-only-cronjobs.md` for detailed guide on script-only mode configuration.

---

## Core Components

### Database Schema

The system uses SQLite with these key tables:

- **holdings**: Current fund positions (code, name, shares, cost, value)
- **transactions**: All buy/sell records with timestamps
- **fund_nav_history**: Historical NAV data for backtesting
- **strategies**: Investment strategy configurations
- **review_reports**: Periodic review summaries
- **user_config**: User preferences and settings

See `references/database-schema.md` for full schema details.

### Data Sources

**Free/Low-cost**:
- 新浪财经：Real-time indices (A-shares, US stocks, HK stocks, FX, Gold)
- 天天基金网 (EastMoney): Fund NAV, historical data

**Paid (optional)**:
- Wind 万得：Professional terminal
- 同花顺 iFinD: Institutional data
- Choice 数据：EastMoney premium

**Industry Data**:
- 行业资金流向：EastMoney API (`fs=m:90+t:2` for 申万行业 classification, NOT `fs=bk` which is deprecated, NOT `fs=m:0+t:6` which returns stocks)
- 基金持仓：EastMoney API (often 404, use name-based inference fallback)
- See `references/industry-data.md` for detailed API patterns and fallback strategies
- See `references/industry-api-troubleshooting.md` for common API failures and fixes

### Report Types

1. **Morning Briefing (8:30 AM)**
   - Global market summary: **美股三大指数**(新浪 gb_dji/ixic/inx), **港股恒生**(新浪 rt_hkHSI), **USD/CNY汇率**(新浪 USDCNY), **COMEX黄金**(新浪 hf_GC)
   - A-share indices status
   - **北向资金** (东财 kamt.kline API, 沪股通+深股通)
   - **Industry capital flow** (主力资金流向 - 行业级别，使用 `fs=m:90+t:2` 参数)
   - **概念板块资金流向** (东财 `fs=m:90+t:3`, Top5 净流入)
   - **个股资金流向Top5** (东财 `fs=m:0+t:6,m:0+t:80,...`)
   - Market sentiment + mainline tracking
   - Portfolio overview with **industry allocation** (行业配置)
   - **Personalized strategy recommendations** (per-fund analysis based on industry trends)
   - Multi-factor adaptive risk signals (adaptive_risk_v2)
   - OOF strategy advice (移动止盈/配置/定投)
   - MA crossover signals
   - Today's suggestions

   **⚠️ Yahoo Finance API已失效** — 不再使用 `query1.finance.yahoo.com`。美股数据改用新浪 `hq.sinajs.cn/list=gb_dji,gb_ixic,gb_inx`。

   **⚠️ 东财 stock/get API 不稳定** — `push2.eastmoney.com/api/qt/stock/get` 经常返回 `data:null`。港股/美股/汇率/黄金等单只指数行情用新浪源；行业/概念/个股资金流向用东财 `clist/get` API（稳定）。

2. **Intraday Morning (10:30 AM)** — includes real-time estimated NAV (盘中估值)
   - **A-share real-time quotes** — MUST be in code block with table format (指数/最新价/涨跌%/涨跌额)
   - **Industry capital flow** (热门/冷门行业)
   - **Market sentiment** (市场情绪)
   - **止盈止损监控** (🛡️) — per-fund smart strategy signals (stop-loss, take-profit, reduce, warning)
   - **历史收益对比** (📈) — 1-week/1-month/3-month returns + max drawdown
   - Holdings with **both latest confirmed NAV + real-time estimated NAV**
   - Table columns: 代码, 名称, 净值(日期), 估值(时间), 涨跌%, 涨跌额, 估算市值
   - QDII/LOF funds may have no estimate (show "—")
   - **操作建议** (📝) — data-driven advice based on market/sentiment/signals (NOT generic filler)
   - See `references/fund-estimate-api.md` for 天天基金估值API details

3. **Intraday Afternoon (2:00 PM)**
   - Afternoon opening alert
   - Full-day trend prediction
   - Holdings performance
   - **止盈止损监控** (🛡️) — same as morning intraday
   - **历史收益对比** (📈) — same as morning intraday
   - **Personalized strategy recommendations** (per-fund analysis)
   - **尾盘操作建议** (📝) — data-driven advice (NOT generic filler)

4. **Evening Summary (4:30 PM)**
   - Daily market review
   - Portfolio value update
   - **Personalized strategy recommendations** (per-fund analysis)
   - Tomorrow's outlook
   - Reminders

5. **Weekly Review (Sunday 8PM)**
   - Weekly P&L analysis
   - Transaction summary
   - Strategy performance
   - Issues and improvements

6. **Monthly/Quarterly/Annual Reviews**
   - Comprehensive performance analysis
   - Strategy effectiveness evaluation
   - Risk metrics (max drawdown, Sharpe ratio)
   - Next period plan

**Personalized Strategy Recommendations** (NEW 2026-05-21):
- Analyzes each fund based on 3 dimensions:
  1. **Industry match**: Fund holdings vs. daily capital flow (hot/cold sectors)
  2. **Relative strength**: Fund return vs. market average
  3. **Profit/loss status**: Current P&L percentage
- Provides specific action recommendations:
  - **可加仓** (Add position): Hot sector + strong performance
  - **持有观望** (Hold & observe): No clear signals
  - **持有待涨** (Hold & wait): Hot sector but not yet performing
  - **考虑减仓** (Consider reducing): Cold sector or high profit
  - **谨慎持有** (Hold cautiously): Weak performance
  - **止盈或部分减仓** (Take profit): Profit > 20%
  - **考虑止损** (Consider stop-loss): Loss > 10%

See `references/industry-data.md` for detailed API patterns and fallback strategies.
See `references/personalized-strategies.md` for implementation details and decision logic.

**Industry Features** (2026-05-21, updated 2026-05-25):
- **行业资金流向**: Fetch industry-level capital flow using `fs=m:90+t:2` parameter (申万行业分类, NOT `fs=bk` which is deprecated, NOT `fs=m:0+t:6` which returns individual stocks)
- **基金行业配置**: Get fund industry allocation from holdings API, fallback to name-based inference when API fails
- **策略建议**: Match fund holdings with capital flow trends for personalized buy/sell/hold recommendations

See `references/intraday-scripts.md` for 盘中简报 implementation details.
See `references/industry-data-api.md` for industry data API patterns and fallback strategies.
See `references/industry-api-troubleshooting.md` for API parameter changes and troubleshooting.

---

## Investment Strategies

### 1. Value DCA (价值定投)

Adjust DCA amount based on valuation:
- Undervalued (<30% percentile): 1.5x normal amount
- Normal (30-70%): 1.0x normal amount
- Overvalued (>70%): 0.5x normal amount
- Bubble (>90%): Pause DCA

### 2. Rebalancing (定期再平衡)

- Frequency: Quarterly
- Threshold: 5% deviation from target
- Method: Use new funds first, then sell/buy

### 3. Stop-Profit (分批止盈)

- Level 1: +15% profit → sell 50%
- Level 2: +25% profit → sell 30%
- Level 3: +35% profit → sell 20%

### 4. Momentum Rotation (动量轮动)

- Lookback: 3 months
- Select top 2 sectors
- Hold period: 1 month

### 5. Investment Analysis (投资分析)

**New in v1.1.0**: Automated portfolio analysis with actionable recommendations.

**Features**:
- Total performance analysis (市值、盈亏、收益率)
- Profit/loss ranking
- Industry allocation analysis
- Portfolio concentration assessment
- Risk evaluation (最大回撤、行业集中度)
- Investment suggestions (止盈、止损、调仓)

**Usage**:
```bash
# Run investment analysis
python3 scripts/investment_analysis.py

# Output includes:
# 📊 总体表现
# 🏆 收益排名
# ⚠️ 亏损基金
# 🏭 行业配置分析
# 🎯 持仓集中度分析
# ⚠️ 风险评估
# 💡 投资建议
```

See `references/investment-analysis.md` for detailed workflow and implementation.

### 6. Strategy Backtesting (策略回测)

**New in v1.2.0**: Complete backtesting system for strategy evaluation and optimization.

**Features**:
- Historical trade simulation (历史交易模拟)
- Parameter optimization (参数优化)
- Strategy comparison (策略比较)
- Monthly evaluation (月度评估)
- Visual reports (可视化报告)

**Components**:
- `backtest_engine.py`: Core backtesting engine
- `strategy_optimizer.py`: Parameter optimization
- `monthly_evaluation.py`: Monthly evaluation system
- `report_visualizer.py`: HTML report generator
- `backtest_main.py`: Main CLI interface

**Built-in Strategies**:
1. **Simple Profit/Loss** (止盈止损策略): Fixed thresholds for take profit and stop loss
2. **Batch Take Profit** (分批止益策略): Sell in batches at different profit levels
3. **Trend Following** (趋势跟踪策略): Based on moving average crossovers
4. **Combined Strategy** (组合策略): Multi-strategy combination

**Usage**:
```bash
# Run backtest
python scripts/backtest_main.py backtest --start-date 2026-03-01 --end-date 2026-04-30

# Optimize parameters
python scripts/backtest_main.py optimize --strategy simple --start-date 2026-03-01 --end-date 2026-04-30

# Compare strategies
python scripts/backtest_main.py compare --start-date 2026-03-01 --end-date 2026-04-30

# Monthly evaluation
python scripts/backtest_main.py monthly

# Generate HTML report
python scripts/backtest_main.py backtest --html
```

**Key Metrics**:
- Total return (总收益率)
- Annualized return (年化收益率)
- Maximum drawdown (最大回撤)
- Sharpe ratio (夏普比率)
- Win rate (胜率)
- Trade frequency (交易频率)

**Monthly Evaluation Setup**:
```bash
# Monthly evaluation cron job (runs on 1st of each month at 9:00 AM)
# Already configured in system
```

See `references/backtest-system.md` for detailed documentation.

### 7. Weekly Review (周度复盘)

**New in v1.2.1**: Weekly strategy review system for continuous improvement.

**Features**:
- Weekly performance analysis (周度表现分析)
- Problem identification (问题识别)
- Optimization suggestions (优化建议)
- Risk assessment (风险评估)

**Components**:
- `weekly_review.py`: Weekly review engine
- Automated problem detection (自动问题检测)
- Performance ranking (表现排名)
- Actionable suggestions (可操作建议)

**Usage**:
```bash
# Run weekly review
python scripts/weekly_review.py
```

**Key Metrics Analyzed**:
- Weekly return (周收益率)
- Volatility (波动率)
- Maximum drawdown (最大回撤)
- Win rate (胜率)
- Problem severity (问题严重性)

**Automated Schedule**:
```bash
# Weekly review cron job (every Sunday at 8:00 PM)
# Already configured in system
```

**Review Categories**:
1. **收益问题** - Funds with significant losses
2. **波动率过高** - High volatility funds
3. **回撤过大** - Excessive drawdowns
4. **胜率过低** - Low win rate funds
5. **持仓集中度** - Portfolio concentration issues

See `references/weekly-review.md` for detailed workflow.
See `references/weekly-portfolio-analysis.md` for **portfolio-level** analysis supplement (total weekly P&L, effective industry exposure, concentration checks) — run `scripts/weekly_portfolio_analysis.py` AFTER `weekly_review.py` to get the complete picture.

### 8. Fund Category Analysis Framework (基金分类分析框架)

**New in v1.2.2**: Different fund types require different analysis frameworks.

**Core Principle**: 
- ❌ NOT all funds analyzed the same way
- ✅ Each fund type has unique metrics, risks, and timing signals

**Fund Category Analysis Matrix**:

| Fund Type | Core Metrics | Timing Signal | Risk Factors | Stop Loss |
|-----------|--------------|---------------|--------------|-----------|
| 行业指数基金 (014414) | 产品价格、供需关系、产能周期 | 行业拐点、季节性 | 政策调控、疫病、进口 | -12% |
| 港股/海外基金 (018388, 022184) | 汇率、估值分位、资金流向 | 港股估值历史分位 | 汇率风险、地缘政治、外围市场 | -12% |
| 科技主题基金 (020692, 026211) | 产业政策、订单数据、技术迭代 | 科技创新周期 | 政策风险、估值泡沫 | -15% |
| 灵活配置基金 (002112, 005165) | 基金经理、持仓变化、换手率 | 基金经理风格适应度 | 基金经理变更、规模异常 | -15% |
| 创新成长基金 (027063, 501205) | 新兴产业政策、盈利增速 | 成长vs价值相对强弱 | 估值容忍度、流动性 | -15% |

**Analysis Dimension Differences**:

| Dimension | 行业指数 | 港股/海外 | 科技主题 | 灵活配置 |
|-----------|----------|-----------|----------|----------|
| 看基金经理？ | ❌ | ❌ | ❌ | ✅ 必须 |
| 看行业基本面？ | ✅ 核心 | 部分相关 | ✅ 重要 | ❌ |
| 看汇率？ | ❌ | ✅ 核心 | ❌ | ❌ |
| 看政策？ | ✅ 重要 | ✅ 重要 | ✅ 核心 | 部分相关 |

**Category-Specific Analysis Examples**:

```python
# 行业指数基金分析要点 (e.g., 014414 畜牧)
industry_fund_metrics = {
    '核心指标': ['猪肉价格', '能繁母猪存栏', '饲料成本'],
    '择时信号': '猪周期位置（上行/下行/筑底）',
    '季节性': '节假日消费旺季（春节、中秋前）',
    '风险因素': ['疫病风险', '政策调控', '进口冲击'],
    '关注数据': ['农业农村部月度数据', '猪肉批发价格', '上市公司出栏量']
}

# 港股基金分析要点 (e.g., 018388 港股红利)
hk_fund_metrics = {
    '核心指标': ['恒生指数', '股息率', '南向资金', '汇率'],
    '择时信号': '港股估值分位（PE/PB历史分位）',
    '风险因素': ['汇率风险', '地缘政治', '美联储政策'],
    '关注指标': ['美元指数', '10年期美债收益率', '港股通净流入']
}

# 灵活配置基金分析要点 (e.g., 002112 德邦鑫星)
flex_fund_metrics = {
    '核心指标': ['基金经理业绩', '持仓集中度', '换手率', '规模变化'],
    '择时信号': '基金经理投资风格是否适应当前市场',
    '风险因素': ['基金经理变更', '规模暴涨', '风格漂移'],
    '关注点': ['季报前十大持仓', '基金经理任期', '管理规模']
}
```

**Weekly Review Enhancement by Category**:
- Different stop-loss/take-profit thresholds per category
- Category-specific problem detection (e.g., industry cycle reversal vs. manager change)
- Tailored optimization suggestions based on fund type

**Auto-Detection for New Funds**:
When a new fund is added via `advisor.py buy`, the system automatically:
1. Reads the fund name from the database
2. Matches keywords in `configs/fund_categories.yaml`
3. Assigns to the best matching category
4. Applies category-specific analysis framework

**Adding Custom Funds to Categories**:
Edit `configs/fund_categories.yaml`:
```yaml
categories:
  科技主题基金:
    auto_keywords: ["科技", "通信", "5G", "AI"]
    stop_loss: -15
    take_profit: +25
    funds:
      - code: "999999"
        name: "新科技基金"
        industry: "半导体"
        core_metrics: ["芯片价格", "订单数据"]
```

See `references/fund-category-analysis.md` for detailed framework and examples.

### 9. Enhanced Strategy Engine (增强版策略引擎)

**New in v1.2.3**: Integrated multiple market-proven strategies.

**Available Strategies**:

| Strategy | Description | Expected Return | Best For |
|----------|-------------|-----------------|----------|
| 价值定投 (Value DCA) | Dynamic DCA based on PE percentile | 8-12% | 宽基指数 |
| 网格交易 (Grid Trading) | Buy low, sell high in fixed grid | 10-15% | 行业ETF、震荡市 |
| 趋势跟踪 (Trend Following) | MA crossover trend following | 12-20% | 趋势行情 |
| 动量轮动 (Momentum Rotation) | Hold top performing funds | 15-25% | 行业轮动 |
| 风险平价 (Risk Parity) | Equal risk contribution weighting | 6-10% | 多资产组合 |
| 移动止盈 (Trailing Stop) | Track highest price, exit on drawdown | +30%+收益 | 所有基金 |
| 核心-卫星 (Core-Satellite) | 70% core + 30% satellite | 8-15% | 平衡型投资者 |
| 双均线择时 (Dual MA) | MA5/MA20 crossover timing | 10-15% | 趋势行情 |

**Key Optimizations**:

1. **移动止盈 > 固定止盈**: 让利润奔跑
   ```python
   # 固定止盈：+25%卖出
   # 移动止盈：从最高点回撤8%卖出，可能在+40%时卖出
   ```

2. **风险平价 > 等权配置**: 降低波动20-30%
   ```python
   # 波动率高的基金配置少，波动率低的配置多
   weights = calculate_risk_parity(volatilities)
   ```

3. **动量轮动**: 追随市场热点
   ```python
   # 选择过去20日涨幅前2的基金持有
   top_funds = select_by_momentum(funds, period=20, top_n=2)
   ```

**Usage**:
```python
from enhanced_strategies import EnhancedStrategyEngine, StrategyType

engine = EnhancedStrategyEngine()

# 移动止盈信号
signal = engine.generate_trailing_stop_signal(
    fund_code="002112",
    current_price=1.05,
    highest_price=1.15,
    cost_price=0.95
)

# 风险平价权重
weights = engine.calculate_risk_parity_weights({
    "002112": 0.15,  # 15%波动率
    "018388": 0.20,  # 20%波动率
})

# 价值定投金额
amount, reason = engine.calculate_value_dca_amount(pe_percentile=25)
```

See `references/strategy-optimization.md` for detailed recommendations.

### 10. OOF Strategy Engine (场外基金专用策略)

**New in v1.2.4**: Strategies optimized specifically for 场外基金 (OTC funds).

**Key Differences from 场内 ETF**:

| Feature | 场内 ETF | 场外基金 |
|---------|----------|----------|
| 交易确认 | 实时 | T+1 |
| 交易时间 | 9:30-15:00 | 全天（按收盘净值） |
| 赎回到账 | T+1 | T+3~7 |
| 交易费用 | 佣金万1-3 | 申购0.15%，赎回0.5% |
| 适合策略 | 高频、日内 | 中长期、定投 |

**Optimized Strategies for 场外基金**:

| Strategy | Frequency | Description |
|----------|-----------|-------------|
| 价值定投 | Monthly | 根据PE分位调整金额，场外基金标配 |
| 移动止盈 | Weekly check | 回撤8%止盈，让利润奔跑 |
| 风险平价 | Quarterly | 波动率倒数配置，降低组合波动 |
| 月度轮动 | Monthly | 改良版动量轮动，考虑赎回费 |
| 周线趋势 | Weekly check | 用周线而非日线，避免噪音 |
| 定期再平衡 | Quarterly | 优先用新资金调仓，省赎回费 |

**Usage**:
```python
from oof_strategies import OOFStrategyEngine

engine = OOFStrategyEngine()

# 价值定投（低估多买）
amount, reason = engine.calculate_value_dca_amount(pe_percentile=25, base_amount=1000)
# → 1500元, "PE分位25.0%，属于低估，定投1.5倍"

# 移动止盈
signal = engine.generate_trailing_stop_signal(
    fund_code="002112",
    current_price=1.05,
    highest_price=1.15,
    cost_price=0.95
)
# → SELL: 从最高点回撤8.7%，触发移动止盈

# 智能定投（估值+趋势）
amount, reason = engine.calculate_smart_dca_amount(
    pe_percentile=20,
    trend_strength=0.3
)
# → 1260元, "估值低估(20%) + 趋势向上 → 1.26倍定投"
```

**Key Optimizations for 场外基金**:
1. ✅ 调仓频率降低（月度而非周度）
2. ✅ 优先用新资金调仓（避免赎回费）
3. ✅ 用周线而非日线判断趋势
4. ✅ 信号延迟确认（避免追高）

See `references/oof-strategy-guide.md` for detailed guide.

### 11. Smart Strategy Engine v3.0 (智能策略引擎)

### 11. Smart Strategy Engine v4.0 (智能策略引擎)

**Updated in v1.8.0**: Unified trailing stop approach, removing fixed stop-profit tiers entirely. Core insight: **all market conditions benefit from trailing stop, fixed tiers create conflicts**.

**v4.0 Key Changes**:
- ❌ Removed: Fixed stop-profit tiers (25%/50%/80%) that conflicted with trailing stop
- ✅ Added: Volatility-adaptive trailing stop (high volatility → larger threshold)
- ✅ Added: Valuation percentile adjustment (high valuation → more sensitive)
- ✅ Added: Portfolio concentration control (single fund max 20-30%)
- ✅ Unified: All market modes use trailing stop only

**Formula**: `final_threshold = base_threshold × volatility_adjustment × valuation_adjustment`
- Volatility adjustment: 0.7-1.5 (based on 30-day std dev)
- Valuation adjustment: 0.8-1.2 (based on percentile in historical range)
- Final threshold clamped to 6%-25%

**Signal Types** (v4.0 simplified):
- `STOP_LOSS`: Hard stop triggered, liquidate immediately
- `TRAILING_STOP`: Drawdown from high triggered, lock profits
- `TRAIL`: Profitable, trailing stop active, keep holding
- `WARNING`: Approaching stop-loss line or concentration limit
- `ALERT`: Weekly drop > 5%
- `HOLD`: No signal triggered

**Usage**:
```python
from smart_strategy_v4 import SmartStrategyEngine

engine = SmartStrategyEngine()

signal = engine.analyze_fund(
    fund_code='020692',
    fund_name='博时通信设备',
    current_nav=3.88,
    cost_nav=2.07,
    highest_nav=3.94,
    holding_days=60,
    weekly_change=-1.5,
    nav_history=navs,  # Required for volatility/valuation adjustment
    portfolio_total=22000,
    fund_value=800,
)
# Returns: TRAIL - "盈利87.5%，移动止盈跟踪中"
# trailing_stop_pct: 6.9% (adjusted for volatility + valuation)
# trigger_nav: 3.6682
```

See `references/smart-strategy-v4.md` for complete implementation.

### 12. Data Cache Layer (数据缓存层)

**New in v1.3.0**: Multi-source data fetching with caching for reliability and speed.

**Features**:
- Multi-level cache: memory + file (TTL: index 2min, industry 10min, NAV 2hr)
- Multi-source fallback: Tencent → Sina auto-switch
- Error retry: exponential backoff
- Cache hit: second fetch < 1ms

**Usage**:
```python
from data_cache import MultiSourceFetcher

fetcher = MultiSourceFetcher()

# Get A-share indices (cached)
indices = fetcher.get_a_share_index()
# → {'上证指数': {'price': 4098.64, 'change_pct': 0.12, 'source': 'tencent'}, ...}

# Get industry data (cached)
industry = fetcher.get_industry_data()
# → {'industries': [...], 'source': 'sina', 'data_type': 'change_pct'}

# Judge market environment
env = fetcher.get_market_env()
# → 'bull' / 'bear' / 'shock'
```

**Cache TTL Settings**:
```python
TTL = {
    'index': 120,        # 指数数据：2分钟
    'industry': 600,     # 行业数据：10分钟
    'fund_nav': 7200,    # 基金净值：2小时
    'fund_info': 86400,  # 基金信息：24小时
    'market': 300,       # 市场概况：5分钟
}
```

See `references/data-cache-layer.md` for implementation details.

### 13. Report Formatter v2.0 (报告分级)

**New in v1.3.0**: Compact and full report formats.

**Compact Report (15 lines)** — MUST include per-fund details in code block, NOT just summary:
```text
📋 投资日报 (2026-05-28)

【指数行情】
📈 上证指数: 4098.64 (+0.12%)
📈 创业板指: 4125.07 (+1.96%)

【行业热点】
🔥 热门: 开发区(+3.8%)、玻璃行业(+3.5%)
❄️ 冷门: 医疗器械(-2.7%)

【持仓概览】
```text
代码      名称              今日收益          持仓盈亏        市值
────────────────────────────────────────────────────────────────
002112  德邦鑫星   +160.90 (2.90%)    +2,265.00    5,548
020692  博时通信    +36.33 (4.77%)      +337.00      762
...
合计                    +276.26 (1.27%)    +2,740.00   21,678
```

【操作建议】
🟡 020692 博时通信: 部分减仓 - 盈利79%

📈 今日整体盈利，市场情绪偏暖
```

**⚠️ Pitfall: Compact format must NOT omit per-fund rows**
- User complaint: "格式不对，数据不全" — compact format only showed summary (total value, best/worst) without individual fund details
- Fix: `format_compact_holdings()` in `report_formatter.py` must include a code-block table with every fund's daily return, profit/loss, and market value
- The summary-only format (just total value + best/worst) is insufficient — users want to see ALL funds at a glance
- Both compact AND full formats must use code blocks (```) with fixed-width alignment

**Full Report (50 lines)**: Complete tables + strategy signals + risk warnings.

**Usage**:
```python
from report_formatter import ReportFormatter

formatter = ReportFormatter()
compact = formatter.generate_compact_report(date, indices, industry, holdings, signals)
full = formatter.generate_full_report(date, indices, industry, holdings, signals)
```

### 14. Market Sentiment (市场情绪)

**New in v1.3.0**: Market breadth and sentiment indicators.

**Features**:
- Up/down stock count ratio
- Sentiment score (0-100)
- Sentiment level (极度悲观 → 极度乐观)

**Usage**:
```python
from market_sentiment import MarketSentiment

sentiment = MarketSentiment()
score = sentiment.get_sentiment_score()
# → {'score': 60, 'level': '偏乐观', 'up_count': 28, 'down_count': 21, 'up_ratio': 57.1}

text = sentiment.format_sentiment(score)
# → "➡️ 市场情绪: 偏乐观 (60分) | 上涨28家 下跌21家"
```

### 15. History Comparison (历史对比)

**New in v1.3.0**: Historical performance comparison.

**Features**:
- Period returns: 1 week / 1 month / 3 months
- Maximum drawdown calculation
- Volatility (daily return std dev)

**Usage**:
```python
from history_comparison import HistoryComparison

comp = HistoryComparison()
ret_1m = comp.get_period_return('002112', 30)  # +2.24%
max_dd = comp.get_max_drawdown('002112', 90)   # -15.17%
vol = comp.get_volatility('002112', 30)         # 2.34%

report = comp.generate_comparison_report('002112', '德邦鑫星')
```

### 14. Intraday Fund Estimates (盘中估值)

**New in v1.7.0**: Real-time estimated NAV during trading hours.

**Data Source**: 天天基金网 JSONP API
- URL: `http://fundgz.1234567.com.cn/js/{fund_code}.js`
- Response: `jsonpgz({"fundcode":"002112","name":"...","gsz":"6.15","gszzl":"0.34","gztime":"2026-05-29 15:00","dwjz":"6.1293","jzrq":"2026-05-28"});`
- Fields: gsz (estimated NAV), gszzl (estimated change %), gztime (estimate time), dwjz (latest NAV), jzrq (NAV date)

**⚠️ Critical Pitfalls**:
1. **DO NOT use `text=True`** in `subprocess.run()` — causes encoding issues with Chinese fund names. Use `capture_output=True` then `result.stdout.decode('utf-8', errors='ignore')`
2. **Regex must use `re.DOTALL`**: `r'jsonpgz\((\{.*?\})\);'` — the JSON may span multiple lines
3. **Exception handling**: Only catch `json.JSONDecodeError, ValueError`, NOT bare `except Exception: continue` — bare except silently swallows ALL errors including the good results
4. **QDII/LOF funds** may return empty data or stale estimates (e.g., 022184 shows 04:00 estimate)

**Display Format** (user preference):
```
代码    名称            净值(日期)    估值(时间)   涨跌%  涨跌额  估算市值
002112  德邦鑫星价.. 6.1293(05-28) 6.1145(10:31)  -0.24%     -14   5,693
```
- `净值(日期)` — latest actual NAV with date (MM-DD)
- `估值(时间)` — estimated NAV with time (HH:MM)
- `涨跌%` — estimated change from NAV
- `涨跌额` — estimated change in ¥ (shares × (est_nav - nav))
- Always show `⏰ 估值时间: YYYY-MM-DD HH:MM` at bottom

See `references/intraday-fund-estimates.md` for API details, pitfalls, and display format.
See `scripts/morning_intraday.py` for implementation.

### 15. Chinese Character Table Alignment (中文表格对齐)

**Pattern**: Use display-width-aware helpers instead of Python's `str.ljust()`/`rjust()`.

```python
def _display_width(self, s: str) -> int:
    """Chinese chars = 2 width, ASCII = 1"""
    width = 0
    for ch in s:
        if '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f' or '\uff00' <= ch <= '\uffef':
            width += 2
        else:
            width += 1
    return width

def _pad(self, s: str, width: int, align='left') -> str:
    """Pad string to display width"""
    dw = self._display_width(s)
    padding = max(0, width - dw)
    if align == 'right':
        return ' ' * padding + s
    else:
        return s + ' ' * padding
```

**Usage**: Always use `self._pad(text, col_width, 'right')` for numeric columns and `self._pad(text, col_width)` for text columns. Define `W_*` constants per column.

**Name truncation**: When truncating fund names, check `self._display_width(name + "..")` not `len(name + "..")`:
```python
if self._display_width(name) > W_NAME:
    while self._display_width(name + "..") > W_NAME and len(name) > 1:
        name = name[:-1]
    name = name + ".."
```

### 16. Market Mainline Tracker (市场主线追踪)

**New in v1.6.0**: Market mainline/theme tracking with holdings alignment.

**Features**:
- Identifies current market mainlines/themes (AI算力, 红利低波, 新能源, 大消费, etc.)
- Tracks hot sectors from industry + concept board data
- Multi-source: EastMoney → Sina fallback (GBK encoding)
- Holdings alignment analysis (which funds are on/off the mainline)
- Daily snapshot persistence for trend tracking
- 7-day theme heat trend with rising/falling indicators

**Theme Categories**:
| Theme | Key Industries | Key Concepts |
|-------|---------------|--------------|
| AI算力 | 电子, 计算机, 通信 | 半导体, AI, 算力, 光模块 |
| 新能源 | 电力设备, 电池 | 光伏, 储能, 锂电 |
| 大消费 | 食品饮料, 医药, 家电 | 白酒, 免税, 酒店 |
| 红利低波 | 银行, 煤炭, 公用事业 | 高股息, 央企 |
| 科技成长 | 通信, 计算机, 军工 | 5G, 物联网, 云计算 |
| 地产基建 | 房地产, 建材, 钢铁 | 水利建设, REITs |
| 畜牧农业 | 农林牧渔 | 猪肉, 生物育种 |

**Data Sources**:
- Industry boards: EastMoney push2 API → Sina Finance (GBK)
- Concept boards: EastMoney push2 API → Sina Finance (GBK)
- Sina concept API: `http://money.finance.sina.com.cn/q/view/newFLJK.php?param=class`

**Usage**:
```python
from market_mainline import MarketMainlineTracker

tracker = MarketMainlineTracker()

# Get hot themes
hot = tracker.get_hot_themes()
# → {'themes': [{'name': '红利低波', 'score': 70, 'level': '🔥 今日主线', ...}], ...}

# Check holdings alignment
alignment = tracker.get_holdings_alignment(hot)
# → {'aligned': [...], 'misaligned': [...], 'aligned_pct': 59}

# Format report
report = tracker.format_mainline_report(hot, alignment)

# Save daily snapshot
tracker.save_daily_snapshot(hot)

# View trend
trend = tracker.format_theme_trend(7)
```

**Integration**: Added to morning and evening reports as 【🧭 市场主线】 section. Snapshots saved automatically.

**Sina Concept Board API** (GBK encoding):
```python
# URL: http://money.finance.sina.com.cn/q/view/newFLJK.php?param=class
# Returns: var S_Finance_bankuai_class = {"key":"code,name,count,...",...}
# Encoding: GBK (NOT UTF-8!)
result.stdout.decode('gbk', errors='ignore')
# Regex: r'"[^"]+":"([^"]+)"'  (generic key pattern, NOT r'"new_\w+":"([^"]+)"')
```

See `references/fund-estimate-api.md` for implementation details.

### 18. Chinese Character Table Alignment (中文表格对齐)

**New in v1.6.0**: Helper methods for aligning tables with Chinese text.

**Problem**: Python's `f"{s:<10}"` counts characters, not display width. Chinese = 2 width units.

**Solution**: `_display_width(s)` and `_pad(s, width, align)` helper methods.

```python
def _display_width(self, s: str) -> int:
    """Chinese chars = 2 width, ASCII = 1 width"""
    width = 0
    for ch in s:
        if '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f' or '\uff00' <= ch <= '\uffef':
            width += 2
        else:
            width += 1
    return width

def _pad(self, s: str, width: int, align='left') -> str:
    dw = self._display_width(s)
    padding = max(0, width - dw)
    return (' ' * padding + s) if align == 'right' else (s + ' ' * padding)
```

**Usage**: Define column widths in display units, use `_pad()` for each cell.

**Pitfalls**:
- Truncating names: use `while self._display_width(name + "..") > W_NAME` loop
- Combined values like `"6.1293(05-28)"` need width = 14 (12 content + 2 padding)
- Always use code blocks for tables, NOT markdown tables

See `references/chinese-table-alignment.md` for full pattern.

**飞书渲染注意**：飞书不渲染 Markdown 表格 `| | |`、标题 `#`、引用块 `>`、分割线 `---`。所有表格必须用代码块包裹。分节线用 `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`。详见 ai-berkshire skill 的 `references/feishu-table-format.md`。

### 17. Adaptive Risk Engine v2.0 (自适应风控)

**Updated in v1.8.1**: Multi-factor risk control with volatility adaptation, valuation percentile, and concentration control.

**Why**: Fixed thresholds ignore industry fundamentals, valuation, and market context. Different fund types need different factor emphasis — tech funds are trend-driven, dividend funds are valuation-anchored.

**6 Factors** (v2.0):
| Factor | Default | Description |
|--------|---------|-------------|
| Profit/Loss | 20% | Current P&L% (extreme profit = risk) |
| Industry Trend | 20% | Industry heat from market mainline tracker |
| Mainline Match | 15% | Is it on the current market mainline? |
| NAV Trend | 20% | NAV vs MA5/MA20 (momentum) |
| Valuation | 25% | NAV position in 90-day range (low = cheap) |
| **Volatility** | - | Adjusts profit/loss score (high vol → more tolerant) |
| **Concentration** | - | Single fund >20% → warning, >30% → reduce |

**v2.0 Key Changes**:
- ✅ Added: Volatility adjustment for profit/loss score (0.8-1.3 multiplier)
- ✅ Added: Valuation percentile adjustment (0.85-1.15 multiplier)
- ✅ Added: Portfolio concentration control with dynamic thresholds
- ✅ Improved: Fund-type-specific weight profiles (tech/dividend/industry/hk)

**Decision Logic** (v2.0 with dynamic thresholds):
- Score ≥ 65 (or 70 if concentration >20%): **持有观望**
- Score 50-65 (or 55 if concentration >20%): **持有+关注**
- Score 35-50 (or 40 if concentration >20%): **考虑减仓**
- Score < 35 (or 40 if concentration >20%): **建议止损/止盈**

**Per-Fund Weight Profiles** (v2.0):
| Profile | 趋势 | 行业 | 估值 | 盈亏 | 主线 | Funds |
|---------|------|------|------|------|------|-------|
| 科技型 `tech` | **30%** | **25%** | 15% | 15% | 15% | 020692, 026211, 027063, 501205 |
| 红利型 `dividend` | 15% | 15% | **35%** | 20% | 15% | 002112, 018388 |
| 行业型 `industry` | 20% | **30%** | 20% | 15% | 15% | 014414 |
| 港股型 `hk` | 15% | **25%** | **30%** | 15% | 15% | 022184 |
| 默认 `default` | 20% | 20% | 25% | 20% | 15% | 005165 |

**Usage**:
```python
from adaptive_risk_v2 import AdaptiveRiskEngine

engine = AdaptiveRiskEngine()
results = engine.analyze_all()  # Uses per-fund weights automatically
print(engine.format_report(results))  # Shows weight profile, volatility, concentration

# Get specific fund's weights
weights = engine.get_weights_for_fund('020692')
# → {'profit_loss': 0.15, 'industry_trend': 0.25, 'nav_trend': 0.30, ...}
```

**Integration** (v1.8.1): `AdaptiveRiskEngine` replaces `SmartStrategyEngine` across ALL report scripts:
- `advisor.py` — morning + evening reports as 【🛡️ 智能风控】
- `morning_intraday.py` — intraday morning report
- `afternoon_intraday.py` — intraday afternoon report

**Report format** (code block):
```
代码      名称           盈亏%    评分    建议          关键原因
──────────────────────────────────────────────────────────────
020692  博时中证全..   +87.5%     32  建议止损/止盈  综合评分32分，风险较高
```
Plus factor detail table with volatility and concentration columns.

See `references/adaptive-risk-backtest.md` for backtest methodology.
See `references/adaptive-risk-data-structure.md` for **analyze_all() return format** and holdings schema pitfalls (⚠️ `code` not `fund_code`, `share_count` not `shares`).
See `references/risk-strategy-optimization.md` for mobile vs fixed stop-profit analysis, volatility-adaptive parameters, and position concentration controls.
See `references/risk-strategy-optimization-v181.md` for v1.8.1 changes: volatility adaptation, valuation percentile, concentration control, migration notes.
See `scripts/adaptive_risk_v2.py` for implementation.

### 18. User Configuration (用户配置)

**New in v1.3.0**: Personalized settings with risk profiles.

**Risk Profiles**:
| Profile | Stop-Profit | Trailing Stop | Hard Stop | Max Single Fund |
|---------|-------------|---------------|-----------|-----------------|
| conservative | 20%/35% | 8% | -12% | 20% |
| balanced | 30%/60%/100% | 12% | -20% | 30% |
| aggressive | 50%/100%/200% | 18% | -30% | 40% |

**Usage**:
```python
from user_config import UserConfig

config = UserConfig.load()  # Load from ~/.hermes/fund-advisor/configs/user_config.json
config.risk_profile = 'conservative'
config.report_format = 'compact'
config.save()

params = config.get_risk_params()
# → {'stop_profit_levels': [(20, 0.5), (35, 1.0)], 'trailing_stop_pct': 8, ...}
```

### 17. Unit Tests (单元测试)

**New in v1.3.0**: 21 test cases covering all core modules.

**Run tests**:
```bash
cd ~/.hermes/fund-advisor/scripts
python3 test_system.py
```

**Coverage**:
- Smart strategy: stop-profit signals, fund type mapping, market environment, signal formatting
- Data cache: read/write, expiry, memory cache
- Report format: compact/full, empty data
- User config: save/load, risk params

---

**Key Learning (2026-05-26)**: Users expect strategy advice to be **integrated into daily reports**, not as standalone modules. Strategies should be actionable within the existing report flow.

**Implementation Pattern**:
```python
# In advisor.py __init__
from oof_strategy_advisor import OOFStrategyAdvisor
self.strategy_advisor = OOFStrategyAdvisor(self.db_path)

# In generate_morning_report()
report.append("\n【📊 场外基金操作建议】")
oof_advice = self.strategy_advisor.generate_daily_strategy_advice()
report.append(oof_advice)
```

**Daily Strategy Advice Includes**:
1. **移动止盈信号** - Check profitable funds for trailing stop triggers
2. **配置建议** - Risk parity rebalancing suggestions
3. **定投建议** - PE-based DCA amount recommendations

**Weekly Strategy Summary**:
```python
# For weekly review integration
summary = self.strategy_advisor.generate_weekly_strategy_summary()
```

**User Feedback**: "策略不应该单独存在，应该集成到日报里自动给出操作建议" - Strategies should not exist in isolation; they should be integrated into reports to provide automatic actionable advice.

---

---

## Output Formatting Best Practices

### Code Block Format for Tables (PREFERRED)

**User Preference**: Use code blocks (```) with fixed-width formatting for ALL fund data displays.

**Why**:
- ✅ Aligns precisely with fixed-width formatting
- ✅ Not truncated in Feishu/Lark or other messaging platforms
- ✅ Easy to copy entire table with one click
- ✅ Shows complete data without rendering issues
- ✅ Chinese characters display correctly in monospace font

**Critical Alignment Pattern**:

```python
# Define column width constants at the start
COL_CODE = 8       # 基金代码
COL_NAME = 18      # 基金名称
COL_SHARES = 12    # 持有份额
COL_NAV_DATE = 10  # 净值日期 (YYYY-MM-DD)
COL_DAILY = 25     # 今日收益（金额 + 比例）
COL_VALUE = 14     # 持仓市值

# Header uses SAME column widths, NO spaces between columns (except after shares)
header = f"{'基金代码':<{COL_CODE}}{'基金名称':<{COL_NAME}}{'持有份额':>{COL_SHARES}} {'净值日期':<{COL_NAV_DATE}}{'今日收益 (%)':>{COL_DAILY}}{'持仓市值':>{COL_VALUE}}"
output.append(header)
output.append("─" * (COL_CODE + COL_NAME + COL_SHARES + COL_NAV_DATE + COL_DAILY + COL_VALUE + 1))  # +1 for space

# Data rows use SAME column widths, with NAV date column
row = f"{code:<{COL_CODE}}{name:<{COL_NAME}}{shares_str} {nav_date_str:<{COL_NAV_DATE}}{daily_str}{value_str}"
output.append(row)
```

**Key Rules**:
1. Always wrap tabular data in ``` code blocks
2. Define column widths as constants (COL_X)
3. Use SAME constants for header AND data rows
4. **NO SPACES between columns** - use column width padding only (except after shares for readability)
5. Include NAV date column for data transparency
6. Separator line: `"-" * (sum of all column widths + 1)` (dynamic, not hardcoded)
7. Include summary statistics (total value, cost, profit/loss)
8. Truncate long fund names: `name[:COL_NAME-2] + ".." if len(name) > COL_NAME`

**Chinese Character Handling**:
- Chinese characters display as 2 English character widths in monospace fonts
- Python's string formatting counts characters, not display width
- Solution: Use consistent column width constants for ALL rows
- **Do NOT add extra spaces between columns** - let column width padding handle alignment
- Test alignment by printing header and first data row side-by-side

**NAV Date Column Best Practices**:
- Use YYYY-MM-DD format (10 characters)
- Left-align dates for consistent display
- Show "N/A" when date is missing
- Each fund may have different NAV date (QDII funds may lag by 1 day)
- Always show actual NAV date, don't assume "today"

**Per-Fund Profit/Loss with Percentage**:
```python
# Calculate individual fund P&L
fund_profit = current_value - cost_value

# Format: "+12.34 (+0.50%)" or "-12.34 (-0.50%)"
if daily_return >= 0:
    daily_str = f"+{daily_return:>.2f} ({daily_return_pct:>.2f}%)"
else:
    daily_str = f"{daily_return:>.2f} ({daily_return_pct:>.2f}%)"

# Right-align within column width
daily_str = daily_str.rjust(COL_DAILY)
```

**Total Daily Return with Percentage**:
```python
# Calculate total daily return percentage
if total_value > 0:
    total_daily_return_pct = (total_daily_return / total_value) * 100
else:
    total_daily_return_pct = 0

# Format: "-57.43 (-0.31%)"
if total_daily_return >= 0:
    summary.append(f"{'📊 今日总收益':<{label_width}} +{total_daily_return:>{value_width-12},.2f} ({total_daily_return_pct:>.2f}%)")
else:
    summary.append(f"{'📊 今日总收益':<{label_width}} {total_daily_return:>{value_width-12},.2f} ({total_daily_return_pct:>.2f}%)")
```

See `references/code-block-formatting.md` for complete examples and column width specifications.
See `references/table-alignment-guide.md` for Chinese character alignment in Feishu/Lark.
See `references/data-validation-and-dates.md` for NAV date marking implementation.

### Legacy Markdown Table Issues

**Problem**: Markdown tables (`| col1 | col2 |`) may be truncated or misaligned in Feishu/Lark.

**Solution**: Use code block format above instead.

See `references/fund-query-display.md` for historical context.

### Templates

- `templates/fund-query-template.py` - Fund holdings query script
- `templates/bulk-import-template.py` - Bulk holdings import script

---

## Backtesting Engine

### Two Approaches

**1. AKShare Real Data Backtesting (RECOMMENDED)**:
```bash
cd ~/.hermes/fund-advisor/scripts
python3 akshare_backtest.py
```
Uses real historical NAV data from AKShare (2500+ records per fund). Compares bull/shock/bear modes.

See `references/akshare-backtest.md` for detailed guide and findings.

**2. Legacy Synthetic Backtesting**:
```python
from backtest_engine import BacktestEngine
engine = BacktestEngine(initial_capital=100000)
result = engine.run_strategy(strategy=my_strategy, fund_codes=['159915'], start_date='2023-01-01', end_date='2024-12-31')
```

### Metrics Tracked

- **Returns**: Total, annualized, benchmark alpha
- **Risk**: Max drawdown, volatility, Sharpe/Sortino ratio
- **Trading**: Win rate, profit factor, turnover rate
- **Stability**: Calmar ratio, consistency

---

## Common Patterns

### Add Fund to Watchlist

Edit `configs/settings.yaml`:

```yaml
watched_funds:
  - code: "159915"
    name: "华夏沪深 300ETF"
    target_weight: 20
```

### Query Transaction History

```bash
sqlite3 data/fund_system.db "
SELECT * FROM transactions 
WHERE trans_date >= date('now', '-30 days')
ORDER BY created_at DESC;
"
```

### Export Holdings to CSV

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/fund_system.db')
df = pd.read_sql_query("SELECT * FROM holdings", conn)
df.to_csv('reports/holdings_export.csv', index=False)
```

### Calculate Shares from Market Value (OCR Workflow)

**Scenario**: User provides portfolio screenshot with market values but no share counts.

**Formula**:
```
shares = market_value / unit_nav
cost_value = market_value - profit_loss
avg_cost = cost_value / shares
```

**Implementation** (`scripts/update_holdings_with_shares.py`):
```python
# Get latest NAV for each fund
cursor.execute('''
    SELECT fund_code, unit_nav 
    FROM fund_nav_history 
    WHERE (fund_code, nav_date) IN (
        SELECT fund_code, MAX(nav_date) 
        FROM fund_nav_history 
        GROUP BY fund_code
    )
''')
nav_data = {row[0]: row[1] for row in cursor.fetchall()}

# Calculate shares from OCR market value
for code, name, market_value, profit_loss, profit_pct in OCR_HOLDINGS:
    if code in nav_data:
        nav = nav_data[code]
        shares = market_value / nav
        cost_value = market_value - profit_loss
        avg_cost = cost_value / shares
```

**⚠️ Pitfalls**:
- QDII funds may have NAV dated 1 day earlier than domestic funds
- Always use each fund's LATEST NAV, not a common date
- Update `current_value` AND `total_invested` in holdings table
- advisor.py must read from holdings table every run, not cached data (否则会显示已清仓的基金)
- DCA cron 切换时必须停掉旧 cron 并建新的，否则简报显示过期定投信息
- 周报 `fund_name` 字段必须从 holdings 表读取，不能用 "基金{code}" 占位
- 月度评估 cron 的 Broken pipe 错误：检查 shell 脚本中是否有管道截断命令

See `references/briefing-audit-fixes.md` for the full audit checklist (P0/P1/P2).
See `references/cron-to-manual-pattern.md` for replacing cron push with manual buttons.

See `scripts/update_holdings_with_shares.py` for complete implementation.

---

## Troubleshooting

### Data Fetching Fails

**Symptom**: API returns 502 or SSL errors

**Root Cause**: Python `requests` library may be blocked by network restrictions, but `curl` works normally.

**Fix**:

1. **Use `curl` instead of `requests`**:

```python
import subprocess
import json

# Instead of requests.get(url)
result = subprocess.run(
    ['curl', '-s', '-A', 'Mozilla/5.0', url],
    capture_output=True,
    text=True,
    timeout=10
)
data = json.loads(result.stdout)
```

2. **Implement Multi-Source Fallback** (RECOMMENDED):

Use `scripts/multi_source_adapter.py` for automatic source switching:

```python
from scripts.multi_source_adapter import MultiSourceAdapter

adapter = MultiSourceAdapter()
indices = adapter.get_a_shares_index()  # Auto-fallback to best source
```

**Data Source Priority**:
- Primary: 腾讯财经 (qt.gtimg.cn) - most stable ✅
- Secondary: 东方财富 (push2.eastmoney.com) - use curl (⚠️ may be blocked by server, returns HTTP 000)
- Fallback: 新浪财经 (hq.sinajs.cn) - last resort

**Industry Data Source Priority** (updated 2026-05-28):
- Primary: 东方财富 push2 API (`fs=m:90+s:4`) - may be blocked from some servers
- Fallback: 新浪财经行业数据 (`vip.stock.finance.sina.com.cn/q/view/newSinaHy.php`) - GBK encoding, returns change% + volume
- See `references/sina-industry-fallback.md` for API details and parsing code
- **Industry Data**: 新浪财经 `http://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php` (returns GBK, see `references/industry-data-api.md`)

**Test network access**:

```bash
# Test with curl (should work)
curl -s 'http://qt.gtimg.cn/q=sh000001'

# Test with Python requests (may fail with 502)
python3 -c "import requests; print(requests.get('http://push2.eastmoney.com/...').status_code)"

# Test push2.eastmoney.com specifically (may return HTTP 000 = blocked)
curl -s -o /dev/null -w '%{http_code}' 'https://push2.eastmoney.com/api/qt/clist/get?fid=f62&po=1&pz=5&pn=1&np=1&fltt=2&invt=2&fs=m:90+s:4&fields=f12,f14,f3'
# If returns 000: server is blocking curl, use Sina fallback
```

**See**: 
- `references/nav-api-troubleshooting.md` for detailed API response parsing
- `references/sina-industry-fallback.md` for Sina industry data as fallback when push2 is blocked
- `scripts/multi_source_adapter.py` for multi-source implementation
- `data-science/china-fund-data/references/multi-source-api-patterns.md` for patterns
if text.startswith('jsonpgz('):
    text = text[8:-2]  # Remove "jsonpgz(" and ");"
data = json.loads(text)
```

6. **⚠️ push2.eastmoney.com may be completely blocked** from some servers (curl returns empty response / exit 52). The Sina Finance API is the recommended fallback for industry data. See `references/sina-industry-data-fallback.md` for implementation details.

5. Try alternative data sources
6. Add retry logic with exponential backoff
7. Use browser tool for web scraping if API fails
8. Cache data locally and update periodically

**See**: 
- `references/nav-api-troubleshooting.md` for detailed API response parsing
- `scripts/multi_source_adapter.py` for multi-source implementation
- `data-science/china-fund-data/references/multi-source-api-patterns.md` for patterns

### Index Data Parsing Issues

**Symptom**: 
- Index change percentages showing impossible values (e.g., "-107.00%")
- Negative percentages when market is up
- Decimal point errors in displayed values

**Root Cause**:
- API response format mismatch (percentage stored as decimal vs. percentage)
- Unit conversion errors (e.g., 0.36 displayed as 36% instead of 0.36%)
- Data source format changes
- Inconsistent handling of `change_pct` values across different methods

**Debugging Steps**:

1. **Check raw API response**:
```bash
# Test index data source
curl -s 'http://qt.gtimg.cn/q=sh000001'
```

2. **Verify parsing logic** in `data_fetcher.py`:
```python
# Common pattern: API returns percentage as decimal (0.36 = 0.36%)
# NOT as 36 (which would be 3600%)
change_pct = data.get('change_pct', 0)
# If API returns 0.36 for 0.36%, display as:
formatted = f"{change_pct:.2f}%"  # Should be "0.36%"
# NOT: f"{change_pct * 100:.2f}%"  # Would be "36.00%"
```

3. **Test with known values**:
```python
# Known test case: 上证指数 at 3000 points, up 10 points = 0.33% change
# API should return: change_pct = 0.33 (decimal)
# NOT: change_pct = 33 (percentage)
```

**Fix Pattern**:
```python
# In advisor.py or data_fetcher.py
if 'change_pct' in data:
    change_pct = data['change_pct']
    # Check if value is too large (>10% change in one day is suspicious)
    if abs(change_pct) > 10:
        # Likely a unit error - divide by 100
        change_pct = change_pct / 100
    pct = f"{change_pct:.2f}%"
```

**Common Data Source Formats**:
- **腾讯财经 (qt.gtimg.cn)**: `change_pct` as decimal (0.36 = 0.36%)
- **东方财富 (push2.eastmoney.com)**: `change_pct` as percentage (36 = 0.36%)
- **新浪财经 (hq.sinajs.cn)**: Varies by endpoint

**Verification**:
```python
# After parsing, verify against known market data
test_cases = {
    'sh000001': {'price_range': (3000, 5000), 'max_daily_change': 0.10},  # 10% max
    'sz399001': {'price_range': (10000, 20000), 'max_daily_change': 0.10},
}
```

**Known Files with This Bug (Fixed)**:
- `morning_intraday.py` line 41: `change_pct * 100` → removed multiplication
- `advisor.py` line 578: `change_pct * 100` → removed multiplication
- `advisor.py` lines 447, 766: previously fixed in v1.1.3

**⚠️ This bug recurs in new scripts. ALWAYS verify when creating or modifying report scripts.**

**See also**: `references/api-encoding.md` for data format specifications

### Cron Job Not Running
   ```
2. Try alternative data sources
3. Add retry logic with exponential backoff
4. Use browser tool for web scraping if API fails
5. Cache data locally and update periodically

**See**: `references/nav-api-troubleshooting.md` for detailed API response parsing and network workarounds

### Cron Job Not Running

**Symptom**: Scheduled report not sent

**Check**:
```bash
# List cron jobs
hermes cron list

# Check job status
hermes cron status

# Test manually
bash scripts/morning_cron.sh
```

**Fix**:
- Verify cron syntax
- Check delivery channel is configured
- Review logs in `logs/` directory

### Cron Report Truncated on Feishu (消息被截断)

**Symptom**: User receives partial report — only first few sections visible, missing strategy advice, action items, risk warnings.

**Root Cause**: `no_agent=true` mode delivers script output as a single message. If output exceeds Feishu's message limit (~4-5KB), it gets silently truncated.

**Detection**:
```bash
# Check output size
wc -c ~/.hermes/cron/output/<job_id>/<latest>.md
# If > 5000 bytes, it will be truncated on Feishu
```

**Fix**: Switch from script-only to agent mode:
1. Delete the job: `hermes cron remove <job_id>`
2. Recreate without `--no-agent true` flag (agent mode is default)
3. Add prompt instructions to split report into multiple messages
4. Include instruction to filter progress logs (✓, 📝, ⚠️, 🔄 lines)

**⚠️ Cannot toggle `no_agent` via update** — must delete and recreate.

**See**: The cron job setup section above for correct agent-mode prompt templates.

### JSONP Parsing Fails (天天基金估值API)

**Symptom**: `get_fund_estimates()` returns 0 results even though API works when called directly.

**Root Cause**: Using `subprocess.run(..., text=True)` causes encoding issues with Chinese characters in fund names.

**Fix**:
```python
# WRONG: text=True causes encoding issues
result = subprocess.run([...], capture_output=True, text=True, timeout=5)

# CORRECT: capture_output=True + manual decode
result = subprocess.run([...], capture_output=True, timeout=5)
text = result.stdout.decode('utf-8', errors='ignore')
```

**Also check**:
- Regex must use `re.DOTALL`: `r'jsonpgz\((\{.*?\})\);'`
- Exception handling: only catch `json.JSONDecodeError, ValueError`, not bare `except Exception: continue`

See `references/fund-estimate-api.md` for full details.

### Report Too Long for Feishu

**Symptom**: Cronjob report truncated or not delivered.

**Fix**: Reports >4000 chars are auto-split at section boundaries using `split_and_print()`. The `---SPLIT---` marker tells the agent to send as 2 messages.

See `references/report-formatting.md` for implementation.

### Sina Concept Board API

**Endpoint**: `http://money.finance.sina.com.cn/q/view/newFLJK.php?param=class`

**Format**: Same as Sina industry boards - GBK encoded JavaScript object.

**Usage**: Fallback for concept board data when EastMoney push2 is blocked.

**Parsing**: Use `_fetch_sina_board()` generic method (same as industry boards).

See `references/fund-estimate-api.md` and `scripts/market_mainline.py` for implementation.

### Cron Script Configuration Pitfalls

**CRITICAL**: Each time-based report must call the CORRECT script. Common misconfiguration:

| Cron Job | Correct Script | Wrong Script |
|----------|---------------|--------------|
| 盘中上午 (10:30) | `morning_intraday.py` | `advisor.py morning` (开盘前报告) |
| 盘中下午 (14:00) | `afternoon_intraday.py` | `morning_intraday.py` |
| 盘后总结 (16:30) | `advisor.py evening` | `advisor.py afternoon` |

**CRITICAL**: Intraday script class/method names must match exactly:

| Script | Class Name | Report Method |
|--------|-----------|---------------|
| `morning_intraday.py` | `IntradayAdvisor` | `generate_intraday_morning_report()` |
| `afternoon_intraday.py` | `AfternoonAdvisor` | `generate_afternoon_report()` |

**⚠️ Common Error**: Using `MorningIntradayReport` or `generate_report()` will crash with ImportError/AttributeError. Always verify actual class/method names before wiring into advisor.py.

**⚠️ Intraday Scripts Must Stay in Sync with advisor.py**:
When adding new analysis modules (止盈止损, 历史收益对比, etc.) to `advisor.py`, the same modules MUST be added to `morning_intraday.py` and `afternoon_intraday.py`. The intraday scripts are standalone — they don't inherit from advisor.py. As of v1.8.0, all three scripts use `AdaptiveRiskEngine` (not `SmartStrategyEngine`).

**Sync checklist when adding a new report section**:
1. Add required imports to the intraday script (`AdaptiveRiskEngine`, `HistoryComparison`, etc.)
2. Initialize new engines in `__init__` (e.g., `self.risk_engine = AdaptiveRiskEngine()`)
3. Copy or adapt the generation method (e.g., `_generate_smart_signals()`, `_generate_history_comparison()`)
4. Add the section to `generate_intraday_morning_report()` / `generate_afternoon_report()`
5. Test: `python scripts/morning_intraday.py 2>&1 | head -80` — verify new section appears

**Sync checklist when REPLACING a module across all scripts** (v1.8.0 lesson):
1. Update the source module first (e.g., `adaptive_risk.py`) — add new features, test standalone
2. Update `advisor.py`: change import, change `__init__`, rewrite the generation method
3. Update `morning_intraday.py`: same 3 changes (import, init, method)
4. Update `afternoon_intraday.py`: same 3 changes
5. **Check for missing utility methods** — if the new code calls `self._display_width()`, verify the target script has it (`advisor.py` lacked it before v1.8.0)
6. Remove dead imports and init lines for the old module
7. Verify `_generate_advice()` keyword matching still works with new output format

**Lesson (2026-05-29)**: advisor.py had 止盈止损监控 and 历史收益对比 since v1.4.0, but intraday scripts were missing them until user complained "还是缺信息呀". Don't assume modules in advisor.py automatically appear in intraday reports.

**⚠️ A股行情 MUST Use Code Block Format**:
- User complaint: "为什么信息不放到代码块" — A股实时行情 was plain bullet points, not a code block table
- Fix: Use same `_pad()` + code block pattern as 持仓估值 section
- Columns: 指数(12) | 最新价(12) | 涨跌%(10) | 涨跌额(12)
- ALL report sections with tabular data must use code blocks — no exceptions

**⚠️ Investment Advice MUST Be Data-Driven, NOT Generic Filler**:
- User complaint: "没有投资建议" — the 投资建议 section was hardcoded generic text like "观察尾盘资金流向", "避免盲目追高杀跌"
- Fix: Implement `_generate_advice(market, sentiment_data, smart_signals_text)` method that generates advice based on actual data:
  1. Market trend: analyze 上证指数 change_pct → judge market condition
  2. Sentiment: use sentiment score → judge crowd psychology
  3. Signals: check smart_signals_text for 止损/止盈 keywords → prioritize actions
  4. Priority: rank as 止损第一 > 止盈第二 > 观望
- Apply to BOTH morning_intraday.py (【📝 操作建议】) and afternoon_intraday.py (【📝 尾盘操作建议】)

**⚠️ Tencent API Field Name: `change` not `change_amt`**:
- `get_a_shares_index()` returns dict with keys: `price`, `change`, `change_pct`
- The field is `change` (not `change_amt`) — using `data.get('change_amt', 0)` silently returns 0
- Always use `data.get('change', 0)` for the price change amount

**⚠️ advisor.py Import/Method Name Pitfalls**:
When adding or modifying intraday report commands in advisor.py, the class and method names must match the actual module definitions:

| advisor.py Command | Correct Import | Correct Method | Common Wrong Names |
|---|---|---|---|
| `morning_intraday` | `IntradayAdvisor` | `generate_intraday_morning_report()` | `MorningIntradayReport`, `generate_report()` |
| `afternoon_intraday` | `AfternoonAdvisor` | `generate_afternoon_report()` | `AfternoonIntradayReport`, `generate_report()` |

**Lesson learned (2026-05-29)**: These import errors are silent until runtime. Always verify class/method names match before committing changes to advisor.py CLI commands.

**⚠️ requests → multi_source_adapter Migration**:
Any script using `requests.get()` for financial data may fail from restricted servers. Replace with:
```python
# BEFORE (may fail with SSL/network errors):
import requests
response = requests.get(url, params=params, timeout=5)

# AFTER (reliable, uses curl under the hood):
from multi_source_adapter import MultiSourceAdapter
adapter = MultiSourceAdapter()
data = adapter.get_a_shares_index()  # or other methods
```

This pattern applies to: `morning_intraday.py`, `afternoon_intraday.py`, and any new report scripts.

**Verification after any cron script change**:
```bash
# Check what each cron script actually calls
cat ~/.hermes/scripts/intra_morning_cron.sh
cat ~/.hermes/scripts/intra_afternoon_cron.sh

# Verify by running manually
cd ~/.hermes/fund-advisor
python scripts/morning_intraday.py 2>&1 | head -5
# Should show "正在生成盘中上午简报", NOT "正在生成开盘前报告"
```

**Symptom of wrong script**: Report title says "开盘前报告" when market is already open, or shows "盘中上午简报" at 2 PM.

### Manual Report Generation

**When to use**:
- User requests "再推送一下" (push again)
- Testing report generation
- Troubleshooting data issues
- Immediate report needed outside scheduled times

**⚠️ Pitfall: Advisor.py import/class name mismatches** (fixed 2026-05-29):
- `morning_intraday.py`: class is `IntradayAdvisor`, method is `generate_intraday_morning_report()`
- `afternoon_intraday.py`: class is `AfternoonAdvisor`, method is `generate_afternoon_report()`
- If you see `ImportError: cannot import name 'MorningIntradayReport'`, check actual class names

**Commands** (unified entry point via advisor.py):
```bash
# Generate morning briefing
cd ~/.hermes/fund-advisor
python scripts/advisor.py morning

# Generate intraday reports
python scripts/advisor.py morning_intraday  # 10:30 AM report
python scripts/advisor.py afternoon_intraday  # 2:00 PM report
python scripts/advisor.py afternoon  # 2:00 PM report (alias)

# Generate evening summary
python scripts/advisor.py evening

# Generate holdings only
python scripts/advisor.py holdings

# Run weekly review
python scripts/advisor.py weekly

# Run monthly evaluation
python scripts/advisor.py monthly

# Update NAV data
python scripts/advisor.py update_nav

# Run investment analysis
python3 scripts/investment_analysis.py
```

**Troubleshooting**:
- If reports show incorrect data, check NAV update status first
- Verify database has recent data: `sqlite3 data/fund_system.db "SELECT MAX(nav_date) FROM fund_nav_history;"`
- For index data issues, test API directly: `curl -s 'http://qt.gtimg.cn/q=sh000001'`

### Database Initialization and Data Update Issues

**Symptom**: 
- Empty database file (0 bytes)
- Missing tables (`fund_nav_history`, `holdings`, etc.)
- NAV data outdated (stale dates)
- Today's收益 shows 0.00 or incorrect values

**Root Cause**:
- Database never initialized after project setup
- NAV update scripts not running regularly
- Cron jobs using stale data

**Fix**:

1. **Initialize database**:
```bash
cd ~/.hermes/fund-advisor/scripts
python db_init.py
```

2. **Update NAV data** (critical for today's returns):
```bash
# Using curl (bypasses network restrictions)
python scripts/update_nav_curl.py

# Verify latest NAV dates
sqlite3 data/fund_system.db "SELECT fund_code, nav_date, unit_nav FROM fund_nav_history ORDER BY nav_date DESC LIMIT 10;"
```

3. **Set up daily NAV update cron job** (SCRIPT-ONLY MODE):
```bash
# Create update script
cat > ~/.hermes/scripts/update-nav-cron.sh << 'EOF'
#!/bin/bash
cd ~/.hermes/fund-advisor
python scripts/update_nav_curl.py 2>&1 | grep -E "更新完成|处理："
EOF
chmod +x ~/.hermes/scripts/update-nav-cron.sh

# Schedule daily at 9:00 AM (after market opens)
hermes cron create "0 9 * * *" \
  "[SILENT]" \
  --name "基金净值每日更新" \
  --script "update-nav-cron.sh" \
  --no-agent true \
  --deliver "local"
```

4. **Verify holdings table**:
```bash
# Check if holdings exist
sqlite3 data/fund_system.db "SELECT COUNT(*) FROM holdings;"

# If empty, import holdings
python scripts/import_holdings.py
```

**⚠️ Critical Notes**:
- QDII funds (like 022184) may have NAV dated 1 day earlier than domestic funds
- Always run NAV update AFTER market close (after 3:00 PM) for accurate daily returns
- Today's收益 in reports uses PREVIOUS trading day's NAV (industry standard)
- For real-time portfolio value, use: `shares * latest_NAV`

**See also**: `references/nav-update-via-curl.md` for detailed NAV update workflow

### Residual Fund Data Cleanup

**Symptom**: Fund appears in `fund_nav_history` but is no longer held (removed from holdings)

**Detection**:
```bash
# Find funds in NAV history but not in holdings
sqlite3 data/fund_system.db "SELECT DISTINCT fund_code FROM fund_nav_history WHERE fund_code NOT IN (SELECT fund_code FROM holdings);"
```

**Fix**:
```bash
# Delete residual NAV data for specific fund
sqlite3 data/fund_system.db "DELETE FROM fund_nav_history WHERE fund_code='159915';"

# Verify cleanup
sqlite3 data/fund_system.db "SELECT COUNT(*) FROM fund_nav_history WHERE fund_code='159915';"
```

**⚠️ Prevention**: When removing a fund, always clean up both `holdings` and `fund_nav_history` tables.

### Future Date Data Issues

**Symptom**:
- Fund NAV data showing future dates (e.g., 2026-05-28, 2026-05-29 when current date is 2026-05-27)
- Reports show incorrect daily returns because they use future NAV data
- User reports positive returns but system shows negative

**Root Cause**:
- API returns incorrect future date NAV data
- `update_nav_curl.py` script inserts future date data without validation
- Database contains corrupted data with future dates

**Detection**:
```bash
# Check for future date data in database
sqlite3 data/fund_system.db "SELECT fund_code, nav_date, unit_nav, daily_return FROM fund_nav_history WHERE nav_date > date('now') ORDER BY nav_date DESC;"

# Check latest NAV dates per fund
sqlite3 data/fund_system.db "SELECT fund_code, MAX(nav_date) as latest_date FROM fund_nav_history GROUP BY fund_code;"
```

**Fix**:
1. **Delete future date data**:
```bash
# Delete all records with future dates
sqlite3 data/fund_system.db "DELETE FROM fund_nav_history WHERE nav_date > date('now');"
```

2. **Re-run NAV update**:
```bash
# Update with correct data
python scripts/update_nav_curl.py
```

3. **Verify fix**:
```bash
# Check that all dates are current or past
sqlite3 data/fund_system.db "SELECT COUNT(*) as future_count FROM fund_nav_history WHERE nav_date > date('now');"
# Should return 0
```

**Prevention**:
- Add data validation step after NAV updates
- Consider adding date validation in `update_nav_curl.py` before insertion
- Set up regular data integrity checks via cron job

**See also**: `references/data-validation-and-dates.md` for comprehensive data validation guide and date marking implementation

### Database Errors

**Symptom**: SQLite errors or corrupted data

**Fix**:
```bash
# Backup current database
cp data/fund_system.db data/fund_system.db.backup

# Reinitialize (WARNING: loses data)
python scripts/db_init.py

# Restore from backup if needed
cp data/fund_system.db.backup data/fund_system.db
```

---

## Best Practices

1. **Data Accuracy**: Cross-validate with multiple sources, note data timestamps
2. **Risk Disclosure**: Always include "not investment advice" disclaimer
3. **Privacy**: Store sensitive data locally, encrypt if needed
4. **Backups**: Daily incremental, weekly full backups
5. **Testing**: Backtest strategies before live use
6. **Documentation**: Keep strategy rules and parameters documented
7. **Compliance**: Understand local financial regulations

---

## Security & Compliance

- ⚠️ **Not Investment Advice**: All outputs are for reference only
- 🔒 **Local Storage**: No cloud upload of portfolio data
- 🔐 **API Keys**: Store in `.env`, never commit to git
- 📋 **Regulations**: Understand local financial advisor requirements
- 🛡️ **Rate Limits**: Respect API rate limits, implement caching

---

## References
- `references/akshare-backtest.md`: AKShare backtesting guide
- `references/adaptive-risk-backtest.md`: Adaptive risk engine backtest results
- `references/adaptive-risk-weights.md`: **NEW** - Per-fund weight profiles design rationale (v1.8.0)
- `references/intraday-fund-estimates.md`: Intraday fund estimate API
- `references/adaptive-risk-engine.md`: **NEW** - Multi-factor risk control design, scoring logic, threshold trigger mechanism (2026-05-29)
- `references/adaptive-risk-data-structure.md`: **NEW** - analyze_all() return format, holdings schema pitfalls (code vs fund_code, share_count vs shares) (2026-05-29)
- `references/risk-strategy-optimization.md`: **NEW** - Mobile vs fixed stop-profit, volatility-adaptive parameters, position concentration control (2026-05-29)
- `references/fund-estimate-api.md`: 天天基金估值API, JSONP parsing pitfalls (2026-05-29)
- `references/report-formatting.md`: **NEW** - Report splitting, Chinese alignment, intraday format (2026-05-29)
- `references/sina-api-patterns.md`: **NEW** - Sina Finance API patterns for industry/concept boards (GBK encoding, field index, parsing code) (2026-05-29)
- `references/smart-strategy-v2.md`: Smart strategy engine v2.0 implementation (now superseded by v3.0)
- `references/system-optimization-roadmap.md`: **NEW** - 系统优化路线图，按优先级分类（P0-P3），包含止盈止损重构、数据源缓存、报告精简等10项优化建议 (2026-05-28)
- `references/sina-industry-fallback.md`: **NEW** - 新浪财经行业数据作为 push2.eastmoney.com 被屏蔽时的 fallback 方案 (2026-05-28)
- `references/data-validation-and-dates.md`: **NEW** - Data validation, future date issues, and NAV date marking implementation (2026-05-27)
- `references/oof-strategy-guide.md`: **NEW** - Comprehensive guide for 场外基金 (OTC fund) strategies, OTC vs ETF differences, and strategy integration patterns (2026-05-26)
- `references/strategy-optimization.md`: **NEW** - Strategy optimization recommendations, enhanced strategy engine documentation, market strategy research (2026-05-26)
- `references/fund-category-analysis.md`: **NEW** - Fund category analysis framework with auto-detection, category-specific thresholds, and analysis dimensions (2026-05-26)
- `references/weekly-review.md`: **NEW** - Weekly strategy review workflow and automated problem detection (2026-05-26)
- `references/weekly-portfolio-analysis.md`: **NEW** - Portfolio-level weekly analysis: total P&L, effective industry exposure, concentration checks (2026-07-05)
- `references/nav-update-daily.md`: **NEW** - Daily NAV update workflow and troubleshooting (2026-05-26)
- `references/index-data-debugging.md`: **NEW** - Complete debugging guide for index data display issues (2026-05-26)
- `references/database-schema.md`: Full database schema and queries
- `references/cron-setup.md`: Cron job configuration and management
- `references/script-only-cronjobs.md`: **MUST READ** - Script-only mode for preserving code block formatting
- `references/screenshot-ocr-workflow.md`: **NEW** - From screenshot OCR to update holdings workflow (2026-05-22)
- `references/screenshot-ocr-holdings-correction.md`: **NEW** - Complete workflow for correcting holdings data from portfolio screenshots using OCR (2026-05-22)
- `references/investment-analysis.md`: **NEW** - Investment analysis workflow, risk assessment, and recommendations (2026-05-22)
- `references/intraday-scripts.md`: 盘中简报脚本 (morning_intraday.py, afternoon_intraday.py)
- `references/investment-strategies.md`: Strategy implementation details
- `references/api-endpoints.md`: Data source API documentation
- `references/risk-metrics.md`: Risk calculation formulas
- `references/fund-query-display.md`: Fund query and display best practices
- `references/code-block-formatting.md`: Code block formatting standards
- `references/table-alignment-guide.md`: **MUST READ** - Chinese character alignment in Feishu/Lark tables
- `references/table-alignment-guide.md`: Column alignment best practices (MUST READ for all table formatting)
- `references/industry-data-api.md`: **UPDATED** - Industry-level data APIs (capital flow, fund holdings) and fallback strategies (now using `fs=m:90+t:2` parameter)
- `references/industry-api-troubleshooting.md`: **NEW** - Industry API parameter failures and troubleshooting (fs=bk deprecated)
- `references/sina-industry-data-fallback.md`: **NEW** - Sina Finance industry data API as fallback when EastMoney push2 is blocked (GBK encoding, parsing)
- `references/nav-update-via-curl.md`: **NEW** - Using curl to fetch fund NAV when requests fails
- `references/network-restrictions-workaround.md`: **NEW** - Complete guide for bypassing network restrictions with curl
- `references/industry-data.md`: **NEW** - Industry capital flow and fund holdings data with fallback strategies
- `references/personalized-strategies.md`: **NEW** - Personalized per-fund strategy recommendations (2026-05-21)
- `templates/report-template.html`: HTML report template
- `templates/fund-query-template.py`: Fund holdings query script template
- `templates/bulk-import-template.py`: Bulk holdings import script template
- `scripts/setup-cron.sh`: Cron job setup helper
- `templates/bulk-import-template.py`: Bulk holdings import script template
- `scripts/update_nav_curl.py`: NAV update script using curl (bypasses network restrictions)
- `scripts/weekly_review.py`: **NEW** - Weekly strategy review engine with problem detection and optimization suggestions (2026-05-26)
- `scripts/fund_categorizer.py`: **NEW** - Fund category auto-detection module based on fund name keywords (2026-05-26)
- `scripts/generate_current_week_data.py`: **NEW** - Generate current week NAV data for testing (2026-05-26)
- `configs/fund_categories.yaml`: **NEW** - Fund category configuration with keywords, thresholds, and analysis dimensions (2026-05-26)
- `scripts/validate_nav_data.py`: **NEW** - Data validation script for NAV consistency and integrity checks (2026-05-26)
- `scripts/smart_strategy.py`: **NEW** - Smart strategy engine v3.0 with bull/shock/bear market modes, fund-type differentiation, trailing stop (2026-05-28)
- `scripts/data_cache.py`: **NEW** - Multi-source data fetching with memory+file caching, TTL, fallback (2026-05-28)
- `scripts/report_formatter.py`: **NEW** - Compact (15 lines) and full (50 lines) report formats (2026-05-28)
- `scripts/market_sentiment.py`: **NEW** - Market breadth and sentiment indicators (up/down ratio, score 0-100) (2026-05-28)
- `scripts/history_comparison.py`: **NEW** - Period returns (1w/1m/3m), max drawdown, volatility (2026-05-28)
- `scripts/user_config.py`: **NEW** - User configuration with risk profiles (conservative/balanced/aggressive) (2026-05-28)
- `scripts/akshare_backtest.py`: **NEW** - AKShare-based backtesting engine with real historical data (2026-05-28)
- `scripts/test_system.py`: **NEW** - 21 unit tests covering all core modules (2026-05-28)
- `scripts/market_mainline.py`: **NEW** - Market mainline/theme tracking with holdings alignment (2026-05-29)
- `scripts/adaptive_risk.py`: **NEW** - Multi-factor adaptive risk control engine (2026-05-29)
- `scripts/backtest_risk.py`: **NEW** - Risk strategy backtest: adaptive vs fixed threshold comparison (2026-05-29)
- `references/fund-estimate-api.md`: **NEW** - Fund estimate API (天天基金网) with JSONP parsing pitfalls (2026-05-29)
- `references/chinese-table-alignment.md`: **NEW** - Chinese character table alignment in Python (2026-05-29)
- `configs/fund_categories.yaml`: **NEW** - Fund category configuration with keywords
- `references/market-mainline-tracker.md`: **NEW** - Market mainline tracker implementation details (2026-05-29)
- `scripts/test_industry_data.py`: **NEW** - Test industry data source availability (EastMoney push2, Sina, Tencent)
- `scripts/market_mainline.py`: **NEW** - Market mainline/theme tracking with holdings alignment (2026-05-29)
- `scripts/investment_analysis.py`: **NEW** - Investment analysis script with portfolio analysis and recommendations (2026-05-22)
- `scripts/update_holdings_with_shares.py`: **NEW** - Calculate and update shares from NAV when only market value is known (2026-05-22)
- `scripts/enhanced_strategies.py`: **NEW** - Enhanced strategy engine with 8 market-proven strategies (Value DCA, Grid Trading, Trend Following, Momentum Rotation, Risk Parity, Trailing Stop, Core-Satellite, Dual MA) (2026-05-26)
- `references/strategy-optimization.md`: **NEW** - Strategy optimization recommendations based on market research, comparing current vs. best practices (2026-05-26)
- `scripts/setup-cron.sh`: Cron job setup helper

---

## Related Tools

- **Hermes cronjob**: Schedule automated reports
- **Python**: Data processing and analysis
- **SQLite**: Local database
- **Feishu/Telegram**: Message delivery
- **Plotly**: Interactive charts (optional)
- **multi_source_adapter**: Multi-source API adapter with auto fallback (2026-05-20)

---

## Version History

**2.2.1** (2026-07-05) - Weekly Portfolio-Level Analysis Supplement
- **NEW**: `scripts/weekly_portfolio_analysis.py` - Portfolio-level weekly analysis script
  - Computes total weekly P&L in ¥ and % (not in built-in `weekly_review.py`)
  - Effective industry exposure: cross-fund weighted industry allocation
  - Position concentration check vs risk profile limits (20%/30%)
  - Industry overlap detection (hidden concentration across funds)
- **NEW**: `references/weekly-portfolio-analysis.md` - Usage guide and findings
- **Key Insight**: The built-in `weekly_review.py` only does per-fund analysis. It missed a critical hidden concentration: 46.9% of the portfolio was exposed to tech/semiconductor across 6 funds, but no single fund looked extreme. This only surfaces when weighting industry allocations by portfolio position.
- **Key Insight**: The adaptive risk engine's "盈亏" (profit/loss) factor scores high profit as LOW risk, but at extreme profit levels (+60%, +84%), the risk of profit giveback is actually HIGH. Large weekly drawdowns on high-profit funds (-11%, -10%) eroded significant unrealized gains.
- **Usage**: Run AFTER `weekly_review.py` — the built-in answers "which funds did well/badly?", the supplement answers "how did the PORTFOLIO do, and where are the hidden risks?"

**2.2.0** (2026-05-29) - see skill description above

**1.8.1** (2026-05-29) - MAJOR: Risk Strategy Optimization v2.0
- **NEW**: `smart_strategy_v4.py` - Unified trailing stop, removed fixed stop-profit tiers
  - ❌ Removed: Fixed stop-profit tiers (25%/50%/80%) that conflicted with trailing stop
  - ✅ Added: Volatility-adaptive trailing stop (high volatility → larger threshold)
  - ✅ Added: Valuation percentile adjustment (high valuation → more sensitive)
  - ✅ Added: Portfolio concentration control (single fund max 20-30%)
  - ✅ Unified: All market modes use trailing stop only
  - Formula: `final_threshold = base_threshold × volatility_adjustment × valuation_adjustment`
  - Final threshold clamped to 6%-25%
- **NEW**: `adaptive_risk_v2.py` - Enhanced multi-factor risk control
  - ✅ Added: Volatility adjustment for profit/loss score (0.8-1.3 multiplier)
  - ✅ Added: Valuation percentile adjustment (0.85-1.15 multiplier)
  - ✅ Added: Portfolio concentration control with dynamic thresholds
  - ✅ Added: Fund-type-specific weight profiles (tech/dividend/industry/hk)
  - ✅ Dynamic thresholds: concentration >20% → stricter (hold 65→70, reduce 35→40)
- **UPDATED**: `advisor.py`, `morning_intraday.py`, `afternoon_intraday.py`
  - Import changed: `from adaptive_risk_v2 import AdaptiveRiskEngine`
  - All report scripts now use v2.0 risk engine
- **NEW**: `references/risk-strategy-optimization-v181.md` - Implementation details and migration notes
- **Key Learning**: Fixed stop-profit tiers conflict with trailing stop (e.g., 020692 +87.5%: fixed says "sell all", trailing says "keep holding"). Unified trailing stop resolves this conflict.

**1.8.0** (2026-05-29) - MAJOR: Adaptive Risk Engine Integration
- **FIX**: A股实时行情 was plain bullet points, now uses code block table format
  - User complaint: "为什么信息不放到代码块"
  - Added table with columns: 指数(12) | 最新价(12) | 涨跌%(10) | 涨跌额(12)
  - Applied to both morning_intraday.py and afternoon_intraday.py
- **FIX**: Investment advice was generic filler text, now data-driven
  - User complaint: "没有投资建议"
  - New method `_generate_advice(market, sentiment_data, smart_signals_text)`
  - Advice based on: market trend (上证涨跌) + sentiment score + signal keywords
  - Action priority: 止损第一 > 止盈第二 > 观望
- **FIX**: Tencent API field name `change_amt` → `change` (was silently returning 0)
- **UPDATED**: `references/intraday-scripts.md` — complete rewrite with all 7 sections, code block patterns, and _generate_advice template

**1.6.3** (2026-05-29) - Intraday Reports: Added 止盈止损监控 + 历史收益对比
- **FIX**: `morning_intraday.py` and `afternoon_intraday.py` were missing 止盈止损监控 (🛡️) and 历史收益对比 (📈) sections that advisor.py had since v1.4.0
- **Root cause**: Intraday scripts are standalone — they don't inherit from advisor.py. New modules must be explicitly added to each script.
- **Added to both scripts**:
  - Imports: `SmartStrategyEngine`, `MarketEnv`, `HistoryComparison`
  - Methods: `_generate_smart_signals()`, `_generate_history_comparison()`
  - Report sections: 【🛡️ 止盈止损监控】 and 【📈 历史收益对比】
- **New pitfall documented**: "Intraday Scripts Must Stay in Sync with advisor.py" — sync checklist added
- **Lesson**: User reported "还是缺信息呀" — don't assume modules in advisor.py automatically appear in intraday reports

**1.6.2** (2026-05-29) - CRON: Switched from script-only to agent mode
- **BREAKING**: All fund advisor cron jobs switched from `no_agent=true` to agent mode (`no_agent=false`)
- **Root cause**: Script-only mode delivered 10-15KB output as single Feishu message, causing silent truncation
- **Fix**: Agent mode filters progress logs (✓, 📝, ⚠️, 🔄 lines) and splits reports into 2-3 messages
- **Lesson**: `no_agent=true` works for short outputs (<4KB) but MUST NOT be used for long reports on Feishu
- **Lesson**: `no_agent` field cannot be toggled via `cronjob update` — must delete and recreate
- Updated: Cron job setup section with agent-mode prompt templates
- Updated: Troubleshooting section with truncation detection and fix

**1.6.1** (2026-05-29) - Intraday Report: Estimated NAV + Bug Fixes
- **NEW**: `morning_intraday.py` - Added `get_fund_estimates()` method for real-time estimated NAV
  - API: `http://fundgz.1234567.com.cn/js/{fund_code}.js` (天天基金网)
  - Returns JSONP: gsz (estimated NAV), gszzl (est. change%), gztime, dwjz (latest NAV), jzrq
  - QDII funds (022184) and LOF funds (501205) have no intraday estimate → show "—"
- **REWRITTEN**: `get_holdings_summary()` now shows 7-column table: 代码/名称/净值/日期/估值/估值涨跌/估算市值
- **FIXED**: `advisor.py` import errors — `MorningIntradayReport` → `IntradayAdvisor`, `AfternoonIntradayReport` → `AfternoonAdvisor`
- **FIXED**: Method name mismatches — `generate_report()` → `generate_intraday_morning_report()` / `generate_afternoon_report()`
- **FIXED**: Both intraday scripts now use `MultiSourceAdapter` instead of `requests`
- **NEW**: `_display_width()` and `_pad()` helpers for Chinese character table alignment
- **NEW**: `references/fund-estimate-api.md`, `references/chinese-table-alignment.md`

**1.6.1** (2026-05-29) - Fund Estimate API + Intraday Report Enhancement — see 1.6.1 entry above (consolidated to avoid duplication)

**1.8.0** (2026-05-29) - MAJOR: Adaptive Risk in Intraday Reports + Per-Fund Weights
- **BREAKING**: `SmartStrategyEngine` fully replaced by `AdaptiveRiskEngine` across ALL report scripts
  - `advisor.py`, `morning_intraday.py`, `afternoon_intraday.py` — all updated
  - Import: `from smart_strategy import SmartStrategyEngine, MarketEnv` → `from adaptive_risk import AdaptiveRiskEngine`
  - Init: `self.smart_engine = SmartStrategyEngine(MarketEnv.SHOCK)` → `self.risk_engine = AdaptiveRiskEngine()`
  - Method: `_generate_smart_signals()` rewritten to use `self.risk_engine.analyze_all()`
- **NEW**: Per-fund differentiated weight profiles in `adaptive_risk.py`
  - `FUND_WEIGHT_PROFILES`: 5 profiles (tech, dividend, industry, hk, default)
  - `FUND_WEIGHT_MAP`: Maps each of 9 funds to its profile
  - `get_weights_for_fund(code)`: Returns weights for a specific fund
  - Science: tech funds weight `nav_trend` at 30%, dividend funds weight `valuation` at 35%
- **FIX**: `advisor.py` was missing `_display_width()` method — added it (required by new `_generate_smart_signals`)
- **FIX**: Dead `SmartStrategyEngine` import/init removed from `advisor.py`
- **Report format**: Table now shows 代码/名称/盈亏%/评分/建议/关键原因 (replaces old 操作/紧急/原因)
- **Report format**: Factor detail table now shows weight profile label (科技型/红利型/etc.)
- **NEW**: `references/adaptive-risk-weights.md` — weight design rationale per fund type
- **PITFALL**: When replacing a module across 3+ scripts, verify each target has all required utility methods. `advisor.py` lacked `_display_width()` which the new code needed.

**1.8.1** (2026-05-29) - Adaptive Risk Engine: Data Structure Documentation + Risk Strategy Optimization
- **NEW**: `references/adaptive-risk-data-structure.md` - Documented `analyze_all()` return format
  - ⚠️ Key is `code` not `fund_code` (causes KeyError if wrong)
  - ⚠️ Holdings table column is `share_count` not `shares` (causes OperationalError)
  - Full field list with types and descriptions
- **NEW**: `references/risk-strategy-optimization.md` - Risk strategy optimization framework
  - Mobile vs fixed stop-profit analysis (conflict resolution)
  - Volatility-adaptive stop-profit parameters
  - Valuation percentile-based adjustments
  - Position concentration control (max 20% per fund)
  - Dynamic market environment judgment
  - Implementation priority (P0-P4)
  - Calculation examples for 020692
- **Lesson**: When using adaptive_risk.py, always use `r['code']` not `r['fund_code']`
- **Lesson**: Holdings table uses `share_count`, not `shares` - check schema before querying

**1.8.0** (2026-05-29) - MAJOR: Adaptive Risk + Intraday Estimates + Report Splitting (consolidated; see 1.8.0 entry above for full details)

**1.6.0** (2026-05-29) - Market Mainline Tracker (consolidated; see 1.6.0 entry above)

**1.5.0** (2026-05-28) - MAJOR: Smart Strategy v3.0 + AKShare Backtesting
- **STRATEGY**: Smart Strategy Engine v3.0 with three market modes
  - Bull mode: NO fixed take-profit tiers, only trailing stop (let profits run)
  - Shock mode: Tiered take-profit (25%/50%/80%) + trailing stop
  - Bear mode: Quick lock (15%/30%/50%) + tight trailing stop
  - Key insight validated by AKShare backtesting: tiered take-profit sells too early in bull markets
- **BACKTEST**: AKShare-based backtesting engine (`akshare_backtest.py`)
  - Real historical NAV data (2500+ records per fund)
  - Three-mode comparison over 2 years
  - Result: Bull mode captured +104% on best fund vs +31% for shock mode
- **NEW**: `references/akshare-backtest.md` - AKShare backtesting guide with API details and findings
- Updated: `smart_strategy.py` v3.0 with MarketEnv-aware logic
- Updated: Fund type parameters with trailing_start, trailing_stop_pct, hard_stop_pct, shock_levels, bear_levels

**1.4.0** (2026-05-28) - MAJOR: Full Integration of All New Modules
- **INTEGRATED**: All v1.3.0 standalone modules now wired into advisor.py report flow
- **advisor.py**: Added imports for SmartStrategyEngine, MarketSentiment, HistoryComparison, UserConfig
- **advisor.py `__init__`**: Initializes smart_engine, sentiment, history, user_config
- **Morning Report**: Added 🌡️ 市场情绪 section + 🛡️ 止盈止损监控 section
- **Evening Report**: Added 🌡️ 市场情绪 + 📈 历史收益对比 (1周/1月/3月+最大回撤) + 🛡️ 止盈止损监控
- **New Method `_generate_smart_signals()`**: Per-fund smart strategy analysis using SmartStrategyEngine
  - Queries latest NAV, highest NAV, holding days, weekly change
  - Only shows actionable signals (skips HOLD)
  - Displays: code, name, action, urgency, reason
- **New Method `_generate_history_comparison()`**: 1-week/1-month/3-month returns + max drawdown table
- **Fixed**: test_system.py test_compact_report assertion ('总市值' → '市值')
- **All 21 tests passing**

**1.3.1** (2026-05-28) - FIX: Compact report format
- Fixed: `format_compact_holdings()` in `report_formatter.py` — now includes per-fund details in code block table
- Was: Only showed summary stats (total value, best/worst) — user reported "格式不对，数据不全"
- Now: Full code-block table with every fund's daily return (+amount +%), profit/loss, and market value
- Both compact and full formats use consistent code-block fixed-width alignment

**1.3.0** (2026-05-28) - MAJOR: Smart Strategy v2.0
- **NEW**: Smart Strategy Engine (`smart_strategy.py`) - complete rewrite of stop-profit/stop-loss
  - Tiered stop-profit per fund type (industry ETF: 25%/45%/70%, tech: 40%/80%/120%)
  - Trailing stop from highest price (8-15% drawdown depending on fund type)
  - Hard stop-loss (-15% to -25% depending on fund type)
  - Market environment adaptation (bull/bear/shock)
  - Weekly drop alert (>5%)
- **NEW**: Data Cache Layer (`data_cache.py`) - multi-source with caching
  - Multi-level cache: memory + file, TTL per data type
  - Multi-source fallback: Tencent → Sina for indices
  - Sina industry data as fallback when EastMoney push2 blocked
  - Exponential backoff retry
- **NEW**: Report Formatter (`report_formatter.py`) - compact (15 lines) and full (50 lines) formats
- **NEW**: Market Sentiment (`market_sentiment.py`) - up/down ratio, sentiment score 0-100
- **NEW**: History Comparison (`history_comparison.py`) - period returns, max drawdown, volatility
- **NEW**: User Configuration (`user_config.py`) - risk profiles (conservative/balanced/aggressive)
- **NEW**: Unit Tests (`test_system.py`) - 21 tests covering all core modules, all passing
- Fixed: Tiered stop-profit bug - must find HIGHEST matching tier, not first
- Updated: advisor.py unified entry point with all commands

**1.2.7** (2026-05-28)
- Fixed: Industry capital flow data - EastMoney push2.eastmoney.com API blocked from server (curl exit 52)
- Added: Sina Finance industry data fallback (`http://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php`)
- Added: `references/sina-industry-data-fallback.md` - complete guide for Sina API parsing (GBK encoding, JavaScript variable format)
- Added: `_fetch_sina_industry_data()` method in `data_fetcher.py` as automatic fallback
- Updated: `_format_capital_flow_summary()` in `advisor.py` to handle both capital flow and change_pct data types
- Fixed: NAV update cron job - replaced unreliable inline script with proper script file (`~/.hermes/scripts/update-nav-cron.sh`)
- Added: Residual fund data cleanup troubleshooting guide
- Added: Warning about inline cron scripts being unreliable - always use proper script files
- Cleaned: Removed 159915 residual data from `fund_nav_history` (2 records)
- Note: Sina data provides industry change% and trading volume, not capital flow - display format adapts automatically

**1.2.6** (2026-05-28)
- Fixed: `intra_morning_cron.sh` was calling `advisor.py morning` (pre-market) instead of `morning_intraday.py` (intraday)
- Fixed: `change_pct * 100` bug in `morning_intraday.py` line 41 and `advisor.py` line 578
- Created: `intra_afternoon_cron.sh` - separate script for afternoon intraday report
- Updated: Afternoon cron job to use correct script
- Added: Cron script configuration pitfalls documentation (which script to call for each time slot)
- Added: Known files with change_pct bug list (prevents recurrence)

**1.2.6** (2026-05-28)
- Fixed: 行业资金流向数据获取失败 - 东方财富 push2 API 被服务器屏蔽（HTTP 000）
- Added: 新浪财经行业数据作为 fallback（49个行业涨跌幅+成交额）
- Added: `references/sina-industry-fallback.md` - Sina API 解析代码和字段说明
- Fixed: 净值更新 cron 任务 - 从内联脚本改为独立脚本文件
- Fixed: 159915 残留数据清理（2条记录）
- Added: advisor.py 统一入口 - 新增 morning_intraday/afternoon_intraday/weekly/monthly/update_nav 命令
- Added: `references/system-optimization-roadmap.md` - 系统优化路线图（P0-P3优先级）
- Tested: 周复盘和月评估脚本正常运行
- Updated: `_format_capital_flow_summary()` 支持两种数据源格式（资金流向/涨跌幅）

**1.2.5** (2026-05-27)
- Added: Data validation for future date NAV data issues
- Added: `references/data-validation-and-dates.md` comprehensive guide for data integrity
- Added: NAV date column in portfolio overview display (COL_NAV_DATE = 10)
- Fixed: Future date data cleanup procedure (DELETE FROM fund_nav_history WHERE nav_date > date('now'))
- Added: Data freshness indicator showing how many days old NAV data is
- Enhanced: Table formatting with NAV date column for better data transparency
- User request: "请标记数据时间" - now each fund shows its NAV date alongside returns
- Issue: API sometimes returns future dates (e.g., 2026-05-28 when current date is 2026-05-27)
- Solution: Added validation steps and cleanup procedures in troubleshooting guide

**1.2.4** (2026-05-26)
- Added: OOF Strategy Engine (`scripts/oof_strategies.py`) for 场外基金 specifically
- Added: `oof_strategy_advisor.py` - Integrates strategy advice into daily reports
- Key learning: Strategies should be INTEGRATED into daily reports, not standalone
- Optimized strategies for 场外基金 (OTC funds):
  - Reduced trading frequency (monthly not weekly for adjustments)
  - Use new funds first for rebalancing (avoid redemption fees)
  - Use weekly chart instead of daily for trend signals
  - Trailing stop with 8% drawdown from highest price
- Added 6 OTC-optimized strategies: Value DCA, Trailing Stop, Risk Parity, Monthly Rotation, Weekly Trend, Smart DCA
- Added: `references/oof-strategy-guide.md` - Comprehensive guide for OTC fund strategies

**1.2.3** (2026-05-26)
- Added: Enhanced strategy engine (`scripts/enhanced_strategies.py`) with 8 market-proven strategies
- Added: Value DCA strategy with PE percentile-based dynamic investment amounts
- Added: Grid Trading strategy for range-bound markets
- Added: Trend Following strategy with MA20/MA60 crossover
- Added: Momentum Rotation strategy for sector rotation
- Added: Risk Parity strategy for equal risk contribution weighting
- Added: Trailing Stop strategy (replaces fixed take-profit) - tracks highest price, exits on 8% drawdown
- Added: Core-Satellite strategy (70% core + 30% satellite allocation)
- Added: Dual MA timing strategy (MA5/MA20 crossover)
- Added: `references/strategy-optimization.md` - Strategy comparison and optimization recommendations
- Key insight: Trailing stop > fixed take-profit (30%+ more profit in trending markets)
- Key insight: Risk parity > equal weighting (20-30% lower volatility)

**1.2.2** (2026-05-26)
- Added: Fund category analysis framework with auto-detection
- Added: `scripts/fund_categorizer.py` - Auto-categorize funds based on name keywords
- Added: `configs/fund_categories.yaml` - Category configuration (5 categories: 行业指数, 港股/海外, 科技主题, 灵活配置, 创新成长)
- Added: `references/fund-category-analysis.md` - Detailed category analysis documentation
- Enhanced: Weekly review now uses category-specific thresholds (different stop-loss/take-profit per category)
- Enhanced: Problem detection is now category-aware (e.g., tech funds have higher vol tolerance)
- Features: New funds are automatically categorized based on name keywords
- Features: Each category has unique analysis dimensions (e.g., HK funds focus on exchange rate, flexible funds focus on manager)

**1.2.1** (2026-05-26)
- Added: Weekly strategy review system with automated problem detection
- Added: `weekly_review.py` - Weekly performance analysis engine
- Added: `references/weekly-review.md` - Weekly review workflow documentation
- Features: Weekly return, volatility, max drawdown, win rate analysis
- Features: Problem detection (return issues, high volatility, excessive drawdown, low win rate, concentration)
- Features: Optimization suggestions (take profit, stop loss, position adjustment, strategy tuning)
- CRON: Set up weekly review job every Sunday at 8:00 PM

**1.1.3** (2026-05-26)
- Fixed: Index data display error where `change_pct` was incorrectly multiplied by 100
- Added: Specific bug fix documentation for inconsistent `change_pct` handling in `advisor.py`
- Location: Lines 447 and 766 in `advisor.py` (generate_afternoon_intraday and generate_evening_summary methods)
- Impact: Index percentages now show correctly (e.g., -0.80% instead of -80.00%)

**1.1.2** (2026-05-26)
- Added: Database initialization and NAV update troubleshooting section
- Added: Index data parsing issues troubleshooting section  
- Added: Daily NAV update cron job setup instructions
- Fixed: Database initialization workflow for new setups
- Fixed: NAV data staleness detection and update procedures
- Updated: Troubleshooting section with common database and data issues

**1.1.1** (2026-05-25)
- Fixed: Industry capital flow API parameter from deprecated `fs=bk` to `fs=m:90+t:2` (申万行业分类)
- Fixed: `fs=bk` parameter returns rc:102 error - API deprecated
- Added: `references/industry-api-troubleshooting.md` for API parameter changes and troubleshooting
- Updated: SKILL.md and all related documentation with correct API parameters
- Verified: System now successfully fetches 50 industry capital flow data points

**1.1.0** (2026-05-22)
- Added investment analysis script (`scripts/investment_analysis.py`)
- Added investment analysis workflow document (`references/investment-analysis.md`)
- Added share calculation from NAV script (`scripts/update_holdings_with_shares.py`)
- Features:
  - Total performance analysis (total value, profit/loss, daily return)
  - Profit ranking (sorted by total profit)
  - Loss fund analysis with suggestions
  - Industry allocation analysis
  - Portfolio concentration analysis
  - Risk assessment (max drawdown, industry concentration)
  - Investment suggestions (take profit, stop loss, rebalancing)
  - **NEW**: Calculate shares from market value when only OCR data is available
- Screenshot OCR workflow improvements

**1.0.1** (2026-05-21)
- Added industry-level capital flow data (主力资金流向 - 行业级别)
- Added fund industry allocation display (基金行业配置)
- Added personalized strategy suggestions based on industry trends
- Fixed: Capital flow API parameter (`fs=bk` for industries, not `fs=m:0+t:6` for stocks)
- Added: Fund holdings API with name-based inference fallback
- Fixed: All cron jobs now use script-only mode to preserve code block formatting

**1.0.0** (2026-05-16)
- Initial implementation
- Core features: data fetching, portfolio tracking, reports
- Basic strategies: DCA, rebalancing, stop-profit
- Cron job integration
- SQLite database schema
