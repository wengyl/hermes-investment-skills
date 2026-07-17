#!/usr/bin/env python3
"""
基金净值数据验证脚本
检查NAV数据的完整性、一致性和合理性
"""
import sqlite3
import os
from datetime import datetime, timedelta

def validate_nav_data(db_path=None):
    """验证基金净值数据"""
    if db_path is None:
        # 默认数据库路径
        hermes_home = os.path.expanduser('~/.hermes/fund-advisor')
        db_path = os.path.join(hermes_home, 'data', 'fund_system.db')
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    issues = []
    
    # 1. 检查基金数量
    cursor.execute("SELECT COUNT(DISTINCT fund_code) FROM fund_nav_history")
    fund_count = cursor.fetchone()[0]
    print(f"📊 基金数量: {fund_count}")
    
    if fund_count == 0:
        issues.append("数据库中没有基金净值数据")
        print("❌ 没有基金净值数据")
        conn.close()
        return False
    
    # 2. 检查最新日期
    cursor.execute("SELECT MAX(nav_date) FROM fund_nav_history")
    latest_date = cursor.fetchone()[0]
    print(f"📅 最新净值日期: {latest_date}")
    
    if latest_date:
        latest_dt = datetime.strptime(latest_date, '%Y-%m-%d')
        days_diff = (datetime.now() - latest_dt).days
        if days_diff > 7:  # 超过7天没更新
            issues.append(f"净值数据过期: 最新日期是{days_diff}天前")
            print(f"⚠️ 净值数据可能过期: {days_diff}天前")
    
    # 3. 检查每个基金的数据完整性
    print("\n📋 各基金数据完整性:")
    cursor.execute('''
        SELECT fund_code, 
               COUNT(*) as record_count,
               MIN(nav_date) as earliest,
               MAX(nav_date) as latest,
               MAX(nav_date) - MIN(nav_date) as date_span_days
        FROM fund_nav_history 
        GROUP BY fund_code
        ORDER BY fund_code
    ''')
    
    for code, count, earliest, latest, span in cursor.fetchall():
        status = "✅" if count >= 10 else "⚠️"
        print(f"  {status} {code}: {count}条记录, 日期范围: {earliest} 到 {latest} ({span}天)")
        
        if count < 5:
            issues.append(f"基金{code}数据不足: 仅{count}条记录")
        
        # 检查日期间隔是否有大的缺口
        if span and span > 0:
            expected_records = span + 1  # 包括首尾日期
            if count < expected_records * 0.8:  # 缺少超过20%的记录
                issues.append(f"基金{code}可能有日期缺口")
    
    # 4. 检查NAV值的合理性
    print("\n🔍 NAV值合理性检查:")
    cursor.execute('''
        SELECT fund_code, nav_date, unit_nav,
               LAG(unit_nav) OVER (PARTITION BY fund_code ORDER BY nav_date) as prev_nav
        FROM fund_nav_history
        ORDER BY fund_code, nav_date
    ''')
    
    suspicious_jumps = []
    for code, date, nav, prev in cursor.fetchall():
        if prev and prev > 0:
            change_pct = abs((nav - prev) / prev * 100)
            if change_pct > 20:  # 单日变化超过20%
                suspicious_jumps.append((code, date, nav, prev, change_pct))
    
    if suspicious_jumps:
        print(f"⚠️ 发现{suspicious_jumps.__len__()}个可疑的NAV大跳变:")
        for code, date, nav, prev, pct in suspicious_jumps[:5]:  # 只显示前5个
            print(f"  {code} {date}: {prev:.4f} -> {nav:.4f} ({pct:.1f}%)")
            issues.append(f"基金{code}在{date}有异常NAV跳变: {pct:.1f}%")
    
    # 5. 检查持仓表与净值表的一致性
    print("\n🔗 持仓与净值一致性检查:")
    cursor.execute('''
        SELECT h.fund_code, h.fund_name, 
               COUNT(n.nav_date) as nav_count,
               MAX(n.nav_date) as latest_nav
        FROM holdings h
        LEFT JOIN fund_nav_history n ON h.fund_code = n.fund_code
        WHERE h.share_count > 0
        GROUP BY h.fund_code
    ''')
    
    holdings_funds = cursor.fetchall()
    if holdings_funds:
        for code, name, nav_count, latest_nav in holdings_funds:
            if nav_count == 0:
                print(f"  ❌ {code} ({name}): 无净值数据")
                issues.append(f"持仓基金{code}没有净值数据")
            elif not latest_nav:
                print(f"  ⚠️ {code} ({name}): 净值数据为空")
                issues.append(f"持仓基金{code}净值数据为空")
            else:
                print(f"  ✅ {code}: {nav_count}条净值记录, 最新: {latest_nav}")
    
    # 6. 输出总结
    print("\n" + "="*50)
    if not issues:
        print("✅ 数据验证通过，未发现问题")
        result = True
    else:
        print(f"⚠️ 发现{len(issues)}个问题:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        result = False
    
    conn.close()
    return result

def check_holdings_consistency(db_path=None):
    """检查持仓数据一致性"""
    if db_path is None:
        hermes_home = os.path.expanduser('~/.hermes/fund-advisor')
        db_path = os.path.join(hermes_home, 'data', 'fund_system.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n💼 持仓数据一致性检查:")
    
    # 检查持仓市值计算
    cursor.execute('''
        SELECT h.fund_code, h.fund_name, h.share_count, h.avg_cost, h.current_value,
               n.unit_nav as latest_nav,
               h.share_count * n.unit_nav as calculated_value
        FROM holdings h
        LEFT JOIN (
            SELECT fund_code, unit_nav
            FROM fund_nav_history
            WHERE (fund_code, nav_date) IN (
                SELECT fund_code, MAX(nav_date)
                FROM fund_nav_history
                GROUP BY fund_code
            )
        ) n ON h.fund_code = n.fund_code
        WHERE h.share_count > 0
    ''')
    
    issues = []
    for code, name, shares, avg_cost, current_value, latest_nav, calculated in cursor.fetchall():
        if latest_nav:
            if current_value and abs(current_value - calculated) > 1.0:  # 差异大于1元
                issues.append(f"{code}: 数据库市值{current_value:.2f} vs 计算市值{calculated:.2f}")
                print(f"  ⚠️ {code}: 市值不一致 (DB: {current_value:.2f}, Calc: {calculated:.2f})")
            else:
                print(f"  ✅ {code}: 市值一致 ({calculated:.2f})")
        else:
            print(f"  ❌ {code}: 无最新净值数据")
            issues.append(f"{code}: 无最新净值数据")
    
    if issues:
        print(f"\n⚠️ 持仓数据有{len(issues)}个不一致问题")
        return False
    else:
        print("\n✅ 持仓数据一致性检查通过")
        return True

if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("基金净值数据验证工具")
    print("="*60)
    
    # 验证NAV数据
    nav_ok = validate_nav_data()
    
    # 检查持仓一致性
    holdings_ok = check_holdings_consistency()
    
    print("\n" + "="*60)
    if nav_ok and holdings_ok:
        print("🎉 所有检查通过！数据状态良好")
        sys.exit(0)
    else:
        print("⚠️ 发现问题，建议运行:")
        print("  python scripts/update_nav_curl.py  # 更新净值")
        print("  python scripts/db_init.py         # 如需重新初始化数据库")
        sys.exit(1)
