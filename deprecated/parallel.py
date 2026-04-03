"""
并行和分布式执行引擎

支持:
- DAG 任务并行执行
- 分布式节点通信
- 任务分片和结果聚合
- 执行监控和进度追踪
"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Callable, Optional


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"     # 顺序执行
    PARALLEL = "parallel"         # 并行执行
    DISTRIBUTED = "distributed"   # 分布式执行


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    start_time: float = 0.0
    end_time: float = 0.0
    node_id: Optional[str] = None

    @property
    def duration_ms(self) -> int:
        if self.end_time and self.start_time:
            return int((self.end_time - self.start_time) * 1000)
        return 0

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "node_id": self.node_id,
        }


@dataclass
class Task:
    """
    任务定义
    DAG 中的节点
    """
    id: str
    name: str
    capability: str
    params: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    condition: Optional[str] = None  # 执行条件
    output_var: Optional[str] = None  # 输出变量名
    priority: int = 5  # 优先级 (1-10)
    timeout_seconds: int = 300
    retry_count: int = 3
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[TaskResult] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "capability": self.capability,
            "params": self.params,
            "depends_on": self.depends_on,
            "condition": self.condition,
            "output_var": self.output_var,
            "priority": self.priority,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "status": self.status.value,
        }


@dataclass
class DAG:
    """
    有向无环图 (DAG)
    任务依赖关系图
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    tasks: dict[str, Task] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)  # 共享变量

    def add_task(self, task: Task) -> None:
        """添加任务"""
        self.tasks[task.id] = task

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)

    def get_ready_tasks(self, completed_tasks: set[str]) -> list[Task]:
        """获取所有依赖已满足的任务"""
        ready = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                deps_met = all(dep in completed_tasks for dep in task.depends_on)
                if deps_met:
                    ready.append(task)
        # 按优先级排序
        return sorted(ready, key=lambda t: -t.priority)

    def get_topological_order(self) -> list[str]:
        """获取拓扑排序"""
        in_degree = {task_id: len(task.depends_on) for task_id, task in self.tasks.items()}
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            task_id = queue.pop(0)
            result.append(task_id)

            for other_id, other_task in self.tasks.items():
                if task_id in other_task.depends_on:
                    in_degree[other_id] -= 1
                    if in_degree[other_id] == 0:
                        queue.append(other_id)

        # 检查是否有循环依赖 (结果数量少于任务数量)
        if len(result) != len(self.tasks):
            raise ValueError("检测到循环依赖")

        return result

    def validate(self) -> list[str]:
        """验证 DAG 有效性"""
        errors = []

        # 检查依赖是否存在
        for task in self.tasks.values():
            for dep in task.depends_on:
                if dep not in self.tasks:
                    errors.append(f"任务 '{task.id}' 依赖不存在的任务 '{dep}'")

        # 检查循环依赖
        try:
            self.get_topological_order()
        except Exception:
            errors.append("检测到循环依赖")

        return errors

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "tasks": {tid: t.to_dict() for tid, t in self.tasks.items()},
            "variables": self.variables,
        }


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

    def to_dict(self) -> dict:
        return {
            "dag_id": self.dag_id,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "running_tasks": self.running_tasks,
            "pending_tasks": self.pending_tasks,
            "progress_percent": self.progress_percent,
            "estimated_remaining_seconds": self.estimated_remaining_seconds,
        }


class TaskScheduler:
    """
    任务调度器
    负责优先级队列和任务分配
    """

    def __init__(self, max_concurrency: int = 10):
        self.max_concurrency = max_concurrency
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._running: dict[str, asyncio.Task] = {}
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def submit(self, task: Task, priority: int = 5) -> None:
        """提交任务到队列"""
        # 优先级数字越小优先级越高
        await self._queue.put((-priority, task.id, task))

    async def get_next(self) -> Optional[Task]:
        """获取下一个任务"""
        try:
            _, _, task = await asyncio.wait_for(self._queue.get(), timeout=0.1)
            return task
        except asyncio.TimeoutError:
            return None

    def is_full(self) -> bool:
        """检查是否已满"""
        return len(self._running) >= self.max_concurrency


class ExecutionNode:
    """
    执行节点
    可以是本地或远程节点
    """

    def __init__(
        self,
        node_id: str,
        capabilities: list[str],
        is_local: bool = True,
        endpoint: Optional[str] = None,
    ):
        self.node_id = node_id
        self.capabilities = set(capabilities)
        self.is_local = is_local
        self.endpoint = endpoint  # 远程节点端点
        self.status = "idle"  # idle, busy, offline
        self.current_tasks: list[str] = []
        self.stats = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "avg_duration_ms": 0,
        }

    def can_execute(self, capability: str) -> bool:
        """检查是否能执行指定能力"""
        return capability in self.capabilities

    def assign_task(self, task_id: str) -> None:
        """分配任务"""
        self.current_tasks.append(task_id)
        self.status = "busy"

    def release_task(self, task_id: str, success: bool, duration_ms: int) -> None:
        """释放任务"""
        if task_id in self.current_tasks:
            self.current_tasks.remove(task_id)

        self.stats["total_tasks"] += 1
        if success:
            self.stats["successful_tasks"] += 1
        else:
            self.stats["failed_tasks"] += 1

        # 更新平均耗时
        n = self.stats["total_tasks"]
        self.stats["avg_duration_ms"] = (
            (self.stats["avg_duration_ms"] * (n - 1) + duration_ms) / n
        )

        if not self.current_tasks:
            self.status = "idle"


class DistributedExecutor:
    """
    分布式执行器
    管理多个执行节点
    """

    def __init__(self):
        self.nodes: dict[str, ExecutionNode] = {}
        self._task_results: dict[str, TaskResult] = {}
        self._callbacks: dict[str, list[Callable]] = defaultdict(list)

    def register_node(self, node: ExecutionNode) -> None:
        """注册节点"""
        self.nodes[node.node_id] = node

    def unregister_node(self, node_id: str) -> None:
        """注销节点"""
        if node_id in self.nodes:
            del self.nodes[node_id]

    def select_node(self, capability: str) -> Optional[ExecutionNode]:
        """选择能执行指定能力的节点"""
        available = [
            node for node in self.nodes.values()
            if node.can_execute(capability) and node.status == "idle"
        ]

        if not available:
            return None

        # 选择最空闲的节点 (按当前任务数和平均耗时)
        return min(available, key=lambda n: (
            len(n.current_tasks),
            n.stats["avg_duration_ms"],
        ))

    async def execute_on_node(
        self,
        node: ExecutionNode,
        task: Task,
        executor_func: Callable,
    ) -> TaskResult:
        """在节点上执行任务"""
        start_time = time.time()
        node.assign_task(task.id)

        try:
            task.status = TaskStatus.RUNNING

            # 执行任务
            if node.is_local:
                result = await executor_func(task)
            else:
                result = await self._execute_remote(node, task)

            end_time = time.time()
            success = result.status == TaskStatus.COMPLETED

            node.release_task(task.id, success, result.duration_ms)

            return result

        except Exception as e:
            end_time = time.time()
            node.release_task(task.id, False, int((end_time - start_time) * 1000))

            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error=str(e),
                start_time=start_time,
                end_time=end_time,
                node_id=node.node_id,
            )

    async def _execute_remote(self, node: ExecutionNode, task: Task) -> TaskResult:
        """远程执行 (简化实现)"""
        # 实际实现应该通过 HTTP/gRPC 调用远程节点
        raise NotImplementedError("远程执行暂未实现")

    def on_task_complete(self, task_id: str, callback: Callable) -> None:
        """注册任务完成回调"""
        self._callbacks[task_id].append(callback)

    def _notify_callbacks(self, task_id: str, result: TaskResult) -> None:
        """通知回调"""
        for callback in self._callbacks.get(task_id, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(result))
                else:
                    callback(result)
            except Exception:
                pass


class ParallelDAGExecutor:
    """
    并行 DAG 执行器

    支持:
    - 拓扑排序执行
    - 并行执行无依赖任务
    - 进度追踪
    - 错误处理和重试
    """

    def __init__(
        self,
        max_concurrency: int = 10,
        distributed_executor: Optional[DistributedExecutor] = None,
    ):
        self.max_concurrency = max_concurrency
        self.distributed = distributed_executor or DistributedExecutor()
        self._results: dict[str, TaskResult] = {}
        self._progress: Optional[ExecutionProgress] = None
        self._start_time: float = 0

    async def execute(
        self,
        dag: DAG,
        executor_func: Callable,
        mode: ExecutionMode = ExecutionMode.PARALLEL,
    ) -> dict[str, TaskResult]:
        """
        执行 DAG

        Args:
            dag: DAG 定义
            executor_func: 任务执行函数 (task) -> result
            mode: 执行模式

        Returns:
            任务结果字典
        """
        # 验证 DAG
        errors = dag.validate()
        if errors:
            raise ValueError(f"DAG 验证失败：{errors}")

        self._start_time = time.time()
        self._results = {}

        # 初始化进度
        self._progress = ExecutionProgress(
            dag_id=dag.id,
            total_tasks=len(dag.tasks),
            completed_tasks=0,
            failed_tasks=0,
            running_tasks=0,
            pending_tasks=len(dag.tasks),
            started_at=self._start_time,
        )

        if mode == ExecutionMode.SEQUENTIAL:
            await self._execute_sequential(dag, executor_func)
        elif mode == ExecutionMode.PARALLEL:
            await self._execute_parallel(dag, executor_func)
        elif mode == ExecutionMode.DISTRIBUTED:
            await self._execute_distributed(dag, executor_func)

        return self._results

    async def _execute_sequential(self, dag: DAG, executor_func: Callable) -> None:
        """顺序执行"""
        completed: set[str] = set()

        for task_id in dag.get_topological_order():
            task = dag.get_task(task_id)
            if not task:
                continue

            # 检查条件
            if task.condition and not self._evaluate_condition(task.condition, self._results):
                task.status = TaskStatus.CANCELLED
                completed.add(task_id)
                continue

            result = await executor_func(task)
            self._results[task_id] = result
            completed.add(task_id)

            if result.status == TaskStatus.FAILED:
                self._progress.failed_tasks += 1
            else:
                self._progress.completed_tasks += 1

    async def _execute_parallel(self, dag: DAG, executor_func: Callable) -> None:
        """并行执行"""
        completed: set[str] = set()
        failed: set[str] = set()
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def execute_task(task: Task) -> None:
            async with semaphore:
                # 检查条件
                if task.condition and not self._evaluate_condition(task.condition, self._results):
                    task.status = TaskStatus.CANCELLED
                    completed.add(task.id)
                    self._progress.pending_tasks -= 1
                    return

                # 等待依赖
                while not all(dep in completed for dep in task.depends_on):
                    # 检查是否有依赖失败
                    if any(dep in failed for dep in task.depends_on):
                        task.status = TaskStatus.CANCELLED
                        completed.add(task.id)
                        failed.add(task.id)
                        self._progress.pending_tasks -= 1
                        return
                    await asyncio.sleep(0.01)

                # 执行任务
                task.status = TaskStatus.RUNNING
                self._progress.running_tasks += 1
                self._progress.pending_tasks -= 1

                result = await executor_func(task)
                self._results[task.id] = result

                self._progress.running_tasks -= 1
                if result.status == TaskStatus.FAILED:
                    task.status = TaskStatus.FAILED
                    completed.add(task.id)
                    failed.add(task.id)
                    self._progress.failed_tasks += 1
                else:
                    task.status = TaskStatus.COMPLETED
                    completed.add(task.id)
                    self._progress.completed_tasks += 1

        # 创建所有任务
        tasks = [execute_task(task) for task in dag.tasks.values()]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_distributed(self, dag: DAG, executor_func: Callable) -> None:
        """分布式执行"""
        completed: set[str] = set()
        failed: set[str] = set()

        async def execute_on_best_node(task: Task) -> None:
            # 等待依赖
            while not all(dep in completed for dep in task.depends_on):
                if any(dep in failed for dep in task.depends_on):
                    task.status = TaskStatus.CANCELLED
                    completed.add(task.id)
                    failed.add(task.id)
                    self._progress.pending_tasks -= 1
                    return
                await asyncio.sleep(0.01)

            # 选择最佳节点
            node = self.distributed.select_node(task.capability)

            if not node:
                # 没有可用节点，本地执行
                result = await executor_func(task)
            else:
                result = await self.distributed.execute_on_node(node, task, executor_func)

            self._results[task.id] = result

            if result.status == TaskStatus.FAILED:
                task.status = TaskStatus.FAILED
                completed.add(task.id)
                failed.add(task.id)
                self._progress.failed_tasks += 1
            else:
                task.status = TaskStatus.COMPLETED
                completed.add(task.id)
                self._progress.completed_tasks += 1

        # 创建所有任务
        tasks = [execute_on_best_node(task) for task in dag.tasks.values()]
        await asyncio.gather(*tasks, return_exceptions=True)

    def _evaluate_condition(self, condition: str, results: dict[str, TaskResult]) -> bool:
        """评估条件表达式"""
        if not condition:
            return True

        # 简化实现：支持 exists(var) 语法
        if condition.startswith("exists("):
            var_name = condition[7:-1]
            return var_name in results

        return True

    def get_progress(self) -> Optional[ExecutionProgress]:
        """获取执行进度"""
        if not self._progress:
            return None

        # 估算剩余时间
        elapsed = time.time() - self._start_time
        if self._progress.completed_tasks > 0:
            avg_time = elapsed / self._progress.completed_tasks
            remaining = avg_time * self._progress.pending_tasks
            self._progress.estimated_remaining_seconds = remaining

        return self._progress

    async def progress_stream(self) -> AsyncIterator[ExecutionProgress]:
        """进度流"""
        while self._progress and self._progress.pending_tasks + self._progress.running_tasks > 0:
            yield self.get_progress()
            await asyncio.sleep(0.1)

    def get_results_summary(self) -> dict:
        """获取结果摘要"""
        return {
            "total_tasks": len(self._results),
            "successful": sum(1 for r in self._results.values() if r.status == TaskStatus.COMPLETED),
            "failed": sum(1 for r in self._results.values() if r.status == TaskStatus.FAILED),
            "cancelled": sum(1 for r in self._results.values() if r.status == TaskStatus.CANCELLED),
            "total_duration_ms": sum(r.duration_ms for r in self._results.values()),
            "tasks": {tid: r.to_dict() for tid, r in self._results.items()},
        }


# 便捷函数
def create_dag(name: str = "") -> DAG:
    """创建 DAG"""
    return DAG(name=name)


def create_task(
    id: str,
    name: str,
    capability: str,
    params: Optional[dict] = None,
    depends_on: Optional[list[str]] = None,
    **kwargs,
) -> Task:
    """创建任务"""
    return Task(
        id=id,
        name=name,
        capability=capability,
        params=params or {},
        depends_on=depends_on or [],
        **kwargs,
    )


def create_local_node(
    node_id: str,
    capabilities: list[str],
) -> ExecutionNode:
    """创建本地节点"""
    return ExecutionNode(
        node_id=node_id,
        capabilities=capabilities,
        is_local=True,
    )


def create_remote_node(
    node_id: str,
    capabilities: list[str],
    endpoint: str,
) -> ExecutionNode:
    """创建远程节点"""
    return ExecutionNode(
        node_id=node_id,
        capabilities=capabilities,
        is_local=False,
        endpoint=endpoint,
    )
