# 策略回测系统

## 系统概述

策略回测系统是一个完整的投资策略评估框架，支持回测、优化、比较和月度评估。

## 文件结构

```
fund-advisor/scripts/
├── backtest_engine.py      # 回测引擎核心
├── strategy_optimizer.py   # 策略优化器
├── monthly_evaluation.py   # 月度评估系统
├── report_visualizer.py    # 报告可视化
├── backtest_main.py        # 主入口脚本
└── generate_mock_data.py   # 模拟数据生成器
```

## 使用方法

### 1. 运行回测
```bash
cd ~/.hermes/fund-advisor
python scripts/backtest_main.py backtest \
    --start-date 2026-03-01 \
    --end-date 2026-04-30 \
    --strategy batch
```

### 2. 优化策略参数
```bash
python scripts/backtest_main.py optimize \
    --strategy simple \
    --start-date 2026-03-01 \
    --end-date 2026-04-30
```

### 3. 比较多策略
```bash
python scripts/backtest_main.py compare \
    --start-date 2026-03-01 \
    --end-date 2026-04-30
```

### 4. 月度评估
```bash
python scripts/backtest_main.py monthly
```

## 内置策略

1. **止盈止损策略** - 基于固定阈值止盈止损
2. **分批止盈策略** - 在不同盈利水平分批卖出
3. **趋势跟踪策略** - 基于移动平均突破
4. **组合策略** - 结合多个策略决策

## 评估指标

- **总收益率** - 策略的整体盈利能力
- **年化收益率** - 年化后的收益水平
- **最大回撤** - 资产从峰值到谷值的最大跌幅
- **夏普比率** - 风险调整后的收益
- **胜率** - 盈利交易的比例

## 月度评估

已设置CRON任务（每月1号9:00），自动运行：
- 策略回测
- 参数优化
- 生成优化建议
- 保存月度报告

## 报告输出

1. **JSON报告** - 完整的回测数据
2. **HTML报告** - 可视化的图表和指标
3. **月度评估报告** - 包含优化建议