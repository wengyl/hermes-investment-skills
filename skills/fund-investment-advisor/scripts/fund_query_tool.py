"""
Fund Query Tool - 天天基金 API 查询工具

使用 http.client 绕过 requests 的 SSL 问题
支持查询基金净值、基本信息
"""
import http.client
import ssl
import json
import urllib.parse


class FundQueryTool:
    """基金查询工具 - 使用底层 http.client"""
    
    def __init__(self):
        self.context = ssl.create_default_context()
        self.context.check_hostname = False
        self.context.verify_mode = ssl.CERT_NONE
    
    def _make_request(self, host, path, headers=None):
        """发送 HTTP 请求"""
        try:
            conn = http.client.HTTPSConnection(
                host,
                port=443,
                timeout=15,
                context=self.context
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
            
            # 尝试多种编码解码
            for encoding in ['utf-8', 'gbk', 'gb2312']:
                try:
                    data = raw_data.decode(encoding)
                    return status, data
                except:
                    continue
            
            return status, raw_data
            
        except Exception as e:
            return None, str(e)
    
    def get_fund_nav(self, fund_code):
        """
        获取基金净值（最可靠的 API）
        
        Args:
            fund_code: 6 位基金代码
        
        Returns:
            dict: {fund_code, fund_name, nav, nav_rate, nav_date, update_time}
            None: 如果查询失败
        """
        host = 'fundgz.1234567.com.cn'
        path = f'/js/{fund_code}.js'
        
        status, data = self._make_request(host, path)
        
        if status != 200:
            print(f"❌ 请求失败，状态码：{status}")
            return None
        
        try:
            # 解析 JSONP 格式
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            
            # 移除 JSONP 包装
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
    
    def get_fund_info(self, fund_code):
        """
        获取基金详细信息
        
        Args:
            fund_code: 6 位基金代码
        
        Returns:
            dict: 基金信息
            None: 如果查询失败
        """
        host = 'api.fund.eastmoney.com'
        path = f'/f10/jjjb?fundcode={fund_code}'
        
        status, data = self._make_request(host, path)
        
        if status != 200:
            print(f"❌ 请求失败，状态码：{status}")
            return None
        
        try:
            if isinstance(data, bytes):
                data = data.decode('gbk')
            
            result = json.loads(data)
            
            if result.get('Data'):
                return result['Data']
            else:
                print(f"⚠️ 未找到基金信息")
                return None
                
        except Exception as e:
            print(f"❌ 解析失败：{e}")
            return None
    
    def search_fund(self, keyword):
        """
        搜索基金（API 可能不稳定）
        
        Args:
            keyword: 基金名称关键词
        
        Returns:
            list: 基金列表
            []: 如果查询失败或未找到
        """
        host = 'api.fund.eastmoney.com'
        params = urllib.parse.urlencode({
            'keyword': keyword,
            'pageIndex': 1,
            'pageSize': 5
        })
        path = f'/FundGalaxy/GetFundSearchResult?{params}'
        
        status, data = self._make_request(host, path)
        
        if status != 200:
            print(f"❌ 请求失败，状态码：{status}")
            return []
        
        try:
            if isinstance(data, bytes):
                data = data.decode('gbk')
            
            result = json.loads(data)
            
            if result.get('Data') and result['Data'].get('Fund'):
                funds = result['Data']['Fund']
                print(f"✅ 找到 {len(funds)} 个结果")
                return funds
            else:
                print(f"⚠️ 未找到匹配结果")
                return []
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败：{e}")
            return []


# 使用示例
if __name__ == "__main__":
    tool = FundQueryTool()
    
    # 示例 1: 查询基金净值
    print("【示例 1】查询基金净值")
    nav = tool.get_fund_nav("000001")
    if nav:
        print(f"基金：{nav['fund_name']}")
        print(f"净值：{nav['nav']}")
        print(f"增长率：{nav['nav_rate']}%")
    
    print()
    
    # 示例 2: 查询基金信息
    print("【示例 2】查询基金信息")
    info = tool.get_fund_info("000001")
    if info:
        print(f"基金名称：{info.get('FUNDNAME')}")
        print(f"基金类型：{info.get('RZJJDWL')}")
        print(f"基金经理：{info.get('JJLM')}")
    
    print()
    
    # 示例 3: 搜索基金（可能失败）
    print("【示例 3】搜索基金")
    funds = tool.search_fund("沪深 300")
    if funds:
        for fund in funds[:3]:
            code = fund.get('FNDSCODE')
            name = fund.get('FUNDNAME')
            print(f"  [{code}] {name}")
