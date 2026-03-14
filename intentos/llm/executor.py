"""
LLM 执行器和路由器

支持:
- 多后端路由
- 故障转移
- 负载均衡
- 成本优化路由
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import AsyncIterator, Optional

from .backends.base import (
    AuthenticationError,
    LLMBackend,
    LLMError,
    LLMResponse,
    Message,
    RateLimitError,
    TimeoutError,
    ToolDefinition,
)
from .backends.mock_backend import MockBackend


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
        """计算成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

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
    """

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

            backend = AnthropicBackend(
                model=config.model,
                api_key=config.api_key,
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        elif "ollama" in config.name.lower():
            from .backends.ollama_backend import OllamaBackend

            backend = OllamaBackend(
                model=config.model,
                host=config.base_url or "http://localhost:11434",
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        else:
            # 默认使用 Mock
            backend = MockBackend(model=config.model)

        self.backends[config.name] = backend

    def select_backend(self, strategy: str = "priority") -> tuple[str, LLMBackend]:
        """选择后端"""
        available = [
            (name, backend)
            for name, backend in self.backends.items()
            if self.stats[name].requests_last_second < self._get_config(name).max_qps
        ]

        if not available:
            # 如果所有后端都限流，返回优先级最高的
            available = list(self.backends.items())

        if not available:
            raise LLMError("没有可用的后端")

        if strategy == "priority":
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
        生成响应 (带故障转移)
        """
        last_error = None
        tried_backends = []

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
            return await self._single_backend.generate(
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
            async for chunk in self.router.generate(
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            ):
                yield chunk
        else:
            async for chunk in self._single_backend.generate_stream(
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
            return {"provider": self._single_backend.provider_name}


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
