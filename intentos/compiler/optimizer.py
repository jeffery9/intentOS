"""
IntentOS 编译器 LLM 优化器

核心洞察:
- 不同 LLM 有不同的能力和限制
- 根据 LLM 能力调整编译策略
- 优化 token 使用，降低成本

优化策略:
1. LLM 能力画像
2. Prompt 优化
3. 编译策略选择
4. Token 优化
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

if TYPE_CHECKING:
    from intentos.compiler.compiler import CompiledPrompt


# =============================================================================
# LLM 能力画像
# =============================================================================

class LLMProvider(Enum):
    """LLM 提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    MOCK = "mock"


@dataclass
class LLMProfile:
    """
    LLM 能力画像
    
    用于根据 LLM 能力优化编译策略
    """
    provider: LLMProvider
    model: str
    
    # 能力限制
    max_context_size: int  # 最大上下文 (tokens)
    max_output_tokens: int  # 最大输出 tokens
    
    # 能力特性
    supports_tools: bool = True  # 是否支持工具调用
    supports_json_mode: bool = True  # 是否支持 JSON 模式
    supports_vision: bool = False  # 是否支持视觉
    
    # 成本 (每 1K tokens)
    input_cost_usd: float = 0.0
    output_cost_usd: float = 0.0
    
    # 偏好格式
    preferred_format: str = "json"  # json/yaml/text
    
    def is_suitable_for(self, intent_complexity: str) -> bool:
        """判断是否适合处理特定复杂度的意图"""
        if intent_complexity == "simple":
            return True
        elif intent_complexity == "medium":
            return self.max_context_size >= 8000
        elif intent_complexity == "complex":
            return self.max_context_size >= 16000 and self.supports_tools
        return False
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """估算成本"""
        input_cost = (input_tokens / 1000) * self.input_cost_usd
        output_cost = (output_tokens / 1000) * self.output_cost_usd
        return input_cost + output_cost


# 预定义的 LLM 画像
LLM_PROFILES = {
    "gpt-4o": LLMProfile(
        provider=LLMProvider.OPENAI,
        model="gpt-4o",
        max_context_size=128000,
        max_output_tokens=4096,
        supports_tools=True,
        supports_json_mode=True,
        input_cost_usd=0.005,
        output_cost_usd=0.015,
    ),
    "gpt-4": LLMProfile(
        provider=LLMProvider.OPENAI,
        model="gpt-4",
        max_context_size=8192,
        max_output_tokens=4096,
        supports_tools=True,
        supports_json_mode=True,
        input_cost_usd=0.03,
        output_cost_usd=0.06,
    ),
    "gpt-3.5-turbo": LLMProfile(
        provider=LLMProvider.OPENAI,
        model="gpt-3.5-turbo",
        max_context_size=16385,
        max_output_tokens=4096,
        supports_tools=True,
        supports_json_mode=True,
        input_cost_usd=0.0005,
        output_cost_usd=0.0015,
    ),
    "claude-3-5-sonnet": LLMProfile(
        provider=LLMProvider.ANTHROPIC,
        model="claude-3-5-sonnet",
        max_context_size=200000,
        max_output_tokens=4096,
        supports_tools=True,
        supports_json_mode=False,
        input_cost_usd=0.003,
        output_cost_usd=0.015,
    ),
    "claude-3-haiku": LLMProfile(
        provider=LLMProvider.ANTHROPIC,
        model="claude-3-haiku",
        max_context_size=200000,
        max_output_tokens=4096,
        supports_tools=True,
        supports_json_mode=False,
        input_cost_usd=0.00025,
        output_cost_usd=0.00125,
    ),
    "llama3.1": LLMProfile(
        provider=LLMProvider.OLLAMA,
        model="llama3.1",
        max_context_size=8192,
        max_output_tokens=2048,
        supports_tools=False,
        supports_json_mode=False,
        input_cost_usd=0.0,  # 本地运行
        output_cost_usd=0.0,
    ),
}


# =============================================================================
# Prompt 优化器
# =============================================================================

class PromptOptimizer:
    """
    Prompt 优化器
    
    根据 LLM 能力优化编译结果
    """
    
    def __init__(self, llm_profile: LLMProfile):
        self.profile = llm_profile
    
    def optimize(
        self,
        compiled_prompt: CompiledPrompt,
        target_tokens: Optional[int] = None,
    ) -> CompiledPrompt:
        """
        优化编译后的 Prompt
        
        Args:
            compiled_prompt: 编译后的 Prompt
            target_tokens: 目标 token 数 (可选)
        
        Returns:
            优化后的 Prompt
        """
        # 1. 根据 LLM 格式偏好调整
        if self.profile.preferred_format == "text":
            compiled_prompt = self._convert_to_text(compiled_prompt)
        elif self.profile.preferred_format == "yaml":
            compiled_prompt = self._convert_to_yaml(compiled_prompt)
        
        # 2. 如果超过上下文限制，进行裁剪
        if target_tokens or self._estimate_tokens(compiled_prompt) > self.profile.max_context_size * 0.9:
            compiled_prompt = self._trim_prompt(compiled_prompt, target_tokens)
        
        # 3. 优化 JSON 模式
        if self.profile.supports_json_mode:
            compiled_prompt = self._enable_json_mode(compiled_prompt)
        
        return compiled_prompt
    
    def _estimate_tokens(self, compiled_prompt: CompiledPrompt) -> int:
        """估算 token 数"""
        # 简单估算：4 字符 ≈ 1 token
        text = compiled_prompt.system_prompt + compiled_prompt.user_prompt
        return len(text) // 4
    
    def _convert_to_text(self, compiled_prompt: CompiledPrompt) -> CompiledPrompt:
        """转换为文本格式"""
        # 移除 JSON 特定格式
        system_prompt = compiled_prompt.system_prompt
        system_prompt = system_prompt.replace("```json", "").replace("```", "")
        
        from intentos.compiler.compiler import CompiledPrompt
        return CompiledPrompt(
            system_prompt=system_prompt,
            user_prompt=compiled_prompt.user_prompt,
            intent=compiled_prompt.intent,
            metadata=compiled_prompt.metadata,
        )
    
    def _convert_to_yaml(self, compiled_prompt: CompiledPrompt) -> CompiledPrompt:
        """转换为 YAML 格式"""
        try:
            import yaml
            intent_dict = compiled_prompt.intent.to_dict()
            yaml_str = yaml.dump(intent_dict, default_flow_style=False, allow_unicode=True)
            
            from intentos.compiler.compiler import CompiledPrompt
            return CompiledPrompt(
                system_prompt=f"请按照以下 YAML 格式的意图执行:\n\n{yaml_str}",
                user_prompt=compiled_prompt.user_prompt,
                intent=compiled_prompt.intent,
                metadata=compiled_prompt.metadata,
            )
        except ImportError:
            return compiled_prompt
    
    def _trim_prompt(
        self,
        compiled_prompt: CompiledPrompt,
        target_tokens: Optional[int],
    ) -> CompiledPrompt:
        """裁剪 Prompt"""
        # 优先保留系统 Prompt 的关键部分
        system_prompt = compiled_prompt.system_prompt
        
        # 如果太长，删除示例和详细说明
        if len(system_prompt) > 2000:
            # 保留前 2000 字符
            system_prompt = system_prompt[:2000] + "\n..."
        
        from intentos.compiler.compiler import CompiledPrompt
        return CompiledPrompt(
            system_prompt=system_prompt,
            user_prompt=compiled_prompt.user_prompt,
            intent=compiled_prompt.intent,
            metadata=compiled_prompt.metadata,
        )
    
    def _enable_json_mode(self, compiled_prompt: CompiledPrompt) -> CompiledPrompt:
        """启用 JSON 模式"""
        # 添加 JSON 模式指令
        system_prompt = compiled_prompt.system_prompt
        system_prompt += "\n\n请以 JSON 格式返回结果。"
        
        from intentos.compiler.compiler import CompiledPrompt
        return CompiledPrompt(
            system_prompt=system_prompt,
            user_prompt=compiled_prompt.user_prompt,
            intent=compiled_prompt.intent,
            metadata=compiled_prompt.metadata,
        )


# =============================================================================
# 编译策略选择器
# =============================================================================

class CompilationStrategy(Enum):
    """编译策略"""
    FAST = "fast"  # 快速编译 (使用模板)
    STANDARD = "standard"  # 标准编译
    OPTIMIZED = "optimized"  # 优化编译 (使用 LLM)


class StrategySelector:
    """
    编译策略选择器
    
    根据意图复杂度和 LLM 能力选择最佳编译策略
    """
    
    def __init__(self, llm_profile: LLMProfile):
        self.profile = llm_profile
    
    def select_strategy(self, intent_complexity: str) -> CompilationStrategy:
        """
        选择编译策略
        
        Args:
            intent_complexity: 意图复杂度 (simple/medium/complex)
        
        Returns:
            编译策略
        """
        if intent_complexity == "simple":
            return CompilationStrategy.FAST
        elif intent_complexity == "medium":
            return CompilationStrategy.STANDARD
        elif intent_complexity == "complex":
            return CompilationStrategy.OPTIMIZED
        else:
            return CompilationStrategy.STANDARD
    
    def estimate_compilation_time(self, strategy: CompilationStrategy) -> float:
        """估算编译时间 (秒)"""
        if strategy == CompilationStrategy.FAST:
            return 0.01  # 10ms
        elif strategy == CompilationStrategy.STANDARD:
            return 0.1  # 100ms
        elif strategy == CompilationStrategy.OPTIMIZED:
            return 1.0  # 1s (需要 LLM 调用)
        return 0.1


# =============================================================================
# Token 优化器
# =============================================================================

class TokenOptimizer:
    """
    Token 优化器
    
    减少 token 使用，降低成本
    """
    
    @staticmethod
    def compress_prompt(text: str, compression_level: int = 1) -> str:
        """
        压缩 Prompt
        
        Args:
            text: 原始文本
            compression_level: 压缩级别 (1-3)
        
        Returns:
            压缩后的文本
        """
        if compression_level == 1:
            # 级别 1: 移除空白和冗余
            import re
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n{2,}', '\n', text)
        
        elif compression_level == 2:
            # 级别 2: 使用缩写
            abbreviations = {
                "please": "plz",
                "thank you": "thx",
                "information": "info",
                "configuration": "config",
            }
            for full, abbr in abbreviations.items():
                text = text.replace(full, abbr)
        
        elif compression_level == 3:
            # 级别 3: 极端压缩 (仅保留关键信息)
            # 实际实现应该使用 LLM 进行摘要
            if len(text) > 500:
                text = text[:500] + "..."
        
        return text
    
    @staticmethod
    def batch_intents(intents: list[Any], max_batch_size: int = 10) -> list[list[Any]]:
        """
        批量意图分组
        
        将多个意图分组，减少 LLM 调用次数
        """
        batches = []
        for i in range(0, len(intents), max_batch_size):
            batch = intents[i:i + max_batch_size]
            batches.append(batch)
        return batches


# =============================================================================
# 上下文管理器
# =============================================================================

class ContextManager:
    """
    上下文管理器
    
    智能管理上下文大小，适配 LLM 限制
    """
    
    def __init__(self, max_context_size: int = 8000):
        self.max_context_size = max_context_size  # tokens
        self._context_entries = []
    
    def add_entry(
        self,
        key: str,
        value: Any,
        importance: float = 1.0,
        ttl_seconds: int = 3600,
    ) -> None:
        """
        添加上下文条目
        
        Args:
            key: 键
            value: 值
            importance: 重要性 (0-1)
            ttl_seconds: 生存时间
        """
        from datetime import datetime, timedelta
        entry = {
            "key": key,
            "value": value,
            "importance": importance,
            "expires_at": datetime.now() + timedelta(seconds=ttl_seconds),
        }
        self._context_entries.append(entry)
    
    def get_context(self) -> str:
        """获取优化后的上下文"""
        from datetime import datetime
        
        # 1. 过滤过期条目
        now = datetime.now()
        valid_entries = [
            e for e in self._context_entries
            if e["expires_at"] > now
        ]
        
        # 2. 按重要性排序
        valid_entries.sort(key=lambda e: e["importance"], reverse=True)
        
        # 3. 裁剪到最大上下文
        context_text = ""
        for entry in valid_entries:
            entry_text = f"{entry['key']}: {entry['value']}\n"
            if len(context_text) + len(entry_text) > self.max_context_size * 4:
                break
            context_text += entry_text
        
        return context_text
    
    def clear(self) -> None:
        """清空上下文"""
        self._context_entries.clear()


# =============================================================================
# 便捷函数
# =============================================================================

def get_llm_profile(model: str) -> LLMProfile:
    """获取 LLM 画像"""
    return LLM_PROFILES.get(model, LLMProfile(
        provider=LLMProvider.MOCK,
        model=model,
        max_context_size=4096,
        max_output_tokens=1024,
    ))


def create_prompt_optimizer(model: str) -> PromptOptimizer:
    """创建 Prompt 优化器"""
    profile = get_llm_profile(model)
    return PromptOptimizer(profile)


def create_strategy_selector(model: str) -> StrategySelector:
    """创建策略选择器"""
    profile = get_llm_profile(model)
    return StrategySelector(profile)
