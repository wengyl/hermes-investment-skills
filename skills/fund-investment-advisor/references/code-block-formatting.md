# Code Block Formatting for Fund Data

**Updated**: 2026-07-08
**Purpose**: Standardize fund data display using code blocks instead of Markdown tables

> ⚠️ **2026-07-08 UPDATE**: The CJK alignment section below ("Chinese Character Alignment")
> is **OUTDATED**. The f-string approach `f"{'通信':<10}"` does NOT correctly align CJK
> text because it pads by character count, not display width. For the correct approach,
> see `references/cjk-table-alignment.md` which uses `_pad_to_width()` + `_display_width()`.
> The rest of this doc (code block structure, number formatting, sign handling) is still valid.

---

## Why Code Blocks?

### Problems with Markdown Tables in Feishu/Lark

1. **Truncation**: Long rows get cut off
2. **Alignment**: Column borders may not render consistently
3. **Copy Issues**: Users can't easily copy the entire table
4. **Mobile Display**: Tables break on small screens

### Benefits of Code Blocks

1. ✅ **Precise Alignment**: Fixed-width formatting ensures perfect column alignment
2. ✅ **Complete Display**: No truncation, full content visible
3. ✅ **Easy Copy**: One-click copy of entire code block
4. ✅ **Cross-Platform**: Works identically on all devices and platforms
5. ✅ **Professional**: Clean, monospace presentation

---

## Implementation Pattern

### Basic Structure

```python
def format_holdings_table(self, holdings):
    """Format holdings using code block"""
    output = []
    
    # Open code block
    output.append("```")
    
    # Header row with fixed-width formatting
    output.append(f"{'序号':<4} {'基金代码':<12} {'基金名称':<20} {'净值':>10} {'日涨跌':>10}")
    output.append("-" * 70)
    
    # Data rows
    for i, fund in enumerate(holdings, 1):
        output.append(
            f"{i:<4} {fund['code']:<12} {fund['name']:<20} "
            f"{fund['nav']:>10.4f} {fund['nav_rate']:>10.2f}%"
        )
    
    # Separator and totals
    output.append("-" * 70)
    output.append(f"{'合计':<4} {'':<12} {'':<20} {'':<10} {'':<10}")
    output.append(f"持仓市值：{total_value:>10.2f} 元")
    output.append(f"总盈亏：{total_profit:>10.2f} 元 ({profit_rate:.2f}%)")
    output.append("")
    output.append(f"共计 {len(holdings)} 只基金")
    
    # Close code block
    output.append("```")
    
    return "\n".join(output)
```

---

## Formatting Guidelines

### Column Width Specifications

| Column | Width | Alignment | Example |
|--------|-------|-----------|---------|
| 序号 | 4 | Left | `f"{i:<4}"` |
| 基金代码 | 12 | Left | `f"{code:<12}"` |
| 基金名称 | 20-25 | Left | `f"{name:<20}"` |
| 净值 | 10 | Right | `f"{nav:>10.4f}"` |
| 日涨跌 | 10 | Right | `f"{rate:>10.2f}%"` |
| 持有份额 | 12 | Right | `f"{shares:>12.2f}"` |
| 持仓市值 | 12 | Right | `f"{value:>12.2f}"` |

### Separator Lines

Use consistent separator length matching total column width:

```python
# For 70-character total width
output.append("-" * 70)

# For 65-character total width  
output.append("-" * 65)
```

### Number Formatting

| Type | Format | Example |
|------|--------|---------|
| 净值 | `.4f` | `2.3624` |
| 涨跌幅 | `.2f%` | `+5.66%` |
| 份额 | `.2f` | `1000.00` |
| 金额 | `.2f` | `18630.70` |
| 百分比 | `.2f%` | `27.61%` |

### Positive/Negative Sign Handling

**CRITICAL**: When adding `+` sign to positive numbers, format the number FIRST, then add the sign, then pad to width.

❌ **WRONG** - Symbol inside format specifier causes misalignment:
```python
# WRONG - creates extra spaces between sign and number
profit_str = f"+{fund_profit:>{COL_PROFIT-1},.0f}"  # Results: "+        362"
profit_str = f"{profit_sign}{fund_profit:>8,.0f}"   # Results: "+ 362" (inconsistent width)
```

✅ **CORRECT** - Format number, add sign, then pad:
```python
# RIGHT - consistent width for all values
if fund_profit >= 0:
    profit_str = f"+{fund_profit:,.0f}"
else:
    profit_str = f"{fund_profit:,.0f}"
# Then pad to column width
profit_str = profit_str.rjust(COL_PROFIT)
```

**Why this matters**:
- `f"+{num:>{width},.0f}"` pads AFTER the sign, creating `"+        362"` (sign + padding + number)
- `f"+{num:,.0f}".rjust(width)` pads BEFORE the sign, creating `"         +362"` (padding + sign + number)
- The second approach ensures all values align at the right edge consistently

**Complete example for profit/loss column**:
```python
COL_PROFIT = 12  # Column width constant

# Calculate profit
fund_profit = current_value - cost_value

# Format with sign
if fund_profit >= 0:
    profit_str = f"+{fund_profit:,.0f}"
else:
    profit_str = f"{fund_profit:,.0f}"

# Pad to column width (right-aligned)
profit_str = profit_str.rjust(COL_PROFIT)

# Add to row (DO NOT re-format profit_str - it's already formatted!)
row = f"{i:<{COL_INDEX}} {code:<{COL_CODE}} {name:<{COL_NAME}} {nav:>{COL_NAV}.4f} {change:>{COL_CHANGE}} {profit_str}"
```

**Common mistake to avoid**:
```python
# WRONG - double formatting!
profit_str = f"+{fund_profit:,.0f}".rjust(COL_PROFIT)
row = f"..." + f"{profit_str:>{COL_PROFIT}}"  # ❌ Re-formats already-formatted string!

# RIGHT - use profit_str directly
row = f"..." + profit_str  # ✅ Already formatted and padded
```

**For daily change (similar pattern)**:
```python
if nav_rate > 0:
    change_str = f"+{nav_rate:.2f}%"
elif nav_rate < 0:
    change_str = f"{nav_rate:.2f}%"
else:
    change_str = "0.00%"
change_str = change_str.rjust(COL_CHANGE)
```

---

## Name Truncation

Long fund names can break alignment. Truncate with ellipsis:

```python
# Truncate names longer than 25 characters
name_display = name[:23] + ".." if len(name) > 25 else name

# Example output:
# "富国全球科技互联网股票 (QDII)C" -> "富国全球科技互联网股票 (QDII)C"
# "博时中证全指通信设备指数发起式 C" -> "博时中证全指通信设备指.."
```

---

## Summary Statistics

Always include totals section at the bottom:

```python
# Calculate totals
total_value = sum(fund['nav'] * fund['shares'] for fund in holdings)
total_cost = sum(fund['cost'] * fund['shares'] for fund in holdings)
total_profit = total_value - total_cost
profit_rate = (total_profit / total_cost * 100) if total_cost > 0 else 0

# Add to output
output.append("-" * 70)
output.append(f"{'合计':<4} {'':<12} {'':<20} {'':<10} {'':<10}")
output.append(f"持仓市值：{total_value:>10.2f} 元")
output.append(f"持仓成本：{total_cost:>10.2f} 元")
output.append(f"总盈亏：{'+-'[total_profit<0]}{abs(total_profit):>10.2f} 元 ({'+-'[profit_rate<0]}{abs(profit_rate):>7.2f}%)")
output.append("")
output.append(f"共计 {len(holdings)} 只基金")
```

---

## Complete Examples

### Example 1: Fund Holdings Query

```
序号   基金代码         基金名称                         净值        日涨跌 类型      
----------------------------------------------------------------------
1    005165       富荣福锦混合 C                  2.3624     +5.66% 未知      
2    014414       招商中证畜牧养殖 ETF 联接 A           0.8409     -0.95% 未知      
3    018388       华泰柏瑞港股通红利 ETF 联接 C        1.4013     -0.59% 未知      
----------------------------------------------------------------------
合计                                                                   
持仓市值：  18630.70 元
持仓成本：  14600.00 元
总盈亏：+   4030.70 元 (+  27.61%)

共计 7 只基金
```

### Example 2: Holdings Summary

```
基金代码         基金名称                              持有份额         持仓市值
-----------------------------------------------------------------
005165       富荣福锦混合 C                       1000.00      2000.00
014414       招商中证畜牧养殖 ETF 联接 A              1000.00       800.00
018388       华泰柏瑞港股通红利 ETF 联接 C             1000.00      1300.00
-----------------------------------------------------------------

持仓总市值                            14600.00 元
持仓总成本                            14600.00 元
总盈亏                          +       0.00 元 (+0.00%)

持有基金数量                                  7 只
```

### Example 3: With Cost Basis

```
基金代码         基金名称                         份额         成本           市值
-----------------------------------------------------------------
005165       富荣福锦混合 C                1000.00     2.0000      2000.00
014414       招商中证畜牧养殖 ETF 联接 A       1000.00     0.8000       800.00
-----------------------------------------------------------------

持仓总市值                            14600.00 元
持仓总成本                            14600.00 元
总盈亏                          +       0.00 元 (+0.00%)

持有基金数量                                  7 只
```

---

## Common Pitfalls

### ❌ Don't: Use Markdown Tables

```python
# WRONG - Markdown tables get truncated
output.append("| 基金代码 | 基金名称 | 净值 |")
output.append("|---------|---------|------|")
output.append(f"| {code} | {name} | {nav} |")
```

### ✅ Do: Use Code Blocks

```python
# RIGHT - Code blocks display completely
output.append("```")
output.append(f"{'基金代码':<12} {'基金名称':<20} {'净值':>10}")
output.append("-" * 45)
output.append(f"{code:<12} {name:<20} {nav:>10.4f}")
output.append("```")
```

### ❌ Don't: Inconsistent Alignment

```python
# WRONG - Mixed alignment looks messy
output.append(f"{code:<10} {name} {nav:>8}")  # name has no width
```

### ✅ Do: Fixed Width for All Columns

```python
# RIGHT - All columns have explicit widths
output.append(f"{code:<12} {name:<20} {nav:>10.4f}")
```

---

## Chinese Character Alignment (CRITICAL)

### The Problem

Chinese characters in monospace fonts occupy **2 character widths** visually, but Python's string formatting counts them as **1 character**. This causes headers and data rows to misalign:

```
序号   基金代码         基金名称                           净值        日涨跌
--------------------------------------------------------------
1    005165       富荣福锦混合 C                    2.3624     +5.66%  # ❌ Misaligned!
```

### The Solution: Use Column Width Constants

Define column widths as constants and apply them **consistently** to both headers and data rows:

```python
# Define column widths (in character count, not visual width)
COL_INDEX = 3      # 序号
COL_CODE = 7       # 基金代码
COL_NAME = 18      # 基金名称
COL_NAV = 10       # 净值
COL_CHANGE = 10    # 日涨跌

# Header - uses same widths
header = f"{'序号':<{COL_INDEX}} {'基金代码':<{COL_CODE}} {'基金名称':<{COL_NAME}} {'净值':>{COL_NAV}} {'日涨跌':>{COL_CHANGE}}"

# Data rows - uses same widths
for i, fund in enumerate(holdings, 1):
    name_display = fund['name'][:COL_NAME] if len(fund['name']) <= COL_NAME else fund['name'][:COL_NAME-2] + ".."
    row = f"{i:<{COL_INDEX}} {fund['code']:<{COL_CODE}} {name_display:<{COL_NAME}} {fund['nav']:>{COL_NAV}.4f} {change_str:>{COL_CHANGE}}"
```

### Why This Works

- Both header and data use the **exact same format specifiers**
- Python's `.ljust()` / `:<N` padding works on **character count**, not visual width
- Even though Chinese chars look wider, the padding is consistent
- Result: columns align perfectly in code blocks

### Example Output

```
序号  基金代码    基金名称                       净值        日涨跌
----------------------------------------------------
1   005165  富荣福锦混合 C                2.3624     +5.66%  # ✅ Aligned!
2   014414  招商中证畜牧养殖 ETF 联接 A         0.8409     -0.95%
```

### Key Rules

1. **Always use constants** for column widths, not hardcoded numbers
2. **Apply same constants** to header and data rows
3. **Use dynamic separator**: `"-" * len(header)` not hardcoded `"-" * 62`
4. **Truncate names** to column width: `name[:COL_NAME-2] + ".."`

---

## Platform-Specific Notes

### Feishu/Lark

- ✅ Code blocks render perfectly
- ✅ Monospace font preserves alignment
- ✅ One-click copy works
- ✅ Mobile and desktop both supported

### Telegram

- ✅ Code blocks supported with triple backticks
- ✅ Monospace formatting preserved

### Email (Plain Text)

- ✅ Code blocks work as preformatted text
- ✅ Alignment preserved in most clients

---

## Related Files

- `scripts/query_holdings.py` - Implementation example
- `scripts/advisor.py` - Holdings summary example
- `scripts/data_fetcher.py` - Data fetcher with code blocks
- `references/fund-query-display.md` - Historical context

---

## Version History

**2026-05-17**: Initial creation - Standardized code block format for all fund data displays
