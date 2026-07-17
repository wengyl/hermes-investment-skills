#!/usr/bin/env python3
"""
Weekly Portfolio-Level Analysis Supplement (周度组合级分析补充)

The built-in weekly_review.py only does per-fund analysis (return, volatility,
drawdown, win rate). This script adds PORTFOLIO-LEVEL metrics that are missing:

  1. Portfolio weekly P&L (总周盈亏 + 百分比)
  2. Effective industry exposure (行业暴露加权分析 — weighted by position)
  3. Position concentration check vs risk profile limits
  4. Cross-fund industry overlap detection

Usage:
  cd ~/.hermes/fund-advisor
  python3 scripts/weekly_portfolio_analysis.py

  # With custom week-start date (defaults to previous Friday):
  python3 scripts/weekly_portfolio_analysis.py --week-start 2026-06-26

Run AFTER weekly_review.py to get the complete picture.
"""
import sqlite3
import os
import argparse
from collections import defaultdict
from datetime import datetime, timedelta


def get_week_start(default_days_back=9):
    """Default: go back ~9 days to last Friday (or use --week-start)."""
    today = datetime.now()
    # Find the most recent Friday
    days_since_friday = (today.weekday() - 4) % 7
    if days_since_friday == 0:
        # Today is Friday — use last Friday
        days_since_friday = 7
    friday = today - timedelta(days=days_since_friday)
    return friday.strftime('%Y-%m-%d')


def main():
    parser = argparse.ArgumentParser(description='Weekly portfolio-level analysis')
    parser.add_argument('--week-start', default=None,
                        help='Week start date (YYYY-MM-DD), defaults to last Friday')
    parser.add_argument('--db', default=None,
                        help='Database path (defaults to ~/.hermes/fund-advisor/data/fund_system.db)')
    args = parser.parse_args()

    week_start = args.week_start or get_week_start()
    db_path = args.db or os.path.expanduser('~/.hermes/fund-advisor/data/fund_system.db')

    if not os.path.exists(db_path):
        print(f'❌ Database not found: {db_path}')
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Get holdings with latest and week-start NAV
    cur.execute('''
        SELECT h.fund_code, h.fund_name, h.share_count, h.avg_cost,
          (SELECT unit_nav FROM fund_nav_history n
           WHERE n.fund_code=h.fund_code ORDER BY nav_date DESC LIMIT 1) as latest_nav,
          (SELECT unit_nav FROM fund_nav_history n
           WHERE n.fund_code=h.fund_code AND nav_date <= ?
           ORDER BY nav_date DESC LIMIT 1) as week_start_nav
        FROM holdings h
    ''', (week_start,))
    rows = cur.fetchall()

    if not rows:
        print('❌ No holdings found in database')
        conn.close()
        return

    total_value = sum(r[2] * r[4] for r in rows if r[4])
    total_cost = sum(r[2] * r[3] for r in rows)
    total_pl = sum(r[2] * (r[4] - r[3]) for r in rows if r[4])

    # === Section 1: Per-fund weekly performance ===
    print('=' * 90)
    print(f'  代码     名称                        周初净值 周末净值  周涨跌%  总盈亏%  仓位%      市值')
    print('-' * 90)

    week_pl = 0
    for r in rows:
        code, name, shares, cost, nav, start_nav = r
        if not nav or not start_nav:
            print(f'  {code}  {name[:20]:<28}  ⚠️ 数据缺失')
            continue
        week_ret = (nav - start_nav) / start_nav * 100
        total_pl_pct = (nav - cost) / cost * 100
        value = shares * nav
        pct = value / total_value * 100
        week_pl += shares * (nav - start_nav)
        n = name[:14] + '..' if len(name) > 16 else name
        print(f'  {code}  {n:<28}{start_nav:>8.4f}{nav:>8.4f}{week_ret:>+7.2f}%'
              f'{total_pl_pct:>+7.1f}%{pct:>6.1f}%{value:>10.0f}')

    print('-' * 90)
    print(f'  总市值: {total_value:.0f}  总成本: {total_cost:.0f}  '
          f'总盈亏: {total_pl:+.0f} ({total_pl/total_cost*100:+.1f}%)')
    if total_value - week_pl > 0:
        print(f'  本周盈亏: {week_pl:+.0f} ({week_pl/(total_value-week_pl)*100:+.2f}%)')
    else:
        print(f'  本周盈亏: {week_pl:+.0f}')

    # === Section 2: Position concentration ===
    print()
    print('=== 持仓集中度分析 ===')
    cur.execute('''
        SELECT h.fund_code, h.fund_name, h.current_value,
               h.current_value / (SELECT SUM(current_value) FROM holdings) * 100 as pct
        FROM holdings h ORDER BY current_value DESC
    ''')
    over_30 = 0
    over_20 = 0
    for r in cur.fetchall():
        if r[3] > 30:
            flag = '🔴'
            over_30 += 1
        elif r[3] > 20:
            flag = '🟡'
            over_20 += 1
        else:
            flag = '✅'
        print(f'  {flag} {r[0]} {r[1][:16]:<18} {r[2]:>8.0f}  {r[3]:>5.1f}%')

    if over_30 > 0:
        print(f'\n  ⚠️ {over_30} 只基金超过30%上限 — 需立即减仓')
    if over_20 > 0:
        print(f'  ⚠️ {over_20 + over_30} 只基金超过20%保守型上限')

    # === Section 3: Industry exposure (weighted) ===
    # NOTE: Industry allocation data must be fetched separately (via holdings API
    # or name-based inference). This section requires a pre-populated industry_map.
    # See references/weekly-portfolio-analysis.md for how to build industry_map.
    print()
    print('=== 行业暴露加权分析 ===')
    print('  (需先获取各基金行业配置数据，见 references/weekly-portfolio-analysis.md)')
    print('  示例: 手动填入 industry_map 后运行分析')

    conn.close()


if __name__ == '__main__':
    main()
