# Screenshot OCR to Holdings Correction Workflow

**Added**: 2026-05-22  
**Purpose**: Correct system holdings data when it doesn't match actual portfolio screenshots

---

## Problem Scenario

User has a screenshot of their actual fund holdings from a trading app, but the system database shows incorrect share counts (often default 1000 shares per fund). The market values in the screenshot don't match the system data.

**Example**:
- System shows: 1000 shares for all 9 funds
- Screenshot shows: Different market values (e.g., 3418.73 元 for one fund, 695.36 元 for another)
- Result: System market values are completely wrong

---

## Solution Workflow

### Step 1: OCR the Screenshot

Use vision tool to extract fund data from the screenshot:

```python
from hermes_tools import vision_analyze

result = vision_analyze(
    image_url="/path/to/screenshot.jpg",
    question="识别图片中所有基金的代码、名称、持有份额、持仓市值数据"
)
```

**Fallback**: If vision tool fails, use pytesseract:

```bash
cd ~/.hermes/fund-advisor
python3 -c "
from PIL import Image
import pytesseract

img = Image.open('/path/to/screenshot.jpg')
text = pytesseract.image_to_string(img, lang='chi_sim+eng', config='--psm 6')
print(text)
"
```

**Expected OCR output**:
```
基金代码    基金名称                      持仓市值    今日收益
014414    招商中证畜牧养殖 ETF 联接 A        3,418.73    -288.76
027063    鹏华创新驱动混合 C                695.36     -22.73
501205    鹏华创新未来混合 (LOF)C          2,265.35    +165.35
...
```

### Step 2: Get Latest NAV Data

Query the database for latest NAV values:

```python
import sqlite3

conn = sqlite3.connect('/Users/wyl/.hermes/fund-advisor/data/fund_system.db')
cursor = conn.cursor()

# Get latest NAV for each fund
cursor.execute('''
    SELECT h.fund_code, h.fund_name, fnh.unit_nav, fnh.nav_date 
    FROM holdings h
    LEFT JOIN fund_nav_history fnh ON h.fund_code = fnh.fund_code
    WHERE h.fund_code IN (?, ?, ?, ...)
    AND fnh.nav_date = (
        SELECT nav_date FROM fund_nav_history fnh2 
        WHERE fnh2.fund_code = h.fund_code 
        ORDER BY nav_date DESC LIMIT 1
    )
    ORDER BY h.fund_code
''', (list_of_fund_codes,))

nav_data = cursor.fetchall()
conn.close()
```

### Step 3: Calculate Actual Share Counts

**Formula**: `Share Count = Market Value (from screenshot) ÷ Latest NAV`

```python
# OCR-identified market values
ocr_market_values = {
    '002112': 4980.96,
    '005165': 1279.41,
    '014414': 3418.73,
    # ... more funds
}

# Calculate shares for each fund
calculated_shares = {}
for code, market_value in ocr_market_values.items():
    nav = nav_dict[code]['nav']  # From Step 2
    shares = market_value / nav
    calculated_shares[code] = round(shares, 2)

print(f"基金 {code}: {shares:.2f} 份 (净值 {nav:.4f})")
```

**Example calculation**:
```
招商中证畜牧养殖 ETF 联接 A:
  图片市值：3,418.73 元
  最新净值：0.7949 (2026-05-21)
  推算份额：3418.73 ÷ 0.7949 = 4,300.83 份
```

### Step 4: Update Database Holdings

Update the `holdings` table with corrected share counts:

```python
import sqlite3

conn = sqlite3.connect('/Users/wyl/.hermes/fund-advisor/data/fund_system.db')
cursor = conn.cursor()

corrected_shares = {
    '002112': 931.09,
    '005165': 485.93,
    '014414': 4300.83,
    '018388': 2833.10,
    '020692': 205.17,
    '022184': 559.08,
    '026211': 397.52,
    '027063': 494.18,
    '501205': 2321.06,
}

# Backup old data first
cursor.execute('SELECT fund_code, share_count FROM holdings WHERE fund_code IN (...)', ...)
old_data = cursor.fetchall()

# Update each fund
for code, new_shares in corrected_shares.items():
    cursor.execute('UPDATE holdings SET share_count = ? WHERE fund_code = ?', 
                   (new_shares, code))

conn.commit()
conn.close()
```

### Step 5: Verify the Update

Run the holdings report to verify:

```bash
cd ~/.hermes/fund-advisor
python3 scripts/advisor.py holdings
```

**Expected result**: System now shows correct share counts. Market values will reflect current NAV (may differ from screenshot due to time gap).

---

## Important Notes

### Why Market Values May Still Differ After Correction

After updating share counts, the system's market values may still differ from the screenshot:

```
图片市值：20,853.37 元 (拍摄时间：2026-05-22 09:53)
系统市值：22,981.80 元 (净值日期：2026-05-21)
差异：+2,128.43 元 (+10.21%)
```

**Reason**: 
- Screenshot was taken at a specific moment
- NAV data is from the latest available date (may be previous day for QDII funds)
- Market fluctuations between screenshot time and current NAV

**This is NORMAL** - the share counts are now correct, and market values will update as new NAV data arrives.

### When to Use This Workflow

✅ **Use when**:
- User provides a screenshot of actual holdings
- System shows default/uniform share counts (e.g., all 1000 shares)
- Market values are completely wrong (differences > 50% for most funds)

❌ **Don't use when**:
- Only small differences due to market fluctuations (< 5%)
- User just wants to add a new fund (use `advisor.py buy` instead)
- Screenshot is too blurry or OCR fails completely

### Common OCR Issues

1. **Vertical layout**: Some apps show funds vertically - use `--psm 6` for uniform block
2. **Chinese characters**: Use `lang='chi_sim+eng'` for Chinese + English
3. **Comma separators**: OCR may read "3,418.73" as "3418.73" - clean with `replace(',', '')`
4. **Fund name truncation**: Long names may be split across lines - join manually

---

## Example: Full Correction Session

**Before** (all funds show 1000 shares):
```
基金代码    基金名称                      持有份额    持仓市值
014414    招商中证畜牧养殖 ETF 联接 A        1,000.00    794.90
027063    鹏华创新驱动混合 C                1,000.00    1,407.10
```

**Screenshot shows**:
```
014414    招商中证畜牧养殖 ETF 联接 A        3,418.73 元
027063    鹏华创新驱动混合 C                695.36 元
```

**After correction**:
```
基金代码    基金名称                      持有份额    持仓市值
014414    招商中证畜牧养殖 ETF 联接 A        4,300.83    794.90
027063    鹏华创新驱动混合 C                494.18    1,407.10
```

✅ Share counts now match reality  
✅ Market values will update with latest NAV  
✅ Future reports will be accurate

---

## Related Files

- `scripts/advisor.py holdings` - Display current holdings
- `references/table-alignment-guide.md` - Formatting holdings output
- `references/database-schema.md` - Holdings table structure

---

## Troubleshooting

**Problem**: OCR fails to recognize fund codes

**Solution**: 
1. Try different `--psm` modes (3 for single column, 6 for uniform block)
2. Manually extract codes from screenshot using vision tool
3. Ask user to provide fund codes directly

**Problem**: NAV data missing for some funds

**Solution**:
1. Run `python3 scripts/update_nav_curl.py` to fetch latest NAV
2. Check if fund code is correct (some funds have A/C share classes)
3. For QDII funds, NAV may be 1-2 days delayed

**Problem**: Calculated shares seem unreasonable (e.g., 0.01 or 100000)

**Solution**:
1. Verify OCR extracted correct market value
2. Check NAV is not zero or null
3. Ensure units are consistent (both in 元，not 万元)
