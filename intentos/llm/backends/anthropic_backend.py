"""
Anthropic 后端集成

支持:
- Claude 3 Opus
- Claude 3 Sonnet
- Claude 3 Haiku
- Claude 3.5 Sonnet
"""

from __future__ import annotations
import time
from typing import Optional, AsyncIterator

from .base import (
    LLMBackend,
    LLMResponse,
    LLMUsage,
    LLMError,
    RateLimitError,
    AuthenticationError,
    TimeoutError,
    Message,
    ToolDefinition,
    ToolCall,
    LLMRole,
)


class AnthropicBackend(LLMBackend):
    """Anthropic LLM 后端"""
    
    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs,
    ):
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )
        self._client = None
        self._async_client = None
    
    def _get_client(self):
        """获取同步客户端"""
        if self._client is None:
            try:
                from anthropic import Anthropic
            except ImportError:
                raise ImportError("请安装 anthropic: pip install anthropic")
            
            self._client = Anthropic(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=self.max_retries,
            )
        return self._client
    
    def _get_async_client(self):
        """获取异步客户端"""
        if self._async_client is None:
            try:
                from anthropic import AsyncAnthropic
            except ImportError:
                raise ImportError("请安装 anthropic: pip install anthropic")
            
            self._async_client = AsyncAnthropic(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=self.max_retries,
            )
        return self._async_client
    
    async def generate(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs,
    ) -> LLMResponse:
        """生成响应"""
        start_time = time.time()
        
        client = self._get_async_client()
        
        # 分离 system 消息
        system_message = ""
        user_messages = []
        for msg in messages:
            if msg.role == LLMRole.SYSTEM:
                system_message = msg.content
            else:
                user_messages.append(msg)
        
        # 转换消息格式
        anthropic_messages = self._convert_messages(user_messages)
        
        # 转换工具格式
        anthropic_tools = self._convert_tools(tools) if tools else None
        
        try:
            response = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens or 4096,
                system=system_message,
                messages=anthropic_messages,
                tools=anthropic_tools,
                temperature=temperature,
                stream=stream,
                **kwargs,
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # 解析响应
            content = ""
            tool_calls = []
            
            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "tool_use":
                    tool_calls.append(ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input,
                    ))
            
            usage = LLMUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            )
            
            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
                tool_calls=tool_calls,
                finish_reason=response.stop_reason or "stop",
                raw_response=response,
                latency_ms=latency_ms,
            )
            
        except Exception as e:
            raise self._convert_error(e)
    
    async def generate_stream(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """流式生成"""
        client = self._get_async_client()
        
        # 分离 system 消息
        system_message = ""
        user_messages = []
        for msg in messages:
            if msg.role == LLMRole.SYSTEM:
                system_message = msg.content
            else:
                user_messages.append(msg)
        
        anthropic_messages = self._convert_messages(user_messages)
        anthropic_tools = self._convert_tools(tools) if tools else None
        
        try:
            async with client.messages.stream(
                model=self.model,
                max_tokens=max_tokens or 4096,
                system=system_message,
                messages=anthropic_messages,
                tools=anthropic_tools,
                temperature=temperature,
                **kwargs,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise self._convert_error(e)
    
    def validate_connection(self) -> bool:
        """验证连接"""
        try:
            client = self._get_client()
            # 简单测试
            client.models.list()
            return True
        except Exception:
            return False
    
    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """转换消息为 Anthropic 格式"""
        result = []
        for msg in messages:
            if msg.role == LLMRole.USER:
                result.append({
                    "role": "user",
                    "content": msg.content,
                })
            elif msg.role == LLMRole.ASSISTANT:
                result.append({
                    "role": "assistant",
                    "content": msg.content,
                })
            elif msg.role == LLMRole.TOOL:
                # 工具响应
                result.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id,
                            "content": msg.content,
                        }
                    ],
                })
        return result
    
    def _convert_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        """转换工具为 Anthropic 格式"""
        result = []
        for tool in tools:
            result.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters,
            })
        return result
    
    def _convert_error(self, error: Exception) -> LLMError:
        """转换错误类型"""
        try:
            from anthropic import (
                RateLimitError as AnthropicRateLimit,
                AuthenticationError as AnthropicAuth,
                APITimeoutError as AnthropicTimeout,
            )
            
            if isinstance(error, AnthropicRateLimit):
                return RateLimitError(
                    str(error),
                    code=getattr(error, "code", None),
                    raw_error=error,
                )
            elif isinstance(error, AnthropicAuth):
                return AuthenticationError(
                    str(error),
                    code=getattr(error, "code", None),
                    raw_error=error,
                )
            elif isinstance(error, AnthropicTimeout):
                return TimeoutError(
                    str(error),
                    code=getattr(error, "code", None),
                    raw_error=error,
                )
        except ImportError:
            pass
        
        return LLMError(str(error), raw_error=error)
    
    @property
    def provider_name(self) -> str:
        return "Anthropic"
