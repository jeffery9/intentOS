# IntentOS / IntentGarden v2.0

> **语言即系统 · Prompt 即可执行文件 · 意图编译器**

IntentGarden v2.0 是一个 **Cloud-Native AI 原生操作系统** 原型，核心是**意图编译器**——将自然语言意图编译为 LLM 可执行的 Prompt。

---

## 🚀 核心理念

### IntentOS 是意图编译器

| 传统编译器 | IntentOS 意图编译器 |
|-----------|-------------------|
| 源代码 (Source Code) | **自然语言意图** |
| 机器码 (Machine Code) | **Prompt** |
| CPU | **LLM** |
| 库函数 | **能力 (Capability)** |
| 内存/存储 | **记忆 (Memory)** |
| 链接器 | **Prompt 链接器** |

### 编译流程

```
自然语言 → Lexer → Tokens → Parser → AST → SemanticAnalyzer → 
StructuredIntent → CodeGenerator → Prompt → Linker → Executable
```

---

## 📋 快速开始

### 安装

```bash
pip install pyyaml
```

### 使用意图编译器

```python
from intentos import IntentCompiler

# 创建编译器
compiler = IntentCompiler()

# 编译意图
prompt = compiler.compile("分析华东区 Q3 销售数据")

print(f"动作：{prompt.intent.action}")
print(f"目标：{prompt.intent.target}")
print(f"参数：{prompt.intent.parameters}")

# 获取 Prompt
print(prompt.system_prompt)
print(prompt.user_prompt)
```

### 编译并执行

```python
from intentos import create_compiler

async def demo():
    compiler = create_compiler()
    
    # 注册能力
    async def query_data(intent):
        return {"data": [1, 2, 3]}
    
    compiler.register_capability("data_query", query_data, "查询数据")
    
    # 编译并执行
    result = await compiler.execute("查询销售数据")
    print(result)

asyncio.run(demo())
```

---

## 🏗️ 架构概览

### 七层执行架构

```
┌─────────────────────────────────────────────────────────────┐
│  App Layer: 双意图入口                                       │
│  • 功能意图："对比华东华南 Q3 销售"                          │
│  • 操作意图："99% 请求延迟≤100ms"                           │
└───────────────┬─────────────────────────────────────────────┘
                ↓
┌───────────────▼─────────────────────────────────────────────┐
│  [L1] 意图层 → 解析功能意图 + 操作意图                       │
│  [L2] 规划层 → 生成任务 DAG + Ops Model                      │
│  [L3] 上下文层 → 多模态事件图                                │
│  [L4] 安全环 → 权限校验 + Human-in-the-loop                 │
│  [L5] 工具层 → 绑定能力调用                                  │
│  [L6] 执行层 → 分布式调度执行                                │
│  [L7] 改进层 → 意图漂移检测 + 自动修复                       │
└───────────────┬─────────────────────────────────────────────┘
                ↓
┌───────────────▼─────────────────────────────────────────────┐
│  LLM Layer: 语义 CPU (OpenAI/Anthropic/Ollama)              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 支持的 LLM 后端

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

## 🧠 记忆管理

### 记忆分层

| 类型 | 存储 | 生命周期 | 同步 |
|------|------|---------|------|
| **工作记忆** | 进程内 | 当前任务 | 无 |
| **短期记忆** | 内存 (LRU) | 分钟 - 小时 | 可选 |
| **长期记忆** | Redis/文件 | 天 - 年 | 分布式 |

```python
from intentos import create_memory_manager

async def demo():
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
    
    await manager.shutdown()

asyncio.run(demo())
```

---

## 📁 项目结构

```
intentos/
├── core/               # 核心数据模型
├── compiler_v2.py      # ⭐ 意图编译器
├── prompt_format.py    # PEF 规范
├── intentgarden_v2.py  # 七层架构
├── parallel.py         # DAG 并行执行
├── memory.py           # 内存管理 + Map/Reduce
├── distributed_memory.py # 分布式记忆
├── llm/backends/       # LLM 后端
└── examples/
    ├── demo.py
    ├── demo_compiler.py
    ├── demo_llm_backends.py
    ├── demo_parallel.py
    ├── demo_memory.py
    ├── demo_distributed_memory.py
    └── test_*.py
```

---

## 🧪 运行示例

```bash
# 编译器演示
python intentos/compiler_v2.py

# LLM 后端演示
python intentos/examples/demo_llm_backends.py

# 并行执行演示
python intentos/examples/demo_parallel.py

# 记忆管理演示
python intentos/examples/demo_memory.py

# 运行测试
python -m pytest intentos/examples/ -v
```

---

## ✅ 测试结果

```
======================== 150+ passed =========================
```

| 测试模块 | 测试数 |
|---------|--------|
| test_intentos.py | 23 |
| test_compiler.py | 16 |
| test_prompt_format.py | 30 |
| test_llm_backends.py | 23 |
| test_parallel.py | 27 |
| test_memory.py | 23 |
| test_distributed_memory.py | 26 |

---

## 📖 论文

详细架构设计请参考：[paper-intentos-architecture.md](paper-intentos-architecture.md)

---

## 🚧 下一步

- [ ] 改进中文分词
- [ ] 实现意图图谱
- [ ] 添加形式化验证
- [ ] 构建 Web UI

---

## License

MIT
