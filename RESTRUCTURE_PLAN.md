# IntentOS 代码结构重组

## 当前结构问题

```
intentos/
├── core/                    # 核心数据模型
├── parser/                  # 意图解析器 (旧架构)
├── compiler/                # 编译器
├── llm/                     # LLM 后端
├── registry/                # 意图仓库
├── engine/                  # 执行引擎
├── interface/               # 接口层
├── parallel.py              # 并行执行 (位置不当)
├── memory.py                # 记忆管理 (位置不当)
├── distributed_memory.py    # 分布式记忆 (位置不当)
├── prompt_format.py         # PEF 规范 (位置不当)
├── intentgarden_v2.py       # 七层架构 (位置不当)
├── compiler_v2.py           # 旧编译器
├── compiler_v3.py           # 新编译器 (LLM 驱动)
├── semantic_vm.py           # 语义 VM
├── distributed_semantic_vm.py # 分布式语义 VM
├── self_bootstrap.py        # Self-Bootstrap (旧)
├── self_bootstrap_executor.py # Self-Bootstrap 执行器
└── examples/                # 示例
```

**问题**:
1. 新旧架构混杂 (v2/v3 编译器并存)
2. 核心组件分散 (semantic_vm 在根目录)
3. 模块职责不清 (parallel.py/memory.py 等)
4. Self-Bootstrap 分散在多处

## 新结构设计

```
intentos/
├── __init__.py              # 统一入口
│
├── core/                    # 核心层
│   ├── __init__.py
│   ├── models.py            # 基础数据模型 (Intent, Context, Capability)
│   ├── types.py             # 类型定义 (Enums)
│   └── errors.py            # 异常定义
│
├── semantic_vm/             # 语义 VM 层 (核心架构)
│   ├── __init__.py
│   ├── vm.py                # SemanticVM 主类
│   ├── instructions.py      # 语义指令集
│   ├── memory.py            # 语义内存
│   ├── processor.py         # LLM 处理器
│   └── program.py           # 语义程序
│
├── distributed/             # 分布式层
│   ├── __init__.py
│   ├── cluster.py           # 分布式集群
│   ├── memory.py            # 分布式语义内存
│   ├── coordinator.py       # 执行协调器
│   └── opcodes.py           # 分布式指令集
│
├── bootstrap/               # Self-Bootstrap 层
│   ├── __init__.py
│   ├── executor.py          # Self-Bootstrap 执行器
│   ├── policy.py            # 自举策略
│   ├── programs.py          # 自举程序库
│   ├── validator.py         # 自举验证器
│   └── records.py           # 自举记录
│
├── compiler/                # 编译器层 (LLM 驱动)
│   ├── __init__.py
│   ├── parser.py            # LLM 解析器
│   ├── generator.py         # 代码生成器
│   └── linker.py            # 链接器
│
├── llm/                     # LLM 后端层
│   ├── __init__.py
│   ├── base.py              # LLM 后端抽象
│   ├── openai.py            # OpenAI 后端
│   ├── anthropic.py         # Anthropic 后端
│   ├── ollama.py            # Ollama 后端
│   └── mock.py              # Mock 后端
│
├── registry/                # 意图仓库层
│   ├── __init__.py
│   └── registry.py          # IntentRegistry
│
├── engine/                  # 执行引擎层
│   ├── __init__.py
│   ├── dag.py               # DAG 执行引擎
│   └── mapreduce.py         # Map/Reduce 引擎
│
├── memory/                  # 记忆管理层 (兼容层)
│   ├── __init__.py
│   ├── short_term.py        # 短期记忆
│   ├── long_term.py         # 长期记忆
│   └── distributed.py       # 分布式记忆 (兼容旧 API)
│
├── interface/               # 接口层
│   ├── __init__.py
│   └── interface.py         # IntentOS 主接口
│
├── examples/                # 示例代码
│   ├── demo_semantic_vm.py
│   ├── demo_distributed.py
│   ├── demo_bootstrap.py
│   └── test_*.py
│
└── utils/                   # 工具函数
    ├── __init__.py
    └── helpers.py
```

## 迁移计划

### 阶段 1: 创建新结构
- [ ] 创建新目录结构
- [ ] 移动文件到新位置
- [ ] 更新导入路径

### 阶段 2: 清理旧代码
- [ ] 移除旧编译器 (compiler_v2.py)
- [ ] 移除旧 Self-Bootstrap (self_bootstrap.py)
- [ ] 移除冗余文件 (intentgarden_v2.py, parallel.py 等)

### 阶段 3: 统一入口
- [ ] 更新 `__init__.py`
- [ ] 提供向后兼容的 API
- [ ] 更新示例代码

### 阶段 4: 测试验证
- [ ] 运行所有测试
- [ ] 验证示例代码
- [ ] 更新文档

## 核心架构说明

```
┌─────────────────────────────────────────────────────────────┐
│  IntentOS                                                   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Interface Layer (interface/)                        │   │
│  │  - IntentOS 主接口                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↑                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Bootstrap Layer (bootstrap/)                        │   │
│  │  - Self-Bootstrap 执行器                             │   │
│  │  - 自举程序库                                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↑                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Distributed Layer (distributed/)                    │   │
│  │  - 分布式集群                                        │   │
│  │  - 分布式语义内存                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↑                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Semantic VM Layer (semantic_vm/)                    │   │
│  │  - 语义 VM 核心                                       │   │
│  │  - 语义指令集                                        │   │
│  │  - LLM 处理器                                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↑                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Compiler Layer (compiler/)                          │   │
│  │  - LLM 解析器                                         │   │
│  │  - 代码生成器                                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↑                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  LLM Layer (llm/)                                    │   │
│  │  - OpenAI/Anthropic/Ollama/Mock                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↑                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Core Layer (core/)                                  │   │
│  │  - 基础数据模型                                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 导入示例

### 旧导入
```python
from intentos.semantic_vm import SemanticVM
from intentos.distributed_semantic_vm import DistributedSemanticVM
from intentos.self_bootstrap_executor import SelfBootstrapExecutor
```

### 新导入
```python
from intentos.semantic_vm import SemanticVM
from intentos.distributed import DistributedSemanticVM
from intentos.bootstrap import SelfBootstrapExecutor
```

### 统一入口
```python
from intentos import (
    SemanticVM,
    DistributedSemanticVM,
    SelfBootstrapExecutor,
    create_semantic_vm,
    create_distributed_vm,
    create_bootstrap_executor,
)
```

## 向后兼容

为了平滑迁移，提供兼容性模块：

```python
# intentos/compat.py
from intentos.semantic_vm import SemanticVM
from intentos.distributed import DistributedSemanticVM
from intentos.bootstrap import SelfBootstrapExecutor

# 旧 API 仍然可用
from intentos.compat import (
    SemanticVM as OldSemanticVM,
    DistributedSemanticVM as OldDistributedSemanticVM,
)
```
