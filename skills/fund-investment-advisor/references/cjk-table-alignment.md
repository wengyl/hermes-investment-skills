# CJK Table Alignment — The Definitive Fix

**Date**: 2026-07-08
**File**: `scripts/advisor.py` — all table-formatting methods
**Status**: SUPERSEDES `table-alignment-fix.md` and `table-alignment-guide.md`

---

## Root Cause

Python f-string alignment (`f"{'通信':<10}"`) pads by **character count**, not
by **display width**. Chinese characters occupy 2 terminal columns but count
as 1 character, so every CJK header label and every CJK data cell is
under-padded by 1 space per CJK char. Columns drift further out of alignment
as text length varies.

The OLD reference docs (`table-alignment-fix.md`, `table-alignment-guide.md`)
documented the f-string approach as "the fix" — that was the bug, not the fix.
They are now outdated and should not be followed.

---

## The Fix: `_pad_to_width()` + `_display_width()`

Two methods on `FundAdvisor`:

```python
def _display_width(self, s: str) -> int:
    """计算字符串显示宽度（中文=2，ASCII=1）"""
    width = 0
    for ch in s:
        if '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f' or '\uff00' <= ch <= '\uffef':
            width += 2
        else:
            width += 1
    return width

def _pad_to_width(self, s: str, width: int, align: str = 'left') -> str:
    """将字符串填充到指定显示宽度
    align: 'left' = 左对齐(右侧补空格), 'right' = 右对齐(左侧补空格)
    """
    dw = self._display_width(s)
    pad = max(0, width - dw)
    if align == 'right':
        return ' ' * pad + s
    return s + ' ' * pad
```

### Usage Pattern

```python
COL_CODE = 10
COL_NAME = 18
COL_RATIO = 10

# Header — every column uses _pad_to_width
row = (
    self._pad_to_width("基金代码", COL_CODE) +
    self._pad_to_width("基金名称", COL_NAME) +
    self._pad_to_width("占比", COL_RATIO, 'right')
)

# Data row — same constants, same method
row = (
    self._pad_to_width(code, COL_CODE) +
    self._pad_to_width(name, COL_NAME) +
    self._pad_to_width(ratio_s, COL_RATIO, 'right')
)
```

### Anti-Pattern (what NOT to do)

```python
# ❌ OLD — pads by char count, not display width; CJK columns drift
f"{code:<{COL_CODE}}{name:<{COL_NAME}}{ratio:>{COL_RATIO-1}.1f}%"

# ❌ OLD — .rjust() / .ljust() also pad by char count
shares_str = f"{shares:,.2f}".rjust(COL_SHARES)

# ❌ OLD — truncation by char count, not display width
name_display = name[:COL_NAME-2] + ".."
```

---

## Column Width Sizing Rules

1. **COL must exceed the display width of the CJK header label** — if the
   header is "基金代码" (dw=8), COL must be ≥10 to leave visible padding
   between adjacent columns. A COL equal to the header's display width
   produces zero padding, making columns run together.

2. **Use the SAME constants for header, data rows, and separator lines.**

3. **Separator length = sum of all COL constants** (+ count of inter-column
   spaces).

4. **Right-align numeric columns, left-align text columns.**

---

## Methods Fixed (2026-07-08)

| Method | Table | Columns |
|--------|-------|---------|
| `get_holdings_summary()` | Holdings table + summary | code, name, shares, nav_date, daily_return, value |
| `get_holdings_summary()` | Industry allocation | fund_code, industry, ratio |
| `get_holdings_summary()` | Portfolio overlap (组合穿透) | (blank), industry, pct |
| `_format_concentration_analysis()` | Theme distribution | theme, value, pct |
| `_format_concentration_analysis()` | Overweight funds | code, name, pct |
| `_generate_smart_signals()` | Risk signals | code, name, pnl, score, action, reason |

---

## Verification

```bash
cd ~/.hermes/fund-advisor
python3 -c "
import sys, os
sys.path.insert(0, 'scripts')
from advisor import FundAdvisor
a = FundAdvisor()
# Quick check: industry table
print(a._pad_to_width('通信', 10) + a._pad_to_width('32.8%', 10, 'right'))
print(a._pad_to_width('汽车零部件', 10) + a._pad_to_width('13.4%', 10, 'right'))
"
```

Expected: both lines should have the ratio column start at the same column
position, regardless of how many CJK chars are in the industry name.
