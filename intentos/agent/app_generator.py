# -*- coding: utf-8 -*-
"""
IntentOS App Generator Module

App 生成器模块，根据租户资源和用户身份即时生成 App 实例。
支持版本管理、个性化配置、能力绑定。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class GeneratedApp:
    """生成的 App 实例"""
    id: str                          # App 实例 ID
    app_id: str                      # App 定义 ID
    tenant_id: str                   # 租户 ID
    user_id: str                     # 用户 ID
    version: str                     # App 版本
    name: str                        # App 名称
    description: str                 # App 描述
    intents: dict[str, Any]          # 意图定义
    capabilities: dict[str, Any]     # 已绑定的能力
    config: dict[str, Any]           # 合并后的配置（默认 + 租户 + 个人）
    resources: dict[str, Any]        # 使用的资源
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None  # 过期时间（用于缓存）
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "app_id": self.app_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "intents": self.intents,
            "capabilities": {k: v.to_dict() if hasattr(v, "to_dict") else v for k, v in self.capabilities.items()},
            "config": self.config,
            "resources": {k: v.to_dict() if hasattr(v, "to_dict") else v for k, v in self.resources.items()},
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
        }

    def get_capability(self, capability_id: str) -> Optional[Any]:
        """获取能力"""
        return self.capabilities.get(capability_id)

    def get_intent(self, intent_id: str) -> Optional[dict[str, Any]]:
        """获取意图"""
        return self.intents.get(intent_id)


@dataclass
class AppGenerationRequest:
    """App 生成请求"""
    app_id: str                      # App 定义 ID
    tenant_id: str                   # 租户 ID
    user_id: str                     # 用户 ID
    version: Optional[str] = None    # 指定版本（可选）
    context: Optional[dict[str, Any]] = None  # 额外上下文

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "app_id": self.app_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "version": self.version,
            "context": self.context,
        }


class AppGenerator:
    """
    App 生成器

    根据租户资源和用户身份即时生成 App 实例。
    """

    def __init__(
        self,
        tenant_manager: Any,
        capability_binder: Any,
        personalization_manager: Any,
        version_manager: Any
    ) -> None:
        self.tenant_manager = tenant_manager
        self.capability_binder = capability_binder
        self.personalization_manager = personalization_manager
        self.version_manager = version_manager
        self.generated_apps: dict[str, GeneratedApp] = {}  # app_instance_id -> GeneratedApp
        logger.info("App 生成器初始化完成")

    def generate(
        self,
        request: AppGenerationRequest
    ) -> GeneratedApp:
        """
        生成 App 实例

        Args:
            request: App 生成请求

        Returns:
            生成的 App 实例
        """
        # 1. 获取租户信息
        tenant = self.tenant_manager.get_tenant(request.tenant_id)
        if not tenant:
            raise ValueError(f"租户不存在：{request.tenant_id}")

        # 2. 获取 App 定义（指定版本或最新版）
        version = request.version or self.version_manager.get_user_version(
            request.user_id, request.app_id
        )
        app_package = self.version_manager.get_version(request.app_id, version)
        if not app_package:
            raise ValueError(f"App 不存在：{request.app_id} v{version}")

        # 3. 获取个性化配置
        user_config = self.personalization_manager.get_config(
            request.user_id, request.app_id
        )

        # 4. 合并配置
        merged_config = self._merge_config(
            app_package.config.get("defaults", {}),
            tenant.config,
            user_config
        )

        # 5. 绑定能力
        bound_capabilities = self._bind_capabilities(
            app_package.capabilities,
            tenant,
            merged_config,
            request.user_id
        )

        # 6. 生成 App 实例 ID
        instance_id = self._generate_instance_id(
            request.app_id,
            request.tenant_id,
            request.user_id,
            version
        )

        # 7. 创建 App 实例
        generated_app = GeneratedApp(
            id=instance_id,
            app_id=request.app_id,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            version=version,
            name=app_package.name,
            description=app_package.description,
            intents=app_package.intents,
            capabilities=bound_capabilities,
            config=merged_config,
            resources={k: v for k, v in tenant.resources.items()},
            metadata={
                "generated_at": datetime.now().isoformat(),
                "user_config": user_config,
                "tenant_config": tenant.config,
            },
        )

        # 8. 缓存 App 实例
        self.generated_apps[instance_id] = generated_app

        logger.info(f"App 实例生成完成：{instance_id}")

        return generated_app

    def get_app(self, instance_id: str) -> Optional[GeneratedApp]:
        """获取生成的 App 实例"""
        return self.generated_apps.get(instance_id)

    def invalidate(self, instance_id: str) -> bool:
        """使 App 实例失效"""
        if instance_id in self.generated_apps:
            del self.generated_apps[instance_id]
            logger.info(f"App 实例已失效：{instance_id}")
            return True
        return False

    def invalidate_user_apps(self, user_id: str) -> int:
        """使指定用户的所有 App 实例失效"""
        count = 0
        to_remove = [
            instance_id for instance_id, app in self.generated_apps.items()
            if app.user_id == user_id
        ]
        for instance_id in to_remove:
            self.invalidate(instance_id)
            count += 1
        return count

    def _merge_config(
        self,
        defaults: dict[str, Any],
        tenant_config: dict[str, Any],
        user_config: dict[str, Any]
    ) -> dict[str, Any]:
        """
        合并配置

        优先级：user_config > tenant_config > defaults
        """
        merged = {}

        # 1. 应用默认配置
        merged.update(defaults)

        # 2. 应用租户配置
        merged.update(tenant_config)

        # 3. 应用用户配置（优先级最高）
        merged.update(user_config)

        return merged

    def _bind_capabilities(
        self,
        capabilities: dict[str, Any],
        tenant: Any,
        config: dict[str, Any],
        user_id: str
    ) -> dict[str, Any]:
        """绑定能力"""
        bound = {}

        for cap_id, cap_def in capabilities.items():
            template_id = cap_def.get("template_id", cap_id)

            try:
                # 使用能力绑定器绑定能力
                bound_cap = self.capability_binder.bind(
                    template_id=template_id,
                    tenant_id=tenant.id,
                    resources=tenant.resources,
                    config={**cap_def.get("config", {}), **config},
                    user_context type("UserContext", (), {"user_id": user_id})()
                )
                bound[cap_id] = bound_cap
            except Exception as e:
                logger.warning(f"能力绑定失败：{cap_id}, error={e}")
                # 绑定失败时，保留原始定义
                bound[cap_id] = cap_def

        return bound

    def _generate_instance_id(
        self,
        app_id: str,
        tenant_id: str,
        user_id: str,
        version: str
    ) -> str:
        """生成 App 实例 ID"""
        import hashlib
        content = f"{app_id}:{tenant_id}:{user_id}:{version}"
        hash_value = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"app_{app_id}_{hash_value}"


class AppInstanceCache:
    """
    App 实例缓存

    缓存生成的 App 实例，提高响应速度。
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600) -> None:
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: dict[str, tuple[GeneratedApp, datetime]] = {}
        logger.info(f"App 实例缓存初始化：max_size={max_size}, ttl={ttl_seconds}s")

    def get(self, instance_id: str) -> Optional[GeneratedApp]:
        """从缓存获取 App 实例"""
        if instance_id not in self.cache:
            return None

        app, created_at = self.cache[instance_id]
        
        # 检查是否过期
        if datetime.now() - created_at > timedelta(seconds=self.ttl_seconds):
            self.remove(instance_id)
            return None

        return app

    def put(self, app: GeneratedApp) -> None:
        """缓存 App 实例"""
        # 如果缓存已满，移除最旧的
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        self.cache[app.id] = (app, datetime.now())
        logger.debug(f"App 实例已缓存：{app.id}")

    def remove(self, instance_id: str) -> bool:
        """从缓存移除"""
        if instance_id in self.cache:
            del self.cache[instance_id]
            return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        logger.info("App 实例缓存已清空")

    def _evict_oldest(self) -> None:
        """移除最旧的缓存项"""
        if not self.cache:
            return

        oldest_id = min(
            self.cache.keys(),
            key=lambda k: self.cache[k][1]
        )
        self.remove(oldest_id)
        logger.debug(f"缓存驱逐：{oldest_id}")


# 导入 timedelta
from datetime import timedelta


# 全局 App 生成器实例
_global_app_generator: Optional[AppGenerator] = None
_global_app_cache: Optional[AppInstanceCache] = None


def get_app_generator(
    tenant_manager: Any = None,
    capability_binder: Any = None,
    personalization_manager: Any = None,
    version_manager: Any = None
) -> AppGenerator:
    """获取全局 App 生成器"""
    global _global_app_generator

    if _global_app_generator is None:
        # 延迟导入避免循环依赖
        from .tenant import get_tenant_manager
        from .capability_binding import get_capability_binder
        from .personalization import get_personalization_manager
        from .versioning import get_version_manager

        _global_app_generator = AppGenerator(
            tenant_manager=tenant_manager or get_tenant_manager(),
            capability_binder=capability_binder or get_capability_binder(),
            personalization_manager=personalization_manager or get_personalization_manager(),
            version_manager=version_manager or get_version_manager(),
        )

    return _global_app_generator


def get_app_cache() -> AppInstanceCache:
    """获取全局 App 实例缓存"""
    global _global_app_cache
    if _global_app_cache is None:
        _global_app_cache = AppInstanceCache()
    return _global_app_cache


def reset_app_generator() -> None:
    """重置 App 生成器"""
    global _global_app_generator, _global_app_cache
    _global_app_generator = None
    _global_app_cache = None
