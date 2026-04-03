# AGENTS.md - IntentOS 分布式 OS 开发指南

> **语言即系统 · Prompt 即可执行文件 · 分布式语义 VM**

本文档面向 **OS 开发者** —— 为 IntentOS 内核、语义 VM 和运行时 Agent 开发能力模块。

---

## IntentOS 是什么

IntentOS 是一个 **分布式 AI 原生操作系统**, 不是传统的 AI Agent 框架。

### 核心区别

| 传统 AI Agent 框架 | IntentOS |
|-------------------|----------|
| 单节点应用层智能代理 | **分布式操作系统内核** |
| Tool Calling + LLM Loop | **语义 VM + PEF** (Prompt Executable File) |
| Prompt Engineering | **意图编译 → 语义执行** |
| 会话级上下文 | **全局语义地址空间** (跨节点) |

### 核心抽象

1. **语言即系统**: 自然语言是 OS 的指令集
2. **Prompt 即可执行文件**: PEF 是语义 VM 的机器码
3. **语义 VM**: LLM 是处理器, 跨网络组成整体 OS

### 你在这里做什么

作为 OS 开发者, 你将:
- ✅ 为语义 VM 开发能力模块 (类似 Linux 系统调用)
- ✅ 扩展意图编译器的指令集
- ✅ 开发分布式运行时 Agent (节点 Daemon)
- ✅ 实现跨节点通信协议

❌ 你不是在开发应用层 AI Agent

---

## 目录

- [IntentOS 是什么](#intentos-是什么)
- [快速开始](#快速开始)
- [OS 架构概览](#os-架构概览)
- [OS 扩展开发指南](#os-扩展开发指南)
- [开发规范与最佳实践](#开发规范与最佳实践)

---

## 快速开始

### 1. 启动 IntentOS

```bash
# 启动内核（必须先执行）
intentos daemon

# 或启动内核 + API 网关
intentos daemon --api
```

### 2. 使用 CLI 与 Agent 交互

```bash
# 启动 CLI（如果内核未运行会自动启动）
intentos cli
```

在 CLI 中：
- 直接输入自然语言执行意图
- 使用 `/help` 查看命令
- 使用 `/status` 查看状态
- 使用 `/quit` 退出

### 3. 使用 API（如果启动了 `--api`）

```bash
curl -X POST http://localhost:8080/v1/execute \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer intentos-secret-token" \
     -d '{"intent": "分析销售数据"}'
```

---

## OS 架构概览

### 分布式 OS 分层架构

```
┌─────────────────────────────────────────────────────────┐
│  IntentOS 分布式 OS 架构                                │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │  接口层 (Interface)                                │ │
│  │  • CLI / REST API / Chat (访问入口)               │ │
│  └──────────────────────┬────────────────────────────┘ │
│                         │ 用户意图                     │
│  ┌──────────────────────▼────────────────────────────┐ │
│  │  语义 VM 层 (Kernel)                               │ │
│  │  • 意图编译器 → PEF (Prompt Executable File)      │ │
│  │  • LLM 执行器 (语义处理器)                        │ │
│  │  • 能力注册中心 (系统调用表)                      │ │
│  └──────────────────────┬────────────────────────────┘ │
│                         │ 调用能力                     │
│  ┌──────────────────────▼────────────────────────────┐ │
│  │  运行时 Agent 层 (Runtime Daemon)                  │ │
│  │  • 节点本地能力 (Shell/FS/Network)                │ │
│  │  • Skill/App 缓存管理                             │ │
│  │  • 跨节点通信 (Map-Reduce)                        │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 核心组件

| 组件 | 位置 | 职责 | OS 视角 |
|------|------|------|---------|
| **语义 VM** | `intentos/semantic_vm/` | 执行 PEF, LLM 作为处理器 | **OS 内核** |
| **意图编译器** | `intentos/compiler/` | 用户意图 → PEF | **编译器** |
| **能力注册中心** | `intentos/agent/registry.py` | 管理系统调用能力 | **系统调用表** |
| **运行时 Agent** | `intentos/runtime/` | 节点 Daemon, 提供本地能力 | **守护进程** |
| **接口层** | `intentos/interface/` | CLI / API / Chat | **系统调用接口** |

### 执行流程

```
1. 用户输入自然语言意图
   ↓
2. 意图编译器编译为 PEF (Prompt Executable File)
   ↓
3. 语义 VM 加载 PEF
   ↓
4. LLM 作为处理器执行语义指令
   ↓
5. 需要 IO 时 → 查询能力注册中心 → 调用运行时 Agent 提供的能力
   ↓
6. 结果返回给用户
```

### 分布式执行

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   节点 1      │      │   节点 2      │      │   节点 3      │
│  (主节点)     │      │  (工作节点)   │      │  (工作节点)   │
│              │      │              │      │              │
│  语义 VM     │      │  语义 VM     │      │  语义 VM     │
│  编译器      │─────▶│  执行 PEF    │      │  执行 PEF    │
│              │      │              │      │              │
│  运行时 Agent│      │  运行时 Agent│      │  运行时 Agent│
│  - 本地能力  │      │  - 本地能力  │      │  - 本地能力  │
│  - Skill缓存 │      │  - Skill缓存 │      │  - Skill缓存 │
└──────────────┘      └──────────────┘      └──────────────┘

跨节点通信: Map-Reduce 模式执行分布式任务
```

---

## OS 扩展开发指南

### 1. 为语义 VM 注册能力

能力 (Capability) 是语义 VM 的**系统调用**。你需要在能力注册中心注册新的能力, 供意图编译器在编译 PEF 时使用。

```python
from intentos.agent.registry import CapabilityRegistry
from intentos.agent.capability import Capability

# 获取全局能力注册中心 (单例)
registry = CapabilityRegistry()

# 定义能力处理函数
def query_sales(region: str, period: str) -> dict:
    """查询销售数据 (OS 级能力)"""
    return {
        "region": region,
        "period": period,
        "data": [...]  # 销售数据
    }

# 注册能力 (类似注册系统调用)
registry.register(
    id="query_sales",
    name="查询销售数据",
    description="查询指定区域和时间的销售数据",
    handler=query_sales,
    input_schema={
        "region": {"type": "string", "description": "区域名称"},
        "period": {"type": "string", "description": "时间周期"}
    },
    output_schema={
        "region": "string",
        "period": "string",
        "data": "array"
    },
    required_permissions=["data:read"],  # 所需权限
    source="builtin",  # builtin / mcp / skill
)
```

**关键理解**:
- 能力注册后, 意图编译器会在编译 PEF 时将能力描述注入到 Prompt
- LLM 执行时会根据能力描述决定何时调用
- 能力调用受 Capability Gate (能力门控) 保护

---

### 2. 使用意图编译器

意图编译器将**用户自然语言意图**编译为**语义 VM 可执行的 PEF**。

```python
from intentos.compiler import IntentCompiler

# 创建编译器 (自动加载已注册的能力)
compiler = IntentCompiler(registry=registry)

# 编译用户意图为 PEF
pef = compiler.compile("分析华东区 Q3 销售数据")

print(pef.system_prompt)  # 包含能力描述的 system prompt
print(pef.user_prompt)    # 包含任务描述的用户 prompt
```

**PEF (Prompt Executable File)**:
- PEF 是语义 VM 的机器码
- 包含 system prompt + user prompt + 元数据
- 可缓存、可分发、可跨节点执行

---

### 3. 使用语义 VM 执行 PEF

```python
from intentos.semantic_vm import SemanticVM
from intentos.agent import AgentContext

# 创建语义 VM
vm = SemanticVM()

# 创建执行上下文
context = AgentContext(
    user_id="demo",
    permissions=["data:read", "data:analyze"]
)

# 执行 PEF
result = await vm.execute(pef, context)

print(result.message)  # 自然语言回复
print(result.data)     # 数据结果
```

**执行流程**:
```
PEF → 语义 VM → LLM 处理 Prompt
         ↓
    需要调用能力?
         ↓
    查询能力注册中心 → Capability Gate 权限检查
         ↓
    执行能力 handler → 返回结果
         ↓
    LLM 生成最终结果
```

---

### 4. 开发分布式运行时 Agent

运行时 Agent 是**节点 Daemon**, 为本地语义 VM 提供能力并管理跨节点通信。

```python
from intentos.runtime import RuntimeAgent

# 创建运行时 Agent (节点 Daemon)
runtime_agent = RuntimeAgent(
    node_id="node1",
    cluster_nodes=["node2", "node3"],  # 集群节点
)

# 启动节点
await runtime_agent.start()

# 分布式执行 (Map-Reduce)
data_partitions = {
    "node2": {"region": "华东", "period": "Q3"},
    "node3": {"region": "华南", "period": "Q3"},
}

results = await runtime_agent.map_reduce(pef, data_partitions)
# results = {
#     "node2": {"region": "华东", "sales": "$5M"},
#     "node3": {"region": "华南", "sales": "$3M"},
# }

# 汇总结果
summary = await runtime_agent.reduce_results(list(results.values()))
```

**运行时 Agent 职责**:
- 提供节点本地能力 (Shell/FileSystem/Network)
- 管理 Skill/App 缓存
- 跨节点通信 (Map-Reduce 执行模型)
- 结果汇总 (使用 LLM)

---

## 开发规范与最佳实践

### 1. 能力设计规范

能力是语义 VM 的系统调用, 必须遵循严格的设计规范。

```python
# ✅ 好的做法: 明确定义输入输出和权限
def query_sales(region: str, period: str) -> dict:
    """查询销售数据 (OS 级能力)

    Args:
        region: 区域名称（如：华东、华北）
        period: 时间周期（如：Q3、2024-Q1）

    Returns:
        包含销售数据的字典

    Required Permissions:
        - data:read
    """
    # 实现...
    return {"data": [...], "count": 100}

# ❌ 不好的做法: 参数和返回值不明确
def query_sales(**kwargs):  # 参数不明确
    # 实现...
    return [...]  # 返回格式不明确
```

**关键原则**:
- **单一职责**: 每个能力只完成一个任务
- **参数明确**: 清晰定义输入参数和输出结果 (使用 Schema)
- **权限最小化**: 只声明必需的权限
- **安全标注**: 标注是否只读/并发安全/破坏性

---

### 2. 权限声明规范

能力必须声明所需权限, Capability Gate 会在执行前检查。

```python
from intentos.agent.registry import CapabilityRegistry

registry = CapabilityRegistry()

# 声明权限
registry.register(
    id="write_file",
    name="写入文件",
    description="写入文件内容",
    handler=write_file_handler,
    required_permissions=["file:write"],  # 文件写入权限
    input_schema={
        "path": {"type": "string", "description": "文件路径"},
        "content": {"type": "string", "description": "文件内容"}
    },
)

# 执行时自动检查权限
context = AgentContext(
    user_id="demo",
    permissions=["file:read"]  # 只有读权限
)

# ❌ 这将抛出 PermissionError
await registry.execute_capability("write_file", context, path="/tmp/test.txt", content="hello")
```

---

### 3. 错误处理

OS 级错误处理必须清晰、可追溯、不泄露敏感信息。

```python
from intentos.agent.errors import CapabilityError, PermissionError

try:
    result = await registry.execute_capability("query_sales", context, region="华东", period="Q3")
except PermissionError as e:
    # 权限不足
    print(f"权限不足：{e}")
except CapabilityError as e:
    # 能力执行失败
    print(f"能力执行失败：{e.code} - {e.message}")
except Exception as e:
    # 未知错误 (不泄露内部细节)
    print(f"执行失败，请联系管理员")
```

---

### 4. 日志记录

OS 组件日志必须结构化, 便于调试和审计。

```python
import logging

logger = logging.getLogger("intentos.os")

logger.info("能力注册完成", extra={"capability_count": 10})
logger.debug(f"编译 PEF: intent=analyze_sales")
logger.error(f"能力执行失败", extra={
    "capability_id": "query_sales",
    "error": str(e),
    "user_id": context.user_id
})
```

---

### 5. 分布式开发注意事项

**跨节点通信**:
- 使用 `RuntimeAgent.map_reduce()` 执行分布式任务
- 结果汇总使用 LLM (语义 VM)
- 节点间数据序列化使用 JSON

**Skill/App 缓存**:
- 运行时 Agent 管理缓存生命周期
- 优先检查缓存, 未命中再下载
- 缓存键格式: `{app_id}:{version}`

**安全边界**:
- 节点间通信必须加密 (TLS)
- 敏感数据不跨节点传输
- Capability Gate 在每个节点独立执行

---

## 调试与测试

### 1. 查看内核状态

```bash
# CLI 中
intentos cli
> /status

# 或命令行
intentos cli status
```

### 2. 健康检查

```bash
curl http://localhost:8080/v1/health \
     -H "Authorization: Bearer intentos-secret-token"
```

### 3. 查看日志

```bash
# 查看 daemon 日志（如果后台运行）
tail -f /tmp/intentos.log
```

---

## 常见问题

### Q: 如何停止 IntentOS？

```bash
# 在 CLI 中
> /quit

# 或终止 daemon 进程
pkill -f "python -m intentos daemon"
```

### Q: Socket 文件在哪里？

默认在 `/tmp/intentos.sock`

### Q: 如何修改 API Token？

```bash
export INTENTOS_API_TOKEN=your-token
intentos daemon --api
```

### Q: CLI 无法连接内核？

1. 检查内核是否运行：`intentos cli status`
2. 检查 Socket 文件：`ls -la /tmp/intentos.sock`
3. 手动启动内核：`intentos daemon`

---

## 参考文档

- [架构文档](./docs/ARCHITECTURE.md) - 完整架构说明
- [核心原则](./docs/CORE_PRINCIPLES.md) - 设计原则
- [AI Native App](./docs/AI_NATIVE_APP.md) - AI 原生应用开发
- [ROADMAP.md](./ROADMAP.md) - 项目路线图

---

**最后更新**: 2026-03-31  
**版本**: v16.0.0 (统一 CLI)
