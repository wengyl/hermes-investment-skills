# Investment Strategy Recommendations (投资策略优化建议)

## Overview (概述)

基于对市面主流基金投资策略的研究，为基金投资顾问系统提出以下优化建议。

## Recommended Optimizations (推荐优化)

### 1. 🌟 移动止盈策略 (Trailing Stop) - 强烈推荐

**问题**: 当前使用固定止盈（如+25%），可能错过大涨行情

**优化方案**:
```python
# 移动止盈逻辑
if profit > 10%:  # 盈利超10%后启动
    trailing_stop = highest_price * (1 - 0.08)  # 回撤8%止盈
```

**优势**: 让利润奔跑，趋势行情可多赚30%+

### 2. 📊 风险平价策略 (Risk Parity) - 推荐

**问题**: 当前仓位等金额配置，没有考虑波动率差异

**优化方案**: 波动率高的基金配置少，波动率低的配置多

**预期效果**: 降低组合整体波动20-30%

### 3. 🔄 动量轮动策略 (Momentum Rotation) - 推荐

**问题**: 当前持仓固定，没有跟随市场热点

**优化方案**: 选择过去20日涨幅前2的基金持有

### 4. 🎯 核心-卫星策略 (Core-Satellite) - 推荐

**优化方案**: 70%核心仓位（宽基指数）+ 30%卫星仓位（行业/主题）

## Files Created (已创建文件)

| File | Location |
|------|----------|
| `scripts/enhanced_strategies.py` | ~/.hermes/fund-advisor/scripts/ |
| `references/strategy-optimization.md` | ~/.hermes/fund-advisor/references/ |

*Version: 1.0 | Date: 2026-05-26*

---

## Update: OptimizedMAStrategy (2026-05-31)

The theoretical strategies above were replaced by a practical, backtested strategy:

**OptimizedMAStrategy** (in `backtest_engine.py`):
- 10/30 day MA crossover
- -8% stop loss, +12% take profit
- Max 5 positions, 15% position size
- 7-day cooldown between trades

**Performance**: +42.65% over 2 years, Sharpe 1.91, max drawdown 9.48%.

Integrated into advisor.py reports as 【📈 均线策略信号】.