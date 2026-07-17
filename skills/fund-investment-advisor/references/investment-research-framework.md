# Investment Research Framework (5-Step Analysis)

Added 2026-06-11. 6-module pipeline for supply-chain bottleneck investment analysis.

## Module Architecture

```
scripts/
├── bottleneck_analyzer.py    # Step 1: BOM decomposition + bottleneck scoring
├── asymmetric_screener.py    # Step 2: A-share screening (5-30B USD market cap)
├── financial_inflection.py   # Step 3: 4-dimension inflection detection
├── red_team_tester.py        # Step 4: 3-axis falsification testing
├── circuit_breaker.py        # Step 5: 6-month milestone tracking
├── investment_research.py    # Unified CLI entry point
└── ssl_patch.py              # SSL compatibility fix (MUST import first)
```

## Step 1: Bottleneck Analysis (`bottleneck_analyzer.py`)

### Pre-loaded Industry Chains (6)
| Chain | Top Bottleneck | Score | Key A-share Targets |
|-------|---------------|-------|-------------------|
| 半导体设备 | 光刻机 | 352.8 | 上海微电子(未上市) |
| AI算力 | AI训练芯片/GPU | 228.0 | 兆易创新, 北京君正 |
| 人形机器人 | 精密减速器 | 189.0 | 绿的谐波688017, 双环传动002472 |
| 光伏 | 多晶硅料 | 184.8 | 通威股份600438, 大全能源688303 |
| 新能源车 | 动力电池 | 180.0 | 宁德时代300750 |
| 创新药/CXO | CDMO/CMO | 137.1 | 药明生物(港股2269), 凯莱英002821 |

### Bottleneck Score Formula
`score = expansion_cycle_months × tech_barrier × cr3_concentration × (10 / substitute_difficulty)`

### Adding New Chains
Extend `INDUSTRY_CHAINS` dict. Each segment needs:
- `name`, `expansion_cycle_months`, `tech_barrier` (1-10), `capex_intensity` (1-10)
- `cr3_concentration` (0-1), `substitute_difficulty` (1-10)
- `key_companies`, `cn_listed` (list of "Name+Code" strings), `bottleneck_note`

## Step 2: Asymmetric Screener (`asymmetric_screener.py`)

Screens A-shares for niche champions: market cap 35-210B CNY, low institutional coverage, high failure risk if missing.

Scoring: mcap_bonus(30) + pe_bonus(20) + turnover_bonus(15) + pb_bonus(15) + chain_keyword_bonus(15)

Uses `ak.stock_zh_a_spot_em()` for real-time market data.

## Step 3: Financial Inflection (`financial_inflection.py`)

4 detection dimensions:
1. **Gross margin inflection**: >3pp QoQ jump = strong signal (5pts), 3-quarter improving trend = medium (3pts)
2. **Capex ramp**: YoY >100% = strong (5pts), >50% = medium (3pts)
3. **Revenue inflection**: V-shaped reversal + >20% growth = strong (5pts), continuous acceleration = medium (4pts)
4. **Operating leverage**: profit growth >2x revenue growth = strong (4pts)

Total score out of 20. Signal: ≥12 strong, ≥6 medium, <6 weak.

### Pitfall: THS Data Format
Data from `stock_financial_abstract_ths` uses Chinese formats: "3047.76万", "48.48%", "False".
Must use `_parse_cn_number()` helper to convert.

### Pitfall: API Function Names
- ❌ `stock_financial_benefit_ths` — does NOT exist
- ✅ `stock_financial_abstract_ths` — correct (25 columns including 销售毛利率, 营业总收入同比增长率)
- ✅ `stock_financial_report_sina` — fallback (83 columns, detailed income statement)

## Step 4: Red Team Tester (`red_team_tester.py`)

3 attack vectors per stock:
1. **Tech substitution**: Could emerging tech make this obsolete?
2. **Customer self-research**: Could key customers vertically integrate?
3. **Supply chain disruption**: Single point of failure analysis

Each risk scored: probability (1-5) × impact (1-5) = risk_score (max 25).
Falsification score = total_risk_score / max_possible × 100%.

### Pre-loaded Risk Knowledge (6 sectors)
- **光模块**: CPO替代, 硅光子, LPO, 云厂商自研, 光芯片/DSP集中
- **AI芯片**: ASIC替代, 大厂自研, 台积电产能, HBM供应
- **减速器**: 直驱替代, 液压方案, 整机厂自研, 精密加工设备
- **动力电池**: 固态电池, 钠离子, 氢能, 车企自研电芯, 锂资源
- **半导体设备**: GAA架构, 出口管制(满分25!), 零部件断供
- **CDMO**: AI制药, 药企回流产能, 生物安全法

### Adding New Sectors
Extend `RISK_KNOWLEDGE_BASE` dict with keys: `tech_substitution`, `customer_self_research`, `supply_chain`.
Each risk item: `risk`, `description`, `probability`, `impact`, optional `timeline` and `key_signal`.

## Step 5: Circuit Breaker (`circuit_breaker.py`)

3 templates:
- **growth**: Revenue growth milestones (M1:>20%, M3:>25%, M6:>30%) → clear_all if M6 fails
- **turnaround**: Gross margin inflection → profit turnaround → cash flow positive
- **bottleneck**: Market share maintenance → pricing power → capacity utilization

Consequences: review → reduce_30 → reduce_50 → halt_buy → clear_all

### Key Rule
Milestones can only be modified when passing, never when failing. This enforces discipline.

## CLI Usage

```bash
# Individual steps
python3 scripts/bottleneck_analyzer.py AI算力
python3 scripts/investment_research.py compare
python3 scripts/investment_research.py screen --min-cap 35 --max-cap 210
python3 scripts/investment_research.py inflection 300308
python3 scripts/investment_research.py redteam 300308 中际旭创 "光模块龙头" 光模块
python3 scripts/investment_research.py circuit create 300308 中际旭创 "论点" --template growth
python3 scripts/investment_research.py circuit check 300308
python3 scripts/investment_research.py circuit summary

# Full 5-step pipeline
python3 scripts/investment_research.py full AI算力 300308 中际旭创 "光模块龙头受益AI算力爆发"

# All commands require ssl_patch import (done automatically in investment_research.py)
```

## Database

Tables in `data/research.db`:
- `bottleneck_analysis` — bottleneck scores per chain/segment
- `research_targets` — tracked investment targets
- `screen_results` — screener output
- `inflection_analysis` — financial inflection results
- `red_team_reports` — red team test reports (JSON)
- `circuit_breakers` — milestone trackers
- `circuit_milestones` — individual milestones with status
