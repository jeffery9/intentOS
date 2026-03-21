# IntentOS 分层架构

> **IntentOS 为核心 · PaaS 为服务**

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**状态**: Draft

---

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    用户 (User)                                  │
│  • 通过自然语言使用应用                                         │
│  • 按使用付费                                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │ 自然语言交互
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              PaaS 服务层 (PaaS Service Layer)                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  多租户管理 (Tenant Management)                          │   │
│  │  • 租户隔离 • 资源配置 • 配额管理                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  计费系统 (Billing System)                               │   │
│  │  • 用量计量 • 账单生成 • 支付网关 • 收益分成             │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  应用市场 (App Marketplace)                              │   │
│  │  • App 发布 • 审核 • 上架 • 评价                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  开发者工具 (Developer Tools)                            │   │
│  │  • SDK • CLI • 调试器 • 文档                             │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────────┘
                     │ IntentOS API
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              IntentOS 核心层 (IntentOS Core)                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  语义 VM (Semantic VM)                                   │   │
│  │  • LLM 作为处理器                                        │   │
│  │  • 语义指令作为"机器码"                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  意图编译器 (Intent Compiler)                            │   │
│  │  • 自然语言 → PEF (Prompt Executable File)              │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  能力注册中心 (Capability Registry)                      │   │
│  │  • 注册和管理能力 (Capabilities/Skills/MCP)             │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  执行引擎 (Execution Engine)                             │   │
│  │  • 执行 PEF • 调用能力 • 返回结果                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  记忆系统 (Memory System)                                │   │
│  │  • 短期记忆 • 长期记忆 • 知识图谱                        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、IntentOS 核心层

### 2.1 核心原则

**语言即系统 · Prompt 即可执行文件 · 语义 VM**

### 2.2 核心模块

| 模块 | 文件 | 功能 |
|------|------|------|
| **语义 VM** | `semantic_vm/` | LLM 作为处理器，执行语义指令 |
| **意图编译器** | `compiler/` | 自然语言 → PEF |
| **能力注册中心** | `registry/` | 注册和管理能力 |
| **执行引擎** | `engine/` | 执行 PEF |
| **记忆系统** | `memory/` | 短期/长期记忆 |
| **上下文管理** | `context.py` | 租户/用户上下文 |

### 2.3 IO 能力层

**IO 能力层** (`intentos/agent/`) 是语义 VM 内部的高层级组件，在**编译/链接 PEF 过程中**将 IO 能力注入到 prompt：

| IO 能力 | 模块 | 作用 |
|--------|------|------|
| **Shell 能力** | `agent.py` | 提供 shell 命令执行能力 |
| **MCP 集成** | `mcp_integration.py` | 提供 MCP 工具调用能力 |
| **Skills 集成** | `skill_integration.py` | 提供技能调用能力 |
| **能力注册** | `registry.py` | 注册和管理所有 IO 能力 |

**IO 能力的定位**：
- ✅ **属于 OS 内核** - 是语义 VM 的有机组成部分，不是外部工具
- ✅ **处于高层级** - 在语义 VM 内部，为 PEF 编译/链接提供 IO 能力
- ✅ **注入到 Prompt** - 在编译/链接时将 IO 能力注入到 prompt
- ✅ **LLM 驱动调用** - LLM 返回工具调用时触发 IO 能力执行

**IO 能力在 PEF 编译/链接中的作用**：
```
1. 用户意图 → 意图解析 → 任务规划
   ↓
2. 编译/链接 PEF
   ↓
3. 注入 IO 能力到 Prompt
   ↓
4. 生成完整的 PEF（包含 IO 能力定义）
```

**PEF 执行过程中的 IO 能力调用（Loop 机制）**：
```
1. 执行 PEF
   ↓
2. LLM 处理 Prompt（已包含 IO 能力）
   ↓
3. LLM 返回工具调用（包含 IO 能力调用）
   ↓
4. 检测到 IO 能力调用
   ↓
5. 调用 IO 能力获取数据
   ↓
6. 将 IO 结果返回给 LLM
   ↓
7. LLM 再次处理（可能需要再次调用工具）
   ↓
8. 重复步骤 3-7，直到不再需要工具调用 ← Loop
   ↓
9. LLM 生成最终结果
```

**编译/链接时 vs 执行时**：
- **编译/链接时**：注入 IO 能力到 Prompt → 生成 PEF
- **执行时**：LLM Loop 调用 IO 能力 → 获取数据 → 直到不再需要 Loop → 生成结果

### 2.4 核心 API

```python
from intentos import Agent, AgentContext

# 创建 Agent
agent = Agent()

# 创建上下文（包含租户/用户信息）
context = AgentContext(
    tenant_id="acme_corp",
    user_id="alice",
)

# 执行意图
result = await agent.execute(
    intent="分析华东区 Q3 销售数据",
    context=context
)

# 结果
print(result.message)      # 自然语言回复
print(result.data)         # 数据结果
print(result.usage)        # Token 使用
```

### 2.5 能力注册

```python
from intentos import register_capability

@register_capability(
    id="data_loader",
    name="数据加载",
    description="从文件/数据库加载数据",
    tags=["data", "io"],
)
def load_data(path: str, context: AgentContext) -> dict:
    """加载数据"""
    # 使用上下文中的租户资源
    db = context.tenant_config.get("database")
    # 加载数据
    ...
```

---

## 三、PaaS 服务层

### 3.1 PaaS 服务模块（已独立）

| 模块 | 文件 | 功能 |
|------|------|------|
| **多租户管理** | `paas/tenant.py` | 租户隔离、资源配置、配额管理 |
| **计费系统** | `paas/billing.py` | 用量计量、账单生成、支付、分成 |
| **应用市场** | `paas/marketplace.py` | App 发布、审核、上架、评价 |
| **开发者工具** | `paas/tools.py` | SDK、CLI、调试器 |

### 3.2 多租户管理

```python
from intentos.paas import TenantManager

manager = TenantManager()

# 创建租户
tenant = manager.create_tenant(
    tenant_id="acme_corp",
    name="ACME 公司",
    plan="pro",
    quota={
        "cpu_seconds": 36000,
        "tokens": 5000000,
    }
)

# 配置租户资源
manager.set_tenant_resources(
    tenant_id="acme_corp",
    resources={
        "database": "acme_db",
        "api_key": "acme_api_key",
    }
)
```

### 3.3 计费系统

```python
from intentos.paas import BillingEngine

billing = BillingEngine()

# 记录用量
billing.record_usage(
    tenant_id="acme_corp",
    user_id="alice",
    app_id="data_analyst",
    tokens=2500,
    execution_time=90,
)

# 生成账单
invoice = billing.generate_invoice(
    tenant_id="acme_corp",
    period="2026-03",
)

# 收益分成
shares = billing.calculate_revenue_share(
    total_revenue=1000,
    developer_id="dev_alice",
)
# 开发者：$800 (80%)
# 平台：$150 (15%)
# 推荐者：$50 (5%)
```

### 3.4 应用市场

```python
from intentos.paas import AppMarketplace

marketplace = AppMarketplace()

# 发布 App
app_id = marketplace.publish_app(
    developer_id="dev_alice",
    app_package={
        "name": "data_analyst",
        "description": "数据分析助手",
        "intents": [...],
        "capabilities": [...],
    },
)

# 审核 App
marketplace.review_app(
    app_id=app_id,
    approved=True,
)

# 查询 App
apps = marketplace.list_apps(category="analytics")
```

---

## 四、分层的好处

### 4.1 IntentOS 核心层

**特点**:
- 简洁、专注
- 聚焦语义 VM 核心
- 无业务逻辑
- 易于维护和扩展

**职责**:
- 提供语义 VM
- 编译和执行意图
- 管理能力和记忆

### 4.2 PaaS 服务层

**特点**:
- 丰富的业务功能
- 多租户、计费、市场
- 可独立演进
- 可定制和扩展

**职责**:
- 租户管理
- 计费和支付
- 应用市场
- 开发者工具

---

## 五、代码组织

```
intentos/
├── core/                    # 核心数据模型
├── semantic_vm/             # 语义 VM
├── compiler/                # 意图编译器
├── registry/                # 能力注册中心
├── engine/                  # 执行引擎
├── memory/                  # 记忆系统
├── context.py               # 上下文管理
│
├── paas/                    # PaaS 服务层
│   ├── tenant.py            # 多租户管理
│   ├── billing.py           # 计费系统
│   ├── marketplace.py       # 应用市场
│   └── tools.py             # 开发者工具
│
├── interface/               # 接口层
│   ├── shell.py             # Shell
│   └── api.py               # REST API
│
└── agent/                   # (废弃，逐步迁移)
    ├── tenant.py            # → paas/tenant.py
    ├── capability_binding.py# → 删除，功能并入 registry
    ├── app_generator.py     # → 删除，意图即应用
    ├── versioning.py        # → paas/marketplace.py
    ├── personalization.py   # → memory/
    ├── metering.py          # → paas/billing.py
    ├── wallet.py            # → paas/billing.py
    ├── marketplace.py       # → paas/marketplace.py
    └── submission.py        # → paas/marketplace.py
```

---

## 六、迁移计划

### 阶段 1: 创建 PaaS 层

- [ ] 创建 `paas/` 目录
- [ ] 迁移租户管理到 `paas/tenant.py`
- [ ] 迁移计费系统到 `paas/billing.py`
- [ ] 迁移应用市场到 `paas/marketplace.py`

### 阶段 2: 简化核心层

- [ ] 删除 `agent/capability_binding.py`
- [ ] 删除 `agent/app_generator.py`
- [ ] 简化 `agent/versioning.py` 为意图包版本
- [ ] 简化 `agent/personalization.py` 为记忆系统

### 阶段 3: 更新文档

- [ ] 更新架构文档
- [ ] 更新 API 文档
- [ ] 更新使用指南

---

## 七、总结

### 架构原则

1. **IntentOS 核心层** - 简洁、专注语义 VM
2. **PaaS 服务层** - 丰富、支持多租户和商业化
3. **清晰分层** - 核心层无业务逻辑，PaaS 层处理业务

### 核心理念

**IntentOS 核心层** 始终坚持：
- 语言即系统
- Prompt 即可执行文件
- 语义 VM

**PaaS 服务层** 提供：
- 多租户管理
- 计费和支付
- 应用市场
- 开发者工具

---

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**最后更新**: 2026-03-21  
**状态**: Draft
