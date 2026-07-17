# Hermes Investment Skills

AI驱动的投资研究与基金顾问技能包，基于 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 运行。

## 技能列表

| 技能 | 说明 | 文件数 |
|------|------|--------|
| 📊 fund-investment-advisor | 基金投资顾问系统：持仓同步/诊断/看板/定投/回测 | 91 |
| 📸 fund-holdings-sync | 基金App截图OCR识别持仓数据并同步到数据库 | 1 |
| 🔗 industry-chain-map | 产业链图谱：上下游关系映射、传导信号分析、基金持仓产业链定位 | 8 |
| 🏛️ ai-berkshire | 伯克希尔价值投资研究框架：巴菲特/芒格/段永平/李录四大师方法论，19个子技能 | 31 |

## 功能概览

### fund-investment-advisor
- 实时基金净值获取（akshare/新浪/天天基金多数据源）
- 组合持仓管理与深度诊断（五段式：数据→评分→问题→优先级→对比）
- 自动定投策略（DCA + 分批止盈）
- 回测引擎（策略回测、自适应风控）
- Flask + Plotly 暗色主题投资看板（16模块）
- 每日播报（早盘/午盘/收盘/晚间）通过飞书推送
- 周报/月报/季报/年报自动生成

### fund-holdings-sync
- 截图OCR识别基金持仓
- 自动同步到 fund_system.db
- 支持支付宝/养基宝等主流平台截图

### industry-chain-map
- GPU/半导体产业链拓扑图
- 上下游传导信号分析
- 基金持仓产业链定位
- 上市公司气泡图可视化（按上中下游分页）

### ai-berkshire
- 四大师投资哲学体系（巴菲特/芒格/段永平/李录）
- 个股深度研究工作流
- 财报精读与审计
- 行业筛选漏斗
- 组合管理与风险追踪
- 金融严谨性工具链（数据交叉验证/估值验算/报告审计）

## 使用方式

1. 安装 [Hermes Agent](https://github.com/NousResearch/hermes-agent)
2. 将 `skills/` 目录下的文件夹复制到 `~/.hermes/skills/`
3. 在 Hermes 中加载对应技能

```bash
# 复制技能到 Hermes
cp -r skills/* ~/.hermes/skills/
```

## 技术栈

- Python 3.11+ (akshare, pandas, plotly, flask)
- SQLite (fund_system.db)
- Cron 定时任务
- 飞书 API 推送
- OCR 截图识别

## License

MIT
