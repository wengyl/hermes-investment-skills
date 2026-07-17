"""
产业链关系数据 (Industry Chain Relationship Data)

定义 9 条主要产业链的拓扑结构：
- 节点（产业环节）：名称、申万行业映射、代表公司、关键驱动因素
- 边（供应关系）：上游→下游、传导类型、传导强度、传导延迟

数据来源：公开研报、申万行业分类、产业经济学基本原理
更新日期：2026-06-18
"""

# ============================================================
# 传导类型定义
# ============================================================
TRANSMISSION_TYPES = {
    'cost_push': {
        'name': '成本推动',
        'description': '上游成本变动传导至下游',
        'upstream_up': 'downstream_negative',   # 上游涨 → 下游利空（成本上升）
        'upstream_down': 'downstream_positive',  # 上游跌 → 下游利好（成本下降）
    },
    'demand_pull': {
        'name': '需求拉动',
        'description': '下游需求变动传导至上游',
        'downstream_up': 'upstream_positive',    # 下游需求增 → 上游利好
        'downstream_down': 'upstream_negative',  # 下游需求降 → 上游利空
    },
    'capacity_link': {
        'name': '产能联动',
        'description': '产能扩张/收缩的连锁反应',
        'upstream_expand': 'downstream_positive',
        'upstream_shrink': 'downstream_negative',
    },
    'tech_substitute': {
        'name': '技术替代',
        'description': '新技术对旧技术的替代效应',
        'new_tech': 'old_tech_negative',
    },
    'policy_transmit': {
        'name': '政策传导',
        'description': '产业政策的链式影响',
        'upstream_policy_positive': 'downstream_positive',
        'upstream_policy_negative': 'downstream_negative',
    },
}

# ============================================================
# 产业链节点定义
# ============================================================

# 半导体产业链
SEMICONDUCTOR_CHAIN = {
    'name': '半导体',
    'description': '半导体全产业链：设计→制造→封测，设备/材料支撑',
    'key_drivers': ['国产替代', 'AI芯片需求', '消费电子周期', '政策扶持'],
    'segments': {
        'IC设计': {
            'name': '芯片设计',
            'shenwan_industries': ['半导体'],
            'representative': ['海思', '紫光展锐', '寒武纪', '兆易创新'],
            'key_factors': ['设计工具(EDA)', 'IP授权', '人才'],
            'position': 'midstream',
        },
        '晶圆制造': {
            'name': '晶圆制造',
            'shenwan_industries': ['半导体'],
            'representative': ['中芯国际', '华虹半导体', '长江存储'],
            'key_factors': ['制程工艺', '产能利用率', '资本开支'],
            'position': 'midstream',
        },
        '封装测试': {
            'name': '封装测试',
            'shenwan_industries': ['半导体'],
            'representative': ['长电科技', '通富微电', '华天科技'],
            'key_factors': ['先进封装技术', '产能', '客户结构'],
            'position': 'midstream',
        },
        '半导体设备': {
            'name': '半导体设备',
            'shenwan_industries': ['机械设备'],
            'representative': ['北方华创', '中微公司', '拓荆科技'],
            'key_factors': ['国产替代进度', '晶圆厂资本开支', '技术突破'],
            'position': 'upstream',
        },
        '半导体材料': {
            'name': '半导体材料',
            'shenwan_industries': ['化工', '有色金属'],
            'representative': ['沪硅产业', '雅克科技', '安集科技'],
            'key_factors': ['硅片价格', '光刻胶国产化', '特种气体'],
            'position': 'upstream',
        },
        'EDA/IP': {
            'name': 'EDA工具与IP',
            'shenwan_industries': ['计算机'],
            'representative': ['华大九天', '概伦电子', '芯原股份'],
            'key_factors': ['EDA国产化', 'IP授权模式', 'AI辅助设计'],
            'position': 'upstream',
        },
    },
    'edges': [
        {'from': 'EDA/IP', 'to': 'IC设计', 'type': 'cost_push', 'strength': 0.7, 'delay_months': 1},
        {'from': '半导体材料', 'to': '晶圆制造', 'type': 'cost_push', 'strength': 0.8, 'delay_months': 1},
        {'from': '半导体设备', 'to': '晶圆制造', 'type': 'capacity_link', 'strength': 0.9, 'delay_months': 6},
        {'from': 'IC设计', 'to': '晶圆制造', 'type': 'demand_pull', 'strength': 0.8, 'delay_months': 2},
        {'from': '晶圆制造', 'to': '封装测试', 'type': 'demand_pull', 'strength': 0.9, 'delay_months': 1},
        {'from': '半导体材料', 'to': '封装测试', 'type': 'cost_push', 'strength': 0.5, 'delay_months': 1},
    ],
}

# AI算力产业链
AI_CHAIN = {
    'name': 'AI算力',
    'description': 'AI全产业链：芯片→算力基建→模型→应用→数据',
    'key_drivers': ['大模型迭代', '算力需求', 'AI应用落地', '数据要素'],
    'segments': {
        'AI芯片': {
            'name': 'AI芯片',
            'shenwan_industries': ['半导体', '电子'],
            'representative': ['英伟达', '寒武纪', '海光信息', '景嘉微'],
            'key_factors': ['GPU供给', '国产替代', '制程工艺'],
            'position': 'upstream',
        },
        '算力基建': {
            'name': '算力基础设施',
            'shenwan_industries': ['通信', '计算机'],
            'representative': ['中兴通讯', '紫光股份', '浪潮信息', '中科曙光'],
            'key_factors': ['数据中心建设', '服务器出货', '液冷技术'],
            'position': 'midstream',
        },
        '大模型': {
            'name': '大模型与算法',
            'shenwan_industries': ['计算机'],
            'representative': ['百度', '阿里', '科大讯飞', '商汤'],
            'key_factors': ['模型能力', '训练成本', '开源生态'],
            'position': 'midstream',
        },
        'AI应用': {
            'name': 'AI应用',
            'shenwan_industries': ['计算机', '传媒'],
            'representative': ['金山办公', '同花顺', '万兴科技'],
            'key_factors': ['用户规模', '商业化变现', '场景落地'],
            'position': 'downstream',
        },
        '数据要素': {
            'name': '数据要素',
            'shenwan_industries': ['计算机'],
            'representative': ['易华录', '深桑达', '人民网'],
            'key_factors': ['数据确权', '数据交易', '数据安全'],
            'position': 'upstream',
        },
    },
    'edges': [
        {'from': 'AI芯片', 'to': '算力基建', 'type': 'cost_push', 'strength': 0.9, 'delay_months': 1},
        {'from': '算力基建', 'to': '大模型', 'type': 'capacity_link', 'strength': 0.8, 'delay_months': 3},
        {'from': '大模型', 'to': 'AI应用', 'type': 'tech_substitute', 'strength': 0.7, 'delay_months': 2},
        {'from': '数据要素', 'to': '大模型', 'type': 'cost_push', 'strength': 0.6, 'delay_months': 2},
        {'from': '数据要素', 'to': 'AI应用', 'type': 'demand_pull', 'strength': 0.5, 'delay_months': 3},
    ],
}

# 通信产业链
TELECOM_CHAIN = {
    'name': '通信',
    'description': '通信产业链：设备→光纤→运营商→终端→应用',
    'key_drivers': ['5G建设', '算力网络', '卫星通信', '物联网'],
    'segments': {
        '通信设备': {
            'name': '通信设备',
            'shenwan_industries': ['通信'],
            'representative': ['中兴通讯', '华为', '烽火通信'],
            'key_factors': ['5G基站建设', '海外市场份额', '技术标准'],
            'position': 'upstream',
        },
        '光通信': {
            'name': '光通信/光纤光缆',
            'shenwan_industries': ['通信'],
            'representative': ['中天科技', '亨通光电', '长飞光纤'],
            'key_factors': ['光纤需求', '光模块价格', '数据中心互联'],
            'position': 'upstream',
        },
        '运营商': {
            'name': '电信运营商',
            'shenwan_industries': ['通信'],
            'representative': ['中国移动', '中国电信', '中国联通'],
            'key_factors': ['ARPU值', '资本开支', '政企业务'],
            'position': 'midstream',
        },
        '通信终端': {
            'name': '通信终端',
            'shenwan_industries': ['电子', '通信'],
            'representative': ['小米', '传音控股', '移远通信'],
            'key_factors': ['出货量', '5G渗透率', '物联网模组'],
            'position': 'downstream',
        },
        '通信应用': {
            'name': '通信应用/增值服务',
            'shenwan_industries': ['传媒', '计算机'],
            'representative': ['梦网科技', '二六三', '会畅通讯'],
            'key_factors': ['用户规模', 'ARPU', '企业数字化'],
            'position': 'downstream',
        },
    },
    'edges': [
        {'from': '通信设备', 'to': '运营商', 'type': 'demand_pull', 'strength': 0.8, 'delay_months': 3},
        {'from': '光通信', 'to': '运营商', 'type': 'cost_push', 'strength': 0.6, 'delay_months': 2},
        {'from': '光通信', 'to': '通信设备', 'type': 'cost_push', 'strength': 0.5, 'delay_months': 1},
        {'from': '运营商', 'to': '通信终端', 'type': 'policy_transmit', 'strength': 0.7, 'delay_months': 2},
        {'from': '运营商', 'to': '通信应用', 'type': 'capacity_link', 'strength': 0.6, 'delay_months': 3},
        {'from': '通信终端', 'to': '通信应用', 'type': 'demand_pull', 'strength': 0.5, 'delay_months': 1},
    ],
}

# 新能源车产业链
EV_CHAIN = {
    'name': '新能源车',
    'description': '新能源车产业链：锂矿→电池→电机→整车→充电桩→回收',
    'key_drivers': ['渗透率提升', '电池技术', '政策补贴', '出海'],
    'segments': {
        '锂矿': {
            'name': '锂矿/上游资源',
            'shenwan_industries': ['有色金属'],
            'representative': ['天齐锂业', '赣锋锂业', '盐湖股份'],
            'key_factors': ['锂价', '矿端供给', '库存周期'],
            'position': 'upstream',
        },
        '电池材料': {
            'name': '电池材料',
            'shenwan_industries': ['化工', '有色金属'],
            'representative': ['恩捷股份', '璞泰来', '天赐材料'],
            'key_factors': ['正极/负极/电解液/隔膜价格', '技术路线'],
            'position': 'upstream',
        },
        '动力电池': {
            'name': '动力电池',
            'shenwan_industries': ['电力设备'],
            'representative': ['宁德时代', '比亚迪', '亿纬锂能'],
            'key_factors': ['产能利用率', '技术路线(固态/钠离子)', '出海'],
            'position': 'midstream',
        },
        '整车': {
            'name': '新能源整车',
            'shenwan_industries': ['汽车'],
            'representative': ['比亚迪', '蔚来', '理想', '小鹏'],
            'key_factors': ['销量', '毛利率', '智能化水平'],
            'position': 'downstream',
        },
        '充电桩': {
            'name': '充电桩/基础设施',
            'shenwan_industries': ['电力设备'],
            'representative': ['特锐德', '盛弘股份', '绿能慧充'],
            'key_factors': ['充电桩保有量', '政策推动', '利用率'],
            'position': 'downstream',
        },
        '电池回收': {
            'name': '电池回收',
            'shenwan_industries': ['环保', '有色金属'],
            'representative': ['格林美', '光华科技', '天奇股份'],
            'key_factors': ['回收政策', '金属价格', '技术成熟度'],
            'position': 'downstream',
        },
    },
    'edges': [
        {'from': '锂矿', 'to': '电池材料', 'type': 'cost_push', 'strength': 0.9, 'delay_months': 1},
        {'from': '电池材料', 'to': '动力电池', 'type': 'cost_push', 'strength': 0.8, 'delay_months': 1},
        {'from': '动力电池', 'to': '整车', 'type': 'cost_push', 'strength': 0.7, 'delay_months': 2},
        {'from': '整车', 'to': '充电桩', 'type': 'demand_pull', 'strength': 0.6, 'delay_months': 3},
        {'from': '动力电池', 'to': '电池回收', 'type': 'demand_pull', 'strength': 0.5, 'delay_months': 12},
        {'from': '电池回收', 'to': '电池材料', 'type': 'cost_push', 'strength': 0.3, 'delay_months': 6},
    ],
}

# 光伏产业链
SOLAR_CHAIN = {
    'name': '光伏',
    'description': '光伏产业链：硅料→硅片→电池片→组件→电站',
    'key_drivers': ['装机量', '硅料价格', '技术路线(TOPCon/HJT)', '海外需求'],
    'segments': {
        '硅料': {
            'name': '多晶硅料',
            'shenwan_industries': ['电力设备'],
            'representative': ['通威股份', '大全能源', '协鑫科技'],
            'key_factors': ['硅料价格', '产能投放', '颗粒硅技术'],
            'position': 'upstream',
        },
        '硅片': {
            'name': '硅片',
            'shenwan_industries': ['电力设备'],
            'representative': ['隆基绿能', 'TCL中环', '双良节能'],
            'key_factors': ['硅片尺寸(210/182)', 'N型渗透', '产能过剩'],
            'position': 'upstream',
        },
        '电池片': {
            'name': '电池片',
            'shenwan_industries': ['电力设备'],
            'representative': ['通威股份', '爱旭股份', '钧达股份'],
            'key_factors': ['转换效率', '技术路线(TOPCon/HJT/BC)', '产能'],
            'position': 'midstream',
        },
        '组件': {
            'name': '光伏组件',
            'shenwan_industries': ['电力设备'],
            'representative': ['隆基绿能', '晶科能源', '天合光能', '晶澳科技'],
            'key_factors': ['组件价格', '品牌渠道', '海外市场份额'],
            'position': 'midstream',
        },
        '电站': {
            'name': '光伏电站',
            'shenwan_industries': ['公用事业', '电力设备'],
            'representative': ['三峡能源', '太阳能', '林洋能源'],
            'key_factors': ['装机量', 'IRR', '电价政策'],
            'position': 'downstream',
        },
    },
    'edges': [
        {'from': '硅料', 'to': '硅片', 'type': 'cost_push', 'strength': 0.9, 'delay_months': 1},
        {'from': '硅片', 'to': '电池片', 'type': 'cost_push', 'strength': 0.8, 'delay_months': 1},
        {'from': '电池片', 'to': '组件', 'type': 'cost_push', 'strength': 0.7, 'delay_months': 1},
        {'from': '组件', 'to': '电站', 'type': 'cost_push', 'strength': 0.6, 'delay_months': 2},
        {'from': '电站', 'to': '组件', 'type': 'demand_pull', 'strength': 0.7, 'delay_months': 2},
    ],
}

# 医药产业链
PHARMA_CHAIN = {
    'name': '医药',
    'description': '医药产业链：创新药→CXO→器械→中药→医疗服务',
    'key_drivers': ['集采政策', '创新药出海', '老龄化', '医保谈判'],
    'segments': {
        '创新药': {
            'name': '创新药/生物药',
            'shenwan_industries': ['医药生物'],
            'representative': ['恒瑞医药', '百济神州', '信达生物'],
            'key_factors': ['管线进展', '出海License-out', '集采影响'],
            'position': 'midstream',
        },
        'CXO': {
            'name': '医药外包(CXO)',
            'shenwan_industries': ['医药生物'],
            'representative': ['药明康德', '康龙化成', '凯莱英'],
            'key_factors': ['订单增速', '海外需求', '产能利用率'],
            'position': 'upstream',
        },
        '医疗器械': {
            'name': '医疗器械',
            'shenwan_industries': ['医药生物'],
            'representative': ['迈瑞医疗', '联影医疗', '微创医疗'],
            'key_factors': ['国产替代', '集采影响', '出海'],
            'position': 'midstream',
        },
        '中药': {
            'name': '中药',
            'shenwan_industries': ['医药生物'],
            'representative': ['片仔癀', '云南白药', '同仁堂'],
            'key_factors': ['中药材价格', '国企改革', '消费属性'],
            'position': 'midstream',
        },
        '医疗服务': {
            'name': '医疗服务',
            'shenwan_industries': ['医药生物'],
            'representative': ['爱尔眼科', '通策医疗', '美年健康'],
            'key_factors': ['门诊量', '客单价', '扩张节奏'],
            'position': 'downstream',
        },
    },
    'edges': [
        {'from': 'CXO', 'to': '创新药', 'type': 'cost_push', 'strength': 0.7, 'delay_months': 3},
        {'from': '创新药', 'to': '医疗服务', 'type': 'demand_pull', 'strength': 0.5, 'delay_months': 6},
        {'from': '医疗器械', 'to': '医疗服务', 'type': 'cost_push', 'strength': 0.6, 'delay_months': 2},
        {'from': '中药', 'to': '医疗服务', 'type': 'cost_push', 'strength': 0.4, 'delay_months': 2},
    ],
}

# 消费产业链
CONSUMER_CHAIN = {
    'name': '消费',
    'description': '消费产业链：原材料→品牌→渠道→零售→电商',
    'key_drivers': ['消费复苏', '品牌升级', '渠道变革', '出海'],
    'segments': {
        '消费原材料': {
            'name': '消费原材料',
            'shenwan_industries': ['农林牧渔', '化工', '有色金属'],
            'representative': ['金龙鱼', '海天味业(上游)', '牧原股份(上游)'],
            'key_factors': ['大宗商品价格', '农产品价格', '包材价格'],
            'position': 'upstream',
        },
        '消费品牌': {
            'name': '消费品牌',
            'shenwan_industries': ['食品饮料', '纺织服饰', '家用电器'],
            'representative': ['贵州茅台', '伊利股份', '安踏体育'],
            'key_factors': ['品牌溢价', '产品创新', '市场份额'],
            'position': 'midstream',
        },
        '渠道': {
            'name': '渠道/经销',
            'shenwan_industries': ['商贸零售'],
            'representative': ['永辉超市', '红旗连锁', '孩子王'],
            'key_factors': ['渠道效率', '库存周转', '下沉市场'],
            'position': 'midstream',
        },
        '零售终端': {
            'name': '零售终端',
            'shenwan_industries': ['商贸零售'],
            'representative': ['苏宁易购', '国美零售', '名创优品'],
            'key_factors': ['坪效', '客流量', '线上线下融合'],
            'position': 'downstream',
        },
        '电商平台': {
            'name': '电商平台',
            'shenwan_industries': ['传媒', '商贸零售'],
            'representative': ['阿里巴巴', '京东', '拼多多', '抖音电商'],
            'key_factors': ['GMV增速', '用户规模', '变现率'],
            'position': 'downstream',
        },
    },
    'edges': [
        {'from': '消费原材料', 'to': '消费品牌', 'type': 'cost_push', 'strength': 0.7, 'delay_months': 1},
        {'from': '消费品牌', 'to': '渠道', 'type': 'demand_pull', 'strength': 0.6, 'delay_months': 1},
        {'from': '消费品牌', 'to': '电商平台', 'type': 'demand_pull', 'strength': 0.7, 'delay_months': 1},
        {'from': '渠道', 'to': '零售终端', 'type': 'cost_push', 'strength': 0.5, 'delay_months': 1},
        {'from': '电商平台', 'to': '零售终端', 'type': 'tech_substitute', 'strength': 0.8, 'delay_months': 3},
    ],
}

# 金融产业链
FINANCE_CHAIN = {
    'name': '金融',
    'description': '金融产业链：银行→券商→保险→金融科技',
    'key_drivers': ['利率政策', '资本市场改革', '经济周期', '金融科技'],
    'segments': {
        '银行': {
            'name': '银行业',
            'shenwan_industries': ['银行'],
            'representative': ['工商银行', '招商银行', '宁波银行'],
            'key_factors': ['净息差', '资产质量', '信贷投放'],
            'position': 'upstream',
        },
        '券商': {
            'name': '证券业',
            'shenwan_industries': ['非银金融'],
            'representative': ['中信证券', '华泰证券', '东方财富'],
            'key_factors': ['市场成交量', 'IPO节奏', '资管规模'],
            'position': 'midstream',
        },
        '保险': {
            'name': '保险业',
            'shenwan_industries': ['非银金融'],
            'representative': ['中国平安', '中国人寿', '新华保险'],
            'key_factors': ['保费增速', '投资收益率', '利率环境'],
            'position': 'midstream',
        },
        '金融科技': {
            'name': '金融科技',
            'shenwan_industries': ['计算机', '非银金融'],
            'representative': ['恒生电子', '同花顺', '指南针'],
            'key_factors': ['监管政策', '技术创新', '客户粘性'],
            'position': 'downstream',
        },
    },
    'edges': [
        {'from': '银行', 'to': '券商', 'type': 'policy_transmit', 'strength': 0.6, 'delay_months': 1},
        {'from': '银行', 'to': '保险', 'type': 'cost_push', 'strength': 0.5, 'delay_months': 2},
        {'from': '券商', 'to': '金融科技', 'type': 'demand_pull', 'strength': 0.7, 'delay_months': 2},
        {'from': '保险', 'to': '金融科技', 'type': 'demand_pull', 'strength': 0.5, 'delay_months': 3},
    ],
}

# 农业产业链
AGRICULTURE_CHAIN = {
    'name': '农业',
    'description': '农业产业链：饲料→种植→养殖→屠宰→食品加工',
    'key_drivers': ['猪周期', '粮食安全', '饲料成本', '消费结构'],
    'segments': {
        '饲料': {
            'name': '饲料',
            'shenwan_industries': ['农林牧渔'],
            'representative': ['海大集团', '新希望', '大北农'],
            'key_factors': ['玉米/豆粕价格', '饲料产量', '配方技术'],
            'position': 'upstream',
        },
        '种植': {
            'name': '种植业',
            'shenwan_industries': ['农林牧渔'],
            'representative': ['北大荒', '苏垦农发', '隆平高科'],
            'key_factors': ['粮食价格', '种子技术', '耕地面积'],
            'position': 'upstream',
        },
        '养殖': {
            'name': '养殖业',
            'shenwan_industries': ['农林牧渔'],
            'representative': ['牧原股份', '温氏股份', '圣农发展'],
            'key_factors': ['猪价/鸡价', '产能去化', '养殖成本'],
            'position': 'midstream',
        },
        '屠宰加工': {
            'name': '屠宰/加工',
            'shenwan_industries': ['农林牧渔', '食品饮料'],
            'representative': ['双汇发展', '龙大美食', '华统股份'],
            'key_factors': ['屠宰量', '肉价价差', '产能利用率'],
            'position': 'downstream',
        },
        '食品加工': {
            'name': '食品加工',
            'shenwan_industries': ['食品饮料'],
            'representative': ['伊利股份', '海天味业', '安井食品'],
            'key_factors': ['原材料成本', '产品结构', '渠道拓展'],
            'position': 'downstream',
        },
    },
    'edges': [
        {'from': '饲料', 'to': '养殖', 'type': 'cost_push', 'strength': 0.9, 'delay_months': 1},
        {'from': '种植', 'to': '饲料', 'type': 'cost_push', 'strength': 0.8, 'delay_months': 1},
        {'from': '种植', 'to': '食品加工', 'type': 'cost_push', 'strength': 0.6, 'delay_months': 2},
        {'from': '养殖', 'to': '屠宰加工', 'type': 'cost_push', 'strength': 0.8, 'delay_months': 1},
        {'from': '屠宰加工', 'to': '食品加工', 'type': 'cost_push', 'strength': 0.6, 'delay_months': 1},
        {'from': '食品加工', 'to': '养殖', 'type': 'demand_pull', 'strength': 0.5, 'delay_months': 3},
    ],
}

# GPU芯片产业链（2026 AI时代专用）
GPU_CHAIN = {
    'name': 'GPU芯片',
    'description': 'GPU芯片产业链全景：EDA→GPU设计→晶圆代工→HBM→先进封装→GPU服务器→云计算→AI模型→AI应用',
    'key_drivers': ['AI算力需求', '大模型迭代', 'HBM产能', 'CoWoS瓶颈', '国产替代'],
    'segments': {
        'EDA软件': {
            'name': 'EDA软件',
            'shenwan_industries': ['计算机'],
            'representative': ['Synopsys', 'Cadence', '华大九天'],
            'key_factors': ['三寡头格局', 'AI辅助设计', '国产化率'],
            'position': 'upstream',
        },
        'IP授权': {
            'name': 'IP授权',
            'shenwan_industries': ['计算机'],
            'representative': ['Arm', 'Imagination', '芯原股份'],
            'key_factors': ['CPU/GPU核心IP', '高速接口IP', 'RISC-V'],
            'position': 'upstream',
        },
        '半导体设备': {
            'name': '半导体设备',
            'shenwan_industries': ['机械设备'],
            'representative': ['ASML', 'Applied Materials', '北方华创', '中微公司'],
            'key_factors': ['光刻机', '国产替代进度', '晶圆厂资本开支'],
            'position': 'upstream',
        },
        '半导体材料': {
            'name': '半导体材料',
            'shenwan_industries': ['化工', '有色金属'],
            'representative': ['Shin-Etsu', 'SUMCO', '沪硅产业', '安集科技'],
            'key_factors': ['硅片', '光刻胶', 'CMP材料', '封装基板'],
            'position': 'upstream',
        },
        'GPU设计': {
            'name': 'GPU芯片设计',
            'shenwan_industries': ['半导体', '电子'],
            'representative': ['NVIDIA', 'AMD', 'Intel', '寒武纪', '海光信息'],
            'key_factors': ['架构设计', 'CUDA生态', 'AI推理芯片'],
            'position': 'midstream',
        },
        '晶圆代工': {
            'name': '晶圆代工',
            'shenwan_industries': ['半导体'],
            'representative': ['TSMC', 'Samsung', '中芯国际'],
            'key_factors': ['先进制程(3nm/2nm)', '产能利用率', '资本开支'],
            'position': 'midstream',
        },
        'HBM': {
            'name': 'HBM高带宽存储',
            'shenwan_industries': ['半导体', '电子'],
            'representative': ['SK hynix', 'Samsung', 'Micron', '兆易创新'],
            'key_factors': ['HBM3E/HBM4', '产能瓶颈', '与GPU共同决定AI性能'],
            'position': 'midstream',
        },
        '先进封装': {
            'name': '先进封装(CoWoS)',
            'shenwan_industries': ['半导体'],
            'representative': ['TSMC', 'ASE', 'Amkor', '长电科技', '通富微电'],
            'key_factors': ['CoWoS产能', '2.5D/3D封装', '产能严重受限'],
            'position': 'midstream',
        },
        'GPU卡': {
            'name': 'GPU卡/模组',
            'shenwan_industries': ['电子'],
            'representative': ['NVIDIA', 'AMD', '景嘉微'],
            'key_factors': ['整卡组装', '散热方案', '国产替代'],
            'position': 'midstream',
        },
        'GPU服务器': {
            'name': 'GPU服务器',
            'shenwan_industries': ['计算机'],
            'representative': ['Supermicro', 'Dell', '浪潮信息', '中科曙光'],
            'key_factors': ['AI服务器出货', '液冷技术', '利润率较低'],
            'position': 'downstream',
        },
        '云计算': {
            'name': '云计算厂商',
            'shenwan_industries': ['计算机'],
            'representative': ['AWS', 'Azure', 'Google Cloud', '阿里云'],
            'key_factors': ['算力租赁', 'GPU云服务', '资本开支'],
            'position': 'downstream',
        },
        'AI模型': {
            'name': 'AI模型训练',
            'shenwan_industries': ['计算机'],
            'representative': ['OpenAI', 'Anthropic', 'DeepSeek', '百度', '科大讯飞'],
            'key_factors': ['模型规模', '训练成本', '推理效率'],
            'position': 'downstream',
        },
        'AI应用': {
            'name': 'AI Agent/应用',
            'shenwan_industries': ['计算机', '传媒'],
            'representative': ['微软Copilot', '金山办公', '同花顺'],
            'key_factors': ['用户规模', '商业化变现', 'Agent框架'],
            'position': 'downstream',
        },
    },
    'edges': [
        {'from': 'EDA软件', 'to': 'GPU设计', 'type': 'cost_push', 'strength': 0.8, 'delay_months': 1},
        {'from': 'IP授权', 'to': 'GPU设计', 'type': 'cost_push', 'strength': 0.7, 'delay_months': 1},
        {'from': '半导体设备', 'to': '晶圆代工', 'type': 'capacity_link', 'strength': 0.9, 'delay_months': 6},
        {'from': '半导体材料', 'to': '晶圆代工', 'type': 'cost_push', 'strength': 0.8, 'delay_months': 1},
        {'from': 'GPU设计', 'to': '晶圆代工', 'type': 'demand_pull', 'strength': 0.9, 'delay_months': 2},
        {'from': 'GPU设计', 'to': 'HBM', 'type': 'demand_pull', 'strength': 0.9, 'delay_months': 2},
        {'from': 'GPU设计', 'to': '先进封装', 'type': 'demand_pull', 'strength': 0.85, 'delay_months': 2},
        {'from': 'HBM', 'to': '先进封装', 'type': 'cost_push', 'strength': 0.8, 'delay_months': 1},
        {'from': '晶圆代工', 'to': '先进封装', 'type': 'demand_pull', 'strength': 0.7, 'delay_months': 1},
        {'from': '先进封装', 'to': 'GPU卡', 'type': 'demand_pull', 'strength': 0.9, 'delay_months': 1},
        {'from': 'GPU卡', 'to': 'GPU服务器', 'type': 'cost_push', 'strength': 0.8, 'delay_months': 1},
        {'from': 'GPU服务器', 'to': '云计算', 'type': 'capacity_link', 'strength': 0.7, 'delay_months': 3},
        {'from': '云计算', 'to': 'AI模型', 'type': 'capacity_link', 'strength': 0.8, 'delay_months': 2},
        {'from': 'AI模型', 'to': 'AI应用', 'type': 'tech_substitute', 'strength': 0.7, 'delay_months': 2},
    ],
}

# 产业链颜色（用于气泡图）
CHAIN_COLORS = {
    "GPU芯片": "#00D2FF",
    "半导体": "#FF6B6B",
    "AI算力": "#4ECDC4",
    "通信": "#45B7D1",
    "新能源车": "#96CEB4",
    "光伏": "#FFEAA7",
    "医药": "#DDA0DD",
    "消费": "#FFB347",
    "金融": "#87CEEB",
    "农业": "#98D8C8",
}

# ============================================================
# 汇总：所有产业链
# ============================================================
ALL_CHAINS = {
    'GPU芯片': GPU_CHAIN,
    '半导体': SEMICONDUCTOR_CHAIN,
    'AI算力': AI_CHAIN,
    '通信': TELECOM_CHAIN,
    '新能源车': EV_CHAIN,
    '光伏': SOLAR_CHAIN,
    '医药': PHARMA_CHAIN,
    '消费': CONSUMER_CHAIN,
    '金融': FINANCE_CHAIN,
    '农业': AGRICULTURE_CHAIN,
}

# ============================================================
# 申万行业 → 产业链映射（反向索引）
# ============================================================
SHENWAN_TO_CHAINS = {}
for chain_name, chain_data in ALL_CHAINS.items():
    for seg_key, seg_data in chain_data['segments'].items():
        for sw_industry in seg_data.get('shenwan_industries', []):
            if sw_industry not in SHENWAN_TO_CHAINS:
                SHENWAN_TO_CHAINS[sw_industry] = []
            entry = {
                'chain': chain_name,
                'segment': seg_key,
                'segment_name': seg_data['name'],
                'position': seg_data['position'],
            }
            if entry not in SHENWAN_TO_CHAINS[sw_industry]:
                SHENWAN_TO_CHAINS[sw_industry].append(entry)

# ============================================================
# 基金名称关键词 → 产业链映射
# ============================================================
FUND_CHAIN_KEYWORDS = {
    '通信': [
        {'chain': '通信', 'segments': ['通信设备', '光通信'], 'weight': 0.8},
        {'chain': 'AI算力', 'segments': ['算力基建'], 'weight': 0.2},
    ],
    '半导体': [
        {'chain': '半导体', 'segments': ['IC设计', '晶圆制造', '封装测试'], 'weight': 0.8},
        {'chain': 'AI算力', 'segments': ['AI芯片'], 'weight': 0.2},
    ],
    '芯片': [
        {'chain': '半导体', 'segments': ['IC设计', '晶圆制造'], 'weight': 0.7},
        {'chain': 'AI算力', 'segments': ['AI芯片'], 'weight': 0.3},
    ],
    '科技': [
        {'chain': 'AI算力', 'segments': ['AI芯片', '算力基建', 'AI应用'], 'weight': 0.4},
        {'chain': '半导体', 'segments': ['IC设计', '晶圆制造'], 'weight': 0.3},
        {'chain': '通信', 'segments': ['通信设备'], 'weight': 0.3},
    ],
    '互联网': [
        {'chain': 'AI算力', 'segments': ['AI应用', '大模型'], 'weight': 0.5},
        {'chain': '消费', 'segments': ['电商平台'], 'weight': 0.5},
    ],
    '全球': [
        {'chain': 'AI算力', 'segments': ['AI芯片', 'AI应用'], 'weight': 0.4},
        {'chain': '半导体', 'segments': ['IC设计', '晶圆制造'], 'weight': 0.3},
        {'chain': '消费', 'segments': ['电商平台', '消费品牌'], 'weight': 0.3},
    ],
    '创新': [
        {'chain': '医药', 'segments': ['创新药', 'CXO', '医疗器械'], 'weight': 0.5},
        {'chain': 'AI算力', 'segments': ['AI应用'], 'weight': 0.3},
        {'chain': '新能源车', 'segments': ['动力电池'], 'weight': 0.2},
    ],
    '驱动': [
        {'chain': 'AI算力', 'segments': ['算力基建', 'AI应用'], 'weight': 0.4},
        {'chain': '半导体', 'segments': ['IC设计'], 'weight': 0.3},
        {'chain': '通信', 'segments': ['通信设备'], 'weight': 0.3},
    ],
    '畜牧': [
        {'chain': '农业', 'segments': ['养殖', '饲料', '屠宰加工'], 'weight': 0.8},
        {'chain': '消费', 'segments': ['消费原材料'], 'weight': 0.2},
    ],
    '红利': [
        {'chain': '金融', 'segments': ['银行', '保险'], 'weight': 0.5},
        {'chain': '消费', 'segments': ['消费品牌'], 'weight': 0.3},
        {'chain': '能源', 'segments': [], 'weight': 0.2},
    ],
    '港股': [
        {'chain': '金融', 'segments': ['银行', '券商', '保险'], 'weight': 0.4},
        {'chain': '消费', 'segments': ['消费品牌', '电商平台'], 'weight': 0.3},
        {'chain': 'AI算力', 'segments': ['AI应用'], 'weight': 0.3},
    ],
    '新能源': [
        {'chain': '新能源车', 'segments': ['动力电池', '整车', '锂矿'], 'weight': 0.5},
        {'chain': '光伏', 'segments': ['组件', '电池片', '电站'], 'weight': 0.5},
    ],
    '光伏': [
        {'chain': '光伏', 'segments': ['硅料', '硅片', '电池片', '组件', '电站'], 'weight': 1.0},
    ],
    '医药': [
        {'chain': '医药', 'segments': ['创新药', 'CXO', '医疗器械', '中药'], 'weight': 1.0},
    ],
    '消费': [
        {'chain': '消费', 'segments': ['消费品牌', '渠道', '电商平台'], 'weight': 0.7},
        {'chain': '农业', 'segments': ['食品加工', '屠宰加工'], 'weight': 0.3},
    ],
    '金融': [
        {'chain': '金融', 'segments': ['银行', '券商', '保险', '金融科技'], 'weight': 1.0},
    ],
    '沪深300': [
        {'chain': '金融', 'segments': ['银行', '券商'], 'weight': 0.3},
        {'chain': '消费', 'segments': ['消费品牌'], 'weight': 0.2},
        {'chain': 'AI算力', 'segments': ['AI应用'], 'weight': 0.2},
        {'chain': '新能源车', 'segments': ['动力电池', '整车'], 'weight': 0.15},
        {'chain': '医药', 'segments': ['创新药'], 'weight': 0.15},
    ],
    '行业': [
        {'chain': 'AI算力', 'segments': ['AI应用', '算力基建'], 'weight': 0.3},
        {'chain': '半导体', 'segments': ['IC设计'], 'weight': 0.2},
        {'chain': '消费', 'segments': ['消费品牌'], 'weight': 0.2},
        {'chain': '医药', 'segments': ['创新药'], 'weight': 0.15},
        {'chain': '新能源车', 'segments': ['动力电池'], 'weight': 0.15},
    ],
    '优选': [
        {'chain': 'AI算力', 'segments': ['AI应用'], 'weight': 0.25},
        {'chain': '消费', 'segments': ['消费品牌'], 'weight': 0.25},
        {'chain': '金融', 'segments': ['银行', '券商'], 'weight': 0.25},
        {'chain': '医药', 'segments': ['创新药'], 'weight': 0.25},
    ],
}
