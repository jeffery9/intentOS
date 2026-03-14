"""
意图仓库
管理意图模板、能力和策略的注册中心
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from ..core import Capability, IntentTemplate


class IntentRegistry:
    """
    意图注册中心
    存储和管理可复用的意图模板和能力
    """

    def __init__(self):
        self._templates: dict[str, IntentTemplate] = {}
        self._capabilities: dict[str, Capability] = {}
        self._policies: dict[str, dict[str, Any]] = {}

    # ========== 模板管理 ==========

    def register_template(self, template: IntentTemplate) -> None:
        """注册意图模板"""
        self._templates[template.name] = template

    def get_template(self, name: str) -> Optional[IntentTemplate]:
        """获取意图模板"""
        return self._templates.get(name)

    def list_templates(self, tags: Optional[list[str]] = None) -> list[IntentTemplate]:
        """列出模板，可按标签过滤"""
        if not tags:
            return list(self._templates.values())

        return [t for t in self._templates.values() if any(tag in t.tags for tag in tags)]

    def remove_template(self, name: str) -> bool:
        """删除模板"""
        if name in self._templates:
            del self._templates[name]
            return True
        return False

    # ========== 能力管理 ==========

    def register_capability(self, capability: Capability) -> None:
        """注册能力"""
        self._capabilities[capability.name] = capability

    def get_capability(self, name: str) -> Optional[Capability]:
        """获取能力"""
        return self._capabilities.get(name)

    def list_capabilities(self, tags: Optional[list[str]] = None) -> list[Capability]:
        """列出能力，可按标签过滤"""
        if not tags:
            return list(self._capabilities.values())

        return [c for c in self._capabilities.values() if any(tag in c.tags for tag in tags)]

    def remove_capability(self, name: str) -> bool:
        """删除能力"""
        if name in self._capabilities:
            del self._capabilities[name]
            return True
        return False

    # ========== 策略管理 ==========

    def register_policy(self, name: str, policy: dict[str, Any]) -> None:
        """注册策略"""
        self._policies[name] = policy

    def get_policy(self, name: str) -> Optional[dict[str, Any]]:
        """获取策略"""
        return self._policies.get(name)

    def apply_policy_to_intent(self, policy_name: str, intent_name: str) -> bool:
        """将策略应用到意图"""
        policy = self.get_policy(policy_name)
        template = self.get_template(intent_name)

        if not policy or not template:
            return False

        # 将策略约束合并到模板
        template.constraints.update(policy.get("constraints", {}))
        template.required_permissions.extend(policy.get("required_permissions", []))
        return True

    # ==========  introspection（自省） ==========

    def introspect(self) -> dict[str, Any]:
        """返回注册中心的完整视图"""
        return {
            "templates": {
                name: {
                    "description": t.description,
                    "type": t.intent_type.value,
                    "version": t.version,
                    "tags": t.tags,
                }
                for name, t in self._templates.items()
            },
            "capabilities": {
                name: {
                    "description": c.description,
                    "tags": c.tags,
                }
                for name, c in self._capabilities.items()
            },
            "policies": self._policies,
        }

    def search(self, query: str) -> dict[str, list[str]]:
        """搜索匹配的模板和能力"""
        query_lower = query.lower()

        matched_templates = [
            name
            for name, t in self._templates.items()
            if query_lower in name.lower() or query_lower in t.description.lower()
        ]

        matched_capabilities = [
            name
            for name, c in self._capabilities.items()
            if query_lower in name.lower() or query_lower in c.description.lower()
        ]

        return {
            "templates": matched_templates,
            "capabilities": matched_capabilities,
        }


def capability(
    name: str,
    description: str = "",
    input_schema: Optional[dict] = None,
    output_schema: Optional[dict] = None,
    requires_permissions: Optional[list[str]] = None,
    tags: Optional[list[str]] = None,
):
    """
    能力装饰器
    用于快速注册能力函数

    用法:
        @capability("query_sales", description="查询销售数据")
        def query_sales(context, region: str, period: str):
            ...
    """

    def decorator(func: Callable) -> Callable:
        cap = Capability(
            name=name,
            description=description,
            input_schema=input_schema or {},
            output_schema=output_schema or {},
            func=func,
            requires_permissions=requires_permissions or [],
            tags=tags or [],
        )
        # 将能力附加到函数上，便于后续注册
        func._capability = cap
        return func

    return decorator
