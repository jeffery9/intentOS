"""
运行时实例管理器 (Runtime Instance Manager)

管理意图包的运行态实例，支持按需下载、缓存和实例生成
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .intent_package import IntentPackage
from .registry import IntentPackageRegistry


@dataclass
class AppInstance:
    """
    应用实例
    
    运行态的意图包实例
    """
    instance_id: str
    app_id: str
    package: IntentPackage
    node_id: str
    tenant_id: str = ""
    user_id: str = ""
    
    # 实例配置
    config: dict[str, Any] = field(default_factory=dict)
    
    # 绑定的能力
    bound_capabilities: dict[str, Any] = field(default_factory=dict)
    
    # 状态
    created_at: datetime = field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None
    execution_count: int = 0
    status: str = "active"  # active, suspended, terminated
    
    # 缓存
    cache: dict[str, Any] = field(default_factory=dict)
    
    @property
    def full_instance_id(self) -> str:
        """完整实例 ID (包含租户信息)"""
        parts = [self.app_id, self.node_id, self.instance_id[:8]]
        if self.tenant_id:
            parts.insert(1, self.tenant_id)
        return ":".join(parts)
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "instance_id": self.instance_id,
            "app_id": self.app_id,
            "full_instance_id": self.full_instance_id,
            "node_id": self.node_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "config": self.config,
            "bound_capabilities": list(self.bound_capabilities.keys()),
            "created_at": self.created_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "execution_count": self.execution_count,
            "status": self.status,
        }
    
    def bind_capability(self, name: str, implementation: Any) -> None:
        """绑定能力实现"""
        self.bound_capabilities[name] = implementation
    
    def get_capability(self, name: str) -> Optional[Any]:
        """获取绑定的能力"""
        return self.bound_capabilities.get(name)
    
    def touch(self) -> None:
        """更新最后使用时间"""
        self.last_used_at = datetime.now()
        self.execution_count += 1
    
    def update_status(self, status: str) -> None:
        """更新状态"""
        self.status = status


@dataclass
class InstanceCache:
    """实例缓存"""
    max_size: int = 1000
    ttl_seconds: int = 3600  # 1 小时
    
    instances: dict[str, AppInstance] = field(default_factory=dict)
    access_order: list[str] = field(default_factory=list)
    
    def get(self, instance_id: str) -> Optional[AppInstance]:
        """获取缓存的实例"""
        instance = self.instances.get(instance_id)
        if instance:
            # 更新访问顺序
            if instance_id in self.access_order:
                self.access_order.remove(instance_id)
            self.access_order.append(instance_id)
            instance.touch()
        return instance
    
    def put(self, instance: AppInstance) -> None:
        """缓存实例"""
        if len(self.instances) >= self.max_size:
            # LRU 淘汰
            self._evict()
        
        self.instances[instance.instance_id] = instance
        self.access_order.append(instance.instance_id)
    
    def remove(self, instance_id: str) -> bool:
        """移除实例"""
        if instance_id in self.instances:
            del self.instances[instance_id]
            if instance_id in self.access_order:
                self.access_order.remove(instance_id)
            return True
        return False
    
    def _evict(self) -> None:
        """淘汰最久未使用的实例"""
        if self.access_order:
            oldest_id = self.access_order.pop(0)
            if oldest_id in self.instances:
                del self.instances[oldest_id]
    
    def clear_expired(self) -> int:
        """清除过期实例"""
        now = datetime.now()
        expired = []
        
        for instance_id, instance in self.instances.items():
            if instance.last_used_at:
                age = (now - instance.last_used_at).total_seconds()
                if age > self.ttl_seconds:
                    expired.append(instance_id)
        
        for instance_id in expired:
            self.remove(instance_id)
        
        return len(expired)
    
    def stats(self) -> dict[str, Any]:
        """缓存统计"""
        return {
            "size": len(self.instances),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
        }


class RuntimeInstanceManager:
    """
    运行时实例管理器
    
    管理意图包的运行态实例生命周期
    """
    
    def __init__(
        self,
        registry: IntentPackageRegistry,
        node_id: str = "local",
        cache_max_size: int = 1000,
        cache_ttl: int = 3600,
    ):
        self.registry = registry
        self.node_id = node_id
        self.cache = InstanceCache(max_size=cache_max_size, ttl_seconds=cache_ttl)
        self.instances: dict[str, AppInstance] = {}
    
    def create_instance(
        self,
        app_id: str,
        tenant_id: str = "",
        user_id: str = "",
        config: Optional[dict[str, Any]] = None,
    ) -> AppInstance:
        """
        创建应用实例
        
        Args:
            app_id: 应用 ID
            tenant_id: 租户 ID
            user_id: 用户 ID
            config: 实例配置
            
        Returns:
            创建的应用实例
        """
        package = self.registry.get_package(app_id)
        if not package:
            raise ValueError(f"Intent package {app_id} not found")
        
        instance_id = str(uuid.uuid4())
        instance = AppInstance(
            instance_id=instance_id,
            app_id=app_id,
            package=package,
            node_id=self.node_id,
            tenant_id=tenant_id,
            user_id=user_id,
            config=config or {},
        )
        
        # 自动绑定系统能力
        self._bind_system_capabilities(instance)
        
        # 缓存实例
        self.cache.put(instance)
        self.instances[instance.instance_id] = instance
        
        # 更新注册表计数
        self.registry.increment_instance_count(app_id)
        
        return instance
    
    def get_instance(self, instance_id: str) -> Optional[AppInstance]:
        """获取实例"""
        return self.cache.get(instance_id)
    
    def get_or_create_instance(
        self,
        app_id: str,
        tenant_id: str = "",
        user_id: str = "",
        config: Optional[dict[str, Any]] = None,
    ) -> AppInstance:
        """
        获取或创建实例
        
        如果缓存中存在则返回，否则创建新实例
        """
        # 尝试从缓存获取（简化版本，实际应该根据 tenant/user 查找）
        for instance in self.cache.instances.values():
            if (instance.app_id == app_id and 
                instance.tenant_id == tenant_id and
                instance.user_id == user_id):
                return self.cache.get(instance.instance_id)
        
        # 创建新实例
        return self.create_instance(app_id, tenant_id, user_id, config)
    
    def release_instance(self, instance_id: str) -> bool:
        """
        释放实例
        
        Args:
            instance_id: 实例 ID
            
        Returns:
            是否成功释放
        """
        instance = self.instances.get(instance_id)
        if not instance:
            return False
        
        # 更新状态
        instance.update_status("terminated")
        
        # 从缓存移除
        self.cache.remove(instance_id)
        
        # 从实例列表移除
        if instance_id in self.instances:
            del self.instances[instance_id]
        
        # 更新注册表计数
        self.registry.decrement_instance_count(instance.app_id)
        
        return True
    
    def suspend_instance(self, instance_id: str) -> bool:
        """暂停实例"""
        instance = self.get_instance(instance_id)
        if instance:
            instance.update_status("suspended")
            return True
        return False
    
    def resume_instance(self, instance_id: str) -> bool:
        """恢复实例"""
        instance = self.get_instance(instance_id)
        if instance:
            instance.update_status("active")
            return True
        return False
    
    def _bind_system_capabilities(self, instance: AppInstance) -> None:
        """绑定系统能力"""
        # 从 manifest 中获取能力需求
        for capability in instance.package.capabilities:
            cap_type = capability.get("type", "io")
            
            if cap_type == "system":
                # 系统能力（如 shell, filesystem）
                cap_name = capability["name"]
                
                # 这里应该绑定实际的系统能力实现
                # 示例：
                if cap_name == "shell":
                    instance.bind_capability("shell", self._get_shell_capability())
                elif cap_name == "filesystem":
                    instance.bind_capability("filesystem", self._get_filesystem_capability())
    
    def _get_shell_capability(self) -> Any:
        """获取 Shell 能力"""
        # 实际实现应该返回 Shell 能力对象
        return {"type": "system", "name": "shell"}
    
    def _get_filesystem_capability(self) -> Any:
        """获取文件系统能力"""
        # 实际实现应该返回文件系统能力对象
        return {"type": "system", "name": "filesystem"}
    
    def list_instances(
        self,
        app_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[AppInstance]:
        """列出实例"""
        instances = list(self.instances.values())
        
        if app_id:
            instances = [i for i in instances if i.app_id == app_id]
        if tenant_id:
            instances = [i for i in instances if i.tenant_id == tenant_id]
        if status:
            instances = [i for i in instances if i.status == status]
        
        return instances
    
    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        instances = list(self.instances.values())
        
        return {
            "total_instances": len(instances),
            "active_instances": sum(1 for i in instances if i.status == "active"),
            "suspended_instances": sum(1 for i in instances if i.status == "suspended"),
            "cache_stats": self.cache.stats(),
            "registry_stats": self.registry.get_statistics(),
        }
    
    def cleanup(self) -> int:
        """清理过期实例"""
        expired_count = self.cache.clear_expired()
        return expired_count


# =============================================================================
# 工厂函数
# =============================================================================


def create_instance_manager(
    registry: IntentPackageRegistry,
    node_id: str = "local",
    cache_max_size: int = 1000,
    cache_ttl: int = 3600,
) -> RuntimeInstanceManager:
    """创建实例管理器"""
    return RuntimeInstanceManager(
        registry=registry,
        node_id=node_id,
        cache_max_size=cache_max_size,
        cache_ttl=cache_ttl,
    )
