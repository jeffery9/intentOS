"""
OpenAI 后端集成

支持:
- GPT-4, GPT-4o, GPT-4-Turbo
- GPT-3.5-Turbo
- 兼容 OpenAI API 的服务 (vLLM, LocalAI, Azure OpenAI 等)
"""

from __future__ import annotations

import time
from typing import AsyncIterator, Optional

from .base import (
    AuthenticationError,
    LLMBackend,
    LLMError,
    LLMResponse,
    LLMUsage,
    Message,
    RateLimitError,
    TimeoutError,
    ToolCall,
    ToolDefinition,
)


class OpenAIBackend(LLMBackend):
    """OpenAI LLM 后端"""

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        organization: Optional[str] = None,
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
        self.organization = organization
        self._client = None
        self._async_client = None

    def _get_client(self):
        """获取同步客户端"""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("请安装 openai: pip install openai")

            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                organization=self.organization,
                timeout=self.timeout,
                max_retries=self.max_retries,
            )
        return self._client

    def _get_async_client(self):
        """获取异步客户端"""
        if self._async_client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise ImportError("请安装 openai: pip install openai")

            self._async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                organization=self.organization,
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

        # 转换消息格式
        openai_messages = self._convert_messages(messages)

        # 转换工具格式
        openai_tools = [t.to_dict() for t in tools] if tools else None

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=openai_tools,
                tool_choice="auto" if openai_tools else None,
                stream=stream,
                **kwargs,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            # 解析响应
            choice = response.choices[0]
            content = choice.message.content or ""
            tool_calls = self._parse_tool_calls(choice.message.tool_calls)
            usage = LLMUsage.from_dict(response.model_dump())

            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason or "stop",
                raw_response=response,
                latency_ms=latency_ms,
            )

        except Exception as e:
            raise self._convert_error(e)

    async def generate_stream(  # type: ignore
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """流式生成"""
        client = self._get_async_client()
        openai_messages = self._convert_messages(messages)
        openai_tools = [t.to_dict() for t in tools] if tools else None

        try:
            stream = await client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=openai_tools,
                stream=True,
                **kwargs,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

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
        """转换消息为 OpenAI 格式"""
        result = []
        for msg in messages:
            d = {"role": msg.role.value, "content": msg.content}
            if msg.name:
                d["name"] = msg.name
            if msg.tool_call_id:
                d["tool_call_id"] = msg.tool_call_id
            result.append(d)
        return result

    def _parse_tool_calls(self, tool_calls) -> list[ToolCall]:
        """解析工具调用"""
        if not tool_calls:
            return []

        result = []
        for tc in tool_calls:
            import json

            result.append(
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                )
            )
        return result

    def _convert_error(self, error: Exception) -> LLMError:
        """转换错误类型"""
        try:
            from openai import (
                APITimeoutError as OpenAITimeout,
            )
            from openai import (
                AuthenticationError as OpenAIAuth,
            )
            from openai import (
                RateLimitError as OpenAIRateLimit,
            )

            if isinstance(error, OpenAIRateLimit):
                return RateLimitError(
                    str(error),
                    code=getattr(error, "code", None),
                    raw_error=error,
                )
            elif isinstance(error, OpenAIAuth):
                return AuthenticationError(
                    str(error),
                    code=getattr(error, "code", None),
                    raw_error=error,
                )
            elif isinstance(error, OpenAITimeout):
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
        return "OpenAI"
