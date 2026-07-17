"""
基金持仓查询脚本模板

用于查询所有持仓基金的实时净值和涨跌情况
"""
import http.client
import ssl
import json
import sqlite3
from datetime import datetime

class FundQueryTool:
    """基金查询工具"""
    
    def __init__(self, db_path):
        self.context = ssl.create_default_context()
        self.context.check_hostname = False
        self.context.verify_mode = ssl.CERT_NONE
        self.db_path = db_path
    
    def _make_request(self, host, path, headers=None):
        """发送 HTTP 请求"""
        try:
            conn = http.client.HTTPSConnection(
                host, port=443, timeout=15, context=self.context
            )
            
            if headers is None:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'Referer': 'https://fund.eastmoney.com/'
                }
            
            conn.request('GET', path, headers=headers)
            response = conn.getresponse()
            
            status = response.status
            raw_data = response.read()
            conn.close()
            
            # 尝试多种编码
            for encoding in ['utf-8', 'gbk', 'gb2312']:
                try:
                    return status, raw_data.decode(encoding)
                except:
                    continue
            
            return status, raw_data
            
        except Exception as e:
            return None, str(e)
    
    def get_fund_nav(self, fund_code):
        """获取基金净值"""
        host = 'fundgz.1234567.com.cn'
        path = f'/js/{fund_code}.js'
        
        status, data = self._make_request(host, path)
        
        if status != 200:
            return None
        
        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            
            # 解析 JSONP
            data = data.replace('jsonpgz(', '').replace(');', '').strip()
            result = json.loads(data)
            
            return {
                'fund_code': result.get('fundcode'),
                'fund_name': result.get('name'),
                'nav': float(result.get('dwjz', 0)),
                'nav_rate': float(result.get('gszzl', 0)),
                'nav_date': result.get('jzrq'),
                'update_time': result.get('gztime')
            }
        except Exception as e:
            print(f"❌ 解析失败：{e}")
            return None
    
    def query_all_holdings(self):
        """查询所有持仓"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT fund_code, fund_name, share_count, avg_cost
            FROM holdings
            WHERE share_count > 0
            ORDER BY fund_code
        ''')
        
        holdings = cursor.fetchall()
        conn.close()
        
        if not holdings:
            return "📭 暂无持仓记录"
        
        # 查询实时数据
        results = []
        for code, name, shares, cost in holdings:
            nav_data = self.get_fund_nav(code)
            if nav_data:
                results.append({
                    'code': code,
                    'name': nav_data['fund_name'],
                    'nav': nav_data['nav'],
                    'nav_rate': nav_data['nav_rate'],
                    'type': '未知',  # 可扩展类型识别
                    'shares': shares,
                    'cost': cost
                })
        
        return self.format_holdings_table(results)
    
    def format_holdings_table(self, holdings):
        """格式化持仓表格"""
        if not holdings:
            return "❌ 没有持仓数据"
        
        output = []
        output.append("## 🎉 成功查询到所有基金！")
        output.append("")
        output.append("### 📊 你的基金持仓列表")
        output.append("")
        output.append("| 序号 | 基金代码 | 基金名称 | 净值 | 日涨跌 | 类型 |")
        output.append("|------|---------|---------|------|--------|------|")
        
        for i, fund in enumerate(holdings, 1):
            nav_rate = fund['nav_rate']
            if nav_rate > 0:
                change_str = f"+{nav_rate:.2f}% ⬆️"
            elif nav_rate < 0:
                change_str = f"{nav_rate:.2f}%"
            else:
                change_str = "0.00%"
            
            output.append(
                f"| {i} | **{fund['code']}** | {fund['name']} | "
                f"{fund['nav']:.4f} | {change_str} | {fund['type']} |"
            )
        
        output.append("")
        output.append(f"**共计 {len(holdings)} 只基金**")
        output.append("")
        output.append("💡 提示：数据来源于天天基金网，如显示不完整请查看完整输出")
        
        return "\n".join(output)


def main():
    """主函数"""
    db_path = "/Users/wyl/.hermes/fund-advisor/data/fund_system.db"
    tool = FundQueryTool(db_path)
    
    print("=" * 80)
    print("📱 基金持仓查询工具")
    print("=" * 80)
    print()
    
    result = tool.query_all_holdings()
    print(result)
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
