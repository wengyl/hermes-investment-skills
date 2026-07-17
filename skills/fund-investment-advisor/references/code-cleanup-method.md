# 代码清理分析方法

## 如何识别废弃模块

### 步骤1：找出主脚本直接引用的模块
```python
import re
with open("advisor.py") as f:
    content = f.read()
imports = re.findall(r'^(?:from|import)\s+(\w+)', content, re.MULTILINE)
```

### 步骤2：检查每个文件是否被其他文件引用
```python
def is_module_imported(module_name, all_files, scripts_dir):
    base_name = module_name.replace('.py', '')
    for f in all_files:
        with open(os.path.join(scripts_dir, f)) as fh:
            content = fh.read()
        if re.search(rf'(?:from|import)\s+{re.escape(base_name)}\b', content):
            return True
    return False
```

### 步骤3：追溯引用链
- 找到"被引用"但不在主脚本直接引用列表中的模块
- 检查是谁引用了它们
- 如果引用者本身废弃，则该模块也可废弃

## 清理结果模板

```
【在用模块】（被主脚本直接引用）:
  ✅ module1.py
  ✅ module2.py

【检查其他模块是否被间接引用】:
  🔗 被引用: module3.py
  ❌ 未被引用: module4.py

【可能废弃的模块】(N个):
  🗑️  module4.py
  🗑️  module5.py
```

## 安全清理流程

1. 创建 `archive/` 目录
2. 移动废弃脚本（不删除，可恢复）
3. 运行主脚本验证系统正常
4. 记录清理结果到技能文档
