"""
性能优化模块 (Performance Optimization)

提供 IntentOS 性能优化功能：
1. 编译器优化（增量编译、并行编译）
2. 缓存优化（多级缓存、LRU 淘汰）
3. Token 优化（压缩、复用）
4. 并发执行优化
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Generic, Optional, TypeVar

T = TypeVar('T')


# =============================================================================
# LRU 缓存
# =============================================================================


class LRUCache(Generic[T]):
    """
    LRU 缓存
    
    特性：
    - O(1) 时间复杂度的 get/put
    - 自动淘汰最久未使用的项
    - 支持最大容量限制
    """
    
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache: OrderedDict[str, T] = OrderedDict()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[T]:
        """获取缓存项"""
        if key not in self.cache:
            self.misses += 1
            return None
        
        # 移动到末尾（最近使用）
        self.cache.move_to_end(key)
        self.hits += 1
        return self.cache[key]
    
    def put(self, key: str, value: T) -> None:
        """放入缓存项"""
        if key in self.cache:
            self.cache.move_to_end(key)
        
        self.cache[key] = value
        
        # 如果超出容量，淘汰最久未使用的
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
    
    def remove(self, key: str) -> bool:
        """删除缓存项"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    @property
    def size(self) -> int:
        """当前缓存大小"""
        return len(self.cache)
    
    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        return {
            "capacity": self.capacity,
            "size": self.size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hit_rate,
        }


# =============================================================================
# 多级缓存
# =============================================================================


@dataclass
class CacheEntry(Generic[T]):
    """缓存条目"""
    value: T
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class MultiLevelCache(Generic[T]):
    """
    多级缓存
    
    L1: 内存缓存（最快，容量小）
    L2: 内存缓存（较快，容量中）
    L3: 磁盘/Redis 缓存（较慢，容量大）
    """
    
    def __init__(
        self,
        l1_capacity: int = 100,
        l2_capacity: int = 1000,
        l3_capacity: int = 10000,
    ):
        self.l1 = LRUCache[T](l1_capacity)
        self.l2 = LRUCache[T](l2_capacity)
        self.l3 = LRUCache[T](l3_capacity)
        
        # 统计
        self.l1_hits = 0
        self.l2_hits = 0
        self.l3_hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[T]:
        """获取缓存项（从任意层级）"""
        # L1
        value = self.l1.get(key)
        if value is not None:
            self.l1_hits += 1
            return value
        
        # L2
        value = self.l2.get(key)
        if value is not None:
            self.l2_hits += 1
            self.l1.put(key, value)  # 提升到 L1
            return value
        
        # L3
        value = self.l3.get(key)
        if value is not None:
            self.l3_hits += 1
            self.l1.put(key, value)  # 提升到 L1
            return value
        
        self.misses += 1
        return None
    
    def put(self, key: str, value: T, level: int = 1) -> None:
        """
        放入缓存项
        
        Args:
            key: 缓存键
            value: 缓存值
            level: 初始层级 (1=L1, 2=L2, 3=L3)
        """
        if level == 1:
            self.l1.put(key, value)
        elif level == 2:
            self.l2.put(key, value)
        else:
            self.l3.put(key, value)
    
    def remove(self, key: str) -> None:
        """从所有层级删除"""
        self.l1.remove(key)
        self.l2.remove(key)
        self.l3.remove(key)
    
    def clear(self) -> None:
        """清空所有缓存"""
        self.l1.clear()
        self.l2.clear()
        self.l3.clear()
    
    def stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        total_hits = self.l1_hits + self.l2_hits + self.l3_hits
        total_requests = total_hits + self.misses
        
        return {
            "l1": self.l1.stats(),
            "l2": self.l2.stats(),
            "l3": self.l3.stats(),
            "l1_hits": self.l1_hits,
            "l2_hits": self.l2_hits,
            "l3_hits": self.l3_hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "overall_hit_rate": total_hits / total_requests if total_requests > 0 else 0.0,
        }


# =============================================================================
# 增量编译器
# =============================================================================


@dataclass
class CompilationUnit:
    """编译单元"""
    unit_id: str
    source_hash: str
    dependencies: list[str] = field(default_factory=list)
    compiled_at: Optional[datetime] = None
    compile_time_ms: float = 0.0


class IncrementalCompiler:
    """
    增量编译器
    
    特性：
    - 只重新编译变更的部分
    - 跟踪依赖关系
    - 缓存编译结果
    """
    
    def __init__(self, cache: Optional[MultiLevelCache] = None):
        self.cache = cache or MultiLevelCache()
        self.units: dict[str, CompilationUnit] = {}
        self.compile_count = 0
        self.incremental_count = 0
    
    def compile(
        self,
        unit_id: str,
        source: str,
        dependencies: Optional[list[str]] = None,
        compiler_func: Optional[Callable[[str], Any]] = None,
    ) -> tuple[Any, bool]:
        """
        编译源码
        
        Args:
            unit_id: 编译单元 ID
            source: 源代码
            dependencies: 依赖项列表
            compiler_func: 实际编译函数
            
        Returns:
            (编译结果，是否使用缓存)
        """
        start_time = time.time()
        
        # 计算源码哈希
        source_hash = hashlib.md5(source.encode()).hexdigest()
        
        # 检查是否有缓存
        cached = self.cache.get(unit_id)
        if cached is not None:
            unit = self.units.get(unit_id)
            if unit and unit.source_hash == source_hash:
                # 源码未变更，使用缓存
                self.incremental_count += 1
                return (cached, True)
        
        # 检查依赖是否变更
        deps = dependencies or []
        for dep_id in deps:
            dep_unit = self.units.get(dep_id)
            if dep_unit and dep_unit.compiled_at:
                # 依赖已重新编译，需要重新编译
                pass
        
        # 执行编译
        if compiler_func:
            result = compiler_func(source)
        else:
            result = source  # 默认：直接返回源码
        
        compile_time = (time.time() - start_time) * 1000
        
        # 更新编译单元
        self.units[unit_id] = CompilationUnit(
            unit_id=unit_id,
            source_hash=source_hash,
            dependencies=deps,
            compiled_at=datetime.now(),
            compile_time_ms=compile_time,
        )
        
        # 缓存结果
        self.cache.put(unit_id, result, level=1)
        self.compile_count += 1
        
        return (result, False)
    
    def invalidate(self, unit_id: str) -> None:
        """使缓存失效"""
        self.cache.remove(unit_id)
        if unit_id in self.units:
            del self.units[unit_id]
    
    def stats(self) -> dict[str, Any]:
        """获取编译器统计"""
        total_compiles = self.compile_count + self.incremental_count
        incremental_rate = self.incremental_count / total_compiles if total_compiles > 0 else 0.0
        
        avg_compile_time = 0.0
        if self.units:
            times = [u.compile_time_ms for u in self.units.values() if u.compile_time_ms > 0]
            if times:
                avg_compile_time = sum(times) / len(times)
        
        return {
            "total_compiles": total_compiles,
            "full_compiles": self.compile_count,
            "incremental_compiles": self.incremental_count,
            "incremental_rate": incremental_rate,
            "avg_compile_time_ms": avg_compile_time,
            "cache_stats": self.cache.stats(),
        }


# =============================================================================
# Token 优化器
# =============================================================================


class TokenOptimizer:
    """
    Token 优化器
    
    优化 LLM Token 使用：
    - 压缩 Prompt
    - 复用上下文
    - 移除冗余信息
    """
    
    def __init__(self):
        self.token_count = 0
        self.saved_count = 0
        self.compression_ratios = []
    
    def compress_prompt(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """
        压缩 Prompt
        
        策略：
        1. 移除多余空白
        2. 缩写常见词
        3. 截断到最大长度
        """
        original_length = len(prompt)
        
        # 移除多余空白
        compressed = " ".join(prompt.split())
        
        # 常见缩写
        abbreviations = {
            "please": "plz",
            "thank you": "thx",
            "information": "info",
            "configuration": "config",
            "application": "app",
        }
        for full, abbr in abbreviations.items():
            compressed = compressed.replace(full, abbr)
        
        # 截断
        if max_tokens:
            max_chars = max_tokens * 4  # 粗略估计
            if len(compressed) > max_chars:
                compressed = compressed[:max_chars]
        
        compressed_length = len(compressed)
        saved = original_length - compressed_length
        
        self.token_count += original_length
        self.saved_count += saved
        if original_length > 0:
            self.compression_ratios.append(compressed_length / original_length)
        
        return compressed
    
    def reuse_context(
        self,
        current_context: dict[str, Any],
        cached_context: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        复用上下文
        
        只传输变更的部分
        """
        if cached_context is None:
            return current_context
        
        # 找出变更的键
        changes = {}
        for key, value in current_context.items():
            if key not in cached_context or cached_context[key] != value:
                changes[key] = value
        
        return changes
    
    def stats(self) -> dict[str, Any]:
        """获取优化统计"""
        avg_ratio = 0.0
        if self.compression_ratios:
            avg_ratio = sum(self.compression_ratios) / len(self.compression_ratios)
        
        return {
            "total_tokens": self.token_count,
            "saved_tokens": self.saved_count,
            "savings_rate": self.saved_count / self.token_count if self.token_count > 0 else 0.0,
            "avg_compression_ratio": avg_ratio,
        }


# =============================================================================
# 并发执行器
# =============================================================================


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    result: Any
    execution_time_ms: float
    success: bool
    error: Optional[str] = None


class ConcurrentExecutor:
    """
    并发执行器
    
    特性：
    - 异步并发执行
    - 批量处理
    - 超时控制
    """
    
    def __init__(self, max_concurrency: int = 10, timeout: float = 30.0):
        self.max_concurrency = max_concurrency
        self.timeout = timeout
        self.executed_count = 0
        self.failed_count = 0
    
    async def execute(
        self,
        func: Callable,
        *args,
        task_id: str = "",
        **kwargs,
    ) -> TaskResult:
        """执行单个任务"""
        start_time = time.time()
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.timeout,
                )
            else:
                result = func(*args, **kwargs)
            
            execution_time = (time.time() - start_time) * 1000
            self.executed_count += 1
            
            return TaskResult(
                task_id=task_id,
                result=result,
                execution_time_ms=execution_time,
                success=True,
            )
        except asyncio.TimeoutError:
            execution_time = (time.time() - start_time) * 1000
            self.failed_count += 1
            return TaskResult(
                task_id=task_id,
                result=None,
                execution_time_ms=execution_time,
                success=False,
                error="Timeout",
            )
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.failed_count += 1
            return TaskResult(
                task_id=task_id,
                result=None,
                execution_time_ms=execution_time,
                success=False,
                error=str(e),
            )
    
    async def execute_batch(
        self,
        tasks: list[tuple[Callable, tuple, dict, str]],
    ) -> list[TaskResult]:
        """
        批量执行任务
        
        Args:
            tasks: [(func, args, kwargs, task_id), ...]
            
        Returns:
            任务结果列表
        """
        semaphore = asyncio.Semaphore(self.max_concurrency)
        
        async def execute_with_semaphore(func, args, kwargs, task_id):
            async with semaphore:
                return await self.execute(func, *args, task_id=task_id, **kwargs)
        
        coroutines = [
            execute_with_semaphore(func, args, kwargs, task_id)
            for func, args, kwargs, task_id in tasks
        ]
        
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        return results
    
    def stats(self) -> dict[str, Any]:
        """获取执行统计"""
        return {
            "executed_count": self.executed_count,
            "failed_count": self.failed_count,
            "success_rate": (self.executed_count - self.failed_count) / self.executed_count if self.executed_count > 0 else 0.0,
            "max_concurrency": self.max_concurrency,
            "timeout": self.timeout,
        }


# =============================================================================
# 性能监控器
# =============================================================================


class PerformanceMonitor:
    """
    性能监控器
    
    监控和报告系统性能指标
    """
    
    def __init__(self):
        self.metrics: dict[str, list[float]] = {}
        self.start_times: dict[str, float] = {}
    
    def start_timer(self, name: str) -> None:
        """开始计时"""
        self.start_times[name] = time.time()
    
    def stop_timer(self, name: str) -> float:
        """停止计时"""
        if name not in self.start_times:
            return 0.0
        
        elapsed = (time.time() - self.start_times[name]) * 1000  # ms
        self.start_times.pop(name)
        
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(elapsed)
        
        return elapsed
    
    def get_stats(self, name: str) -> dict[str, Any]:
        """获取指定指标的统计"""
        if name not in self.metrics or not self.metrics[name]:
            return {"count": 0}
        
        values = self.metrics[name]
        return {
            "count": len(values),
            "min_ms": min(values),
            "max_ms": max(values),
            "avg_ms": sum(values) / len(values),
            "p50_ms": self._percentile(values, 50),
            "p90_ms": self._percentile(values, 90),
            "p99_ms": self._percentile(values, 99),
        }
    
    def _percentile(self, values: list[float], percentile: int) -> float:
        """计算百分位数"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def all_stats(self) -> dict[str, Any]:
        """获取所有指标统计"""
        return {name: self.get_stats(name) for name in self.metrics}
    
    def reset(self) -> None:
        """重置所有指标"""
        self.metrics.clear()
        self.start_times.clear()


# =============================================================================
# 工厂函数
# =============================================================================


def create_lru_cache(capacity: int = 1000) -> LRUCache:
    """创建 LRU 缓存"""
    return LRUCache(capacity)


def create_multi_level_cache(
    l1_capacity: int = 100,
    l2_capacity: int = 1000,
    l3_capacity: int = 10000,
) -> MultiLevelCache:
    """创建多级缓存"""
    return MultiLevelCache(l1_capacity, l2_capacity, l3_capacity)


def create_incremental_compiler() -> IncrementalCompiler:
    """创建增量编译器"""
    return IncrementalCompiler()


def create_token_optimizer() -> TokenOptimizer:
    """创建 Token 优化器"""
    return TokenOptimizer()


def create_concurrent_executor(
    max_concurrency: int = 10,
    timeout: float = 30.0,
) -> ConcurrentExecutor:
    """创建并发执行器"""
    return ConcurrentExecutor(max_concurrency, timeout)


def create_performance_monitor() -> PerformanceMonitor:
    """创建性能监控器"""
    return PerformanceMonitor()
