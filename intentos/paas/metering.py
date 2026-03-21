# -*- coding: utf-8 -*-
"""
IntentOS Usage Metering Module

用量计量模块，负责记录和统计 AI Native App 的资源使用情况。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger: logging.Logger = logging.getLogger(__name__)


class UsageUnit(Enum):
    """用量单位"""
    CPU_MILLISECOND = "cpu_ms"        # CPU 毫秒
    TOKEN = "token"                    # Token 数量
    MEMORY_MB = "memory_mb"            # 内存 MB
    API_CALL = "api_call"              # API 调用次数
    EXECUTION_SECOND = "exec_sec"      # 执行秒数
    STORAGE_MB = "storage_mb"          # 存储 MB
    BANDWIDTH_MB = "bandwidth_mb"      # 带宽 MB
    REQUEST = "request"                # 请求次数


@dataclass
class UsageRecord:
    """单条用量记录"""
    unit: UsageUnit
    amount: float
    timestamp: datetime = field(default_factory=datetime.now)
    description: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "unit": self.unit.value,
            "amount": self.amount,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "metadata": self.metadata,
        }


@dataclass
class UsageSummary:
    """用量汇总"""
    user_id: str
    session_id: Optional[str]
    period_start: datetime
    period_end: datetime
    records: list[UsageRecord] = field(default_factory=list)

    # 汇总数据
    cpu_time_ms: float = 0.0
    tokens_used: int = 0
    memory_mb: float = 0.0
    api_calls: int = 0
    execution_time_sec: float = 0.0
    storage_mb: float = 0.0
    bandwidth_mb: float = 0.0
    requests: int = 0

    def add_record(self, record: UsageRecord) -> None:
        """添加记录并更新汇总"""
        self.records.append(record)

        if record.unit == UsageUnit.CPU_MILLISECOND:
            self.cpu_time_ms += record.amount
        elif record.unit == UsageUnit.TOKEN:
            self.tokens_used += int(record.amount)
        elif record.unit == UsageUnit.MEMORY_MB:
            self.memory_mb += record.amount
        elif record.unit == UsageUnit.API_CALL:
            self.api_calls += int(record.amount)
        elif record.unit == UsageUnit.EXECUTION_SECOND:
            self.execution_time_sec += record.amount
        elif record.unit == UsageUnit.STORAGE_MB:
            self.storage_mb += record.amount
        elif record.unit == UsageUnit.BANDWIDTH_MB:
            self.bandwidth_mb += record.amount
        elif record.unit == UsageUnit.REQUEST:
            self.requests += int(record.amount)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "summary": {
                "cpu_time_ms": round(self.cpu_time_ms, 2),
                "tokens_used": self.tokens_used,
                "memory_mb": round(self.memory_mb, 2),
                "api_calls": self.api_calls,
                "execution_time_sec": round(self.execution_time_sec, 2),
                "storage_mb": round(self.storage_mb, 2),
                "bandwidth_mb": round(self.bandwidth_mb, 2),
                "requests": self.requests,
            },
            "record_count": len(self.records),
        }


class UsageMeter:
    """
    用量计量器

    用于记录单个会话或执行的资源使用情况。
    """

    def __init__(self, user_id: str, session_id: Optional[str] = None) -> None:
        self.user_id: str = user_id
        self.session_id: Optional[str] = session_id
        self.records: list[UsageRecord] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self._execution_start: Optional[float] = None

    def start(self) -> None:
        """开始计量"""
        self.start_time = datetime.now()
        self._execution_start = time.time()
        logger.info(f"用量计量开始：user={self.user_id}, session={self.session_id}")

    def stop(self) -> UsageSummary:
        """停止计量并返回汇总"""
        self.end_time = datetime.now()

        # 自动记录执行时间
        if self._execution_start:
            exec_time = time.time() - self._execution_start
            self.record(UsageUnit.EXECUTION_SECOND, exec_time, description="执行时长")

        logger.info(f"用量计量结束：user={self.user_id}, session={self.session_id}")
        return self.get_summary()

    def record(
        self,
        unit: UsageUnit,
        amount: float,
        description: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """记录用量"""
        record = UsageRecord(
            unit=unit,
            amount=amount,
            description=description,
            metadata=metadata or {},
        )
        self.records.append(record)
        logger.debug(f"记录用量：{unit.value}={amount}, desc={description}")

    def record_cpu(self, ms: float, description: Optional[str] = None) -> None:
        """记录 CPU 时间"""
        self.record(UsageUnit.CPU_MILLISECOND, ms, description)

    def record_tokens(self, count: int, description: Optional[str] = None) -> None:
        """记录 Token 使用"""
        self.record(UsageUnit.TOKEN, float(count), description)

    def record_memory(self, mb: float, description: Optional[str] = None) -> None:
        """记录内存使用"""
        self.record(UsageUnit.MEMORY_MB, mb, description)

    def record_api_call(self, description: Optional[str] = None) -> None:
        """记录 API 调用"""
        self.record(UsageUnit.API_CALL, 1, description)

    def record_request(self, description: Optional[str] = None) -> None:
        """记录请求"""
        self.record(UsageUnit.REQUEST, 1, description)

    def get_summary(self) -> UsageSummary:
        """获取用量汇总"""
        summary = UsageSummary(
            user_id=self.user_id,
            session_id=self.session_id,
            period_start=self.start_time or datetime.now(),
            period_end=self.end_time or datetime.now(),
        )

        for record in self.records:
            summary.add_record(record)

        return summary

    def get_usage(self) -> dict[str, Any]:
        """获取用量字典（兼容旧接口）"""
        summary = self.get_summary()
        return {
            "cpu_time_ms": summary.cpu_time_ms,
            "tokens_used": summary.tokens_used,
            "execution_time_sec": summary.execution_time_sec,
            "memory_mb": summary.memory_mb,
            "api_calls": summary.api_calls,
            "requests": summary.requests,
        }

    def reset(self) -> None:
        """重置计量器"""
        self.records.clear()
        self.start_time = None
        self.end_time = None
        self._execution_start = None
        logger.info(f"用量计量重置：user={self.user_id}")


class MeteringService:
    """
    计量服务

    管理多个用户的用量计量，支持持久化和查询。
    """

    def __init__(self) -> None:
        self.meters: dict[str, UsageMeter] = {}
        self.summaries: dict[str, list[UsageSummary]] = {}
        logger.info("计量服务初始化完成")

    def get_or_create_meter(self, user_id: str, session_id: Optional[str] = None) -> UsageMeter:
        """获取或创建计量器"""
        key = f"{user_id}:{session_id}" if session_id else user_id

        if key not in self.meters:
            self.meters[key] = UsageMeter(user_id, session_id)
            logger.info(f"创建新计量器：{key}")

        return self.meters[key]

    def finalize_meter(self, user_id: str, session_id: Optional[str] = None) -> UsageSummary:
        """停止计量器并保存汇总"""
        key = f"{user_id}:{session_id}" if session_id else user_id

        if key not in self.meters:
            raise ValueError(f"计量器不存在：{key}")

        meter = self.meters[key]
        summary = meter.stop()

        # 保存汇总
        if user_id not in self.summaries:
            self.summaries[user_id] = []
        self.summaries[user_id].append(summary)

        # 移除计量器
        del self.meters[key]
        logger.info(f"计量器已保存：{key}")

        return summary

    def get_user_summaries(
        self,
        user_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> list[UsageSummary]:
        """获取用户用量汇总"""
        if user_id not in self.summaries:
            return []

        summaries = self.summaries[user_id]

        # 按时间过滤
        if period_start:
            summaries = [s for s in summaries if s.period_end >= period_start]
        if period_end:
            summaries = [s for s in summaries if s.period_start <= period_end]

        return summaries

    def get_user_usage(
        self,
        user_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> dict[str, Any]:
        """获取用户用量汇总（聚合）"""
        summaries = self.get_user_summaries(user_id, period_start, period_end)

        if not summaries:
            return {
                "user_id": user_id,
                "period": {
                    "start": period_start.isoformat() if period_start else None,
                    "end": period_end.isoformat() if period_end else None,
                },
                "total": {
                    "cpu_time_ms": 0,
                    "tokens_used": 0,
                    "execution_time_sec": 0,
                    "memory_mb": 0,
                    "api_calls": 0,
                    "requests": 0,
                },
            }

        # 聚合数据
        total_cpu = sum(s.cpu_time_ms for s in summaries)
        total_tokens = sum(s.tokens_used for s in summaries)
        total_exec = sum(s.execution_time_sec for s in summaries)
        total_memory = sum(s.memory_mb for s in summaries)
        total_api = sum(s.api_calls for s in summaries)
        total_requests = sum(s.requests for s in summaries)

        return {
            "user_id": user_id,
            "period": {
                "start": period_start.isoformat() if period_start else None,
                "end": period_end.isoformat() if period_end else None,
            },
            "total": {
                "cpu_time_ms": round(total_cpu, 2),
                "tokens_used": total_tokens,
                "execution_time_sec": round(total_exec, 2),
                "memory_mb": round(total_memory, 2),
                "api_calls": total_api,
                "requests": total_requests,
            },
            "session_count": len(summaries),
        }

    def clear_user_data(self, user_id: str) -> None:
        """清除用户数据"""
        if user_id in self.summaries:
            del self.summaries[user_id]
        logger.info(f"清除用户数据：{user_id}")


# 全局计量服务实例
_global_metering_service: Optional[MeteringService] = None


def get_metering_service() -> MeteringService:
    """获取全局计量服务"""
    global _global_metering_service
    if _global_metering_service is None:
        _global_metering_service = MeteringService()
    return _global_metering_service


def reset_metering_service() -> None:
    """重置全局计量服务"""
    global _global_metering_service
    _global_metering_service = None
