"""
基金→产业链定位模块 (Fund Chain Mapper)

将基金持仓映射到产业链环节：
- 基于名称关键词推断产业链敞口
- 基于持仓股票推断产业链位置
- 计算多基金的产业链重叠度

Usage:
    from chain_map import IndustryChainMap
    from fund_chain_mapper import FundChainMapper
    cmap = IndustryChainMap()
    mapper = FundChainMapper(cmap)
    print(mapper.map_fund('020692', '博时中证全指通信设备指数C'))
"""

from typing import Dict, List, Optional
from chain_data import FUND_CHAIN_KEYWORDS


class FundChainMapper:
    """基金→产业链定位"""

    def __init__(self, chain_map):
        self.chain_map = chain_map
        self.keyword_map = FUND_CHAIN_KEYWORDS

    def map_fund(self, fund_code: str, fund_name: str) -> Dict:
        """
        定位基金在产业链中的位置

        返回:
        {
            'fund_code': str,
            'fund_name': str,
            'chain_exposures': [
                {
                    'chain': str,           # 产业链名称
                    'weight': float,        # 敞口权重
                    'segments': [str],      # 涉及环节
                    'segment_names': [str], # 环节中文名
                    'position': str,        # 主要位置(upstream/midstream/downstream)
                }
            ],
            'primary_chain': str,  # 主产业链
            'chain_diversity': float,  # 产业链分散度(0-1)
        }
        """
        exposures = self._infer_from_name(fund_name)

        if not exposures:
            exposures = self._default_exposure()

        # 计算主要产业链
        primary = max(exposures, key=lambda x: x['weight'])

        # 计算分散度 (1 - HHI)
        total_weight = sum(e['weight'] for e in exposures)
        hhi = sum((e['weight'] / total_weight) ** 2 for e in exposures) if total_weight > 0 else 1
        diversity = 1 - hhi

        return {
            'fund_code': fund_code,
            'fund_name': fund_name,
            'chain_exposures': exposures,
            'primary_chain': primary['chain'],
            'chain_diversity': round(diversity, 3),
        }

    def _infer_from_name(self, fund_name: str) -> List[Dict]:
        """从基金名称推断产业链敞口"""
        # 按关键词长度降序匹配（优先匹配更精确的关键词）
        sorted_keywords = sorted(self.keyword_map.items(), key=lambda x: len(x[0]), reverse=True)

        for keyword, exposures in sorted_keywords:
            if keyword in fund_name:
                result = []
                for exp in exposures:
                    chain = self.chain_map.get_chain(exp['chain'])
                    if not chain:
                        continue
                    segment_names = []
                    for seg_key in exp['segments']:
                        seg = chain['segments'].get(seg_key)
                        if seg:
                            segment_names.append(seg['name'])

                    # 确定主要位置
                    positions = []
                    for seg_key in exp['segments']:
                        seg = chain['segments'].get(seg_key)
                        if seg:
                            positions.append(seg.get('position', 'midstream'))
                    position = max(set(positions), key=positions.count) if positions else 'midstream'

                    result.append({
                        'chain': exp['chain'],
                        'weight': exp['weight'],
                        'segments': exp['segments'],
                        'segment_names': segment_names,
                        'position': position,
                    })
                return result

        return []

    def _default_exposure(self) -> List[Dict]:
        """默认敞口（无法推断时）"""
        return [{
            'chain': '未知',
            'weight': 1.0,
            'segments': [],
            'segment_names': [],
            'position': 'unknown',
        }]

    def map_fund_with_holdings(self, fund_code: str, fund_name: str,
                                holdings: List[Dict]) -> Dict:
        """
        基于持仓股票的产业链定位（更精确）

        holdings: [{'name': '贵州茅台', 'ratio': 8.5}, ...]
        """
        result = self.map_fund(fund_code, fund_name)

        if not holdings:
            return result

        # 遍历持仓，匹配产业链
        chain_scores = {}
        for holding in holdings:
            stock_name = holding.get('name', '')
            ratio = holding.get('ratio', 0)

            # 在所有产业链中查找该股票
            for chain_name, chain_data in self.chain_map.chains.items():
                for seg_key, seg_data in chain_data['segments'].items():
                    if stock_name in seg_data.get('representative', []):
                        if chain_name not in chain_scores:
                            chain_scores[chain_name] = {
                                'weight': 0,
                                'segments': set(),
                                'stocks': [],
                            }
                        chain_scores[chain_name]['weight'] += ratio
                        chain_scores[chain_name]['segments'].add(seg_key)
                        chain_scores[chain_name]['stocks'].append({
                            'stock': stock_name,
                            'ratio': ratio,
                            'segment': seg_key,
                        })

        if chain_scores:
            # 归一化权重
            total = sum(v['weight'] for v in chain_scores.values())
            exposures = []
            for chain_name, data in chain_scores.items():
                chain = self.chain_map.get_chain(chain_name)
                segment_names = [
                    chain['segments'][s]['name']
                    for s in data['segments']
                    if s in chain['segments']
                ] if chain else []

                exposures.append({
                    'chain': chain_name,
                    'weight': round(data['weight'] / total, 3) if total > 0 else 0,
                    'segments': list(data['segments']),
                    'segment_names': segment_names,
                    'stocks': data['stocks'],
                    'position': 'midstream',
                })

            result['chain_exposures'] = exposures
            result['primary_chain'] = max(exposures, key=lambda x: x['weight'])['chain']
            result['data_source'] = 'holdings'
        else:
            result['data_source'] = 'name_inference'

        return result

    def get_chain_exposure(self, fund_code: str, fund_name: str) -> Dict[str, float]:
        """获取基金的产业链敞口（简化版）"""
        result = self.map_fund(fund_code, fund_name)
        return {e['chain']: e['weight'] for e in result['chain_exposures']}

    def find_chain_overlap(self, fund1_code: str, fund1_name: str,
                           fund2_code: str, fund2_name: str) -> Dict:
        """
        查找两只基金的产业链重叠

        返回:
        {
            'overlap_chains': [{'chain': str, 'weight1': float, 'weight2': float}],
            'overlap_ratio': float,  # 重叠度(0-1)
            'diversification_benefit': str,  # 分散化评价
        }
        """
        exp1 = self.get_chain_exposure(fund1_code, fund1_name)
        exp2 = self.get_chain_exposure(fund2_code, fund2_name)

        overlap = []
        overlap_weight = 0
        for chain in set(exp1.keys()) & set(exp2.keys()):
            w1, w2 = exp1[chain], exp2[chain]
            overlap.append({
                'chain': chain,
                'weight1': w1,
                'weight2': w2,
                'overlap_weight': min(w1, w2),
            })
            overlap_weight += min(w1, w2)

        # 计算重叠度
        max_overlap = min(sum(exp1.values()), sum(exp2.values()))
        overlap_ratio = overlap_weight / max_overlap if max_overlap > 0 else 0

        # 评价
        if overlap_ratio > 0.7:
            benefit = '高度重叠，分散化效果差'
        elif overlap_ratio > 0.4:
            benefit = '中度重叠，有一定分散化效果'
        else:
            benefit = '低重叠，分散化效果好'

        return {
            'fund1': f"{fund1_code} {fund1_name}",
            'fund2': f"{fund2_code} {fund2_name}",
            'overlap_chains': overlap,
            'overlap_ratio': round(overlap_ratio, 3),
            'diversification_benefit': benefit,
        }

    def analyze_portfolio_chains(self, holdings: List[Dict]) -> Dict:
        """
        分析整个投资组合的产业链分布

        holdings: [{'code': '020692', 'name': '博时...', 'amount': 10000}, ...]
        """
        chain_total = {}
        fund_details = []
        total_amount = sum(h.get('amount', 0) for h in holdings)

        for h in holdings:
            code = h.get('code', '')
            name = h.get('name', '')
            amount = h.get('amount', 0)

            result = self.map_fund(code, name)
            fund_details.append({
                'code': code,
                'name': name,
                'amount': amount,
                'primary_chain': result['primary_chain'],
                'exposures': result['chain_exposures'],
            })

            # 累加产业链敞口
            for exp in result['chain_exposures']:
                chain = exp['chain']
                if chain not in chain_total:
                    chain_total[chain] = 0
                chain_total[chain] += amount * exp['weight']

        # 计算占比
        chain_allocation = {}
        for chain, amount in chain_total.items():
            chain_allocation[chain] = {
                'amount': round(amount, 2),
                'ratio': round(amount / total_amount * 100, 1) if total_amount > 0 else 0,
            }

        # 排序
        sorted_chains = sorted(chain_allocation.items(), key=lambda x: x[1]['amount'], reverse=True)

        return {
            'total_amount': total_amount,
            'chain_allocation': dict(sorted_chains),
            'fund_details': fund_details,
            'concentration': self._calc_concentration(chain_allocation),
        }

    def _calc_concentration(self, chain_allocation: Dict) -> Dict:
        """计算产业链集中度"""
        if not chain_allocation:
            return {'hhi': 0, 'top_chain': '', 'top_ratio': 0}

        total = sum(v['amount'] for v in chain_allocation.values())
        if total == 0:
            return {'hhi': 0, 'top_chain': '', 'top_ratio': 0}

        ratios = [v['amount'] / total for v in chain_allocation.values()]
        hhi = sum(r ** 2 for r in ratios)
        top = max(chain_allocation.items(), key=lambda x: x[1]['amount'])

        return {
            'hhi': round(hhi, 3),
            'top_chain': top[0],
            'top_ratio': round(top[1]['amount'] / total * 100, 1),
        }

    def format_fund_position(self, fund_code: str, fund_name: str) -> str:
        """格式化基金产业链定位（文本输出）"""
        result = self.map_fund(fund_code, fund_name)

        lines = []
        lines.append(f"基金产业链定位: {fund_code} {fund_name}")
        lines.append(f"{'─' * 50}")
        lines.append(f"主产业链: {result['primary_chain']}")
        lines.append(f"分散度: {result['chain_diversity']:.1%}")
        lines.append(f"{'─' * 50}")

        for exp in result['chain_exposures']:
            chain_name = exp['chain']
            weight = exp['weight']
            segs = ' → '.join(exp.get('segment_names', []))
            weight_bar = '█' * int(weight * 10) + '░' * (10 - int(weight * 10))
            lines.append(f"  {chain_name:<8} [{weight_bar}] {weight:.0%}")
            if segs:
                lines.append(f"    环节: {segs}")

        return '\n'.join(lines)

    def format_overlap(self, fund1_code: str, fund1_name: str,
                       fund2_code: str, fund2_name: str) -> str:
        """格式化两只基金的产业链重叠"""
        result = self.find_chain_overlap(fund1_code, fund1_name, fund2_code, fund2_name)

        lines = []
        lines.append(f"产业链重叠分析")
        lines.append(f"{'─' * 50}")
        lines.append(f"基金1: {result['fund1']}")
        lines.append(f"基金2: {result['fund2']}")
        lines.append(f"重叠度: {result['overlap_ratio']:.1%}")
        lines.append(f"评价: {result['diversification_benefit']}")
        lines.append(f"{'─' * 50}")

        if result['overlap_chains']:
            lines.append(f"  {'产业链':<8} {'基金1权重':<10} {'基金2权重':<10} {'重叠'}")
            for oc in result['overlap_chains']:
                lines.append(
                    f"  {oc['chain']:<8} {oc['weight1']:<10.0%} {oc['weight2']:<10.0%} "
                    f"{'█' * int(oc['overlap_weight'] * 10)}"
                )
        else:
            lines.append("  无产业链重叠")

        return '\n'.join(lines)


# ============================================================
# CLI 入口
# ============================================================
if __name__ == '__main__':
    from chain_map import IndustryChainMap
    cmap = IndustryChainMap()
    mapper = FundChainMapper(cmap)

    # 用户持仓基金
    FUNDS = [
        ('002112', '德邦鑫星'),
        ('005165', '富荣福锦'),
        ('014414', '招商中证畜牧养殖ETF联接A'),
        ('018388', '华泰柏瑞港股红利'),
        ('020692', '博时中证全指通信设备指数C'),
        ('022184', '富国全球科技互联网股票(QDII)C'),
        ('026211', '平安中证科技50ETF联接C'),
        ('027063', '鹏华创新驱动混合C'),
        ('257070', '国联安优选行业混合'),
        ('501205', '鹏华创新未来混合'),
    ]

    print(mapper.format_fund_position(FUNDS[0][0], FUNDS[0][1]))
    print()

    for code, name in FUNDS:
        print(mapper.format_fund_position(code, name))
        print()
