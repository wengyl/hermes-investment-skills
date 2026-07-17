---
name: fund-holdings-sync
description: "从基金App截图识别持仓数据并同步到系统数据库"
version: "1.0.0"
---

# 基金持仓截图同步

用户在支付宝/养基宝等App中截图基金持仓页面，发到飞书对话中。
本技能识别截图中的基金代码、名称、份额、成本等信息，批量同步到 fund_system.db。

## 触发条件

用户发送图片（基金持仓截图）时触发。通常会说"同步持仓"、"更新基金"等。

## 操作步骤

### 1. 识别截图

**优先方案**：使用 vision_analyze 工具分析用户发送的截图。

**回退方案（vision_analyze 失败时）**：当 provider 不支持图片输入（报错 `unknown variant 'image_url'`），用 macOS Vision 框架做 OCR：

```bash
# 生成 /tmp/ocr.swift 并运行
cat > /tmp/ocr.swift << 'SWIFT'
import Vision
import AppKit

let imagePath = CommandLine.arguments[1]
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
SWIFT

swift /tmp/ocr.swift "/path/to/screenshot.jpg"
```

OCR 输出是逐行文本，需要按以下规则解析为结构化数据：

1. 基金名称行：通常以中文开头，可能包含"（QDII）"等括号
2. 金额行：`1,471.43` 格式（带千分位逗号）
3. 盈亏行：`+1.94` 或 `-28.57` 格式
4. 收益率行：`-2.38%` 格式
5. 忽略噪声行：如"定投"、"金选 指数基金⑥"、"市场解读"等

解析逻辑：遍历所有行，识别基金名称后，后续的数字行依次对应：市值、今日变动、累计盈亏、收益率。

**长截图处理**：如果图片高度>2000px，OCR 可能耗时较长但 Vision 框架能处理。不需要切割图片。

### 2. 数据清洗

识别结果可能不完美，需要清洗：
- 确认基金代码是6位数字
- 份额转成 float
- 如果名称不完整，可从代码查询全名：`curl -s "https://fundgz.1234567.com.cn/js/<code>.js"`
- 如果没有成本价，设为0（sync_holdings.py 会用最新净值计算现值）

### 3. 同步到数据库

调用 sync_holdings.py 脚本：

```bash
cd ~/.hermes/fund-advisor
python3 scripts/sync_holdings.py '{"holdings":[{"code":"022184","name":"富国全球科技","shares":1642.49,"cost":5.7839,"invested":9500.00},...],"mode":"replace"}'
```

- `mode: "replace"` — 全量替换（推荐，适合定期同步）
- `mode: "merge"` — 只更新传入的基金（适合只截图了部分基金）

### 4. 回报结果

同步完成后，向用户报告：
- 更新了哪些基金
- 份额变化（与上次对比）
- 总持仓市值
- 如有异常（份额大幅变化），提醒确认

## 支持的截图类型

| App | 截图特征 |
|---|---|
| 支付宝 | 财富→基金→持有页面，显示基金列表 |
| 养基宝 | 持仓页面，显示基金代码/名称/份额/收益 |
| 天天基金 | 持有页面 |
| 通用 | 任何包含基金代码+份额的列表截图 |

## 注意事项

- 截图需清晰，数字可辨认
- 如果截图包含敏感信息（手机号等），识别时忽略
- 同步前确认份额数量级合理（避免OCR识别错误）
- 如果用户只发部分基金截图，使用 merge 模式避免覆盖全部持仓
