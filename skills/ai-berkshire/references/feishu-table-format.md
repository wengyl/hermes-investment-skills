# 飞书代码块表格格式指南

飞书不渲染 Markdown 表格（`| | |`）、标题（`#`）、引用块（`>`）、分割线（`---`）。代码块渲染正常。

## 问题

标准 Markdown 表格在飞书中显示为原始文本：

```
| 公司 | 市值 | 涨跌 |
|------|------|------|
| 中际旭创 | 3472亿 | +422% |
```

在飞书中看到的是一堆管道符和横线，无法阅读。

## 解决方案

用代码块 + Python CJK 对齐函数生成等宽表格。

### Python 辅助函数

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

def make_table(headers, rows):
    """Generate a code-block table with CJK alignment"""
    all_rows = [headers] + rows
    widths = []
    for i in range(len(headers)):
        max_w = 0
        for row in all_rows:
            cell = str(row[i]) if i < len(row) else ''
            w = wdt(cell)
            if w > max_w:
                max_w = w
        widths.append(max_w)
    
    lines = []
    # Header
    lines.append(fmt_row(headers, widths))
    # Separator
    sep = '──'.join('─' * w for w in widths)
    lines.append(sep)
    # Rows
    for row in rows:
        lines.append(fmt_row(row, widths))
    
    return '\n'.join(lines)
```

### 使用示例

```python
table = make_table(
    ["公司", "代码", "市值(亿)", "推荐度"],
    [
        ["中际旭创", "300308", "3,472", "★★★★★"],
        ["新易盛", "300502", "2,024", "★★★★☆"],
    ]
)
print(f"```\n{table}\n```")
```

### 输出效果

```
公司      代码    市值(亿)  推荐度
────────────────────────────────────
中际旭创  300308  3,472     ★★★★★
新易盛    300502  2,024     ★★★★☆
```

## 其他飞书格式规则

| Markdown 语法 | 飞书支持 | 替代方案 |
|---|---|---|
| `**加粗**` | ✅ 支持 | 正常使用 |
| `*斜体*` | ✅ 支持 | 正常使用 |
| `` `行内代码` `` | ✅ 支持 | 正常使用 |
| ` ```代码块``` ` | ✅ 支持 | 表格的唯一方案 |
| `[链接](url)` | ✅ 支持 | 正常使用 |
| `- 列表` | ✅ 支持 | 正常使用 |
| `\| 表格 \|` | ❌ 不渲染 | 用代码块 |
| `# 标题` | ❌ 不渲染 | 用加粗+emoji |
| `> 引用` | ❌ 不渲染 | 用加粗引号 |
| `---` 分割线 | ❌ 不渲染 | 用 `━━━` |

## 分节线

用 `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━` 代替 `---` 做分节线。

## 长报告分段

飞书单条消息有长度限制。长报告应分段发送，每段用一个代码块表格 + 简短文字说明。
