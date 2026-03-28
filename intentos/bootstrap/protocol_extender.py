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
        use_llm: bool = True,
    ) -> Optional[CapabilityGap]:
        """
        检测能力缺口
        
        Args:
            intent_text: 用户意图文本
            available_capabilities: 当前可用能力列表
            execution_context: 执行上下文
            use_llm: 是否使用 LLM 语义分析（默认 True）

        Returns:
            检测到的能力缺口，如果没有则返回 None
        """
        import asyncio
        
        # 1. 分析意图，识别需要的能力（使用 LLM 或关键词）
        if use_llm:
            # LLM 需要异步调用
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            required_capabilities = loop.run_until_complete(
                self._extract_required_capabilities(intent_text, use_llm=True)
            )
        else:
            required_capabilities = self._keyword_extract_capabilities(intent_text)
        
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
            detected_at=datetime.now(),
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
    
    async def _extract_required_capabilities(self, intent_text: str, use_llm: bool = True) -> list[str]:
        """
        从意图文本中提取需要的能力
        
        Args:
            intent_text: 意图文本
            use_llm: 是否使用 LLM 语义分析（默认 True）
            
        Returns:
            需要的能力列表
        """
        if use_llm:
            try:
                return await self._llm_extract_capabilities(intent_text)
            except Exception as e:
                # LLM 失败时降级到关键词匹配
                logging.warning(f"LLM 提取失败，降级到关键词匹配：{e}")
        
        # 降级：关键词匹配
        return self._keyword_extract_capabilities(intent_text)
    
    async def _llm_extract_capabilities(self, intent_text: str) -> list[str]:
        """
        使用 LLM 进行语义分析提取能力
        
        优势:
        - 理解语义，不只是关键词
        - 支持同义词和隐含意图
        - 更准确的意图识别
        """
        # 构建 Prompt
        prompt = f"""
你是一个能力识别专家。请分析用户意图，识别需要的系统能力。

用户意图：{intent_text}

可用能力类型:
- renderer: 渲染类 (AR, VR, 3D, chart, graph, plot, visualize 等)
- connector: 连接类 (database, api, http, network 等)
- handler: 处理类 (file, save, load, fetch, data 等)
- analyzer: 分析类 (analyze, process, compute, calculate 等)

请识别需要的能力，返回 JSON 格式:
{{
    "capabilities": ["capability_name1", "capability_name2"],
    "confidence": 0.95,
    "reasoning": "识别理由"
}}

只返回 JSON，不要其他内容。
"""
        
        # 调用 LLM (使用 IntentOS 的 LLM 后端)
        try:
            from intentos.llm import create_executor
            
            llm = create_executor(provider="mock")  # 实际使用配置中的 provider
            response = await llm.execute(prompt)
            
            # 解析响应
            import json
            result = json.loads(response.strip())
            
            capabilities = result.get("capabilities", [])
            confidence = result.get("confidence", 0.0)
            
            # 只返回高置信度的能力
            if confidence >= 0.7:
                logging.info(f"LLM 识别能力：{capabilities} (confidence: {confidence})")
                return capabilities
            else:
                logging.warning(f"LLM 置信度过低：{confidence}")
                return []
                
        except Exception as e:
            logging.error(f"LLM 能力提取失败：{e}")
            raise
    
    def _keyword_extract_capabilities(self, intent_text: str) -> list[str]:
        """
        关键词匹配（降级方案）
        """
        capability_keywords = {
            # 渲染类
            "ar": "ar_renderer",
            "vr": "vr_renderer",
            "3d": "3d_renderer",
            "chart": "chart_renderer",
            "graph": "chart_renderer",
            "plot": "chart_renderer",
            "visualize": "chart_renderer",
            "可视化": "chart_renderer",
            "渲染": "chart_renderer",
            
            # 连接类
            "database": "database_connector",
            "db": "database_connector",
            "api": "api_client",
            "http": "http_client",
            "network": "network_client",
            "数据库": "database_connector",
            
            # 处理类
            "file": "file_handler",
            "save": "file_handler",
            "load": "data_loader",
            "fetch": "data_loader",
            "下载": "data_loader",
            "保存": "file_handler",
            
            # 分析类
            "analyze": "data_analyzer",
            "process": "data_processor",
            "compute": "data_processor",
            "calculate": "data_processor",
            "分析": "data_analyzer",
            "计算": "data_processor",
        }

        required = []
        intent_lower = intent_text.lower()

        for keyword, capability in capability_keywords.items():
            if keyword in intent_lower:
                if capability not in required:  # 避免重复
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
