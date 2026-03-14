"""
LLM 后端抽象基类

定义所有 LLM 后端必须实现的统一接口
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Callable, Optional


class LLMRole(Enum):
    """消息角色"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """LLM 消息"""

    role: LLMRole
    content: str
    name: Optional[str] = None  # 工具调用时的名称
    tool_call_id: Optional[str] = None  # 工具调用 ID

    def to_dict(self) -> dict:
        """转换为字典"""
        d = {
            "role": self.role.value,
            "content": self.content,
        }
        if self.name:
            d["name"] = self.name
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        return d

    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(role=LLMRole.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role=LLMRole.USER, content=content)

    @classmethod
    def assistant(cls, content: str) -> "Message":
        return cls(role=LLMRole.ASSISTANT, content=content)

    @classmethod
    def tool(cls, content: str, name: str, tool_call_id: str) -> "Message":
        return cls(
            role=LLMRole.TOOL,
            content=content,
            name=name,
            tool_call_id=tool_call_id,
        )


@dataclass
class ToolDefinition:
    """工具定义"""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema
    func: Optional[Callable] = None  # 可选的本地函数

    def to_dict(self) -> dict:
        """转换为 OpenAI 兼容格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ToolCall:
    """工具调用"""

    id: str
    name: str
    arguments: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict) -> "ToolCall":
        """从字典创建"""
        if "function" in data:  # OpenAI 格式
            return cls(
                id=data["id"],
                name=data["function"]["name"],
                arguments=data["function"]["arguments"]
                if isinstance(data["function"]["arguments"], dict)
                else data["function"]["arguments"],
            )
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            arguments=data.get("arguments", {}),
        )


@dataclass
class LLMUsage:
    """Token 使用统计"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    # 扩展字段 (不同提供商可能不同)
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "LLMUsage":
        """从字典创建"""
        usage = data.get("usage", data)
        return cls(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            extra={
                k: v
                for k, v in usage.items()
                if k not in ["prompt_tokens", "completion_tokens", "total_tokens"]
            },
        )


@dataclass
class LLMResponse:
    """LLM 响应"""

    content: str
    model: str
    usage: LLMUsage
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"
    raw_response: Any = None  # 原始响应对象
    latency_ms: int = 0  # 延迟 (毫秒)

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class LLMError(Exception):
    """LLM 错误基类"""

    def __init__(self, message: str, code: Optional[str] = None, raw_error: Any = None):
        super().__init__(message)
        self.code = code
        self.raw_error = raw_error


class RateLimitError(LLMError):
    """速率限制错误"""

    pass


class AuthenticationError(LLMError):
    """认证错误"""

    pass


class TimeoutError(LLMError):
    """超时错误"""

    pass


class LLMBackend(ABC):
    """
    LLM 后端抽象基类

    所有 LLM 提供商必须实现此接口
    """

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs,
    ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.extra_config = kwargs

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs,
    ) -> LLMResponse:
        """
        生成响应

        Args:
            messages: 消息列表
            tools: 工具定义列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            stream: 是否流式输出
            **kwargs: 其他参数

        Returns:
            LLM 响应
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        流式生成

        Yields:
            生成的文本片段
        """
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """
        验证连接

        Returns:
            是否连接成功
        """
        pass

    def _create_usage_from_tokens(
        self,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> LLMUsage:
        """从 token 数创建 Usage 对象"""
        return LLMUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )

    def _estimate_tokens(self, text: str) -> int:
        """估算文本的 token 数 (英文约 4 字符/token，中文约 1.5 字符/token)"""
        # 简化估算
        chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)

    @property
    def provider_name(self) -> str:
        """返回提供商名称"""
        return self.__class__.__name__.replace("Backend", "")


class BackendRegistry:
    """后端注册中心"""

    _backends: dict[str, type[LLMBackend]] = {}

    @classmethod
    def register(cls, name: str, backend_class: type[LLMBackend]) -> None:
        """注册后端"""
        cls._backends[name] = backend_class

    @classmethod
    def get(cls, name: str) -> Optional[type[LLMBackend]]:
        """获取后端类"""
        return cls._backends.get(name)

    @classmethod
    def list_backends(cls) -> list[str]:
        """列出所有注册的后端"""
        return list(cls._backends.keys())

    @classmethod
    def create(
        cls,
        name: str,
        model: str,
        **kwargs,
    ) -> LLMBackend:
        """创建后端实例"""
        backend_class = cls.get(name)
        if not backend_class:
            raise ValueError(f"未知后端：{name}")
        return backend_class(model=model, **kwargs)


# 注册默认后端
def _register_default_backends():
    """注册默认后端"""
    # 延迟导入避免循环依赖
    try:
        from .openai_backend import OpenAIBackend

        BackendRegistry.register("openai", OpenAIBackend)
    except ImportError:
        pass

    try:
        from .anthropic_backend import AnthropicBackend

        BackendRegistry.register("anthropic", AnthropicBackend)
    except ImportError:
        pass

    try:
        from .ollama_backend import OllamaBackend

        BackendRegistry.register("ollama", OllamaBackend)
    except ImportError:
        pass

    from .mock_backend import MockBackend

    BackendRegistry.register("mock", MockBackend)


_register_default_backends()
