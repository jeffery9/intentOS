# IntentOS 概述

> IntentOS 是一个 AI 原生操作系统原型，核心是**意图编译器**——将自然语言意图编译为 LLM 可执行的 Prompt。

---

## 1. 什么是 IntentOS

**IntentOS** (意图操作系统) 是一个 AI 原生软件范式的原型实现，核心理念是：

- **语言是入口**，而非 UI
- **界面是派生**，而非固定容器
- **软件是执行**，而非工程产物

### 核心洞察

IntentOS 的本质是一个**意图编译器**：

| 传统编译器 | IntentOS 意图编译器 |
|-----------|-------------------|
| 源代码 (Source Code) | **自然语言意图** |
| 机器码 (Machine Code) | **Prompt** |
| CPU | **LLM** |
| 库函数 | **能力 (Capability)** |
| 内存/存储 | **记忆 (Memory)** |
| 链接器 | **Prompt 链接器** |

---

## 2. 3 Layer / 7 Level 架构

IntentOS 采用**3 Layer / 7 Level**架构模型：

### 2.1 3 Layer 架构

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Application Layer (应用层)                         │
│  • CRM App / Sales App / BI App                             │
│  • 领域意图包 + 用户交互 + 结果呈现                           │
└───────────────┬─────────────────────────────────────────────┘
                ↓ 意图调用
┌───────────────▼─────────────────────────────────────────────┐
│  Layer 2: IntentOS Layer (意图操作系统层 - 7 Level)                    │
│  • 意图编译 / 调度 / 执行 / 记忆                             │
└───────────────┬─────────────────────────────────────────────┘
                ↓ Prompt 执行
┌───────────────▼─────────────────────────────────────────────┐
│  Layer 1: LLM Layer (大语言模型层)                           │
│  • OpenAI / Anthropic / Ollama                              │
│  • 语义 CPU: 理解/推理/生成                                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 IntentOS 7 Level

```
┌─────────────────────────────────────────────────────────────┐
│  [Tier 7] 意图层 → 解析功能意图 + 操作意图                       │
│  [Tier 6] 规划层 → 生成任务 DAG + Ops Model                      │
│  [Tier 5] 上下文层 → 多模态事件图                                │
│  [Tier 4] 安全环 → 权限校验 + Human-in-the-loop                 │
│  [Tier 3] 工具层 → 绑定能力调用                                  │
│  [Tier 2] 执行层 → 分布式调度执行                                │
│  [Tier 1] 改进层 → 意图漂移检测 + 自动修复                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 核心组件

### 3.1 意图编译器

将自然语言编译为 LLM 可执行的 Prompt：

```
自然语言 → Lexer → Tokens → Parser → AST → SemanticAnalyzer → 
StructuredIntent → CodeGenerator → Prompt → Linker → Executable
```

### 3.2 Prompt 可执行格式 (PEF)

PEF 是 IntentOS 的"可执行文件格式"，类似 ELF/PE，但采用 YAML/JSON 声明式：

```yaml
metadata:
  version: "1.0.0"
  name: "sales_analysis"
  execution_mode: dag
  
intent:
  goal: "分析华东区 Q3 销售"
  intent_type: functional
  performance_targets:
    latency_p99_ms: 100
    
workflow:
  steps:
    - id: step1
      capability: query_data
    - id: step2
      capability: analyze
      depends_on: [step1]
```

### 3.3 分布式记忆系统 (Layer)

| 记忆类型 | 存储位置 | 生命周期 | 同步机制 |
|---------|---------|---------|---------|
| **工作记忆 (Layer)** | 进程内 | 当前任务 | 无 |
| **短期记忆 (Layer)** | 内存 (LRU) | 分钟 - 小时 | 可选 Redis |
| **长期记忆 (Layer)** | Redis/文件 | 天 - 年 | 分布式同步 |

### 3.4 执行引擎

支持多种执行模式：

- **顺序执行**: 任务按依赖顺序执行
- **并行执行**: 无依赖任务并行执行
- **分布式执行**: 跨节点调度执行
- **Map/Reduce**: 大数据处理

---

## 4. 快速示例

### 4.1 编译意图

```python
from intentos import IntentCompiler

compiler = IntentCompiler()
prompt = compiler.compile("分析华东区 Q3 销售数据")

print(f"动作：{prompt.intent.action}")
print(f"目标：{prompt.intent.target}")
print(f"参数：{prompt.intent.parameters}")
```

### 4.2 执行意图

```python
from intentos import IntentOS

os = IntentOS()
os.initialize()

result = await os.execute("分析华东区 Q3 销售数据")
print(result)
```

### 4.3 记忆管理

```python
from intentos import create_memory_manager

manager = await create_and_initialize_memory_manager(
    short_term_max=1000,
    long_term_enabled=True,
)

# 设置记忆
await manager.set_long_term(
    key="knowledge:fact:1",
    value={"fact": "地球是圆的"},
    tags=["knowledge"],
)

# 检索
entry = await manager.get("knowledge:fact:1")
```

---

## 5. 支持的 LLM 后端

| 提供商 | 模型 | 配置 |
|--------|------|------|
| **Mock** | mock-model | `provider="mock"` |
| **OpenAI** | GPT-4o, GPT-4 | `provider="openai"` |
| **Anthropic** | Claude 3/3.5 | `provider="anthropic"` |
| **Ollama** | Llama 3.1 | `provider="ollama"` |

```python
from intentos import create_executor

# OpenAI
executor = create_executor(provider="openai", api_key="sk-...")

# Anthropic
executor = create_executor(provider="anthropic", api_key="...")

# Ollama (本地)
executor = create_executor(provider="ollama", host="http://localhost:11434")
```

---

## 6. 项目结构

```
intentos/
├── core/               # 核心数据模型
├── compiler_v2.py      # 意图编译器
├── prompt_format.py    # PEF 规范
├── intentgarden_v2.py  # 7 Level 执行架构
├── parallel.py         # DAG 并行执行
├── memory.py           # 内存管理 + Map/Reduce
├── distributed_memory.py # 分布式记忆
├── llm/backends/       # LLM 后端
└── examples/           # 示例和测试
```

---

## 7. 下一步

- [阅读垂直3 Layer + 水平7 Level 架构文档](../02-architecture/01-three-layer-model.md)
- [学习编译器原理](../03-compiler/01-compiler-architecture.md)
- [构建第一个 App](../07-guides/01-build-first-app.md)

---

**下一篇**: [快速开始](04-quickstart.md)

**上一篇**: [从界面到意图](02-from-ui-to-intent.md)
