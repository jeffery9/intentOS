"""
Ollama 后端集成

支持本地运行开源模型:
- Llama 3.1
- Mistral
- Qwen2.5
- Gemma 2
- 以及其他 Ollama 支持的模型
"""

from __future__ import annotations
import time
import json
from typing import Optional, AsyncIterator

from .base import (
    LLMBackend,
    LLMResponse,
    LLMUsage,
    LLMError,
    Message,
    ToolDefinition,
    ToolCall,
    LLMRole,
)


class OllamaBackend(LLMBackend):
    """Ollama LLM 后端"""
    
    def __init__(
        self,
        model: str = "llama3.1",
        host: str = "http://localhost:11434",
        timeout: int = 120,  # Ollama 本地运行可能需要更长时间
        max_retries: int = 3,
        **kwargs,
    ):
        super().__init__(
            model=model,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )
        self.host = host
        self._client = None
    
    def _get_client(self):
        """获取客户端"""
        if self._client is None:
            try:
                import ollama
            except ImportError:
                raise ImportError("请安装 ollama: pip install ollama")
            
            self._client = ollama.AsyncClient(host=self.host, timeout=self.timeout)
        return self._client
    
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
        
        client = self._get_client()
        
        # 转换消息格式
        ollama_messages = self._convert_messages(messages)
        
        # 转换工具格式
        ollama_tools = self._convert_tools(tools) if tools else None
        
        try:
            response = await client.chat(
                model=self.model,
                messages=ollama_messages,
                tools=ollama_tools,
                stream=stream,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # 解析响应
            message = response["message"]
            content = message.get("content", "")
            tool_calls = self._parse_tool_calls(message.get("tool_calls", []))
            
            # 估算 token 使用
            usage = self._estimate_usage(messages, content)
            
            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
                tool_calls=tool_calls,
                finish_reason="stop",
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
        client = self._get_client()
        ollama_messages = self._convert_messages(messages)
        ollama_tools = self._convert_tools(tools) if tools else None
        
        try:
            stream = await client.chat(
                model=self.model,
                messages=ollama_messages,
                tools=ollama_tools,
                stream=True,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )
            
            async for chunk in stream:
                if chunk["message"].get("content"):
                    yield chunk["message"]["content"]
                    
        except Exception as e:
            raise self._convert_error(e)
    
    def validate_connection(self) -> bool:
        """验证连接"""
        import httpx
        
        try:
            response = httpx.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """转换消息为 Ollama 格式"""
        result = []
        for msg in messages:
            result.append({
                "role": msg.role.value,
                "content": msg.content,
            })
        return result
    
    def _convert_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        """转换工具为 Ollama 格式"""
        result = []
        for tool in tools:
            result.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            })
        return result
    
    def _parse_tool_calls(self, tool_calls: list) -> list[ToolCall]:
        """解析工具调用"""
        if not tool_calls:
            return []
        
        result = []
        for tc in tool_calls:
            result.append(ToolCall(
                id=tc.get("function", {}).get("name", ""),
                name=tc.get("function", {}).get("name", ""),
                arguments=tc.get("function", {}).get("arguments", {}),
            ))
        return result
    
    def _estimate_usage(self, messages: list[Message], content: str) -> LLMUsage:
        """估算 token 使用"""
        prompt_tokens = sum(self._estimate_tokens(msg.content) for msg in messages)
        completion_tokens = self._estimate_tokens(content)
        
        return LLMUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )
    
    def _convert_error(self, error: Exception) -> LLMError:
        """转换错误类型"""
        return LLMError(str(error), raw_error=error)
    
    @property
    def provider_name(self) -> str:
        return "Ollama"
