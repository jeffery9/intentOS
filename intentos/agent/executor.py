"""
Agent 执行器
"""

from __future__ import annotations

from typing import Any
from .core import AgentResult
from .compiler import PEF
from .registry import CapabilityRegistry


class AgentExecutor:
    """Agent 执行器"""
    
    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry
    
    async def execute(self, pef: PEF, context: dict[str, Any]) -> AgentResult:
        """执行 PEF"""
        intent_lower = pef.intent.lower()
        matched = self._match_capability(intent_lower)
        
        if matched:
            params = self._extract_params(matched, pef.intent)
            try:
                result = await self.registry.execute_capability(matched.id, **params)
                return AgentResult(success=True, message="✓ 执行成功", data=result)
            except Exception as e:
                return AgentResult(success=False, message=f"执行失败：{e}", error=str(e))
        
        return AgentResult(success=True, message=f"✓ 已理解：{pef.intent}", data={"intent": pef.intent})
    
    def _match_capability(self, intent: str) -> Any:
        """匹配能力"""
        for cap in self.registry.list_capabilities():
            for tag in cap.tags:
                if tag in intent or cap.name.lower() in intent:
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
        elif cap.id == "calculator":
            match = re.search(r'([\d+\-*/().\s]+)', intent)
            if match:
                params["expression"] = match.group(1).strip()
        
        return params
