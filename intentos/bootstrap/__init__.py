"""
IntentOS Bootstrap 模块

Self-Bootstrap 自举机制：系统可以修改自身的规则
"""

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
]
