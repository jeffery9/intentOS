"""
能力注册中心

管理所有可用的能力 (Capabilities/Skills/MCP Tools)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional


@dataclass
class Capability:
    """能力定义"""

    id: str
    name: str
    description: str
    handler: Callable[..., Any]
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    required_permissions: list[str] = field(default_factory=list)  # 所需权限
    source: str = "builtin"  # builtin, mcp, skill
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 安全标注 (模式 3: 安全默认值)
    is_read_only: bool = False  # 是否只读
    is_concurrency_safe: bool = False  # 是否允许并发
    is_destructive: Callable[[dict], bool] = field(  # 是否破坏性操作
        default_factory=lambda: lambda input: False
    )
    
    # 三层过滤 (模式 3)
    load_condition: Optional[str] = None  # 加载期条件 (环境变量名)
    runtime_condition: Optional[Callable[[Any], bool]] = None  # 运行时条件

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "tags": self.tags,
            "metadata": self.metadata,
            "source": self.source,
            "created_at": self.created_at,
            "is_read_only": self.is_read_only,
            "is_concurrency_safe": self.is_concurrency_safe,
        }


class CapabilityRegistry:
    """
    能力注册中心

    管理所有可用的能力 (Capabilities/Skills/MCP Tools)
    
    增强特性:
    - 三层过滤 (加载期/运行时/执行期)
    - 安全默认值 (is_read_only/is_concurrency_safe/is_destructive)
    - Capability Gate 集成 (模式 7)
    """

    _instance: Optional["CapabilityRegistry"] = None
    _capabilities: dict[str, Capability] = {}

    def __new__(cls) -> "CapabilityRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._capabilities = {}
        
        # 导入 CapabilityGate (延迟导入避免循环依赖)
        from ..security.gate import CapabilityGate
        self.gate = CapabilityGate()

    def register(
        self,
        id: str,
        name: str,
        description: str,
        handler: Callable[..., Any],
        input_schema: Optional[dict[str, Any]] = None,
        output_schema: Optional[dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        required_permissions: Optional[list[str]] = None,
        source: str = "builtin",
        # 三层过滤 (模式 3)
        load_condition: Optional[str] = None,  # 环境变量名
        runtime_condition: Optional[Callable[[Any], bool]] = None,
        # 安全标注 (模式 3: 安全默认值)
        is_read_only: bool = False,
        is_concurrency_safe: bool = False,
        is_destructive: Optional[Callable[[dict], bool]] = None,
    ) -> Optional[Capability]:
        """
        注册能力 (带三层过滤和安全默认值)
        
        Args:
            id: 能力 ID
            name: 能力名称
            description: 能力描述
            handler: 处理函数
            input_schema: 输入 Schema
            output_schema: 输出 Schema
            tags: 标签
            metadata: 元数据
            required_permissions: 所需权限
            source: 来源 (builtin/mcp/skill)
            load_condition: 加载期条件 (环境变量名, 未设置或为 false 则不注册)
            runtime_condition: 运行时条件 (返回 False 则不执行)
            is_read_only: 是否只读
            is_concurrency_safe: 是否允许并发
            is_destructive: 是否破坏性操作
        
        Returns:
            注册的能力, 如果加载期条件不满足则返回 None
        """
        # ① 加载期过滤 (环境变量)
        if load_condition:
            import os
            if not os.getenv(load_condition):
                return None  # 条件不满足, 不注册
        
        # ② 构建能力对象 (带安全默认值)
        capability = Capability(
            id=id,
            name=name,
            description=description,
            handler=handler,
            input_schema=input_schema or {},
            output_schema=output_schema or {},
            tags=tags or [],
            metadata=metadata or {},
            required_permissions=required_permissions or [],
            source=source,
            # 安全标注
            is_read_only=is_read_only,
            is_concurrency_safe=is_concurrency_safe,
            is_destructive=is_destructive or (lambda input: False),
            # 三层过滤
            load_condition=load_condition,
            runtime_condition=runtime_condition,
        )

        self._capabilities[id] = capability
        return capability

    def unregister(self, capability_id: str) -> bool:
        """注销能力"""
        if capability_id in self._capabilities:
            del self._capabilities[capability_id]
            return True
        return False

    def get_capability(self, capability_id: str) -> Optional[Capability]:
        """获取能力"""
        return self._capabilities.get(capability_id)

    def list_capabilities(
        self, tags: Optional[list[str]] = None, source: Optional[str] = None
    ) -> list[Capability]:
        """列出能力"""
        capabilities: list[Capability] = list(self._capabilities.values())

        if tags:
            capabilities = [cap for cap in capabilities if any(tag in cap.tags for tag in tags)]

        if source:
            capabilities = [cap for cap in capabilities if cap.source == source]

        return capabilities

    async def execute_capability(
        self,
        capability_id: str,
        context: Optional[Any] = None,
        **kwargs: Any,
    ) -> Any:
        """
        执行能力 (带 Capability Gate 管线)
        
        管线流程:
        1. 全局 deny 规则
        2. Ask 规则
        3. 权限检查
        4. 安全标注
        5. 熔断器
        6. 内容级规则
        7. 安全检查
        """
        capability: Optional[Capability] = self.get_capability(capability_id)

        if not capability:
            raise ValueError(f"能力不存在：{capability_id}")
        
        # ① 运行时条件检查
        if capability.runtime_condition:
            if not capability.runtime_condition(context):
                raise PermissionError(
                    f"运行时条件不满足，能力 {capability_id} 未执行"
                )

        # ② Capability Gate 管线检查
        gate_result = await self.gate.evaluate(
            capability_id=capability_id,
            context=context or {},
            input_data=kwargs,
            capability=capability,
        )
        
        # ③ 根据决策执行
        from ..security.gate import GateDecision, CircuitBreakerError, PermissionDeniedError
        
        if gate_result.decision == GateDecision.DENY:
            if gate_result.circuit_broken:
                raise CircuitBreakerError(
                    f"能力 {capability_id} 熔断器触发: {gate_result.reason}"
                )
            raise PermissionDeniedError(
                f"能力 {capability_id} 被拒绝: {gate_result.reason}"
            )
        
        elif gate_result.decision == GateDecision.ASK:
            # TODO: 实现用户确认逻辑 (需要与接口层交互)
            if gate_result.requires_confirmation:
                # 暂时记录拒绝, 实际应由接口层询问用户
                self.gate.denial_tracker.record_denial(capability_id)
                raise PermissionError(
                    f"能力 {capability_id} 需要用户确认: {gate_result.reason}"
                )
        
        # ④ 执行能力
        import asyncio

        try:
            if asyncio.iscoroutinefunction(capability.handler):
                result = await capability.handler(**kwargs)
            else:
                result = capability.handler(**kwargs)
            
            # 记录允许
            self.gate.denial_tracker.record_allow(capability_id)
            return result
        except Exception as e:
            # 执行失败, 记录拒绝
            self.gate.denial_tracker.record_denial(capability_id)
            raise
