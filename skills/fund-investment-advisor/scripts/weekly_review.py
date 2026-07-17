#!/usr/bin/env python3
"""
周度策略复盘系统
每周日自动分析策略表现，识别问题，提出优化方向
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import statistics


class WeeklyReviewer:
    """周度复盘器"""
    
    def __init__(self, db_path: str, reports_dir: str):
        self.db_path = db_path
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)
    
    def get_weekly_dates(self) -> Tuple[str, str]:
        """获取本周的起止日期（周一到周日）"""
        today = datetime.now()
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        sunday = monday + timedelta(days=6)
        return monday.strftime('%Y-%m-%d'), sunday.strftime('%Y-%m-%d')
    
    def analyze_weekly_performance(self, start_date: str, end_date: str) -> Dict:
        """分析本周表现"""
        print(f"📊 分析周度表现: {start_date} 至 {end_date}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取本周净值数据
        cursor.execute('''
            SELECT fund_code, nav_date, unit_nav, daily_return
            FROM fund_nav_history
            WHERE nav_date BETWEEN ? AND ?
            ORDER BY fund_code, nav_date
        ''', (start_date, end_date))
        
        nav_data = cursor.fetchall()
        fund_performance = {}
        
        for code, date, nav, daily_return in nav_data:
            if code not in fund_performance:
                fund_performance[code] = []
            fund_performance[code].append({
                'date': date,
                'nav': nav,
                'daily_return': daily_return if daily_return else 0
            })
        
        # 获取持仓信息
        cursor.execute('''
            SELECT fund_code, fund_name, share_count, avg_cost, current_value
            FROM holdings WHERE share_count > 0
        ''')
        
        holdings = {}
        for code, name, shares, avg_cost, current_value in cursor.fetchall():
            holdings[code] = {'name': name, 'shares': shares, 'avg_cost': avg_cost, 'current_value': current_value}
        
        conn.close()
        
        # 计算各基金周度表现
        weekly_summary = []
        for code, nav_list in fund_performance.items():
            if len(nav_list) < 2:
                continue
            
            first_nav = nav_list[0]['nav']
            last_nav = nav_list[-1]['nav']
            weekly_return = ((last_nav - first_nav) / first_nav * 100) if first_nav > 0 else 0
            
            daily_returns = [item['daily_return'] for item in nav_list]
            volatility = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 0
            max_drawdown = self._calculate_max_drawdown([item['nav'] for item in nav_list])
            
            up_days = len([r for r in daily_returns if r > 0])
            win_rate = (up_days / len(daily_returns) * 100) if daily_returns else 0
            
            fund_info = holdings.get(code, {'name': f'基金{code}', 'shares': 0, 'avg_cost': 0, 'current_value': 0})
            
            weekly_summary.append({
                'code': code,
                'name': fund_info['name'],
                'weekly_return': weekly_return,
                'volatility': volatility,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'trading_days': len(nav_list),
                'current_value': fund_info['current_value']
            })
        
        weekly_summary.sort(key=lambda x: x['weekly_return'], reverse=True)
        return {'period': {'start': start_date, 'end': end_date}, 'fund_performance': weekly_summary, 'total_funds': len(weekly_summary)}
    
    def _calculate_max_drawdown(self, nav_list: List[float]) -> float:
        """计算最大回撤"""
        if not nav_list:
            return 0
        peak = nav_list[0]
        max_drawdown = 0
        for nav in nav_list[1:]:
            if nav > peak:
                peak = nav
            drawdown = (peak - nav) / peak * 100 if peak > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        return max_drawdown
    
    def identify_problems(self, weekly_data: Dict) -> List[Dict]:
        """识别策略问题"""
        problems = []
        funds = weekly_data.get('fund_performance', [])
        
        # 1. 收益问题
        negative_funds = [f for f in funds if f['weekly_return'] < -3]
        if negative_funds:
            problems.append({'type': '收益问题', 'severity': '高', 'description': f'有{len(negative_funds)}只基金本周亏损超过3%', 'funds': [f['code'] for f in negative_funds], 'suggestion': '分析亏损原因，考虑调整仓位或止损'})
        
        # 2. 波动率问题
        high_vol_funds = [f for f in funds if f['volatility'] > 3]
        if high_vol_funds:
            problems.append({'type': '波动率过高', 'severity': '中', 'description': f'有{len(high_vol_funds)}只基金波动率超过3%', 'funds': [f['code'] for f in high_vol_funds], 'suggestion': '高波动基金需要更严格的止损策略'})
        
        # 3. 回撤问题
        high_dd_funds = [f for f in funds if f['max_drawdown'] > 5]
        if high_dd_funds:
            problems.append({'type': '回撤过大', 'severity': '高', 'description': f'有{len(high_dd_funds)}只基金本周最大回撤超过5%', 'funds': [f['code'] for f in high_dd_funds], 'suggestion': '检查止损设置是否合理，考虑降低仓位'})
        
        # 4. 胜率问题
        low_winrate_funds = [f for f in funds if f['win_rate'] < 30]
        if low_winrate_funds:
            problems.append({'type': '胜率过低', 'severity': '中', 'description': f'有{len(low_winrate_funds)}只基金胜率低于30%', 'funds': [f['code'] for f in low_winrate_funds], 'suggestion': '基金表现不稳定，考虑更换或减少配置'})
        
        # 5. 集中度问题
        if funds:
            top3_value = sum(f['current_value'] for f in funds[:3])
            total_value = sum(f['current_value'] for f in funds)
            if total_value > 0:
                concentration = (top3_value / total_value * 100)
                if concentration > 70:
                    problems.append({'type': '持仓集中度过高', 'severity': '中', 'description': f'前3只基金占比{concentration:.1f}%，超过70%', 'suggestion': '适当分散投资，降低单一基金风险'})
        
        return problems
    
    def generate_optimization_suggestions(self, weekly_data: Dict, problems: List[Dict]) -> List[Dict]:
        """生成优化建议"""
        suggestions = []
        funds = weekly_data.get('fund_performance', [])
        
        if funds:
            best_fund = funds[0]
            worst_fund = funds[-1]
            
            if best_fund['weekly_return'] > 5:
                suggestions.append({'category': '止盈建议', 'priority': '高', 'content': f"{best_fund['name']} 本周涨幅{best_fund['weekly_return']:.1f}%，考虑分批止盈", 'action': '止盈1/3仓位'})
            
            if worst_fund['weekly_return'] < -5:
                suggestions.append({'category': '止损建议', 'priority': '高', 'content': f"{worst_fund['name']} 本周跌幅{worst_fund['weekly_return']:.1f}%，考虑止损", 'action': '止损或减仓1/2'})
        
        high_vol_funds = [f for f in funds if f['volatility'] > 3]
        if high_vol_funds:
            suggestions.append({'category': '仓位调整', 'priority': '中', 'content': f"{len(high_vol_funds)}只高波动基金，建议降低仓位", 'action': '高波动基金仓位降至10%以下'})
        
        low_winrate_funds = [f for f in funds if f['win_rate'] < 40]
        if low_winrate_funds:
            suggestions.append({'category': '持仓优化', 'priority': '中', 'content': f"{len(low_winrate_funds)}只基金胜率偏低，考虑更换", 'action': '评估是否更换为同类型其他基金'})
        
        suggestions.append({'category': '行业配置', 'priority': '低', 'content': '检查行业集中度，确保分散投资', 'action': '单一行业配置不超过30%'})
        suggestions.append({'category': '策略参数', 'priority': '中', 'content': '根据本周表现调整止盈止损参数', 'action': '止盈从30%调整为25%，止损从-15%调整为-10%'})
        
        return suggestions
    
    def generate_weekly_report(self) -> Dict:
        """生成周度复盘报告"""
        print("="*60)
        print("📅 周度策略复盘")
        print("="*60)
        
        start_date, end_date = self.get_weekly_dates()
        print(f"\n📈 复盘期间: {start_date} 至 {end_date}")
        
        weekly_data = self.analyze_weekly_performance(start_date, end_date)
        problems = self.identify_problems(weekly_data)
        suggestions = self.generate_optimization_suggestions(weekly_data, problems)
        
        report = {
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'review_period': {'start': start_date, 'end': end_date},
            'weekly_performance': weekly_data,
            'problems_identified': problems,
            'optimization_suggestions': suggestions,
            'summary': self._generate_summary(weekly_data, problems)
        }
        
        self.print_weekly_report(report)
        self.save_weekly_report(report)
        return report
    
    def _generate_summary(self, weekly_data: Dict, problems: List[Dict]) -> Dict:
        """生成总结"""
        funds = weekly_data.get('fund_performance', [])
        if not funds:
            return {'status': '无数据', 'score': 0}
        
        avg_return = sum(f['weekly_return'] for f in funds) / len(funds)
        problem_count = len(problems)
        high_severity_count = len([p for p in problems if p['severity'] == '高'])
        
        score = 100
        score -= high_severity_count * 20
        score -= (problem_count - high_severity_count) * 10
        
        if avg_return > 3:
            score += 10
        elif avg_return > 0:
            score += 5
        elif avg_return < -3:
            score -= 15
        
        score = max(0, min(100, score))
        
        if score >= 80:
            status = '优秀'
        elif score >= 60:
            status = '良好'
        elif score >= 40:
            status = '一般'
        else:
            status = '需改进'
        
        return {'status': status, 'score': score, 'avg_return': avg_return, 'problem_count': problem_count, 'high_severity_count': high_severity_count}
    
    def print_weekly_report(self, report: Dict):
        """打印周度报告"""
        print("\n" + "="*70)
        print("📊 周度策略复盘报告")
        print("="*70)
        
        period = report.get('review_period', {})
        print(f"\n📅 复盘期间: {period.get('start', '')} 至 {period.get('end', '')}")
        
        summary = report.get('summary', {})
        print(f"📈 综合评分: {summary.get('score', 0)}/100 ({summary.get('status', '')})")
        print(f"📊 平均收益: {summary.get('avg_return', 0):.2f}%")
        
        print(f"\n📈 周度表现排名:")
        print("-"*70)
        print(f"{'排名':<6}{'基金名称':<25}{'周收益率':<12}{'波动率':<10}{'最大回撤':<10}{'胜率':<8}")
        print("-"*70)
        
        funds = report.get('weekly_performance', {}).get('fund_performance', [])
        for i, fund in enumerate(funds[:10], 1):
            print(f"{i:<6}{fund['name'][:23]:<25}{fund['weekly_return']:>10.2f}%  {fund['volatility']:>8.2f}%  {fund['max_drawdown']:>8.2f}%  {fund['win_rate']:>6.1f}%")
        print("-"*70)
        
        problems = report.get('problems_identified', [])
        if problems:
            print(f"\n⚠️ 识别到 {len(problems)} 个问题:")
            for i, problem in enumerate(problems, 1):
                severity_icon = "🔴" if problem['severity'] == '高' else "🟡" if problem['severity'] == '中' else "🟢"
                print(f"  {i}. {severity_icon} [{problem['type']}] {problem['description']}")
                print(f"     建议: {problem['suggestion']}")
        else:
            print(f"\n✅ 未识别到明显问题")
        
        suggestions = report.get('optimization_suggestions', [])
        if suggestions:
            print(f"\n💡 优化建议 ({len(suggestions)} 条):")
            for i, suggestion in enumerate(suggestions, 1):
                priority_icon = "🔴" if suggestion['priority'] == '高' else "🟡" if suggestion['priority'] == '中' else "🟢"
                print(f"  {i}. {priority_icon} [{suggestion['category']}] {suggestion['content']}")
                print(f"     操作: {suggestion['action']}")
        
        print(f"\n🔮 下周展望:")
        print("  • 关注市场整体趋势和资金流向")
        print("  • 监控高波动基金的表现")
        print("  • 准备执行本周提出的优化建议")
        print("  • 定期检查止损设置是否合理")
        print("\n" + "="*70)
    
    def save_weekly_report(self, report: Dict):
        """保存周度报告"""
        today = datetime.now()
        filename = f"weekly_review_{today.strftime('%Y%m%d')}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 周度报告已保存到: {filepath}")
        
        latest_path = os.path.join(self.reports_dir, 'weekly_review_latest.json')
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"✅ 最新报告已保存到: {latest_path}")


def main():
    """主函数：运行周度复盘"""
    reviewer = WeeklyReviewer(
        db_path=os.path.expanduser('~/.hermes/fund-advisor/data/fund_system.db'),
        reports_dir=os.path.expanduser('~/.hermes/fund-advisor/reports')
    )
    return reviewer.generate_weekly_report()


if __name__ == '__main__':
    main()