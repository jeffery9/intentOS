"""
Agent 执行器

使用 LLM 进行智能能力匹配
"""

from __future__ import annotations

from typing import Any, Optional
from .core import AgentResult
from .compiler import PEF
from .registry import CapabilityRegistry


class AgentExecutor:
    """Agent 执行器"""
    
    def __init__(self, registry: CapabilityRegistry, llm_processor: Optional[Any] = None):
        self.registry = registry
        self.llm_processor = llm_processor
    
    async def execute(self, pef: PEF, context: dict[str, Any]) -> AgentResult:
        """执行 PEF"""
        intent_lower = pef.intent.lower()
        
        # 使用 LLM 进行智能匹配
        matched = await self._llm_match_capability(intent_lower)
        
        if matched:
            params = self._extract_params(matched, pef.intent)
            try:
                result = await self.registry.execute_capability(matched.id, **params)
                return AgentResult(success=True, message="✓ 执行成功", data=result)
            except Exception as e:
                return AgentResult(success=False, message=f"执行失败：{e}", error=str(e))
        
        # 降级到关键词匹配
        matched = self._keyword_match_capability(intent_lower)
        if matched:
            params = self._extract_params(matched, pef.intent)
            try:
                result = await self.registry.execute_capability(matched.id, **params)
                return AgentResult(success=True, message="✓ 执行成功", data=result)
            except Exception as e:
                return AgentResult(success=False, message=f"执行失败：{e}", error=str(e))
        
        return AgentResult(success=True, message=f"✓ 已理解：{pef.intent}", data={"intent": pef.intent})
    
    async def _llm_match_capability(self, intent: str) -> Optional[Any]:
        """使用 LLM 进行语义匹配"""
        if not self.llm_processor:
            return None
        
        capabilities = self.registry.list_capabilities()
        cap_list = "\n".join([
            f"- {cap.id}: {cap.name} ({cap.description}) tags={cap.tags}"
            for cap in capabilities
        ])
        
        prompt = f"""分析用户意图，匹配最合适的能力。

可用能力:
{cap_list}

用户意图：{intent}

请返回最匹配的能力 ID，如果没有匹配的返回 null。
只返回能力 ID，不要其他内容。"""
        
        try:
            # 调用 LLM
            result = await self.llm_processor.generate(prompt)
            matched_id = result.strip() if result else None
            
            if matched_id and matched_id != "null":
                return self.registry.get_capability(matched_id)
        except Exception:
            pass
        
        return None
    
    def _keyword_match_capability(self, intent: str) -> Optional[Any]:
        """关键词匹配（降级方案）"""
        for cap in self.registry.list_capabilities():
            # 检查能力 tags
            for tag in cap.tags:
                if tag in intent or cap.name.lower() in intent:
                    return cap
            # 检查能力描述
            if cap.description and any(kw in intent for kw in cap.description.split()):
                return cap
        return None
    
    def _extract_params(self, cap: Any, intent: str) -> dict:
        """提取参数"""
        import re
        params = {}
        
        if cap.id == "shell":
            for pattern in [r'["\']([^"\']+)["\']', r'执行 (.+)', r'运行 (.+)']:
                match = re.search(pattern, intent)
                if match:
                    params["command"] = match.group(1).strip()
                    break
            if "command" not in params:
                params["command"] = intent.replace("执行", "").replace("运行", "").strip()
        elif cap.id == "calculator":
            match = re.search(r'([\d+\-*/().\s]+)', intent)
            if match:
                params["expression"] = match.group(1).strip()
        
        return params
