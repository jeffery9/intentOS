# 分布式架构

> IntentOS 本质是 Cloud-Native 的，支持分布式执行和记忆同步。

---

## 1. 为什么需要分布式

### 1.1 需求驱动

| 需求 | 说明 | 示例 |
|------|------|------|
| **性能** | 单个 LLM 无法满足高并发 | 黑五大促期间 |
| **成本** | 多模型路由优化成本 | 简单任务用小模型 |
| **容错** | 单点故障影响可用性 | 某模型宕机 |
| **合规** | 数据本地化要求 | GDPR 数据不出境 |

### 1.2 Cloud-Native 类比

| Cloud-Native | IntentGarden |
|-------------|-------------|
| Kubernetes Pod | Prompt Executable |
| YAML Manifest | PEF (YAML/JSON) |
| kubectl apply | garden.execute() |
| Controller Manager | Planning Layer |
| Scheduler | Execution Layer |
| Admission Controller | Safety Ring |
| HPA | Ops Model (自修复) |
| Service Mesh | Capability Binding |

---

## 2. 分布式执行

### 2.1 执行模式

```python
# 顺序执行
await executor.execute(dag, mode=ExecutionMode.SEQUENTIAL)

# 并行执行
await executor.execute(dag, mode=ExecutionMode.PARALLEL)

# 分布式执行
await executor.execute(dag, mode=ExecutionMode.DISTRIBUTED)
```

### 2.2 DAG 并行执行

```python
# 任务 DAG
dag = DAG(name="sales_analysis")

# 独立任务（可并行）
dag.add_task(Task(id="t1", capability="query_east"))
dag.add_task(Task(id="t2", capability="query_south"))
dag.add_task(Task(id="t3", capability="query_north"))

# 聚合任务（依赖 t1, t2, t3）
dag.add_task(Task(
    id="t4",
    capability="aggregate",
    depends_on=["t1", "t2", "t3"]
))

# 并行执行
# t1, t2, t3 同时执行
# t4 等待 t1, t2, t3 完成后执行
```

### 2.3 执行流程

```
┌─────────────────────────────────────────────────────────────┐
│  1. 解析 DAG                                                 │
│     • 拓扑排序                                               │
│     • 识别可并行任务                                         │
└───────────────┬─────────────────────────────────────────────┘
                ↓
┌───────────────▼─────────────────────────────────────────────┐
│  2. 任务调度                                                 │
│     • 创建任务队列                                           │
│     • 分配执行节点                                           │
└───────────────┬─────────────────────────────────────────────┘
                ↓
┌───────────────▼─────────────────────────────────────────────┐
│  3. 并行执行                                                 │
│     • 无依赖任务并发执行                                     │
│     • 有依赖任务等待依赖完成                                 │
└───────────────┬─────────────────────────────────────────────┘
                ↓
┌───────────────▼─────────────────────────────────────────────┐
│  4. 结果聚合                                                 │
│     • 收集所有任务结果                                       │
│     • 合并为最终结果                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Map/Reduce 模式

### 3.1 定义

**Map/Reduce** 是一种分布式数据处理模式：

- **Map**: 将输入数据分片处理，生成中间键值对
- **Shuffle**: 按 key 分组
- **Reduce**: 聚合每组数据

### 3.2 示例：Word Count

```python
# 输入
documents = ["hello world", "hello python", "world python"]

# Map
def map_func(doc):
    for word in doc.split():
        yield (word, 1)

# Map 输出
# ("hello", 1), ("world", 1)
# ("hello", 1), ("python", 1)
# ("world", 1), ("python", 1)

# Shuffle
# "hello": [1, 1]
# "world": [1, 1]
# "python": [1, 1]

# Reduce
def reduce_func(key, values):
    return sum(values)

# 最终结果
# {"hello": 2, "world": 2, "python": 2}
```

### 3.3 实现

```python
from intentos import create_map_reduce_executor

executor = create_map_reduce_executor(max_memory_mb=50)

task = create_map_reduce_task(
    name="word_count",
    map_func=map_func,
    reduce_func=reduce_func,
    input_data=documents,
    num_mappers=4,
    num_reducers=2,
)

results = await executor.execute(task)
```

---

## 4. 内存优化

### 4.1 流式处理

避免一次性加载所有数据：

```python
async def execute_map(map_func, input_data, chunk_size=100):
    """流式 Map 执行"""
    for i in range(0, len(input_data), chunk_size):
        chunk = input_data[i:i + chunk_size]
        
        # 处理 chunk
        for item in chunk:
            results = map_func(item)
            for result in results:
                yield result
        
        # 释放 chunk 内存
        del chunk
        
        # 定期 GC
        if i % (chunk_size * 10) == 0:
            gc.collect()
```

### 4.2 磁盘溢出

当内存不足时溢出到磁盘：

```python
class DistributedShuffle:
    def __init__(self, spill_threshold_mb=100):
        self.spill_threshold = spill_threshold_mb * 1024 * 1024
        self._partitions = defaultdict(list)
        self._spill_files = []
    
    async def add(self, key, value):
        partition_id = hash(key) % num_partitions
        self._partitions[partition_id].append(value)
        
        # 检查是否需要溢出
        if self._get_partition_size(partition_id) > self.spill_threshold:
            await self._spill_partition(partition_id)
    
    async def _spill_partition(self, partition_id):
        """溢出分区到磁盘"""
        data = self._partitions[partition_id]
        path = f"/tmp/shuffle_{partition_id}_{uuid.uuid4()}.json"
        
        with open(path, 'w') as f:
            json.dump(data, f)
        
        self._spill_files.append(path)
        del self._partitions[partition_id]
```

### 4.3 内存感知执行

```python
class MemoryAwareExecutor:
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
    
    async def execute_map(self, map_func, input_data):
        for item in input_data:
            # 检查内存
            if self.memory_manager.get_level() == MemoryLevel.CRITICAL:
                await self.memory_manager.force_gc()
            
            # 处理
            for result in map_func(item):
                yield result
```

---

## 5. 分布式记忆同步

### 5.1 记忆分层

| 类型 | 存储 | 同步 |
|------|------|------|
| **工作记忆** | 进程内 | 无 |
| **短期记忆** | 内存 (LRU) | 可选 Redis |
| **长期记忆** | Redis/文件 | 分布式同步 |

### 5.2 Redis 同步机制

```python
class DistributedMemoryManager:
    async def _start_sync(self):
        """启动分布式同步"""
        # 订阅其他节点的更新
        task = asyncio.create_task(self._sync_listener())
        self._sync_subscribers.append(task)
    
    async def _sync_listener(self):
        """监听同步消息"""
        async for message in self.redis.subscribe("sync"):
            if message["node_id"] != self.node_id:
                # 来自其他节点的更新
                entry = MemoryEntry.from_dict(message["entry"])
                await self._long_term_backend.set(entry)
    
    async def _queue_sync(self, entry, scope):
        """将记忆加入同步队列"""
        await self.pending_sync.put({
            "node_id": self.node_id,
            "scope": scope,
            "entry": entry.to_dict(),
            "timestamp": time.time(),
        })
        
        # 发布到 Redis
        await self.redis.publish("sync", message)
```

### 5.3 多节点架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Node 1                                   │
│  ┌─────────────┐                                            │
│  │  Memory     │────┐                                       │
│  │  Manager    │    │                                       │
│  └─────────────┘    │                                       │
│                     │                                       │
└─────────────────────┼───────────────────────────────────────┘
                      │                                       │
                   ┌──▼───┐                                  │
                   │ Redis│                                  │
                   │ Pub/Sub│                                 │
                   └──┬───┘                                  │
                      │                                       │
┌─────────────────────┼───────────────────────────────────────┐
│                     │                                       │
│  ┌─────────────┐    │                                       │
│  │  Memory     │◄───┘                                       │
│  │  Manager    │                                            │
│  └─────────────┘                                            │
│                     Node 2                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. 多 LLM 后端路由

### 6.1 路由策略

| 策略 | 说明 | 适用场景 |
|------|------|---------|
| **优先级** | 按优先级选择后端 | 主备模式 |
| **轮询** | 轮流选择后端 | 负载均衡 |
| **加权** | 按权重随机选择 | 异构节点 |
| **延迟** | 选择延迟最低的后端 | 性能敏感 |
| **成本** | 选择成本最低的后端 | 成本敏感 |

### 6.2 故障转移

```python
class LLMRouter:
    async def generate(self, messages, tools=None):
        last_error = None
        
        for attempt in range(len(self.backends)):
            try:
                # 选择后端
                name, backend = self.select_backend(strategy="priority")
                
                # 生成响应
                response = await backend.generate(messages, tools)
                
                # 记录成功
                self.stats[name].record_success(response)
                return response
                
            except (RateLimitError, TimeoutError) as e:
                # 可重试的错误，尝试下一个后端
                last_error = e
                continue
        
        # 所有后端都失败
        raise LLMError(f"所有后端都失败：{last_error}")
```

### 6.3 配置示例

```python
from intentos import create_router, BackendConfig

router = create_router([
    BackendConfig(
        name="primary",
        model="gpt-4o",
        api_key=os.environ.get("OPENAI_API_KEY"),
        priority=10,
        max_qps=100,
    ),
    BackendConfig(
        name="backup",
        model="claude-3-5-sonnet",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        priority=5,
    ),
    BackendConfig(
        name="local",
        model="llama3.1",
        base_url="http://localhost:11434",
        priority=1,
    ),
])

# 自动故障转移
response = await router.generate(messages)
```

---

## 7. 总结

IntentOS 的分布式架构特征：

1. **DAG 并行执行**: 无依赖任务并发执行
2. **Map/Reduce 模式**: 大数据处理
3. **内存优化**: 流式处理 + 磁盘溢出
4. **记忆同步**: Redis Pub/Sub
5. **多 LLM 路由**: 故障转移 + 负载均衡

---

**下一篇**: [意图编译器架构](../03-compiler/01-compiler-architecture.md)

**上一篇**: [Self-Bootstrap](03-self-bootstrap.md)
