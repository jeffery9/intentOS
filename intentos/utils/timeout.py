"""
超时控制工具

提供多层级的超时控制机制

设计文档：docs/private/002-timeout-mechanism.md
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TimeoutError(Exception):
    """超时错误"""
    pass


class TimeoutLevel(Enum):
    """超时级别"""
    INSTRUCTION = "instruction"  # 指令级
    PROGRAM = "program"          # 程序级
    REQUEST = "request"          # 请求级
    LLM_CALL = "llm_call"        # LLM 调用级


@dataclass
class TimeoutConfig:
    """超时配置"""
    
    # 各层级超时时间（秒）
    instruction_timeout: float = 60.0
    program_timeout: float = 300.0
    request_timeout: float = 600.0
    llm_call_timeout: float = 30.0
    
    # 重试配置
    max_retries: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 30.0
    
    @classmethod
    def default(cls) -> TimeoutConfig:
        """默认配置"""
        return cls()
    
    @classmethod
    def strict(cls) -> TimeoutConfig:
        """严格配置（更短超时）"""
        return cls(
            instruction_timeout=30.0,
            program_timeout=120.0,
            request_timeout=300.0,
            llm_call_timeout=15.0,
        )
    
    @classmethod
    def relaxed(cls) -> TimeoutConfig:
        """宽松配置（更长超时）"""
        return cls(
            instruction_timeout=120.0,
            program_timeout=600.0,
            request_timeout=1200.0,
            llm_call_timeout=60.0,
        )
    
    def get_timeout(self, level: TimeoutLevel) -> float:
        """获取指定级别的超时时间"""
        timeout_map = {
            TimeoutLevel.INSTRUCTION: self.instruction_timeout,
            TimeoutLevel.PROGRAM: self.program_timeout,
            TimeoutLevel.REQUEST: self.request_timeout,
            TimeoutLevel.LLM_CALL: self.llm_call_timeout,
        }
        return timeout_map[level]


class TimeoutController:
    """
    超时控制器
    
    管理多层级的超时控制
    """
    
    def __init__(self, config: Optional[TimeoutConfig] = None):
        self.config = config or TimeoutConfig.default()
        self._start_time: Optional[float] = None
        self._instruction_count = 0
    
    def start(self) -> None:
        """开始计时"""
        self._start_time = time.time()
    
    def get_elapsed(self) -> float:
        """获取已过去的时间（秒）"""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time
    
    def get_remaining(self, level: TimeoutLevel) -> float:
        """获取剩余时间"""
        elapsed = self.get_elapsed()
        timeout = self.config.get_timeout(level)
        return max(0.0, timeout - elapsed)
    
    def check_timeout(self, level: TimeoutLevel) -> bool:
        """检查是否超时"""
        return self.get_remaining(level) <= 0
    
    async def execute_with_timeout(
        self,
        coro: Any,
        level: TimeoutLevel,
        operation_name: str = "",
    ) -> Any:
        """
        执行带超时的协程
        
        Args:
            coro: 要执行的协程
            level: 超时级别
            operation_name: 操作名称（用于日志）
            
        Returns:
            执行结果
            
        Raises:
            TimeoutError: 超时时抛出
        """
        timeout = self.get_remaining(level)
        name = operation_name or f"{level.value}_operation"
        
        logger.debug(f"执行 {name}, 超时限制：{timeout}秒")
        
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"{name} 超时 ({timeout}秒)")
            raise TimeoutError(f"{name} 超时 ({timeout}秒)")
    
    async def execute_with_retry(
        self,
        coro_func: Callable[..., Any],
        level: TimeoutLevel,
        operation_name: str = "",
        *args,
        **kwargs,
    ) -> Any:
        """
        执行带重试和超时的协程
        
        Args:
            coro_func: 协程函数
            level: 超时级别
            operation_name: 操作名称
            *args, **kwargs: 传递给协程函数的参数
            
        Returns:
            执行结果
        """
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # 每次重试使用完整的超时时间，而不是剩余时间
                timeout = self.config.get_timeout(level)
                coro = coro_func(*args, **kwargs)
                return await asyncio.wait_for(coro, timeout=timeout)
            except asyncio.TimeoutError:
                if attempt < self.config.max_retries:
                    delay = min(
                        self.config.retry_base_delay * (2 ** attempt),
                        self.config.retry_max_delay
                    )
                    logger.warning(
                        f"{operation_name} 超时，{delay}秒后重试 "
                        f"(第 {attempt + 1}/{self.config.max_retries} 次)"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"{operation_name} 超时，已达最大重试次数 "
                        f"({self.config.max_retries}次)"
                    )
                    raise TimeoutError(f"{operation_name} 超时，已达最大重试次数")
            except Exception as e:
                # 非超时错误，根据配置决定是否重试
                logger.exception(f"{operation_name} 执行失败：{e}")
                raise
        
        raise last_error
    
    def increment_instruction_count(self) -> int:
        """增加指令计数，返回当前计数"""
        self._instruction_count += 1
        return self._instruction_count
    
    def get_instruction_count(self) -> int:
        """获取指令执行计数"""
        return self._instruction_count


async def timeout_wrapper(
    coro: Any,
    timeout: float,
    operation_name: str = "",
) -> Any:
    """
    简单的超时包装函数
    
    适用于不需要复杂超时控制的场景
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"{operation_name} 超时 ({timeout}秒)")


# 装饰器版本
def with_timeout(
    timeout: float,
    operation_name: Optional[str] = None,
):
    """
    超时装饰器
    
    用法:
        @with_timeout(timeout=60.0, operation_name="my_operation")
        async def my_async_func():
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            name = operation_name or func.__name__
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                raise TimeoutError(f"{name} 超时 ({timeout}秒)")
        return wrapper
    return decorator
