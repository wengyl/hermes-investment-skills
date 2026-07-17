# 报告拆分与中文对齐

## 报告自动拆分

飞书单条消息安全长度约4KB。超长报告自动拆分：

```python
def split_and_print(report: str, max_len: int = 4000):
    """超长报告自动拆分输出"""
    if len(report) <= max_len:
        print(report)
        return
    
    # 按【】section拆分
    lines = report.split('\n')
    part1 = []
    part2 = []
    current = part1
    
    for line in lines:
        current.append(line)
        # 遇到section标题且part1已够长时切换
        if current is part1 and line.startswith('【') and len('\n'.join(part1)) > max_len * 0.4:
            current = part2
    
    print('\n'.join(part1))
    print('\n---SPLIT---\n')
    print('\n'.join(part2))
```

**拆分点选择**：在 `【】` section 边界拆分，第一段占40%+。

**cronjob处理**：agent模式下，agent看到 `---SPLIT---` 分隔符会分两条消息发送。

## 中文字符对齐

中文字符在等宽字体中占2个英文字符宽度。Python的 `str.ljust()` / `str.rjust()` 按字符数计算，不考虑显示宽度。

### 显示宽度计算

```python
def display_width(s: str) -> int:
    """计算字符串显示宽度（中文算2，英文算1）"""
    width = 0
    for ch in s:
        if '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f' or '\uff00' <= ch <= '\uffef':
            width += 2
        else:
            width += 1
    return width
```

### 按显示宽度填充

```python
def pad(s: str, width: int, align='left') -> str:
    """按显示宽度填充字符串"""
    dw = display_width(s)
    padding = max(0, width - dw)
    if align == 'right':
        return ' ' * padding + s
    else:
        return s + ' ' * padding
```

### 使用示例

```python
# 表头
header = pad('代码', 8) + pad('名称', 12) + pad('净值', 10, 'right') + pad('涨跌%', 8, 'right')

# 数据行
row = pad('002112', 8) + pad('德邦鑫星', 12) + pad('6.1293', 10, 'right') + pad('+1.13%', 8, 'right')
```

## 盘中报告格式

盘中报告同时显示净值和估值：

```
代码    名称            净值(日期)    估值(时间)   涨跌%  涨跌额  估算市值
──────────────────────────────────────────────────────────────────────
002112  德邦鑫星价.. 6.1293(05-28) 6.1145(10:31)  -0.24%     -14   5,693
```

- **净值(日期)**：最新收盘净值 + 日期（MM-DD）
- **估值(时间)**：盘中实时估值 + 估值时间（HH:MM）
- **涨跌%**：估值相对净值的涨跌幅
- **涨跌额**：每只基金的涨跌金额（元）
- QDII/LOF基金无盘中估值，显示"—"
