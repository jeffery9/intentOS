"""
Utils Metrics Module Tests

测试性能监控：计数器、仪表、直方图、指标注册表和性能分析器
"""

import asyncio
import pytest
import time

from intentos.utils.metrics import (
    MetricType,
    MetricLabel,
    MetricSample,
    Counter,
    Gauge,
    Histogram,
    MetricRegistry,
    Span,
    Profiler,
    profile_function,
    registry,
    profiler,
    vm_programs_executed,
    vm_execution_duration,
    vm_gas_consumed,
)


class TestMetricType:
    """测试指标类型枚举"""

    def test_counter_type(self):
        """计数器类型"""
        assert MetricType.COUNTER.value == "counter"

    def test_gauge_type(self):
        """仪表类型"""
        assert MetricType.GAUGE.value == "gauge"

    def test_histogram_type(self):
        """直方图类型"""
        assert MetricType.HISTOGRAM.value == "histogram"


class TestMetricLabel:
    """测试指标标签"""

    def test_create_label(self):
        """创建标签"""
        label = MetricLabel(name="method", value="GET")
        
        assert label.name == "method"
        assert label.value == "GET"


class TestMetricSample:
    """测试指标样本"""

    def test_create_sample(self):
        """创建样本"""
        from datetime import datetime
        
        sample = MetricSample(
            name="test_metric",
            value=42.0,
            labels=[MetricLabel(name="tag", value="value")]
        )
        
        assert sample.name == "test_metric"
        assert sample.value == 42.0
        assert len(sample.labels) == 1
        assert isinstance(sample.timestamp, datetime)


class TestCounter:
    """测试计数器"""

    def test_create_counter(self):
        """创建计数器"""
        counter = Counter("test_counter", "Test description")
        
        assert counter.name == "test_counter"
        assert counter.description == "Test description"

    def test_increment(self):
        """增加计数"""
        counter = Counter("test")
        
        counter.inc()
        assert counter.get() == 1.0

    def test_increment_by_value(self):
        """按值增加"""
        counter = Counter("test")
        
        counter.inc(5)
        assert counter.get() == 5.0

    def test_increment_with_labels(self):
        """带标签的增加"""
        counter = Counter("test")
        
        counter.inc(method="GET", status="200")
        counter.inc(method="POST", status="200")
        
        assert counter.get(method="GET", status="200") == 1.0
        assert counter.get(method="POST", status="200") == 1.0

    def test_multiple_increments(self):
        """多次增加"""
        counter = Counter("test")
        
        counter.inc()
        counter.inc()
        counter.inc(3)
        
        assert counter.get() == 5.0


class TestGauge:
    """测试仪表"""

    def test_create_gauge(self):
        """创建仪表"""
        gauge = Gauge("test_gauge", "Test description")
        
        assert gauge.name == "test_gauge"
        assert gauge.description == "Test description"

    def test_set_value(self):
        """设置值"""
        gauge = Gauge("test")
        
        gauge.set(42.0)
        assert gauge.get() == 42.0

    def test_increment(self):
        """增加"""
        gauge = Gauge("test")
        
        gauge.set(10)
        gauge.inc(5)
        
        assert gauge.get() == 15.0

    def test_decrement(self):
        """减少"""
        gauge = Gauge("test")
        
        gauge.set(10)
        gauge.dec(3)
        
        assert gauge.get() == 7.0

    def test_increment_with_labels(self):
        """带标签的增加"""
        gauge = Gauge("test")
        
        gauge.set(10, region="us")
        gauge.inc(5, region="us")
        gauge.set(20, region="eu")
        
        assert gauge.get(region="us") == 15.0
        assert gauge.get(region="eu") == 20.0


class TestHistogram:
    """测试直方图"""

    def test_create_histogram(self):
        """创建直方图"""
        histogram = Histogram("test_histogram", "Test description")
        
        assert histogram.name == "test_histogram"
        assert histogram.description == "Test description"
        assert len(histogram.buckets) > 0

    def test_observe_value(self):
        """观察值"""
        histogram = Histogram("test")
        
        histogram.observe(0.5)
        
        # 值应被记录到相应桶中
        assert histogram._counts[""] == 1

    def test_observe_with_labels(self):
        """带标签的观察"""
        histogram = Histogram("test")
        
        histogram.observe(0.5, method="GET")
        histogram.observe(1.0, method="POST")
        
        assert histogram._counts["method=GET"] == 1
        assert histogram._counts["method=POST"] == 1

    def test_bucket_distribution(self):
        """桶分布"""
        histogram = Histogram("test", buckets=(1.0, 5.0, 10.0))
        
        histogram.observe(0.5)
        histogram.observe(3.0)
        histogram.observe(7.0)
        histogram.observe(15.0)
        
        # 检查桶计数
        assert histogram._bucket_counts[""][1.0] == 1  # 0.5
        assert histogram._bucket_counts[""][5.0] == 2  # 0.5, 3.0
        assert histogram._bucket_counts[""][10.0] == 3  # 0.5, 3.0, 7.0
        assert histogram._bucket_counts[""][float("inf")] == 4  # 全部


class TestMetricRegistry:
    """测试指标注册表"""

    def test_singleton(self):
        """单例模式"""
        registry1 = MetricRegistry()
        registry2 = MetricRegistry()
        
        assert registry1 is registry2

    def test_register_counter(self):
        """注册计数器"""
        test_registry = MetricRegistry()
        
        counter = test_registry.counter("test_counter")
        
        assert isinstance(counter, Counter)
        assert counter.name == "test_counter"

    def test_register_gauge(self):
        """注册仪表"""
        test_registry = MetricRegistry()
        
        gauge = test_registry.gauge("test_gauge")
        
        assert isinstance(gauge, Gauge)
        assert gauge.name == "test_gauge"

    def test_register_histogram(self):
        """注册直方图"""
        test_registry = MetricRegistry()
        
        histogram = test_registry.histogram("test_histogram")
        
        assert isinstance(histogram, Histogram)
        assert histogram.name == "test_histogram"

    def test_register_histogram_custom_buckets(self):
        """注册带自定义桶的直方图"""
        test_registry = MetricRegistry()
        
        histogram = test_registry.histogram(
            "test",
            buckets=(0.1, 0.5, 1.0)
        )
        
        assert histogram.buckets == (0.1, 0.5, 1.0)

    def test_get_existing_metric(self):
        """获取已存在的指标"""
        test_registry = MetricRegistry()
        
        counter1 = test_registry.counter("test")
        counter2 = test_registry.counter("test")
        
        assert counter1 is counter2

    def test_to_dict(self):
        """导出为字典"""
        test_registry = MetricRegistry()
        
        test_registry.counter("c1")
        test_registry.gauge("g1")
        
        data = test_registry.to_dict()
        
        assert "counters" in data
        assert "gauges" in data
        assert "histograms" in data


class TestGlobalRegistry:
    """测试全局注册表"""

    def test_global_registry_exists(self):
        """全局注册表应存在"""
        assert registry is not None

    def test_predefined_metrics(self):
        """预定义指标"""
        assert vm_programs_executed is not None
        assert vm_execution_duration is not None
        assert vm_gas_consumed is not None


class TestSpan:
    """测试追踪 Span"""

    def test_create_span(self):
        """创建 Span"""
        span = Span(name="test_operation", start_time=time.time())
        
        assert span.name == "test_operation"
        assert span.start_time is not None
        assert span.end_time is None
        assert span.error is None

    def test_span_with_attributes(self):
        """带属性的 Span"""
        span = Span(
            name="test",
            start_time=time.time(),
            attributes={"key": "value", "count": 42}
        )
        
        assert span.attributes["key"] == "value"
        assert span.attributes["count"] == 42

    def test_span_duration_active(self):
        """活跃 Span 的持续时间"""
        start = time.time()
        span = Span(name="test", start_time=start)
        
        # 等待一小段时间
        time.sleep(0.01)
        
        duration = span.duration
        assert duration >= 0.01

    def test_span_duration_completed(self):
        """已完成 Span 的持续时间"""
        start = time.time()
        span = Span(name="test", start_time=start)
        span.end_time = start + 0.5
        
        assert span.duration == 0.5

    def test_span_duration_no_start(self):
        """未开始 Span 的持续时间"""
        span = Span(name="test", start_time=None)
        
        assert span.duration == 0.0


class TestProfiler:
    """测试性能分析器"""

    def test_create_profiler(self):
        """创建分析器"""
        profiler = Profiler()
        
        assert profiler._enabled is True
        assert len(profiler._active_spans) == 0
        assert len(profiler._completed_spans) == 0

    def test_start_span(self):
        """开始 Span"""
        profiler = Profiler()
        
        span = profiler.start_span("test_operation")
        
        assert span.name == "test_operation"
        assert len(profiler._active_spans) == 1

    def test_end_span(self):
        """结束 Span"""
        profiler = Profiler()
        
        span = profiler.start_span("test")
        profiler.end_span(span)
        
        assert len(profiler._active_spans) == 0
        assert len(profiler._completed_spans) == 1

    def test_end_span_with_error(self):
        """结束带错误的 Span"""
        profiler = Profiler()
        
        span = profiler.start_span("test")
        profiler.end_span(span, error="Test error")
        
        assert span.error == "Test error"

    def test_get_spans(self):
        """获取已完成的 Span"""
        profiler = Profiler()
        
        span1 = profiler.start_span("op1")
        span2 = profiler.start_span("op2")
        profiler.end_span(span1)
        profiler.end_span(span2)
        
        spans = profiler.get_spans()
        
        assert len(spans) == 2

    def test_get_stats(self):
        """获取统计信息"""
        profiler = Profiler()
        
        for _ in range(3):
            span = profiler.start_span("db_query")
            time.sleep(0.01)
            profiler.end_span(span)
        
        stats = profiler.get_stats()
        
        assert "db_query" in stats
        assert stats["db_query"]["count"] == 3
        assert stats["db_query"]["total_duration"] > 0

    def test_get_stats_with_errors(self):
        """获取带错误的统计"""
        profiler = Profiler()
        
        span1 = profiler.start_span("op")
        profiler.end_span(span1)
        
        span2 = profiler.start_span("op")
        profiler.end_span(span2, error="Error")
        
        stats = profiler.get_stats()
        
        assert stats["op"]["count"] == 2
        assert stats["op"]["errors"] == 1

    def test_clear(self):
        """清除所有 Span"""
        profiler = Profiler()
        
        span = profiler.start_span("test")
        profiler.end_span(span)
        profiler.clear()
        
        assert len(profiler._completed_spans) == 0


class TestGlobalProfiler:
    """测试全局分析器"""

    def test_global_profiler_exists(self):
        """全局分析器应存在"""
        assert profiler is not None


class TestProfileFunction:
    """测试函数性能分析装饰器"""

    @pytest.mark.asyncio
    async def test_profile_async_function(self):
        """分析异步函数"""
        test_profiler = Profiler()
        
        @profile_function
        async def async_func():
            await asyncio.sleep(0.01)
            return "result"
        
        # 清除全局分析器的 span
        profiler.clear()
        
        result = await async_func()
        
        assert result == "result"
        # 应记录 span
        stats = profiler.get_stats()
        assert "async_func" in stats

    def test_profile_sync_function(self):
        """分析同步函数"""
        test_profiler = Profiler()
        
        @profile_function
        def sync_func():
            time.sleep(0.01)
            return "result"
        
        profiler.clear()
        
        result = sync_func()
        
        assert result == "result"
        stats = profiler.get_stats()
        assert "sync_func" in stats

    @pytest.mark.asyncio
    async def test_profile_async_with_error(self):
        """分析出错的异步函数"""
        profiler.clear()
        
        @profile_function
        async def failing_async():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await failing_async()
        
        stats = profiler.get_stats()
        assert "failing_async" in stats
        assert stats["failing_async"]["errors"] == 1

    def test_profile_sync_with_error(self):
        """分析出错的同步函数"""
        profiler.clear()
        
        @profile_function
        def failing_sync():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_sync()
        
        stats = profiler.get_stats()
        assert "failing_sync" in stats
        assert stats["failing_sync"]["errors"] == 1
