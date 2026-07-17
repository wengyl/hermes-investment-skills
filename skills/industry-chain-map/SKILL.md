---
name: industry-chain-map
description: "产业链图谱：上下游关系映射、传导信号分析、基金持仓产业链定位。与 fund-investment-advisor 集成。"
version: "1.0.0"
author: User + Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [finance, investment, industry-chain, supply-chain, fund-analysis]
    related_skills: [fund-investment-advisor, terminal, file]
---

# 产业链图谱 (Industry Chain Map)

产业链关系映射、传导信号分析、基金持仓产业链定位。

**What this skill covers**:
- 产业链上下游关系图谱（半导体、AI、新能源、通信、医药、消费、金融、农业等）
- 产业链传导逻辑分析（价格/政策/需求变动 → 关联环节影响）
- 基金持仓 → 产业链环节定位
- 产业链信号与行业资金流向整合
- 可视化输出（ASCII 图谱 + 结构化报告）

**Use this skill when**:
- 分析某行业变动对关联行业的影响
- 定位基金持仓在产业链中的位置
- 发现产业链传导带来的投资机会或风险
- 生成产业链研究报告

---

## Quick Start

### 1. 模块结构

```
~/.hermes/skills/industry-chain-map/
├── SKILL.md                          # 本文件
├── scripts/
│   ├── chain_data.py                 # 产业链关系数据
│   ├── chain_map.py                  # 核心图谱引擎
│   ├── fund_chain_mapper.py          # 基金→产业链定位
│   └── transmission_analyzer.py      # 传导信号分析
└── references/
    └── chain-topology.md             # 详细链路拓扑文档
```

### 2. 基本使用

```python
import sys
sys.path.insert(0, '/path/to/scripts')

from chain_map import IndustryChainMap
from fund_chain_mapper import FundChainMapper
from transmission_analyzer import TransmissionAnalyzer

# 初始化
chain_map = IndustryChainMap()
mapper = FundChainMapper(chain_map)
analyzer = TransmissionAnalyzer(chain_map)

# 查看产业链
chain = chain_map.get_chain('半导体')
print(chain_map.format_chain_ascii('半导体'))

# 基金定位
position = mapper.map_fund('020692', '博时中证全指通信设备指数C')
print(position)

# 传导分析
impact = analyzer.analyze_impact('半导体', 'supply_shock', {'severity': 'high'})
print(impact)
```

---

## 产业链覆盖范围

| 产业链 | 环节数 | 覆盖行业 | 相关基金 |
|--------|--------|----------|----------|
| **GPU芯片** | 14 | EDA/半导体/存储/封装/服务器/云计算/AI | 020692, 026211, 022184 |
| 半导体 | 6 | 设计/制造/封测/设备/材料/EDA | 020692, 026211, 022184 |
| AI算力 | 5 | 芯片/算力基建/模型/应用/数据 | 026211, 022184, 027063 |
| 通信 | 5 | 设备/光纤/运营商/终端/应用 | 020692 |
| 新能源车 | 6 | 锂矿/电池/电机/整车/充电桩/回收 | - |
| 光伏 | 5 | 硅料/硅片/电池片/组件/电站 | - |
| 医药 | 5 | 创新药/CXO/器械/中药/医疗服务 | 027063, 501205 |
| 消费 | 5 | 原材料/品牌/渠道/零售/电商 | 014414 |
| 金融 | 4 | 银行/券商/保险/金融科技 | 018388 |
| 农业 | 5 | 饲料/种植/养殖/屠宰/食品加工 | 014414 |

### GPU芯片产业链（2026 AI时代专用）

GPU产业链是半导体产业链的细化版本，专注于AI算力核心环节：

```
EDA/IP → GPU设计 → 晶圆代工 → HBM → 先进封装(CoWoS) → GPU卡
                                                         ↓
GPU服务器 → 云计算 → AI模型训练 → AI Agent → 企业应用
```

**三大瓶颈**：晶圆代工（TSMC垄断）、HBM（SK hynix领先）、CoWoS封装（产能严重受限）

**GPU整机价值拆分**：GPU芯片 ≈ 40~50% | HBM ≈ 20~30% | 先进封装 ≈ 10% | 其他 ≈ 20%
| AI算力 | 5 | 芯片/算力基建/模型/应用/数据 | 026211, 022184, 027063 |
| 通信 | 5 | 设备/光纤/运营商/终端/应用 | 020692 |
| 新能源车 | 6 | 锂矿/电池/电机/整车/充电桩/回收 | - |
| 光伏 | 5 | 硅料/硅片/电池片/组件/电站 | - |
| 医药 | 5 | 创新药/CXO/器械/中药/医疗服务 | 027063, 501205 |
| 消费 | 5 | 原材料/品牌/渠道/零售/电商 | 014414 |
| 金融 | 4 | 银行/券商/保险/金融科技 | 018388 |
| 农业 | 5 | 饲料/种植/养殖/屠宰/食品加工 | 014414 |

---

## 传导信号类型

| 信号类型 | 说明 | 上游→下游 | 下游→上游 |
|----------|------|-----------|-----------|
| supply_shock | 供给冲击（产能受限/扩张） | 成本传导 | 需求拉动 |
| demand_surge | 需求激增 | 订单传导 | - |
| policy_change | 政策变动 | 利好/利空传导 | - |
| tech_breakthrough | 技术突破 | 替代/升级 | - |
| price_change | 价格变动 | 成本传导 | 需求弹性 |

---

## 与 fund-investment-advisor 集成

### 在 advisor.py 中使用

```python
from chain_map import IndustryChainMap
from fund_chain_mapper import FundChainMapper
from transmission_analyzer import TransmissionAnalyzer

class FundAdvisor:
    def __init__(self):
        self.chain_map = IndustryChainMap()
        self.chain_mapper = FundChainMapper(self.chain_map)
        self.transmission = TransmissionAnalyzer(self.chain_map)
    
    def analyze_with_chains(self, holdings, industry_data):
        """产业链增强分析"""
        results = []
        for code, name, *_ in holdings:
            # 基金→产业链定位
            position = self.chain_mapper.map_fund(code, name)
            
            # 检查产业链传导信号
            signals = self.transmission.check_fund_signals(
                code, name, industry_data
            )
            
            results.append({
                'code': code,
                'name': name,
                'chain_position': position,
                'transmission_signals': signals
            })
        return results
```

### 报告输出格式

```
产业链分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
基金        产业链        环节      传导信号
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
020692      半导体        设计→制造  ⚠️ 上游材料涨价
026211      AI算力        算力基建    ✅ 需求持续增长
022184      AI算力        应用端      ✅ 模型迭代加速
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 核心模块说明

### chain_data.py - 产业链关系数据

定义产业链拓扑结构，包括：
- 节点（产业环节）：名称、申万行业映射、代表公司、关键驱动因素
- 边（供应关系）：上游→下游、传导类型、传导强度、传导延迟
- 产业链元数据：名称、描述、关键变量

### chain_map.py - 核心图谱引擎

提供图谱操作 API：
- `get_chain(name)` - 获取产业链详情
- `get_upstream(segment)` - 获取上游环节
- `get_downstream(segment)` - 获取下游环节
- `get_related_chains(segment)` - 获取关联产业链
- `format_chain_ascii(name)` - ASCII 可视化
- `find_path(from_seg, to_seg)` - 查找传导路径

### fund_chain_mapper.py - 基金→产业链定位

- `map_fund(code, name)` - 定位基金在产业链中的位置
- `get_chain_exposure(code, name)` - 获取基金的产业链敞口
- `find_chain_overlap(code1, code2)` - 查找两只基金的产业链重叠

### transmission_analyzer.py - 传导信号分析

- `analyze_impact(chain, event_type, params)` - 分析事件影响
- `check_fund_signals(code, name, industry_data)` - 检查基金相关传导信号
- `get_transmission_path(from_seg, to_seg)` - 获取传导路径和延迟
- `calculate_chain_heat(industry_capital_flow)` - 计算产业链热度

---

## 数据来源

- **申万行业分类**: 东方财富 `fs=m:90+t:2` (31 个行业)
- **行业资金流向**: 东方财富 push2 API + 新浪财经 fallback
- **基金持仓**: 东方财富基金持仓 API + 名称推断 fallback
- **产业链关系**: 内置静态数据（基于公开研究）

---

## 注意事项

1. **传导有延迟**: 产业链传导不是即时的，上游变动可能需要 1-6 个月传导到下游
2. **非线性传导**: 传导强度受政策、库存周期、技术替代等因素影响
3. **多链交叉**: 同一行业可能处于多条产业链（如半导体同时在半导体链和AI链中）
4. **数据时效**: 产业链关系是相对稳定的，但关键驱动因素会随市场变化

---

## 气泡图生成器 (bubble_chart.py)

交互式 HTML 气泡图，一图看清全产业链的壁垒、利润、增长格局。

**⚠️ 用户偏好**：默认使用 `--mode per-chain`（按产业链分页），不要混在一张图。每条链单独查看上游→中游→下游结构。

### CLI 用法

```bash
# 按产业链分页（默认，每条链单独查看）
python3 scripts/bubble_chart.py

# 全部混在一张图
python3 scripts/bubble_chart.py --mode all

# 指定产业链
python3 scripts/bubble_chart.py --chains 半导体,AI算力,通信

# 指定输出路径
python3 scripts/bubble_chart.py -o ~/fund-advisor/reports/chain_bubble.html

# 列出所有数据（含上市公司）
python3 scripts/bubble_chart.py --list
```

### 模块调用

```python
from bubble_chart import generate_bubble_chart

# 生成全量图
html = generate_bubble_chart(output_path='~/chart.html')

# 指定产业链
html = generate_bubble_chart(chains=['半导体', 'AI算力', '医药'])
```

### 四象限含义

| 象限 | 特征 | 典型环节 | 投资策略 |
|------|------|----------|----------|
| 右上 ⭐ | 高壁垒·高利润 | AI芯片、EDA、半导体设备、创新药 | 黄金赛道，长期持有 |
| 左上 | 低壁垒·高利润 | 消费品牌 | 品牌溢价，关注竞争格局 |
| 右下 | 高壁垒·低利润 | 晶圆制造、运营商、通信设备 | 资本密集，等待盈利拐点 |
| 左下 | 低壁垒·低利润 | 零售终端、消费原材料 | 红海竞争，谨慎参与 |

### 悬停信息

鼠标悬停每个气泡可查看：
- 产业链归属 + 环节名称
- 上游/中游/下游位置标签
- 壁垒/利润/增长进度条
- 📌 A股上市公司代码+名称

---

## 版本历史

**v1.1.0** (2026-06-18):
- 新增：GPU芯片产业链（14环节，覆盖EDA→GPU设计→HBM→CoWoS→AI应用）
- 新增：`references/gpu-chain-topology.md` — GPU产业链详细拓扑文档
- 更新：气泡图默认使用分页模式（--mode per-chain），按产业链分页查看
- 更新：chain_data.py 增加 CHAIN_COLORS 定义
- 更新：bubble_chart.py 增加 GPU芯片 产业链数据

**v1.0.0** (2026-06-18):
- 初始版本
- 覆盖 9 条主要产业链
- 产业链关系数据（上下游、传导逻辑）
- 基金→产业链定位
- 传导信号分析
- ASCII 可视化输出
- 与 fund-investment-advisor 集成
