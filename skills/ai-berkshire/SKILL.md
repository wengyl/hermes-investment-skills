---
name: ai-berkshire
description: "AI时代的伯克希尔：巴菲特·芒格·段永平·李录四大师价值投资研究框架。19个子技能覆盖个股研究、团队并行分析、财报精读、行业筛选、组合管理、风险追踪全流程。含金融严谨性工具链（数据交叉验证/估值验算/报告审计）。"
tags:
  - investing
  - value-investing
  - research
  - finance
  - buffet
  - munger
triggers:
  - "投资研究"
  - "价值投资"
  - "个股分析"
  - "财报精读"
  - "行业筛选"
  - "组合管理"
  - "投资论文追踪"
  - "巴菲特"
  - "段永平"
  - "芒格"
  - "李录"
---

# AI Berkshire — 四大师价值投资研究框架

基于 [xbtlin/ai-berkshire](https://github.com/xbtlin/ai-berkshire) 项目，适配 Hermes Agent 运行时。

## 核心理念

将巴菲特、芒格、段永平、李录四位投资大师的方法论，转化为可执行的 AI 研究工作流。每个分析模块对应一位大师的核心追问：

| 大师 | 核心框架 | 追问 |
|------|---------|------|
| 段永平 | 对的生意、对的人、对的价格 | 这门生意好在哪？如果股市关闭5年你愿意持有吗？ |
| 巴菲特 | 经济护城河、内在价值、安全边际 | 10年后这条护城河还在吗？什么能摧毁它？ |
| 芒格 | 逆向思考、跨学科模型 | 我最可能在哪里犯错？聪明人为什么不买？ |
| 李录 | 文明演进框架、产业范式转移 | 站在20年后回看，这是"标准石油"还是"3Com"？ |

## 子技能矩阵（references/ 目录）

| 子技能 | 文件 | 用途 |
|--------|------|------|
| **飞书表格格式化** | `feishu-table-format.md` | CJK对齐的代码块表格生成工具 |
| **个股综合研究** | `investment-research.md` | 七步法完整分析一家公司 |
| **团队并行研究** | `investment-team.md` | 4 Agent 并行：商业/财务/行业/风险 |
| **财报精读** | `earnings-review.md` | 一手财报深度解读 |
| **财报团队精读** | `earnings-team.md` | 四大师并行解读 + 公众号文章产出 |
| **行业研究** | `industry-research.md` | 产业链全景扫描 + 个股分析 |
| **行业漏斗筛选** | `industry-funnel.md` | 全市场 → 3家精选标的 |
| **去劣筛选** | `quality-screen.md` | 7条指标快速排除非一流公司 |
| **买入前 Checklist** | `investment-checklist.md` | 巴菲特10项买入前检查 |
| **管理层纵深** | `management-deep-dive.md` | CEO决策复盘 + 资本配置能力 |
| **未上市公司研究** | `private-company-research.md` | 蚂蚁/SpaceX等非上市公司 |
| **组合管理** | `portfolio-review.md` | 持仓审视与优化 |
| **投资论文追踪** | `thesis-tracker.md` | 买入后纪律系统 |
| **论文漂移检测** | `thesis-drift.md` | 分清事实变化与措辞变化 |
| **瓶颈猎手** | `bottleneck-hunter.md` | 供应链瓶颈套利机会挖掘 |
| **深度公司系列** | `deep-company-series.md` | 8篇长文拆一家公司 |
| **公众号文章** | `wechat-article.md` | 作者-编辑-读者三Agent协作 |
| **段永平问答** | `dyp-ask.md` | 以段永平的方式思考回答 |
| **新闻脉搏** | `news-pulse.md` | 股价异动快速归因 |
| **财务数据规范** | `financial-data.md` | 数据源优先级 + 交叉验证规则 |

## 金融工具链（scripts/ 目录）

| 工具 | 用途 | 关键命令 |
|------|------|---------|
| `financial_rigor.py` | 金融数据严谨性验证 | 市值验算、多源交叉验证、估值验算、三情景估值 |
| `report_audit.py` | 报告数据抽检 | 提取15%随机抽样清单 + 准出/打回判决 |
| `ashare_data.py` | A股数据获取 | 东方财富/巨潮资讯数据拉取 |
| `xueqiu_scraper.py` | 雪球数据抓取 | 股票/基金数据 |
| `stock_screener.py` | 股票筛选器 | 多条件筛选 |
| `morningstar_fair_value.py` | Morningstar公允价值 | 估值参考 |
| `momentum_backtest_v2.py` | 动量回测 | 策略回测 |

## Feishu 输出格式（重要）

投资研究报告在飞书中发送时，**Markdown表格不渲染**，会显示为原始文本。必须使用以下格式：

### 代码块表格

所有表格用 ``` 代码块包裹，用 Python 的 `east_asian_width` 函数计算 CJK 字符显示宽度并填充空格对齐：

```python
import unicodedata

def wdt(s):
    """CJK-aware display width"""
    w = 0
    for c in s:
        if unicodedata.east_asian_width(c) in ('F','W','A'):
            w += 2
        else:
            w += 1
    return w

def fmt_row(cols, widths):
    parts = []
    for i, col in enumerate(cols):
        s = str(col)
        pad = widths[i] - wdt(s)
        parts.append(s + ' ' * max(0, pad))
    return '  '.join(parts)
```

### 分节标记

用 `━━━` 分隔线代替 Markdown `---`，飞书不渲染水平分割线。

### 避免的格式

- ❌ Markdown 表格 `| | |` — 飞书不渲染
- ❌ `>` 引用块 — 飞书不渲染
- ❌ `#` 标题 — 飞书不渲染
- ✅ 代码块表格 — 等宽字体，对齐良好
- ✅ `**加粗**` — 飞书支持
- ✅ 列表 `-` / `1.` — 飞书支持

## Hermes 适配说明

原项目为 Claude Code / Codex 设计，以下为 Hermes 对应关系：

| 原始工具 | Hermes 替代 | 说明 |
|----------|------------|------|
| `Task`（后台Agent） | `delegate_task` | 单任务或批量并行（最多3个） |
| `Team`/`TeamCreate` | `delegate_task`（tasks模式） | 批量派发多个子Agent |
| `WebSearch` | `web` 工具集 / `browser` | 浏览器导航+搜索 |
| `Bash` | `terminal` | Shell命令执行 |
| `Read`/`Write` | `read_file`/`write_file` | 文件读写 |
| `SendMessage`（Agent间通信） | 无直接等价 | 子Agent结果自动返回汇总 |
| `$ARGUMENTS` | 用户输入 | 用户消息中的公司名/股票代码 |

### 关键适配点

1. **团队并行研究**：原项目用 Claude Code Team 工具创建4个Agent。在 Hermes 中，使用 `delegate_task` 的 `tasks` 模式批量派发（一次最多3个，需要时分两批）。每个子Agent的 `goal` 字段包含完整的分析指令。**注意：子Agent默认超时600秒（10分钟），复杂的行业研究+浏览器搜索可能超时。建议将任务拆细，减少每个子Agent的搜索范围，或用 `toolsets: ["browser", "web"]` 限定工具集。**

2. **金融工具调用**：脚本位于技能目录 `scripts/` 下。调用时需使用完整路径：
   ```bash
   python3 ~/.hermes/skills/business/ai-berkshire/scripts/financial_rigor.py verify-market-cap \
     --price {股价} --shares {总股本} --reported {报告市值} --currency {币种}
   ```

3. **报告输出**：原项目写入 `~/[公司名]投资研究报告.md`。Hermes 中保持一致，同时可通过 Feishu 直接发送。

4. **数据交叉验证**：必须使用 `financial_rigor.py` 工具验算，禁止 LLM 心算。这是该技能的硬性要求。

5. **子Agent超时风险**：`delegate_task` 默认超时600秒。涉及大量浏览器搜索的财务数据收集Agent容易超时（尤其是搜索A股数据需要翻页东方财富/巨潮资讯）。**对策**：将财务数据收集拆分为A股和美股两个独立子Agent，每个聚焦3-4家公司而非全部10家。行业研究子Agent将搜索任务限定为5-6个核心问题，不追求全覆盖。

6. **持仓交叉分析**：用户持有基金（非个股），需穿透基金到底层股票才能与行业研究匹配。数据在 `~/.hermes/fund-advisor/data/fund_system.db` 的 `holdings` 和 `fund_holdings_cache` 表中。用 Python 计算"有效暴露"= 基金市值 × 基金内该股票权重 / 总持仓，再按个股汇总。这是 ai-berkshire 行业研究与用户实际持仓连接的关键桥梁。

7. **飞书输出格式**：见上方"输出格式（飞书适配）"章节。核心：表格用代码块+CJK对齐，不用Markdown管道表格。

## 输出格式（飞书适配）

飞书不支持 Markdown 表格、标题（#）、引用块（>）和分割线（---）。在飞书环境输出报告时：

1. **所有表格用代码块包裹**：` ``` ` + CJK 等宽对齐 + ` ``` `
2. **分隔线用 `━━━`**，不用 `---`
3. **标题用纯文本+━━━上下包围**，不用 `#`
4. **Python 对齐工具**：用 `unicodedata.east_asian_width()` 计算 CJK 显示宽度（F/W/A=2，其余=1），然后用固定宽度 padding 对齐

```python
import unicodedata
def wdt(s):
    w = 0
    for c in s:
        if unicodedata.east_asian_width(c) in ('F','W','A'):
            w += 2
        else:
            w += 1
    return w
```

## 使用方式

### 快速入口：个股研究

用户说"分析腾讯"或"研究 NVDA"时，加载 `references/investment-research.md` 并按七步法执行：

1. **AI研究偏见自觉** — 评估信息丰富度（A/B/C级）
2. **数据收集** — 10类数据 + 双源交叉验证 + `financial_rigor.py` 验算
3. **生意本质** — 段永平"对的生意"
4. **护城河评估** — 巴菲特"经济护城河"五类验证
5. **逆向思考** — 芒格"反过来想"风险清单
6. **管理层评估** — 段永平"对的人" + 巴菲特"诚信"
7. **行业与文明趋势** — 李录"文明演进框架"
8. **估值与安全边际** — 三情景估值（工具验算）
9. **综合决策备忘录** — 四维评分 + 投资建议
10. **数据抽检** — `report_audit.py` 15%随机抽样准出

### 团队并行研究

用户说"团队分析美团"时，加载 `references/investment-team.md`，使用 `delegate_task` 批量派发4个子Agent（分两批，每批≤3个）：

- **business-analyst**：商业模式 + 护城河（段永平视角）
- **financial-analyst**：财务报表 + 估值（巴菲特视角，含工具验算）
- **industry-researcher**：行业格局 + 竞争态势（芒格视角）
- **risk-assessor**：风险评估 + 管理层研判（李录视角）

### 其他入口

- "财报精读 腾讯 2025Q4" → `earnings-review.md`
- "行业筛选 新能源" → `industry-funnel.md`
- "去劣筛选 茅台,五粮液" → `quality-screen.md`
- "买入前checklist 英伟达" → `investment-checklist.md`
- "组合审视" → `portfolio-review.md`
- "论文追踪 腾讯" → `thesis-tracker.md`

## 数据源规范

| 市场 | 主要来源 | 备用来源 |
|------|---------|---------|
| 美股 | macrotrends.net | stockanalysis.com |
| 港股 | aastocks.com | macrotrends（ADR代码） |
| A股 | 东方财富 eastmoney.com | 巨潮资讯 cninfo.com.cn |

**铁律**：每个关键数据必须来自两个独立来源，误差>1%须标记，>5%必须查原始财报。

## 反偏见机制

该技能内置 AI 研究偏见自觉系统：

- **A级（信息充裕）**：重点做反面检验，避免输出与市场共识趋同的"正确的废话"
- **B级（信息适中）**：每个推算数据标注置信度，区分"有据推算"和"凭空填充"
- **C级（信息稀缺）**：不追求报告完整性，用第一性原理聚焦商业本质

报告必须区分"AI分析置信度"（取决于资料量）与"投资确定性"（取决于生意本质）。

## 飞书输出格式（重要）

飞书不渲染 Markdown 表格（`| | |`）、标题（`#`）、引用块（`>`）、分割线（`---`）。代码块（```）渲染正常。

**所有表格必须用代码块包裹 + CJK 对齐**：

```python
import unicodedata

def wdt(s):
    """Calculate display width accounting for CJK characters"""
    w = 0
    for c in s:
        if unicodedata.east_asian_width(c) in ('F', 'W', 'A'):
            w += 2
        else:
            w += 1
    return w

def fmt_row(cols, widths):
    """Format a row with proper padding for CJK alignment"""
    parts = []
    for i, col in enumerate(cols):
        s = str(col)
        pad = widths[i] - wdt(s)
        parts.append(s + ' ' * max(0, pad))
    return '  '.join(parts)
```

分节线用 `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━` 代替 `---`。

详见 `references/feishu-table-format.md`。

## 实战经验（2026-07-08 首次使用）

### Hermes 适配验证

1. **delegate_task 替代 Team 工具**：批量派发3个子Agent成功（行业/财务/商业模式三视角并行），但单个子Agent有600秒超时限制。如果任务量大（如同时搜索10家公司的财务数据），可能超时。建议：每个子Agent目标控制在3-5家公司，超过则分批。

2. **financial_rigor.py 可直接运行**：所有工具在 `~/.hermes/skills/business/ai-berkshire/scripts/` 下可直接用 `python3` 运行，无需额外依赖。验证了 `verify-market-cap`、`three-scenario`、`cross-validate`、`verify-valuation` 四个子命令。

3. **行业研究适配路径**：用 `industry-research.md` 框架，delegate_task 派发芒格/巴菲特/段永平三个视角的子Agent，结果合并后用 financial_rigor.py 验算关键数据，最后格式化为飞书代码块表格输出。

### macOS Vision OCR 回退方案

当 vision_analyze / browser_vision 因 provider 不支持图片而失败时，用 macOS Vision 框架做 OCR：

```swift
// /tmp/ocr.swift — 需 macOS Command Line Tools
import Vision
import AppKit

let imagePath = "PATH_TO_IMAGE"
guard let image = NSImage(contentsOfFile: imagePath),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    print("Failed to load"); exit(1)
}

let request = VNRecognizeTextRequest { request, _ in
    guard let observations = request.results as? [VNRecognizedTextObservation] else { return }
    for obs in observations {
        if let text = obs.topCandidates(1).first?.string { print(text) }
    }
}
request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hans", "en-US"]
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try? handler.perform([request])
RunLoop.main.run(until: Date(timeIntervalSinceNow: 15))
```

运行：`swift /tmp/ocr.swift`

注意：`CGImageRef` 在 Swift 3+ 已重命名为 `CGImage`，不要用旧语法。

## 来源

- 仓库：https://github.com/xbtlin/ai-berkshire
- 安装日期：2026-07-08
- 版本：main 分支最新
