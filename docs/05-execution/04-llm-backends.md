# LLM 后端支持

> IntentOS 支持多种 LLM 后端，包括 OpenAI、Anthropic、Ollama 等，支持路由、故障转移和负载均衡。

---

## 1. 概述

### 1.1 支持的后端

| 提供商 | 模型 | 配置 |
|--------|------|------|
| **OpenAI** | GPT-4o, GPT-4, GPT-3.5 | `provider="openai"` |
| **Anthropic** | Claude 3/3.5 | `provider="anthropic"` |
| **Ollama** | Llama 3.1, Mistral, Qwen | `provider="ollama"` |
| **兼容 OpenAI API** | vLLM, LocalAI | `provider="openai", base_url=...` |

### 1.2 后端抽象

```python
class LLMBackend(ABC):
    """LLM 后端抽象基类"""
    
    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """生成响应"""
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: list[Message],
        **kwargs,
    ) -> AsyncIterator[str]:
        """流式生成"""
        pass
```

---

## 2. OpenAI 后端

### 2.1 配置

```python
from intentos import create_executor

# 基本配置
executor = create_executor(
    provider="openai",
    api_key="sk-...",  # 或从环境变量 OPENAI_API_KEY 读取
    model="gpt-4o",
    base_url=None,  # 可选：自定义 API 端点
    timeout=60,
    max_retries=3,
)
```

### 2.2 使用示例

```python
from intentos import Message

messages = [
    Message.system("你是销售分析助手"),
    Message.user("分析华东区 Q3 销售数据"),
]

response = await executor.execute(messages)

print(f"响应：{response.content}")
print(f"Token 使用：{response.usage.total_tokens}")
print(f"延迟：{response.latency_ms}ms")
```

### 2.3 Tool Calling

```python
from intentos import ToolDefinition

tools = [
    ToolDefinition(
        name="query_sales",
        description="查询销售数据",
        parameters={
            "type": "object",
            "properties": {
                "region": {"type": "string", "description": "区域"},
                "period": {"type": "string", "description": "时间段"},
            },
            "required": ["region"],
        },
    ),
]

messages = [
    Message.system("你是销售分析助手"),
    Message.user("查询华东区 Q3 销售数据"),
]

response = await executor.execute(messages, tools=tools)

# 检查工具调用
if response.has_tool_calls:
    for tc in response.tool_calls:
        print(f"调用工具：{tc.name}")
        print(f"参数：{tc.arguments}")
        
        # 执行工具
        result = await call_tool(tc.name, tc.arguments)
        
        # 将结果返回给 LLM
        messages.append(response.message)
        messages.append(Message.tool(
            content=str(result),
            name=tc.name,
            tool_call_id=tc.id,
        ))
        
        # 继续对话
        response = await executor.execute(messages, tools=tools)
```

---

## 3. Anthropic 后端

### 3.1 配置

```python
executor = create_executor(
    provider="anthropic",
    api_key="...",  # 或从环境变量 ANTHROPIC_API_KEY 读取
    model="claude-3-5-sonnet-20241022",
    timeout=60,
    max_retries=3,
)
```

### 3.2 使用示例

```python
messages = [
    Message.system("你是 Claude，一个有用的助手"),
    Message.user("你好，请介绍一下自己"),
]

response = await executor.execute(messages)
print(response.content)
```

### 3.3 Tool Use

```python
# Anthropic 的 Tool 使用方式类似
tools = [
    ToolDefinition(
        name="query_sales",
        description="查询销售数据",
        parameters={...},
    ),
]

response = await executor.execute(messages, tools=tools)

# 处理 Tool Use
if response.tool_calls:
    for tc in response.tool_calls:
        # Anthropic 的工具调用格式略有不同
        result = await call_tool(tc.name, tc.arguments)
```

---

## 4. Ollama 后端

### 4.1 配置

```python
executor = create_executor(
    provider="ollama",
    model="llama3.1",
    host="http://localhost:11434",  # Ollama 服务地址
    timeout=120,  # 本地模型可能需要更长时间
)
```

### 4.2 使用示例

```python
messages = [
    Message.user("你好"),
]

response = await executor.execute(messages)
print(response.content)
```

### 4.3 本地模型优势

| 优势 | 说明 |
|------|------|
| **隐私** | 数据不出本地 |
| **成本** | 免费使用 |
| **定制** | 可微调模型 |
| **离线** | 无需网络连接 |

---

## 5. 多后端路由

### 5.1 路由器配置

```python
from intentos import create_router, BackendConfig

router = create_router([
    BackendConfig(
        name="primary",
        model="gpt-4o",
        api_key=os.environ.get("OPENAI_API_KEY"),
        priority=10,      # 最高优先级
        max_qps=100,      # 每秒最大请求数
        weight=1.0,       # 权重
    ),
    BackendConfig(
        name="backup",
        model="claude-3-5-sonnet",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        priority=5,       # 中等优先级
    ),
    BackendConfig(
        name="local",
        model="llama3.1",
        host="http://localhost:11434",
        priority=1,       # 最低优先级
    ),
])
```

### 5.2 路由策略

```python
# 优先级路由（默认）
response = await router.generate(messages, strategy="priority")

# 轮询路由
response = await router.generate(messages, strategy="round_robin")

# 加权路由
response = await router.generate(messages, strategy="weighted")

# 最低延迟路由
response = await router.generate(messages, strategy="latency")
```

### 5.3 故障转移

```python
try:
    response = await router.generate(messages)
except LLMError as e:
    # 所有后端都失败
    logger.error(f"所有 LLM 后端都失败：{e}")
    
    # 可以使用 Mock 后端降级
    mock_executor = create_executor(provider="mock")
    response = await mock_executor.execute(messages)
```

---

## 6. 流式输出

### 6.1 流式生成

```python
executor = create_executor(provider="openai", model="gpt-4o")

messages = [
    Message.user("请用 100 字介绍人工智能"),
]

# 流式输出
async for chunk in executor.generate_stream(messages):
    print(chunk, end="", flush=True)
```

### 6.2 流式处理管道

```python
async def streaming_pipeline(user_input: str):
    """流式处理管道"""
    executor = create_executor(provider="openai")
    
    messages = [
        Message.system("你是有用的助手"),
        Message.user(user_input),
    ]
    
    # 收集完整响应
    full_response = ""
    
    async for chunk in executor.generate_stream(messages):
        full_response += chunk
        # 实时显示
        print(chunk, end="", flush=True)
    
    print()  # 换行
    
    return full_response
```

---

## 7. 统计和监控

### 7.1 获取统计

```python
# 获取后端统计
stats = router.get_stats()

for name, s in stats.items():
    print(f"{name}:")
    print(f"  成功率：{s['success_rate']:.1f}%")
    print(f"  平均延迟：{s['avg_latency_ms']:.0f}ms")
    print(f"  总请求：{s['total_requests']}")
```

### 7.2 Token 计数

```python
response = await executor.execute(messages)

print(f"Prompt Token: {response.usage.prompt_tokens}")
print(f"Completion Token: {response.usage.completion_tokens}")
print(f"Total Token: {response.usage.total_tokens}")

# 估算成本（以 OpenAI 为例）
cost = (
    response.usage.prompt_tokens / 1000 * 0.01 +  # $10/1M tokens
    response.usage.completion_tokens / 1000 * 0.03  # $30/1M tokens
)
print(f"估算成本：${cost:.4f}")
```

---

## 8. 完整示例

### 8.1 多模型对比

```python
async def compare_models(prompt: str):
    """多模型对比"""
    models = [
        ("OpenAI GPT-4o", create_executor(provider="openai", model="gpt-4o")),
        ("Anthropic Claude", create_executor(provider="anthropic")),
        ("Ollama Llama3", create_executor(provider="ollama", model="llama3.1")),
    ]
    
    messages = [Message.user(prompt)]
    
    for name, executor in models:
        start = time.time()
        response = await executor.execute(messages)
        elapsed = time.time() - start
        
        print(f"\n{name} ({elapsed:.2f}s):")
        print(f"  {response.content[:100]}...")
```

### 8.2 成本优化路由

```python
class CostAwareRouter:
    """成本感知路由器"""
    
    def __init__(self):
        self.cheap_executor = create_executor(provider="ollama", model="llama3.1")
        self.expensive_executor = create_executor(provider="openai", model="gpt-4o")
    
    async def execute(self, messages: list[Message]) -> LLMResponse:
        # 简单问题用便宜模型
        if self._is_simple_query(messages):
            return await self.cheap_executor.execute(messages)
        
        # 复杂问题用昂贵模型
        return await self.expensive_executor.execute(messages)
    
    def _is_simple_query(self, messages: list[Message]) -> bool:
        """判断是否是简单查询"""
        last_message = messages[-1].content
        return len(last_message) < 50 and "?" not in last_message
```

---

## 9. 总结

LLM 后端支持的核心功能：

1. **多后端支持**: OpenAI, Anthropic, Ollama 等
2. **路由和故障转移**: 自动选择最佳后端
3. **流式输出**: 实时响应
4. **Tool Calling**: 调用外部工具
5. **统计监控**: Token 使用和成本追踪

---

**下一篇**: [核心 API](../06-api/01-core-api.md)

**上一篇**: [内存优化](03-memory-optimization.md)
