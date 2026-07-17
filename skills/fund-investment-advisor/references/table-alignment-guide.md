# Table Alignment Best Practices

## Problem: Chinese Characters in Fixed-Width Tables

In Feishu/Lark and other messaging platforms, Chinese characters display at 2x the width of English characters in monospace fonts. This causes visual misalignment even when Python string formatting uses consistent column widths.

## Solution: Column Width Constants

### Key Principles

1. **Define column widths as constants** at the start of the formatting function
2. **Use the SAME constants** for both header and data rows
3. **Add single spaces between columns** in both header and data
4. **Use full-width separators** (`─`) instead of half-width (`-`) for visual consistency

### Implementation Pattern

```python
# Define column width constants
COL_CODE = 8       # 基金代码
COL_NAME = 18      # 基金名称
COL_SHARES = 12    # 持有份额
COL_DAILY = 20     # 今日收益 (%)
COL_VALUE = 14     # 持仓市值

# Header - use constants with spaces between columns
summary.append(f"{'基金代码':<{COL_CODE}} {'基金名称':<{COL_NAME}} {'持有份额':>{COL_SHARES}} {'今日收益 (%)':>{COL_DAILY}} {'持仓市值':>{COL_VALUE}}")

# Separator - use full-width dashes
summary.append("─" * (COL_CODE + COL_NAME + COL_SHARES + COL_DAILY + COL_VALUE + 4))  # +4 for spaces

# Data rows - use SAME constants and spaces
summary.append(f"{code:<{COL_CODE}} {name:<{COL_NAME}} {shares_str} {daily_str} {value_str}")
```

### Why This Works

- Python's `f"{text:<{width}}"` pads to the specified character count
- Both header and data use identical padding logic
- Single spaces between columns ensure consistent visual gaps
- Full-width separators (`─`) match the visual width of Chinese characters

### Common Pitfalls

❌ **Don't** use hardcoded separator lengths:
```python
summary.append("-" * 68)  # May not match actual width
```

✅ **Do** calculate separator length:
```python
summary.append("─" * (COL_CODE + COL_NAME + COL_SHARES + COL_DAILY + COL_VALUE + 4))
```

❌ **Don't** omit spaces between columns in data rows:
```python
f"{code:<{COL_CODE}}{name:<{COL_NAME}}"  # No space
```

✅ **Do** include spaces:
```python
f"{code:<{COL_CODE}} {name:<{COL_NAME}}"  # Space between
```

### Truncating Long Names

When fund names exceed column width, truncate with ellipsis:

```python
name_display = name[:COL_NAME] if len(name) <= COL_NAME else name[:COL_NAME-2] + ".."
```

This ensures the displayed name never exceeds the column width.

### Testing Alignment

Verify alignment by printing header and first data row side-by-side:

```python
header = f"{'基金代码':<{COL_CODE}} {'基金名称':<{COL_NAME}} ..."
row = f"{code:<{COL_CODE}} {name:<{COL_NAME}} ..."
print(f"Header length: {len(header)}")
print(f"Row length: {len(row)}")
# Both should be equal
```

## Example Output

```
基金代码    基金名称                      持有份额            今日收益 (%)          持仓市值
────────────────────────────────────────────────────────────────────────
005165  富荣福锦混合 C              1,000.00       +1.28 (0.04%)      2,557.70
014414  招商中证畜牧养殖 ETF 联接 A     1,000.00       +1.39 (0.17%)        815.10
```

All columns align perfectly in Feishu/Lark code blocks.
