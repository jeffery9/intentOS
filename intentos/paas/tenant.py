# -*- coding: utf-8 -*-
"""
IntentOS Tenant Management Module

租户管理模块，实现多租户隔离和资源配置。
每个租户拥有独立的资源、能力和配置。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class ResourceQuota:
    """资源配额"""
    cpu_seconds: int = 3600          # CPU 秒数/月
    memory_mb: int = 512             # 内存 MB
    storage_mb: int = 1024           # 存储 MB
    api_calls: int = 10000           # API 调用次数/月
    tokens: int = 1000000            # Token 数量/月
    bandwidth_mb: int = 1000         # 带宽 MB/月

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "cpu_seconds": self.cpu_seconds,
            "memory_mb": self.memory_mb,
            "storage_mb": self.storage_mb,
            "api_calls": self.api_calls,
            "tokens": self.tokens,
            "bandwidth_mb": self.bandwidth_mb,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResourceQuota":
        """从字典创建"""
        return cls(**data)


@dataclass
class TenantResource:
    """租户资源"""
    id: str                          # 资源 ID
    name: str                        # 资源名称
    type: str                        # 资源类型 (database/api/storage 等)
    config: dict[str, Any]           # 资源配置
    endpoint: Optional[str] = None   # 资源端点
    credentials: Optional[dict[str, str]] = None  # 访问凭证 (加密存储)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典 (不包含敏感信息)"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "config": self.config,
            "endpoint": self.endpoint,
            "metadata": self.metadata,
        }


@dataclass
class TenantCapability:
    """租户能力"""
    id: str                          # 能力 ID
    name: str                        # 能力名称
    description: str                 # 能力描述
    bound_config: dict[str, Any]     # 绑定后的配置
    rate_limit: Optional[dict[str, Any]] = None  # 速率限制
    enabled: bool = True             # 是否启用

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "bound_config": self.bound_config,
            "rate_limit": self.rate_limit,
            "enabled": self.enabled,
        }


@dataclass
class Tenant:
    """租户"""
    id: str                          # 租户 ID
    name: str                        # 租户名称
    status: str = "active"           # 状态 (active/suspended/deleted)
    plan: str = "free"               # 套餐 (free/pro/enterprise)
    quota: ResourceQuota = field(default_factory=ResourceQuota)
    resources: dict[str, TenantResource] = field(default_factory=dict)
    capabilities: dict[str, TenantCapability] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def get_resource(self, resource_id: str) -> Optional[TenantResource]:
        """获取资源"""
        return self.resources.get(resource_id)

    def get_capability(self, capability_id: str) -> Optional[TenantCapability]:
        """获取能力"""
        cap = self.capabilities.get(capability_id)
        if cap and cap.enabled:
            return cap
        return None

    def list_capabilities(self) -> list[str]:
        """列出可用能力 ID"""
        return [cap.id for cap in self.capabilities.values() if cap.enabled]

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "plan": self.plan,
            "quota": self.quota.to_dict(),
            "resources": {k: v.to_dict() for k, v in self.resources.items()},
            "capabilities": {k: v.to_dict() for k, v in self.capabilities.items()},
            "config": self.config,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class UserContext:
    """用户上下文"""
    tenant_id: str                   # 所属租户
    user_id: str                     # 用户 ID
    email: Optional[str] = None      # 邮箱
    roles: list[str] = field(default_factory=list)  # 角色列表
    permissions: list[str] = field(default_factory=list)  # 权限列表
    preferences: dict[str, Any] = field(default_factory=dict)  # 个人偏好
    metadata: dict[str, Any] = field(default_factory=dict)

    def has_role(self, role: str) -> bool:
        """检查是否有指定角色"""
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        """检查是否有指定权限"""
        return permission in self.permissions

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "email": self.email,
            "roles": self.roles,
            "permissions": self.permissions,
            "preferences": self.preferences,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserContext":
        """从字典创建"""
        return cls(
            tenant_id=data["tenant_id"],
            user_id=data["user_id"],
            email=data.get("email"),
            roles=data.get("roles", []),
            permissions=data.get("permissions", []),
            preferences=data.get("preferences", {}),
            metadata=data.get("metadata", {}),
        )


class TenantManager:
    """
    租户管理器

    管理所有租户的生命周期和资源配置。
    """

    def __init__(self) -> None:
        self.tenants: dict[str, Tenant] = {}
        logger.info("租户管理器初始化完成")

    def create_tenant(
        self,
        tenant_id: str,
        name: str,
        plan: str = "free",
        quota: Optional[ResourceQuota] = None,
        config: Optional[dict[str, Any]] = None
    ) -> Tenant:
        """创建租户"""
        if tenant_id in self.tenants:
            raise ValueError(f"租户已存在：{tenant_id}")

        tenant = Tenant(
            id=tenant_id,
            name=name,
            plan=plan,
            quota=quota or ResourceQuota(),
            config=config or {},
        )

        self.tenants[tenant_id] = tenant
        logger.info(f"创建租户：{tenant_id}, plan={plan}")

        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """获取租户"""
        return self.tenants.get(tenant_id)

    def delete_tenant(self, tenant_id: str) -> bool:
        """删除租户"""
        if tenant_id not in self.tenants:
            return False

        del self.tenants[tenant_id]
        logger.info(f"删除租户：{tenant_id}")
        return True

    def add_resource(
        self,
        tenant_id: str,
        resource: TenantResource
    ) -> bool:
        """添加租户资源"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        tenant.resources[resource.id] = resource
        tenant.updated_at = datetime.now()
        logger.info(f"租户 {tenant_id} 添加资源：{resource.id}")
        return True

    def remove_resource(self, tenant_id: str, resource_id: str) -> bool:
        """移除租户资源"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        if resource_id in tenant.resources:
            del tenant.resources[resource_id]
            tenant.updated_at = datetime.now()
            logger.info(f"租户 {tenant_id} 移除资源：{resource_id}")
            return True
        return False

    def add_capability(
        self,
        tenant_id: str,
        capability: TenantCapability
    ) -> bool:
        """添加租户能力"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        tenant.capabilities[capability.id] = capability
        tenant.updated_at = datetime.now()
        logger.info(f"租户 {tenant_id} 添加能力：{capability.id}")
        return True

    def enable_capability(self, tenant_id: str, capability_id: str) -> bool:
        """启用能力"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        if capability_id in tenant.capabilities:
            tenant.capabilities[capability_id].enabled = True
            tenant.updated_at = datetime.now()
            logger.info(f"租户 {tenant_id} 启用能力：{capability_id}")
            return True
        return False

    def disable_capability(self, tenant_id: str, capability_id: str) -> bool:
        """禁用能力"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        if capability_id in tenant.capabilities:
            tenant.capabilities[capability_id].enabled = False
            tenant.updated_at = datetime.now()
            logger.info(f"租户 {tenant_id} 禁用能力：{capability_id}")
            return True
        return False

    def update_config(
        self,
        tenant_id: str,
        config: dict[str, Any]
    ) -> bool:
        """更新租户配置"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        tenant.config.update(config)
        tenant.updated_at = datetime.now()
        logger.info(f"租户 {tenant_id} 更新配置")
        return True

    def list_tenants(
        self,
        status: Optional[str] = None,
        plan: Optional[str] = None
    ) -> list[Tenant]:
        """列出租户"""
        tenants = list(self.tenants.values())

        if status:
            tenants = [t for t in tenants if t.status == status]
        if plan:
            tenants = [t for t in tenants if t.plan == plan]

        return tenants

    def get_usage_stats(self, tenant_id: str) -> dict[str, Any]:
        """获取租户用量统计"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return {}

        # 实际实现会从计量系统获取真实用量
        return {
            "tenant_id": tenant_id,
            "period": "current_month",
            "usage": {
                "cpu_seconds": 0,
                "memory_mb": 0,
                "storage_mb": 0,
                "api_calls": 0,
                "tokens": 0,
            },
            "quota": tenant.quota.to_dict(),
            "usage_percent": {
                "cpu_seconds": 0,
                "api_calls": 0,
                "tokens": 0,
            },
        }


class RoleManager:
    """
    角色管理器

    管理用户角色和权限。
    """

    def __init__(self) -> None:
        # 预定义角色
        self.roles: dict[str, dict[str, Any]] = {
            "viewer": {
                "permissions": ["app:read", "data:read_own"],
            },
            "user": {
                "permissions": ["app:read", "app:execute", "data:read_own", "data:write_own"],
            },
            "developer": {
                "permissions": ["app:read", "app:execute", "app:deploy", "data:read_shared", "capability:register"],
            },
            "admin": {
                "permissions": ["*"],  # 所有权限
            },
        }
        logger.info("角色管理器初始化完成")

    def get_role_permissions(self, role: str) -> list[str]:
        """获取角色权限"""
        role_data = self.roles.get(role)
        if not role_data:
            return []
        return role_data.get("permissions", [])

    def create_user_context(
        self,
        tenant_id: str,
        user_id: str,
        roles: Optional[list[str]] = None,
        preferences: Optional[dict[str, Any]] = None
    ) -> UserContext:
        """创建用户上下文"""
        roles = roles or ["user"]
        
        # 收集所有权限
        permissions: set[str] = set()
        for role in roles:
            permissions.update(self.get_role_permissions(role))

        # 处理通配符权限
        if "*" in permissions:
            permissions = {"*"}

        return UserContext(
            tenant_id=tenant_id,
            user_id=user_id,
            roles=roles,
            permissions=list(permissions),
            preferences=preferences or {},
        )


# 全局租户管理器实例
_global_tenant_manager: Optional[TenantManager] = None
_global_role_manager: Optional[RoleManager] = None


def get_tenant_manager() -> TenantManager:
    """获取全局租户管理器"""
    global _global_tenant_manager
    if _global_tenant_manager is None:
        _global_tenant_manager = TenantManager()
    return _global_tenant_manager


def get_role_manager() -> RoleManager:
    """获取全局角色管理器"""
    global _global_role_manager
    if _global_role_manager is None:
        _global_role_manager = RoleManager()
    return _global_role_manager


def reset_tenant_services() -> None:
    """重置租户服务"""
    global _global_tenant_manager, _global_role_manager
    _global_tenant_manager = None
    _global_role_manager = None
