# IntentOS 核心原则

> **语言即系统 · Prompt 即可执行文件 · 语义 VM**

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**状态**: **不可违背的核心原则**

---

## 一、核心原则

### 原则 1: 语言即系统 (Language is the System)

**含义**: 自然语言是操作系统的基本接口，不是"调用 API"，而是"用语言操作系统"。

**OS 层面实现**:
```
用户 → 自然语言 → 语义 VM → 执行结果
```

**不是**:
```
用户 → GUI/API → 系统调用 → 内核 → 硬件
```

**检查清单**:
- ✅ 用户是否用自然语言交互？
- ✅ 是否无需学习命令或 API？
- ✅ 系统是否理解用户意图？

### 原则 2: Prompt 即可执行文件 (Prompt is Executable)

**含义**: Prompt 是语义 VM 的"机器码"，是 IntentOS 中的.exe 文件。

**OS 层面实现**:
```
意图 → 语义编译 → PEF (Prompt Executable File) → LLM 执行
```

**传统 OS 对比**:
```
源代码 → 编译器 → 二进制 (.exe) → CPU 执行
```

**检查清单**:
- ✅ 意图是否编译为 PEF？
- ✅ PEF 是否可独立执行？
- ✅ PEF 是否包含完整的执行计划？

### 原则 3: 语义 VM (Semantic Virtual Machine)

**含义**: LLM 作为处理器，执行语义指令，不是"调用外部工具"。

**OS 层面实现**:
```
LLM → 理解意图 → 任务规划 → 能力绑定 → 执行
```

**传统 VM 对比**:
```
CPU → 取指 → 解码 → 执行 → 写回
```

**语义指令集**:
| 指令类型 | 指令 | 说明 |
|---------|------|------|
| 数据操作 | CREATE/MODIFY/DELETE/QUERY | 创建/修改/删除/查询 |
| 控制流 | IF/ELSE/LOOP/WHILE/JUMP | 条件/循环/跳转 |
| 能力调用 | CALL_CAPABILITY | 调用注册能力 |
| 记忆操作 | STORE/RETRIEVE | 存储/检索记忆 |

**检查清单**:
- ✅ LLM 是否作为处理器？
- ✅ 语义指令是否作为"机器码"？
- ✅ 是否有完整的执行周期？

---

## 二、OS 层面的设计约束

### 2.2 什么必须在 OS 层面

**必须遵循核心理念**:
- ✅ 语义 VM 实现
- ✅ 意图编译器
- ✅ 能力注册中心
- ✅ 执行引擎
- ✅ 记忆系统
- ✅ 上下文管理

**IO 能力层 (intentos/agent/)**:
- ✅ 属于 OS 内核（语义 VM 内部高层级）
- ✅ 在编译/链接 PEF 过程中注入 IO 能力
- ✅ 提供 Shell、MCP、Skills 等 IO 能力
- ✅ 通过能力注册中心提供统一接口

| IO 能力 | 模块 | 作用 |
|--------|------|------|
| **Shell 能力** | `agent.py` | 提供 shell 命令执行能力 |
| **MCP 集成** | `mcp_integration.py` | 提供 MCP 工具调用能力 |
| **Skills 集成** | `skill_integration.py` | 提供技能调用能力 |
| **能力注册** | `registry.py` | 注册和管理所有 IO 能力 |

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

**必须在 OS 层面实现的功能**:
```python
# OS 层 API
from intentos import Agent, AgentContext

agent = Agent()
context = AgentContext(tenant_id="acme", user_id="alice")

# 编译/链接时，IO 能力获取上下文
result = await agent.execute(intent="分析数据", context=context)
```

### 2.2 什么不应该在 OS 层面

**不应该在 OS 层面的功能**:
- ❌ 复杂的多租户管理系统
- ❌ 计费系统和支付网关
- ❌ 应用市场和审核流程
- ❌ 复杂的版本管理
- ❌ 用户偏好管理

**这些功能应该在哪里**:
- ✅ PaaS 服务层 (intentos/paas/)
- ✅ 使用 OS 层 API 构建
- ❌ 不应该污染 OS 层核心

---

## 三、设计决策检查

### 3.1 检查问题

在设计任何功能时，问自己：

1. **是否符合"语言即系统"**?
   - 用户是否用自然语言交互？
   - 是否需要学习界面或 API？
   - 系统是否理解用户意图？

2. **是否符合"Prompt 即可执行文件"**?
   - 意图是否编译为 PEF？
   - PEF 是否可独立执行？
   - PEF 是否包含完整的执行计划？

3. **是否符合"语义 VM"**?
   - LLM 是否作为处理器？
   - 语义指令是否作为"机器码"？
   - 是否有完整的执行周期？

### 3.2 反模式

**违反核心理念的设计**:

| 反模式 | 问题 | 正确做法 |
|--------|------|---------|
| **GUI 优先** | 用户需要学习界面 | 自然语言优先 |
| **API 调用** | 用户需要学习 API | 意图编译 |
| **外部工具** | LLM 调用外部工具 | LLM 作为处理器 |
| **复杂租户** | OS 层管理租户 | PaaS 层管理 |
| **复杂计费** | OS 层计费 | PaaS 层计费 |

---

## 四、代码组织

### 4.1 OS 层代码组织

```
intentos/
├── semantic_vm/         # 语义 VM (LLM 作为处理器)
│   ├── processor.py     # 语义处理器
│   └── instructions.py  # 语义指令集
│
├── compiler/            # 意图编译器 (NLP → PEF)
│   ├── parser.py        # 意图解析
│   ├── planner.py       # 任务规划
│   └── codegen.py       # PEF 生成
│
├── registry/            # 能力注册中心
│   ├── registry.py      # 能力注册
│   └── capabilities.py  # 能力定义
│
├── engine/              # 执行引擎
│   ├── executor.py      # PEF 执行
│   └── monitor.py       # 执行监控
│
├── memory/              # 记忆系统
│   ├── short_term.py    # 短期记忆
│   └── long_term.py     # 长期记忆
│
└── context.py           # 上下文管理
    ├── tenant_context   # 租户上下文
    └── user_context     # 用户上下文
```

### 4.2 PaaS 层代码组织

```
intentos/paas/
├── tenant.py            # 多租户管理 (使用 OS 层 context)
├── billing.py           # 计费系统 (使用 OS 层 usage)
├── marketplace.py       # 应用市场 (使用 OS 层 registry)
└── tools.py            # 开发者工具 (使用 OS 层 API)
```

---

## 五、API 设计

### 5.1 OS 层 API

```python
# 核心 API - 必须简单、专注
from intentos import Agent, AgentContext, register_capability

# 创建 Agent
agent = Agent()

# 创建上下文
context = AgentContext(
    tenant_id="acme_corp",
    user_id="alice",
)

# 执行意图
result = await agent.execute(
    intent="分析华东区 Q3 销售数据",
    context=context
)

# 注册能力
@register_capability(
    id="data_loader",
    name="数据加载",
    description="从文件/数据库加载数据",
)
def load_data(path: str, context: AgentContext) -> dict:
    # 使用上下文中的信息
    db = context.tenant_config.get("database")
    # 加载数据
    ...
```

### 5.2 PaaS 层 API

```python
# PaaS API - 使用 OS 层 API 构建
from intentos import Agent, AgentContext
from intentos.paas import TenantManager, BillingEngine

# PaaS 层使用 OS 层
class PaaSService:
    def __init__(self):
        self.agent = Agent()  # 使用 OS 层 Agent
        self.tenant_manager = TenantManager()
        self.billing = BillingEngine()
    
    async def execute_with_billing(self, tenant_id, user_id, intent):
        # 获取租户上下文
        context = self.tenant_manager.get_context(tenant_id, user_id)
        
        # 执行意图 (OS 层)
        result = await self.agent.execute(intent, context)
        
        # 记录用量并计费 (PaaS 层)
        self.billing.record_usage(
            tenant_id=tenant_id,
            tokens=result.usage.total_tokens,
        )
        
        return result
```

---

## 六、总结

### 核心原则

**OS 层面必须遵循**:
- ✅ 语言即系统
- ✅ Prompt 即可执行文件
- ✅ 语义 VM

**PaaS 层面可以扩展**:
- ✅ 多租户管理
- ✅ 计费系统
- ✅ 应用市场
- ✅ 开发者工具

### 设计约束

**OS 层**:
- 简洁、专注
- 聚焦语义 VM 核心
- 无业务逻辑
- 遵循核心理念

**PaaS 层**:
- 丰富的业务功能
- 使用 OS 层 API 构建
- 可独立演进
- 可扩展和定制

### 检查清单

在提交任何代码前，问自己：

1. **这个功能是否在正确的层次**?
   - OS 层：语义 VM、意图编译、能力注册、执行引擎、记忆系统
   - PaaS 层：多租户、计费、市场、开发者工具

2. **是否符合核心理念**?
   - 语言即系统
   - Prompt 即可执行文件
   - 语义 VM

3. **是否简单、专注**?
   - 删除不必要的抽象
   - 回归本质
   - 语义优先

---

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**状态**: **不可违背的核心原则**
