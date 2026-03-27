"""
性能优化测试

测试性能优化模块的核心功能：
1. LRU 缓存
2. 多级缓存
3. 增量编译器
4. Token 优化器
5. 并发执行器
6. 性能监控器
"""

import asyncio
import pytest
import time
from intentos.optimization import (
    LRUCache,
    MultiLevelCache,
    IncrementalCompiler,
    TokenOptimizer,
    ConcurrentExecutor,
    PerformanceMonitor,
    create_lru_cache,
    create_multi_level_cache,
    create_incremental_compiler,
    create_token_optimizer,
    create_concurrent_executor,
    create_performance_monitor,
)


class TestLRUCache:
    """测试 LRU 缓存"""
    
    def test_basic_operations(self):
        """测试基本操作"""
        cache = LRUCache[str](capacity=3)
        
        # 放入
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # 获取
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        
        # 统计
        stats = cache.stats()
        assert stats["hits"] == 3
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 1.0
    
    def test_eviction(self):
        """测试淘汰机制"""
        cache = LRUCache[str](capacity=2)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")  # 应该淘汰 key1
        
        assert cache.get("key1") is None  # 已被淘汰
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
    
    def test_lru_order(self):
        """测试 LRU 顺序"""
        cache = LRUCache[str](capacity=2)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        # 访问 key1，使其成为最近使用
        cache.get("key1")
        
        # 放入 key3，应该淘汰 key2（最久未使用）
        cache.put("key3", "value3")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None  # 被淘汰
        assert cache.get("key3") == "value3"
    
    def test_hit_rate(self):
        """测试命中率计算"""
        cache = LRUCache[str](capacity=2)
        
        cache.put("key1", "value1")
        
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("key2")  # miss
        
        stats = cache.stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert abs(stats["hit_rate"] - 2/3) < 0.01


class TestMultiLevelCache:
    """测试多级缓存"""
    
    def test_basic_operations(self):
        """测试基本操作"""
        cache = MultiLevelCache[str](l1_capacity=2, l2_capacity=3, l3_capacity=5)
        
        # 放入 L3
        cache.put("key1", "value1", level=3)
        
        # 获取（应该从 L3 提升到 L1）
        assert cache.get("key1") == "value1"
        
        # 再次获取（应该从 L1 命中）
        assert cache.get("key1") == "value1"
        
        stats = cache.stats()
        assert stats["l3_hits"] == 1
        assert stats["l1_hits"] == 1
    
    def test_cache_hierarchy(self):
        """测试缓存层级"""
        cache = MultiLevelCache[str](l1_capacity=1, l2_capacity=2, l3_capacity=3)
        
        # 放入多个值
        cache.put("key1", "value1", level=3)
        cache.put("key2", "value2", level=3)
        cache.put("key3", "value3", level=3)
        
        # 获取 key1（从 L3 到 L1）
        cache.get("key1")
        
        # 获取 key2（从 L3 到 L1，key1 可能被挤到 L2）
        cache.get("key2")
        
        stats = cache.stats()
        assert stats["l3_hits"] == 2
        assert stats["overall_hit_rate"] == 1.0


class TestIncrementalCompiler:
    """测试增量编译器"""
    
    def test_full_compile(self):
        """测试完整编译"""
        compiler = IncrementalCompiler()
        
        def mock_compile(source):
            return f"compiled: {source}"
        
        result, cached = compiler.compile(
            unit_id="unit1",
            source="print('hello')",
            compiler_func=mock_compile,
        )
        
        assert result == "compiled: print('hello')"
        assert cached is False
        
        stats = compiler.stats()
        assert stats["full_compiles"] == 1
    
    def test_incremental_compile(self):
        """测试增量编译"""
        compiler = IncrementalCompiler()
        
        def mock_compile(source):
            return f"compiled: {source}"
        
        # 第一次编译
        compiler.compile("unit1", "source1", compiler_func=mock_compile)
        
        # 第二次编译（相同源码）
        result, cached = compiler.compile("unit1", "source1", compiler_func=mock_compile)
        
        assert cached is True
        
        stats = compiler.stats()
        assert stats["incremental_compiles"] == 1
        assert stats["incremental_rate"] == 0.5
    
    def test_invalidation(self):
        """测试缓存失效"""
        compiler = IncrementalCompiler()
        
        compiler.compile("unit1", "source1")
        compiler.invalidate("unit1")
        
        result, cached = compiler.compile("unit1", "source1")
        
        assert cached is False


class TestTokenOptimizer:
    """测试 Token 优化器"""
    
    def test_compress_prompt(self):
        """测试 Prompt 压缩"""
        optimizer = TokenOptimizer()
        
        original = "please provide the information about the application configuration"
        compressed = optimizer.compress_prompt(original)
        
        assert len(compressed) < len(original)
        assert "plz" in compressed
        assert "info" in compressed
        assert "app" in compressed
        assert "config" in compressed
    
    def test_reuse_context(self):
        """测试上下文复用"""
        optimizer = TokenOptimizer()
        
        cached = {"user_id": "123", "session": "abc", "role": "admin"}
        current = {"user_id": "123", "session": "xyz", "role": "admin"}  # 只有 session 变更
        
        changes = optimizer.reuse_context(current, cached)
        
        assert "session" in changes
        assert "user_id" not in changes
        assert "role" not in changes
    
    def test_stats(self):
        """测试统计"""
        optimizer = TokenOptimizer()
        
        optimizer.compress_prompt("hello world")
        optimizer.compress_prompt("please help me")
        
        stats = optimizer.stats()
        assert stats["total_tokens"] > 0
        assert stats["savings_rate"] >= 0


class TestConcurrentExecutor:
    """测试并发执行器"""
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """测试执行"""
        executor = ConcurrentExecutor(max_concurrency=2, timeout=5.0)
        
        def sync_func(x):
            return x * 2
        
        result = await executor.execute(sync_func, 5, task_id="test1")
        
        assert result.success is True
        assert result.result == 10
        assert result.execution_time_ms >= 0
    
    @pytest.mark.asyncio
    async def test_execute_async(self):
        """测试异步执行"""
        executor = ConcurrentExecutor(max_concurrency=2, timeout=5.0)
        
        async def async_func(x):
            await asyncio.sleep(0.1)
            return x * 2
        
        result = await executor.execute(async_func, 5, task_id="test1")
        
        assert result.success is True
        assert result.result == 10
    
    @pytest.mark.asyncio
    async def test_timeout(self):
        """测试超时"""
        executor = ConcurrentExecutor(max_concurrency=2, timeout=0.1)
        
        async def slow_func():
            await asyncio.sleep(1.0)
            return "done"
        
        result = await executor.execute(slow_func, task_id="test1")
        
        assert result.success is False
        assert result.error == "Timeout"
    
    @pytest.mark.asyncio
    async def test_batch_execute(self):
        """测试批量执行"""
        executor = ConcurrentExecutor(max_concurrency=3, timeout=5.0)
        
        async def task(x):
            await asyncio.sleep(0.1)
            return x * 2
        
        tasks = [
            (task, (i,), {}, f"task_{i}")
            for i in range(5)
        ]
        
        results = await executor.execute_batch(tasks)
        
        assert len(results) == 5
        assert all(r.success for r in results)
    
    def test_stats(self):
        """测试统计"""
        executor = ConcurrentExecutor(max_concurrency=2, timeout=5.0)
        
        stats = executor.stats()
        assert stats["max_concurrency"] == 2
        assert stats["timeout"] == 5.0


class TestPerformanceMonitor:
    """测试性能监控器"""
    
    def test_timer(self):
        """测试计时器"""
        monitor = PerformanceMonitor()
        
        monitor.start_timer("operation1")
        time.sleep(0.1)
        elapsed = monitor.stop_timer("operation1")
        
        assert elapsed >= 100  # ms
        assert elapsed < 200
    
    def test_multiple_timers(self):
        """测试多个计时器"""
        monitor = PerformanceMonitor()
        
        monitor.start_timer("op1")
        time.sleep(0.05)
        monitor.stop_timer("op1")
        
        monitor.start_timer("op1")
        time.sleep(0.05)
        monitor.stop_timer("op1")
        
        monitor.start_timer("op2")
        time.sleep(0.1)
        monitor.stop_timer("op2")
        
        stats = monitor.all_stats()
        
        assert stats["op1"]["count"] == 2
        assert stats["op2"]["count"] == 1
        assert stats["op1"]["avg_ms"] >= 50
    
    def test_percentile(self):
        """测试百分位数计算"""
        monitor = PerformanceMonitor()
        
        monitor.metrics["test"] = list(range(1, 101))
        
        stats = monitor.get_stats("test")
        
        assert stats["count"] == 100
        assert stats["min_ms"] == 1
        assert stats["max_ms"] == 100
        assert 49 <= stats["p50_ms"] <= 51  # 允许误差
        assert 89 <= stats["p90_ms"] <= 91
        assert 98 <= stats["p99_ms"] <= 100
    
    def test_reset(self):
        """测试重置"""
        monitor = PerformanceMonitor()
        
        monitor.start_timer("op1")
        monitor.stop_timer("op1")
        
        monitor.reset()
        
        stats = monitor.all_stats()
        assert len(stats) == 0


class TestFactoryFunctions:
    """测试工厂函数"""
    
    def test_create_lru_cache(self):
        """测试创建 LRU 缓存"""
        cache = create_lru_cache(capacity=100)
        assert isinstance(cache, LRUCache)
        assert cache.capacity == 100
    
    def test_create_multi_level_cache(self):
        """测试创建多级缓存"""
        cache = create_multi_level_cache(l1_capacity=50, l2_capacity=500, l3_capacity=5000)
        assert isinstance(cache, MultiLevelCache)
        assert cache.l1.capacity == 50
        assert cache.l2.capacity == 500
        assert cache.l3.capacity == 5000
    
    def test_create_incremental_compiler(self):
        """测试创建增量编译器"""
        compiler = create_incremental_compiler()
        assert isinstance(compiler, IncrementalCompiler)
    
    def test_create_token_optimizer(self):
        """测试创建 Token 优化器"""
        optimizer = create_token_optimizer()
        assert isinstance(optimizer, TokenOptimizer)
    
    def test_create_concurrent_executor(self):
        """测试创建并发执行器"""
        executor = create_concurrent_executor(max_concurrency=5, timeout=10.0)
        assert isinstance(executor, ConcurrentExecutor)
        assert executor.max_concurrency == 5
        assert executor.timeout == 10.0
    
    def test_create_performance_monitor(self):
        """测试创建性能监控器"""
        monitor = create_performance_monitor()
        assert isinstance(monitor, PerformanceMonitor)


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_optimization_pipeline(self):
        """测试优化流水线"""
        # 创建组件
        cache = create_multi_level_cache()
        compiler = create_incremental_compiler()
        compiler.cache = cache  # 手动设置缓存
        optimizer = create_token_optimizer()
        monitor = create_performance_monitor()
        
        # 模拟编译流程
        monitor.start_timer("compile")
        
        # Token 优化
        source = "please analyze the sales data and generate a report"
        compressed = optimizer.compress_prompt(source)
        
        # 增量编译
        result, cached = compiler.compile(
            unit_id="analyze_sales",
            source=compressed,
        )
        
        monitor.stop_timer("compile")
        
        # 验证
        stats = monitor.get_stats("compile")
        assert stats["count"] == 1
        assert stats["avg_ms"] < 100  # 应该很快
        
        compiler_stats = compiler.stats()
        assert compiler_stats["full_compiles"] == 1
        
        optimizer_stats = optimizer.stats()
        assert optimizer_stats["savings_rate"] > 0
    
    def test_cache_with_compiler(self):
        """测试缓存与编译器集成"""
        cache = create_multi_level_cache()
        compiler = create_incremental_compiler()
        compiler.cache = cache  # 手动设置缓存
        
        # 编译两次
        compiler.compile("unit1", "source1")
        compiler.compile("unit1", "source1")  # 应该命中缓存
        
        stats = compiler.stats()
        assert stats["incremental_rate"] == 0.5
        assert stats["cache_stats"]["overall_hit_rate"] == 0.5
