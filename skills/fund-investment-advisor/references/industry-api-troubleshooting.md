# 行业资金流向 API 故障排除

**问题**: 行业资金流向数据获取失败，显示"⚠️ 行业资金流向数据获取失败，使用模拟数据演示格式"

**根因**: 东方财富的行业资金流向 API 参数 `fs=bk` 已失效，返回 `rc:102` 错误。

## 问题详情

### 失效的 API 参数
```bash
# 旧参数（已失效）
http://push2.eastmoney.com/api/qt/clist/get?fs=bk&fid=f62&...
# 响应: {"rc": 102, "data": null}
```

### 正确的 API 参数
```bash
# 新参数（使用申万行业分类）
http://push2.eastmoney.com/api/qt/clist/get?fs=m:90+t:2&fid=f62&...
# 响应: 正常的行业资金流向数据
```

## 修复步骤

### 1. 更新 `data_fetcher.py`

在 `get_industry_capital_flow()` 函数中，将：
```python
url = 'http://push2.eastmoney.com/api/qt/clist/get?fid=f62&po=1&pz=50&pn=1&np=1&fltt=2&invt=2&fs=bk&fields=f12,f13,f14,f62,f63'
```

改为：
```python
url = 'http://push2.eastmoney.com/api/qt/clist/get?fid=f62&po=1&pz=50&pn=1&np=1&fltt=2&invt=2&fs=m:90+t:2&fields=f12,f13,f14,f62,f63'
```

### 2. 更新相关文档

在以下文件中搜索并替换：
- `references/industry-data-api.md`
- `references/industry-data.md`
- `SKILL.md` (主技能文件)

搜索: `fs=bk`
替换为: `fs=m:90+t:2`

## API 参数对比

| 参数 | 用途 | 状态 | 返回数量 |
|------|------|------|----------|
| `fs=bk` | 行业板块 | ❌ **已失效** | rc:102 |
| `fs=m:90+t:2` | 申万行业分类 | ✅ **正常** | 31个行业 |
| `fs=m:90+t:1` | 东方财富行业分类 | ✅ **正常** | 地域板块 |
| `fs=m:0+t:6` | 个股数据 | ⚠️ 不适用 | 1637只股票 |

## 测试命令

```bash
# 测试新API参数
curl -s 'http://push2.eastmoney.com/api/qt/clist/get?fid=f62&po=1&pz=5&pn=1&np=1&fltt=2&invt=2&fs=m:90+t:2&fields=f12,f13,f14,f62,f63' | python3 -c "import sys, json; data=json.load(sys.stdin); print('rc:', data.get('rc'), 'total:', data.get('data', {}).get('total', 0) if data.get('data') else 0)"
```

预期输出:
```
rc: 0 total: 496
```

## 诊断步骤

1. **检查API响应**:
```bash
curl -s 'http://push2.eastmoney.com/api/qt/clist/get?fs=bk&fid=f62&fields=f12,f14,f62,f63'
# 应该返回 rc: 102（表示失效）
```

2. **检查新参数**:
```bash
curl -s 'http://push2.eastmoney.com/api/qt/clist/get?fs=m:90+t:2&fid=f62&fields=f12,f14,f62,f63'
# 应该返回 rc: 0 和实际数据
```

3. **验证数据格式**:
```python
import json
data = json.loads(response)
if data.get('rc') == 0 and data.get('data') and data['data'].get('diff'):
    print("✅ API正常")
    print(f"获取到 {len(data['data']['diff'])} 条数据")
else:
    print("❌ API异常")
    print(f"返回码: {data.get('rc')}")
```

## 常见错误码

| 错误码 | 含义 | 解决方案 |
|--------|------|----------|
| `rc: 0` | 成功 | - |
| `rc: 102` | 参数错误或API失效 | 更新 `fs` 参数 |
| `rc: 1001` | 频率限制 | 降低请求频率 |
| `rc: null` | 响应为空 | 检查网络连接 |

## 相关文件

- `scripts/data_fetcher.py`: 主要的数据获取逻辑
- `references/industry-data-api.md`: 完整的API文档
- `references/industry-data.md`: 行业数据模式和fallback策略

## 版本历史

**2026-05-25**: 
- 记录 `fs=bk` 参数失效问题
- 添加 `fs=m:90+t:2` 作为替代参数
- 更新诊断步骤和测试命令