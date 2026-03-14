"""
性能监控

提供指标收集和性能分析

设计文档：docs/private/010-performance-monitoring.md
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class MetricLabel:
    """指标标签"""
    name: str
    value: str


@dataclass
class MetricSample:
    """指标样本"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: list[MetricLabel] = field(default_factory=list)


class Counter:
    """计数器"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._values: dict[str, float] = defaultdict(float)
    
    def inc(self, value: float = 1.0, **labels) -> None:
        """增加计数"""
        key = self._make_key(labels)
        self._values[key] += value
    
    def get(self, **labels) -> float:
        """获取计数"""
        key = self._make_key(labels)
        return self._values[key]
    
    def _make_key(self, labels: dict) -> str:
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))


class Gauge:
    """仪表"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._values: dict[str, float] = defaultdict(float)
    
    def set(self, value: float, **labels) -> None:
        """设置值"""
        key = self._make_key(labels)
        self._values[key] = value
    
    def inc(self, value: float = 1.0, **labels) -> None:
        """增加"""
        key = self._make_key(labels)
        self._values[key] += value
    
    def dec(self, value: float = 1.0, **labels) -> None:
        """减少"""
        key = self._make_key(labels)
        self._values[key] -= value
    
    def get(self, **labels) -> float:
        """获取值"""
        key = self._make_key(labels)
        return self._values[key]
    
    def _make_key(self, labels: dict) -> str:
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))


class Histogram:
    """直方图"""
    
    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    
    def __init__(
        self,
        name: str,
        description: str = "",
        buckets: tuple = DEFAULT_BUCKETS,
    ):
        self.name = name
        self.description = description
        self.buckets = buckets
        self._bucket_counts: dict[str, dict[float, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._sums: dict[str, float] = defaultdict(float)
        self._counts: dict[str, int] = defaultdict(int)
    
    def observe(self, value: float, **labels) -> None:
        """观察一个值"""
        key = self._make_key(labels)
        
        self._counts[key] += 1
        self._sums[key] += value
        
        for bucket in self.buckets:
            if value <= bucket:
                self._bucket_counts[key][bucket] += 1
        
        self._bucket_counts[key][float("inf")] += 1
    
    def _make_key(self, labels: dict) -> str:
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))


class MetricRegistry:
    """指标注册表"""
    
    _instance: Optional["MetricRegistry"] = None
    
    def __new__(cls) -> "MetricRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}
        self._initialized = True
    
    def counter(self, name: str, description: str = "") -> Counter:
        """注册计数器"""
        if name not in self._counters:
            self._counters[name] = Counter(name, description)
        return self._counters[name]
    
    def gauge(self, name: str, description: str = "") -> Gauge:
        """注册仪表"""
        if name not in self._gauges:
            self._gauges[name] = Gauge(name, description)
        return self._gauges[name]
    
    def histogram(self, name: str, description: str = "", buckets: tuple = None) -> Histogram:
        """注册直方图"""
        if name not in self._histograms:
            self._histograms[name] = Histogram(name, description, buckets or Histogram.DEFAULT_BUCKETS)
        return self._histograms[name]
    
    def to_dict(self) -> dict:
        """导出为字典"""
        return {
            "counters": {name: self._values_to_dict(counter) for name, counter in self._counters.items()},
            "gauges": {name: self._values_to_dict(gauge) for name, gauge in self._gauges.items()},
            "histograms": {name: self._values_to_dict(histogram) for name, histogram in self._histograms.items()},
        }
    
    def _values_to_dict(self, metric) -> dict:
        if hasattr(metric, '_values'):
            return dict(metric._values)
        return {}


# 全局注册表
registry = MetricRegistry()


# IntentOS 预定义指标
vm_programs_executed = registry.counter(
    "intentos_vm_programs_executed_total",
    "Total number of programs executed",
)

vm_execution_duration = registry.histogram(
    "intentos_vm_execution_duration_seconds",
    "Program execution duration in seconds",
)

vm_gas_consumed = registry.counter(
    "intentos_vm_gas_consumed_total",
    "Total gas consumed",
)


@dataclass
class Span:
    """追踪 Span"""
    
    name: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    attributes: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    @property
    def duration(self) -> float:
        if self.start_time is None:
            return 0.0
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time


class Profiler:
    """性能分析器"""
    
    def __init__(self):
        self._active_spans: dict[int, Span] = {}
        self._completed_spans: list[Span] = []
        self._enabled = True
    
    def start_span(self, name: str, **attributes) -> Span:
        """开始 span"""
        span = Span(name=name, start_time=time.time(), attributes=attributes)
        self._active_spans[id(span)] = span
        return span
    
    def end_span(self, span: Span, error: Optional[str] = None) -> None:
        """结束 span"""
        span.end_time = time.time()
        if error:
            span.error = error
        
        if id(span) in self._active_spans:
            del self._active_spans[id(span)]
        self._completed_spans.append(span)
    
    def get_spans(self) -> list[Span]:
        """获取所有完成的 span"""
        return self._completed_spans.copy()
    
    def get_stats(self) -> dict[str, dict[str, float]]:
        """获取统计信息"""
        stats: dict[str, dict[str, float]] = defaultdict(
            lambda: {"count": 0, "total_duration": 0.0, "errors": 0}
        )
        
        for span in self._completed_spans:
            stats[span.name]["count"] += 1
            stats[span.name]["total_duration"] += span.duration
            if span.error:
                stats[span.name]["errors"] += 1
        
        result = {}
        for name, data in stats.items():
            result[name] = {
                "count": data["count"],
                "avg_duration": data["total_duration"] / data["count"] if data["count"] > 0 else 0,
                "total_duration": data["total_duration"],
                "errors": data["errors"],
            }
        
        return result
    
    def clear(self) -> None:
        """清除所有 span"""
        self._completed_spans.clear()


# 全局分析器
profiler = Profiler()


def profile_function(func: Callable) -> Callable:
    """装饰器：分析函数性能"""
    import functools
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        span = profiler.start_span(func.__name__)
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            profiler.end_span(span, error=str(e))
            raise
        finally:
            if span in profiler._active_spans.values():
                profiler.end_span(span)
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        span = profiler.start_span(func.__name__)
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            profiler.end_span(span, error=str(e))
            raise
        finally:
            if span in profiler._active_spans.values():
                profiler.end_span(span)
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


import asyncio
