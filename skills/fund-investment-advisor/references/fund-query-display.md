# 基金数据查询与显示最佳实践

## 问题：表格输出被截断

### 症状
在 Feishu/消息平台输出基金持仓表格时，最后一行显示不完整，例如：
```
| 7 | **
```
而不是完整的表格行。

### 原因
- 使用 `"\n".join(output)` 时，某些元素可能包含未闭合的 Markdown 语法
- 列表项拼接时缺少空行分隔
- 表格行生成时字符串拼接不完整

### 解决方案

#### 1. 确保每个表格行完整生成
```python
# ✅ 正确方式
output.append(
    f"| {i} | **{fund['code']}** | {fund['name']} | "
    f"{fund['nav']:.4f} | {change_str} | {fund['type']} |"
)

# ❌ 错误方式（可能导致截断）
output.append(f"| {i} | **")  # 未完成的行
```

#### 2. 使用明确的空行分隔
```python
output = []
output.append("## 标题")
output.append("")  # 显式空行
output.append("### 子标题")
output.append("")  # 显式空行
output.append("| 表格头 |")
```

#### 3. 添加完整性提示
```python
output.append("💡 提示：数据来源于天天基金网，如显示不完整请查看完整输出")
```

## 基金类型识别

### API 返回的基金类型字段
```python
fund_type = result['Data'].get('RZJJDWL', '')
```

### 类型映射规则
```python
def get_fund_type(fund_type_raw):
    if 'QDII' in fund_type_raw:
        return "QDII"
    elif 'ETF' in fund_type_raw or '联接' in fund_type_raw:
        return "ETF"
    elif 'LOF' in fund_type_raw:
        return "LOF"
    elif '指数' in fund_type_raw:
        return "指数"
    elif '混合' in fund_type_raw:
        return "混合"
    elif '股票' in fund_type_raw:
        return "股票"
    elif '债券' in fund_type_raw:
        return "债券"
    else:
        return "其他"
```

## 数据源选择

### 推荐 API 端点

#### 1. 基金净值查询（最可靠）
```
https://fundgz.1234567.com.cn/js/{fund_code}.js
```
- 返回 JSONP 格式，需移除包装
- 字段：fundcode, name, dwjz (净值), gszzl (增长率), jzrq (日期)
- 优点：稳定、快速

#### 2. 基金基本信息
```
https://api.fund.eastmoney.com/f10/jjjb?fundcode={fund_code}
```
- 返回 JSON，GBK 编码
- 字段：FUNDNAME, RZJJDWL (类型), JJLM (经理)
- 注意：可能返回 502 错误

#### 3. 基金搜索（不稳定）
```
https://api.fund.eastmoney.com/FundGalaxy/GetFundSearchResult
```
- 可能返回空结果
- 建议作为备选方案

## 编码处理

### 多编码尝试
```python
for encoding in ['utf-8', 'gbk', 'gb2312']:
    try:
        data = raw_data.decode(encoding)
        return status, data
    except:
        continue
```

### JSONP 解析
```python
data = data.replace('jsonpgz(', '').replace(');', '').strip()
result = json.loads(data)
```

## 表格格式化最佳实践

### Markdown 表格规范
```markdown
| 序号 | 基金代码 | 基金名称 | 净值 | 日涨跌 | 类型 |
|------|---------|---------|------|--------|------|
| 1 | **005165** | 富荣福锦混合 C | 2.3624 | +5.66% ⬆️ | 混合 |
```

### 涨跌标识
- 正数：`+{value}% ⬆️`
- 负数：`{value}%`
- 零：`0.00%`

### 数字格式化
- 净值：`{:.4f}` (4 位小数)
- 增长率：`{:.2f}%` (2 位小数 + 百分号)
- 金额：`{:.2f} 元` (2 位小数)

## 常见问题

### 问题 1：API 返回 502 错误
**解决**：使用备用数据源 `fundgz.1234567.com.cn`

### 问题 2：SSL 证书验证失败
**解决**：使用 `http.client` 绕过 requests 的 SSL 验证
```python
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
```

### 问题 3：表格在消息中被截断
**解决**：
1. 确保每行完整闭合
2. 添加空行分隔
3. 提示用户查看完整输出

## 相关脚本

- `scripts/query_holdings.py` - 持仓查询主脚本
- `scripts/import_holdings.py` - 批量导入持仓
- `scripts/fund_query.py` - 基金查询工具类
