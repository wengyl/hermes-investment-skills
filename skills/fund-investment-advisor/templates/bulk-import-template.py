"""
批量导入基金持仓脚本模板

用于快速导入多个基金的持仓数据
"""
import sqlite3
from datetime import datetime

# 基金持仓数据配置
# 可以根据实际情况修改
FUND_HOLDINGS = [
    {
        "code": "000001",        # 6 位基金代码
        "name": "基金名称",      # 基金全称
        "shares": 1000,          # 持有份额
        "cost": 1.0              # 平均成本价
    },
    # 添加更多基金...
]

def import_holdings(db_path, holdings_data):
    """
    导入持仓数据
    
    Args:
        db_path: SQLite 数据库路径
        holdings_data: 持仓数据列表
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    today = datetime.now().date()
    
    for fund in holdings_data:
        code = fund['code']
        name = fund['name']
        shares = fund['shares']
        cost = fund['cost']
        
        # 插入或更新持仓
        cursor.execute('''
            INSERT INTO holdings (
                fund_code, fund_name, share_count, avg_cost, 
                total_invested, first_buy_date, last_update_date,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fund_code) DO UPDATE SET
                share_count = excluded.share_count,
                avg_cost = excluded.avg_cost,
                total_invested = excluded.total_invested,
                last_update_date = excluded.last_update_date,
                updated_at = excluded.updated_at
        ''', (
            code, name, shares, cost,
            shares * cost,
            today, today,
            datetime.now(), datetime.now()
        ))
        
        print(f"✅ 已导入：{name} ({code})")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 成功导入 {len(holdings_data)} 只基金")


if __name__ == "__main__":
    db_path = "/Users/wyl/.hermes/fund-advisor/data/fund_system.db"
    import_holdings(db_path, FUND_HOLDINGS)
