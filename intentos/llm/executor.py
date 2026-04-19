"""
LLM 执行器和路由器

支持:
- 多后端路由
- 故障转移
- 负载均衡
- 成本优化路由
- 顾问策略 (常规模型优先，遇难转大模型)
"""

from __future__ import annotations

import random
import time
import logging
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional

from .backends.base import (
    AuthenticationError,
    LLMBackend,
    LLMError,
    LLMResponse,
    LLMRole,
    Message,
    RateLimitError,
    TimeoutError,
    ToolDefinition,
)
from .backends.mock_backend import MockBackend

logger = logging.getLogger(__name__)


@dataclass
class BackendConfig:
    """后端配置"""

    name: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    priority: int = 5  # 优先级 (1-10, 越高越优先)
    weight: float = 1.0  # 权重 (用于负载均衡)
    max_qps: float = float("inf")  # 最大每秒请求数
    enabled: bool = True  # 是否启用
    is_consultant: bool = False  # 是否作为顾问模型 (用于顾问测试模式)

    # 重试配置
    max_retries: int = 3
    retry_delay: float = 1.0

    # 超时配置
    timeout: int = 60


@dataclass
class BackendStats:
    """后端统计信息"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0  # 估算成本
    avg_latency_ms: float = 0.0
    last_error: Optional[str] = None
    last_error_time: Optional[float] = None

    # 速率限制追踪
    requests_last_second: int = 0
    last_request_time: float = 0.0

    def record_success(self, latency_ms: int, tokens: int) -> None:
        """记录成功请求"""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_tokens += tokens

        # 指数移动平均更新延迟
        alpha = 0.1
        self.avg_latency_ms = alpha * latency_ms + (1 - alpha) * self.avg_latency_ms

        # 更新速率限制追踪
        current_time = time.time()
        if current_time - self.last_request_time > 1.0:
            self.requests_last_second = 1
        else:
            self.requests_last_second += 1
        self.last_request_time = current_time

    def record_failure(self, error: str) -> None:
        """记录失败请求"""
        self.total_requests += 1
        self.failed_requests += 1
        self.last_error = error
        self.last_error_time = time.time()

    @property
    def success_rate(self) -> float:
        """获取成功率"""
        if self.total_requests == 0:
            return 100.0
        return self.successful_requests / self.total_requests * 100

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "avg_latency_ms": self.avg_latency_ms,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time,
        }


class LLMRouter:
    """
    LLM 路由器

    支持多种路由策略:
    - priority: 优先级路由
    - round_robin: 轮询
    - weighted: 加权随机
    - latency: 最低延迟优先
    - cost: 成本优化
    - consultant: 顾问策略 (常规模型执行，遇难转向高精度模型)
    """

    CONSULTANT_TAG = "[HARD_TASK]"

    def __init__(self, configs: list[BackendConfig]):
        self.configs = configs
        self.backends: dict[str, LLMBackend] = {}
        self.stats: dict[str, BackendStats] = {}
        self._round_robin_index = 0

        # 初始化后端和统计
        for config in configs:
            if config.enabled:
                self._create_backend(config)
                self.stats[config.name] = BackendStats()

    def _create_backend(self, config: BackendConfig) -> None:
        """创建后端实例"""
        # 根据配置创建对应的后端
        backend: LLMBackend

        if "openai" in config.name.lower() or config.base_url:
            from .backends.openai_backend import OpenAIBackend

            backend = OpenAIBackend(
                model=config.model,
                api_key=config.api_key,
                base_url=config.base_url,
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        elif "anthropic" in config.name.lower():
            from .backends.anthropic_backend import AnthropicBackend

            backend = AnthropicBackend(  # type: ignore
                model=config.model,
                api_key=config.api_key,
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        elif "ollama" in config.name.lower():
            from .backends.ollama_backend import OllamaBackend

            backend = OllamaBackend(  # type: ignore
                model=config.model,
                host=config.base_url or "http://localhost:11434",
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        else:
            # 默认使用 Mock
            backend = MockBackend(model=config.model)  # type: ignore

        self.backends[config.name] = backend

    def select_backend(
        self, strategy: str = "priority", filter_consultants: Optional[bool] = None
    ) -> tuple[str, LLMBackend]:
        """
        选择后端

        Args:
            strategy: 路由策略
            filter_consultants: 是否只选择顾问模型 (True) 或非顾问模型 (False)
        """
        available_names = [
            name
            for name, backend in self.backends.items()
            if self.stats[name].requests_last_second < self._get_config(name).max_qps
        ]

        if filter_consultants is not None:
            available_names = [
                name
                for name in available_names
                if self._get_config(name).is_consultant == filter_consultants
            ]

        available = [(name, self.backends[name]) for name in available_names]

        if not available:
            # 如果按过滤条件找不到，且有过滤条件，则抛出异常
            if filter_consultants is not None:
                type_str = "顾问" if filter_consultants else "专家"
                raise LLMError(f"没有可用的{type_str}后端")

            #  fallback 到所有可用后端
            available = list(self.backends.items())

        if not available:
            raise LLMError("没有可用的后端")

        if strategy == "priority" or strategy == "consultant":
            return self._select_by_priority(available)
        elif strategy == "round_robin":
            return self._select_round_robin(available)
        elif strategy == "weighted":
            return self._select_weighted(available)
        elif strategy == "latency":
            return self._select_by_latency(available)
        elif strategy == "cost":
            return self._select_by_cost(available)
        else:
            return available[0]

    def _select_by_priority(self, available: list) -> tuple[str, LLMBackend]:
        """按优先级选择"""
        sorted_backends = sorted(
            available,
            key=lambda x: self._get_config(x[0]).priority,
            reverse=True,
        )
        return sorted_backends[0]

    def _select_round_robin(self, available: list) -> tuple[str, LLMBackend]:
        """轮询选择"""
        self._round_robin_index = (self._round_robin_index + 1) % len(available)
        return available[self._round_robin_index]

    def _select_weighted(self, available: list) -> tuple[str, LLMBackend]:
        """加权随机选择"""
        weights = [self._get_config(name).weight for name, _ in available]
        return random.choices(available, weights=weights, k=1)[0]

    def _select_by_latency(self, available: list) -> tuple[str, LLMBackend]:
        """按延迟选择"""
        sorted_backends = sorted(
            available,
            key=lambda x: self.stats[x[0]].avg_latency_ms,
        )
        return sorted_backends[0]

    def _select_by_cost(self, available: list) -> tuple[str, LLMBackend]:
        """按成本选择 (简化实现)"""
        # 这里可以根据模型的每 token 成本排序
        # 简化为随机选择
        return random.choice(available)

    def _get_config(self, name: str) -> BackendConfig:
        """获取配置"""
        for config in self.configs:
            if config.name == name:
                return config
        raise ValueError(f"未知后端：{name}")

    async def generate(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        strategy: str = "priority",
        **kwargs,
    ) -> LLMResponse:
        """
        生成响应 (支持故障转移与顾问策略)
        """
        if strategy == "consultant":
            return await self._generate_with_consultant_strategy(
                messages, tools, temperature, max_tokens, **kwargs
            )

        last_error: Optional[LLMError] = None
        tried_backends: list[str] = []

        for attempt in range(len(self.backends)):
            try:
                # 选择后端
                name, backend = self.select_backend(strategy)

                if name in tried_backends:
                    # 避免重复尝试同一个后端
                    if len(tried_backends) >= len(self.backends):
                        break
                    continue

                tried_backends.append(name)

                # 生成响应
                response = await backend.generate(
                    messages=messages,
                    tools=tools,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )

                # 记录成功
                self.stats[name].record_success(
                    latency_ms=response.latency_ms,
                    tokens=response.usage.total_tokens,
                )

                return response

            except (RateLimitError, TimeoutError) as e:
                # 可重试的错误，尝试下一个后端
                last_error = e
                if name in self.stats:
                    self.stats[name].record_failure(str(e))
                continue

            except AuthenticationError as e:
                # 认证错误，不可重试
                raise e

            except LLMError as e:
                last_error = e
                if name in self.stats:
                    self.stats[name].record_failure(str(e))
                continue

        # 所有后端都失败
        raise LLMError(
            f"所有后端都失败：{last_error}",
            raw_error=last_error,
        )

    async def _generate_with_consultant_strategy(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """顾问策略具体实现：常规模型处理，难题请教高精度专家"""
        # 1. 尝试常规模型 (标记为 is_consultant=True)
        try:
            name, backend = self.select_backend(strategy="priority", filter_consultants=True)
            logger.info(f"[Router] 顾问策略: 优先尝试常规模型 '{name}'")

            # 为常规模型增加指令，明确告知如果任务复杂请返回特定标记
            consultant_messages = list(messages)
            system_instruction = (
                f"你是一个常规任务处理器。如果接下来的任务非常复杂、需要极高精度的逻辑推理、"
                f"或者你认为当前任务超出了你的可靠处理范围，请务必在回复的开头包含标记 '{self.CONSULTANT_TAG}'。"
            )

            # 检查是否已有系统消息
            has_system = False
            for msg in consultant_messages:
                if msg.role == LLMRole.SYSTEM:
                    msg.content = system_instruction + "\n" + msg.content
                    has_system = True
                    break

            if not has_system:
                consultant_messages.insert(0, Message.system(system_instruction))

            response = await backend.generate(
                messages=consultant_messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            # 记录成功
            self.stats[name].record_success(
                latency_ms=response.latency_ms,
                tokens=response.usage.total_tokens,
            )

            # 2. 检查是否需要转向高精度专家模型
            if self.CONSULTANT_TAG in response.content:
                logger.info(f"[Router] 触发升级: 常规模型 '{name}' 请求高精度专家支援")
                # 识别为难题，转向高精度专家模型
                try:
                    expert_name, expert_backend = self.select_backend(
                        strategy="priority", filter_consultants=False
                    )
                    logger.info(f"[Router] 切换至专家模型 '{expert_name}'")

                    # 调用专家模型（使用原始消息，确保高精度）
                    expert_response = await expert_backend.generate(
                        messages=messages,
                        tools=tools,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs,
                    )

                    # 记录成功
                    self.stats[expert_name].record_success(
                        latency_ms=expert_response.latency_ms,
                        tokens=expert_response.usage.total_tokens,
                    )

                    return expert_response
                except LLMError as e:
                    logger.warning(f"[Router] 专家模型不可用，回退常规模型响应: {e}")
                    return response

            logger.info(f"[Router] 顾问策略: 常规模型成功解决任务")
            return response

        except LLMError:
            # 如果没有常规模型或失败，直接尝试高精度专家
            expert_name, expert_backend = self.select_backend(
                strategy="priority", filter_consultants=False
            )
            expert_response = await expert_backend.generate(
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            self.stats[expert_name].record_success(
                latency_ms=expert_response.latency_ms,
                tokens=expert_response.usage.total_tokens,
            )
            return expert_response

    def get_stats(self) -> dict[str, dict]:
        """获取所有后端统计"""
        return {
            name: {
                "total_requests": stats.total_requests,
                "success_rate": (
                    stats.successful_requests / stats.total_requests * 100
                    if stats.total_requests > 0
                    else 0
                ),
                "avg_latency_ms": stats.avg_latency_ms,
                "total_tokens": stats.total_tokens,
                "last_error": stats.last_error,
            }
            for name, stats in self.stats.items()
        }


class LLMExecutor:
    """
    LLM 执行器

    统一的高层接口，支持单后端和多后端路由
    """

    def __init__(
        self,
        provider: str = "mock",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        router: Optional[LLMRouter] = None,
        **kwargs,
    ):
        """
        初始化执行器

        Args:
            provider: 提供商名称 (mock, openai, anthropic, ollama)
            model: 模型名称
            api_key: API 密钥
            base_url: API 基础 URL
            router: 路由器 (多后端时使用)
            **kwargs: 其他配置
        """
        self.router = router
        self._single_backend = None

        if router is None:
            # 单后端模式
            self._single_backend = self._create_backend(
                provider=provider,
                model=model,
                api_key=api_key,
                base_url=base_url,
                **kwargs,
            )

    def _create_backend(
        self,
        provider: str,
        model: Optional[str],
        api_key: Optional[str],
        base_url: Optional[str],
        **kwargs,
    ) -> LLMBackend:
        """创建后端实例"""
        provider_lower = provider.lower()

        if provider_lower == "mock":
            return MockBackend(model=model or "mock-model")

        elif provider_lower == "openai":
            from .backends.openai_backend import OpenAIBackend

            return OpenAIBackend(
                model=model or "gpt-4o",
                api_key=api_key,
                base_url=base_url,
                **kwargs,
            )

        elif provider_lower == "anthropic":
            from .backends.anthropic_backend import AnthropicBackend

            return AnthropicBackend(
                model=model or "claude-3-5-sonnet-20241022",
                api_key=api_key,
                **kwargs,
            )

        elif provider_lower == "ollama":
            from .backends.ollama_backend import OllamaBackend

            return OllamaBackend(
                model=model or "llama3.1",
                host=base_url or "http://localhost:11434",
                **kwargs,
            )

        else:
            raise ValueError(f"未知提供商：{provider}")

    async def execute(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs,
    ) -> LLMResponse:
        """
        执行 LLM 调用
        """
        if self.router:
            # 路由模式
            return await self.router.generate(
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        else:
            # 单后端模式
            return await self._single_backend.generate(  # type: ignore
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs,
            )

    async def generate_stream(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """流式生成"""
        if self.router:
            async for chunk in self.router.generate(  # type: ignore
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            ):
                yield chunk
        else:
            async for chunk in self._single_backend.generate_stream(  # type: ignore
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            ):
                yield chunk

    def get_stats(self) -> dict:
        """获取统计信息"""
        if self.router:
            return self.router.get_stats()
        else:
            return {"provider": self._single_backend.provider_name}  # type: ignore


# 便捷函数
def create_executor(
    provider: str = "mock",
    **kwargs,
) -> LLMExecutor:
    """创建执行器"""
    return LLMExecutor(provider=provider, **kwargs)


def create_router(
    configs: list[dict | BackendConfig],
) -> LLMRouter:
    """创建路由器"""
    backend_configs = []
    for c in configs:
        if isinstance(c, BackendConfig):
            backend_configs.append(c)
        else:
            backend_configs.append(BackendConfig(**c))
    return LLMRouter(backend_configs)
