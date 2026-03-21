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
    required_permissions: list[str] = field(default_factory=list) # 所需权限
    source: str = "builtin"  # builtin, mcp, skill
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

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
        }


class CapabilityRegistry:
    """
    能力注册中心

    管理所有可用的能力 (Capabilities/Skills/MCP Tools)
    """

    _instance: Optional["CapabilityRegistry"] = None
    _capabilities: dict[str, Capability] = {}

    def __new__(cls) -> "CapabilityRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

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
    ) -> Capability:
        """注册能力"""
        capability: Capability = Capability(
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
        self,
        tags: Optional[list[str]] = None,
        source: Optional[str] = None
    ) -> list[Capability]:
        """列出能力"""
        capabilities: list[Capability] = list(self._capabilities.values())

        if tags:
            capabilities = [
                cap for cap in capabilities
                if any(tag in cap.tags for tag in tags)
            ]

        if source:
            capabilities = [
                cap for cap in capabilities
                if cap.source == source
            ]

        return capabilities

    async def execute_capability(
        self,
        capability_id: str,
        context: Optional[Any] = None, # 增加上下文注入
        **kwargs: Any
    ) -> Any:
        """执行能力 (带语义权限校验)"""
        capability: Optional[Capability] = self.get_capability(capability_id)

        if not capability:
            raise ValueError(f"能力不存在：{capability_id}")

        # 语义权限校验 (Capability Gate)
        if capability.required_permissions and context:
            # 假设 context 有 permissions 列表
            user_perms = getattr(context, 'permissions', [])
            if not isinstance(user_perms, list):
                # 兼容字典格式
                user_perms = context.get('permissions', []) if isinstance(context, dict) else []

            for perm in capability.required_permissions:
                if perm not in user_perms:
                    raise PermissionError(f"权限不足：需要 {perm} 权限以调用 {capability_id}")

        import asyncio
        if asyncio.iscoroutinefunction(capability.handler):
            return await capability.handler(**kwargs)
        else:
            return capability.handler(**kwargs)
