# IntentOS - AI 原生操作系统

> **语言即系统 · Prompt 即可执行文件 · 意图编译器**

IntentGarden v2.0 是一个 **Cloud-Native AI 原生操作系统** 原型，核心是**意图编译器**——将自然语言意图编译为 LLM 可执行的 Prompt，运行在云计算基础设施之上。

---

## 🚀 快速开始

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

# 查看结果
print(f"动作：{prompt.intent.action}")
print(f"目标：{prompt.intent.target}")
print(f"System Prompt: {prompt.system_prompt[:200]}...")
```

### 带记忆注入的编译

```python
from intentos import IntentCompiler, create_and_initialize_memory_manager, Context

# 创建记忆管理器
memory_manager = await create_and_initialize_memory_manager(
    short_term_max=1000,
    long_term_enabled=True,
)

# 设置记忆
await memory_manager.set_short_term(
    key="user:manager_001:preference",
    value={"region": "华东", "format": "dashboard"},
)

# 创建编译器（带记忆管理器）
compiler = IntentCompiler(
    capabilities={"analyze": {"description": "分析数据"}},
    memory_manager=memory_manager,
)

# 编译并注入记忆
context = Context(user_id="manager_001")
executable = await compiler.compile_and_link("分析销售数据", context)

# 查看注入的记忆
print(executable["memories"])  # 用户偏好等上下文记忆
```

---

## 🏗️ 架构概览

### 三层七层架构

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Application Layer (应用层)                         │
│  • CRM App / Sales App / BI App                            │
│  • 领域意图包 + 用户交互 + 结果呈现                           │
└───────────────┬─────────────────────────────────────────────┘
                ↓ 意图调用
┌───────────────▼─────────────────────────────────────────────┐
│  Layer 2: IntentOS Layer (意图操作系统层 - 七层)              │
│  [L1] 意图层 → 解析功能意图 + 操作意图                       │
│  [L2] 规划层 → 生成任务 DAG + Ops Model                      │
│  [L3] 上下文层 → 多模态事件图                                │
│  [L4] 安全环 → 权限校验 + Human-in-the-loop                 │
│  [L5] 工具层 → 绑定能力调用                                  │
│  [L6] 执行层 → 分布式调度执行                                │
│  [L7] 改进层 → 意图漂移检测 + 自动修复                       │
└───────────────┬─────────────────────────────────────────────┘
                ↓ Prompt 执行
┌───────────────▼─────────────────────────────────────────────┐
│  Layer 3: LLM Layer (大语言模型层)                           │
│  • OpenAI / Anthropic / Ollama                              │
│  • 语义 CPU: 理解/推理/生成                                   │
└─────────────────────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────────────────────┐
│  Cloud Infrastructure (云计算基础设施)                        │
│  • Kubernetes/ECS: 容器化部署                                │
│  • Redis: 短期记忆存储                                       │
│  • S3: 长期记忆存储                                          │
│  • API Gateway: API 暴露                                     │
│  • CloudWatch: 监控和告警                                    │
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

## 🧠 记忆系统

### 记忆分层

| 类型 | 存储 | 生命周期 | 同步 |
|------|------|---------|------|
| **工作记忆** | 进程内 | 当前任务 | 无 |
| **短期记忆** | Redis (LRU) | 分钟 - 小时 | 可选 |
| **长期记忆** | Redis/S3 | 天 - 年 | 分布式同步 |

```python
from intentos import create_memory_manager

manager = await create_and_initialize_memory_manager(
    short_term_max=10000,
    long_term_enabled=True,
    long_term_backend="redis",
    redis_host="localhost",
)

# 设置记忆
await manager.set_short_term(
    key="user:123:preference",
    value={"theme": "dark"},
    ttl_seconds=3600,
)

# 检索记忆
entry = await manager.get("user:123:preference")
```

---

## 📁 项目结构

```
intentos/
├── core/                   # 核心数据模型
│   └── models.py           # Intent, Capability, Context
├── compiler_v2.py          # ⭐ 意图编译器（含记忆注入）
├── prompt_format.py        # PEF 规范
├── intentgarden_v2.py      # 七层执行架构
├── parallel.py             # DAG 并行执行
├── memory.py               # 内存管理 + Map/Reduce
├── distributed_memory.py   # 分布式记忆系统
├── llm/
│   └── backends/           # LLM 后端 (OpenAI/Anthropic/Ollama)
└── examples/               # 示例和测试
    ├── demo.py
    ├── demo_compiler.py
    ├── demo_llm_backends.py
    ├── demo_parallel.py
    ├── demo_memory.py
    └── test_*.py
```

---

## 🧪 运行示例

```bash
# 编译器演示（含记忆注入）
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

## 📊 项目统计

| 指标 | 数值 |
|------|------|
| **代码行数** | ~10,000 Python |
| **测试用例** | 150+ |
| **测试通过率** | 99% |
| **文档篇数** | 30 |
| **论文篇数** | 3 |
| **文档覆盖** | 100% |

---

## 📚 文档导航

完整文档位于 [`docs/`](docs/) 目录：

### 第一部分：入门 (4 篇)
- 什么是 AI 原生软件
- 从界面到意图
- IntentOS 概述
- 快速开始

### 第二部分：架构 (6 篇)
- 三层七层架构
- 意图即元语言
- Self-Bootstrap
- 分布式架构
- **上下文层**
- **云基础设施** ☁️

### 第三部分：编译器 (4 篇)
- 意图编译器架构
- PEF 规范
- 代码生成
- **链接器（含记忆注入）**

### 第四部分：记忆 (4 篇)
- 记忆分层架构
- 分布式记忆同步
- 记忆检索
- 过期策略

### 第五部分：执行 (4 篇)
- DAG 执行引擎
- Map/Reduce
- 记忆优化
- LLM 后端

### 第六部分：API 参考 (4 篇)
- 核心 API
- 编译器 API
- 记忆 API
- 执行 API

### 第七部分：指南 (4 篇)
- 构建第一个 App
- 定义意图模板
- 注册能力
- 部署 IntentOS

---

## 🔗 相关资源

| 资源 | 链接 |
|------|------|
| **文档索引** | [docs/README.md](docs/README.md) |
| **项目路线图** | [ROADMAP.md](ROADMAP.md) |
| **论文：三层七层架构** | [paper-three-layer-architecture.md](paper-three-layer-architecture.md) |
| **论文：IntentOS 架构** | [paper-intentos-architecture.md](paper-intentos-architecture.md) |
| **论文：PEF 与编译器** | [paper-pef-compiler.md](paper-pef-compiler.md) |
| **示例代码** | [intentos/examples/](intentos/examples/) |

---

## 🚧 下一步 (v0.6.0)

- [ ] **意图图谱支持**: 支持复杂意图的图结构表示和多跳推理
- [ ] **形式化验证**: 确保意图执行的正确性和安全性
- [ ] **性能优化**: Prompt 缓存、记忆检索优化、并行编译
- [ ] **开发者工具**: CLI 工具、PEF 语言服务器、可视化 DAG 编辑器

详见 [ROADMAP.md](ROADMAP.md)

---

## 📝 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.5.0 | 2026-03-12 | 基础架构完成，记忆注入实现 |
| v0.4.0 | 2026-03-10 | 记忆管理系统完成 |
| v0.3.0 | 2026-03-08 | 多 LLM 后端支持 |
| v0.2.0 | 2026-03-05 | PEF 规范定义 |
| v0.1.0 | 2026-03-01 | 初始版本 |

---

## License

MIT
