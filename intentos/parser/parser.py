"""
意图解析器
将自然语言解析为结构化意图
"""

from __future__ import annotations
import re
from typing import Optional, TYPE_CHECKING
from ..core import Intent, IntentType, Context, IntentStep

if TYPE_CHECKING:
    from ..registry.registry import IntentRegistry


class IntentParser:
    """
    意图解析器
    负责将自然语言转换为结构化意图
    """
    
    def __init__(self, registry: "IntentRegistry" | None = None):
        self.registry = registry
        self._patterns: list[tuple[re.Pattern, str]] = []
    
    def register_pattern(self, pattern: str, intent_name: str) -> None:
        """注册意图匹配模式"""
        self._patterns.append((re.compile(pattern, re.IGNORECASE), intent_name))
    
    def parse(self, text: str, context: Optional[Context] = None) -> Intent:
        """
        解析自然语言为意图
        
        Args:
            text: 用户输入的自然语言
            context: 执行上下文
        
        Returns:
            结构化意图对象
        """
        context = context or Context(user_id="anonymous")
        
        # 1. 尝试匹配已注册的意图模板
        matched_intent = self._match_registered(text, context)
        if matched_intent:
            return matched_intent
        
        # 2. 解析为通用意图
        return self._parse_generic(text, context)
    
    def _match_registered(self, text: str, context: Context) -> Optional[Intent]:
        """匹配已注册的意图模板"""
        if not self.registry:
            return None
        
        for pattern, intent_name in self._patterns:
            if pattern.search(text):
                template = self.registry.get_template(intent_name)
                if template:
                    # 提取参数
                    params = self._extract_params(text, template)
                    return template.instantiate(context, **params)
        
        return None
    
    def _extract_params(self, text: str, template: IntentTemplate) -> dict:
        """从文本中提取参数"""
        params = {}
        
        # 简单的参数提取逻辑（可扩展为更复杂的 NLP）
        # 提取引号内的字符串
        quoted_strings = re.findall(r'"([^"]+)"|\'([^\']+)\'', text)
        if quoted_strings and "query" in template.params_schema:
            params["query"] = quoted_strings[0][0] or quoted_strings[0][1]
        
        # 提取数字
        numbers = re.findall(r'\d+', text)
        if numbers:
            if "limit" in template.params_schema:
                params["limit"] = int(numbers[0])
        
        return params
    
    def _parse_generic(self, text: str, context: Context) -> Intent:
        """解析为通用意图"""
        # 意图分类
        intent_type = self._classify_intent(text)
        
        # 提取目标
        goal = self._extract_goal(text)
        
        # 创建意图
        intent = Intent(
            name="generic_intent",
            intent_type=intent_type,
            description=text,
            goal=goal,
            context=context,
            params={"raw_input": text},
        )
        
        return intent
    
    def _classify_intent(self, text: str) -> IntentType:
        """根据文本分类意图类型"""
        text_lower = text.lower()
        
        # 复合意图关键词
        composite_keywords = ["分析", "对比", "生成", "创建", "整理", "处理"]
        if any(kw in text_lower for kw in composite_keywords):
            return IntentType.COMPOSITE
        
        # 场景意图关键词
        scenario_keywords = ["周报", "月报", "复盘", "总结", "报告"]
        if any(kw in text_lower for kw in scenario_keywords):
            return IntentType.SCENARIO
        
        # 默认为原子意图
        return IntentType.ATOMIC
    
    def _extract_goal(self, text: str) -> str:
        """提取用户目标"""
        # 简化实现：直接返回原文
        # 可扩展为更复杂的目标提取逻辑
        return text.strip()
