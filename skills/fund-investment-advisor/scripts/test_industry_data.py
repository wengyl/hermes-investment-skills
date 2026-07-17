#!/usr/bin/env python3
"""
测试行业数据源可用性
用法: python3 scripts/test_industry_data.py
"""
import subprocess
import json
import re
import sys

def test_eastmoney_push2():
    """测试东方财富 push2 API"""
    url = 'https://push2.eastmoney.com/api/qt/clist/get?fid=f62&po=1&pz=5&pn=1&np=1&fltt=2&invt=2&fs=m:90+t:2&fields=f12,f14,f62,f184'
    
    result = subprocess.run(
        ['curl', '-s', '-A', 'Mozilla/5.0', '-m', '10', url],
        capture_output=True, text=True, timeout=15
    )
    
    if result.returncode != 0 or not result.stdout:
        return {'status': 'fail', 'reason': f'curl exit {result.returncode}, empty response'}
    
    try:
        data = json.loads(result.stdout)
        if data.get('data') and data['data'].get('diff'):
            return {'status': 'ok', 'count': len(data['data']['diff'])}
        return {'status': 'fail', 'reason': 'no data in response'}
    except:
        return {'status': 'fail', 'reason': 'JSON parse error'}

def test_sina_industry():
    """测试新浪财经行业数据"""
    url = 'http://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php'
    
    result = subprocess.run(
        ['curl', '-s', '-A', 'Mozilla/5.0', '-m', '10', url],
        capture_output=True, timeout=15
    )
    
    if result.returncode != 0 or not result.stdout:
        return {'status': 'fail', 'reason': f'curl exit {result.returncode}'}
    
    try:
        text = result.stdout.decode('gbk', errors='ignore')
        match = re.search(r'var\s+S_Finance_bankuai_sinaindustry\s*=\s*(\{.*?\})\s*;?\s*$', text, re.MULTILINE | re.DOTALL)
        if not match:
            return {'status': 'fail', 'reason': 'variable not found'}
        
        entries = re.findall(r'"([^"]+)":"([^"]+)"', match.group(1))
        return {'status': 'ok', 'count': len(entries)}
    except Exception as e:
        return {'status': 'fail', 'reason': str(e)}

def test_tencent_index():
    """测试腾讯指数数据"""
    url = 'http://qt.gtimg.cn/q=sh000001'
    
    result = subprocess.run(
        ['curl', '-s', '-m', '10', url],
        capture_output=True, timeout=15
    )
    
    if result.returncode != 0 or not result.stdout:
        return {'status': 'fail', 'reason': f'curl exit {result.returncode}'}
    
    try:
        text = result.stdout.decode('gbk', errors='ignore')
        if '上证指数' in text:
            return {'status': 'ok'}
        return {'status': 'fail', 'reason': 'unexpected content'}
    except Exception as e:
        return {'status': 'fail', 'reason': str(e)}

if __name__ == '__main__':
    print("=== 行业数据源测试 ===\n")
    
    tests = [
        ('东方财富 push2 (行业资金流向)', test_eastmoney_push2),
        ('新浪财经 (行业涨跌幅)', test_sina_industry),
        ('腾讯财经 (指数数据)', test_tencent_index),
    ]
    
    all_ok = True
    for name, test_fn in tests:
        result = test_fn()
        status = '✅' if result['status'] == 'ok' else '❌'
        detail = f" ({result.get('count', '')}条)" if result.get('count') else f" - {result.get('reason', '')}"
        print(f"{status} {name}{detail}")
        if result['status'] != 'ok':
            all_ok = False
    
    print(f"\n{'全部通过' if all_ok else '部分失败'}")
    sys.exit(0 if all_ok else 1)
