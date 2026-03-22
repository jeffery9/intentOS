# 分布式架构

> **分布式语义 VM · 运行时 Agent · 集群自愈**

**文档版本**: 2.0 (增强版)  
**最后更新**: 2026-03-22

---

## 目录

1. [为什么需要分布式](#1-为什么需要分布式)
2. [分布式内核架构](#2-分布式内核架构)
3. [运行时 Agent](#3-运行时-agent)
4. [语义进程管理](#4-语义进程管理)
5. [分布式执行](#5-分布式执行)
6. [Map/Reduce 模式](#6-mapreduce 模式)
7. [分布式记忆同步](#7-分布式记忆同步)
8. [多 LLM 后端路由](#8-多-llm 后端路由)
9. [部署与运维](#9-部署与运维)
10. [总结](#10-总结)

---

## 1. 为什么需要分布式

### 1.1 需求驱动

| 需求 | 说明 | 示例 |
|------|------|------|
| **性能** | 单个 LLM 无法满足高并发 | 黑五大促期间 |
| **成本** | 多模型路由优化成本 | 简单任务用小模型 |
| **容错** | 单点故障影响可用性 | 某模型宕机 |
| **合规** | 数据本地化要求 | GDPR 数据不出境 |
| **扩展** | 弹性扩缩容 | 自动添加节点 |

### 1.2 Cloud-Native 类比

| Cloud-Native | IntentOS |
|-------------|----------|
| Kubernetes Pod | Prompt Executable (PEF) |
| YAML Manifest | PEF (YAML/JSON) |
| kubectl apply | `executor.execute()` |
| Controller Manager | Planning Layer |
| Scheduler | Execution Layer |
| Admission Controller | Safety Ring |
| HPA | Ops Model (自修复) |
| Service Mesh | Capability Binding |
| Node.js Worker | Runtime Agent |

### 1.3 分布式架构全景

```
┌─────────────────────────────────────────────────────────────────┐
│                    用户/应用层                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  REST API   │  │  Chat UI    │  │  SDK        │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
└─────────┼────────────────┼────────────────┼────────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
          ┌────────────────▼────────────────┐
          │     Load Balancer / API Gateway │
          └────────────────┬────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
┌────────▼────────┐ ┌──────▼──────┐ ┌────────▼────────┐
│  Runtime Agent  │ │  Runtime    │ │  Runtime        │
│  Node 1         │ │  Agent      │ │  Agent          │
│  ┌───────────┐  │ │  Node 2     │ │  Node 3         │
│  │Semantic VM│  │ │  ┌───────┐  │ │  ┌───────────┐  │
│  └───────────┘  │ │  │SVM    │  │ │  │Semantic VM│  │
│  ┌───────────┐  │ │  └───────┘  │ │  └───────────┘  │
│  │  Memory   │  │ │  ┌───────┐  │ │  ┌───────────┐  │
│  │  Manager  │  │ │  │Memory │  │ │  │  Memory   │  │
│  └───────────┘  │ │  │Manager│  │ │  │  Manager  │  │
│                 │ │  └───────┘  │ │  └───────────┘  │
└────────┬────────┘ └──────┬──────┘ └────────┬────────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
┌────────▼────────┐ ┌──────▼──────┐ ┌────────▼────────┐
│  Redis Cluster  │ │  PostgreSQL │ │  LLM Gateway    │
│  (记忆同步)      │ │  (持久化)    │ │  (多模型路由)    │
└─────────────────┘ └─────────────┘ └─────────────────┘
```

---

## 2. 分布式内核与进程管理

IntentOS 采用了类似微内核的分布式设计，每个节点运行一个 `VMServer` 并通过 `DistributedCoordinator` 进行全局调度。

### 2.1 核心组件

| 组件 | 说明 |
|------|------|
| **VMNode** | 计算节点，运行一个独立的语义虚拟机实例 |
| **VMServer** | 节点的 RPC 接口（基于 aiohttp），处理内存读写和程序执行 |
| **DistributedCoordinator** | 内核调度器，管理全局进程表（Process Table） |
| **Consistent Hash Ring** | 一致性哈希环，负责将意图数据和程序分布到不同节点 |

### 2.2 语义进程 (Semantic Process)

每个执行的语义程序在内核中被抽象为一个 **SemanticProcess (PCB)**：

- **PID**: 进程唯一标识符 (UUID)
- **State**: 进程状态（NEW, RUNNING, SUSPENDED, COMPLETED, FAILED, ZOMBIE）
- **PC**: 程序计数器，实时记录执行到的指令行号
- **NodeID**: 执行该进程的目标节点 ID
- **Context**: 进程私有的变量空间和执行堆栈

### 2.3 进程生命周期 (Fork/Exec)

内核通过 `fork_process` 机制实现程序的派生：
1. **Fork**: 创建一个新的 PCB 并分配 PID。
2. **Schedule**: 协调器根据节点负载 (Load) 选择最优计算节点。
3. **Dispatch**: 通过 RPC 将程序镜像分发到目标节点。
4. **Track**: 节点定期汇报 PC 进度，协调器更新全局进程表。
5. **Reap**: 进程结束后自动回收资源（清理僵尸进程）。

---

## 3. 分布式执行

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

## 10. 总结

IntentOS 的分布式架构特征：

1. **DAG 并行执行**: 无依赖任务并发执行
2. **Map/Reduce 模式**: 大数据处理
3. **内存优化**: 流式处理 + 磁盘溢出
4. **记忆同步**: Redis Pub/Sub
5. **多 LLM 路由**: 故障转移 + 负载均衡

---

## 附录 A: 运行时 Agent 完整职责

### A.1 为什么需要运行时 Agent

**问题**: IntentOS 是分布式 OS，语义 VM 运行在多个节点（容器/主机）上，跨网络组成整体 OS。如何管理每个节点的本地资源和能力？

**基于第一性原理的分析**:

**第一性原理 1：分布式语义 VM**
- 语义 VM 在每个节点上运行
- 多个语义 VM 跨网络通信，组成整体 OS
- 运行时 Agent 在每个节点上，为本地语义 VM 提供能力
- ✅ **结论**：运行时 Agent 是分布式 OS 的节点基础设施，为本地语义 VM 提供服务

**第一性原理 2：能力与执行分离**
- 语义 VM：定义能力（语义描述），执行 PEF
- 运行时 Agent：提供能力的具体实现（本地 shell、文件系统等）
- ✅ **结论**：运行时 Agent 是能力的提供者，语义 VM 是能力的使用者

**第一性原理 3：按需加载**
- 语义 VM：PEF 包含能力引用
- 运行时 Agent：按需下载/缓存 Skill，提供能力实现
- ✅ **结论**：运行时 Agent 管理能力的生命周期（下载、缓存、供应）

### A.2 Runtime Agent 的 6 大职责

**职责 1：为本地语义 VM 提供能力**
```python
class RuntimeAgent:
    def __init__(self, node_id, semantic_vm):
        self.node_id = node_id
        self.semantic_vm = semantic_vm
        self.local_capabilities = {
            "shell": ShellCapability(),
            "filesystem": FileSystemCapability(),
            "network": NetworkCapability(),
        }
        self.register_capabilities()

    def register_capabilities(self):
        for cap_id, cap in self.local_capabilities.items():
            self.semantic_vm.registry.register(
                id=cap_id,
                description=cap.description,
                handler=cap.execute,
            )
```

**职责 2：App 分发和缓存**
```python
class RuntimeAgent:
    def __init__(self, node_id, app_cache_dir):
        self.node_id = node_id
        self.app_cache_dir = app_cache_dir
        self.app_instances = {}

    async def on_startup(self):
        # 节点启动时预加载常用 App
        await self.download_apps(["data_analyst", "code_generator"])

    async def get_app(self, app_id, version=None):
        cache_key = f"{app_id}:{version or 'latest'}"
        if cache_key not in self.app_instances:
            app_package = await self.download_app(app_id, version)
            app_instance = await self.compile_app(app_package)
            self.app_instances[cache_key] = app_instance
        return self.app_instances[cache_key]
```

**职责 3：分布式执行（Map-Reduce）**
```python
class RuntimeAgent:
    async def map_reduce(self, pef, data_partitions):
        # Map 阶段：分发任务
        tasks = []
        for node_id, partition in data_partitions.items():
            task = self.send_to_node(node_id, pef, partition)
            tasks.append(task)

        # 等待所有任务完成
        results = await asyncio.gather(*tasks)

        # Reduce 阶段：汇总结果（使用 LLM 生成自然语言摘要）
        summary = await self.llm.summarize(results)
        return summary
```

**职责 4：Skill 缓存和下载**
```python
class RuntimeAgent:
    async def load_skill(self, skill_id):
        cache_path = self.skill_cache_dir / f"{skill_id}.skill"

        # 检查缓存
        if not cache_path.exists():
            await self.download_skill(skill_id, cache_path)

        # 加载 Skill
        skill = await self.parse_skill(cache_path)
        return skill
```

**职责 5：结果汇总（LLM 汇总）**
```python
class RuntimeAgent:
    async def aggregate_results(self, results: list[dict]) -> dict:
        prompt = f"""
        请汇总以下分布式节点的执行结果：
        {json.dumps(results, indent=2, ensure_ascii=False)}
        请提供：
        1. 总体执行状态
        2. 各节点结果摘要
        3. 关键发现和洞察
        4. 建议的后续操作
        """
        response = await self.llm.generate(prompt)
        return {
            "summary": response,
            "detailed_results": results,
        }
```

**职责 6：跨节点通信**
```python
class RuntimeAgent:
    async def send_to_node(self, node_id: str, pef: dict, data: dict) -> dict:
        url = f"http://{node_id}:8080/execute"
        payload = {"pef": pef, "data": data}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                return await resp.json()

    async def broadcast(self, message: dict, nodes: list[str]):
        tasks = [self.send_to_node(node, message, {}) for node in nodes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
```

### A.3 Runtime Agent 部署配置

**Docker Compose 部署**:
```yaml
version: '3.8'
services:
  runtime-agent-1:
    build: .
    environment:
      - NODE_ID=node1
      - CLUSTER_NODES=node2,node3
      - REDIS_URL=redis://redis:6379
    ports:
      - "8081:8080"
    volumes:
      - ./app_cache:/app/cache
      - ./skills:/app/skills

  runtime-agent-2:
    build: .
    environment:
      - NODE_ID=node2
      - CLUSTER_NODES=node1,node3
      - REDIS_URL=redis://redis:6379
    ports:
      - "8082:8080"
    volumes:
      - ./app_cache:/app/cache
      - ./skills:/app/skills

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

**Kubernetes 部署**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: runtime-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: runtime-agent
  template:
    metadata:
      labels:
        app: runtime-agent
    spec:
      containers:
      - name: runtime-agent
        image: intentos/runtime-agent:latest
        env:
        - name: NODE_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: CLUSTER_NODES
          value: "runtime-agent-0,runtime-agent-1,runtime-agent-2"
        - name: REDIS_URL
          value: "redis://redis-master:6379"
        ports:
        - containerPort: 8080
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
```

---

## 附录 B: 语义进程管理 (PCB)

### B.1 语义进程控制块

```python
@dataclass
class SemanticProcess:
    """语义进程控制块 (PCB)"""
    # 进程标识
    pid: str = field(default_factory=lambda: str(uuid.uuid4()))
    ppid: Optional[str] = None  # 父进程 ID
    name: str = ""

    # 进程状态
    state: ProcessState = ProcessState.NEW
    # NEW, RUNNING, SUSPENDED, COMPLETED, FAILED, ZOMBIE

    # 执行信息
    pc: int = 0  # 程序计数器 (指令行号)
    node_id: Optional[str] = None  # 执行节点
    pef: Optional[dict] = None  # 程序镜像

    # 上下文
    context: dict = field(default_factory=dict)  # 变量空间
    stack: list = field(default_factory=list)  # 执行堆栈

    # 资源
    memory_usage: int = 0  # 内存使用 (字节)
    cpu_time: float = 0.0  # CPU 时间 (秒)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

    # 结果
    result: Optional[dict] = None
    error: Optional[str] = None
```

### B.2 进程状态机

```
                    ┌─────────┐
                    │   NEW   │
                    └────┬────┘
                         │ fork()
                         ▼
                    ┌─────────┐
         ┌─────────│ RUNNING │─────────┐
         │         └────┬────┘         │
         │              │              │
    suspend()       complete()     fail()
         │              │              │
         ▼              ▼              ▼
    ┌─────────┐   ┌───────────┐  ┌────────┐
    │SUSPENDED│   │ COMPLETED │  │ FAILED │
    └────┬────┘   └─────┬─────┘  └───┬────┘
         │             │            │
    resume()      reap()       reap()
         │             │            │
         └─────────────┴────────────┘
                       │
                       ▼
                    ┌────────┐
                    │ ZOMBIE │
                    └───┬────┘
                        │ cleanup()
                        ▼
                    (销毁)
```

### B.3 进程生命周期 (Fork/Exec)

**步骤 1: Fork - 创建进程**
```python
async def fork_process(self, pef: dict, parent_pid: Optional[str] = None) -> str:
    pcb = SemanticProcess(ppid=parent_pid, name=pef.get("name", "anonymous"), pef=pef)
    self.process_table[pcb.pid] = pcb
    return pcb.pid
```

**步骤 2: Schedule - 调度节点**
```python
async def schedule_node(self, pcb: SemanticProcess) -> str:
    node_loads = await self.get_node_loads()
    best_node = min(node_loads, key=node_loads.get)
    pcb.node_id = best_node
    return best_node
```

**步骤 3: Dispatch - 分发程序**
```python
async def dispatch_program(self, pcb: SemanticProcess, node_id: str):
    url = f"http://{node_id}:8080/execute"
    payload = {"pid": pcb.pid, "pef": pcb.pef, "context": pcb.context}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            return await resp.json()
```

**步骤 4: Track - 跟踪进度**
```python
async def track_progress(self, pid: str):
    while True:
        pcb = self.process_table.get(pid)
        if not pcb: break
        pc = await self.get_process_pc(pid)
        pcb.pc = pc
        if pc >= len(pcb.pef.get("instructions", [])):
            pcb.state = ProcessState.COMPLETED
            break
        await asyncio.sleep(0.1)
```

**步骤 5: Reap - 回收资源**
```python
async def reap_process(self, pid: str):
    pcb = self.process_table.get(pid)
    if not pcb: return
    while pcb.state not in [ProcessState.COMPLETED, ProcessState.FAILED]:
        await asyncio.sleep(0.1)
    pcb.state = ProcessState.ZOMBIE
    pcb.end_time = time.time()
    await self.cleanup_process(pid)
```

---

## 附录 C: 故障转移与自动扩缩容

### C.1 故障转移

```python
class DistributedExecutor:
    async def execute_with_failover(self, dag: dict, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                primary_node = await self.select_primary_node()
                result = await self.execute_on_node(primary_node, dag)
                return result
            except NodeUnavailableError as e:
                await self.mark_node_unavailable(e.node_id)
                backup_node = await self.select_backup_node()
                if attempt < max_retries - 1:
                    logger.warning(f"节点 {e.node_id} 故障，切换到 {backup_node}")
                    continue
                else:
                    raise
        raise ExecutionError("所有重试失败")
```

### C.2 自动扩缩容

```python
class AutoScaler:
    async def scale_based_on_load(self):
        while True:
            avg_load = await self.get_average_cluster_load()
            if avg_load > 80:
                await self.scale_up()
                logger.info(f"集群负载 {avg_load}%，已扩容")
            elif avg_load < 30:
                await self.scale_down()
                logger.info(f"集群负载 {avg_load}%，已缩容")
            await asyncio.sleep(60)
```

---

## 参考文档

- [Map/Reduce 数据处理](../05-execution/02-map-reduce.md)
- [分布式记忆同步](../04-memory/02-distributed-sync.md)
- [Self-Bootstrap 完整架构](../SELF_BOOTSTRAP_COMPLETE.md)
- [部署指南](../DEPLOYMENT_GUIDE.md)
- [性能优化策略](../PERFORMANCE_OPTIMIZATION.md)
