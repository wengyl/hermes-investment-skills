"""
产业链传导信号分析模块 (Transmission Analyzer)

分析产业链传导信号：
- 事件影响分析（某环节发生变动 → 关联环节影响）
- 基金传导信号检查
- 产业链热度计算
- 传导路径可视化

Usage:
    from chain_map import IndustryChainMap
    from transmission_analyzer import TransmissionAnalyzer
    cmap = IndustryChainMap()
    analyzer = TransmissionAnalyzer(cmap)
    impact = analyzer.analyze_impact('半导体', 'supply_shock', {'segment': '半导体材料', 'severity': 'high'})
"""

from typing import Dict, List, Optional
from chain_data import TRANSMISSION_TYPES


class TransmissionAnalyzer:
    """产业链传导信号分析"""

    def __init__(self, chain_map):
        self.chain_map = chain_map
        self.transmission_types = TRANSMISSION_TYPES

    # ============================================================
    # 事件影响分析
    # ============================================================

    def analyze_impact(self, chain_name: str, event_type: str, params: Dict) -> Dict:
        """
        分析某事件对产业链的影响

        参数:
            chain_name: 产业链名称
            event_type: 事件类型 (supply_shock / demand_surge / policy_change / tech_breakthrough / price_change)
            params: 事件参数
                - segment: 发生事件的环节 (可选，默认分析全链)
                - severity: 严重程度 (low/medium/high)
                - direction: 方向 (positive/negative)

        返回:
            {
                'chain': str,
                'event_type': str,
                'source_segment': str,
                'direct_impacts': [...],  # 直接影响
                'indirect_impacts': [...],  # 间接影响（传导）
                'total_affected': int,
                'summary': str,
            }
        """
        chain = self.chain_map.get_chain(chain_name)
        if not chain:
            return {'error': f'未找到产业链: {chain_name}'}

        source = params.get('segment', '')
        severity = params.get('severity', 'medium')
        direction = params.get('direction', 'negative')

        severity_score = {'low': 0.3, 'medium': 0.6, 'high': 0.9}.get(severity, 0.6)

        direct_impacts = []
        indirect_impacts = []

        # 如果指定了源环节，分析传导
        if source and source in chain['segments']:
            # 直接影响：与源环节相连的环节
            downstream = self.chain_map.get_downstream(chain_name, source)
            upstream = self.chain_map.get_upstream(chain_name, source)

            for ds in downstream:
                edge = ds['relation']
                impact_score = edge.get('strength', 0.5) * severity_score
                impact_direction = self._calc_impact_direction(
                    event_type, direction, edge['type'], 'downstream'
                )
                direct_impacts.append({
                    'segment': ds['segment_key'],
                    'segment_name': ds['segment_name'],
                    'direction': impact_direction,
                    'score': round(impact_score, 3),
                    'delay_months': edge.get('delay_months', 1),
                    'mechanism': edge['type'],
                    'mechanism_name': self.transmission_types.get(edge['type'], {}).get('name', edge['type']),
                })

            for us in upstream:
                edge = us['relation']
                impact_score = edge.get('strength', 0.5) * severity_score * 0.7  # 反向传导衰减
                impact_direction = self._calc_impact_direction(
                    event_type, direction, edge['type'], 'upstream'
                )
                direct_impacts.append({
                    'segment': us['segment_key'],
                    'segment_name': us['segment_name'],
                    'direction': impact_direction,
                    'score': round(impact_score, 3),
                    'delay_months': edge.get('delay_months', 1),
                    'mechanism': edge['type'],
                    'mechanism_name': self.transmission_types.get(edge['type'], {}).get('name', edge['type']),
                })

            # 间接影响：二阶传导
            for impact in direct_impacts:
                second_order = self._get_second_order(chain_name, source, impact, severity_score)
                indirect_impacts.extend(second_order)

        else:
            # 未指定源环节：分析全链影响
            for seg_key, seg_data in chain['segments'].items():
                impact_score = severity_score * 0.5
                direct_impacts.append({
                    'segment': seg_key,
                    'segment_name': seg_data['name'],
                    'direction': direction,
                    'score': round(impact_score, 3),
                    'delay_months': 0,
                    'mechanism': 'direct',
                    'mechanism_name': '直接影响',
                })

        # 排序
        direct_impacts.sort(key=lambda x: x['score'], reverse=True)
        indirect_impacts.sort(key=lambda x: x['score'], reverse=True)

        # 生成摘要
        summary = self._generate_impact_summary(
            chain_name, event_type, source, direct_impacts, indirect_impacts
        )

        return {
            'chain': chain_name,
            'event_type': event_type,
            'source_segment': source,
            'severity': severity,
            'direction': direction,
            'direct_impacts': direct_impacts,
            'indirect_impacts': indirect_impacts,
            'total_affected': len(direct_impacts) + len(indirect_impacts),
            'summary': summary,
        }

    def _calc_impact_direction(self, event_type: str, event_direction: str,
                                edge_type: str, propagation: str) -> str:
        """计算影响方向"""
        tt = self.transmission_types.get(edge_type, {})

        if edge_type == 'cost_push':
            if propagation == 'downstream':
                return 'negative' if event_direction == 'negative' else 'positive'
            else:
                return 'positive' if event_direction == 'negative' else 'negative'

        elif edge_type == 'demand_pull':
            if propagation == 'upstream':
                return 'positive' if event_direction == 'positive' else 'negative'
            else:
                return 'negative' if event_direction == 'positive' else 'positive'

        elif edge_type == 'capacity_link':
            if propagation == 'downstream':
                return 'positive' if event_direction == 'positive' else 'negative'
            else:
                return event_direction

        elif edge_type == 'tech_substitute':
            return 'negative'  # 技术替代通常对被替代方不利

        elif edge_type == 'policy_transmit':
            return event_direction  # 政策传导方向一致

        return event_direction

    def _get_second_order(self, chain_name: str, source: str,
                           first_impact: Dict, severity_score: float) -> List[Dict]:
        """计算二阶传导"""
        results = []
        chain = self.chain_map.get_chain(chain_name)
        if not chain:
            return results

        mid = first_impact['segment']
        # 跳过回到源环节的传导
        downstream = self.chain_map.get_downstream(chain_name, mid)
        upstream = self.chain_map.get_upstream(chain_name, mid)

        for ds in downstream:
            if ds['segment_key'] == source:
                continue
            edge = ds['relation']
            # 二阶衰减
            second_score = first_impact['score'] * edge.get('strength', 0.5) * 0.5
            if second_score < 0.05:
                continue
            delay = first_impact['delay_months'] + edge.get('delay_months', 1)
            results.append({
                'segment': ds['segment_key'],
                'segment_name': ds['segment_name'],
                'direction': self._calc_impact_direction(
                    'transmit', first_impact['direction'], edge['type'], 'downstream'
                ),
                'score': round(second_score, 3),
                'delay_months': delay,
                'mechanism': f"{first_impact['mechanism']}→{edge['type']}",
                'mechanism_name': f"经{first_impact['segment_name']}传导",
                'order': 2,
            })

        return results

    # ============================================================
    # 基金传导信号
    # ============================================================

    def check_fund_signals(self, fund_code: str, fund_name: str,
                            industry_capital_flow: Dict = None) -> List[Dict]:
        """
        检查基金相关的产业链传导信号

        参数:
            fund_code: 基金代码
            fund_name: 基金名称
            industry_capital_flow: 行业资金流向数据（可选，来自东方财富API）

        返回:
            [
                {
                    'chain': str,
                    'signal_type': str,  # 'capital_inflow' / 'capital_outflow' / 'chain_heat'
                    'direction': str,    # 'positive' / 'negative'
                    'description': str,
                    'score': float,
                    'affected_segments': [str],
                }
            ]
        """
        from fund_chain_mapper import FundChainMapper
        mapper = FundChainMapper(self.chain_map)
        fund_info = mapper.map_fund(fund_code, fund_name)

        signals = []

        for exposure in fund_info['chain_exposures']:
            chain_name = exposure['chain']
            chain = self.chain_map.get_chain(chain_name)
            if not chain:
                continue

            # 1. 检查产业链内各环节的资金流向
            if industry_capital_flow:
                chain_flow_signal = self._check_chain_capital_flow(
                    chain_name, industry_capital_flow
                )
                if chain_flow_signal:
                    chain_flow_signal['weight'] = exposure['weight']
                    signals.append(chain_flow_signal)

            # 2. 检查产业链热度
            heat_signal = self._check_chain_heat(chain_name, industry_capital_flow)
            if heat_signal:
                heat_signal['weight'] = exposure['weight']
                signals.append(heat_signal)

            # 3. 检查传导链上的信号
            chain_signals = self._check_transmission_chain(
                chain_name, exposure['segments']
            )
            for s in chain_signals:
                s['weight'] = exposure['weight']
            signals.extend(chain_signals)

        # 按 score 排序
        signals.sort(key=lambda x: x.get('score', 0) * x.get('weight', 1), reverse=True)
        return signals

    def _check_chain_capital_flow(self, chain_name: str,
                                    capital_flow: Dict) -> Optional[Dict]:
        """检查产业链的资金流向信号"""
        if not capital_flow or 'industries' not in capital_flow:
            return None

        chain = self.chain_map.get_chain(chain_name)
        if not chain:
            return None

        # 收集产业链涉及的申万行业
        chain_industries = set()
        for seg in chain['segments'].values():
            chain_industries.update(seg.get('shenwan_industries', []))

        # 在资金流向数据中查找匹配
        matched = []
        for flow in capital_flow['industries']:
            if flow.get('name', '') in chain_industries:
                matched.append(flow)

        if not matched:
            return None

        total_inflow = sum(m.get('net_inflow', 0) for m in matched)
        direction = 'positive' if total_inflow > 0 else 'negative'

        return {
            'chain': chain_name,
            'signal_type': 'capital_flow',
            'direction': direction,
            'score': min(abs(total_inflow) / 1e8, 1.0),  # 归一化
            'description': f"{chain_name}产业链资金{'流入' if total_inflow > 0 else '流出'}"
                          f" {abs(total_inflow)/1e8:.1f}亿",
            'affected_segments': list(chain['segments'].keys()),
            'matched_industries': [m['name'] for m in matched],
            'net_inflow': total_inflow,
        }

    def _check_chain_heat(self, chain_name: str,
                            capital_flow: Dict = None) -> Optional[Dict]:
        """检查产业链热度"""
        chain = self.chain_map.get_chain(chain_name)
        if not chain:
            return None

        # 简单热度评估：基于产业链的驱动因素数量和关键因素
        heat_score = 0
        reasons = []

        # 关键驱动因素
        drivers = chain.get('key_drivers', [])
        heat_score += len(drivers) * 0.1

        # 如果有资金流向数据，结合评估
        if capital_flow and 'industries' in capital_flow:
            chain_industries = set()
            for seg in chain['segments'].values():
                chain_industries.update(seg.get('shenwan_industries', []))

            hot_industries = capital_flow.get('summary', {}).get('top_inflow', [])
            for hi in hot_industries:
                if hi.get('name', '') in chain_industries:
                    heat_score += 0.3
                    reasons.append(f"{hi['name']}资金流入")

        if heat_score > 0.3:
            direction = 'positive' if heat_score > 0.5 else 'neutral'
            return {
                'chain': chain_name,
                'signal_type': 'chain_heat',
                'direction': direction,
                'score': min(heat_score, 1.0),
                'description': f"{chain_name}产业链热度{'高' if heat_score > 0.5 else '中'}"
                              f"（{', '.join(reasons[:3])}）" if reasons else
                              f"{chain_name}产业链关注度{'高' if heat_score > 0.5 else '中'}",
                'affected_segments': list(chain['segments'].keys()),
                'reasons': reasons,
            }

        return None

    def _check_transmission_chain(self, chain_name: str,
                                    fund_segments: List[str]) -> List[Dict]:
        """检查传导链上的信号"""
        signals = []
        chain = self.chain_map.get_chain(chain_name)
        if not chain:
            return signals

        for seg in fund_segments:
            # 检查上游变动对基金持仓环节的影响
            upstream = self.chain_map.get_upstream(chain_name, seg)
            for us in upstream:
                edge = us['relation']
                if edge.get('strength', 0) >= 0.7:
                    signals.append({
                        'chain': chain_name,
                        'signal_type': 'upstream_dependency',
                        'direction': 'neutral',
                        'score': edge['strength'] * 0.5,
                        'description': f"{us['segment_name']}→{chain['segments'].get(seg, {}).get('name', seg)}"
                                      f" 强依赖(强度{edge['strength']:.1f})",
                        'affected_segments': [seg],
                        'upstream_segment': us['segment_key'],
                        'delay_months': edge.get('delay_months', 1),
                    })

            # 检查下游需求对基金持仓环节的影响
            downstream = self.chain_map.get_downstream(chain_name, seg)
            for ds in downstream:
                edge = ds['relation']
                if edge.get('strength', 0) >= 0.7:
                    signals.append({
                        'chain': chain_name,
                        'signal_type': 'downstream_demand',
                        'direction': 'neutral',
                        'score': edge['strength'] * 0.5,
                        'description': f"{chain['segments'].get(seg, {}).get('name', seg)}→"
                                      f"{ds['segment_name']} 强拉动(强度{edge['strength']:.1f})",
                        'affected_segments': [seg],
                        'downstream_segment': ds['segment_key'],
                        'delay_months': edge.get('delay_months', 1),
                    })

        return signals

    # ============================================================
    # 传导路径分析
    # ============================================================

    def get_transmission_path(self, chain_name: str, from_seg: str, to_seg: str) -> Dict:
        """获取传导路径和延迟"""
        path = self.chain_map.find_path(chain_name, from_seg, to_seg)
        if not path:
            return {'error': f'未找到从 {from_seg} 到 {to_seg} 的传导路径'}

        total_delay = 0
        total_strength = 1.0
        for node in path:
            if 'from_edge' in node:
                edge = node['from_edge']
                total_delay += edge.get('delay_months', 0)
                total_strength *= edge.get('strength', 0.5)

        return {
            'chain': chain_name,
            'from': from_seg,
            'to': to_seg,
            'path': path,
            'path_length': len(path),
            'total_delay_months': total_delay,
            'cumulative_strength': round(total_strength, 3),
            'transmission_reliability': '高' if total_strength > 0.5 else '中' if total_strength > 0.2 else '低',
        }

    def calculate_chain_heat(self, industry_capital_flow: Dict) -> Dict[str, float]:
        """
        计算所有产业链的热度

        返回: {chain_name: heat_score}
        """
        heat_scores = {}

        for chain_name in self.chain_map.list_chains():
            signal = self._check_chain_heat(chain_name, industry_capital_flow)
            if signal:
                heat_scores[chain_name] = signal['score']
            else:
                heat_scores[chain_name] = 0.0

        return dict(sorted(heat_scores.items(), key=lambda x: x[1], reverse=True))

    # ============================================================
    # 格式化输出
    # ============================================================

    def _generate_impact_summary(self, chain_name: str, event_type: str,
                                   source: str, direct: List, indirect: List) -> str:
        """生成影响摘要"""
        event_names = {
            'supply_shock': '供给冲击',
            'demand_surge': '需求激增',
            'policy_change': '政策变动',
            'tech_breakthrough': '技术突破',
            'price_change': '价格变动',
        }
        event_name = event_names.get(event_type, event_type)

        chain = self.chain_map.get_chain(chain_name)
        source_name = chain['segments'].get(source, {}).get('name', source) if chain and source else '全链'

        parts = [f"{chain_name}产业链发生{event_name}（{source_name}）"]

        positive = [d for d in direct if d['direction'] == 'positive']
        negative = [d for d in direct if d['direction'] == 'negative']

        if positive:
            names = ', '.join(d['segment_name'] for d in positive[:3])
            parts.append(f"利好: {names}")
        if negative:
            names = ', '.join(d['segment_name'] for d in negative[:3])
            parts.append(f"利空: {names}")

        if indirect:
            parts.append(f"二阶传导影响{len(indirect)}个环节")

        return ' | '.join(parts)

    def format_impact_report(self, impact: Dict) -> str:
        """格式化影响分析报告"""
        lines = []
        lines.append(f"{'=' * 55}")
        lines.append(f"  产业链传导影响分析")
        lines.append(f"{'=' * 55}")
        lines.append(f"  产业链: {impact['chain']}")
        lines.append(f"  事件: {impact['event_type']}")
        lines.append(f"  源环节: {impact.get('source_segment', '全链')}")
        lines.append(f"  严重度: {impact.get('severity', 'N/A')}")
        lines.append(f"  受影响环节: {impact['total_affected']}个")
        lines.append(f"{'─' * 55}")

        # 直接影响
        if impact['direct_impacts']:
            lines.append(f"\n  直接影响:")
            lines.append(f"  {'环节':<10} {'方向':<6} {'强度':<8} {'传导机制':<10} {'延迟'}")
            lines.append(f"  {'─' * 48}")
            for imp in impact['direct_impacts']:
                dir_emoji = '📈' if imp['direction'] == 'positive' else '📉' if imp['direction'] == 'negative' else '➡️'
                score_bar = '█' * int(imp['score'] * 5) + '░' * (5 - int(imp['score'] * 5))
                lines.append(
                    f"  {imp['segment_name']:<10} {dir_emoji:<6} {score_bar} "
                    f"{imp['mechanism_name']:<10} {imp['delay_months']}月"
                )

        # 间接影响
        if impact['indirect_impacts']:
            lines.append(f"\n  间接影响（二阶传导）:")
            lines.append(f"  {'环节':<10} {'方向':<6} {'强度':<8} {'传导路径'}")
            lines.append(f"  {'─' * 48}")
            for imp in impact['indirect_impacts']:
                dir_emoji = '📈' if imp['direction'] == 'positive' else '📉'
                lines.append(
                    f"  {imp['segment_name']:<10} {dir_emoji:<6} {imp['score']:.2f}    "
                    f"{imp.get('mechanism_name', '')}"
                )

        lines.append(f"\n  摘要: {impact['summary']}")
        lines.append(f"{'=' * 55}")
        return '\n'.join(lines)

    def format_fund_signals(self, fund_code: str, fund_name: str,
                             signals: List[Dict]) -> str:
        """格式化基金传导信号报告"""
        lines = []
        lines.append(f"{'=' * 55}")
        lines.append(f"  基金产业链传导信号: {fund_code} {fund_name}")
        lines.append(f"{'=' * 55}")

        if not signals:
            lines.append("  暂无显著传导信号")
        else:
            lines.append(f"  {'信号类型':<12} {'方向':<6} {'评分':<6} {'描述'}")
            lines.append(f"  {'─' * 50}")
            for sig in signals:
                dir_emoji = '✅' if sig['direction'] == 'positive' else '⚠️' if sig['direction'] == 'negative' else '➡️'
                score = sig.get('score', 0) * sig.get('weight', 1)
                lines.append(
                    f"  {sig['signal_type']:<12} {dir_emoji:<6} {score:.2f}   "
                    f"{sig['description']}"
                )

        lines.append(f"{'=' * 55}")
        return '\n'.join(lines)

    def format_chain_heat(self, heat_scores: Dict[str, float]) -> str:
        """格式化产业链热度排名"""
        lines = []
        lines.append(f"{'=' * 45}")
        lines.append(f"  产业链热度排名")
        lines.append(f"{'=' * 45}")
        lines.append(f"  {'排名':<4} {'产业链':<8} {'热度':<8} {'热度条'}")
        lines.append(f"  {'─' * 40}")

        for i, (chain, score) in enumerate(heat_scores.items(), 1):
            bar = '█' * int(score * 10) + '░' * (10 - int(score * 10))
            heat_level = '🔥' if score > 0.5 else '🌡️' if score > 0.2 else '❄️'
            lines.append(f"  {i:<4} {chain:<8} {score:.2f}    {bar} {heat_level}")

        lines.append(f"{'=' * 45}")
        return '\n'.join(lines)


# ============================================================
# CLI 入口
# ============================================================
if __name__ == '__main__':
    from chain_map import IndustryChainMap

    cmap = IndustryChainMap()
    analyzer = TransmissionAnalyzer(cmap)

    # 示例：半导体材料供给冲击
    print("\n=== 示例: 半导体材料供给冲击 ===")
    impact = analyzer.analyze_impact(
        '半导体', 'supply_shock',
        {'segment': '半导体材料', 'severity': 'high', 'direction': 'negative'}
    )
    print(analyzer.format_impact_report(impact))

    # 示例：AI芯片需求激增
    print("\n=== 示例: AI芯片需求激增 ===")
    impact2 = analyzer.analyze_impact(
        'AI算力', 'demand_surge',
        {'segment': 'AI芯片', 'severity': 'high', 'direction': 'positive'}
    )
    print(analyzer.format_impact_report(impact2))

    # 示例：传导路径
    print("\n=== 示例: 传导路径 ===")
    path = analyzer.get_transmission_path('新能源车', '锂矿', '整车')
    print(f"锂矿 → 整车: 延迟{path.get('total_delay_months', 'N/A')}月, "
          f"强度{path.get('cumulative_strength', 'N/A')}, "
          f"可靠性{path.get('transmission_reliability', 'N/A')}")
