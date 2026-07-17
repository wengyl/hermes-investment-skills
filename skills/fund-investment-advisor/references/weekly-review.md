# Weekly Review Workflow (周度复盘工作流)

## Overview (概述)

This document outlines the weekly strategy review workflow for the fund investment advisor system.

## Schedule (时间安排)

- **Every Sunday at 8:00 PM**: Automated weekly review runs
- **Analysis Period**: Monday to Friday of the current week
- **Review Categories**: Performance, problems, optimizations

## Review Process (复盘流程)

### 1. Data Collection (数据收集)

The weekly review automatically collects:
- Daily NAV data for all funds in the current week
- Performance metrics (returns, volatility, drawdowns)
- Trading day counts and win rates

### 2. Performance Analysis (表现分析)

**Metrics Calculated**:
- **Weekly Return**: Total return for the week
- **Volatility**: Standard deviation of daily returns
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of positive trading days
- **Trading Days**: Number of active trading days

**Ranking System**:
- Funds ranked by weekly return (highest to lowest)
- Performance tiers identified
- Outliers flagged for attention

### 3. Problem Identification (问题识别)

**Automated Detection**:

| Problem Type | Severity | Threshold | Suggested Action |
|-------------|----------|-----------|------------------|
| 收益问题 (Return Issues) | High | Weekly loss > 3% | Analyze causes, consider position adjustment |
| 波动率过高 (High Volatility) | Medium | Volatility > 3% | Apply stricter stop-loss strategies |
| 回撤过大 (Excessive Drawdown) | High | Drawdown > 5% | Check stop-loss settings, reduce positions |
| 胜率过低 (Low Win Rate) | Medium | Win rate < 30% | Consider fund replacement |
| 持仓集中度 (Concentration) | Medium | Top 3 funds > 70% | Diversify portfolio |

### 4. Optimization Suggestions (优化建议)

**Priority Levels**:
- **High**: Immediate action required
- **Medium**: Should address this week
- **Low**: Monitor and consider

**Common Suggestions**:
1. **止盈建议** - Take profits on funds with > 5% weekly gains
2. **止损建议** - Stop loss on funds with > 5% weekly losses
3. **仓位调整** - Reduce positions in high-volatility funds
4. **持仓优化** - Replace funds with consistently poor performance
5. **行业配置** - Ensure no industry > 30% of portfolio
6. **策略参数** - Adjust take-profit/stop-loss thresholds

### 5. Report Generation (报告生成)

**Output Format (Console)**:
- Code block table with per-fund detail rows
- One row per fund, NOT a rollup summary
- File storage for historical reference (JSON)

**Required Columns (每只基金一行)**:

| Column | Example | Description |
|--------|---------|-------------|
| 代码 (code) | `002112` | Fund code |
| 名称 (name) | `德邦鑫星价值` | Fund name (truncated to ~8 chars if needed) |
| 周收益率% | `+1.23%` / `-0.45%` | After split detection correction |
| 周盈亏¥ | `+¥1,234` / `-¥567` | Absolute P&L in yuan |
| 仓位% | `15.3%` | Position ratio of total portfolio |
| 累计盈亏% | `+8.7%` | Cumulative return since purchase |

**Table rendering** (中文对齐，等宽字体):
```text
代码    名称        周收益率  周盈亏(¥)  仓位%   累计盈亏
─────────────────────────────────────────────────────────
002112  德邦鑫星..  +1.23%   +1,234    15.3%   +8.7%
005165  富荣福锦..  -0.45%     -567    12.1%   +3.2%
```

**⚠️ 格式要求（用户偏好）**:
- **必须**展示每只基金明细行，而非仅汇总
- 汇总行（总计/均值）放在明细表之后，作为补充
- 周收益率支持按 `周盈亏/总成本` 和 `净值首尾差/首净值` 两种方式计算
- 基金拆分/份额折算的基金，周收益率用持仓盈亏近似（见 Known Issues）
- 代码块内表格，确保中文对齐

**Report Contents**:
- Period covered (日期范围)
- Per-fund detail table (required — user preference)
- Summary metrics (total return, total P&L, position allocation)
- Problem identification
- Optimization suggestions
- Next week outlook

## Automation (自动化)

### Cron Job Configuration

```bash
# Weekly review: Every Sunday at 8:00 PM
Schedule: 0 20 * * 0
Deliver to: origin (current chat)
Skills: ["fund-investment-advisor"]
```

### Manual Execution

```bash
# Run weekly review manually
cd ~/.hermes/fund-advisor
python scripts/weekly_review.py
```

## Interpretation (解读指南)

### Performance Score

| Score Range | Status | Action Required |
|-------------|--------|-----------------|
| 80-100 | 优秀 (Excellent) | Continue current strategy |
| 60-79 | 良好 (Good) | Minor optimizations |
| 40-59 | 一般 (Average) | Review and adjust |
| 0-39 | 需改进 (Needs Improvement) | Major changes needed |

### Problem Severity

- **🔴 High**: Requires immediate attention
- **🟡 Medium**: Should address within the week
- **🟢 Low**: Monitor and review

## Best Practices (最佳实践)

1. **Weekly Review Day**: Always review on Sunday evening
2. **Action Items**: Create task list from optimization suggestions
3. **Progress Tracking**: Compare with previous week's performance
4. **Parameter Tuning**: Adjust stop-loss/take-profit based on volatility
5. **Diversification**: Maintain balanced portfolio across industries

## Known Issues & Fixes (已知问题与修复)

### Fund Split Detection (基金拆分检测) — Fixed 2026-07-12

**Problem**: `weekly_review.py` used `first_nav → last_nav` to compute weekly returns. When a fund undergoes share splitting/recalculation (份额折算/拆分), the NAV jumps dramatically (e.g., 0.92 → 4.36), producing absurd weekly returns like +405%. This was observed for funds 012922, 257070, 025687 on 2026-07-06/07-08.

**Fix**: Added split detection in `weekly_review.py` (line ~115). If any single-day NAV change exceeds 30%, the script falls back to computing return from actual holdings P&L (current_value vs avg_cost × shares) instead of NAV-based return.

**Pattern**: Always cross-check NAV-based returns against holdings-based returns. When they diverge wildly, a split has occurred.

## Integration Points (集成点)

### Related Systems

- **Backtest System**: Use for testing new strategies before implementation
- **NAV Update System**: Ensure fresh data for accurate analysis
- **Portfolio Management**: Align with current holdings and positions

### Data Flow

```
NAV Data → Weekly Analysis → Problem Detection → Suggestions → Report
    ↓           ↓               ↓               ↓            ↓
Backtest ← Strategy Tuning ← Position Adjustment ← Action Plan
```

## Troubleshooting (故障排除)

### Common Issues

1. **No Data Available**
   - Check if NAV data exists for the current week
   - Run NAV update script if needed
   - Verify database connection

2. **Incomplete Analysis**
   - Ensure all funds have NAV data for at least 2 trading days
   - Check for missing fund codes in holdings

3. **Report Not Generated**
   - Verify reports directory exists
   - Check file permissions
   - Review error messages in console output

### Debug Commands

```bash
# Check weekly NAV data
sqlite3 data/fund_system.db "SELECT COUNT(*) FROM fund_nav_history WHERE nav_date >= '2026-05-25'"

# List recent reports
ls -la reports/weekly_review_*.json

# View latest report
cat reports/weekly_review_latest.json
```

## Related Files (相关文件)

- `scripts/weekly_review.py`: Weekly review engine
- `scripts/generate_current_week_data.py`: Generate current week mock data
- `references/backtest-system.md`: Related backtesting system documentation

---

*Last Updated: 2026-05-26*
*Version: 1.2.1*