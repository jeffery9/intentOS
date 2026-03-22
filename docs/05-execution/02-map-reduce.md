# Map/Reduce 分布式数据处理

> Map/Reduce 是一种分布式数据处理模式，在 IntentOS 中用于处理大规模数据集，支持内存优化和磁盘溢出。

---

## 1. 概述

### 1.1 什么是 Map/Reduce

**Map/Reduce** 是一种编程模型，用于大规模数据集的并行处理：

- **Map**: 将输入数据分片处理，生成中间键值对
- **Shuffle**: 按 key 分组（相同 key 的数据聚集在一起）
- **Reduce**: 聚合每组数据，生成最终结果

### 1.2 执行流程

```
输入数据
   │
   ▼
┌─────────────────────────────────────────┐
│  Map 阶段                               │
│  ┌─────┐  ┌─────┐  ┌─────┐            │
│  │Map 1│  │Map 2│  │Map 3│  ...       │
│  └──┬──┘  └──┬──┘  └──┬──┘            │
│     │        │        │                │
│     └────────┼────────┘                │
│              ▼                          │
│     中间键值对 (key, value)              │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│  Shuffle 阶段                           │
│  按 key 分组：                           │
│  "hello": [1, 1, 1]                     │
│  "world": [1, 1]                        │
│  "python": [1, 1]                       │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│  Reduce 阶段                            │
│  ┌─────┐  ┌─────┐  ┌─────┐            │
│  │Red 1│  │Red 2│  │Red 3│  ...       │
│  └──┬──┘  └──┬──┘  └──┬──┘            │
│     │        │        │                │
│     ▼        ▼        ▼                │
│   结果 1   结果 2   结果 3              │
└─────────────────────────────────────────┘
   │
   ▼
最终结果
```

### 1.3 适用场景

| 场景 | 说明 | 示例 |
|------|------|------|
| **词频统计** | 统计文本中单词出现次数 | Word Count |
| **数据聚合** | 按维度汇总数据 | 销售汇总 |
| **倒排索引** | 构建搜索引擎索引 | 文档索引 |
| **日志分析** | 分析日志中的模式 | 错误统计 |

---

## 2. Map/Reduce 定义

### 2.1 任务结构

```python
@dataclass
class MapReduceTask:
    """Map/Reduce 任务"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    
    # Map 函数：输入 -> 中间键值对
    map_func: Callable[[Any], Iterator[tuple[str, Any]]] = None
    
    # Reduce 函数：键 + 值列表 -> 输出
    reduce_func: Callable[[str, list[Any]], Any] = None
    
    # 可选的组合函数（本地预聚合）
    combine_func: Optional[Callable[[str, list[Any]], list[Any]]] = None
    
    # 输入数据
    input_data: list[Any] = field(default_factory=list)
    
    # 配置
    num_mappers: int = 4       # Map 任务数
    num_reducers: int = 2      # Reduce 任务数
    chunk_size: int = 1000     # 每个 Map 处理的数据量
    
    # 内存管理
    spill_to_disk: bool = True  # 内存不足时溢出到磁盘
    max_memory_per_task: int = 1024 * 1024 * 1024  # 1GB
    
    # 状态
    status: str = "pending"
    progress: float = 0.0
    result: Any = None
```

### 2.2 创建任务

```python
from intentos import create_map_reduce_task

# Word Count 示例
def map_func(doc):
    """Map: 将文档拆分为 (word, 1)"""
    for word in doc.split():
        yield (word.lower(), 1)

def reduce_func(key, values):
    """Reduce: 累加计数"""
    return sum(values)

# 创建任务
task = create_map_reduce_task(
    name="word_count",
    map_func=map_func,
    reduce_func=reduce_func,
    input_data=["hello world", "hello python", "world python"],
    num_mappers=2,
    num_reducers=2,
    chunk_size=100,
)
```

---

## 3. 执行引擎

### 3.1 执行器定义

```python
class MapReduceExecutor:
    """Map/Reduce 执行器"""
    
    def __init__(
        self,
        memory_manager: MemoryManager = None,
        num_workers: int = 4,
        temp_dir: str = "/tmp",
    ):
        self.memory_manager = memory_manager or MemoryManager()
        self.num_workers = num_workers
        self.temp_dir = temp_dir
    
    async def execute(self, task: MapReduceTask) -> Any:
        """执行 Map/Reduce 任务"""
        task.status = "running"
        start_time = time.time()
        
        try:
            # Map 阶段
            shuffle = DistributedShuffle(
                num_partitions=task.num_reducers,
                temp_dir=self.temp_dir,
            )
            
            async for key, value in self._execute_map(task):
                await shuffle.add(key, value)
            
            task.progress = 50.0
            
            # Reduce 阶段
            results = await self._execute_reduce(task, shuffle)
            
            task.progress = 100.0
            task.status = "completed"
            task.result = results
            
            # 清理
            await shuffle.cleanup()
            
            return results
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            raise
        
        finally:
            elapsed = time.time() - start_time
            logger.info(f"Map/Reduce 任务完成：{task.name}, 耗时：{elapsed:.2f}s")
```

### 3.2 Map 阶段

```python
async def _execute_map(
    self,
    task: MapReduceTask,
) -> AsyncIterator[tuple[str, Any]]:
    """执行 Map 阶段"""
    input_data = task.input_data
    
    # 分块处理
    for i in range(0, len(input_data), task.chunk_size):
        chunk = input_data[i:i + task.chunk_size]
        
        # 检查内存
        if self.memory_manager.get_level() == MemoryLevel.CRITICAL:
            await self.memory_manager.force_gc()
        
        # 处理 chunk
        for item in chunk:
            try:
                # 调用 Map 函数
                results = task.map_func(item)
                for result in results:
                    yield result
            except Exception as e:
                logger.error(f"Map 处理失败：{e}")
        
        # 释放 chunk 内存
        del chunk
        
        # 更新进度
        task.progress = (i + len(chunk)) / len(input_data) * 50  # Map 占 50%
```

### 3.3 Reduce 阶段

```python
async def _execute_reduce(
    self,
    task: MapReduceTask,
    shuffle: DistributedShuffle,
) -> dict[str, Any]:
    """执行 Reduce 阶段"""
    grouped_data = defaultdict(list)
    
    # 从 Shuffle 获取分组数据
    async for key, values in shuffle.get_all():
        grouped_data[key].extend(values)
    
    # 执行 Reduce
    results = {}
    total_keys = len(grouped_data)
    
    for i, (key, values) in enumerate(grouped_data.items()):
        # 可选的 Combine（本地预聚合）
        if task.combine_func:
            values = task.combine_func(key, values)
        
        # Reduce
        try:
            result = task.reduce_func(key, values)
            results[key] = result
        except Exception as e:
            logger.error(f"Reduce 失败：{key}, 错误：{e}")
            results[key] = None
        
        # 更新进度
        task.progress = 50 + ((i + 1) / total_keys) * 50  # Reduce 占 50%
    
    return results
```

---

## 4. Shuffle 实现

### 4.1 分布式 Shuffle

```python
class DistributedShuffle:
    """分布式 Shuffle"""
    
    def __init__(
        self,
        num_partitions: int = 4,
        spill_threshold_bytes: int = 100 * 1024 * 1024,  # 100MB
        temp_dir: str = "/tmp",
    ):
        self.num_partitions = num_partitions
        self.spill_threshold = spill_threshold_bytes
        self.temp_dir = temp_dir
        
        self._partitions: dict[int, dict[str, list[Any]]] = defaultdict(lambda: defaultdict(list))
        self._partition_sizes: dict[int, int] = defaultdict(int)
        self._spill_files: list[str] = []
    
    async def add(self, key: str, value: Any) -> None:
        """添加键值对到分区"""
        # 计算分区
        partition_id = self._get_partition(key)
        
        # 添加到分区
        self._partitions[partition_id][key].append(value)
        self._partition_sizes[partition_id] += self._get_size(value)
        
        # 检查是否需要溢出
        if self._partition_sizes[partition_id] > self.spill_threshold:
            await self._spill_partition(partition_id)
    
    async def get_partition(self, partition_id: int) -> dict[str, list[Any]]:
        """获取分区数据"""
        if partition_id in self._partitions:
            return dict(self._partitions[partition_id])
        
        # 从磁盘加载
        return await self._load_partition(partition_id)
    
    async def get_all(self) -> AsyncIterator[tuple[str, list[Any]]]:
        """获取所有分组数据"""
        # 内存中的数据
        for partition_id, partition in self._partitions.items():
            for key, values in partition.items():
                yield (key, values)
            self._partitions[partition_id].clear()
        
        # 磁盘上的数据
        for spill_file in self._spill_files:
            async for key, values in self._load_spill_file(spill_file):
                yield (key, values)
```

### 4.2 分区策略

```python
def _get_partition(self, key: str) -> int:
    """计算键的分区 ID"""
    # 使用 MD5 哈希确保均匀分布
    hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
    return hash_value % self.num_partitions
```

### 4.3 磁盘溢出

```python
async def _spill_partition(self, partition_id: int) -> None:
    """溢出分区到磁盘"""
    if partition_id not in self._partitions:
        return
    
    data = self._partitions[partition_id]
    spill_path = os.path.join(
        self.temp_dir,
        f"shuffle_{partition_id}_{uuid.uuid4()}.json",
    )
    
    # 异步写入磁盘
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: self._write_spill_file(spill_path, data),
    )
    
    self._spill_files.append(spill_path)
    del self._partitions[partition_id]
    self._partition_sizes[partition_id] = 0

def _write_spill_file(self, path: str, data: dict) -> None:
    """写入溢出文件"""
    with open(path, 'w') as f:
        json.dump({k: v for k, v in data.items()}, f)
```

---

## 5. 内存优化

### 5.1 流式处理

```python
class MemoryAwareExecutor:
    """内存感知执行器"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
    
    async def execute_map(
        self,
        map_func: Callable,
        input_data: list,
        chunk_size: int = 100,
    ) -> AsyncIterator[tuple[str, Any]]:
        """流式 Map 执行"""
        for i in range(0, len(input_data), chunk_size):
            chunk = input_data[i:i + chunk_size]
            
            # 检查内存
            if self.memory_manager.get_level() == MemoryLevel.CRITICAL:
                collected = await self.memory_manager.force_gc()
                logger.info(f"GC 回收：{collected} 对象")
            
            # 处理 chunk
            for item in chunk:
                try:
                    results = map_func(item)
                    for result in results:
                        yield result
                except Exception as e:
                    logger.error(f"Map 失败：{e}")
            
            # 释放 chunk 内存
            del chunk
            
            # 定期 GC
            if i % (chunk_size * 10) == 0:
                gc.collect()
```

### 5.2 分批 Reduce

```python
async def execute_reduce(
    self,
    reduce_func: Callable,
    grouped_data: dict[str, list[Any]],
    batch_size: int = 100,
) -> dict[str, Any]:
    """分批 Reduce 执行"""
    results = {}
    items = list(grouped_data.items())
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        # 检查内存
        if self.memory_manager.get_level() == MemoryLevel.CRITICAL:
            await self.memory_manager.force_gc()
        
        for key, values in batch:
            try:
                result = reduce_func(key, values)
                results[key] = result
            except Exception as e:
                logger.error(f"Reduce 失败：{key}, 错误：{e}")
                results[key] = None
            
            # 释放内存
            del values
        
        del batch
        gc.collect()
    
    return results
```

---

## 6. 完整示例

### 6.1 Word Count

```python
from intentos import create_map_reduce_executor, create_map_reduce_task

# 输入数据
documents = [
    "hello world hello",
    "world peace world",
    "hello python world",
    "python is great python",
    "great world great",
] * 100  # 放大数据

# Map 函数
def map_func(doc):
    for word in doc.split():
        yield (word.lower(), 1)

# Reduce 函数
def reduce_func(key, values):
    return sum(values)

# 创建任务
task = create_map_reduce_task(
    name="word_count",
    map_func=map_func,
    reduce_func=reduce_func,
    input_data=documents,
    num_mappers=4,
    num_reducers=4,
    chunk_size=10,
)

# 执行
executor = create_map_reduce_executor(max_memory_mb=50)
results = await executor.execute(task)

# 查看结果
print("词频统计结果:")
for word, count in sorted(results.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {word}: {count}")
```

### 6.2 销售数据聚合

```python
# 输入数据：销售记录
sales_records = [
    {"region": "华东", "product": "A", "amount": 1000},
    {"region": "华东", "product": "B", "amount": 1500},
    {"region": "华南", "product": "A", "amount": 800},
    {"region": "华南", "product": "B", "amount": 1200},
    {"region": "华北", "product": "A", "amount": 600},
] * 100

# Map: 按区域分组
def map_func(record):
    region = record["region"]
    yield (region, {"amount": record["amount"], "count": 1})

# Reduce: 聚合
def reduce_func(key, values):
    total_amount = sum(v["amount"] for v in values)
    total_count = sum(v["count"] for v in values)
    return {
        "region": key,
        "total_amount": total_amount,
        "total_count": total_count,
        "avg_amount": total_amount / total_count if total_count > 0 else 0,
    }

# 创建任务
task = create_map_reduce_task(
    name="sales_aggregation",
    map_func=map_func,
    reduce_func=reduce_func,
    input_data=sales_records,
    num_reducers=4,
)

# 执行
executor = create_map_reduce_executor(max_memory_mb=30)
results = await executor.execute(task)

# 查看结果
print("销售数据聚合结果:")
for region, data in sorted(results.items()):
    print(f"  {data['region']}: 金额={data['total_amount']:,}, "
          f"数量={data['total_count']}, 均价={data['avg_amount']:.2f}")
```

### 6.3 日志分析

```python
# 输入数据：日志行
log_lines = [
    "INFO [api] Request processed",
    "ERROR [db] Connection failed",
    "WARN [api] Rate limit exceeded",
    "ERROR [api] Timeout",
    "INFO [web] Page loaded",
] * 1000

# Map: 按级别 + 服务分组
def map_func(line):
    parts = line.split()
    level = parts[0]
    service = parts[1].strip("[]")
    key = f"{service}_{level}"
    yield (key, 1)

# Reduce: 计数
def reduce_func(key, values):
    return {"count": sum(values), "level": key.split("_")[1], "service": key.split("_")[0]}

# 创建任务
task = create_map_reduce_task(
    name="log_analysis",
    map_func=map_func,
    reduce_func=reduce_func,
    input_data=log_lines,
    num_reducers=8,
)

# 执行
executor = create_map_reduce_executor(max_memory_mb=30)
results = await executor.execute(task)

# 查看结果
print("日志分析结果:")
for key, value in sorted(results.items()):
    print(f"  {key}: {value['count']} 条")
```

---

## 7. 总结

Map/Reduce 的核心价值：

1. **分布式处理**: 大规模数据并行处理
2. **内存优化**: 流式处理和磁盘溢出
3. **灵活配置**: Map/Reduce 函数可自定义
4. **容错处理**: 单个任务失败不影响整体

---

## 附录 A: 分布式 Map/Reduce

### A.1 分布式执行器

```python
class DistributedMapReduceExecutor(MapReduceExecutor):
    """分布式 Map/Reduce 执行器"""

    async def run_mappers(self, task: MapReduceTask) -> list:
        """在多个节点上并行运行 Map 任务"""
        # 分割输入数据
        splits = self.split_input(task.input_data, task.input_splits)

        # 选择节点
        nodes = await self.select_nodes(len(splits))

        # 分布式执行
        tasks = [
            self.run_mapper_on_node(node, task.map_function, split, task.map_params)
            for node, split in zip(nodes, splits)
        ]
        results = await asyncio.gather(*tasks)

        return results

    async def run_mapper_on_node(
        self,
        node_id: str,
        map_function: str,
        data: list,
        params: dict,
    ) -> list:
        """在指定节点上运行单个 Map 任务"""
        url = f"http://{node_id}:8080/map"
        payload = {
            "function": map_function,
            "data": data,
            "params": params,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                return await resp.json()
```

### A.2 应用场景

**场景 1: 大规模数据处理**
```python
# 分析 1TB 销售数据
task = MapReduceTask(
    name="sales_analysis",
    map_function="analyze_sales_map",
    reduce_function="aggregate_sales_reduce",
    input_data=load_data_from_s3("s3://bucket/sales-2025"),
    input_splits=1000,  # 分成 1000 个分片
    num_mappers=100,
    num_reducers=20,
)
result = await distributed_executor.execute(task)
```

**场景 2: 日志分析**
```python
# 分析 1 亿条日志
log_lines = load_logs("s3://logs/2025-*.gz")  # 1 亿条

task = MapReduceTask(
    name="log_analysis",
    map_func=lambda line: (extract_level(line), 1),
    reduce_func=lambda k, v: {"count": sum(v)},
    input_data=log_lines,
    num_mappers=500,
    num_reducers=50,
)
result = await distributed_executor.execute(task)
```

---

## 参考文档

- [分布式架构](../02-architecture/04-distributed-architecture.md)
- [DAG 执行引擎](01-dag-engine.md)
- [内存优化](03-memory-optimization.md)
