# 核心 API

> 本文档介绍 IntentOS 的核心类和函数，是使用 IntentOS 的基础参考。

---

## 1. 意图相关

### 1.1 Intent

意图是用户目标的结构性表达。

```python
from intentos import Intent, IntentType, Context

# 创建意图
intent = Intent(
    name="sales_analysis",
    intent_type=IntentType.COMPOSITE,
    goal="分析华东区 Q3 销售数据",
    description="销售数据分析任务",
    context=Context(
        user_id="manager_001",
        user_role="sales_manager",
    ),
    params={
        "region": "华东",
        "period": "Q3",
    },
    constraints={
        "timeout_seconds": 300,
    },
)

# 转换为字典
data = intent.to_dict()

# 更新状态
intent.update_status(IntentStatus.RUNNING)
```

**属性**:

| 属性 | 类型 | 说明 |
|------|------|------|
| `id` | str | 唯一标识 |
| `name` | str | 意图名称 |
| `intent_type` | IntentType | 意图类型 |
| `goal` | str | 目标描述 |
| `params` | dict | 参数 |
| `constraints` | dict | 约束 |
| `status` | IntentStatus | 执行状态 |

### 1.2 IntentType

意图类型枚举：

```python
from intentos import IntentType

IntentType.ATOMIC       # 原子意图
IntentType.COMPOSITE    # 复合意图
IntentType.SCENARIO     # 场景意图
IntentType.META         # 元意图
```

### 1.3 IntentStatus

意图状态枚举：

```python
from intentos import IntentStatus

IntentStatus.PENDING     # 待执行
IntentStatus.RUNNING     # 执行中
IntentStatus.COMPLETED   # 已完成
IntentStatus.FAILED      # 失败
IntentStatus.CANCELLED   # 已取消
```

### 1.4 Context

执行上下文：

```python
from intentos import Context

# 创建上下文
context = Context(
    user_id="user_001",
    user_role="manager",
    permissions=["read_sales", "create_report"],
)

# 检查权限
if context.has_permission("read_sales"):
    ...

# 设置/获取变量
context.set_variable("region", "华东")
region = context.get_variable("region")
```

---

## 2. 能力相关

### 2.1 Capability

能力是可调用的原子功能单元：

```python
from intentos import Capability, Context

# 定义能力函数
async def query_sales(context: Context, region: str) -> dict:
    return {"region": region, "revenue": 1000000}

# 创建能力
capability = Capability(
    name="query_sales",
    description="查询销售数据",
    input_schema={
        "type": "object",
        "properties": {
            "region": {"type": "string"},
        },
        "required": ["region"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "revenue": {"type": "number"},
        },
    },
    func=query_sales,
    requires_permissions=["read_sales"],
    tags=["sales", "query"],
)

# 执行能力
result = await capability.execute(context, region="华东")
```

### 2.2 IntentTemplate

意图模板：

```python
from intentos import IntentTemplate, IntentType, IntentStep

template = IntentTemplate(
    name="sales_analysis",
    description="分析销售数据",
    intent_type=IntentType.COMPOSITE,
    params_schema={
        "region": {"type": "string"},
        "period": {"type": "string"},
    },
    steps=[
        IntentStep(
            capability_name="query_sales",
            params={"region": "{{region}}"},
            output_var="sales_data",
        ),
    ],
    version="1.0.0",
    tags=["sales", "analysis"],
)

# 实例化
from intentos import Context
intent = template.instantiate(
    Context(user_id="test"),
    region="华东",
    period="Q3",
)
```

### 2.3 IntentStep

意图步骤：

```python
from intentos import IntentStep

step = IntentStep(
    capability_name="query_sales",
    params={"region": "{{region}}"},
    depends_on=["step1"],
    condition="exists(${data})",
    output_var="result",
)
```

---

## 3. 仓库相关

### 3.1 IntentRegistry

意图仓库：

```python
from intentos import IntentRegistry

# 创建仓库
registry = IntentRegistry()

# 注册能力
registry.register_capability(capability)

# 注册模板
registry.register_template(template)

# 获取能力
cap = registry.get_capability("query_sales")

# 获取模板
template = registry.get_template("sales_analysis")

# 列出能力
all_caps = registry.list_capabilities()
sales_caps = registry.list_capabilities(tags=["sales"])

# 搜索
results = registry.search("销售")
print(results["templates"])
print(results["capabilities"])

# 自省
introspect = registry.introspect()
```

---

## 4. 执行相关

### 4.1 IntentOS

IntentOS 主类：

```python
from intentos import IntentOS

# 创建实例
os = IntentOS()
os.initialize()

# 执行意图
result = await os.execute("分析华东区 Q3 销售数据")

# 设置用户
os.interface.set_user(
    user_id="manager_001",
    role="manager",
    permissions=["read_sales"],
)

# 获取对话历史
history = os.interface.get_history()
```

### 4.2 ExecutionEngine

执行引擎：

```python
from intentos import ExecutionEngine, IntentRegistry

registry = IntentRegistry()
engine = ExecutionEngine(registry)

# 执行意图
result = await engine.execute(intent)
```

---

## 5. LLM 相关

### 5.1 Message

LLM 消息：

```python
from intentos import Message, LLMRole

# 创建消息
system_msg = Message.system("你是销售分析助手")
user_msg = Message.user("分析华东区销售数据")
assistant_msg = Message.assistant("好的，正在分析...")
tool_msg = Message.tool(
    content="销售数据：...",
    name="query_sales",
    tool_call_id="call_123",
)

# 转换为字典
msg_dict = user_msg.to_dict()
```

### 5.2 ToolDefinition

工具定义：

```python
from intentos import ToolDefinition

tool = ToolDefinition(
    name="query_sales",
    description="查询销售数据",
    parameters={
        "type": "object",
        "properties": {
            "region": {"type": "string"},
        },
        "required": ["region"],
    },
)
```

### 5.3 LLMExecutor

LLM 执行器：

```python
from intentos import LLMExecutor, create_executor

# 创建执行器
executor = create_executor(
    provider="openai",
    api_key="sk-...",
    model="gpt-4o",
)

# 执行
from intentos import Message
messages = [
    Message.system("你是助手"),
    Message.user("你好"),
]
response = await executor.execute(messages)

# 流式输出
async for chunk in executor.generate_stream(messages):
    print(chunk, end="", flush=True)
```

### 5.4 LLMResponse

LLM 响应：

```python
from intentos import LLMResponse

# 响应属性
print(response.content)           # 内容
print(response.model)             # 模型
print(response.usage.total_tokens)  # Token 使用
print(response.tool_calls)        # 工具调用
print(response.latency_ms)        # 延迟
```

---

## 6. 记忆相关

### 6.1 MemoryType

记忆类型：

```python
from intentos import MemoryType

MemoryType.SHORT_TERM   # 短期记忆
MemoryType.LONG_TERM    # 长期记忆
```

### 6.2 MemoryEntry

记忆条目：

```python
from intentos import MemoryEntry, MemoryType, MemoryPriority

entry = MemoryEntry(
    key="user:123:preference",
    value={"theme": "dark"},
    memory_type=MemoryType.SHORT_TERM,
    priority=MemoryPriority.NORMAL,
    tags=["user", "preference"],
)

# 检查过期
if entry.is_expired():
    ...

# 设置过期时间
entry.set_expiry(3600)  # 1 小时

# 转换为字典
data = entry.to_dict()
```

### 6.3 MemoryPriority

记忆优先级：

```python
from intentos import MemoryPriority

MemoryPriority.LOW       # 低
MemoryPriority.NORMAL    # 普通
MemoryPriority.HIGH      # 高
MemoryPriority.CRITICAL  # 关键
```

### 6.4 DistributedMemoryManager

分布式记忆管理器：

```python
from intentos import create_memory_manager, create_and_initialize_memory_manager

# 创建并初始化
manager = await create_and_initialize_memory_manager(
    short_term_max=10000,
    long_term_enabled=True,
    long_term_backend="redis",
    redis_host="localhost",
    redis_port=6379,
)

# 设置记忆
await manager.set_short_term(
    key="user:123",
    value={"name": "张三"},
    tags=["user"],
    ttl_seconds=3600,
)

await manager.set_long_term(
    key="knowledge:sales",
    value={"best_practice": "..."},
    tags=["knowledge", "sales"],
)

# 获取记忆
entry = await manager.get("user:123")

# 按标签检索
entries = await manager.get_by_tag("user")

# 搜索
results = await manager.search("销售")

# 获取统计
stats = await manager.get_stats()
```

---

## 7. 便捷函数

### 7.1 创建执行器

```python
from intentos import create_executor

# OpenAI
executor = create_executor(provider="openai", api_key="sk-...")

# Anthropic
executor = create_executor(provider="anthropic", api_key="...")

# Ollama
executor = create_executor(provider="ollama", host="http://localhost:11434")

# Mock
executor = create_executor(provider="mock")
```

### 7.2 创建路由器

```python
from intentos import create_router, BackendConfig

router = create_router([
    BackendConfig(
        name="primary",
        model="gpt-4o",
        api_key="sk-...",
        priority=10,
    ),
    BackendConfig(
        name="backup",
        model="claude-3-5-sonnet",
        api_key="...",
        priority=5,
    ),
])

# 执行
response = await router.generate(messages)
```

### 7.3 创建记忆管理器

```python
from intentos import create_memory_manager

manager = create_memory_manager(
    short_term_max=10000,
    short_term_ttl_seconds=3600,
    long_term_enabled=True,
    long_term_backend="redis",
)
await manager.initialize()
```

### 7.4 创建 Map/Reduce 任务

```python
from intentos import create_map_reduce_task, create_map_reduce_executor

task = create_map_reduce_task(
    name="word_count",
    map_func=lambda doc: [(word, 1) for word in doc.split()],
    reduce_func=lambda k, v: sum(v),
    input_data=["hello world", "hello python"],
)

executor = create_map_reduce_executor(max_memory_mb=50)
results = await executor.execute(task)
```

---

## 8. 异常处理

### 8.1 常见异常

```python
from intentos import LLMError, RateLimitError, AuthenticationError, TimeoutError

try:
    response = await executor.execute(messages)
except RateLimitError as e:
    # 速率限制
    print(f"请求过多：{e}")
except AuthenticationError as e:
    # 认证失败
    print(f"API 密钥无效：{e}")
except TimeoutError as e:
    # 超时
    print(f"请求超时：{e}")
except LLMError as e:
    # 其他 LLM 错误
    print(f"LLM 错误：{e}")
```

### 8.2 权限错误

```python
from intentos import PermissionError

try:
    result = await capability.execute(context, **params)
except PermissionError as e:
    print(f"权限不足：{e}")
```

---

## 9. 总结

IntentOS 核心 API 分类：

| 类别 | 主要类/函数 |
|------|-----------|
| **意图** | Intent, IntentType, IntentStatus, Context |
| **能力** | Capability, IntentTemplate, IntentStep |
| **仓库** | IntentRegistry |
| **执行** | IntentOS, ExecutionEngine |
| **LLM** | Message, ToolDefinition, LLMExecutor, LLMResponse |
| **记忆** | MemoryType, MemoryEntry, MemoryPriority, DistributedMemoryManager |
| **便捷** | create_executor, create_router, create_memory_manager |

---

**下一篇**: [编译器 API](02-compiler-api.md)

**上一篇**: [部署 IntentOS](../07-guides/04-deploy-intentos.md)
