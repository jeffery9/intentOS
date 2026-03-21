# -*- coding: utf-8 -*-
"""
IntentOS Capability Binding Module

能力绑定模块，根据租户资源和用户身份动态绑定能力。
支持能力模板、资源注入、权限控制。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class CapabilityTemplate:
    """能力模板"""
    id: str                          # 模板 ID
    name: str                        # 能力名称
    description: str                 # 能力描述
    handler_template: str            # 处理器模板 (包含占位符)
    input_schema: dict[str, Any]     # 输入 Schema
    output_schema: dict[str, Any]    # 输出 Schema
    required_resources: list[str] = field(default_factory=list)  # 需要的资源类型
    config_schema: dict[str, Any] = field(default_factory=dict)  # 配置 Schema
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "handler_template": self.handler_template,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "required_resources": self.required_resources,
            "config_schema": self.config_schema,
            "tags": self.tags,
        }


@dataclass
class BoundCapability:
    """已绑定的能力"""
    id: str                          # 能力 ID (模板 ID + 租户 ID)
    template_id: str                 # 模板 ID
    tenant_id: str                   # 租户 ID
    name: str                        # 能力名称
    description: str                 # 能力描述
    handler: Callable[..., Any]      # 实际处理器
    input_schema: dict[str, Any]     # 输入 Schema
    output_schema: dict[str, Any]    # 输出 Schema
    bound_config: dict[str, Any]     # 绑定后的配置
    resources: dict[str, Any] = field(default_factory=dict)  # 绑定的资源
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "bound_config": self.bound_config,
            "resources": {k: v.to_dict() if hasattr(v, "to_dict") else v for k, v in self.resources.items()},
            "tags": self.tags,
            "metadata": self.metadata,
        }


class CapabilityBinder:
    """
    能力绑定器

    根据租户资源和用户身份动态绑定能力。
    """

    def __init__(self) -> None:
        self.templates: dict[str, CapabilityTemplate] = {}
        self.bound_capabilities: dict[str, dict[str, BoundCapability]] = {}  # template_id -> tenant_id -> capability
        logger.info("能力绑定器初始化完成")

    def register_template(self, template: CapabilityTemplate) -> None:
        """注册能力模板"""
        self.templates[template.id] = template
        logger.info(f"注册能力模板：{template.id}")

    def get_template(self, template_id: str) -> Optional[CapabilityTemplate]:
        """获取能力模板"""
        return self.templates.get(template_id)

    def bind(
        self,
        template_id: str,
        tenant_id: str,
        resources: dict[str, Any],
        config: Optional[dict[str, Any]] = None,
        user_context: Optional[Any] = None
    ) -> BoundCapability:
        """
        对齐新内核的能力绑定
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"能力模板不存在：{template_id}")

        # 1. 检查必需资源 (原有逻辑)
        for required_resource in template.required_resources:
            if required_resource not in resources:
                raise ValueError(
                    f"能力 {template_id} 需要资源 {required_resource}，但租户 {tenant_id} 未提供"
                )

        # 2. 合并配置并注入物理句柄 (对齐 OS 层 IO)
        bound_config = self._merge_config(template.config_schema, config or {}, resources)

        # 3. 创建处理器 (保持您的原有实现，但增加 Context 感知)
        handler = self._create_handler(template, bound_config, resources)

        # 4. 生成 BoundCapability
        # 注意：这里增加了对新内核 required_permissions 的自动映射
        capability_id = f"{template_id}_{tenant_id}"
        capability = BoundCapability(
            id=capability_id,
            template_id=template_id,
            tenant_id=tenant_id,
            name=template.name,
            description=template.description,
            handler=handler,
            input_schema=template.input_schema,
            output_schema=template.output_schema,
            bound_config=bound_config,
            resources=resources,
            tags=template.tags,
            metadata={
                "created_by": user_context.user_id if user_context else "system",
                "kernel_permission_required": f"tenant:{tenant_id}:use:{template_id}" # 自动生成内核权限名
            },
        )

        # 5. 【关键对齐】将绑定后的私有能力同步到 OS 层的注册中心
        from intentos.agent.registry import CapabilityRegistry
        registry = CapabilityRegistry()
        registry.register(
            id=capability_id,
            name=capability.name,
            description=capability.description,
            handler=capability.handler,
            required_permissions=[f"tenant:{tenant_id}:use:{template_id}"],
            source="paas_bound"
        )

        # 缓存绑定结果
        if template_id not in self.bound_capabilities:
            self.bound_capabilities[template_id] = {}
        self.bound_capabilities[template_id][tenant_id] = capability

        logger.info(f"✅ PaaS -> Kernel Alignment: Bound and registered private capability {capability_id}")

        return capability

    def get_bound_capability(
        self,
        template_id: str,
        tenant_id: str
    ) -> Optional[BoundCapability]:
        """获取已绑定的能力"""
        if template_id not in self.bound_capabilities:
            return None
        return self.bound_capabilities[template_id].get(tenant_id)

    def bind_private_resource(
        self,
        tenant_id: str,
        resource_id: str,
        capability_id: str
    ) -> bool:
        """
        私有资源嫁接 (Secure Resource Grafting)

        第一性原理：将物理资源（如私有 DB）绑定到语义能力（如 DataQuery），
        使 App 可以在不感知物理细节的情况下操作私有数据。
        """
        # 1. 获取绑定的能力实例
        # 注意：这里假设能力模板已经处理了资源注入逻辑
        bound_map = self.bound_capabilities.get(capability_id, {})
        if tenant_id not in bound_map:
            logger.warning(f"Tenant {tenant_id} has no bound capability {capability_id}")
            return False

        # 2. 标记该能力正在使用特定私有资源 (Virtual Handle)
        bound_cap = bound_map[tenant_id]
        bound_cap.metadata["private_resource_link"] = resource_id
        bound_cap.metadata["grafted_at"] = datetime.now().isoformat()

        logger.info(f"✅ Grafted private resource {resource_id} onto {capability_id} for tenant {tenant_id}")
        return True

    def get_grafted_context(self, tenant_id: str, app_instance_id: str) -> dict[str, Any]:
        """
        获取已嫁接的执行上下文

        为 App 执行提供已注入私有资源的物理句柄。
        """
        grafted_context = {
            "tenant_id": tenant_id,
            "app_instance": app_instance_id,
            "active_bindings": []
        }

        # 遍历所有已绑定的能力，提取其私有资源链接
        for tid, tenants in self.bound_capabilities.items():
            if tenant_id in tenants:
                cap = tenants[tenant_id]
                if "private_resource_link" in cap.metadata:
                    grafted_context["active_bindings"].append({
                        "capability": cap.id,
                        "resource_id": cap.metadata["private_resource_link"]
                    })

        return grafted_context

    def unbind(self, template_id: str, tenant_id: str) -> bool:
        """解绑能力 (恢复原有设计)"""
        if template_id not in self.bound_capabilities:
            return False

        if tenant_id in self.bound_capabilities[template_id]:
            del self.bound_capabilities[template_id][tenant_id]
            logger.info(f"能力解绑：{template_id}_{tenant_id}")
            return True
        return False

    def _merge_config(
        self,
        schema: dict[str, Any],
        config: dict[str, Any],
        resources: dict[str, Any]
    ) -> dict[str, Any]:
        """合并配置"""
        merged = {}

        # 应用默认值
        for key, prop in schema.get("properties", {}).items():
            if "default" in prop:
                merged[key] = prop["default"]

        # 从资源注入配置
        for resource_id, resource in resources.items():
            if hasattr(resource, "config"):
                merged.update(resource.config)

        # 覆盖用户配置
        merged.update(config)

        return merged

    def _create_handler(
        self,
        template: CapabilityTemplate,
        config: dict[str, Any],
        resources: dict[str, Any]
    ) -> Callable[..., Any]:
        """
        创建处理器

        根据模板和资源配置创建实际的处理函数。
        """
        # 解析处理器模板
        handler_code = template.handler_template

        # 替换占位符
        for key, value in config.items():
            placeholder = f"${{{key}}}"
            if isinstance(value, str):
                handler_code = handler_code.replace(placeholder, f'"{value}"')
            else:
                handler_code = handler_code.replace(placeholder, str(value))

        # 注入资源
        for resource_id, resource in resources.items():
            # 实际实现会根据资源类型创建具体的连接
            pass

        # 创建处理函数（这里使用一个通用的异步处理函数）
        async def handler(**kwargs: Any) -> dict[str, Any]:
            # 实际实现会根据模板执行对应的逻辑
            # 这里返回一个模拟结果
            return {
                "success": True,
                "data": {"message": f"能力 {template.name} 执行成功"},
                "config": config,
            }

        return handler


class ResourceInjector:
    """
    资源注入器

    将租户资源注入到能力中。
    """

    def __init__(self) -> None:
        self.resource_types: dict[str, type] = {}
        logger.info("资源注入器初始化完成")

    def register_resource_type(self, resource_type: str, cls: type) -> None:
        """注册资源类型"""
        self.resource_types[resource_type] = cls
        logger.info(f"注册资源类型：{resource_type}")

    def inject(
        self,
        resource_id: str,
        resource_config: dict[str, Any],
        target_context: dict[str, Any]
    ) -> Any:
        """
        注入资源

        Args:
            resource_id: 资源 ID
            resource_config: 资源配置
            target_context: 目标上下文

        Returns:
            注入的资源实例
        """
        resource_type = resource_config.get("type")
        if not resource_type:
            raise ValueError(f"资源 {resource_id} 未指定类型")

        cls = self.resource_types.get(resource_type)
        if not cls:
            # 如果没有注册类型，返回配置字典
            return resource_config

        # 创建资源实例
        instance = cls(**resource_config)
        target_context[resource_id] = instance
        logger.info(f"资源注入完成：{resource_id}")
        return instance


# 预定义的能力模板

DATA_LOADER_TEMPLATE = CapabilityTemplate(
    id="data_loader",
    name="数据加载器",
    description="从数据源加载数据",
    handler_template="""
async def load_data(path, format='auto'):
    # 从 ${data_source} 加载数据
    # 使用配置：${max_rows}, ${timeout}
    pass
""",
    input_schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "数据路径"},
            "format": {"type": "string", "enum": ["csv", "json", "parquet", "auto"]},
        },
        "required": ["path"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "data": {"type": "array"},
            "metadata": {"type": "object"},
        },
    },
    required_resources=["database"],
    config_schema={
        "properties": {
            "data_source": {"type": "string", "default": "default_db"},
            "max_rows": {"type": "integer", "default": 10000},
            "timeout": {"type": "integer", "default": 30},
        }
    },
    tags=["data", "io"],
)

ANALYZER_TEMPLATE = CapabilityTemplate(
    id="analyzer",
    name="数据分析器",
    description="分析数据并生成洞察",
    handler_template="""
async def analyze(data, metrics):
    # 使用 ${analysis_engine} 进行分析
    # 配置：${confidence_threshold}
    pass
""",
    input_schema={
        "type": "object",
        "properties": {
            "data": {"type": "array"},
            "metrics": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["data"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "insights": {"type": "array"},
            "statistics": {"type": "object"},
        },
    },
    required_resources=[],
    config_schema={
        "properties": {
            "analysis_engine": {"type": "string", "default": "builtin"},
            "confidence_threshold": {"type": "number", "default": 0.7},
        }
    },
    tags=["analysis", "ml"],
)

REPORTER_TEMPLATE = CapabilityTemplate(
    id="reporter",
    name="报告生成器",
    description="生成分析报告",
    handler_template="""
async def generate_report(analysis_result, template):
    # 使用 ${report_template} 生成报告
    # 配置：${format}, ${include_charts}
    pass
""",
    input_schema={
        "type": "object",
        "properties": {
            "analysis_result": {"type": "object"},
            "template": {"type": "string"},
        },
        "required": ["analysis_result"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "report": {"type": "string"},
            "charts": {"type": "array"},
        },
    },
    required_resources=[],
    config_schema={
        "properties": {
            "report_template": {"type": "string", "default": "default"},
            "format": {"type": "string", "enum": ["markdown", "html", "pdf"], "default": "markdown"},
            "include_charts": {"type": "boolean", "default": True},
        }
    },
    tags=["report", "generation"],
)


# 全局绑定器实例
_global_binder: Optional[CapabilityBinder] = None
_global_injector: Optional[ResourceInjector] = None


def get_capability_binder() -> CapabilityBinder:
    """获取全局能力绑定器"""
    global _global_binder
    if _global_binder is None:
        _global_binder = CapabilityBinder()
        # 注册预定义模板
        _global_binder.register_template(DATA_LOADER_TEMPLATE)
        _global_binder.register_template(ANALYZER_TEMPLATE)
        _global_binder.register_template(REPORTER_TEMPLATE)
    return _global_binder


def get_resource_injector() -> ResourceInjector:
    """获取全局资源注入器"""
    global _global_injector
    if _global_injector is None:
        _global_injector = ResourceInjector()
    return _global_injector


def reset_binding_services() -> None:
    """重置绑定服务"""
    global _global_binder, _global_injector
    _global_binder = None
    _global_injector = None
