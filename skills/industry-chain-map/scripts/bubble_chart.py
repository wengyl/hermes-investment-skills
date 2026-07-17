"""
产业链气泡图生成器 (Industry Chain Bubble Chart Generator)

生成交互式 HTML 气泡图：
- 横轴: 进入壁垒（围墙）
- 纵轴: 利润率
- 气泡大小: 增长速度
- 颜色: 按产业链分组
- 悬停显示: 上下游位置、代表上市公司

Usage:
    python3 bubble_chart.py                          # 生成全量图
    python3 bubble_chart.py --chains 半导体,AI算力    # 指定产业链
    python3 bubble_chart.py --output ~/chart.html    # 指定输出路径

    # 作为模块调用
    from bubble_chart import generate_bubble_chart
    html = generate_bubble_chart(chains=['半导体', 'AI算力'])
"""

import argparse
import json
import os
import sys

# ============================================================
# 产业链环节评分数据
# ============================================================
# 壁垒(moat): 0-100  利润(profit): 0-100  增长(growth): 1-10
# 上市公司列表 (A股为主，含港股/美股)

SEGMENT_DATA = [
    # ── GPU芯片（2026 AI时代专用） ──
    {"chain":"GPU芯片","name":"EDA软件",   "moat":95,"profit":80,"growth":5, "pos":"上游","stocks":[{"code":"SNPS","name":"Synopsys(美)"},{"code":"CDNS","name":"Cadence(美)"},{"code":"301269","name":"华大九天"}]},
    {"chain":"GPU芯片","name":"IP授权",    "moat":85,"profit":70,"growth":5, "pos":"上游","stocks":[{"code":"ARM","name":"Arm(美)"},{"code":"688521","name":"芯原股份"}]},
    {"chain":"GPU芯片","name":"半导体设备", "moat":92,"profit":65,"growth":7, "pos":"上游","stocks":[{"code":"ASML","name":"ASML(荷)"},{"code":"AMAT","name":"Applied Materials(美)"},{"code":"002371","name":"北方华创"},{"code":"688012","name":"中微公司"}]},
    {"chain":"GPU芯片","name":"半导体材料", "moat":75,"profit":50,"growth":6, "pos":"上游","stocks":[{"code":"688126","name":"沪硅产业"},{"code":"688019","name":"安集科技"}]},
    {"chain":"GPU芯片","name":"GPU设计",   "moat":95,"profit":95,"growth":10,"pos":"中游","stocks":[{"code":"NVDA","name":"NVIDIA(美)"},{"code":"AMD","name":"AMD(美)"},{"code":"688256","name":"寒武纪"},{"code":"688041","name":"海光信息"}]},
    {"chain":"GPU芯片","name":"晶圆代工",  "moat":95,"profit":75,"growth":7, "pos":"中游","stocks":[{"code":"TSM","name":"TSMC(美)"},{"code":"688981","name":"中芯国际"}]},
    {"chain":"GPU芯片","name":"HBM",       "moat":92,"profit":80,"growth":10,"pos":"中游","stocks":[{"code":"MU","name":"Micron(美)"},{"code":"603986","name":"兆易创新"}]},
    {"chain":"GPU芯片","name":"先进封装",  "moat":88,"profit":65,"growth":9, "pos":"中游","stocks":[{"code":"TSM","name":"TSMC(美)"},{"code":"3711","name":"ASE(台)"},{"code":"AMKR","name":"Amkor(美)"},{"code":"600584","name":"长电科技"},{"code":"002156","name":"通富微电"}]},
    {"chain":"GPU芯片","name":"GPU卡",     "moat":70,"profit":55,"growth":8, "pos":"中游","stocks":[{"code":"NVDA","name":"NVIDIA(美)"},{"code":"300474","name":"景嘉微"}]},
    {"chain":"GPU芯片","name":"GPU服务器", "moat":40,"profit":30,"growth":8, "pos":"下游","stocks":[{"code":"SMCI","name":"Supermicro(美)"},{"code":"DELL","name":"Dell(美)"},{"code":"000977","name":"浪潮信息"},{"code":"603019","name":"中科曙光"}]},
    {"chain":"GPU芯片","name":"云计算",    "moat":70,"profit":50,"growth":8, "pos":"下游","stocks":[{"code":"AMZN","name":"AWS(美)"},{"code":"MSFT","name":"Azure(美)"},{"code":"9988","name":"阿里云(港)"}]},
    {"chain":"GPU芯片","name":"AI模型",    "moat":80,"profit":60,"growth":9, "pos":"下游","stocks":[{"code":"9888","name":"百度(港)"},{"code":"002230","name":"科大讯飞"}]},
    {"chain":"GPU芯片","name":"AI应用",    "moat":55,"profit":55,"growth":10,"pos":"下游","stocks":[{"code":"688111","name":"金山办公"},{"code":"300033","name":"同花顺"}]},

    # ── 半导体（泛行业） ──
    {"chain":"半导体","name":"EDA/IP","moat":95,"profit":75,"growth":8,"pos":"上游",
     "stocks":[{"code":"301269","name":"华大九天"},{"code":"688206","name":"概伦电子"},{"code":"688521","name":"芯原股份"}]},
    {"chain":"半导体","name":"半导体设备","moat":90,"profit":70,"growth":9,"pos":"上游",
     "stocks":[{"code":"002371","name":"北方华创"},{"code":"688012","name":"中微公司"},{"code":"688072","name":"拓荆科技"}]},
    {"chain":"半导体","name":"半导体材料","moat":75,"profit":55,"growth":7,"pos":"上游",
     "stocks":[{"code":"688126","name":"沪硅产业"},{"code":"002409","name":"雅克科技"},{"code":"688019","name":"安集科技"}]},
    {"chain":"半导体","name":"芯片设计","moat":70,"profit":65,"growth":8,"pos":"中游",
     "stocks":[{"code":"688256","name":"寒武纪"},{"code":"603986","name":"兆易创新"},{"code":"688041","name":"海光信息"}]},
    {"chain":"半导体","name":"晶圆制造","moat":85,"profit":50,"growth":7,"pos":"中游",
     "stocks":[{"code":"688981","name":"中芯国际"},{"code":"688347","name":"华虹半导体"}]},
    {"chain":"半导体","name":"封装测试","moat":45,"profit":35,"growth":5,"pos":"中游",
     "stocks":[{"code":"600584","name":"长电科技"},{"code":"002156","name":"通富微电"},{"code":"002185","name":"华天科技"}]},

    # ── AI算力 ──
    {"chain":"AI算力","name":"AI芯片","moat":92,"profit":80,"growth":10,"pos":"上游",
     "stocks":[{"code":"688256","name":"寒武纪"},{"code":"688041","name":"海光信息"},{"code":"300474","name":"景嘉微"}]},
    {"chain":"AI算力","name":"数据要素","moat":60,"profit":50,"growth":7,"pos":"上游",
     "stocks":[{"code":"300212","name":"易华录"},{"code":"000032","name":"深桑达A"},{"code":"603000","name":"人民网"}]},
    {"chain":"AI算力","name":"算力基建","moat":55,"profit":40,"growth":9,"pos":"中游",
     "stocks":[{"code":"000977","name":"浪潮信息"},{"code":"603019","name":"中科曙光"},{"code":"000063","name":"中兴通讯"}]},
    {"chain":"AI算力","name":"大模型","moat":80,"profit":60,"growth":9,"pos":"中游",
     "stocks":[{"code":"9888","name":"百度(港)"},{"code":"002230","name":"科大讯飞"},{"code":"0020","name":"商汤(港)"}]},
    {"chain":"AI算力","name":"AI应用","moat":50,"profit":55,"growth":8,"pos":"下游",
     "stocks":[{"code":"688111","name":"金山办公"},{"code":"300033","name":"同花顺"},{"code":"300624","name":"万兴科技"}]},

    # ── 通信 ──
    {"chain":"通信","name":"通信设备","moat":70,"profit":45,"growth":6,"pos":"上游",
     "stocks":[{"code":"000063","name":"中兴通讯"},{"code":"600498","name":"烽火通信"}]},
    {"chain":"通信","name":"光通信","moat":60,"profit":40,"growth":7,"pos":"上游",
     "stocks":[{"code":"600522","name":"中天科技"},{"code":"600487","name":"亨通光电"},{"code":"601869","name":"长飞光纤"}]},
    {"chain":"通信","name":"运营商","moat":80,"profit":55,"growth":4,"pos":"中游",
     "stocks":[{"code":"600941","name":"中国移动"},{"code":"601728","name":"中国电信"},{"code":"600050","name":"中国联通"}]},
    {"chain":"通信","name":"通信终端","moat":35,"profit":25,"growth":5,"pos":"下游",
     "stocks":[{"code":"1810","name":"小米(港)"},{"code":"688036","name":"传音控股"},{"code":"603236","name":"移远通信"}]},
    {"chain":"通信","name":"通信应用","moat":40,"profit":45,"growth":6,"pos":"下游",
     "stocks":[{"code":"002123","name":"梦网科技"},{"code":"002467","name":"二六三"}]},

    # ── 新能源车 ──
    {"chain":"新能源车","name":"锂矿","moat":65,"profit":60,"growth":5,"pos":"上游",
     "stocks":[{"code":"002466","name":"天齐锂业"},{"code":"002460","name":"赣锋锂业"},{"code":"000792","name":"盐湖股份"}]},
    {"chain":"新能源车","name":"电池材料","moat":55,"profit":40,"growth":6,"pos":"上游",
     "stocks":[{"code":"002812","name":"恩捷股份"},{"code":"603659","name":"璞泰来"},{"code":"002709","name":"天赐材料"}]},
    {"chain":"新能源车","name":"动力电池","moat":75,"profit":50,"growth":8,"pos":"中游",
     "stocks":[{"code":"300750","name":"宁德时代"},{"code":"002594","name":"比亚迪"},{"code":"300014","name":"亿纬锂能"}]},
    {"chain":"新能源车","name":"整车","moat":50,"profit":30,"growth":7,"pos":"下游",
     "stocks":[{"code":"002594","name":"比亚迪"},{"code":"9866","name":"蔚来(港)"},{"code":"2015","name":"理想(港)"}]},
    {"chain":"新能源车","name":"充电桩","moat":30,"profit":25,"growth":8,"pos":"下游",
     "stocks":[{"code":"300001","name":"特锐德"},{"code":"300693","name":"盛弘股份"}]},
    {"chain":"新能源车","name":"电池回收","moat":40,"profit":35,"growth":6,"pos":"下游",
     "stocks":[{"code":"002340","name":"格林美"},{"code":"002009","name":"天奇股份"}]},

    # ── 光伏 ──
    {"chain":"光伏","name":"硅料","moat":60,"profit":55,"growth":5,"pos":"上游",
     "stocks":[{"code":"600438","name":"通威股份"},{"code":"688303","name":"大全能源"}]},
    {"chain":"光伏","name":"硅片","moat":50,"profit":35,"growth":4,"pos":"上游",
     "stocks":[{"code":"601012","name":"隆基绿能"},{"code":"002129","name":"TCL中环"}]},
    {"chain":"光伏","name":"电池片","moat":55,"profit":30,"growth":6,"pos":"中游",
     "stocks":[{"code":"600438","name":"通威股份"},{"code":"600732","name":"爱旭股份"}]},
    {"chain":"光伏","name":"组件","moat":45,"profit":25,"growth":5,"pos":"中游",
     "stocks":[{"code":"688223","name":"晶科能源"},{"code":"688599","name":"天合光能"},{"code":"002459","name":"晶澳科技"}]},
    {"chain":"光伏","name":"电站","moat":40,"profit":35,"growth":6,"pos":"下游",
     "stocks":[{"code":"600905","name":"三峡能源"},{"code":"000591","name":"太阳能"}]},

    # ── 医药 ──
    {"chain":"医药","name":"CXO","moat":65,"profit":55,"growth":6,"pos":"上游",
     "stocks":[{"code":"603259","name":"药明康德"},{"code":"300759","name":"康龙化成"},{"code":"002821","name":"凯莱英"}]},
    {"chain":"医药","name":"创新药","moat":85,"profit":70,"growth":7,"pos":"中游",
     "stocks":[{"code":"600276","name":"恒瑞医药"},{"code":"688235","name":"百济神州"},{"code":"002422","name":"科伦药业"}]},
    {"chain":"医药","name":"医疗器械","moat":75,"profit":60,"growth":7,"pos":"中游",
     "stocks":[{"code":"300760","name":"迈瑞医疗"},{"code":"688271","name":"联影医疗"}]},
    {"chain":"医药","name":"中药","moat":55,"profit":50,"growth":4,"pos":"中游",
     "stocks":[{"code":"600436","name":"片仔癀"},{"code":"000538","name":"云南白药"},{"code":"600085","name":"同仁堂"}]},
    {"chain":"医药","name":"医疗服务","moat":60,"profit":45,"growth":6,"pos":"下游",
     "stocks":[{"code":"300015","name":"爱尔眼科"},{"code":"600763","name":"通策医疗"}]},

    # ── 消费 ──
    {"chain":"消费","name":"消费原材料","moat":25,"profit":20,"growth":3,"pos":"上游",
     "stocks":[{"code":"300999","name":"金龙鱼"}]},
    {"chain":"消费","name":"消费品牌","moat":80,"profit":70,"growth":5,"pos":"中游",
     "stocks":[{"code":"600519","name":"贵州茅台"},{"code":"600887","name":"伊利股份"},{"code":"2020","name":"安踏(港)"}]},
    {"chain":"消费","name":"渠道","moat":35,"profit":30,"growth":3,"pos":"中游",
     "stocks":[{"code":"601933","name":"永辉超市"},{"code":"002697","name":"红旗连锁"}]},
    {"chain":"消费","name":"零售终端","moat":20,"profit":15,"growth":2,"pos":"下游",
     "stocks":[{"code":"9896","name":"名创优品(港)"}]},
    {"chain":"消费","name":"电商平台","moat":70,"profit":55,"growth":6,"pos":"下游",
     "stocks":[{"code":"9988","name":"阿里巴巴(港)"},{"code":"9618","name":"京东(港)"},{"code":"PDD","name":"拼多多(美)"}]},

    # ── 金融 ──
    {"chain":"金融","name":"银行","moat":75,"profit":60,"growth":3,"pos":"上游",
     "stocks":[{"code":"600036","name":"招商银行"},{"code":"002142","name":"宁波银行"},{"code":"601398","name":"工商银行"}]},
    {"chain":"金融","name":"券商","moat":55,"profit":45,"growth":5,"pos":"中游",
     "stocks":[{"code":"600030","name":"中信证券"},{"code":"601688","name":"华泰证券"},{"code":"300059","name":"东方财富"}]},
    {"chain":"金融","name":"保险","moat":65,"profit":50,"growth":4,"pos":"中游",
     "stocks":[{"code":"601318","name":"中国平安"},{"code":"601628","name":"中国人寿"}]},
    {"chain":"金融","name":"金融科技","moat":50,"profit":55,"growth":7,"pos":"下游",
     "stocks":[{"code":"600570","name":"恒生电子"},{"code":"300033","name":"同花顺"}]},

    # ── 农业 ──
    {"chain":"农业","name":"种植","moat":35,"profit":25,"growth":3,"pos":"上游",
     "stocks":[{"code":"600598","name":"北大荒"},{"code":"000998","name":"隆平高科"}]},
    {"chain":"农业","name":"饲料","moat":40,"profit":30,"growth":4,"pos":"上游",
     "stocks":[{"code":"002311","name":"海大集团"},{"code":"000876","name":"新希望"}]},
    {"chain":"农业","name":"养殖","moat":45,"profit":35,"growth":5,"pos":"中游",
     "stocks":[{"code":"002714","name":"牧原股份"},{"code":"300498","name":"温氏股份"}]},
    {"chain":"农业","name":"屠宰加工","moat":35,"profit":25,"growth":3,"pos":"下游",
     "stocks":[{"code":"000895","name":"双汇发展"}]},
    {"chain":"农业","name":"食品加工","moat":50,"profit":40,"growth":4,"pos":"下游",
     "stocks":[{"code":"600887","name":"伊利股份"},{"code":"603345","name":"安井食品"}]},
]

# 产业链颜色
CHAIN_COLORS = {
    "GPU芯片": "#00D2FF",
    "半导体": "#FF6B6B",
    "AI算力": "#4ECDC4",
    "通信":   "#45B7D1",
    "新能源车": "#96CEB4",
    "光伏":   "#FFEAA7",
    "医药":   "#DDA0DD",
    "消费":   "#FFB347",
    "金融":   "#87CEEB",
    "农业":   "#98D8C8",
}


def generate_bubble_chart(chains=None, output_path=None, width=1100, height=720):
    """
    生成产业链气泡图 HTML

    Args:
        chains: 要显示的产业链列表，None=全部
        output_path: 输出HTML路径，None=返回字符串
        width: 图表宽度
        height: 图表高度

    Returns:
        HTML 字符串（output_path=None时）或写入文件
    """
    # 过滤数据
    if chains:
        data = [d for d in SEGMENT_DATA if d['chain'] in chains]
    else:
        data = SEGMENT_DATA

    if not data:
        return "<p>未找到匹配的产业链数据</p>"

    html = _build_html(data, width, height)

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return output_path
    return html


def _build_html(data, width, height):
    """构建完整 HTML"""
    # 提取所有产业链
    chains_in_data = list(dict.fromkeys(d['chain'] for d in data))

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>产业链图谱 - 壁垒×利润×增长 气泡图</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #1a1a2e; color: #eee; font-family: -apple-system, "PingFang SC", "Helvetica Neue", sans-serif; padding: 20px; }}
h1 {{ text-align: center; font-size: 22px; margin-bottom: 6px; color: #fff; }}
.subtitle {{ text-align: center; font-size: 13px; color: #888; margin-bottom: 16px; }}
.chart-wrap {{ position: relative; width: {width}px; height: {height}px; margin: 0 auto; background: #16213e; border-radius: 12px; overflow: hidden; }}
svg {{ position: absolute; top: 0; left: 0; }}
.tooltip {{ position: absolute; background: rgba(0,0,0,0.92); color: #fff; padding: 14px 18px; border-radius: 10px; font-size: 13px; pointer-events: none; display: none; z-index: 10; line-height: 1.9; border: 1px solid rgba(255,255,255,0.15); max-width: 320px; backdrop-filter: blur(8px); }}
.tooltip .t-title {{ font-weight: bold; font-size: 15px; margin-bottom: 6px; padding-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.15); }}
.tooltip .t-row {{ display: flex; align-items: center; gap: 8px; }}
.tooltip .t-bar {{ display: inline-block; height: 8px; border-radius: 4px; }}
.tooltip .t-stocks {{ margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.1); }}
.tooltip .t-stock {{ display: inline-block; background: rgba(255,255,255,0.1); padding: 2px 8px; border-radius: 4px; margin: 2px; font-size: 12px; }}
.legend {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 14px; margin-top: 14px; }}
.legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 12px; cursor: pointer; opacity: 0.85; transition: opacity 0.2s; }}
.legend-item:hover {{ opacity: 1; }}
.legend-dot {{ width: 12px; height: 12px; border-radius: 50%; }}
.size-legend {{ text-align: center; margin-top: 10px; font-size: 12px; color: #888; }}
.size-legend span {{ display: inline-block; margin: 0 8px; }}
.size-bubble {{ display: inline-block; border-radius: 50%; background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4); vertical-align: middle; margin-right: 4px; }}
.pos-tag {{ display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 11px; font-weight: 500; }}
.pos-up {{ background: rgba(78,205,196,0.3); color: #4ECDC4; }}
.pos-mid {{ background: rgba(255,218,121,0.3); color: #FFDA79; }}
.pos-down {{ background: rgba(255,107,107,0.3); color: #FF6B6B; }}
</style>
</head>
<body>

<h1>🏭 产业链图谱 · 壁垒 × 利润 × 增长</h1>
<div class="subtitle">横轴: 进入壁垒(围墙) → &nbsp;|&nbsp; 纵轴: 利润率 ↑ &nbsp;|&nbsp; 气泡大小: 增长速度 🔥</div>

<div class="chart-wrap" id="chartWrap">
<svg id="svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <!-- Plot area: left=100, top=40, right=1060, bottom=640 => 960x600 -->
  <line x1="580" y1="40" x2="580" y2="640" stroke="#2a3a5a" stroke-width="1" stroke-dasharray="8,5"/>
  <line x1="100" y1="340" x2="1060" y2="340" stroke="#2a3a5a" stroke-width="1" stroke-dasharray="8,5"/>
  <line x1="100" y1="190" x2="1060" y2="190" stroke="#1e2d4a" stroke-width="0.5"/>
  <line x1="100" y1="490" x2="1060" y2="490" stroke="#1e2d4a" stroke-width="0.5"/>
  <line x1="340" y1="40" x2="340" y2="640" stroke="#1e2d4a" stroke-width="0.5"/>
  <line x1="820" y1="40" x2="820" y2="640" stroke="#1e2d4a" stroke-width="0.5"/>

  <text x="340" y="70" fill="#4a5a7a" font-size="13" text-anchor="middle" font-style="italic">低壁垒 · 高利润</text>
  <text x="340" y="88" fill="#4a5a7a" font-size="11" text-anchor="middle">品牌溢价型 / 轻资产</text>
  <text x="820" y="70" fill="#4a5a7a" font-size="13" text-anchor="middle" font-style="italic">高壁垒 · 高利润</text>
  <text x="820" y="88" fill="#4a5a7a" font-size="11" text-anchor="middle">⭐ 黄金赛道</text>
  <text x="340" y="615" fill="#4a5a7a" font-size="13" text-anchor="middle" font-style="italic">低壁垒 · 低利润</text>
  <text x="340" y="633" fill="#4a5a7a" font-size="11" text-anchor="middle">红海竞争</text>
  <text x="820" y="615" fill="#4a5a7a" font-size="13" text-anchor="middle" font-style="italic">高壁垒 · 低利润</text>
  <text x="820" y="633" fill="#4a5a7a" font-size="11" text-anchor="middle">资本密集型</text>

  <text x="100" y="660" fill="#667" font-size="11" text-anchor="middle">0</text>
  <text x="340" y="660" fill="#667" font-size="11" text-anchor="middle">25</text>
  <text x="580" y="660" fill="#667" font-size="11" text-anchor="middle">50</text>
  <text x="820" y="660" fill="#667" font-size="11" text-anchor="middle">75</text>
  <text x="1060" y="660" fill="#667" font-size="11" text-anchor="middle">100</text>
  <text x="580" y="690" fill="#99a" font-size="14" text-anchor="middle" font-weight="bold">进入壁垒(围墙) →</text>

  <text x="90" y="644" fill="#667" font-size="11" text-anchor="end">0</text>
  <text x="90" y="494" fill="#667" font-size="11" text-anchor="end">25</text>
  <text x="90" y="344" fill="#667" font-size="11" text-anchor="end">50</text>
  <text x="90" y="194" fill="#667" font-size="11" text-anchor="end">75</text>
  <text x="90" y="44" fill="#667" font-size="11" text-anchor="end">100</text>
  <text x="30" y="340" fill="#99a" font-size="14" text-anchor="middle" font-weight="bold" transform="rotate(-90,30,340)">利润率 →</text>

  <rect x="100" y="40" width="960" height="600" fill="none" stroke="#2a3a5a" stroke-width="1"/>
</svg>
<div class="tooltip" id="tooltip"></div>
</div>

<div class="legend" id="legend"></div>
<div class="size-legend">
  气泡大小: <span><span class="size-bubble" style="width:12px;height:12px"></span>增长慢</span>
  <span><span class="size-bubble" style="width:22px;height:22px"></span>增长中</span>
  <span><span class="size-bubble" style="width:36px;height:36px"></span>增长快 🔥</span>
</div>

<script>
const data = {json.dumps(data, ensure_ascii=False)};
const colors = {json.dumps(CHAIN_COLORS, ensure_ascii=False)};
const svg = document.getElementById('svg');
const ns = 'http://www.w3.org/2000/svg';
const PL = 100, PT = 40, PW = 960, PH = 600;

function xScale(moat) {{ return PL + (moat / 100) * PW; }}
function yScale(profit) {{ return PT + ((100 - profit) / 100) * PH; }}
function rScale(growth) {{ return growth * 3.5 + 6; }}

// Collision avoidance: nudge overlapping labels
function nudgePositions(data) {{
  const positioned = [];
  data.forEach(d => {{
    let cx = xScale(d.moat), cy = yScale(d.profit);
    let attempts = 0;
    while (attempts < 20) {{
      let overlap = false;
      for (const p of positioned) {{
        const dx = cx - p.x, dy = cy - p.y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        const minDist = rScale(d.growth) + rScale(p.r) + 2;
        if (dist < minDist) {{
          const angle = Math.atan2(dy, dx) || Math.random() * Math.PI * 2;
          cx += Math.cos(angle) * (minDist - dist + 2);
          cy += Math.sin(angle) * (minDist - dist + 2);
          overlap = true;
          break;
        }}
      }}
      if (!overlap) break;
      attempts++;
    }}
    positioned.push({{x: cx, y: cy, r: d.growth, idx: d._idx}});
    d._cx = cx; d._cy = cy;
  }});
}}

data.forEach((d, i) => d._idx = i);
nudgePositions(data);

data.forEach((d, i) => {{
  const cx = d._cx || xScale(d.moat);
  const cy = d._cy || yScale(d.profit);
  const r = rScale(d.growth);
  const color = colors[d.chain] || '#888';

  const glow = document.createElementNS(ns, 'circle');
  glow.setAttribute('cx', cx); glow.setAttribute('cy', cy);
  glow.setAttribute('r', r + 3);
  glow.setAttribute('fill', color); glow.setAttribute('fill-opacity', '0.15');
  glow.setAttribute('filter', 'url(#glow)');
  svg.appendChild(glow);

  const circle = document.createElementNS(ns, 'circle');
  circle.setAttribute('cx', cx); circle.setAttribute('cy', cy);
  circle.setAttribute('r', r);
  circle.setAttribute('fill', color); circle.setAttribute('fill-opacity', '0.5');
  circle.setAttribute('stroke', color); circle.setAttribute('stroke-width', '1.5');
  circle.setAttribute('data-idx', i);
  circle.classList.add('bubble-el');
  circle.style.cursor = 'pointer';
  circle.style.transition = 'r 0.15s, fill-opacity 0.15s';
  svg.appendChild(circle);

  const text = document.createElementNS(ns, 'text');
  text.setAttribute('x', cx); text.setAttribute('y', cy + 4);
  text.setAttribute('text-anchor', 'middle');
  text.setAttribute('fill', '#fff');
  text.setAttribute('font-size', r > 20 ? '10' : '9');
  text.setAttribute('font-weight', '500');
  text.setAttribute('pointer-events', 'none');
  text.textContent = d.name;
  svg.appendChild(text);
}});

const tooltip = document.getElementById('tooltip');
const wrap = document.getElementById('chartWrap');

svg.addEventListener('mouseover', e => {{
  const el = e.target;
  if (!el.classList.contains('bubble-el')) return;
  const d = data[+el.dataset.idx];
  const r = rScale(d.growth);
  el.setAttribute('fill-opacity', '0.8');
  el.setAttribute('r', r + 4);

  const fire = '🔥'.repeat(Math.min(d.growth, 10));
  const mBar = '█'.repeat(Math.round(d.moat/10)) + '░'.repeat(10 - Math.round(d.moat/10));
  const pBar = '█'.repeat(Math.round(d.profit/10)) + '░'.repeat(10 - Math.round(d.profit/10));
  const posClass = d.pos === '上游' ? 'pos-up' : d.pos === '中游' ? 'pos-mid' : 'pos-down';
  const stocksHtml = d.stocks.map(s => '<span class="t-stock">' + s.code + ' ' + s.name + '</span>').join('');

  tooltip.innerHTML =
    '<div class="t-title" style="color:' + (colors[d.chain]||'#fff') + '">' + d.chain + ' · ' + d.name + '</div>' +
    '<div class="t-row">位置: <span class="pos-tag ' + posClass + '">' + d.pos + '</span></div>' +
    '<div class="t-row">壁垒: ' + mBar + ' ' + d.moat + '</div>' +
    '<div class="t-row">利润: ' + pBar + ' ' + d.profit + '</div>' +
    '<div class="t-row">增长: ' + fire + ' (' + d.growth + '/10)</div>' +
    '<div class="t-stocks">📌 上市公司:<br>' + stocksHtml + '</div>';
  tooltip.style.display = 'block';
}});

svg.addEventListener('mouseout', e => {{
  const el = e.target;
  if (!el.classList.contains('bubble-el')) return;
  const d = data[+el.dataset.idx];
  el.setAttribute('fill-opacity', '0.5');
  el.setAttribute('r', rScale(d.growth));
  tooltip.style.display = 'none';
}});

svg.addEventListener('mousemove', e => {{
  const rect = wrap.getBoundingClientRect();
  let tx = e.clientX - rect.left + 16;
  let ty = e.clientY - rect.top - 10;
  if (tx + 300 > rect.width) tx = e.clientX - rect.left - 310;
  if (ty + 200 > rect.height) ty = rect.height - 210;
  tooltip.style.left = tx + 'px';
  tooltip.style.top = ty + 'px';
}});

const chains = [...new Set(data.map(d => d.chain))];
const legendEl = document.getElementById('legend');
chains.forEach(c => {{
  const color = colors[c] || '#888';
  const item = document.createElement('div');
  item.className = 'legend-item';
  item.innerHTML = '<div class="legend-dot" style="background:' + color + '"></div><span>' + c + '</span>';
  legendEl.appendChild(item);
}});
</script>
</body>
</html>'''


# ============================================================
# CLI
# ============================================================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='产业链气泡图生成器')
    parser.add_argument('--chains', type=str, default=None,
                        help='逗号分隔的产业链名称，如: 半导体,AI算力,通信')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='输出HTML文件路径')
    parser.add_argument('--list', action='store_true',
                        help='列出所有产业链和环节')
    parser.add_argument('--mode', choices=['all', 'per-chain'], default='per-chain',
                        help='all=全部混在一张图, per-chain=按产业链分页(默认)')
    args = parser.parse_args()

    if args.list:
        print("产业链图谱数据:")
        print("=" * 60)
        current_chain = ""
        for d in SEGMENT_DATA:
            if d['chain'] != current_chain:
                current_chain = d['chain']
                print(f"\n【{current_chain}】")
            stocks = ', '.join(f"{s['name']}({s['code']})" for s in d['stocks'])
            print(f"  {d['pos']} {d['name']:<8} 壁垒:{d['moat']:>3} 利润:{d['profit']:>3} 增长:{d['growth']}/10  → {stocks}")
        sys.exit(0)

    chains = args.chains.split(',') if args.chains else None
    output = args.output or os.path.expanduser('~/industry_chain_bubble.html')

    result = generate_bubble_chart(chains=chains, output_path=output)
    print(f"✅ 气泡图已生成: {result}")
    if chains:
        print(f"   包含产业链: {', '.join(chains)}")
    else:
        print(f"   包含全部 {len(CHAIN_COLORS)} 条产业链, {len(SEGMENT_DATA)} 个环节")
