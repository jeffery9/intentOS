# deprecated/interface

⚠️ **已废弃的启动入口文件**

此目录中的文件已废弃，**请勿再使用**。

## 废弃文件

| 文件 | 原功能 | 替代命令 |
|------|--------|----------|
| `shell.py` | 交互式 Shell | `python -m intentos shell` 或 `intentos shell` |
| `api.py` | REST API 服务器 | `python -m intentos api` 或 `intentos api` |
| `daemon.py` | 守护进程 | `python -m intentos daemon` 或 `intentos daemon` |
| `chat_tui.py` | Chat TUI | `python -m intentos shell` |

## 废弃日期

2026-03-31

## 迁移指南

### 之前使用方式
```bash
# 启动 Shell
PYTHONPATH=. python intentos/interface/shell.py

# 启动 API
PYTHONPATH=. python intentos/interface/api.py

# 启动守护进程
PYTHONPATH=. python intentos/interface/daemon.py
```

### 现在使用方式
```bash
# 安装后使用命令
intentos shell
intentos api
intentos daemon

# 或使用 Python 模块方式
python -m intentos shell
python -m intentos api
python -m intentos daemon
```

## 原因

统一启动入口提供以下优势：
- ✅ 单一入口点，易于维护
- ✅ 一致的命令行接口
- ✅ 支持 `pip install` 后直接使用 `intentos` 命令
- ✅ 更好的模块封装
