"""
LLM 提供者服务

为 AI Agent 提供 LLM 调用能力
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Optional


class LLMProvider:
    """
    LLM 提供者
    
    支持多种 LLM 后端：
    - OpenAI (GPT-4)
    - Anthropic (Claude)
    - Ollama (本地模型)
    - Mock (测试)
    """
    
    _instance: Optional["LLMProvider"] = None
    
    def __new__(cls) -> "LLMProvider":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # 配置
        self.provider = os.getenv("LLM_PROVIDER", "mock")
        self.model = os.getenv("LLM_MODEL", "gpt-4")
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.base_url = os.getenv("LLM_BASE_URL", "")
        
        # 客户端缓存
        self._client = None
        
        self._initialized = True
    
    async def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """
        聊天完成
        
        Args:
            messages: 对话历史
            system_prompt: 系统提示
            temperature: 温度
            max_tokens: 最大 token 数
        
        Returns:
            LLM 响应文本
        """
        # 构建完整消息
        full_messages = []
        
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        
        full_messages.extend(messages)
        
        # 根据提供商调用
        if self.provider == "openai":
            return await self._call_openai(full_messages, temperature, max_tokens)
        elif self.provider == "anthropic":
            return await self._call_anthropic(full_messages, temperature, max_tokens)
        elif self.provider == "ollama":
            return await self._call_ollama(full_messages, temperature, max_tokens)
        else:
            return await self._call_mock(full_messages)
    
    async def _call_openai(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int
    ) -> str:
        """调用 OpenAI"""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url or None
            )
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            return "[OpenAI SDK 未安装，使用 Mock 模式]"
        except Exception as e:
            return f"[OpenAI 调用失败：{e}]"
    
    async def _call_anthropic(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int
    ) -> str:
        """调用 Anthropic"""
        try:
            from anthropic import AsyncAnthropic
            
            client = AsyncAnthropic(api_key=self.api_key)
            
            # 转换消息格式
            system_prompt = ""
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_prompt = msg["content"]
                else:
                    user_messages.append(msg)
            
            response = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=user_messages,
            )
            
            return response.content[0].text
            
        except ImportError:
            return "[Anthropic SDK 未安装，使用 Mock 模式]"
        except Exception as e:
            return f"[Anthropic 调用失败：{e}]"
    
    async def _call_ollama(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int
    ) -> str:
        """调用 Ollama"""
        try:
            import ollama
            
            response = await asyncio.to_thread(
                ollama.chat,
                model=self.model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            )
            
            return response["message"]["content"]
            
        except ImportError:
            return "[Ollama 未安装，使用 Mock 模式]"
        except Exception as e:
            return f"[Ollama 调用失败：{e}]"
    
    async def _call_mock(self, messages: list[dict]) -> str:
        """Mock 调用（用于测试）"""
        # 简单实现：返回输入的最后一条消息
        last_message = messages[-1]["content"] if messages else ""
        
        # 根据内容生成 Mock 响应
        if any(kw in last_message for kw in ["会议", "安排", "预约"]):
            return "✓ 会议已安排\n时间：2026-03-16 15:00\n地点：会议室 301"
        elif any(kw in last_message for kw in ["分析", "数据"]):
            return "✓ 分析完成\n总销售额：¥1,250,000\n同比增长：+15%"
        elif any(kw in last_message for kw in ["写", "文章", "内容"]):
            return "✓ 内容已生成\n字数：1,500 字\n阅读时间：5 分钟"
        elif any(kw in last_message for kw in ["代码", "编程"]):
            return "✓ 代码已生成\n```python\ndef hello():\n    print('Hello!')\n```"
        else:
            return f"✓ 已完成：{last_message[:50]}..."
    
    def get_config(self) -> dict[str, Any]:
        """获取配置"""
        return {
            "provider": self.provider,
            "model": self.model,
            "api_key_set": bool(self.api_key),
            "base_url": self.base_url,
        }


_llm_provider: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    """获取 LLM 提供者单例"""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = LLMProvider()
    return _llm_provider
