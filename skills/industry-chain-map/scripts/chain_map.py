"""
产业链图谱核心引擎 (Industry Chain Map Engine)

提供图谱操作 API：
- 获取产业链详情
- 查询上下游关系
- 查找传导路径
- ASCII 可视化输出
- 产业链关联分析

Usage:
    from chain_map import IndustryChainMap
    cmap = IndustryChainMap()
    print(cmap.format_chain_ascii('半导体'))
"""

from typing import Dict, List, Optional, Tuple
from collections import deque
from chain_data import ALL_CHAINS, SHENWAN_TO_CHAINS


class IndustryChainMap:
    """产业链图谱核心引擎"""

    def __init__(self):
        self.chains = ALL_CHAINS
        self.shenwan_index = SHENWAN_TO_CHAINS
        # 构建全局节点索引
        self._node_index = {}
        self._build_index()

    def _build_index(self):
        """构建全局节点索引：segment_key → {chain, segment_data}"""
        for chain_name, chain_data in self.chains.items():
            for seg_key, seg_data in chain_data['segments'].items():
                full_key = f"{chain_name}:{seg_key}"
                self._node_index[full_key] = {
                    'chain': chain_name,
                    'segment_key': seg_key,
                    'segment_data': seg_data,
                }
                # 也用 segment_name 索引
                self._node_index[seg_data['name']] = self._node_index[full_key]

    # ============================================================
    # 查询 API
    # ============================================================

    def get_chain(self, name: str) -> Optional[Dict]:
        """获取产业链详情"""
        return self.chains.get(name)

    def list_chains(self) -> List[str]:
        """列出所有产业链名称"""
        return list(self.chains.keys())

    def get_segments(self, chain_name: str) -> Dict:
        """获取产业链的所有环节"""
        chain = self.chains.get(chain_name)
        if chain:
            return chain['segments']
        return {}

    def get_upstream(self, chain_name: str, segment_key: str) -> List[Dict]:
        """获取某环节的上游环节"""
        chain = self.chains.get(chain_name)
        if not chain:
            return []
        upstream = []
        for edge in chain['edges']:
            if edge['to'] == segment_key:
                seg_data = chain['segments'].get(edge['from'], {})
                upstream.append({
                    'segment_key': edge['from'],
                    'segment_name': seg_data.get('name', edge['from']),
                    'relation': edge,
                })
        return upstream

    def get_downstream(self, chain_name: str, segment_key: str) -> List[Dict]:
        """获取某环节的下游环节"""
        chain = self.chains.get(chain_name)
        if not chain:
            return []
        downstream = []
        for edge in chain['edges']:
            if edge['from'] == segment_key:
                seg_data = chain['segments'].get(edge['to'], {})
                downstream.append({
                    'segment_key': edge['to'],
                    'segment_name': seg_data.get('name', edge['to']),
                    'relation': edge,
                })
        return downstream

    def get_segment_info(self, chain_name: str, segment_key: str) -> Optional[Dict]:
        """获取环节详细信息"""
        chain = self.chains.get(chain_name)
        if not chain:
            return None
        seg = chain['segments'].get(segment_key)
        if not seg:
            return None
        return {
            **seg,
            'chain': chain_name,
            'segment_key': segment_key,
            'upstream': self.get_upstream(chain_name, segment_key),
            'downstream': self.get_downstream(chain_name, segment_key),
        }

    def find_path(self, chain_name: str, from_seg: str, to_seg: str) -> Optional[List[Dict]]:
        """
        BFS 查找从 from_seg 到 to_seg 的传导路径
        返回路径上的节点和边信息
        """
        chain = self.chains.get(chain_name)
        if not chain:
            return None

        # 构建邻接表
        adj = {}
        edge_map = {}
        for edge in chain['edges']:
            if edge['from'] not in adj:
                adj[edge['from']] = []
            adj[edge['from']].append(edge['to'])
            edge_map[(edge['from'], edge['to'])] = edge

        # BFS
        queue = deque([(from_seg, [from_seg])])
        visited = {from_seg}

        while queue:
            current, path = queue.popleft()
            if current == to_seg:
                # 构建完整路径信息
                result = []
                for i, seg in enumerate(path):
                    seg_data = chain['segments'].get(seg, {})
                    entry = {
                        'segment_key': seg,
                        'segment_name': seg_data.get('name', seg),
                        'position': seg_data.get('position', 'unknown'),
                    }
                    if i > 0:
                        prev = path[i - 1]
                        edge = edge_map.get((prev, seg))
                        if edge:
                            entry['from_edge'] = edge
                    result.append(entry)
                return result

            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def get_related_chains(self, segment_key: str) -> List[Dict]:
        """查找某环节在哪些产业链中出现（跨链关联）"""
        related = []
        for chain_name, chain_data in self.chains.items():
            if segment_key in chain_data['segments']:
                related.append({
                    'chain': chain_name,
                    'segment_key': segment_key,
                    'segment_name': chain_data['segments'][segment_key]['name'],
                })
        return related

    def find_cross_chain_links(self, chain1: str, chain2: str) -> List[Dict]:
        """查找两条产业链之间的关联（共享行业/环节）"""
        links = []
        c1 = self.chains.get(chain1)
        c2 = self.chains.get(chain2)
        if not c1 or not c2:
            return links

        for seg1_key, seg1 in c1['segments'].items():
            for sw1 in seg1.get('shenwan_industries', []):
                for seg2_key, seg2 in c2['segments'].items():
                    for sw2 in seg2.get('shenwan_industries', []):
                        if sw1 == sw2:
                            links.append({
                                'shared_industry': sw1,
                                'chain1_segment': seg1_key,
                                'chain1_name': seg1['name'],
                                'chain2_segment': seg2_key,
                                'chain2_name': seg2['name'],
                            })
        return links

    def query_by_shenwan(self, industry_name: str) -> List[Dict]:
        """根据申万行业名称查询涉及的产业链和环节"""
        return self.shenwan_index.get(industry_name, [])

    # ============================================================
    # ASCII 可视化
    # ============================================================

    def format_chain_ascii(self, chain_name: str, highlight_segments: List[str] = None) -> str:
        """
        ASCII 可视化产业链
        highlight_segments: 高亮显示的环节（用于基金定位）
        """
        chain = self.chains.get(chain_name)
        if not chain:
            return f"未找到产业链: {chain_name}"

        highlight = set(highlight_segments or [])
        lines = []
        lines.append(f"{'=' * 60}")
        lines.append(f"  产业链图谱: {chain['name']}")
        lines.append(f"  {chain['description']}")
        lines.append(f"  关键驱动: {', '.join(chain['key_drivers'])}")
        lines.append(f"{'=' * 60}")

        # 按 position 分层
        layers = {'upstream': [], 'midstream': [], 'downstream': []}
        for seg_key, seg_data in chain['segments'].items():
            pos = seg_data.get('position', 'midstream')
            marker = '★' if seg_key in highlight else '  '
            layers[pos].append((seg_key, seg_data, marker))

        # 绘制分层
        pos_names = {'upstream': '上游', 'midstream': '中游', 'downstream': '下游'}
        for pos in ['upstream', 'midstream', 'downstream']:
            segs = layers[pos]
            if not segs:
                continue
            lines.append(f"\n  ┌─ {pos_names[pos]} ─────────────────────────────┐")
            for seg_key, seg_data, marker in segs:
                factors = ', '.join(seg_data.get('key_factors', [])[:2])
                reps = ', '.join(seg_data.get('representative', [])[:2])
                lines.append(f"  │ {marker}[{seg_key}] {seg_data['name']}")
                lines.append(f"  │     代表: {reps}")
                lines.append(f"  │     驱动: {factors}")
            lines.append(f"  └──────────────────────────────────────────┘")

        # 绘制传导关系
        lines.append(f"\n  传导关系:")
        lines.append(f"  {'─' * 50}")
        for edge in chain['edges']:
            from_name = chain['segments'].get(edge['from'], {}).get('name', edge['from'])
            to_name = chain['segments'].get(edge['to'], {}).get('name', edge['to'])
            strength = edge.get('strength', 0.5)
            delay = edge.get('delay_months', 1)
            strength_bar = '█' * int(strength * 5) + '░' * (5 - int(strength * 5))
            lines.append(
                f"  {from_name} ──→ {to_name}  "
                f"[{strength_bar}] 强度{strength:.1f} 延迟{delay}月"
            )

        lines.append(f"{'=' * 60}")
        return '\n'.join(lines)

    def format_all_chains_summary(self) -> str:
        """输出所有产业链概览"""
        lines = []
        lines.append(f"{'=' * 60}")
        lines.append(f"  产业链图谱总览")
        lines.append(f"{'=' * 60}")
        lines.append(f"  {'产业链':<8} {'环节数':<6} {'连接数':<6} {'覆盖行业'}")
        lines.append(f"  {'─' * 55}")

        for name, chain in self.chains.items():
            seg_count = len(chain['segments'])
            edge_count = len(chain['edges'])
            industries = set()
            for seg in chain['segments'].values():
                industries.update(seg.get('shenwan_industries', []))
            ind_str = ', '.join(sorted(industries))
            lines.append(f"  {name:<8} {seg_count:<6} {edge_count:<6} {ind_str}")

        lines.append(f"{'=' * 60}")
        return '\n'.join(lines)

    def format_transmission_path(self, chain_name: str, from_seg: str, to_seg: str) -> str:
        """格式化传导路径"""
        path = self.find_path(chain_name, from_seg, to_seg)
        if not path:
            return f"未找到从 {from_seg} 到 {to_seg} 的传导路径"

        lines = []
        lines.append(f"传导路径: {chain_name}")
        lines.append(f"{'─' * 40}")

        for i, node in enumerate(path):
            prefix = '  ' if i == 0 else '  ↓ '
            edge_info = ''
            if 'from_edge' in node:
                e = node['from_edge']
                edge_info = f"  ← [{e['type']}] 强度{e.get('strength', 0.5):.1f} 延迟{e.get('delay_months', 1)}月"
            lines.append(f"{prefix}[{node['segment_key']}] {node['segment_name']}{edge_info}")

        return '\n'.join(lines)


# ============================================================
# CLI 入口
# ============================================================
if __name__ == '__main__':
    import sys

    cmap = IndustryChainMap()

    if len(sys.argv) < 2:
        print(cmap.format_all_chains_summary())
        print()
        for chain_name in cmap.list_chains():
            print(cmap.format_chain_ascii(chain_name))
            print()
    else:
        chain_name = sys.argv[1]
        if chain_name == '--all':
            print(cmap.format_all_chains_summary())
        else:
            print(cmap.format_chain_ascii(chain_name))
            if len(sys.argv) >= 4:
                # 显示传导路径
                print()
                print(cmap.format_transmission_path(chain_name, sys.argv[2], sys.argv[3]))
