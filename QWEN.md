# IntentOS - AI 原生操作系统

> **语言即系统 · Prompt 即可执行文件 · 语义 VM**

**文档版本**: 2.0  
**创建日期**: 2026-03-12  
**最后更新**: 2026-03-21  
**状态**: Release Candidate

---

## 项目概述

IntentOS 是一个 **AI 原生操作系统** 原型，核心是**语义虚拟机 (Semantic VM)**——将自然语言意图编译为 LLM 可执行的 Prompt，支持 Self-Bootstrap 和分布式部署。

### 核心理念

- **语义 VM**: LLM 作为处理器，语义指令作为"机器码"
- **分布式**: 多节点集群，语义 VM 跨网络组成整体 OS
- **运行时 Agent**: 在每个节点上提供本地能力，管理 Skill 缓存
- **接口层**: 对外提供 REST API 和 Chat 访问接口
- **PaaS 服务层**: 多租户、计费、应用市场（独立于 OS 核心层）

### 快速导航

| 文档 | 说明 |
|------|------|
| [架构文档](./docs/ARCHITECTURE.md) | ⭐ **完整架构说明**：分布式语义 VM、运行时 Agent、PaaS 层 |
| [核心原则](./docs/CORE_PRINCIPLES.md) | 语言即系统 · Prompt 即可执行文件 · 语义 VM |
| [AI Native App](./docs/AI_NATIVE_APP.md) | AI Native App 概念、开发指南 |
| [ROADMAP.md](./ROADMAP.md) | 项目路线图 |

---

## 快速开始

### 1. 安装

```bash
# 基础安装
pip install -e .

# 启动 Shell
PYTHONPATH=. python intentos/interface/shell.py

# 启动 API 服务器
PYTHONPATH=. python intentos/interface/api.py
```

### 2. 使用示例

```python
from intentos import Agent, AgentContext

# 创建 Agent
agent = Agent()
await agent.initialize()

# 创建上下文
context = AgentContext(user_id="demo")

# 执行意图
result = await agent.execute("分析华东区 Q3 销售数据", context)

print(result.message)  # 自然语言回复
print(result.data)     # 数据结果
```

### 3. 分布式部署

```python
from intentos.runtime import RuntimeAgent

# 创建运行时 Agent
runtime_agent = RuntimeAgent(
    node_id="node1",
    cluster_nodes=["node2", "node3"],
)

# 启动节点
await runtime_agent.start()

# 分布式执行
pef = compiler.compile("分析销售数据")
result = await runtime_agent.map_reduce(pef, data_partitions)
```

---

## 项目结构

```
IntentOS/
├── intentos/
│   ├── agent/           # AI Agent（智能代理，基于 LLM）
│   ├── runtime/         # 运行时 Agent（分布式节点代理）
│   ├── semantic_vm/     # 语义 VM（在每个节点上运行）
│   ├── interface/       # 接口层（REST API + Chat）
│   ├── paas/            # PaaS 服务层（多租户、计费、市场）
│
├── docs/                # 文档
│   ├── ARCHITECTURE.md  # ⭐ 完整架构说明
│   ├── CORE_PRINCIPLES.md
│   ├── AI_NATIVE_APP.md
│   └── ...
│
├── examples/            # 示例代码
├── tests/               # 测试用例
├── README.md            # 项目说明
├── ROADMAP.md           # 项目路线图
└── QWEN.md              # 本文件（项目概括）
```

---

## 核心概念（简要）

### 语义 VM
- **LLM 作为处理器**，执行语义指令
- **PEF (Prompt Executable File)** 是语义 VM 的"机器码"
- 在每个节点上运行，跨网络组成整体 OS

### AI Agent
- **基于 LLM**，理解意图、规划任务、调用工具
- 在语义 VM 内部，是语义执行的一部分

### 运行时 Agent
- **分布式节点代理**，在每个节点上运行
- 提供本地能力（shell、文件系统）
- 管理 Skill 缓存
- 分布式运行（Map-Reduce）、结果汇总

### 接口层
- **对外提供 REST API 和 Chat 访问接口**
- REST API: POST /v1/execute, GET /v1/status, GET /v1/nodes
- Chat Interface: Shell TUI, WebSocket, Web UI

### PaaS 服务层
- **独立于 OS 核心层**，处理业务逻辑
- 多租户管理、计费系统、应用市场、开发者工具

---

## 参考文档

完整架构说明请参考：[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)

其他文档：
- [核心原则](./docs/CORE_PRINCIPLES.md)
- [AI Native App](./docs/AI_NATIVE_APP.md)
- [分层架构](./docs/LAYERED_ARCHITECTURE.md)
- [计费与收益](./docs/BILLING_AND_REVENUE.md)
- [意图包格式规范](./docs/INTENT_PACKAGE_SPEC.md)
- [安全与权限](./docs/SECURITY_AND_PERMISSIONS.md)
- [性能优化策略](./docs/PERFORMANCE_OPTIMIZATION.md)
- [测试与调试指南](./docs/TESTING_AND_DEBUGGING.md)

---

**QWEN.md 说明**: 本文档是项目概括，帮助快速了解 IntentOS。完整架构说明请参考 [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)。
