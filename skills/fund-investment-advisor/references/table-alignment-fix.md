# Table Alignment Fix - advisor.py get_holdings_summary()

**Date**: 2026-05-19  
**File**: `/scripts/advisor.py` - `get_holdings_summary()` method  
**Issue**: Table columns misaligned between header and data rows

---

## Problem Identified

The `get_holdings_summary()` function had several alignment issues:

1. **Hardcoded separator length**: Used `COL_CODE + COL_NAME + COL_SHARES + COL_DAILY + COL_VALUE + 4` instead of dynamic `len(header)`
2. **Inconsistent column widths**: Summary section used different width calculations than data rows
3. **Total profit display**: Used separate `profit_sign` variable causing extra spacing (`+ 3,913.50` instead of `+3,913.50`)

---

## Fix Applied

### 1. Define Column Width Constants

```python
# 定义列宽常量（统一使用这些常量确保对齐）
COL_CODE = 7       # 基金代码（6 位数字 +1 空格）
COL_NAME = 18      # 基金名称
COL_SHARES = 10    # 持有份额
COL_DAILY = 18     # 今日收益（金额 + 比例，增加宽度）
COL_VALUE = 12     # 持仓市值
```

### 2. Use Constants for Header AND Data Rows

```python
# 表头 - 使用列宽常量
header = f"{'基金代码':<{COL_CODE}} {'基金名称':<{COL_NAME}} {'持有份额':>{COL_SHARES}} {'今日收益 (%)':>{COL_DAILY}} {'持仓市值':>{COL_VALUE}}"
summary.append(header)
summary.append("-" * len(header))  # 动态分隔线

# 数据行 - 使用相同的列宽常量
summary.append(
    f"{code:<{COL_CODE}} {name_display:<{COL_NAME}} {shares_str} {daily_str} {value_str}"
)
```

### 3. Dynamic Separator Line

```python
# ✅ RIGHT - Dynamic length from actual header
summary.append("-" * len(header))

# ❌ WRONG - Hardcoded calculation
summary.append("-" * (COL_CODE + COL_NAME + COL_SHARES + COL_DAILY + COL_VALUE + 4))
```

### 4. Summary Section Alignment

```python
# 汇总信息（对齐到表头下方）
# 标签宽度 = 基金代码 + 基金名称 + 持有份额
label_width = COL_CODE + COL_NAME + COL_SHARES + 2
# 值宽度 = 今日收益 + 持仓市值
value_width = COL_DAILY + COL_VALUE

summary.append(f"{'💰 持仓总市值':<{label_width}} {total_value:>{value_width-2},.2f}")
summary.append(f"{'💵 持仓总成本':<{label_width}} {total_cost:>{value_width-2},.2f}")
```

### 5. Total Profit Display (Compact Format)

```python
# 总盈亏格式化：符号和数字连在一起
if total_profit >= 0:
    profit_display = f"+{abs(total_profit):,.2f}"
else:
    profit_display = f"{total_profit:,.2f}"
summary.append(f"{summary_label:<{label_width}} {profit_display:>{value_width-8}} ({profit_sign}{profit_rate:.2f}%)")
```

---

## Before vs After

### Before (Misaligned)
```
基金代码    基金名称                     持有份额           今日收益 (%)         持仓市值
---------------------------------------------------------------------
005165  富荣福锦混合 C             1,000.00     -2.30 (-0.09%)     2,557.70
...
---------------------------------------------------------------------
💰 持仓总市值                                                  18,513.50
💵 持仓总成本                                                  14,600.00
📊 今日总收益                                           -57.43 (-0.31%)
📈 总盈亏                                 +                 3,913.50 (+26.80%)
```

### After (Aligned)
```
基金代码    基金名称                     持有份额           今日收益 (%)         持仓市值
---------------------------------------------------------------------
005165  富荣福锦混合 C             1,000.00     -2.30 (-0.09%)     2,557.70
...
---------------------------------------------------------------------
💰 持仓总市值                                                  18,513.50
💵 持仓总成本                                                  14,600.00
📊 今日总收益                                           -57.43 (-0.31%)
📈 总盈亏                                              +3,913.50 (+26.80%)
```

---

## Key Takeaways

1. **Always use `len(header)` for separator lines** - Never hardcode
2. **Define column width constants once** - Use them everywhere (header, data rows, summary)
3. **Combine sign and number** - `+3,913.50` not `+ 3,913.50` for compact display
4. **Test alignment visually** - Print header and first row side-by-side to verify

---

## Related Files

- `references/table-alignment-guide.md` - General column alignment best practices
- `scripts/advisor.py` - Fixed implementation
- `scripts/query_holdings.py` - Already follows these patterns correctly

---

## Verification

Test with:
```bash
cd ~/.hermes/fund-advisor
python scripts/advisor.py holdings
```

Expected: All columns should align vertically, separator lines match header length exactly.
