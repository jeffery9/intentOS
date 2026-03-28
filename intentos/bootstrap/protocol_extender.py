"""
协议自扩展器 (Protocol Self-Extender)

实现系统的"超界生长"能力：
当用户意图超出当前能力边界时，自动识别缺口并生成元意图来扩展系统能力
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .meta_intent_executor import MetaIntent, MetaIntentType


@dataclass
class CapabilityGap:
    """
    能力缺口
    
    系统检测到的能力缺失
    """
    capability_name: str
    description: str
    required_by: str  # 哪个意图需要
    detected_at: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    suggested_interface: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_name": self.capability_name,
            "description": self.description,
            "required_by": self.required_by,
            "detected_at": self.detected_at.isoformat(),
            "confidence": self.confidence,
            "suggested_interface": self.suggested_interface,
        }


@dataclass
class ExtensionSuggestion:
    """
    扩展建议
    
    系统生成的能力扩展建议
    """
    gap: CapabilityGap
    suggestion_type: str  # register_capability / modify_protocol / etc.
    params: dict[str, Any]
    reason: str
    risk_level: str = "low"  # low / medium / high
    
    def to_meta_intent(self) -> MetaIntent:
        """转换为元意图"""
        return MetaIntent(
            type=MetaIntentType(self.suggestion_type),
            target=self.gap.capability_name,
            params=self.params,
            description=f"Auto-generated: {self.reason}",
            confidence=self.gap.confidence,
        )


class ProtocolSelfExtender:
    """
    协议自扩展器
    
    检测能力缺口并生成扩展建议
    """
    
    def __init__(self):
        self.detected_gaps: dict[str, CapabilityGap] = {}
        self.extension_history: list[ExtensionSuggestion] = []
    
    def detect_capability_gap(
        self,
        intent_text: str,
        available_capabilities: list[str],
        execution_context: Optional[dict] = None,
    ) -> Optional[CapabilityGap]:
        """
        检测能力缺口
        
        Args:
            intent_text: 用户意图文本
            available_capabilities: 当前可用能力列表
            execution_context: 执行上下文
            
        Returns:
            检测到的能力缺口，如果没有则返回 None
        """
        # 1. 分析意图，识别需要的能力
        required_capabilities = self._extract_required_capabilities(intent_text)
        
        # 2. 检查是否有缺失的能力
        missing_caps = []
        for cap in required_capabilities:
            if cap not in available_capabilities:
                missing_caps.append(cap)
        
        if not missing_caps:
            return None
        
        # 3. 创建能力缺口
        gap = CapabilityGap(
            capability_name=missing_caps[0],
            description=f"Required by intent: {intent_text}",
            required_by=intent_text,
            confidence=0.9,
            suggested_interface=self._infer_interface(missing_caps[0], intent_text),
        )
        
        self.detected_gaps[gap.capability_name] = gap
        
        return gap
    
    def generate_extension_suggestion(
        self,
        gap: CapabilityGap,
    ) -> ExtensionSuggestion:
        """
        生成扩展建议
        
        Args:
            gap: 能力缺口
            
        Returns:
            扩展建议
        """
        # 分析能力名称，推断能力类型和接口
        cap_name = gap.capability_name
        
        # 推断能力类型
        if "render" in cap_name or "display" in cap_name:
            cap_type = "io"
            output_type = "string"  # URL or Base64
        elif "load" in cap_name or "fetch" in cap_name:
            cap_type = "io"
            output_type = "array"
        elif "analyze" in cap_name or "process" in cap_name:
            cap_type = "io"
            output_type = "object"
        else:
            cap_type = "io"
            output_type = "any"
        
        # 创建建议
        suggestion = ExtensionSuggestion(
            gap=gap,
            suggestion_type="register_capability",
            params={
                "name": cap_name,
                "description": gap.description,
                "type": cap_type,
                "interface": gap.suggested_interface,
            },
            reason=f"Capability '{cap_name}' is required but not registered",
            risk_level="low",
        )
        
        self.extension_history.append(suggestion)
        
        return suggestion
    
    def _extract_required_capabilities(self, intent_text: str) -> list[str]:
        """
        从意图文本中提取需要的能力
        
        在实际系统中，这里会使用 LLM 进行语义分析
        """
        # 简化的关键词匹配（实际应该用 LLM）
        capability_keywords = {
            "ar": "ar_renderer",
            "vr": "vr_renderer",
            "3d": "3d_renderer",
            "chart": "chart_renderer",
            "graph": "chart_renderer",
            "plot": "chart_renderer",
            "database": "database_connector",
            "api": "api_client",
            "http": "http_client",
            "file": "file_handler",
            "save": "file_handler",
            "load": "data_loader",
            "fetch": "data_loader",
        }
        
        required = []
        intent_lower = intent_text.lower()
        
        for keyword, capability in capability_keywords.items():
            if keyword in intent_lower:
                required.append(capability)
        
        return required
    
    def _infer_interface(
        self,
        capability_name: str,
        intent_text: str,
    ) -> dict[str, Any]:
        """
        推断能力接口
        
        在实际系统中，这里会使用 LLM 生成接口定义
        """
        # 简化的推断逻辑
        if "renderer" in capability_name:
            return {
                "input": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "array"},
                        "style": {"type": "string"},
                    }
                },
                "output": {"type": "string"},  # URL or Base64
            }
        elif "loader" in capability_name:
            return {
                "input": {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string"},
                        "filters": {"type": "object"},
                    }
                },
                "output": {"type": "array"},
            }
        else:
            return {
                "input": {"type": "object"},
                "output": {"type": "any"},
            }
    
    def get_detected_gaps(self) -> list[CapabilityGap]:
        """获取所有检测到的能力缺口"""
        return list(self.detected_gaps.values())
    
    def get_extension_history(self) -> list[ExtensionSuggestion]:
        """获取扩展历史"""
        return self.extension_history
    
    def clear_gaps(self) -> None:
        """清除已检测的缺口"""
        self.detected_gaps.clear()


# =============================================================================
# 使用示例
# =============================================================================


async def demo_protocol_extension():
    """演示协议自扩展"""
    from .meta_intent_executor import MetaIntentExecutor, BootstrapPolicy
    from ..apps import IntentPackageRegistry
    
    # 1. 初始化组件
    registry = IntentPackageRegistry()
    executor = MetaIntentExecutor(registry=registry)
    extender = ProtocolSelfExtender()
    
    # 2. 用户意图
    intent_text = "用 AR 展示华东区销售数据"
    available_capabilities = ["data_loader", "chart_renderer"]
    
    # 3. 检测能力缺口
    gap = extender.detect_capability_gap(
        intent_text=intent_text,
        available_capabilities=available_capabilities,
    )
    
    if gap:
        print(f"检测到能力缺口：{gap.capability_name}")
        
        # 4. 生成扩展建议
        suggestion = extender.generate_extension_suggestion(gap)
        print(f"扩展建议：{suggestion.reason}")
        
        # 5. 转换为元意图
        meta_intent = suggestion.to_meta_intent()
        
        # 6. 执行元意图（在实际系统中需要人工审批）
        meta_intent.approved_by = "auto_approved"  # 演示用
        result = await executor.execute(meta_intent)
        
        if result.status == "completed":
            print(f"✅ 系统已自我扩展！新增能力：{gap.capability_name}")
        else:
            print(f"❌ 扩展失败：{result.error}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_protocol_extension())
