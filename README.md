# IntentOS - AI 原生操作系统

> **语言即系统 · Prompt 即可执行文件 · 语义 VM**

IntentOS 是一个 **AI 原生操作系统** 原型，核心是**语义虚拟机**——将自然语言意图编译为 LLM 可执行的 Prompt，支持 Self-Bootstrap 和分布式部署。

---

## 📊 架构蓝图

<embed src="./docs/IntentOS_Architecture_Blueprint.pdf" type="application/pdf" width="100%" height="600px" />

> 💡 如果 PDF 无法显示，请 [点击查看架构蓝图](./docs/IntentOS_Architecture_Blueprint.pdf)

---

## 🧠 核心理念：道即 Meta

IntentOS 的设计融合了东方哲学与西方计算机科学的精髓：

| 东方哲学 | 西方 CS 体系 | IntentOS 对应 |
|----------|-------------|---------------|
| **器** (万物) | Instance/Data | 具体的业务数据、运行中的进程 |
| **法** (规则) | Meta/Metadata | 意图定义、Prompt 模板、Schema |
| **道** (本源) | **Meta-Meta** | 语义 VM、Self-Bootstrap、演进算法 |

### 为什么"道"是终极 Meta？

在 IntentOS 中，"道"不仅是哲学概念，更是**技术架构的终极抽象**：

- **普通 Meta**：静态描述（如数据库 Schema、API 定义）
- **道 (Meta-Meta)**：**生成规则的规则**，驱动系统自我演进的元驱动力

```
自然语言意图 → [语义编译] → Prompt → [LLM 执行] → 结果
      ↓              ↓           ↓          ↓
    器 (Instance)   法 (Meta)   道 (Meta-Meta)  器 (新 Instance)
```

IntentOS 的"道"体现在：
1. **Self-Bootstrap**：系统可以修改自身的指令集和处理器逻辑
2. **语义 VM**：LLM 作为处理器，自然语言作为"机器码"
3. **分布式演进**：多节点集群中，语义一致性驱动系统自发演化

> 💡 **道生一，一生二，二生三，三生万物**  
> 在 IntentOS 中：**语义 VM → 意图/能力 → 进程/节点 → 分布式应用生态**

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

### 交互式 Shell

IntentOS 提供了一个类似 Linux Shell 的交互式界面，支持自然语言意图输入：

```bash
# 启动 Shell（交互式）
PYTHONPATH=. python intentos/interface/shell.py
```

在 Shell 中，你可以直接输入自然语言指令，或者使用内置命令：
- `status`: 查看内核状态
- `ls`: 列出所有可用的意图模板
- `clear`: 清除对话历史
- `exit`: 退出系统

### 守护进程模式（推荐）

IntentOS 可以作为后台守护进程持续运行：

```bash
# 启动守护进程
PYTHONPATH=. python intentos/interface/daemon.py
```

守护进程会：
- ✅ 持续运行，等待请求
- ✅ 自动处理中断信号（Ctrl+C）
- ✅ 记录运行时间和状态
- ✅ 优雅关闭系统资源

### REST API 网关

可以通过 HTTP 接口远程访问 IntentOS 内核：

```bash
# 启动 API 服务器 (默认 localhost:8080)
PYTHONPATH=. python intentos/interface/api.py
```

**示例请求**:
```bash
curl -X POST http://localhost:8080/execute \
     -H "Content-Type: application/json" \
     -d '{"intent": "分析销售数据"}'
```

### 带记忆注入的编译

```python
from intentos import IntentCompiler, create_and_initialize_memory_manager, Context

# 创建内存管理器
memory_manager = create_and_initialize_memory_manager()

# 创建编译器
compiler = IntentCompiler(memory_manager=memory_manager)

# 编译（自动注入相关记忆）
context = Context(user_id="user_001", session_id="session_abc")
prompt = compiler.compile("查询上季度销售数据", context=context)
```

---

## 🏗️ 核心架构

### 3 层 / 7 级处理流程

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Application Layer (应用层)                         │
│  • CRM App / Sales App / BI App                            │
│  • 领域意图包 + 用户交互 + 结果呈现                           │
└───────────────┬─────────────────────────────────────────────┘
                ↓ 调用意图
┌───────────────▼─────────────────────────────────────────────┐
│  Layer 2: Intent Layer (意图层 - 7 Level 处理流程)                  │
│  [Level 1] 意图解析 → 解析功能意图 + 操作意图                   │
│  [Level 2] 任务规划 → 生成任务 DAG + Ops Model                  │
│  [Level 3] 上下文收集 → 多模态事件图                            │
│  [Level 4] 安全验证 → 权限校验 + Human-in-the-loop             │
│  [Level 5] 能力绑定 → 绑定能力调用                              │
│  [Level 6] 执行 → 分布式调度执行                                │
│  [Level 7] 改进 → 意图漂移检测 + 自动修复                       │
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
- **3 Layer**: 应用层、意图层、模型层 (调用关系)
- **7 Level**: 意图层内部的七个处理阶段

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

## 🎯 核心特性

### 1. 语义 VM (Semantic VM)

IntentOS 的本质是一个语义虚拟机：
- **指令集**：语义指令 (CREATE/MODIFY/QUERY/LOOP/BRANCH...)
- **处理器**：LLM
- **内存**：语义存储 (意图/能力/策略/Prompt/上下文)
- **图灵完备**：是 (支持循环 + 分支)

**核心洞察**:
- LLM 是处理器，不是外部工具
- 语义指令在存储中，可自修改
- Self-Bootstrap 是语义 VM 的自然结果

### 2. 分布式内核

- **PCB (Process Control Block)**：追踪进程状态、PC 计数器
- **Fork/Exec**：分布式进程调度
- **一致性哈希内存**：跨节点语义存储
- **HTTP RPC**：节点间通信

### 3. Self-Bootstrap

系统可以动态修改自身：
- **指令扩展**：向 LLM Processor 注入新的 `_handle_<opcode>` 方法
- **配置同步**：修改 CONFIG 时自动广播到集群
- **审计轨迹**：`/history` 指令可回溯所有内核自修改动作

### 4. 意图编译器

将自然语言编译为 LLM Prompt：
- **L1 缓存**：意图解析结果缓存
- **L2 缓存**：Prompt 模板缓存
- **L3 缓存**：执行计划缓存
- **优化器**：Map/Reduce 数据本地性优化

---

## 📦 项目结构

```
IntentOS/
├── intentos/                # 主包
│   ├── core/                # 核心数据模型
│   ├── semantic_vm/         # ⭐ 语义 VM
│   ├── distributed/         # ⭐ 分布式内核
│   ├── bootstrap/           # ⭐ Self-Bootstrap
│   ├── compiler/            # 编译器 (三级缓存 + 优化器)
│   ├── interface/           # ⭐ Shell + REST API
│   ├── llm/                 # LLM 后端层
│   ├── registry/            # 意图仓库
│   ├── engine/              # 执行引擎
│   └── parser/              # 意图解析器
│
├── examples/                # 示例代码
├── docs/                    # 文档
├── tests/                   # 测试
└── README.md                # 项目说明
```

---

## 🧪 测试与质量

```bash
# 运行测试
pytest

# 类型检查
mypy intentos --exclude deprecated/

# 代码格式
ruff check .
ruff format --check .
```

**质量指标**:
- ✅ 测试覆盖：99.87% (759/760)
- ✅ 类型检查：Mypy 0 错误
- ✅ 代码格式：Ruff 全部通过

---

## 📚 文档与论文

- **架构蓝图**: [docs/IntentOS_Architecture_Blueprint.pdf](./docs/IntentOS_Architecture_Blueprint.pdf)
- **技术文档**: [docs/](./docs/)
- **研究论文**: [papers/](./papers/)

---

## 🛣️ 路线图

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

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

**最后更新**: 2026-03-15  
**版本**: v9.0 (Distributed Process Management)  
**状态**: ✅ Production Ready
