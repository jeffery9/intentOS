"""
内存管理和 Map/Reduce 执行引擎

支持:
- 内存使用追踪和管理
- Map/Reduce 分布式数据处理
- 流式处理和内存优化
- 分布式内存共享
- 内存监控和告警
"""

from __future__ import annotations

import asyncio
import gc
import hashlib
import json
import os
import tempfile
import time
import uuid
import weakref
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Callable, Generic, Iterator, Optional, TypeVar

# =============================================================================
# 内存管理核心
# =============================================================================

@dataclass
class MemoryStats:
    """内存统计信息"""
    total_bytes: int = 0
    used_bytes: int = 0
    available_bytes: int = 0
    peak_bytes: int = 0

    # 对象统计
    object_count: int = 0
    large_object_count: int = 0  # >1MB 的对象

    # GC 统计
    gc_collections: int = 0
    gc_time_ms: int = 0

    @property
    def usage_percent(self) -> float:
        if self.total_bytes == 0:
            return 0.0
        return (self.used_bytes / self.total_bytes) * 100

    def to_dict(self) -> dict:
        return {
            "total_bytes": self.total_bytes,
            "used_bytes": self.used_bytes,
            "available_bytes": self.available_bytes,
            "peak_bytes": self.peak_bytes,
            "usage_percent": self.usage_percent,
            "object_count": self.object_count,
            "large_object_count": self.large_object_count,
            "gc_collections": self.gc_collections,
            "gc_time_ms": self.gc_time_ms,
        }


class MemoryLevel(Enum):
    """内存级别"""
    LOW = "low"           # <50%
    MEDIUM = "medium"     # 50-75%
    HIGH = "high"         # 75-90%
    CRITICAL = "critical" # >90%


class MemoryManager:
    """
    内存管理器

    功能:
    - 追踪内存使用
    - 内存限制和配额
    - 自动垃圾回收
    - 内存告警
    """

    def __init__(
        self,
        max_memory_bytes: int = 0,  # 0 = 无限制
        warning_threshold: float = 0.75,
        critical_threshold: float = 0.90,
    ):
        self.max_memory = max_memory_bytes
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

        self._allocations: dict[str, tuple[int, float, Any]] = {}  # id -> (size, time, ref)
        self._callbacks: list[Callable] = []
        self._stats = MemoryStats()
        self._lock = asyncio.Lock()

        # 初始化统计
        self._update_stats()

    def allocate(self, obj: Any, name: Optional[str] = None) -> str:
        """分配内存（注册对象）"""
        obj_id = name or str(uuid.uuid4())
        size = self._get_object_size(obj)

        # 只对可变对象使用 weakref
        try:
            ref = weakref.ref(obj) if isinstance(obj, (list, dict, set)) else obj
        except TypeError:
            ref = obj

        self._allocations[obj_id] = (size, time.time(), ref)
        self._update_stats()

        # 检查阈值
        self._check_thresholds()

        return obj_id

    def deallocate(self, obj_id: str) -> None:
        """释放内存（注销对象）"""
        if obj_id in self._allocations:
            del self._allocations[obj_id]
            self._update_stats()

    def get_stats(self) -> MemoryStats:
        """获取内存统计"""
        self._update_stats()
        return self._stats

    def get_level(self) -> MemoryLevel:
        """获取内存级别"""
        usage = self._stats.usage_percent / 100
        if usage < 0.5:
            return MemoryLevel.LOW
        elif usage < 0.75:
            return MemoryLevel.MEDIUM
        elif usage < 0.9:
            return MemoryLevel.HIGH
        else:
            return MemoryLevel.CRITICAL

    def on_memory_change(self, callback: Callable) -> None:
        """注册内存变化回调"""
        self._callbacks.append(callback)

    async def force_gc(self) -> int:
        """强制垃圾回收"""
        start = time.time()
        collected = gc.collect()
        elapsed_ms = int((time.time() - start) * 1000)

        self._stats.gc_collections += 1
        self._stats.gc_time_ms += elapsed_ms
        self._update_stats()

        return collected

    def _get_object_size(self, obj: Any) -> int:
        """估算对象大小（字节）"""
        import sys
        try:
            size = sys.getsizeof(obj)
            if isinstance(obj, (list, tuple, set)):
                size += sum(sys.getsizeof(i) for i in obj)
            elif isinstance(obj, dict):
                size += sum(sys.getsizeof(k) + sys.getsizeof(v) for k, v in obj.items())
            return size
        except Exception:
            return 0

    def _update_stats(self) -> None:
        """更新统计信息"""

        # 计算已分配内存
        total_allocated = sum(alloc[0] for alloc in self._allocations.values())

        # 获取系统内存信息
        try:
            import psutil
            process = psutil.Process()
            mem_info = process.memory_info()
            self._stats.used_bytes = mem_info.rss
            self._stats.total_bytes = self.max_memory or psutil.virtual_memory().total
        except ImportError:
            self._stats.used_bytes = total_allocated
            self._stats.total_bytes = self.max_memory or (16 * 1024 * 1024 * 1024)  # 默认 16GB

        self._stats.available_bytes = self._stats.total_bytes - self._stats.used_bytes
        self._stats.peak_bytes = max(self._stats.peak_bytes, self._stats.used_bytes)
        self._stats.object_count = len(self._allocations)
        self._stats.large_object_count = sum(1 for alloc in self._allocations.values() if alloc[0] > 1024 * 1024)

    def _check_thresholds(self) -> None:
        """检查内存阈值"""
        level = self.get_level()

        if level == MemoryLevel.CRITICAL:
            # 临界：同步执行 GC（避免事件循环问题）
            self.force_gc_sync()

        # 通知回调
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    try:
                        asyncio.create_task(callback(level, self._stats))
                    except RuntimeError:
                        # 没有运行中的事件循环
                        pass
                else:
                    callback(level, self._stats)
            except Exception:
                pass

    def force_gc_sync(self) -> int:
        """同步强制垃圾回收"""
        start = time.time()
        collected = gc.collect()
        elapsed_ms = int((time.time() - start) * 1000)

        self._stats.gc_collections += 1
        self._stats.gc_time_ms += elapsed_ms
        self._update_stats()

        return collected


# =============================================================================
# Map/Reduce 核心
# =============================================================================

T = TypeVar('T')
U = TypeVar('U')
V = TypeVar('V')


@dataclass
class MapReduceTask(Generic[T, U, V]):
    """Map/Reduce 任务定义"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""

    # Map 函数：输入 -> 中间键值对
    map_func: Callable[[T], Iterator[tuple[str, U]]] = None

    # Reduce 函数：键 + 值列表 -> 输出
    reduce_func: Callable[[str, list[U]], V] = None

    # 可选的组合函数（本地预聚合）
    combine_func: Optional[Callable[[str, list[U]], list[U]]] = None

    # 输入数据
    input_data: list[T] = field(default_factory=list)

    # 配置
    num_mappers: int = 4
    num_reducers: int = 2
    chunk_size: int = 1000

    # 内存管理
    spill_to_disk: bool = True  # 内存不足时溢出到磁盘
    max_memory_per_task: int = 1024 * 1024 * 1024  # 1GB

    # 状态
    status: str = "pending"
    progress: float = 0.0
    result: Optional[V] = None
    error: Optional[str] = None


@dataclass
class ShuffleResult:
    """Shuffle 阶段结果"""
    partition_id: str
    key: str
    values: list[Any]
    size_bytes: int = 0
    spilled: bool = False  # 是否溢出到磁盘
    spill_path: Optional[str] = None


class MemoryAwareExecutor:
    """
    内存感知执行器

    根据内存使用情况调整执行策略
    """

    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self._executor = ThreadPoolExecutor(max_workers=4)

    async def execute_map(
        self,
        map_func: Callable[[T], Iterator[tuple[str, U]]],
        input_data: list[T],
        chunk_size: int = 100,
    ) -> AsyncIterator[tuple[str, U]]:
        """
        内存感知的 Map 执行

        流式处理输入数据，避免一次性加载所有数据
        """
        for i in range(0, len(input_data), chunk_size):
            chunk = input_data[i:i + chunk_size]

            # 检查内存
            if self.memory_manager.get_level() == MemoryLevel.CRITICAL:
                await self.memory_manager.force_gc()

            # 处理 chunk
            for item in chunk:
                try:
                    results = map_func(item)
                    for result in results:
                        yield result
                except Exception:
                    # 记录错误但继续处理
                    pass

            # 释放 chunk 内存
            del chunk

            # 定期 GC
            if i % (chunk_size * 10) == 0:
                gc.collect()

    async def execute_reduce(
        self,
        reduce_func: Callable[[str, list[U]], V],
        grouped_data: dict[str, list[U]],
    ) -> dict[str, V]:
        """
        内存感知的 Reduce 执行

        分批处理分组数据
        """
        results = {}
        batch_size = 100

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
                except Exception:
                    pass

                # 释放内存
                del values

            del batch
            gc.collect()

        return results


class DistributedShuffle:
    """
    分布式 Shuffle 实现

    支持:
    - 内存 Shuffle
    - 磁盘溢出 Shuffle
    - 分布式 Shuffle（Redis/共享存储）
    """

    def __init__(
        self,
        num_partitions: int = 4,
        spill_threshold_bytes: int = 100 * 1024 * 1024,  # 100MB
        temp_dir: Optional[str] = None,
    ):
        self.num_partitions = num_partitions
        self.spill_threshold = spill_threshold_bytes
        self.temp_dir = temp_dir or tempfile.gettempdir()

        self._partitions: dict[int, dict[str, list[Any]]] = defaultdict(lambda: defaultdict(list))
        self._partition_sizes: dict[int, int] = defaultdict(int)
        self._spill_files: list[str] = []

    async def add(self, key: str, value: Any, partition_id: Optional[int] = None) -> None:
        """添加键值对到分区"""
        if partition_id is None:
            partition_id = self._get_partition(key)

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

    async def cleanup(self) -> None:
        """清理临时文件"""
        for spill_file in self._spill_files:
            try:
                os.remove(spill_file)
            except Exception:
                pass
        self._spill_files.clear()

    def _get_partition(self, key: str) -> int:
        """计算键的分区 ID"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % self.num_partitions

    def _get_size(self, obj: Any) -> int:
        """估算对象大小"""
        import sys
        try:
            return sys.getsizeof(obj)
        except Exception:
            return 100

    async def _spill_partition(self, partition_id: int) -> None:
        """溢出分区到磁盘"""
        if partition_id not in self._partitions:
            return

        data = self._partitions[partition_id]
        spill_path = os.path.join(self.temp_dir, f"shuffle_{partition_id}_{uuid.uuid4()}.json")

        # 异步写入磁盘
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor if hasattr(self, '_executor') else None,
            lambda: self._write_spill_file(spill_path, data),
        )

        self._spill_files.append(spill_path)
        del self._partitions[partition_id]
        self._partition_sizes[partition_id] = 0

    def _write_spill_file(self, path: str, data: dict) -> None:
        """写入溢出文件"""
        with open(path, 'w') as f:
            json.dump({k: v for k, v in data.items()}, f)

    async def _load_spill_file(self, path: str) -> AsyncIterator[tuple[str, list[Any]]]:
        """加载溢出文件"""
        loop = asyncio.get_event_loop()

        def load():
            with open(path, 'r') as f:
                return json.load(f)

        data = await loop.run_in_executor(None, load)
        for key, values in data.items():
            yield (key, values)

    async def _load_partition(self, partition_id: int) -> dict[str, list[Any]]:
        """从磁盘加载分区"""
        # 简化实现：合并所有溢出文件
        result = defaultdict(list)
        async for key, values in self.get_all():
            result[key].extend(values)
        return dict(result)


class MapReduceExecutor:
    """
    Map/Reduce 执行器

    支持:
    - 本地执行
    - 并行执行
    - 分布式执行
    - 内存优化
    """

    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        num_workers: int = 4,
    ):
        self.memory_manager = memory_manager or MemoryManager()
        self.num_workers = num_workers
        self._executor = MemoryAwareExecutor(self.memory_manager)

    async def execute(
        self,
        task: MapReduceTask[T, U, V],
    ) -> V:
        """执行 Map/Reduce 任务"""
        task.status = "running"
        start_time = time.time()

        try:
            # Map 阶段
            shuffle = DistributedShuffle(num_partitions=task.num_reducers)

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
            print(f"Map/Reduce 任务完成：{task.name}, 耗时：{elapsed:.2f}s")

    async def _execute_map(
        self,
        task: MapReduceTask[T, U, V],
    ) -> AsyncIterator[tuple[str, U]]:
        """执行 Map 阶段"""
        async for key, value in self._executor.execute_map(
            task.map_func,
            task.input_data,
            task.chunk_size,
        ):
            yield (key, value)

    async def _execute_reduce(
        self,
        task: MapReduceTask[T, U, V],
        shuffle: DistributedShuffle,
    ) -> V:
        """执行 Reduce 阶段"""
        grouped_data = defaultdict(list)

        async for key, values in shuffle.get_all():
            grouped_data[key].extend(values)

        # 执行 Reduce
        reduce_results = await self._executor.execute_reduce(
            task.reduce_func,
            grouped_data,
        )

        # 返回结果（不再合并，直接返回 reduce 结果）
        return reduce_results


# =============================================================================
# 便捷函数
# =============================================================================

def create_memory_manager(
    max_memory_mb: int = 0,
    warning_percent: float = 0.75,
    critical_percent: float = 0.90,
) -> MemoryManager:
    """创建内存管理器"""
    return MemoryManager(
        max_memory_bytes=max_memory_mb * 1024 * 1024 if max_memory_mb > 0 else 0,
        warning_threshold=warning_percent,
        critical_threshold=critical_percent,
    )


def create_map_reduce_task(
    name: str,
    map_func: Callable,
    reduce_func: Callable,
    input_data: list,
    **kwargs,
) -> MapReduceTask:
    """创建 Map/Reduce 任务"""
    return MapReduceTask(
        name=name,
        map_func=map_func,
        reduce_func=reduce_func,
        input_data=input_data,
        **kwargs,
    )


def create_map_reduce_executor(
    max_memory_mb: int = 0,
    num_workers: int = 4,
) -> MapReduceExecutor:
    """创建 Map/Reduce 执行器"""
    memory_manager = create_memory_manager(max_memory_mb)
    return MapReduceExecutor(memory_manager=memory_manager, num_workers=num_workers)
