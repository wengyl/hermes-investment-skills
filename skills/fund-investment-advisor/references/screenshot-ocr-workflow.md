# 从截图 OCR 更新基金持仓工作流

**适用场景**: 用户通过基金 APP 截图提供最新持仓数据，需要更新到基金投资顾问系统

**日期**: 2026-05-22

---

## 工作流程

### 1. OCR 识别截图

使用 `pytesseract` 进行 OCR 识别：

```bash
# 检查 tesseract 是否安装
which tesseract

# 安装 Python 依赖
pip3 install Pillow pytesseract

# 执行 OCR
python3 << 'EOF'
from PIL import Image
import pytesseract

img_path = "/path/to/screenshot.jpg"
img = Image.open(img_path)
text = pytesseract.image_to_string(img, lang='chi_sim+eng')
print(text)
EOF
```

**注意事项**:
- 使用 `chi_sim+eng` 语言包以支持中文 + 英文混合识别
- 截图应包含完整的基金列表（基金名称、市值、盈亏、收益率）
- 如果识别效果差，可尝试调整图片对比度或使用更高精度配置

### 2. 解析 OCR 结果

OCR 输出通常是混乱的多行文本，需要按模式匹配提取数据：

```python
# 典型 OCR 输出格式（列对齐混乱）
"""
招商中证畜牧养殖             3,418.73             -288.76
ETF 联接 A                               -47.60                -7.79%
"""

# 提取模式：
# 第 1 列：基金名称（可能跨行）
# 第 2 列：当前市值
# 第 3 列：持仓盈亏
# 第 4 列：收益率（%）
```

**数据清洗要点**:
- 合并跨行的基金名称
- 去除空白行和乱码行
- 识别数字格式（带千位分隔符、正负号）
- 匹配基金名称与对应的数值列

### 3. 计算成本价

```python
# 公式：成本 = 市值 - 盈亏
current_value = 3418.73
profit_loss = -288.76
cost_value = current_value - profit_loss  # = 3707.49
```

### 4. 查询缺失的基金代码

**问题**: OCR 只能识别基金名称，无法获取 6 位基金代码

**解决方案**:

#### 方案 A: 使用 curl 查询天天基金 API（推荐）

```bash
# 查询单个基金
curl -s "https://fundgz.1234567.com.cn/js/007128.js"
# 输出：jsonpgz({"fundcode":"007128","name":"天弘增强回报债券 A",...});
```

**批量验证代码**:
```bash
for code in 007128 007528 000387; do
  result=$(curl -s -A "Mozilla/5.0" "https://fundgz.1234567.com.cn/js/${code}.js")
  name=$(echo "$result" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
  echo "$code: $name"
done
```

#### 方案 B: 使用 Python urllib（可能遇到网络限制）

```python
import urllib.request
import json

code = "007128"
url = f"https://fundgz.1234567.com.cn/js/{code}.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=5) as response:
    text = response.read().decode('utf-8')
    # 解析 JSONP: jsonpgz({...});
    json_str = text[8:-2]
    data = json.loads(json_str)
    print(f"{code}: {data['name']}")
```

**网络限制提示**:
- Python `urllib`/`requests` 可能遇到 SSL 错误或 502 Bad Gateway
- `curl` 通常更稳定，建议优先使用
- 如遇到 `HTTP Error 502`，尝试切换数据源或使用 curl 替代

#### 方案 C: 用户手动提供

当 API 查询失败时，请用户：
1. 在天天基金网 / 支付宝 / 微信理财通搜索基金名称
2. 提供 6 位基金代码
3. 手动添加到系统

### 5. 更新数据库

使用 `scripts/update_holdings_from_screenshot.py`：

```python
# 脚本逻辑
for code, name, current_value, profit_loss, profit_pct in OCR_HOLDINGS:
    cost_value = current_value - profit_loss
    
    # 检查基金是否存在
    cursor.execute("SELECT fund_code FROM holdings WHERE fund_code = ?", (code,))
    existing = cursor.fetchone()
    
    if existing:
        # 更新成本价（假设份额不变）
        cursor.execute('''
            UPDATE holdings 
            SET avg_cost = ?, total_invested = ?, last_update_date = ?
            WHERE fund_code = ?
        ''', (new_avg_cost, cost_value, today, code))
    else:
        # 插入新基金（需要知道份额，默认为 1000）
        shares = 1000
        avg_cost = cost_value / shares
        cursor.execute('''
            INSERT INTO holdings (...) VALUES (...)
        ''', (...))
```

**注意事项**:
- 更新现有持仓时，保持份额不变，只更新成本价
- 新增持仓时，需要知道份额（可从 OCR 提取或默认为 1000）
- 记录 `last_update_date` 为截图日期

### 6. 验证更新结果

```bash
cd ~/.hermes/fund-advisor
python3 scripts/advisor.py holdings
```

检查输出是否包含：
- ✅ 所有基金都已更新
- ✅ 持仓市值与截图一致
- ✅ 总盈亏计算正确

---

## 常见问题

### Q1: OCR 识别结果混乱，无法匹配列

**原因**: 截图中的列对齐在 OCR 后被打乱

**解决**:
1. 使用按行识别模式，提取所有非空行
2. 按基金名称关键词分组（如"ETF"、"混合"、"指数"）
3. 手动调整数据对应关系

### Q2: 基金代码查询失败

**原因**: 
- 网络限制（502 Bad Gateway）
- API 端点变更
- 基金名称不匹配

**解决**:
1. 优先使用 `curl` 而非 Python `requests`
2. 尝试多个数据源（天天基金、东方财富、新浪）
3. 请用户手动提供代码

### Q3: 成本价计算错误

**原因**: 误将"持仓盈亏"当作"收益率"

**解决**:
- 确认 OCR 识别的列含义：
  - 第 3 列通常是**持仓盈亏（金额）**
  - 第 4 列通常是**收益率（%）**
- 公式：`成本 = 市值 - 持仓盈亏`

### Q4: 份额未知，无法计算成本价

**原因**: 截图未显示持有份额

**解决**:
1. 从 OCR 结果中搜索"份额"关键词
2. 如果找不到，询问用户
3. 临时方案：假设份额为 1000，后续调整

---

## 相关脚本

- `scripts/update_holdings_from_screenshot.py` - 主更新脚本
- `scripts/import_holdings.py` - 批量导入示例
- `scripts/advisor.py` - 查询持仓 (`python3 scripts/advisor.py holdings`)

---

## 示例数据（2026-05-22 用户截图）

```python
OCR_HOLDINGS = [
    ("014414", "招商中证畜牧养殖 ETF 联接 A", 3418.73, -288.76, -7.19),
    ("501205", "鹏华创新未来混合 (LOF)C", 2265.35, 165.35, 11.02),
    ("022184", "富国全球科技互联网股票 (QDII)C", 2881.74, -18.26, -0.73),
    ("005165", "富荣福锦混合 C", 1279.41, 79.41, 6.62),
    ("018388", "华泰柏瑞中证港股通红利 ETF 联接 C", 3896.65, -40.99, -1.03),
    ("020692", "博时中证全指通信设备指数 C", 712.84, 288.13, 67.84),
]

# 待查询基金（需要手动补充代码）
PENDING_FUNDS = [
    ("鹏华创新驱动混合 C", 695.36, -4.64, -0.66),
    ("平安科技精选混合 C", 722.33, 37.28, 5.44),
    ("德邦侈星价值灵活配置混合 C", 4980.96, 1697.57, 51.70),
]
```

---

## 更新日志

**2026-05-22**: 初始版本，基于用户截图更新持仓的实际工作流程
