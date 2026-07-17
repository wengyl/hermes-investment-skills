#!/usr/bin/env python3
"""
更新基金净值数据 - 使用 curl 绕过网络限制
适用于 requests 库被防火墙阻挡的场景
"""
import sys
import os
import sqlite3
import subprocess
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_init import get_db_path

def get_fund_nav_curl(fund_code: str) -> dict:
    """
    使用 curl 获取基金最新净值
    返回：{'fund_code', 'nav_date', 'unit_nav', 'daily_return', 'timestamp'}
    """
    url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
    
    try:
        # 使用 curl 获取数据（绕过 requests 的网络限制）
        result = subprocess.run(
            ['curl', '-s', '-A', 'Mozilla/5.0', url],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"  curl 错误：{result.stderr}")
            return None
        
        # 解析返回的 JSON 数据（去掉函数调用包装）
        text = result.stdout.strip()
        if text.startswith('jsonpgz('):
            text = text[8:-2]  # 去掉 "jsonpgz(" 和 ");"
        
        data = json.loads(text)
        
        # 字段映射：jzrq=净值日期，dwjz=单位净值，gsz=估值，gszzl=估值涨幅，gztime=估值时间
        return {
            'fund_code': fund_code,
            'nav_date': data.get('jzrq', data.get('gsrq', '')),
            'unit_nav': float(data.get('dwjz', data.get('gsz', 0))),
            'daily_return': float(data.get('gszzl', 0)),
            'timestamp': data.get('gztime', data.get('timestamp', ''))
        }
    except Exception as e:
        print(f"✗ 获取 {fund_code} 净值失败：{e}")
        return None

def update_nav_for_holdings():
    """
    更新所有持仓基金的最新净值
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有持仓基金
    cursor.execute('''
        SELECT fund_code, fund_name 
        FROM holdings 
        WHERE share_count > 0
        ORDER BY fund_code
    ''')
    
    holdings = cursor.fetchall()
    
    if not holdings:
        print("📭 暂无持仓基金")
        conn.close()
        return
    
    print(f"🔄 开始更新 {len(holdings)} 只基金的净值数据...\n")
    
    updated_count = 0
    failed_count = 0
    
    for fund_code, fund_name in holdings:
        print(f"📊 处理：{fund_code} {fund_name}")
        
        # 获取最新净值
        latest_nav = get_fund_nav_curl(fund_code)
        
        if latest_nav:
            # 检查是否已存在今天的记录
            cursor.execute('''
                SELECT COUNT(*) FROM fund_nav_history 
                WHERE fund_code = ? AND nav_date = ?
            ''', (fund_code, latest_nav['nav_date']))
            
            exists = cursor.fetchone()[0]
            
            if exists > 0:
                # 更新现有记录
                cursor.execute('''
                    UPDATE fund_nav_history 
                    SET unit_nav = ?, daily_return = ?
                    WHERE fund_code = ? AND nav_date = ?
                ''', (latest_nav['unit_nav'], latest_nav['daily_return'], 
                      fund_code, latest_nav['nav_date']))
            else:
                # 插入新记录
                cursor.execute('''
                    INSERT INTO fund_nav_history 
                    (fund_code, nav_date, unit_nav, daily_return)
                    VALUES (?, ?, ?, ?)
                ''', (fund_code, latest_nav['nav_date'], 
                      latest_nav['unit_nav'], latest_nav['daily_return']))
            
            # 同时更新持仓的当前价值
            cursor.execute('''
                SELECT share_count FROM holdings WHERE fund_code = ?
            ''', (fund_code,))
            
            result = cursor.fetchone()
            if result:
                shares = result[0]
                current_value = shares * latest_nav['unit_nav']
                
                cursor.execute('''
                    UPDATE holdings 
                    SET current_value = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE fund_code = ?
                ''', (current_value, fund_code))
            
            print(f"  ✓ 更新成功：净值={latest_nav['unit_nav']:.4f}, 日涨跌={latest_nav['daily_return']:.2f}%")
            updated_count += 1
        else:
            print(f"  ✗ 更新失败")
            failed_count += 1
        
        print()
    
    conn.commit()
    conn.close()
    
    print(f"📊 更新完成：成功 {updated_count} 只，失败 {failed_count} 只")

def main():
    """主函数"""
    update_nav_for_holdings()

if __name__ == "__main__":
    main()
