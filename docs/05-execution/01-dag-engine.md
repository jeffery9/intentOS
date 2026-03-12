# DAG 执行引擎

> DAG（有向无环图）是 IntentOS 中任务执行的基本结构，支持并行执行、依赖管理和错误处理。

---

## 1. 概述

### 1.1 什么是 DAG

**DAG (Directed Acyclic Graph)** 是有向无环图，在 IntentOS 中用于表示任务的执行顺序和依赖关系。

```
    ┌─────┐
    │ T1  │  查询华东销售
    └──┬──┘
       │
    ┌──▼──┐     ┌─────┐
    │ T2  │────>│ T4  │  聚合分析
    └──┬──┘     └──┬──┘
       │           │
    ┌──▼──┐     ┌──▼──┐
    │ T3  │────>│ T5  │  生成报告
    └─────┘     └─────┘
    
    T1: 查询华东销售
    T2: 查询华南销售
    T3: 查询去年同期
    T4: 对比分析 (依赖 T1, T2, T3)
    T5: 生成报告 (依赖 T4)
```

### 1.2 DAG 的优势

| 优势 | 说明 | 示例 |
|------|------|------|
| **并行执行** | 无依赖任务可同时执行 | T1, T2, T3 可并行 |
| **依赖管理** | 明确任务执行顺序 | T4 等待 T1,T2,T3 完成 |
| **错误隔离** | 单个任务失败不影响其他 | T1 失败不影响 T2 |
| **可观测性** | 清晰的执行流程 | 可视化执行图 |

---

## 2. DAG 定义

### 2.1 任务节点

```python
@dataclass
class Task:
    """任务节点"""
    id: str                    # 唯一标识
    name: str                  # 任务名称
    capability: str            # 能力名称
    params: dict = field(default_factory=dict)  # 参数
    depends_on: list[str] = field(default_factory=list)  # 依赖
    condition: str = None      # 执行条件
    output_var: str = None     # 输出变量名
    priority: int = 5          # 优先级 (1-10)
    timeout_seconds: int = 300 # 超时时间
    retry_count: int = 3       # 重试次数
    status: TaskStatus = TaskStatus.PENDING
```

### 2.2 DAG 结构

```python
@dataclass
class DAG:
    """有向无环图"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    tasks: dict[str, Task] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)
    
    def add_task(self, task: Task) -> None:
        """添加任务"""
        self.tasks[task.id] = task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)
```

### 2.3 创建 DAG

```python
from intentos import DAG, Task, create_task

# 方法 1: 使用 dataclass
dag = DAG(name="sales_analysis")

dag.add_task(Task(
    id="step1",
    name="查询华东销售",
    capability="query_sales",
    params={"region": "华东", "period": "Q3"},
))

dag.add_task(Task(
    id="step2",
    name="查询华南销售",
    capability="query_sales",
    params={"region": "华南", "period": "Q3"},
    depends_on=["step1"],  # 依赖 step1
))

# 方法 2: 使用便捷函数
dag = create_dag(name="sales_analysis")

dag.add_task(create_task(
    id="step1",
    name="查询华东销售",
    capability="query_sales",
    params={"region": "华东"},
))

dag.add_task(create_task(
    id="step2",
    name="分析趋势",
    capability="analyze",
    depends_on=["step1"],
    output_var="analysis_result",
))
```

---

## 3. 拓扑排序

### 3.1 算法实现

```python
def get_topological_order(self) -> list[str]:
    """获取拓扑排序"""
    in_degree = {
        task_id: len(task.depends_on)
        for task_id, task in self.tasks.items()
    }
    
    # 入度为 0 的任务
    queue = [
        task_id for task_id, degree in in_degree.items()
        if degree == 0
    ]
    
    result = []
    
    while queue:
        task_id = queue.pop(0)
        result.append(task_id)
        
        # 更新依赖此任务的任务
        for other_id, other_task in self.tasks.items():
            if task_id in other_task.depends_on:
                in_degree[other_id] -= 1
                if in_degree[other_id] == 0:
                    queue.append(other_id)
    
    # 检查循环依赖
    if len(result) != len(self.tasks):
        raise ValueError("检测到循环依赖")
    
    return result
```

### 3.2 使用示例

```python
dag = create_dag(name="test")
dag.add_task(create_task(id="t1", name="T1", capability="c1"))
dag.add_task(create_task(id="t2", name="T2", capability="c2", depends_on=["t1"]))
dag.add_task(create_task(id="t3", name="T3", capability="c3", depends_on=["t1"]))
dag.add_task(create_task(id="t4", name="T4", capability="c4", depends_on=["t2", "t3"]))

# 拓扑排序
order = dag.get_topological_order()
print(order)  # ["t1", "t2", "t3", "t4"] 或 ["t1", "t3", "t2", "t4"]
```

---

## 4. 执行引擎

### 4.1 执行器定义

```python
class DAGExecutor:
    """DAG 执行器"""
    
    def __init__(
        self,
        max_concurrency: int = 10,
        capability_registry: IntentRegistry = None,
    ):
        self.max_concurrency = max_concurrency
        self.registry = capability_registry
        self._results: dict[str, TaskResult] = {}
        self._semaphore = asyncio.Semaphore(max_concurrency)
    
    async def execute(self, dag: DAG) -> dict[str, TaskResult]:
        """执行 DAG"""
        # 验证 DAG
        errors = dag.validate()
        if errors:
            raise ValueError(f"DAG 验证失败：{errors}")
        
        # 获取拓扑顺序
        order = dag.get_topological_order()
        
        # 执行任务
        completed = set()
        
        for task_id in order:
            task = dag.get_task(task_id)
            
            # 检查依赖
            if not all(dep in completed for dep in task.depends_on):
                # 等待依赖完成
                await self._wait_for_dependencies(task)
            
            # 检查条件
            if task.condition and not self._evaluate_condition(task.condition):
                task.status = TaskStatus.CANCELLED
                completed.add(task_id)
                continue
            
            # 执行任务
            result = await self._execute_task(task)
            self._results[task_id] = result
            completed.add(task_id)
        
        return self._results
```

### 4.2 并行执行

```python
async def execute_parallel(self, dag: DAG) -> dict[str, TaskResult]:
    """并行执行 DAG"""
    completed = set()
    failed = set()
    
    async def execute_with_semaphore(task: Task) -> None:
        async with self._semaphore:
            # 等待依赖
            while not all(dep in completed for dep in task.depends_on):
                if any(dep in failed for dep in task.depends_on):
                    # 依赖失败，取消此任务
                    task.status = TaskStatus.CANCELLED
                    completed.add(task.id)
                    failed.add(task.id)
                    return
                await asyncio.sleep(0.01)
            
            # 执行任务
            task.status = TaskStatus.RUNNING
            result = await self._execute_task(task)
            self._results[task.id] = result
            
            if result.status == TaskStatus.FAILED:
                task.status = TaskStatus.FAILED
                completed.add(task.id)
                failed.add(task.id)
            else:
                task.status = TaskStatus.COMPLETED
                completed.add(task.id)
    
    # 创建所有任务
    tasks = [
        execute_with_semaphore(task)
        for task in dag.tasks.values()
    ]
    
    await asyncio.gather(*tasks)
    
    return self._results
```

---

## 5. 错误处理

### 5.1 重试机制

```python
async def _execute_with_retry(self, task: Task) -> TaskResult:
    """带重试的执行"""
    last_error = None
    
    for attempt in range(task.retry_count + 1):
        try:
            return await self._execute_task_impl(task)
        except Exception as e:
            last_error = e
            
            if attempt < task.retry_count:
                # 指数退避
                wait_time = 2 ** attempt
                logger.warning(
                    f"任务 {task.id} 失败，{wait_time}秒后重试 ({attempt+1}/{task.retry_count})"
                )
                await asyncio.sleep(wait_time)
    
    # 所有重试失败
    return TaskResult(
        task_id=task.id,
        status=TaskStatus.FAILED,
        error=f"执行失败：{last_error}",
    )
```

### 5.2 超时处理

```python
async def _execute_with_timeout(self, task: Task) -> TaskResult:
    """带超时的执行"""
    try:
        async with asyncio.timeout(task.timeout_seconds):
            return await self._execute_with_retry(task)
    except asyncio.TimeoutError:
        return TaskResult(
            task_id=task.id,
            status=TaskStatus.FAILED,
            error=f"执行超时 ({task.timeout_seconds}秒)",
        )
```

### 5.3 错误传播

```python
async def execute_with_error_propagation(self, dag: DAG) -> dict[str, TaskResult]:
    """带错误传播的执行"""
    results = await self.execute_parallel(dag)
    
    # 检查是否有失败的任务
    failed_tasks = [
        task_id for task_id, result in results.items()
        if result.status == TaskStatus.FAILED
    ]
    
    if failed_tasks:
        # 找到失败的任务（没有失败依赖的）
        root_failures = []
        for task_id in failed_tasks:
            task = dag.get_task(task_id)
            if not any(dep in failed_tasks for dep in task.depends_on):
                root_failures.append(task_id)
        
        logger.error(f"根因失败任务：{root_failures}")
    
    return results
```

---

## 6. 进度追踪

### 6.1 进度结构

```python
@dataclass
class ExecutionProgress:
    """执行进度"""
    dag_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    running_tasks: int
    pending_tasks: int
    started_at: float
    estimated_remaining_seconds: float = 0.0
    
    @property
    def progress_percent(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100
```

### 6.2 进度更新

```python
class DAGExecutor:
    def __init__(self):
        self._progress = None
        self._start_time = 0
    
    async def execute(self, dag: DAG) -> dict[str, TaskResult]:
        self._start_time = time.time()
        self._progress = ExecutionProgress(
            dag_id=dag.id,
            total_tasks=len(dag.tasks),
            completed_tasks=0,
            failed_tasks=0,
            running_tasks=0,
            pending_tasks=len(dag.tasks),
            started_at=self._start_time,
        )
        
        # 执行过程中更新进度
        # ...
        
        return self._results
    
    def _update_progress(self, task_id: str, status: TaskStatus) -> None:
        """更新进度"""
        if status == TaskStatus.COMPLETED:
            self._progress.completed_tasks += 1
            self._progress.pending_tasks -= 1
        elif status == TaskStatus.FAILED:
            self._progress.failed_tasks += 1
            self._progress.pending_tasks -= 1
        elif status == TaskStatus.RUNNING:
            self._progress.running_tasks += 1
            self._progress.pending_tasks -= 1
        
        # 估算剩余时间
        if self._progress.completed_tasks > 0:
            elapsed = time.time() - self._start_time
            avg_time = elapsed / self._progress.completed_tasks
            self._progress.estimated_remaining_seconds = (
                avg_time * self._progress.pending_tasks
            )
    
    def get_progress(self) -> Optional[ExecutionProgress]:
        """获取进度"""
        return self._progress
```

---

## 7. 完整示例

### 7.1 销售分析 DAG

```python
from intentos import DAG, Task, create_dag, create_task, DAGExecutor

# 创建 DAG
dag = create_dag(name="sales_analysis")

# 添加任务
dag.add_task(create_task(
    id="query_east",
    name="查询华东销售",
    capability="query_sales",
    params={"region": "华东", "period": "Q3"},
    output_var="east_data",
))

dag.add_task(create_task(
    id="query_south",
    name="查询华南销售",
    capability="query_sales",
    params={"region": "华南", "period": "Q3"},
    output_var="south_data",
    depends_on=["query_east"],  # 可并行，这里演示依赖
))

dag.add_task(create_task(
    id="analyze",
    name="分析趋势",
    capability="analyze_trends",
    params={
        "east": "${east_data}",
        "south": "${south_data}",
    },
    depends_on=["query_east", "query_south"],
    output_var="analysis",
))

dag.add_task(create_task(
    id="report",
    name="生成报告",
    capability="generate_report",
    params={"data": "${analysis}", "format": "pdf"},
    depends_on=["analyze"],
))

# 执行
executor = DAGExecutor(
    max_concurrency=5,
    capability_registry=registry,
)

results = await executor.execute(dag)

# 查看结果
for task_id, result in results.items():
    print(f"{task_id}: {result.status} - {result.result}")

# 查看进度
progress = executor.get_progress()
print(f"进度：{progress.progress_percent:.1f}%")
print(f"预计剩余：{progress.estimated_remaining_seconds:.1f}秒")
```

### 7.2 并行优化

```python
# 修改 DAG 为并行执行
dag = create_dag(name="sales_analysis_parallel")

# 这三个任务可以并行执行
dag.add_task(create_task(id="query_east", ...))
dag.add_task(create_task(id="query_south", ...))
dag.add_task(create_task(id="query_north", ...))

# 聚合任务等待所有查询完成
dag.add_task(create_task(
    id="aggregate",
    name="聚合分析",
    capability="aggregate",
    depends_on=["query_east", "query_south", "query_north"],
))

# 并行执行
executor = DAGExecutor(max_concurrency=10)
results = await executor.execute_parallel(dag)

# 原本需要 3 个查询的时间，现在只需要 1 个查询的时间
```

---

## 8. 总结

DAG 执行引擎的核心功能：

1. **拓扑排序**: 确定执行顺序
2. **并行执行**: 无依赖任务并发执行
3. **错误处理**: 重试、超时、错误传播
4. **进度追踪**: 实时进度和剩余时间估算

---

**下一篇**: [Map/Reduce](02-map-reduce.md)

**上一篇**: [过期策略](../04-memory/04-expiry-policy.md)
