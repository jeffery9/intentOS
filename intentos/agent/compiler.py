"""
意图编译器

将自然语言意图编译为 PEF (Prompt Executable File)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class PEF:
    """Prompt Executable File"""
    version: str = "1.0"
    id: str = field(default_factory=lambda: f"pef_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    intent: str = ""
    system_prompt: str = ""
    user_prompt: str = ""
    capabilities: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "version": self.version,
            "id": self.id,
            "intent": self.intent,
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "capabilities": self.capabilities,
            "constraints": self.constraints,
            "metadata": self.metadata,
        }


class IntentCompiler:
    """意图编译器"""
    
    def __init__(self) -> None:
        self._prompt_templates: dict[str, str] = {}
        self._register_default_templates()
    
    def _register_default_templates(self) -> None:
        """注册默认 Prompt 模板"""
        self._prompt_templates["default"] = """你是一个 AI 智能助理。可用能力：{capabilities}。用户意图：{intent}。"""
    
    def compile(
        self,
        intent: str,
        capabilities: list[str],
        context: Optional[dict[str, Any]] = None
    ) -> PEF:
        """编译意图为 PEF"""
        template: str = self._prompt_templates.get("default", "")
        system_prompt: str = template.format(capabilities=", ".join(capabilities), intent=intent)
        
        return PEF(
            intent=intent,
            system_prompt=system_prompt,
            user_prompt=f"请执行：{intent}",
            capabilities=capabilities,
            metadata=context or {},
        )
