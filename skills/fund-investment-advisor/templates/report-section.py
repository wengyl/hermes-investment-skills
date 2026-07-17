"""
Report Section Template for Fund Advisor System
Copy this template when adding new report sections
"""

def _format_new_section(self, data: Dict) -> str:
    """
    Format new section with fixed-width columns
    
    Args:
        data: Dictionary containing data to format
        
    Returns:
        Formatted string ready to append to report
    """
    from typing import Dict
    
    lines = []
    
    # ===== CONFIGURE COLUMN WIDTHS =====
    # Define widths in English character units
    # Chinese chars count as ~2 English chars in monospace
    COL_RANK = 6       # 排名
    COL_NAME = 12      # 名称 (~6 Chinese chars)
    COL_VALUE1 = 16    # 数值 1
    COL_VALUE2 = 12    # 数值 2 (optional)
    
    # ===== OPTIONAL: SUMMARY LINE =====
    summary = data.get('summary', {})
    total_value = summary.get('total', 0)
    total_sign = "+" if total_value >= 0 else ""
    lines.append(f"📊 汇总信息：{total_sign}{total_value:,.2f}\n")
    
    # ===== TABLE HEADER =====
    lines.append("```text")
    lines.append(f"{'排名':<{COL_RANK}}{'名称':<{COL_NAME}}{'数值 1':>{COL_VALUE1}}{'数值 2':>{COL_VALUE2}}")
    lines.append("─" * (COL_RANK + COL_NAME + COL_VALUE1 + COL_VALUE2))
    
    # ===== DATA ROWS =====
    items = data.get('items', [])[:10]  # Limit to top 10
    
    for i, item in enumerate(items, 1):
        name = item.get('name', '')
        value1 = item.get('value1', 0)
        value2 = item.get('value2', 0)
        
        # Truncate long names
        if len(name) > COL_NAME:
            name = name[:COL_NAME-2] + ".."
        
        # Format with signs
        if value1 >= 0:
            value1_str = f"+{value1:,.2f}"
        else:
            value1_str = f"{value1:,.2f}"
            
        if value2 >= 0:
            value2_str = f"+{value2:.1f}%"
        else:
            value2_str = f"{value2:.1f}%"
        
        # NO SPACES between columns - padding handles alignment
        lines.append(
            f"{i:<{COL_RANK}}{name:<{COL_NAME}}{value1_str:>{COL_VALUE1}}{value2_str:>{COL_VALUE2}}"
        )
    
    lines.append("─" * (COL_RANK + COL_NAME + COL_VALUE1 + COL_VALUE2))
    lines.append("```\n")
    
    # ===== OPTIONAL: INSIGHTS =====
    if items:
        top_item = items[0]['name']
        lines.append(f"💡 **热点**：{top_item} 排名第一")
        if len(items) > 1:
            lines.append(f"   其次为 {items[1]['name']}、{items[2]['name']}")
    
    return "\n".join(lines)


# ===== USAGE IN REPORT =====
# In generate_morning_report() or similar:

# report.append("\n【📊 新板块标题】")
# new_data = market.get('new_data_key', {})
# if new_data.get('items'):
#     report.append(self._format_new_section(new_data))
# else:
#     report.append("  暂无数据")


# ===== COMMON FORMATTING PATTERNS =====

# Money with thousands separator
f"{amount:,.2f}"  # 1,234.56

# Percentage
f"{pct:.2f}%"  # 12.34%

# Signed numbers
if value >= 0:
    signed = f"+{value:,.2f}"  # +1,234.56
else:
    signed = f"{value:,.2f}"   # -1,234.56

# Truncate long strings
name_display = name[:width] if len(name) <= width else name[:width-2] + ".."

# Align multiple columns (NO SPACES between)
f"{col1:<{w1}}{col2:<{w2}}{col3:>{w3}}"  # Correct
f"{col1:<{w1}} {col2:<{w2}} {col3:>{w3}}"  # Wrong - spaces break alignment
