"""
意图包注册表 (Intent Package Registry)

管理已安装的意图包，支持能力查找和绑定
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .intent_package import IntentPackage


@dataclass
class PackageInstallation:
    """已安装的意图包"""
    package: IntentPackage
    installed_at: datetime = field(default_factory=datetime.now)
    enabled: bool = True
    instance_count: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "app_id": self.package.app_id,
            "name": self.package.name,
            "version": self.package.version,
            "installed_at": self.installed_at.isoformat(),
            "enabled": self.enabled,
            "instance_count": self.instance_count,
        }


class IntentPackageRegistry:
    """
    意图包注册表
    
    管理已安装的意图包，提供能力查找和绑定服务
    """
    
    def __init__(self):
        self.packages: dict[str, PackageInstallation] = {}
        self.capability_index: dict[str, str] = {}  # capability_name -> app_id
    
    def register(self, package: IntentPackage) -> None:
        """
        注册意图包
        
        Args:
            package: 要注册的意图包
        """
        installation = PackageInstallation(package=package)
        self.packages[package.app_id] = installation
        
        # 索引能力
        for capability in package.capabilities:
            cap_name = capability["name"]
            if cap_name not in self.capability_index:
                self.capability_index[cap_name] = package.app_id
    
    def unregister(self, app_id: str) -> None:
        """
        注销意图包
        
        Args:
            app_id: 应用 ID
        """
        if app_id in self.packages:
            installation = self.packages[app_id]
            
            # 从能力索引中移除
            for capability in installation.package.capabilities:
                cap_name = capability["name"]
                if self.capability_index.get(cap_name) == app_id:
                    del self.capability_index[cap_name]
            
            del self.packages[app_id]
    
    def get_package(self, app_id: str) -> Optional[IntentPackage]:
        """获取意图包"""
        installation = self.packages.get(app_id)
        return installation.package if installation else None
    
    def get_installation(self, app_id: str) -> Optional[PackageInstallation]:
        """获取安装信息"""
        return self.packages.get(app_id)
    
    def list_packages(self) -> list[IntentPackage]:
        """列出所有已注册的意图包"""
        return [inst.package for inst in self.packages.values()]
    
    def find_capability(self, capability_name: str) -> Optional[str]:
        """
        查找提供指定能力的意图包
        
        Args:
            capability_name: 能力名称
            
        Returns:
            提供该能力的意图包 ID，如果不存在则返回 None
        """
        return self.capability_index.get(capability_name)
    
    def find_capabilities(self, capability_names: list[str]) -> dict[str, str]:
        """
        批量查找能力提供者
        
        Args:
            capability_names: 能力名称列表
            
        Returns:
            {capability_name: app_id} 映射
        """
        result = {}
        for cap_name in capability_names:
            app_id = self.find_capability(cap_name)
            if app_id:
                result[cap_name] = app_id
        return result
    
    def enable(self, app_id: str) -> bool:
        """启用意图包"""
        installation = self.packages.get(app_id)
        if installation:
            installation.enabled = True
            return True
        return False
    
    def disable(self, app_id: str) -> bool:
        """禁用意图包"""
        installation = self.packages.get(app_id)
        if installation:
            installation.enabled = False
            return True
        return False
    
    def increment_instance_count(self, app_id: str) -> None:
        """增加实例计数"""
        installation = self.packages.get(app_id)
        if installation:
            installation.instance_count += 1
    
    def decrement_instance_count(self, app_id: str) -> None:
        """减少实例计数"""
        installation = self.packages.get(app_id)
        if installation:
            installation.instance_count = max(0, installation.instance_count - 1)
    
    def get_statistics(self) -> dict[str, Any]:
        """获取注册表统计"""
        return {
            "total_packages": len(self.packages),
            "enabled_packages": sum(1 for inst in self.packages.values() if inst.enabled),
            "total_capabilities": len(self.capability_index),
            "total_instances": sum(inst.instance_count for inst in self.packages.values()),
        }
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "packages": [inst.to_dict() for inst in self.packages.values()],
            "capabilities": self.capability_index,
            "statistics": self.get_statistics(),
        }


# =============================================================================
# 全局注册表
# =============================================================================


_global_registry: Optional[IntentPackageRegistry] = None


def get_global_registry() -> IntentPackageRegistry:
    """获取全局注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = IntentPackageRegistry()
    return _global_registry


def register_intent_package(package: IntentPackage) -> None:
    """注册意图包到全局注册表"""
    get_global_registry().register(package)


def unregister_intent_package(app_id: str) -> None:
    """从全局注册表注销意图包"""
    get_global_registry().unregister(app_id)


def find_capability_provider(capability_name: str) -> Optional[str]:
    """查找能力提供者"""
    return get_global_registry().find_capability(capability_name)
