"""
LLM 后端集成模块

支持多种 LLM 提供商:
- OpenAI (GPT-4, GPT-4o, GPT-3.5-Turbo)
- Anthropic (Claude 3, Claude 3.5)
- Ollama (本地开源模型)
- 兼容 OpenAI API 的服务 (vLLM, LocalAI 等)
"""

from .backends.base import (
    LLMBackend,
    LLMResponse,
    LLMUsage,
    LLMError,
    ToolDefinition,
    ToolCall,
    Message,
    LLMRole,
    BackendRegistry,
)
from .backends.mock_backend import MockBackend
from .executor import LLMExecutor, LLMRouter, BackendConfig, create_executor, create_router

__all__ = [
    # 基类和接口
    "LLMBackend",
    "LLMResponse",
    "LLMUsage",
    "LLMError",
    "ToolDefinition",
    "ToolCall",
    "Message",
    "LLMRole",
    "BackendRegistry",
    # 后端实现
    "MockBackend",
    # 执行器和路由
    "LLMExecutor",
    "LLMRouter",
    "BackendConfig",
    "create_executor",
    "create_router",
]
