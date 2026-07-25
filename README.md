[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/jeffery9/intentOS)

---

# IntentOS - 分布式 AI 原生操作系统

> **AI 时代的 UNIX · 语言即系统 · Prompt 即可执行文件 · 分布式语义 VM**

IntentOS 是一个 **分布式 AI 原生操作系统**, 不是传统的 AI Agent 框架。

核心是**语义虚拟机 (Semantic VM)** —— 将自然语言意图编译为 PEF (Prompt Executable File), 由 LLM 作为处理器执行, 支持 Self-Bootstrap 和跨节点分布式部署。

---

### 🌌 AI 时代的 UNIX (The UNIX of the AI Era)

如果说 1969 年诞生的 UNIX 确立了以 **“字节流 (Bytes) 作为最小通用介质”** 和 **“一切皆文件 (Everything is a File)”** 的管道联结哲学；
那么 2026 年的 IntentOS 则确立了以 **“高维语义 (Semantics) 作为最小通用介质”** 和 **“一切皆意图 (Everything is an Intent)”** 的全新管道演进：

```
                    UNIX (1969)                  │               IntentOS (2026)
────────────────────────────────────────────────┼────────────────────────────────────────────────
 最小通用介质 │  Bytes / Text (字节/纯文本)      │  Semantics / Intent (高维语义/意图)
 核心管道连接 │  cat data.txt | grep "error"    │  Read Watcher | Analyze Log | Apoptosis Skill
 阻抗对齐方式 │  手动编写 sed/awk/cut 胶水代码   │  _match_impedance (大模型动态热阻抗转换)
 通信与分发   │  TCP Sockets / IPC 进程间通信   │  SemanticP2P (社会化认知 Gossip / 意图 Relay)
```

通过 **「语义阻抗匹配器」**（`_match_impedance`），任意两个物理隔离、接口不对称的 I/O 节点在通过管道（`|`）连接时，都无需定义静态的 API 契约或编写手写胶水代码，操作系统会自动利用 LLM 将上游的非结构化输出在执行前夜智能转换、映射为下游物理 Skill/MCP 工具所需的强类型参数，真正实现万物在语义层面的“天下大同”与即插即用流水线拼装。

---

### 与传统 AI Agent 框架的本质区别

| 传统 AI Agent 框架 | IntentOS |
|-------------------|----------|
| 单节点应用层智能代理 | **分布式操作系统内核** |
| Tool Calling + LLM Loop | **语义 VM + PEF** (Prompt Executable File) |
| Prompt Engineering | **意图编译 → 语义执行** |
| 会话级上下文 | **全局语义地址空间** (跨节点) |

---

## 📊 架构蓝图

<object data="./docs/IntentOS_Architecture_Blueprint.pdf" type="application/pdf" width="100%" height="700px">
  <p>💡 如果 PDF 无法显示，请 <a href="./docs/IntentOS_Architecture_Blueprint.pdf" target="_blank">点击打开</a></p>
</object>

### 架构总览

![IntentOS 架构图](./docs/images/image.png)


## 🧠 核心理念：道即 Meta-Meta

IntentOS 的设计融合了东方哲学与西方计算机科学的精髓：

| 东方哲学 | 西方 CS 体系 | IntentOS 对应 |
|----------|-------------|---------------|
| **器** (万物) | Instance/Data | 具体的业务数据、运行中的进程 |
| **法** (规则) | Meta/Metadata | 意图定义、Prompt 模板、Schema |
| **道** (本源) | **Meta-Meta** | 语义 VM、Self-Bootstrap、演进算法 |

### 为什么"道"是终极 Meta-Meta？

在 IntentOS 中，"道"不仅是哲学概念，更是**技术架构的终极抽象**：

- **普通 Meta**：静态描述（如数据库 Schema、API 定义）
- **道 (Meta-Meta)**：**生成规则的规则**，驱动系统自我演进的元驱动力

```
自然语言意图 → [语义编译] → PEF → [语义 VM 执行] → 结果
      ↓              ↓           ↓          ↓
    器 (Instance)   法 (Meta)   道 (Meta-Meta)  器 (新 Instance)
```

IntentOS 的"道"体现在：
1. **Self-Bootstrap**：系统可以修改自身的指令集和处理器逻辑
2. **语义 VM**：LLM 作为处理器，PEF 作为机器码
3. **分布式演进**：多节点集群中，语义一致性驱动系统自发演化

> 💡 **道生一，一生二，二生三，三生万物**
> 在 IntentOS 中：**语义 VM → 意图/能力 → 进程/节点 → 分布式应用生态**

---

## 🚀 快速开始

### 核心抽象：用户意图 → PEF → 语义执行

```
用户输入自然语言意图
    ↓
意图编译器编译为 PEF (Prompt Executable File)
    ↓
语义 VM 加载并执行 PEF
    ↓
LLM 作为处理器执行语义指令
    ↓
需要 IO 时 → 查询能力注册中心 → 调用运行时 Agent 提供的能力
    ↓
结果返回给用户
```

### 使用语义 VM

```python
from intentos.compiler import IntentCompiler
from intentos.semantic_vm import SemanticVM
from intentos.agent import AgentContext

# 1. 编译用户意图为 PEF
compiler = IntentCompiler()
pef = compiler.compile("分析华东区 Q3 销售数据")

# 2. 创建语义 VM 和执行上下文
vm = SemanticVM()
context = AgentContext(user_id="demo", permissions=["data:read"])

# 3. 执行 PEF
result = await vm.execute(pef, context)

print(result.message)  # 自然语言回复
print(result.data)     # 数据结果
```

### 分布式执行

```python
from intentos.runtime import RuntimeAgent

# 创建运行时 Agent (节点 Daemon)
runtime_agent = RuntimeAgent(
    node_id="node1",
    cluster_nodes=["node2", "node3"],
)

# 启动节点
await runtime_agent.start()

# 分布式执行 (Map-Reduce)
data_partitions = {
    "node2": {"region": "华东", "period": "Q3"},
    "node3": {"region": "华南", "period": "Q3"},
}

results = await runtime_agent.map_reduce(pef, data_partitions)
summary = await runtime_agent.reduce_results(list(results.values()))
```

### 统一启动入口

IntentOS 采用 **客户端 - 服务器架构**，提供统一的命令行启动入口：

```bash
# 查看帮助
intentos --help

# 或使用 Python 模块方式运行
python -m intentos --help
```

#### 架构说明

IntentOS 采用 **进程分离架构**：
- **Daemon（服务器）**：运行 IntentOS 内核，提供 RPC 服务和 API 网关
- **CLI（客户端）**：连接到运行中的内核，提供统一的交互界面

```
┌─────────────────────────────────────────────────────────────┐
│                    IntentOS Daemon (服务器)                  │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────┐ │
│  │  IntentOS     │  │  RPC Server   │  │   API Gateway   │ │
│  │  Kernel       │  │  (Unix Socket)│  │   (可选启动)    │ │
│  └───────────────┘  └───────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                             ▲
                             │
                    ┌────────┴────────┐
                    │  IntentOS CLI   │
                    │  (统一界面)      │
                    └─────────────────┘
```

#### 1. 启动内核（必须先执行）

```bash
# 启动守护进程（仅内核）
intentos daemon

# 启动守护进程（内核 + API 网关）
intentos daemon --api

# 自定义 API 监听地址和端口
intentos daemon --api --api-host 0.0.0.0 --api-port 8080
```

守护进程会：
- ✅ 初始化 IntentOS 内核
- ✅ 启动后台服务（Watchdog 等）
- ✅ 创建 Unix Socket 监听 RPC 请求
- ✅ 如果指定 `--api`，同时启动 HTTP API 网关
- ✅ 持续运行直到接收到中断信号

> 💡 **提示**：如果未手动启动内核，执行 `intentos cli` 时会自动启动内核进程。

#### 2. CLI - 统一交互界面

IntentOS CLI 整合了 Shell 和 Chat 功能，提供统一的交互界面：

```bash
# 启动 CLI（交互式）
intentos cli

# 或使用 Python 模块方式
python -m intentos cli
```

在 CLI 中，你可以：
- **直接输入自然语言**执行意图（例如："分析销售数据"）
- **使用系统命令**：
  - `/help` - 显示帮助
  - `/status` - 查看内核状态
  - `/ping` - 心跳检测
  - `/clear` - 清空屏幕
  - `/quit` 或 `/exit` - 退出

**示例**:
```
$ intentos cli
✅ 已连接到 IntentOS 内核

====================================================
       IntentOS CLI - AI Native Operating System      
====================================================

intentos> /status
┏━━━━━━━━┳━━━━━━━━━━┓
┃ 组件   ┃ 状态     ┃
┡━━━━━━━━╇━━━━━━━━━━┩
│ 内核   │ ✓ 运行中 │
│ 初始化 │ ✓ 已就绪 │
│ 能力   │ 3 个     │
│ 模板   │ 2 个     │
└────────┴──────────┘

intentos> 分析销售数据
┌─────────────────────────────────────┐
│ Response                            │
├─────────────────────────────────────┤
│ ✅ 已完成：分析销售数据              │
│ 结果：华东区 Q3 销售额增长 15%       │
└─────────────────────────────────────┘

intentos> /quit
👋 Goodbye!
```

#### 3. REST API

API 网关集成在 Daemon 中，启动时需要指定 `--api` 参数：

```bash
# 启动内核 + API 网关
intentos daemon --api

# 自定义监听地址和端口
intentos daemon --api --api-host 0.0.0.0 --api-port 8080
```

**示例请求**:
```bash
# 查看状态
curl http://localhost:8080/v1/status \
     -H "Authorization: Bearer intentos-secret-token"

# 执行意图
curl -X POST http://localhost:8080/v1/execute \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer intentos-secret-token" \
     -d '{"intent": "分析销售数据"}'

# 健康检查
curl http://localhost:8080/v1/health \
     -H "Authorization: Bearer intentos-secret-token"
```

**API Token**:
- 默认：`intentos-secret-token`
- 自定义：`export INTENTOS_API_TOKEN=your-token`

# 执行轨迹
intentos cli trace record --intent-id test-001 -o trace.json
intentos cli trace replay -i trace.json

# 系统状态
intentos cli status
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
│  Layer 3: Application Layer (应用层)                         │
│  • CRM App / Sales App / BI App                            │
│  • 领域意图包 + 用户交互 + 结果呈现                           │
└───────────────┬─────────────────────────────────────────────┘
                ↓ 调用意图
┌───────────────▼─────────────────────────────────────────────┐
│  Layer 2: Intent Layer (意图层 - 7 Level 处理流程)                  │
│  [Level 7] 意图解析 → 解析功能意图 + 操作意图                   │
│  [Level 6] 任务规划 → 生成任务 DAG + Ops Model                  │
│  [Level 5] 上下文收集 → 多模态事件图                            │
│  [Level 4] 安全验证 → 权限校验 + Human-in-the-loop             │
│  [Level 3] 能力绑定 → 绑定能力调用                              │
│  [Level 2] 执行 → 分布式调度执行                                │
│  [Level 1] 改进 → 意图漂移检测 + 自动修复                       │
└───────────────┬─────────────────────────────────────────────┘
                ↓ 执行 Prompt
┌───────────────▼─────────────────────────────────────────────┐
│  Layer 1: Model Layer (模型层)                               │
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

## 🌐 分布式架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│              PaaS 服务层 (intentos/paas/)                       │
│          AI Native App 层（构建在 OS 之上的服务层）               │
│  • 多租户管理 • 计费系统 • 应用市场 • 开发者工具                │
└────────────────────┬────────────────────────────────────────────┘
                     │ 使用 OS API
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              接口层 (intentos/interface/)                       │
│              分布式 OS 对外访问入口                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  REST API                                                │   │
│  │  • POST /v1/execute - 执行意图                           │   │
│  │  • GET /v1/status - 查看状态                             │   │
│  │  • GET /v1/nodes - 查看节点                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Chat Interface                                          │   │
│  │  • Shell TUI - 命令行聊天界面                            │   │
│  │  • WebSocket - 实时聊天                                  │   │
│  │  • Web UI - Web 界面                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼───────────────────────────────────────────┐
│         分布式语义 VM 集群 (跨网络组成整体 OS)                   │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  节点 1 (容器/主机)                                      │  │
│  │  ┌─────────────────────────────────────────────────┐   │  │
│  │  │  语义 VM                                        │   │  │
│  │  │  • 运行 PEF                                     │   │  │
│  │  │  • LLM 执行                                      │   │  │
│  │  │  ┌─────────────────────────────────────────┐   │   │  │
│  │  │  │  AI Agent (智能代理)                    │   │   │  │
│  │  │  │  • 基于 LLM                              │   │   │  │
│  │  │  │  • 理解意图、规划任务                    │   │   │  │
│  │  │  └─────────────────────────────────────────┘   │   │  │
│  │  └─────────────────────────────────────────────────┘   │  │
│  │  ┌─────────────────────────────────────────────────┐   │  │
│  │  │  运行时 Agent (分布式节点代理)                  │   │  │
│  │  │  • 提供本地能力（shell、文件系统）               │   │  │
│  │  │  • 管理 Skill 缓存                               │   │  │
│  │  │  • 分布式运行（Map-Reduce）                      │   │  │
│  │  │  • 结果汇总（LLM 汇总）                          │   │  │
│  │  │  • 跨节点通信                                    │   │  │
│  │  └─────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                           │                                   │
│  ┌────────────────────────┼───────────────────────────────┐  │
│  │                        │ 跨网络通信 (HTTP RPC)          │  │
│  └────────────────────────┼───────────────────────────────┘  │
│                           │                                   │
│  ┌────────────────────────▼───────────────────────────────┐  │
│  │  节点 2 (容器/主机)                                      │  │
│  │  ┌─────────────────────────────────────────────────┐   │  │
│  │  │  语义 VM                                        │   │  │
│  │  │  • 运行 PEF                                     │   │  │
│  │  │  • LLM 执行                                      │   │  │
│  │  └─────────────────────────────────────────────────┘   │  │
│  │  ┌─────────────────────────────────────────────────┐   │  │
│  │  │  运行时 Agent                                    │   │  │
│  │  │  • 提供本地能力                                  │   │  │
│  │  │  • 分布式运行                                    │   │  │
│  │  └─────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 核心组件

| 组件 | 位置 | 职责 | OS 视角 |
|------|------|------|---------|
| **语义 VM** | `intentos/semantic_vm/` | 执行 PEF, LLM 作为处理器 | **OS 内核** |
| **意图编译器** | `intentos/compiler/` | 用户意图 → PEF | **编译器** |
| **能力注册中心** | `intentos/agent/registry.py` | 管理系统调用能力 | **系统调用表** |
| **运行时 Agent** | `intentos/runtime/` | 节点 Daemon, 提供本地能力 | **守护进程** |
| **接口层** | `intentos/interface/` | CLI / API / Chat | **系统调用接口** |

### Map-Reduce 分布式执行

```
用户意图："分析全国 100 个城市的销售数据"
         ↓
┌─────────────────────────────────────────────────────────┐
│  接口层 (负载均衡)                                       │
│  • 将任务分发到多个节点                                  │
└───────────────┬─────────────────────────────────────────┘
                ↓
┌───────────────┼───────────────┬───────────────┐
│               │               │               │
▼               ▼               ▼               ▼
节点 1          节点 2          节点 3          节点 N
(Map)           (Map)           (Map)           (Map)
分析 25 城        分析 25 城        分析 25 城        分析 25 城
                │               │               │
                └───────────────┴───────────────┘
                                ↓
                        ┌───────────────┐
                        │  汇总节点      │
                        │  (Reduce)     │
                        │  LLM 汇总结果   │
                        └───────────────┘
                                ↓
                        返回给用户
```

### 分布式特性

- ✅ **语义 VM 跨节点** - 每个节点运行独立的语义 VM，跨网络组成整体 OS
- ✅ **运行时 Agent** - 在每个节点上提供本地能力，管理 Skill 缓存
- ✅ **Map-Reduce** - 分布式数据处理，支持大数据场景
- ✅ **结果汇总** - LLM 智能汇总各节点结果，生成最终回复
- ✅ **跨节点通信** - HTTP RPC 协议，节点间高效通信
- ✅ **负载均衡** - 接口层自动分发请求到不同节点

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

### 1. 语义 VM (Semantic VM) - OS 内核

IntentOS 的本质是一个语义虚拟机：
- **指令集**：语义指令 (CREATE/MODIFY/QUERY/LOOP/BRANCH...)
- **处理器**：LLM
- **机器码**：PEF (Prompt Executable File)
- **内存**：语义存储 (意图/能力/策略/Prompt/上下文)
- **图灵完备**：是 (支持循环 + 分支)

**核心洞察**:
- LLM 是处理器，不是外部工具
- PEF 是编译后的可执行文件，在存储中可自修改
- Self-Bootstrap 是语义 VM 的自然结果

### 2. 意图编译器

将自然语言编译为 PEF：
- **输入**：用户自然语言意图
- **输出**：PEF (Prompt Executable File)
- **编译过程**：解析意图 → 绑定能力 → 生成 Prompt
- **优化**：L1/L2/L3 三级缓存, Token 优化, 增量编译

### 3. 分布式内核

- **PCB (Process Control Block)**：追踪进程状态、PC 计数器
- **Fork/Exec**：分布式进程调度
- **一致性哈希内存**：跨节点语义存储
- **HTTP RPC**：节点间通信
- **Map-Reduce**：分布式数据处理

### 4. Self-Bootstrap

系统可以动态修改自身：
- **指令扩展**：向 LLM Processor 注入新的 `_handle_<opcode>` 方法
- **配置同步**：修改 CONFIG 时自动广播到集群
- **审计轨迹**：`/history` 指令可回溯所有内核自修改动作

---

## 📦 项目结构

```
IntentOS/
├── intentos/                # 主包
│   ├── core/                # 核心数据模型
│   ├── semantic_vm/         # ⭐ 语义 VM (OS 内核)
│   ├── compiler/            # ⭐ 意图编译器 (用户意图 → PEF)
│   ├── agent/               # 能力注册中心 (系统调用表)
│   ├── runtime/             # ⭐ 运行时 Agent (节点 Daemon)
│   ├── distributed/         # ⭐ 分布式内核
│   ├── bootstrap/           # ⭐ Self-Bootstrap
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
