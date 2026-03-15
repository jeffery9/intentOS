# AI Agent 使用指南

## 概述

IntentOS AI Agent 是一个基于应用层框架开发的智能助理，通过 LLM、记忆系统、知识库和工具调用提供服务。

---

## 快速开始

### 方式 1: Chat TUI (推荐)

```bash
# 启动现代化聊天界面
python -m intentos.apps.chat_tui
```

**界面预览**:
```
╔════════════════════════════════════════════════════════╗
║           IntentOS AI Agent - 智能助理                  ║
║                                                        ║
║  输入任意消息开始对话                                   ║
║  输入 /help 查看帮助，/quit 退出                       ║
╚════════════════════════════════════════════════════════╝

👤 你：安排明天下午 3 点的会议

╭────────────────────────────────────────────────────────╮
│ 🤖 AI 助理 • 14:30:25                                 │
│ ✓ 会议已安排                                           │
│                                                        │
│ 详情:                                                  │
│ • event_id: evt_123                                   │
│ • time: 2026-03-16 15:00                              │
│                                                        │
│ 💡 建议下一步:                                         │
│ • 发送邀请                                             │
│ • 设置提醒                                             │
╰────────────────────────────────────────────────────────╯
```

### 方式 2: 传统 CLI

```bash
# 启动传统命令行界面
python -m intentos.apps.ai_agent_cli
```

### 方式 3: Python API

```
👤 你：安排明天下午 3 点的会议

🤖 AI 智能助理：✓ 会议已安排

📋 详情:
   • event_id: evt_123
   • title: 会议
   • time: 2026-03-16 15:00

💡 建议下一步:
   • 发送邀请
   • 设置提醒
```

---

## Python API 使用

### 基础使用

```python
from intentos.apps import AIAgentApp, get_app_layer

# 获取应用层
layer = get_app_layer()

# 创建 AI Agent
agent = AIAgentApp()
await agent.initialize(layer.services)

# 注册到应用层
layer.register_app(agent)

# 执行意图
from intentos.apps import AppContext

context = AppContext(user_id="user123")
result = await agent.execute("安排明天下午 3 点的会议", context)

print(result.message)
print(result.data)
```

### 连接记忆系统

```python
from intentos.apps.services import MemorySystem

# 创建记忆系统
memory = MemorySystem(user_id="user123")

# 连接到 AI Agent
agent.memory_system = memory

# 对话会自动记录
result = await agent.execute("我喜欢喝咖啡", context)

# 查询记忆
memories = memory.search("咖啡")
print(memories)  # 找到相关记忆
```

### 连接知识库

```python
from intentos.apps.services import KnowledgeBase

# 创建知识库
kb = KnowledgeBase()

# 添加知识
kb.add(
    title="用户偏好",
    content="用户喜欢喝咖啡，不喜欢茶",
    category="preferences",
    tags=["偏好", "饮品"],
)

# 连接到 AI Agent
agent.knowledge_base = kb

# AI Agent 可以查询知识
result = await agent.execute("我喜欢喝什么？", context)
# 会基于知识库回答
```

### 使用工具

```python
from intentos.apps.services import ToolRegistry

# 获取工具注册表
tools = ToolRegistry()

# 调用内置工具
result = await tools.call("calculator", expression="123 * 456")
print(result["result"])  # 56088

result = await tools.call("weather", city="北京")
print(result["result"])  # 天气信息

# 注册自定义工具
def my_custom_tool(param1: str, param2: int) -> dict:
    return {"result": f"{param1} x {param2}"}

tools.register(
    id="my_tool",
    name="我的工具",
    description="自定义工具",
    handler=my_custom_tool,
    tags=["custom"],
)
```

---

## 配置 LLM

### 环境变量配置

```bash
# 选择 LLM 提供商
export LLM_PROVIDER=openai  # 或 anthropic/ollama/mock

# OpenAI 配置
export LLM_MODEL=gpt-4
export LLM_API_KEY=sk-xxx
export LLM_BASE_URL=https://api.openai.com/v1

# Anthropic 配置
export LLM_PROVIDER=anthropic
export LLM_MODEL=claude-3
export LLM_API_KEY=sk-ant-xxx

# Ollama 配置 (本地模型)
export LLM_PROVIDER=ollama
export LLM_MODEL=llama2
export LLM_BASE_URL=http://localhost:11434

# Mock 配置 (测试用)
export LLM_PROVIDER=mock
```

### 代码配置

```python
from intentos.apps.services import get_llm_provider

llm = get_llm_provider()

# 查看配置
config = llm.get_config()
print(config)
# {'provider': 'openai', 'model': 'gpt-4', ...}
```

---

## 记忆系统详解

### 短期记忆

```python
from intentos.apps.services import ShortTermMemory

# 创建短期记忆 (最近 50 条)
stm = ShortTermMemory(max_size=50)

# 添加记忆
stm.add(
    content="用户说喜欢喝咖啡",
    tags=["preference", "drink"],
)

# 获取最近记忆
recent = stm.get_recent(10)

# 搜索记忆
results = stm.search("咖啡")

# 获取上下文文本
context = stm.get_context()
```

### 长期记忆

```python
from intentos.apps.services import LongTermMemory

# 创建长期记忆 (持久化)
ltm = LongTermMemory(
    storage_path="~/.intentos/memory/user123"
)

# 添加记忆 (带重要性)
ltm.add(
    content="用户生日是 3 月 15 日",
    tags=["personal", "birthday"],
    importance=0.9,  # 重要性 0-1
)

# 搜索记忆
results = ltm.search("生日")

# 获取重要记忆
important = ltm.get_important(limit=20)

# 按标签获取
by_tags = ltm.get_by_tags(["personal"])
```

### 记忆系统

```python
from intentos.apps.services import MemorySystem

# 完整记忆系统 (短期 + 长期)
memory = MemorySystem(user_id="user123")

# 添加对话 (自动判断重要性)
memory.add_conversation(
    intent="我喜欢喝咖啡",
    response="好的，我记住了您喜欢喝咖啡",
    tags=["preference"],
)

# 获取完整上下文
context = memory.get_context()
# {
#   'short_term': '...',
#   'important_memories': ['...']
# }

# 搜索所有记忆
results = memory.search("咖啡")
```

---

## 知识库详解

### 添加知识

```python
from intentos.apps.services import KnowledgeBase

kb = KnowledgeBase()

# 添加知识条目
item = kb.add(
    title="IntentOS 公司信息",
    content="IntentOS 是一个 AI 原生操作系统项目",
    category="company",
    tags=["IntentOS", "AI", "操作系统"],
    source="internal",
)

print(item.id)  # 知识 ID
```

### 搜索知识

```python
# 文本搜索
results = kb.search("AI 操作系统", limit=10)

# 按分类获取
company_info = kb.get_by_category("company")

# 获取特定条目
item = kb.get(item_id)

# 删除条目
kb.delete(item_id)
```

### 知识图谱

```python
from intentos.apps.services import KnowledgeGraph

# 创建知识图谱
graph = KnowledgeGraph()

# 添加关系
graph.add_relation(
    from_id="intentos",
    to_id="ai_os",
    relation_type="is_a",  # 是一种
    weight=1.0,
)

graph.add_relation(
    from_id="intentos",
    to_id="semantic_vm",
    relation_type="has_part",  # 包含
    weight=0.8,
)

# 获取关联知识
connected = graph.get_connected("intentos", kb)
```

### 加载内置知识

```python
from intentos.apps.services.knowledge import load_builtin_knowledge

kb = KnowledgeBase()
load_builtin_knowledge(kb)  # 加载内置知识

# 现在有预定义的公司信息、产品知识等
```

---

## 工具系统详解

### 内置工具

```python
from intentos.apps.services import ToolRegistry

tools = ToolRegistry()

# 计算器
result = await tools.call("calculator", expression="2 + 2 * 3")

# 天气查询
result = await tools.call("weather", city="北京")

# 新闻查询
result = await tools.call("news", category="tech")

# 文件读取
result = await tools.call("file_read", path="/path/to/file.txt")

# 网页搜索
result = await tools.call("web_search", query="AI 新闻")
```

### 注册自定义工具

```python
from intentos.apps.services import ToolRegistry

tools = ToolRegistry()

# 方法 1: 直接注册
def my_tool(param1: str, param2: int) -> dict:
    return {"result": f"{param1} x {param2}"}

tools.register(
    id="my_tool",
    name="我的工具",
    description="自定义工具描述",
    handler=my_tool,
    tags=["custom"],
)

# 方法 2: 使用装饰器
from intentos.apps.services.tools import register_tool

@register_tool(
    id="another_tool",
    name="另一个工具",
    description="描述",
    tags=["custom"],
)
def another_tool(data: str) -> dict:
    return {"processed": data.upper()}
```

### 工具调用

```python
# 列出所有工具
all_tools = tools.list_tools()
for tool in all_tools:
    print(f"{tool.name}: {tool.description}")

# 按标签过滤
math_tools = tools.list_tools(tags=["math"])

# 调用工具
result = await tools.call("my_tool", param1="hello", param2=5)

if result["success"]:
    print(result["result"])
else:
    print(result["error"])
```

---

## 完整示例

### 示例 1: 带记忆的对话

```python
from intentos.apps import AIAgentApp, get_app_layer, AppContext
from intentos.apps.services import MemorySystem

# 初始化
layer = get_app_layer()
agent = AIAgentApp()
await agent.initialize(layer.services)

# 连接记忆
agent.memory_system = MemorySystem(user_id="user123")
layer.register_app(agent)

# 对话 1
context = AppContext(user_id="user123")
result1 = await agent.execute("我喜欢喝咖啡", context)

# 对话 2 (会记住之前的偏好)
result2 = await agent.execute("推荐一个饮品", context)
# AI 会基于记忆推荐咖啡
```

### 示例 2: 知识库增强

```python
from intentos.apps import AIAgentApp, get_app_layer
from intentos.apps.services import KnowledgeBase

# 初始化
layer = get_app_layer()
agent = AIAgentApp()
await agent.initialize(layer.services)

# 连接知识库
kb = KnowledgeBase()
kb.add(
    title="公司产品",
    content="我们的主要产品是 IntentOS AI 操作系统",
    category="product",
)
agent.knowledge_base = kb

layer.register_app(agent)

# 现在 AI 可以回答公司相关问题
result = await agent.execute("你们公司有什么产品？", AppContext())
```

### 示例 3: 工具调用

```python
from intentos.apps import AIAgentApp
from intentos.apps.services import ToolRegistry

# 注册工具
tools = ToolRegistry()

def get_stock_price(symbol: str) -> dict:
    return {"symbol": symbol, "price": 150.00}

tools.register(
    id="stock_price",
    name="股票价格查询",
    description="查询股票价格",
    handler=get_stock_price,
    tags=["finance"],
)

# AI Agent 可以使用工具
agent = AIAgentApp()
agent.tool_registry = tools

result = await agent.execute("查询 AAPL 的股票价格", AppContext())
```

---

## 命令行使用

### 基本命令

```bash
# 启动 AI Agent
python -m intentos.apps.ai_agent_cli

# 查看帮助
/help

# 查看能力
/capabilities

# 查看对话历史
/history

# 清空历史
/clear

# 查看用户信息
/profile

# 退出
/quit
```

### 对话示例

```
╔════════════════════════════════════════════════════════╗
║           IntentOS AI Agent - 智能助理                  ║
╚════════════════════════════════════════════════════════╝

🤖 AI 智能助理 v1.0.0

💡 我能帮你:
  📅 日程管理 - 安排会议、设置提醒
  📧 邮件处理 - 撰写邮件、总结邮件
  🔍 信息检索 - 搜索资料、总结文章
  ✍️ 内容创作 - 写文章、写报告、写文案
  📊 数据分析 - 分析数据、生成图表
  💻 编程助手 - 写代码、审查代码
  ⚙️ 自动化 - 自动执行重复任务
  📋 任务规划 - 分解任务、优先级排序

👤 你：安排明天下午 3 点的会议

🤖 AI 智能助理：✓ 会议已安排

📋 详情:
   • event_id: evt_123
   • title: 会议
   • time: 2026-03-16 15:00
   • calendar_link: https://calendar.intentos.io/evt_123

💡 建议下一步:
   • 发送邀请
   • 设置提醒
   • 准备材料
```

---

## 故障排查

### LLM 调用失败

```bash
# 检查配置
echo $LLM_PROVIDER
echo $LLM_API_KEY

# 使用 Mock 模式测试
export LLM_PROVIDER=mock
python -m intentos.apps.ai_agent_cli
```

### 记忆系统问题

```python
# 检查记忆存储路径
from intentos.apps.services import MemorySystem
memory = MemorySystem("test")
print(memory.long_term.storage_path)

# 清空记忆
memory.short_term.clear()
```

### 工具调用失败

```python
# 列出可用工具
from intentos.apps.services import ToolRegistry
tools = ToolRegistry()
for tool in tools.list_tools():
    print(f"{tool.id}: {tool.name}")

# 测试工具
result = await tools.call("calculator", expression="1+1")
print(result)
```

---

## 最佳实践

### 1. 用户隔离

```python
# 每个用户独立的记忆和知识
memory = MemorySystem(user_id=user_id)
kb = KnowledgeBase(storage_path=f"~/.intentos/kb/{user_id}")
```

### 2. 重要性评估

```python
# 重要信息存入长期记忆
if "重要" in intent or "记住" in intent:
    memory.long_term.add(
        content=intent,
        importance=0.9,
    )
```

### 3. 知识更新

```python
# 定期更新知识库
async def update_knowledge():
    kb = KnowledgeBase()
    kb.add(
        title="最新信息",
        content=get_latest_info(),
        source="auto_update",
    )
```

### 4. 工具安全

```python
# 验证工具参数
def safe_file_read(path: str) -> dict:
    # 限制访问范围
    if not path.startswith("/safe/path"):
        return {"error": "路径不允许"}
    return file_read(path)
```

---

## 总结

AI Agent 通过以下服务提供服务：

| 服务 | 功能 | 使用场景 |
|------|------|---------|
| **LLM Provider** | LLM 调用 | 语义理解、内容生成 |
| **Memory System** | 记忆存储 | 对话历史、用户偏好 |
| **Knowledge Base** | 知识库 | 公司信息、产品知识 |
| **Tool Registry** | 工具调用 | 计算器、天气、搜索 |

**开始使用 AI Agent 吧！** 🤖✨
