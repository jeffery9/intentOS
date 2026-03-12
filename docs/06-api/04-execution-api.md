# 执行 API

> 本文档介绍 IntentOS 执行引擎的 API，包括 DAG 执行、Map/Reduce 和 LLM 执行。

---

## 1. DAG 执行引擎

### 1.1 DAGExecutor

DAG 执行器：

```python
from intentos import DAGExecutor, IntentRegistry

# 创建执行器
executor = DAGExecutor(
    max_concurrency=10,
    capability_registry=registry,
)

# 执行 DAG
results = await executor.execute(dag)

# 查看结果
for task_id, result in results.items():
    print(f"{task_id}: {result.status}")
```

### 1.2 DAG

```python
from intentos import DAG, Task, create_dag, create_task

# 创建 DAG
dag = DAG(name="sales_analysis")

# 添加任务
dag.add_task(Task(
    id="step1",
    name="查询华东销售",
    capability="query_sales",
    params={"region": "华东"},
))

dag.add_task(Task(
    id="step2",
    name="分析趋势",
    capability="analyze",
    depends_on=["step1"],
))

# 或使用便捷函数
dag = create_dag(name="analysis")
dag.add_task(create_task(
    id="step1",
    name="查询",
    capability="query",
))

# 获取拓扑顺序
order = dag.get_topological_order()

# 验证 DAG
errors = dag.validate()
```

### 1.3 Task

```python
from intentos import Task, TaskStatus

task = Task(
    id="step1",
    name="查询销售",
    capability="query_sales",
    params={"region": "华东"},
    depends_on=[],
    condition=None,
    output_var="sales_data",
    priority=5,
    timeout_seconds=300,
    retry_count=3,
)

# 属性
print(task.id)              # 任务 ID
print(task.name)            # 任务名称
print(task.capability)      # 能力名称
print(task.params)          # 参数
print(task.depends_on)      # 依赖
print(task.status)          # 状态
```

### 1.4 TaskResult

```python
from intentos import TaskResult, TaskStatus

# 任务结果属性
print(result.task_id)           # 任务 ID
print(result.status)            # 状态
print(result.result)            # 结果
print(result.error)             # 错误信息
print(result.start_time)        # 开始时间
print(result.end_time)          # 结束时间
print(result.duration_ms)       # 耗时 (毫秒)
print(result.node_id)           # 执行节点 ID

# 转换为字典
data = result.to_dict()
```

### 1.5 ExecutionProgress

执行进度：

```python
from intentos import ExecutionProgress

# 获取进度
progress = executor.get_progress()

print(f"总任务数：{progress.total_tasks}")
print(f"已完成：{progress.completed_tasks}")
print(f"失败：{progress.failed_tasks}")
print(f"运行中：{progress.running_tasks}")
print(f"待执行：{progress.pending_tasks}")
print(f"进度：{progress.progress_percent:.1f}%")
print(f"预计剩余：{progress.estimated_remaining_seconds:.1f}秒")
```

---

## 2. Map/Reduce 执行

### 2.1 MapReduceExecutor

```python
from intentos import MapReduceExecutor, MemoryManager

# 创建执行器
memory_manager = MemoryManager(max_memory_mb=100)
executor = MapReduceExecutor(
    memory_manager=memory_manager,
    num_workers=4,
)

# 执行任务
results = await executor.execute(task)
```

### 2.2 MapReduceTask

```python
from intentos import MapReduceTask, create_map_reduce_task

# 创建任务
task = MapReduceTask(
    name="word_count",
    map_func=lambda doc: [(word, 1) for word in doc.split()],
    reduce_func=lambda k, v: sum(v),
    input_data=["hello world", "hello python"],
    num_mappers=4,
    num_reducers=2,
    chunk_size=100,
)

# 或使用便捷函数
task = create_map_reduce_task(
    name="word_count",
    map_func=map_func,
    reduce_func=reduce_func,
    input_data=documents,
)
```

### 2.3 DistributedShuffle

分布式 Shuffle：

```python
from intentos import DistributedShuffle

# 创建 Shuffle
shuffle = DistributedShuffle(
    num_partitions=4,
    spill_threshold_bytes=100 * 1024 * 1024,  # 100MB
)

# 添加数据
await shuffle.add("key1", "value1")
await shuffle.add("key1", "value2")
await shuffle.add("key2", "value3")

# 获取分区
partition = await shuffle.get_partition(0)

# 获取所有数据
async for key, values in shuffle.get_all():
    print(f"{key}: {values}")

# 清理
await shuffle.cleanup()
```

---

## 3. LLM 执行

### 3.1 LLMExecutor

```python
from intentos import LLMExecutor, create_executor

# 创建执行器
executor = create_executor(
    provider="openai",
    api_key="sk-...",
    model="gpt-4o",
    timeout=60,
    max_retries=3,
)

# 执行
from intentos import Message
messages = [
    Message.system("你是助手"),
    Message.user("你好"),
]
response = await executor.execute(messages)

# 带工具调用
from intentos import ToolDefinition
tools = [ToolDefinition(...)]
response = await executor.execute(messages, tools=tools)
```

### 3.2 流式执行

```python
# 流式输出
async for chunk in executor.generate_stream(messages):
    print(chunk, end="", flush=True)
```

### 3.3 LLMResponse

```python
from intentos import LLMResponse, LLMUsage, ToolCall

# 响应属性
print(response.content)              # 内容
print(response.model)                # 模型
print(response.usage.total_tokens)   # Token 使用
print(response.tool_calls)           # 工具调用
print(response.finish_reason)        # 结束原因
print(response.latency_ms)           # 延迟

# Token 使用
usage: LLMUsage = response.usage
print(f"Prompt: {usage.prompt_tokens}")
print(f"Completion: {usage.completion_tokens}")
print(f"Total: {usage.total_tokens}")

# 工具调用
for tc in response.tool_calls:
    print(f"工具：{tc.name}")
    print(f"参数：{tc.arguments}")
```

### 3.4 Message

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

# 属性
print(msg.role)         # 角色
print(msg.content)      # 内容
print(msg.name)         # 名称（工具调用时）
print(msg.tool_call_id) # 工具调用 ID

# 转换为字典
msg_dict = msg.to_dict()
```

### 3.5 ToolDefinition

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

# 转换为 OpenAI 格式
tool_dict = tool.to_dict()
```

---

## 4. LLM 后端

### 4.1 LLMBackend

LLM 后端抽象基类：

```python
from intentos.llm import LLMBackend

# 所有后端都继承自 LLMBackend
# - OpenAIBackend
# - AnthropicBackend
# - OllamaBackend
# - MockBackend
```

### 4.2 OpenAIBackend

```python
from intentos.llm import OpenAIBackend

backend = OpenAIBackend(
    model="gpt-4o",
    api_key="sk-...",
    base_url=None,  # 可选：自定义端点
    timeout=60,
    max_retries=3,
)

# 生成响应
response = await backend.generate(
    messages=[Message.user("你好")],
    temperature=0.7,
    max_tokens=1000,
)
```

### 4.3 AnthropicBackend

```python
from intentos.llm import AnthropicBackend

backend = AnthropicBackend(
    model="claude-3-5-sonnet-20241022",
    api_key="...",
    timeout=60,
)

response = await backend.generate(messages)
```

### 4.4 OllamaBackend

```python
from intentos.llm import OllamaBackend

backend = OllamaBackend(
    model="llama3.1",
    host="http://localhost:11434",
    timeout=120,
)

response = await backend.generate(messages)
```

### 4.5 MockBackend

```python
from intentos.llm import MockBackend

backend = MockBackend(model="mock")
response = await backend.generate(messages)
```

---

## 5. LLM 路由

### 5.1 LLMRouter

```python
from intentos import LLMRouter, BackendConfig, create_router

# 创建路由器
router = create_router([
    BackendConfig(
        name="primary",
        model="gpt-4o",
        api_key="sk-...",
        priority=10,
        weight=1.0,
        max_qps=100,
    ),
    BackendConfig(
        name="backup",
        model="claude-3-5-sonnet",
        api_key="...",
        priority=5,
    ),
])

# 执行（自动故障转移）
response = await router.generate(messages)

# 指定策略
response = await router.generate(messages, strategy="priority")
response = await router.generate(messages, strategy="round_robin")
response = await router.generate(messages, strategy="latency")

# 获取统计
stats = router.get_stats()
for name, s in stats.items():
    print(f"{name}: 成功率={s['success_rate']:.1f}%, "
          f"延迟={s['avg_latency_ms']:.0f}ms")
```

### 5.2 BackendConfig

```python
from intentos import BackendConfig

config = BackendConfig(
    name="primary",
    model="gpt-4o",
    api_key="sk-...",
    base_url=None,
    priority=10,
    weight=1.0,
    max_qps=100,
    enabled=True,
    max_retries=3,
    retry_delay=1.0,
    timeout=60,
)
```

---

## 6. 后端注册

### 6.1 BackendRegistry

```python
from intentos.llm import BackendRegistry

# 注册后端
BackendRegistry.register("custom", CustomBackend)

# 获取后端类
backend_class = BackendRegistry.get("custom")

# 创建后端实例
backend = BackendRegistry.create(
    name="custom",
    model="my-model",
)

# 列出所有后端
backends = BackendRegistry.list_backends()
```

---

## 7. 错误处理

### 7.1 LLM 错误

```python
from intentos.llm import (
    LLMError,
    RateLimitError,
    AuthenticationError,
    TimeoutError,
)

try:
    response = await executor.execute(messages)
except RateLimitError as e:
    print(f"速率限制：{e}")
except AuthenticationError as e:
    print(f"认证失败：{e}")
except TimeoutError as e:
    print(f"超时：{e}")
except LLMError as e:
    print(f"LLM 错误：{e}")
```

### 7.2 执行错误

```python
from intentos import TaskResult, TaskStatus

# 检查任务状态
if result.status == TaskStatus.FAILED:
    print(f"任务失败：{result.error}")
elif result.status == TaskStatus.CANCELLED:
    print(f"任务取消：{result.task_id}")
```

---

## 8. 完整示例

### 8.1 DAG 执行示例

```python
from intentos import create_dag, create_task, DAGExecutor

# 创建 DAG
dag = create_dag(name="sales_analysis")

dag.add_task(create_task(
    id="query_east",
    name="查询华东",
    capability="query_sales",
    params={"region": "华东"},
    output_var="east_data",
))

dag.add_task(create_task(
    id="query_south",
    name="查询华南",
    capability="query_sales",
    params={"region": "华南"},
    output_var="south_data",
))

dag.add_task(create_task(
    id="analyze",
    name="分析",
    capability="analyze",
    depends_on=["query_east", "query_south"],
))

# 执行
executor = DAGExecutor(max_concurrency=10)
results = await executor.execute(dag)

# 查看进度
progress = executor.get_progress()
print(f"进度：{progress.progress_percent:.1f}%")
```

### 8.2 Map/Reduce 示例

```python
from intentos import create_map_reduce_task, create_map_reduce_executor

# Word Count
task = create_map_reduce_task(
    name="word_count",
    map_func=lambda doc: [(word, 1) for word in doc.split()],
    reduce_func=lambda k, v: sum(v),
    input_data=["hello world"] * 1000,
)

executor = create_map_reduce_executor(max_memory_mb=50)
results = await executor.execute(task)

print(results)  # {"hello": 1000, "world": 1000}
```

### 8.3 LLM 路由示例

```python
from intentos import create_router, BackendConfig, Message

# 创建路由器
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
messages = [Message.user("你好")]
response = await router.generate(messages)

# 统计
stats = router.get_stats()
print(stats)
```

---

## 9. 总结

执行 API 分类：

| 类别 | 主要类/函数 |
|------|-----------|
| **DAG 执行** | DAGExecutor, DAG, Task, TaskResult |
| **Map/Reduce** | MapReduceExecutor, MapReduceTask, DistributedShuffle |
| **LLM 执行** | LLMExecutor, Message, ToolDefinition, LLMResponse |
| **LLM 后端** | OpenAIBackend, AnthropicBackend, OllamaBackend |
| **路由** | LLMRouter, BackendConfig, create_router |
| **进度** | ExecutionProgress |
| **错误** | LLMError, RateLimitError, AuthenticationError |

---

**上一篇**: [记忆 API](03-memory-api.md)
