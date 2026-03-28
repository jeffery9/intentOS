"""
IntentOS Bootstrap 模块

Self-Bootstrap 自举机制：系统可以修改自身的规则
"""

import logging

from .executor import (
    SelfBootstrapExecutor,
    BootstrapRecord,
    BootstrapPolicy,
    create_bootstrap_executor,
    create_bootstrap_policy,
)

from .meta_intent_executor import (
    MetaIntentExecutor,
    MetaIntent,
    MetaIntentType,
    BootstrapPolicy as MetaPolicy,
    create_meta_intent_executor,
    create_meta_intent,
)

from .protocol_extender import (
    ProtocolSelfExtender,
    CapabilityGap,
    ExtensionSuggestion,
)

from .template_grower import (
    IntentTemplateSelfGrower,
    IntentPatternMiner,
    IntentPattern,
)

from .self_modifying_os import (
    SelfModifyingOS,
    OSComponent,
    create_self_modifying_os,
)

from .dual_memory_os import (
    DualMemoryOS,
    MemoryBank,
    MemoryBankStatus,
    create_dual_memory_os,
)

from .self_reproduction import (
    SelfReproduction,
    ReproductionType,
    ReproductionStatus,
    ReproductionPlan,
    IntentOSInstance,
    AuditLog,
    SecurityError,
)

__all__ = [
    # Self-Bootstrap 执行器
    "SelfBootstrapExecutor",
    "BootstrapRecord",
    "BootstrapPolicy",
    "create_bootstrap_executor",
    "create_bootstrap_policy",
    # 元意图执行器
    "MetaIntentExecutor",
    "MetaIntent",
    "MetaIntentType",
    "MetaPolicy",
    "create_meta_intent_executor",
    "create_meta_intent",
    # 协议自扩展
    "ProtocolSelfExtender",
    "CapabilityGap",
    "ExtensionSuggestion",
    # 模板自生长
    "IntentTemplateSelfGrower",
    "IntentPatternMiner",
    "IntentPattern",
    # 自修改 OS
    "SelfModifyingOS",
    "OSComponent",
    "create_self_modifying_os",
    # 双内存 OS
    "DualMemoryOS",
    "MemoryBank",
    "MemoryBankStatus",
    "create_dual_memory_os",
    # 自我繁殖
    "SelfReproduction",
    "ReproductionType",
    "ReproductionStatus",
    "ReproductionPlan",
    "IntentOSInstance",
    "AuditLog",
    "SecurityError",
]
