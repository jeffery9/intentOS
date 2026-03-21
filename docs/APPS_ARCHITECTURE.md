# IntentOS 应用层架构与 AI Agent 实现指南

## 概述

在 IntentOS 的架构体系中，**应用层（Apps Layer）** 位于三层调用架构的最顶部，是开发者构建具体功能和用户直接交互的场所。

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Application Layer (应用层)                         │
│  • 领域意图包                                                │
│  • 用户交互                                                  │
│  • 结果呈现                                                  │
└───────────────┬─────────────────────────────────────────────┘
                ↓ 调用意图
┌───────────────▼─────────────────────────────────────────────┐
│  Layer 2: IntentOS Layer (意图层 - 7 Level 处理流程)          │
│  [L1] 意图解析 → [L2] 任务规划 → [L3] 上下文收集 →           │
│  [L4] 安全验证 → [L5] 能力绑定 → [L6] 执行 → [L7] 改进       │
└───────────────┬─────────────────────────────────────────────┘
                ↓ Prompt 执行 (Semantic Opcode)
┌───────────────▼─────────────────────────────────────────────┐
│  Layer 3: Model Layer (模型层 - LLM Processor)               │
│  • 语义 CPU (LLM)                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 一、Apps 层（应用层）的职责

应用层是**面向用户的意图入口**，其核心职责是实现从业务逻辑到系统能力的映射。具体职责包括：

### 1. 封装领域意图包 (Domain Intent Packages)

应用层负责定义和封装特定业务领域的**意图模板（Intent Templates）**和**能力（Capabilities）**。意图包是 AI 原生应用的核心载体，包含了将自然语言转化为结构化逻辑的代码和描述。

**意图包结构**:
```
intent-package/
├── SKILL.md              # 意图包元数据和规范
├── intents/              # 意图模板定义
│   ├── schedule.yaml
│   └── email.yaml
├── capabilities/         # 能力定义
│   ├── api_client.py
│   └── llm_tool.py
└── resources/            # 资源文件
    ├── prompts/
    └── templates/
```

### 2. 提供用户交互接口

通过多模态交互界面（如对话、图表、表单、交互式 Shell 或 REST API）接收人类的自然语言意图。在 AI 原生范式下，用户不再通过点击按钮，而是通过"表达目标"来驱动系统。

**交互方式**:
```python
# 1. 交互式 Shell
from intentos.interface import IntentShell
shell = IntentShell()
await shell.run()

# 2. REST API
POST /v1/execute
{
    "intent": "分析华东区销售数据",
    "context": {"user_id": "user123"}
}

# 3. Python SDK (新方式)
from intentos.agent import AIAgent
agent = AIAgent()
await agent.initialize()
result = await agent.execute("分析销售数据", context)
```

### 3. 结果呈现与渲染

将系统执行后的结果（如数据视图、artifacts）渲染为用户友好的形式。界面在这一层不再是固定的容器，而是可随语言意图即时派生和重建的"表达层"。

**渲染示例**:
```python
# 数据可视化
if result.data.get('chart'):
    render_chart(result.data['chart'])

# 文本摘要
if result.data.get('summary'):
    display_summary(result.data['summary'])

# 可执行 Artifact
if result.artifacts:
    for artifact in result.artifacts:
        yield artifact
```

### 4. 管理高维抽象层

管理用户目标的语义解析、能力图谱的映射、动态上下文（Context）的建模以及执行结构（Executable Structure）的生成。

**上下文管理**:
```python
from intentos.agent import AgentContext

context = AgentContext(
    user_id="user123",
    session_id="session_abc",
    conversation_history=[...],  # 对话历史
    variables={...},  # 变量
)
```

---

## 二、新一代 AI Agent 实现 (v10.0+)

在 IntentOS v10.0 中，AI Agent 采用全新的实现方式，基于**能力注册**、**意图编译**和**执行器**模式，并原生支持 **MCP (Model Context Protocol)** 和 **Claude Skills** 规范。

### 1. 核心架构

```
┌─────────────────────────────────────────────────────────────┐
│  AIAgent                                                    │
├─────────────────────────────────────────────────────────────┤
│  • CapabilityRegistry (能力注册中心)                        │
│    ├─ Builtin Capabilities (内置能力)                       │
│    ├─ MCP Tools (MCP 工具)                                  │
│    └─ Skills (Claude Skills)                                │
│                                                             │
│  • IntentCompiler (意图编译器)                              │
│    └─ PEF (Prompt Executable File)                          │
│                                                             │
│  • AgentExecutor (执行器)                                   │
│    └─ 匹配 → 参数提取 → 执行                                │
└─────────────────────────────────────────────────────────────┘
```

### 2. 核心组件

#### CapabilityRegistry (能力注册中心)

管理所有可用的能力，包括：
- **内置能力**: Shell 命令、文件操作、计算器、时间等
- **MCP Tools**: 通过 MCP 协议连接的外部工具
- **Skills**: 基于 Claude Skills 规范的技能

```python
from intentos.agent import CapabilityRegistry

registry = CapabilityRegistry()

# 注册能力
registry.register(
    id="shell",
    name="Shell 命令",
    description="执行 Shell 命令",
    handler=shell_execute,
    tags=["system", "shell"],
    source="builtin",  # 或 "mcp", "skill"
)

# 执行能力
result = await registry.execute_capability("shell", command="ls -la")
```

#### IntentCompiler (意图编译器)

将自然语言意图编译为 **PEF (Prompt Executable File)**：

```python
from intentos.agent import IntentCompiler

compiler = IntentCompiler()

# 编译意图
pef = compiler.compile(
    intent="执行 ls -la 命令",
    capabilities=["Shell 命令", "计算器", "当前时间"],
    context={"user_id": "user123"},
)

# PEF 输出
{
    "version": "1.0",
    "id": "pef_20260315220000",
    "intent": "执行 ls -la 命令",
    "system_prompt": "...",
    "user_prompt": "请执行：执行 ls -la 命令",
    "capabilities": ["Shell 命令", "计算器", "当前时间"],
}
```

#### AgentExecutor (执行器)

执行编译后的 PEF：

```python
from intentos.agent import AgentExecutor

executor = AgentExecutor(registry)

# 执行 PEF
result = await executor.execute(pef, context)
```

### 3. 实现步骤

#### 步骤 1: 创建 Agent

```python
from intentos.agent import AIAgent, AgentConfig, AgentContext

# 配置 Agent
config = AgentConfig(
    name="My Agent",
    enable_mcp=True,      # 启用 MCP
    enable_skills=True,   # 启用 Skills
)

# 创建 Agent
agent = AIAgent(config)
await agent.initialize()
```

#### 步骤 2: 连接 MCP 服务器 (可选)

```python
# 连接天气 MCP 服务器
await agent.connect_mcp(
    name="weather",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-weather"],
)

# 连接文件系统 MCP 服务器
await agent.connect_mcp(
    name="filesystem",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/Users/jeffery"],
)
```

#### 步骤 3: 加载 Skills (自动)

Skills 会自动从 `~/.claude/skills/` 加载：

```python
# 查看已加载的 Skills
skills = agent.get_loaded_skills()
print(f"已加载 {len(skills)} 个 Skills:")
for skill in skills:
    print(f"  • {skill}")
```

#### 步骤 4: 执行意图

```python
context = AgentContext(user_id="user123")

# 执行 Shell 命令
result = await agent.execute("执行 pwd", context)
print(result.message)  # ✓ 执行成功
print(result.data)     # {"stdout": "/Users/jeffery/...\n"}

# 执行计算
result = await agent.execute("计算 123 * 456", context)
print(result.data)     # {"result": 56088}

# 查询时间
result = await agent.execute("现在几点", context)
print(result.data)     # {"time": "14:30:25"}
```

### 4. 能力匹配机制

Agent 通过**标签匹配**和**关键词匹配**自动选择合适的能力：

```python
# 用户意图
intent = "执行 ls -la"

# 匹配过程
1. 提取关键词：["执行", "ls"]
2. 匹配能力 tags:
   - Shell 命令 (tags: ["system", "shell"]) ✓ 匹配 "执行"
3. 提取参数:
   - command: "ls -la"
4. 执行能力:
   - result = registry.execute_capability("shell", command="ls -la")
```

---

## 三、MCP 集成 (Model Context Protocol)

### 1. MCP 架构

```
┌─────────────────────────────────────┐
│  AIAgent                            │
│  └─ MCPIntegration                  │
│      ├─ Server: weather             │
│      ├─ Server: filesystem          │
│      └─ Server: github              │
└─────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│  MCP Servers                        │
│  • @mcp/server-weather              │
│  • @mcp/server-filesystem           │
│  • @mcp/server-github               │
└─────────────────────────────────────┘
```

### 2. 连接 MCP 服务器

```python
from intentos.agent import AIAgent

agent = AIAgent()
await agent.initialize()

# 连接天气服务器
await agent.connect_mcp(
    name="weather",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-weather"],
)

# 连接文件系统服务器
await agent.connect_mcp(
    name="filesystem",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"],
)

# 查看已连接的服务器
servers = agent.mcp.get_connected_servers()
print(f"已连接：{servers}")  # ['weather', 'filesystem']
```

### 3. MCP 工具注册

MCP 工具会自动注册为能力：

```python
# 连接后自动注册
# weather.get_current_weather → weather_get_current_weather
# filesystem.read_file → filesystem_read_file

# 查看 MCP 能力
mcp_caps = [cap for cap in agent.get_capabilities() if "mcp" in cap]
print(mcp_caps)
```

---

## 四、Skill 集成 (Claude Skills 规范)

### 1. Skill 结构

基于 Claude Skills 规范：

```
~/.claude/skills/
└── skill-name/
    ├── SKILL.md              # 元数据和规范
    ├── scripts/              # 可执行代码
    ├── references/           # 文档材料
    └── assets/               # 输出文件
```

### 2. SKILL.md 格式

```markdown
---
name: skill-name
description: Skill 描述
license: MIT
---

# Skill 名称

Skill 详细说明...

## 何时使用

- 使用场景 1
- 使用场景 2

## 资源

### Scripts
- `scripts/example.py`

### References
- `references/docs.md`
```

### 3. 自动加载

Skills 在 Agent 初始化时自动加载：

```python
agent = AIAgent(enable_skills=True)
await agent.initialize()

# 自动扫描 ~/.claude/skills/
# 自动解析 SKILL.md
# 自动注册能力
```

---

## 五、完整示例

### 示例 1: 基础使用

```python
import asyncio
from intentos.agent import AIAgent, AgentContext

async def main():
    # 创建 Agent
    agent = AIAgent()
    await agent.initialize()
    
    # 创建上下文
    context = AgentContext(user_id="user123")
    
    # 执行意图
    intents = [
        "执行 pwd",
        "计算 123 * 456",
        "现在几点",
    ]
    
    for intent in intents:
        print(f"\n用户：{intent}")
        result = await agent.execute(intent, context)
        print(f"Agent: {result.message}")
        if result.data:
            print(f"数据：{result.data}")

asyncio.run(main())
```

### 示例 2: 使用 MCP

```python
import asyncio
from intentos.agent import AIAgent, AgentContext

async def main():
    agent = AIAgent(enable_mcp=True)
    await agent.initialize()
    
    # 连接 MCP 服务器
    await agent.connect_mcp("weather", "npx", ["-y", "@mcp/server-weather"])
    
    context = AgentContext(user_id="user123")
    
    # 使用 MCP 工具
    result = await agent.execute("查询北京天气", context)
    print(result.data)

asyncio.run(main())
```

### 示例 3: 使用 Skills

```python
import asyncio
from intentos.agent import AIAgent, AgentContext

async def main():
    agent = AIAgent(enable_skills=True)
    await agent.initialize()
    
    # 查看已加载的 Skills
    print(f"已加载 {len(agent.get_loaded_skills())} 个 Skills")
    
    context = AgentContext(user_id="user123")
    
    # 使用 Skill
    result = await agent.execute("创建内容策略", context)
    print(result.data)

asyncio.run(main())
```

---

## 六、新旧架构对比

| 特性 | 旧架构 (deprecated/apps) | 新架构 (agent) |
|------|-------------------------|---------------|
| **能力管理** | 硬编码 | 注册中心 |
| **意图处理** | 直接匹配 | 编译为 PEF |
| **MCP 支持** | 有限 | 原生支持 |
| **Skill 支持** | 有限 | 原生支持 |
| **扩展性** | 低 | 高 |
| **模块职责** | 混合 | 清晰分离 |

---

## 七、最佳实践

### 1. 能力注册

```python
# ✅ 正确：使用注册中心
registry.register(
    id="my_tool",
    name="我的工具",
    description="描述",
    handler=my_handler,
    tags=["custom"],
    source="builtin",
)

# ❌ 错误：硬编码
def execute(intent):
    if "my_tool" in intent:
        return my_handler()
```

### 2. 意图编译

```python
# ✅ 正确：使用编译器
pef = compiler.compile(intent, capabilities, context)

# ❌ 错误：直接执行
result = llm.generate(intent)
```

### 3. 错误处理

```python
# ✅ 正确：完整的错误处理
result = await agent.execute(intent, context)
if not result.success:
    print(f"错误：{result.error}")
else:
    print(f"成功：{result.message}")
```

---

## 八、总结

在 IntentOS v10.0+ 中，AI Agent 的实现方式发生了根本性变化：

**核心理念**:
- ✓ 基于能力注册 (而非硬编码)
- ✓ 意图编译为 PEF (而非直接执行)
- ✓ 原生支持 MCP 和 Skills
- ✓ 清晰的模块职责

**使用方式**:
```python
from intentos.agent import AIAgent, AgentContext

agent = AIAgent()
await agent.initialize()
result = await agent.execute("意图", context)
```

**在 IntentOS 中，Agent 是通过能力注册和意图编译"生长"出来的，而不是"编写"出来的！** 🚀✨

---

## 参考文档

### AI Native App 文档体系

| 文档 | 说明 |
|------|------|
| [AI Native App 概述](./AI_NATIVE_APP.md) | ⭐ 核心概念、架构概览 |
| [即时生成架构](./JIT_GENERATION_ARCHITECTURE.md) | App 即时生成、身份感知 |
| [租户架构](./TENANT_ARCHITECTURE.md) | 多租户隔离、资源配置 |
| [应用开发指南](./APP_DEVELOPMENT_GUIDE.md) | 开发流程、最佳实践 |

### 其他相关文档

- [Self-Bootstrap 机制](./SELF_BOOTSTRAP.md)
- [IntentOS vs OpenClaw](./INTENTOS_VS_OPENCLAW.md)
- [架构集成说明](./ARCHITECTURE_INTEGRATION.md)
- [Skill 规范](./SKILL_SPECIFICATION.md)
