"""
IntentOS Apps 模块

AI Native App 运行时支持
"""

from .instance_manager import (
    AppInstance,
    InstanceCache,
    RuntimeInstanceManager,
    create_instance_manager,
)
from .intent_package import (
    IntentPackage,
    IntentPackageLoader,
    ValidationResult,
    create_intent_package,
    load_intent_package,
    validate_intent_package,
)
from .registry import (
    IntentPackageRegistry,
    PackageInstallation,
    find_capability_provider,
    get_global_registry,
    register_intent_package,
    unregister_intent_package,
)

__all__ = [
    # 意图包
    "IntentPackage",
    "IntentPackageLoader",
    "ValidationResult",
    "load_intent_package",
    "validate_intent_package",
    "create_intent_package",
    # 注册表
    "PackageInstallation",
    "IntentPackageRegistry",
    "get_global_registry",
    "register_intent_package",
    "unregister_intent_package",
    "find_capability_provider",
    # 实例管理
    "AppInstance",
    "InstanceCache",
    "RuntimeInstanceManager",
    "create_instance_manager",
]
