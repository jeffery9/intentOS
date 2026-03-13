# IntentOS - AI 原生操作系统

> **语言即系统 · Prompt 即可执行文件 · 语义 VM**

IntentOS 是一个 **AI 原生操作系统** 原型，核心是**语义虚拟机**——将自然语言意图编译为 LLM 可执行的 Prompt，支持 Self-Bootstrap 和分布式部署。

**代码仓库**: `https://github.com/jeffery9/IntentOS`

---

## 🚀 快速开始

### 安装

```bash
pip install pyyaml
```

### 使用语义 VM

```python
from intentos import SemanticVM, create_semantic_vm

# 创建语义 VM
vm = create_semantic_vm(llm_executor)

# 加载程序
await vm.load_program(program)

# 执行程序
result = await vm.execute_program("my_program")
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

### 垂直三层 + 水平七级

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Application Layer (应用层)                         │
│  • CRM App / Sales App / BI App                            │
│  • 领域意图包 + 用户交互 + 结果呈现                           │
└───────────────┬─────────────────────────────────────────────┘
                ↓ 调用意图
┌───────────────▼─────────────────────────────────────────────┐
│  Layer 2: Intent Layer (意图层 - 七级处理流程)                │
│  [1 级] 意图解析 → 解析功能意图 + 操作意图                   │
│  [2 级] 任务规划 → 生成任务 DAG + Ops Model                  │
│  [3 级] 上下文收集 → 多模态事件图                            │
│  [4 级] 安全验证 → 权限校验 + Human-in-the-loop             │
│  [5 级] 能力绑定 → 绑定能力调用                              │
│  [6 级] 执行 → 分布式调度执行                                │
│  [7 级] 改进 → 意图漂移检测 + 自动修复                       │
└───────────────┬─────────────────────────────────────────────┘
                ↓ 执行 Prompt
┌───────────────▼─────────────────────────────────────────────┐
│  Layer 3: Model Layer (模型层)                               │
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

**术语说明**:
- **垂直三层**: 应用层、意图层、模型层 (调用关系)
- **水平七级**: 意图层内部的七个处理阶段

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
IntentOS/
├── intentos/                # 主包 (~10,000 行代码)
│   ├── __init__.py          # 统一入口
│   │
│   ├── core/                # 核心数据模型
│   ├── semantic_vm/         # ⭐ 语义 VM (核心架构)
│   ├── distributed/         # ⭐ 分布式层
│   ├── bootstrap/           # ⭐ Self-Bootstrap 层
│   ├── compiler/            # 编译器层 (LLM 驱动)
│   ├── llm/                 # LLM 后端层
│   ├── registry/            # 意图仓库
│   ├── engine/              # 执行引擎
│   └── types.py             # 类型定义
│
├── examples/                # 示例代码 (18 个文件)
│   ├── demo_semantic_vm.py
│   ├── demo_distributed_semantic_vm.py
│   ├── demo_complete_bootstrap.py
│   └── test_*.py (10 个测试文件)
│
├── docs/                    # 文档 (33 篇，~18,000 行)
├── papers/                  # 论文 (3 篇，~32,000 字)
├── README.md                # 项目说明
├── ROADMAP.md               # 项目路线图
└── pyproject.toml           # 项目配置
```

---

## 🧪 运行示例

```bash
# 语义 VM 演示
python examples/demo_semantic_vm.py

# 分布式语义 VM 演示
python examples/demo_distributed_semantic_vm.py

# Self-Bootstrap 演示
python examples/demo_complete_bootstrap.py

# 运行测试
python -m pytest examples/ -v
```

---

## 📊 项目统计

| 指标 | 数值 |
|------|------|
| **核心代码** | ~10,000 行 Python |
| **示例代码** | ~5,000 行 |
| **测试用例** | 150+ |
| **测试通过率** | 99% |
| **类型覆盖率** | 90%+ |
| **文档** | 33 篇，~18,000 行 |
| **论文** | 3 篇，~32,000 字 |

---

## 📚 文档导航

完整文档位于 [`docs/`](docs/) 目录：

### 第一部分：入门 (4 篇)
- 什么是 AI 原生软件
- 从界面到意图
- IntentOS 概述
- 快速开始

### 第二部分：架构 (9 篇)
- 垂直三层架构
- 水平七级流程
- 意图即元语言
- Self-Bootstrap
- 分布式架构
- 上下文层
- 云基础设施
- Self-Bootstrap 架构
- 语义 VM 架构
- 完整 Self-Bootstrap

### 第三部分：编译器 (4 篇)
- 意图编译器架构
- PEF 规范
- 代码生成
- 链接器

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

## 📄 核心论文

| 论文 | 主题 | 字数 |
|------|------|------|
| **semantic-vm-paper.md** | 语义 VM 架构 | ~10,000 字 |
| **intentos-architecture-paper.md** | IntentOS 三层七级架构 | ~10,000 字 |
| **pef-compiler-paper.md** | PEF 与编译器 | ~12,000 字 |
| **总计** | - | **~32,000 字** |

---

## 🔗 相关资源

| 资源 | 链接 |
|------|------|
| **文档索引** | [docs/README.md](docs/README.md) |
| **项目路线图** | [ROADMAP.md](ROADMAP.md) |
| **代码仓库** | [GitHub](https://github.com/jeffery9/IntentOS) |

---

## 🚧 下一步 (v0.7.0)

根据 [ROADMAP.md](ROADMAP.md)，下一步优先改进项：

### 高优先级 🔴

1. **实现分布式通信** (distributed/vm.py)
   - 实现 gRPC/HTTP 通信
   - 添加节点健康检查
   - 实现故障转移

2. **完善错误处理** (所有模块)
   - 细化错误类型
   - 添加错误恢复机制
   - 添加重试逻辑

3. **加强安全性** (所有模块)
   - 所有写操作添加权限检查
   - 所有输入添加验证
   - 添加操作审计

### 中优先级 🟡

4. **添加类型注解** (所有模块)
   - 使用 mypy 检查
   - 目标：100% 类型覆盖

5. **提升测试覆盖率** (测试文件)
   - 目标：90%+ 覆盖率
   - 添加集成测试
   - 添加性能测试

---

## 📝 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.5.0 | 2026-03-12 | 基础架构完成 |
| v0.6.0 | 2026-03-13 | 语义 VM + Self-Bootstrap |
| v0.7.0 | 2026-03-13 | 分布式语义 VM |
| v7.0 | 2026-03-13 | 类型注解补全 (90%+) |

---

## License

MIT
