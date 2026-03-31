# AGENTS.md - IntentOS AI 代理开发指南

> **语言即系统 · Prompt 即可执行文件 · 语义 VM**

本文档描述如何在 IntentOS 中开发和运行 AI 代理（Agent）。

---

## 目录

- [快速开始](#快速开始)
- [架构概述](#架构概述)
- [开发指南](#开发指南)
- [最佳实践](#最佳实践)

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

## 架构概述

### 核心组件

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

### 组件说明

| 组件 | 位置 | 职责 |
|------|------|------|
| **Daemon** | `intentos/interface/daemon.py` | 运行内核，提供 RPC 和 API 服务 |
| **RPC Server** | `intentos/interface/ipc.py` | Unix Socket 通信，处理客户端请求 |
| **API Gateway** | `intentos/interface/api.py` | HTTP API 网关（可选） |
| **CLI** | `intentos/cli/cli.py` | 统一交互界面（Shell + Chat） |

---

## 开发指南

### 1. 创建自定义 Agent

Agent 是基于 LLM 的智能代理，理解意图、规划任务、调用工具。

```python
from intentos.agent import Agent, AgentContext

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

### 2. 注册自定义能力

```python
from intentos.core import Capability
from intentos.registry import IntentRegistry

registry = IntentRegistry()

# 定义能力
def query_sales(region: str, period: str) -> dict:
    """查询销售数据"""
    return {
        "region": region,
        "period": period,
        "data": [...]  # 销售数据
    }

# 注册能力
capability = Capability(
    name="query_sales",
    description="查询指定区域和时间的销售数据",
    input_schema={
        "region": "string",
        "period": "string"
    },
    output_schema={
        "region": "string",
        "period": "string",
        "data": "array"
    },
    func=query_sales,
    tags=["sales", "query"]
)

registry.register_capability(capability)
```

### 3. 创建意图模板

```python
from intentos.core import IntentTemplate, IntentType, IntentStep

# 定义意图模板
template = IntentTemplate(
    name="analyze_sales",
    description="分析销售数据",
    intent_type=IntentType.COMPOSITE,
    params_schema={
        "region": "string",
        "period": "string"
    },
    steps=[
        IntentStep(
            capability_name="query_sales",
            params={"region": "{{region}}", "period": "{{period}}"},
            output_var="sales_data"
        ),
        IntentStep(
            capability_name="analyze_data",
            params={"data": "${sales_data}"},
            output_var="analysis_result"
        )
    ],
    tags=["sales", "analysis"]
)

registry.register_template(template)
```

### 4. 使用语义 VM

```python
from intentos.semantic_vm import SemanticVM, create_semantic_vm

# 创建语义 VM
vm = create_semantic_vm(llm_executor)

# 加载程序
await vm.load_program(program)

# 执行程序
result = await vm.execute_program("my_program")
```

---

## 最佳实践

### 1. 意图设计原则

- **单一职责**：每个意图模板只完成一个任务
- **参数明确**：清晰定义输入参数和输出结果
- **可组合**：使用复合意图组合多个原子意图
- **错误处理**：提供清晰的错误信息

### 2. 能力开发规范

```python
# ✅ 好的做法
def query_sales(region: str, period: str) -> dict:
    """查询销售数据
    
    Args:
        region: 区域名称（如：华东、华北）
        period: 时间周期（如：Q3、2024-Q1）
    
    Returns:
        包含销售数据的字典
    """
    # 实现...
    return {"data": [...], "count": 100}

# ❌ 不好的做法
def query_sales(**kwargs):  # 参数不明确
    # 实现...
    return [...]  # 返回格式不明确
```

### 3. 错误处理

```python
from intentos.agent.errors import AgentError

try:
    result = await agent.execute("分析销售数据", context)
except AgentError as e:
    print(f"Agent 执行失败：{e.code} - {e.message}")
```

### 4. 日志记录

```python
import logging

logger = logging.getLogger("intentos.agent")

logger.info("Agent 初始化完成")
logger.debug(f"执行意图：{intent.name}")
logger.error(f"执行失败：{error}")
```

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
