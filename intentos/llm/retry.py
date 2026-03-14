"""
LLM 重试机制

提供带重试和超时的 LLM 调用

设计文档：docs/private/006-llm-retry.md
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RetryableErrorType(Enum):
    """可重试错误类型"""

    NETWORK_ERROR = "network_error"
    SERVER_ERROR = "server_error"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    PARSE_ERROR = "parse_error"
    CLIENT_ERROR = "client_error"
    AUTH_ERROR = "auth_error"


@dataclass
class RetryConfig:
    """重试配置"""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: float = 0.5
    timeout: float = 30.0

    enable_fallback: bool = True
    max_fallbacks: int = 2

    rate_limit_base_delay: float = 5.0
    rate_limit_max_delay: float = 300.0

    @classmethod
    def default(cls) -> RetryConfig:
        return cls()

    @classmethod
    def aggressive(cls) -> RetryConfig:
        """激进重试"""
        return cls(
            max_retries=5,
            base_delay=0.5,
            max_delay=30.0,
        )

    @classmethod
    def conservative(cls) -> RetryConfig:
        """保守重试"""
        return cls(
            max_retries=2,
            base_delay=2.0,
            max_delay=120.0,
        )

    def calculate_delay(self, attempt: int, is_rate_limit: bool = False) -> float:
        """计算延迟时间"""
        if is_rate_limit:
            delay = min(self.rate_limit_base_delay * (2**attempt), self.rate_limit_max_delay)
        else:
            delay = min(self.base_delay * (self.exponential_base**attempt), self.max_delay)

        jitter_range = delay * self.jitter
        delay += random.uniform(-jitter_range, jitter_range)

        return max(0.1, delay)


@dataclass
class RetryAttempt:
    """重试尝试记录"""

    attempt_number: int
    backend_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    error_type: Optional[RetryableErrorType] = None
    success: bool = False

    @property
    def duration(self) -> float:
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

    def to_dict(self) -> dict:
        return {
            "attempt_number": self.attempt_number,
            "backend_name": self.backend_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "error": self.error,
            "error_type": self.error_type.value if self.error_type else None,
            "success": self.success,
        }


@dataclass
class RetryResult:
    """重试结果"""

    success: bool
    response: Optional[Any] = None
    error: Optional[str] = None

    total_attempts: int = 0
    backends_used: list[str] = field(default_factory=list)
    attempts: list[RetryAttempt] = field(default_factory=list)
    total_duration: float = 0.0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "error": self.error,
            "total_attempts": self.total_attempts,
            "backends_used": self.backends_used,
            "attempts": [a.to_dict() for a in self.attempts],
            "total_duration": self.total_duration,
        }


class RetryExecutor:
    """重试执行器"""

    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        backends: Optional[list] = None,
    ):
        self.config = config or RetryConfig.default()
        self.backends = backends or []

    async def execute(
        self,
        messages: list[dict],
        **kwargs,
    ) -> RetryResult:
        """执行带重试的 LLM 调用"""
        result = RetryResult()
        start_time = time.time()

        backends_to_try = self._get_backends_to_try()

        if not backends_to_try:
            result.error = "没有可用的 LLM 后端"
            return result

        for backend in backends_to_try:
            backend_result = await self._execute_with_retries(backend, messages, **kwargs)

            result.attempts.extend(backend_result.attempts)
            result.backends_used.append(backend.get("name", "unknown"))

            if backend_result.success:
                result.success = True
                result.response = backend_result.response
                break

        result.total_attempts = len(result.attempts)
        result.total_duration = time.time() - start_time

        if not result.success:
            errors = [f"[{a.backend_name}] {a.error}" for a in result.attempts if a.error]
            result.error = "所有重试失败:\n" + "\n".join(errors)

        return result

    def _get_backends_to_try(self) -> list:
        """获取要尝试的后端列表"""
        if not self.backends:
            return []

        backends = [self.backends[0]]

        if self.config.enable_fallback and len(self.backends) > 1:
            fallbacks = self.backends[1 : self.config.max_fallbacks + 1]
            backends.extend(fallbacks)

        return backends

    async def _execute_with_retries(
        self,
        backend: dict,
        messages: list[dict],
        **kwargs,
    ) -> RetryResult:
        """在单个后端上执行带重试的调用"""
        result = RetryResult()

        for attempt in range(self.config.max_retries + 1):
            attempt_record = RetryAttempt(
                attempt_number=attempt + 1,
                backend_name=backend.get("name", "unknown"),
                start_time=datetime.now(),
            )

            try:
                # 模拟 LLM 调用
                response = await asyncio.wait_for(
                    self._call_backend(backend, messages, **kwargs), timeout=self.config.timeout
                )

                attempt_record.success = True
                attempt_record.response = response
                attempt_record.end_time = datetime.now()

                result.attempts.append(attempt_record)
                result.success = True
                result.response = response

                return result

            except asyncio.TimeoutError as e:
                attempt_record.error = f"Timeout: {e}"
                attempt_record.error_type = RetryableErrorType.TIMEOUT
                attempt_record.end_time = datetime.now()

            except Exception as e:
                attempt_record.error = f"Error: {e}"
                attempt_record.error_type = RetryableErrorType.NETWORK_ERROR
                attempt_record.end_time = datetime.now()

            result.attempts.append(attempt_record)

            if attempt < self.config.max_retries:
                is_rate_limit = attempt_record.error_type == RetryableErrorType.RATE_LIMIT
                delay = self.config.calculate_delay(attempt, is_rate_limit)

                logger.warning(
                    f"后端 {backend.get('name')} 第 {attempt + 1} 次尝试失败，"
                    f"{delay:.1f}秒后重试：{attempt_record.error}"
                )

                await asyncio.sleep(delay)

        return result

    async def _call_backend(
        self,
        backend: dict,
        messages: list[dict],
        **kwargs,
    ) -> Any:
        """调用后端（模拟）"""
        await asyncio.sleep(0.1)
        return {"content": "Mock response"}


class LLMRetryWrapper:
    """LLM 重试包装器"""

    def __init__(
        self,
        llm_executor: Any,
        config: Optional[RetryConfig] = None,
    ):
        self.llm_executor = llm_executor
        self.config = config or RetryConfig.default()
        self.retry_executor = RetryExecutor(config=self.config)

    async def execute(
        self,
        messages: list[dict],
        **kwargs,
    ) -> Any:
        """执行 LLM 调用（带重试）"""
        retry_result = await self.retry_executor.execute(messages, **kwargs)

        if retry_result.success:
            return retry_result.response
        else:
            raise Exception(f"LLM 调用失败：{retry_result.error}")

    async def execute_with_fallback(
        self,
        messages: list[dict],
        fallback_response: Optional[Any] = None,
        **kwargs,
    ) -> Any:
        """执行带降级的 LLM 调用"""
        try:
            return await self.execute(messages, **kwargs)
        except Exception as e:
            logger.warning(f"LLM 调用失败，使用降级响应：{e}")

            if fallback_response:
                return fallback_response
            else:
                return {"content": "抱歉，服务暂时不可用，请稍后重试。"}
