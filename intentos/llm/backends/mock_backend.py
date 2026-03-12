"""
Mock 后端

用于测试和演示，不需要真实的 LLM 服务
"""

from __future__ import annotations
import time
import json
from typing import Optional, AsyncIterator

from .base import (
    LLMBackend,
    LLMResponse,
    LLMUsage,
    Message,
    ToolDefinition,
    ToolCall,
    LLMRole,
)


class MockBackend(LLMBackend):
    """Mock LLM 后端"""
    
    def __init__(
        self,
        model: str = "mock-model",
        response_callback: Optional[callable] = None,
        **kwargs,
    ):
        super().__init__(model=model, **kwargs)
        self.response_callback = response_callback
        self._call_count = 0
    
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
        self._call_count += 1
        
        # 获取最后一条用户消息
        last_user_message = ""
        for msg in reversed(messages):
            if msg.role == LLMRole.USER:
                last_user_message = msg.content
                break
        
        # 使用回调或生成默认响应
        if self.response_callback:
            content = self.response_callback(messages, tools)
        else:
            content = self._generate_mock_response(last_user_message, tools)
        
        # 解析工具调用
        tool_calls = self._parse_tool_calls(content, tools)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        usage = self._estimate_usage(messages, content)
        
        return LLMResponse(
            content=content,
            model=self.model,
            usage=usage,
            tool_calls=tool_calls,
            finish_reason="stop",
            latency_ms=latency_ms,
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
        response = await self.generate(
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # 模拟流式输出
        for word in response.content.split():
            yield word + " "
    
    def validate_connection(self) -> bool:
        """验证连接"""
        return True
    
    def _generate_mock_response(self, user_message: str, tools: Optional[list[ToolDefinition]]) -> str:
        """生成模拟响应"""
        # 简单的关键词匹配
        message_lower = user_message.lower()
        
        if "销售" in user_message or "分析" in user_message:
            return json.dumps({
                "success": True,
                "data": {
                    "region": "华东",
                    "revenue": 1250000,
                    "growth": 0.15,
                },
                "message": "分析完成",
            }, ensure_ascii=False)
        
        elif "报告" in user_message or "report" in user_message:
            return "# 分析报告\n\n## 摘要\n\n分析已完成，结果良好。\n\n## 详情\n\n- 指标 A: +15%\n- 指标 B: +8%"
        
        elif tools:
            # 如果有工具定义，尝试调用第一个工具
            return f"我将调用工具：{tools[0].name}"
        
        else:
            return f"收到消息：{user_message[:50]}..."
    
    def _parse_tool_calls(self, content: str, tools: Optional[list[ToolDefinition]]) -> list[ToolCall]:
        """解析工具调用"""
        if not tools:
            return []
        
        # 检查内容中是否提到工具名称
        for tool in tools:
            if tool.name in content:
                return [ToolCall(
                    id=f"mock_call_{self._call_count}",
                    name=tool.name,
                    arguments={},
                )]
        
        return []
    
    def _estimate_usage(self, messages: list[Message], content: str) -> LLMUsage:
        """估算 token 使用"""
        prompt_tokens = sum(self._estimate_tokens(msg.content) for msg in messages)
        completion_tokens = self._estimate_tokens(content)
        
        return LLMUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )
    
    @property
    def call_count(self) -> int:
        """获取调用次数"""
        return self._call_count
    
    @property
    def provider_name(self) -> str:
        return "Mock"
