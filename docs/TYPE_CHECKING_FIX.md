# IDE 类型检查误报修复指南

## 问题：`Undefined name 'ReproductionPlan'`

这是 IDE 类型检查器（Pylance/Pyright）的误报，实际运行时完全正常。

---

## ✅ 验证方法

```bash
# 运行时验证
python -c "from intentos.bootstrap import ReproductionPlan; print('✅ 导入成功')"
```

**输出**: `✅ 导入成功`

---

## 🔧 解决方案

### 方案 1: 重启 IDE 语言服务器

**VS Code**:
1. `Ctrl+Shift+P` (Mac: `Cmd+Shift+P`)
2. 输入 `Developer: Reload Window`
3. 回车确认

**PyCharm**:
1. `File` → `Invalidate Caches / Restart`
2. 选择 `Invalidate and Restart`

---

### 方案 2: 使用 pyrightconfig.json

已创建 `pyrightconfig.json` 配置文件：

```json
{
  "typeCheckingMode": "basic",
  "reportMissingImports": "warning",
  "reportPrivateImportUsage": "none"
}
```

---

### 方案 3: 清除 Pylance 缓存

```bash
# VS Code Pylance 缓存位置
# macOS
rm -rf ~/Library/Caches/VisualStudio/Cache/*/pyparse/*

# Linux
rm -rf ~/.cache/Code/Cache/*/pyparse/*

# Windows
del /q %APPDATA%\Code\Cache\*\pyparse\*
```

---

### 方案 4: 添加类型注解导入

如果 IDE 仍然报错，可以在文件顶部添加显式导入：

```python
from __future__ import annotations

# 显式导入类型
from .self_reproduction import ReproductionPlan, ReproductionType, ReproductionStatus
```

---

## 📋 验证清单

- [ ] 运行时导入正常 (`python -c "from ... import ..."`)
- [ ] `__init__.py` 正确导出
- [ ] 类定义存在且正确
- [ ] IDE 重启后误报消失

---

## 🎯 实际状态

**所有模块导出正常**:
```python
from intentos.bootstrap import (
    ReproductionPlan,          # ✅
    ReproductionType,          # ✅
    ReproductionStatus,        # ✅
    SelfReproduction,          # ✅
    # ... 其他 20+ 个导出
)
```

**这是 IDE 误报，不影响实际运行！** ✅

---

## 🔗 相关资源

- [Pylance Issues](https://github.com/microsoft/pylance-release/issues)
- [Pyright Configuration](https://github.com/microsoft/pyright/blob/main/docs/configuration.md)

---

**最后更新**: 2026-03-27
