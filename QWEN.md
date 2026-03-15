# IntentOS - AI 原生操作系统

## 项目概述

IntentOS 是一个 **AI 原生操作系统** 原型，核心是**语义虚拟机 (Semantic VM)**——将自然语言意图编译为 LLM 可执行的 Prompt，支持 Self-Bootstrap 和分布式部署。

### 核心理念

- **语义 VM**: LLM 作为处理器，语义指令作为"机器码"
- **分布式**: 多节点集群，一致性哈希内存，HTTP RPC 通信
- **进程管理**: 分布式 PCB (Process Control Block) 与 Fork/Exec 调度
- **Self-Bootstrap**: 系统可以动态修改自身的规则和指令集
- **Interface**: 提供类似 Linux 的 Shell 和 RESTful API 网关

### 架构概览

```
3 Layer / 7 Level:

Layer 1: Application Layer (应用层)
  ↓ 调用意图 (Shell / API / Apps)
Layer 2: Intent Layer (意图层 - 7 Level 处理流程)
  [Level 1] 意图解析 → [Level 2] 任务规划 → [Level 3] 上下文收集 → 
  [Level 4] 安全验证 → [Level 5] 能力绑定 → [Level 6] 执行 (Distributed VM / Scheduler) → [Level 7] 改进
  ↓ 执行 Prompt (Semantic Opcode)
Layer 3: Model Layer (模型层 - LLM Processor)
```

### 技术栈

- **语言**: Python 3.10+
- **通信**: aiohttp (REST RPC)
- **UI/UX**: rich (Shell Interface)
- **类型系统**: 完整类型注解 (90%+ 覆盖率)
- **测试**: pytest, pytest-asyncio

---

## 代码规范

### 类型注解 (强制要求)

**所有代码必须使用类型注解**，这是 IntentOS 的核心要求：

```python
# ✅ 正确 - 使用类型注解
from typing import Any, Optional, list

def process_data(
    data: dict[str, Any],
    timeout: int = 30,
    callback: Optional[Callable] = None
) -> list[dict[str, Any]]:
    """处理数据"""
    ...

class DataProcessor:
    """数据处理器"""
    
    def __init__(self, config: dict[str, Any]) -> None:
        self.config: dict[str, Any] = config
        self._cache: dict[str, Any] = {}
    
    async def process(self, data: str) -> dict[str, Any]:
        """处理数据"""
        ...
```

```python
# ❌ 错误 - 缺少类型注解
def process_data(data, timeout=30, callback=None):
    ...

class DataProcessor:
    def __init__(self, config):
        self.config = config
    
    async def process(self, data):
        ...
```

### 类型注解规则

1. **函数参数和返回值** - 必须标注类型
2. **类属性** - 必须标注类型
3. **变量** - 复杂类型必须标注
4. **泛型** - 使用 `list[T]`, `dict[K, V]`, `Optional[T]` 等
5. **异步函数** - 使用 `async def` 和 `Awaitable[T]`

### 类型检查

使用 mypy 进行类型检查：

```bash
# 运行类型检查
mypy intentos --exclude deprecated/

# 配置 (pyproject.toml)
[tool.mypy]
python_version = "3.10"
exclude = ["deprecated/"]
ignore_missing_imports = true
disallow_untyped_defs = true
```

### 常见类型

```python
from typing import Any, Optional, Callable, Awaitable
from dataclasses import dataclass

# 基础类型
name: str
count: int
ratio: float
enabled: bool

# 容器类型
items: list[str]
mapping: dict[str, Any]
optional_value: Optional[str]

# 函数类型
callback: Callable[[str], bool]
async_callback: Callable[[str], Awaitable[bool]]

# 数据类
@dataclass
class Result:
    success: bool
    data: Optional[dict[str, Any]] = None
    error: Optional[str] = None
```

---

## 项目结构

```
IntentOS/
├── intentos/                # 主包 (~12,000 行代码)
│   ├── __init__.py          # 统一入口
│   │
│   ├── core/                # 核心数据模型
│   ├── semantic_vm/         # ⭐ 语义 VM (核心架构)
│   ├── distributed/         # ⭐ 分布式内核 (PCB/Process Manager/RPC)
│   ├── bootstrap/           # ⭐ Self-Bootstrap 层 (内核自修改)
│   ├── compiler/            # 编译器层 (L1/L2/L3 缓存 + 优化器)
│   ├── interface/           # ⭐ 接口层 (Shell + REST API)
│   ├── llm/                 # LLM 后端层
│   ├── registry/            # 意图仓库
│   ├── engine/              # 执行引擎
│   └── types.py             # 类型定义
│
├── examples/                # 示例代码
│   ├── demo_*.py            # 演示脚本
│   └── test_*.py            # 测试用例
│
├── docs/                    # 文档 (33 篇)
├── papers/                  # 论文 (3 篇)
├── README.md                # 项目说明
├── ROADMAP.md               # 项目路线图
└── pyproject.toml           # 项目配置
```

---

## 构建和运行

### 安装

```bash
# 基础安装
pip install -e .

# 启动 Shell
PYTHONPATH=. python intentos/interface/shell.py

# 启动 API 服务器
PYTHONPATH=. python intentos/interface/api.py
```

### 核心操作

- **Shell 指令 (需 / 前缀)**: `/ps`, `/top`, `/df`, `/mem`, `/nodes`, `/history`, `/kill`
- **自然语言**: 直接输入，如 "分析华东区销售数据"
- **API 调用**: `POST /v1/execute {"intent": "..."}`

---

## 核心模块更新 (v9.0)

### 1. 分布式内核与进程管理 (`intentos/distributed/`)
实现了完整的分布式进程子系统。
- **SemanticProcess (PCB)**: 追踪 PID、状态 (Running/Zombie等)、PC 计数器及执行上下文。
- **Fork/Exec 机制**: 实现语义程序的分布式调度、派生与实时监控。
- **Process Manager**: 充当内核调度器，管理全局进程表与节点负载均衡。
- **Distributed RPC**: 基于 `aiohttp` 实现真实的跨节点内存共享与进程控制。

### 2. Self-Bootstrap (`intentos/bootstrap/`)
支持内核级的在线热更新与安全审计。
- **指令扩展**: 可以动态向 `LLMProcessor` 注入新的 `_handle_<opcode>` 方法。
- **配置同步**: 修改系统关键 `CONFIG` 时自动在集群内广播。
- **审计轨迹**: `/history` 指令可回溯所有内核自修改动作。

### 3. 统一界面 (`intentos/interface/`)
提供了工业级系统交互入口。
- **IntentShell**: 支持命令模式 (`/ps`, `/kill`, `/top`) 与自然语言意图模式的无缝切换。
- **API Gateway**: v1 版本 RESTful API，支持多租户远程内核管理。

---

## 关键概念

### 语义指令集

| 指令类型 | 指令 | 说明 |
|---------|------|------|
| **基础指令** | CREATE/MODIFY/DELETE/QUERY | 存储操作 |
| **控制流** | IF/ELSE/LOOP/WHILE/JUMP | 图灵完备支持 |
| **分布式** | REPLICATE/SPAWN/BROADCAST | 集群协调 |
| **系统调用** | ps/kill/nodes | 内核级管理指令 |

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| **v9.0** | 2026-03-13 | 实现分布式进程管理与 PCB |
| **v8.5** | 2026-03-13 | 实现 Shell、API 及真实分布式 RPC |
| **v8.1** | 2026-03-13 | Map/Reduce 数据本地性优化 |
| **v8.0** | 2026-03-13 | 编译器优化系统 (三级缓存) |
| **v7.0** | 2026-03-13 | 类型注解补全 |
| **v0.7.0** | 2026-03-13 | 分布式语义 VM |
| **v0.6.0** | 2026-03-13 | Self-Bootstrap 内核 |

---

**最后更新**: 2026-03-13  
**版本**: v9.0 (Distributed Process Management)
