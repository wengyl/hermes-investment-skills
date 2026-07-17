# Index Data Debugging Guide

## Problem Description

### Symptom
Index change percentages showing impossible values (e.g., "-79.00%" instead of "-0.79%")

### Example
```
A 股指数:
  • 上证指数: 4119.72 -79.00%  ← INCORRECT
  • 沪深 300: 4915.14 -13.00%  ← INCORRECT
  • 深证成指: 15740.80 -73.00%  ← INCORRECT
  • 创业板指: 4008.59 -31.00%  ← INCORRECT
```

Expected:
```
A 股指数:
  • 上证指数: 4119.40 -0.80%   ← CORRECT
  • 沪深 300: 4914.24 -0.15%   ← CORRECT
  • 深证成指: 15731.44 -0.79%   ← CORRECT
  • 创业板指: 4007.06 -0.35%   ← CORRECT
```

## Root Cause Analysis

### 1. Data Source Format
The Tencent Finance API (`qt.gtimg.cn`) returns `change_pct` as a **percentage value**:
- `-0.79` means `-0.79%`
- NOT `-79` (which would be `-7900%`)

### 2. Inconsistent Handling in Code
The `advisor.py` file had two different methods handling `change_pct` differently:

**Method 1 (Correct)**: `generate_morning_briefing()` (line 50-51)
```python
# change_pct 是百分比值（如 0.36 表示 0.36%），直接显示
pct = f"{data.get('change_pct', 0):.2f}%"
```

**Method 2 (Incorrect)**: `generate_afternoon_intraday()` (line 447)
```python
pct = f"{data.get('change_pct', 0) * 100:.2f}%"  # WRONG - multiplies by 100
```

**Method 3 (Incorrect)**: `generate_evening_summary()` (line 766)
```python
pct = f"{data.get('change_pct', 0) * 100:.2f}%"  # WRONG - multiplies by 100
```

## Debugging Steps

### Step 1: Verify API Response
```bash
# Test the actual API response
curl -s 'http://qt.gtimg.cn/q=sh000001'

# Expected output (GBK encoded):
# v_sh000001="1~上证指数~000001~4119.76~4152.57~4137.32~...~-32.81~-0.79~..."
#                                                    ↑        ↑
#                                                change   change_pct
```

### Step 2: Parse the Response
```python
# The response format:
# parts[31] = change (absolute value)
# parts[32] = change_pct (percentage value)

# Example: "-32.81~-0.79"
# change = -32.81 (points)
# change_pct = -0.79 (percent, i.e., -0.79%)
```

### Step 3: Check Code Logic
```python
# In multi_source_adapter.py (lines 95-96):
change = float(parts[31])  # -32.81
change_pct = float(parts[32])  # -0.79

# This is CORRECT - API returns percentage value
```

### Step 4: Identify Display Issues
```python
# WRONG (causes -79.00%):
pct = f"{data.get('change_pct', 0) * 100:.2f}%"

# CORRECT:
pct = f"{data.get('change_pct', 0):.2f}%"
```

## Fix Applied

### Files Modified
- `scripts/advisor.py` (lines 447 and 766)

### Changes
```diff
-                    pct = f"{data.get('change_pct', 0) * 100:.2f}%"
+                    # change_pct 是百分比值（如 0.36 表示 0.36%），直接显示
+                    pct = f"{data.get('change_pct', 0):.2f}%"
```

### Verification
After the fix:
```bash
cd ~/.hermes/fund-advisor
python scripts/advisor.py afternoon

# Output should show:
# • 上证指数: 4119.40 -0.80%
# • 沪深 300: 4914.24 -0.15%
```

## Prevention

### Code Review Checklist
When modifying index data display:
1. **Verify API format**: Check what format the API returns (decimal vs percentage)
2. **Consistent handling**: Use same display logic across all report methods
3. **Add comments**: Document the expected format
4. **Test with real data**: Verify output matches market reality

### Testing Script
```python
def test_index_display():
    """Test index percentage display logic"""
    test_cases = [
        (-0.79, "-0.79%"),  # Real-world case
        (0.36, "0.36%"),
        (-1.50, "-1.50%"),
        (10.00, "10.00%"),  # Rare but possible (limit up)
    ]
    
    for api_value, expected_display in test_cases:
        # Simulate API response
        data = {'change_pct': api_value}
        
        # Apply display logic
        pct = f"{data.get('change_pct', 0):.2f}%"
        
        assert pct == expected_display, f"Failed for {api_value}: got {pct}, expected {expected_display}"
    
    print("All index display tests passed!")

# Run test
test_index_display()
```

## Related Issues

### Similar Problems
1. **Industry capital flow display**: Same pattern - verify API returns percentage vs decimal
2. **Fund daily return display**: Check if `daily_return` is percentage (1.5 = 1.5%) or decimal (0.015 = 1.5%)

### Data Source Differences
Different APIs return different formats:
- **Tencent Finance**: `change_pct` as percentage (-0.79 = -0.79%)
- **EastMoney**: May return as decimal (0.0079 = 0.79%)
- **Sina Finance**: Varies by endpoint

Always verify format before implementing display logic.

## References
- `references/api-encoding.md` - API data format specifications
- `references/nav-api-troubleshooting.md` - General API troubleshooting
- `scripts/multi_source_adapter.py` - Multi-source API adapter with format handling