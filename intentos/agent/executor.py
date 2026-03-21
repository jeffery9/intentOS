"""
Agent 执行器（监控版）

支持执行指标、日志和追踪
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ExecutionTrace:
    """执行追踪记录"""
    id: str
    intent: str
    matched_capability: Optional[str]
    status: ExecutionStatus
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "intent": self.intent,
            "matched_capability": self.matched_capability,
            "status": self.status.value,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class ExecutionMetrics:
    """执行指标"""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_duration_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0

    # 能力使用统计
    capability_usage: dict[str, int] = field(default_factory=dict)

    # 延迟统计
    p50_latency_ms: float = 0.0
    p90_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate": self.successful_executions / max(self.total_executions, 1),
            "avg_duration_ms": self.total_duration_ms / max(self.total_executions, 1),
            "p50_latency_ms": self.p50_latency_ms,
            "p90_latency_ms": self.p90_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "capability_usage": self.capability_usage,
        }


class ExecutionMonitor:
    """执行监控器"""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.logger: logging.Logger = logger or logging.getLogger(__name__)
        self.metrics: ExecutionMetrics = ExecutionMetrics()
        self.traces: list[ExecutionTrace] = []
        self._active_traces: dict[str, ExecutionTrace] = {}

    def start_trace(self, intent: str) -> ExecutionTrace:
        """开始追踪"""
        trace_id: str = f"exec_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        trace = ExecutionTrace(
            id=trace_id,
            intent=intent,
            matched_capability=None,
            status=ExecutionStatus.PENDING,
            start_time=time.time(),
        )
        self._active_traces[trace_id] = trace
        self.traces.append(trace)
        self.logger.debug(f"开始执行追踪：{trace_id}, 意图：{intent}")
        return trace

    def update_trace(
        self,
        trace: ExecutionTrace,
        matched_capability: Optional[str] = None,
        status: Optional[ExecutionStatus] = None,
        error: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """更新追踪"""
        if matched_capability:
            trace.matched_capability = matched_capability

        if status:
            trace.status = status

        if error:
            trace.error = error

        if metadata:
            trace.metadata.update(metadata)

        self.logger.debug(f"更新执行追踪：{trace.id}, 状态：{trace.status.value}")

    def end_trace(self, trace: ExecutionTrace, status: ExecutionStatus, error: Optional[str] = None) -> None:
        """结束追踪"""
        trace.end_time = time.time()
        trace.duration_ms = (trace.end_time - trace.start_time) * 1000
        trace.status = status
        if error:
            trace.error = error

        if trace.id in self._active_traces:
            del self._active_traces[trace.id]

        # 更新指标
        self._update_metrics(trace)

        # 日志
        if status == ExecutionStatus.SUCCESS:
            self.logger.info(f"执行成功：{trace.id}, 耗时：{trace.duration_ms:.2f}ms")
        else:
            self.logger.error(f"执行失败：{trace.id}, 错误：{error}")

    def _update_metrics(self, trace: ExecutionTrace) -> None:
        """更新指标"""
        self.metrics.total_executions += 1

        if trace.status == ExecutionStatus.SUCCESS:
            self.metrics.successful_executions += 1
        else:
            self.metrics.failed_executions += 1

        if trace.duration_ms:
            self.metrics.total_duration_ms += trace.duration_ms

        if trace.matched_capability:
            self.metrics.capability_usage[trace.matched_capability] = \
                self.metrics.capability_usage.get(trace.matched_capability, 0) + 1

        # 更新延迟百分位
        self._update_latency_percentiles(trace.duration_ms)

    def _update_latency_percentiles(self, duration_ms: Optional[float]) -> None:
        """更新延迟百分位"""
        if not duration_ms:
            return

        # 从追踪中获取所有延迟
        durations: list[float] = [
            t.duration_ms for t in self.traces
            if t.duration_ms is not None
        ]

        if not durations:
            return

        durations.sort()
        n = len(durations)

        self.metrics.p50_latency_ms = durations[int(n * 0.5)]
        self.metrics.p90_latency_ms = durations[int(n * 0.9)]
        self.metrics.p99_latency_ms = durations[int(n * 0.99)]

    def record_cache_hit(self) -> None:
        """记录缓存命中"""
        self.metrics.cache_hits += 1

    def record_cache_miss(self) -> None:
        """记录缓存未命中"""
        self.metrics.cache_misses += 1

    def get_recent_traces(self, limit: int = 100) -> list[ExecutionTrace]:
        """获取最近的追踪"""
        return self.traces[-limit:]

    def get_metrics(self) -> dict[str, Any]:
        """获取指标"""
        return self.metrics.to_dict()

    def get_capability_stats(self) -> dict[str, Any]:
        """获取能力使用统计"""
        total = sum(self.metrics.capability_usage.values())
        return {
            cap: {
                "count": count,
                "percentage": count / max(total, 1) * 100,
            }
            for cap, count in sorted(
                self.metrics.capability_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )
        }


class AgentExecutor:
    """Agent 执行器（监控版）"""

    def __init__(
        self,
        registry: Any,
        llm_processor: Optional[Any] = None,
        enable_monitoring: bool = True
    ) -> None:
        self.registry = registry
        self.llm_processor = llm_processor
        self.enable_monitoring = enable_monitoring
        self.monitor = ExecutionMonitor() if enable_monitoring else None

    async def execute(self, pef: Any, context: dict[str, Any]) -> Any:
        """执行 PEF"""
        from .core import AgentResult

        # 开始追踪
        trace = None
        if self.monitor:
            trace = self.monitor.start_trace(pef.intent)

        try:
            intent_lower: str = pef.intent.lower()

            # 使用 LLM 进行智能匹配
            matched = await self._llm_match_capability(intent_lower)

            if matched:
                if trace and self.monitor:
                    self.monitor.update_trace(trace, matched_capability=matched.id)

                params = self._extract_params(matched, pef.intent)
                result = await self.registry.execute_capability(matched.id, context=context, **params)

                if trace and self.monitor:
                    self.monitor.end_trace(trace, ExecutionStatus.SUCCESS)

                return AgentResult(success=True, message="✓ 执行成功", data=result)

            # 降级到关键词匹配
            matched = self._keyword_match_capability(intent_lower)
            if matched:
                params = self._extract_params(matched, pef.intent)
                result = await self.registry.execute_capability(matched.id, context=context, **params)

                if trace and self.monitor:
                    self.monitor.end_trace(trace, ExecutionStatus.SUCCESS)

                return AgentResult(success=True, message="✓ 执行成功", data=result)

            if trace and self.monitor:
                self.monitor.end_trace(trace, ExecutionStatus.SUCCESS)

            return AgentResult(
                success=True,
                message=f"✓ 已理解：{pef.intent}",
                data={"intent": pef.intent}
            )

        except Exception as e:
            if trace and self.monitor:
                self.monitor.end_trace(trace, ExecutionStatus.FAILED, error=str(e))

            from .core import AgentResult
            return AgentResult(success=False, message=f"执行失败：{e}", error=str(e))

    async def _llm_match_capability(self, intent: str) -> Optional[Any]:
        """使用 LLM 进行语义匹配"""
        if not self.llm_processor:
            return None

        capabilities = self.registry.list_capabilities()
        cap_list = "\n".join([
            f"- {cap.id}: {cap.name} ({cap.description}) tags={cap.tags}"
            for cap in capabilities
        ])

        prompt = f"""分析用户意图，匹配最合适的能力。

可用能力:
{cap_list}

用户意图：{intent}

请返回最匹配的能力 ID，如果没有匹配的返回 null。
只返回能力 ID，不要其他内容。"""

        try:
            result = await self.llm_processor.generate(prompt)
            matched_id = result.strip() if result else None

            if matched_id and matched_id != "null":
                return self.registry.get_capability(matched_id)
        except Exception:
            pass

        return None

    def _keyword_match_capability(self, intent: str) -> Optional[Any]:
        """关键词匹配（降级方案）"""
        for cap in self.registry.list_capabilities():
            for tag in cap.tags:
                if tag in intent or cap.name.lower() in intent:
                    return cap
            if cap.description and any(kw in intent for kw in cap.description.split()):
                return cap
        return None

    def _extract_params(self, cap: Any, intent: str) -> dict:
        """提取参数"""
        import re
        params = {}

        if cap.id == "shell":
            for pattern in [r'["\']([^"\']+)["\']', r'执行 (.+)', r'运行 (.+)']:
                match = re.search(pattern, intent)
                if match:
                    params["command"] = match.group(1).strip()
                    break
            if "command" not in params:
                params["command"] = intent.replace("执行", "").replace("运行", "").strip()
        elif cap.id == "calculator":
            match = re.search(r'([\d+\-*/().\s]+)', intent)
            if match:
                params["expression"] = match.group(1).strip()

        return params

    def get_monitor(self) -> Optional[ExecutionMonitor]:
        """获取监控器"""
        return self.monitor
