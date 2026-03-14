"""
IntentOS - 分布式语义 VM + Self-Bootstrap

核心理念:
- 语义 VM: LLM 作为处理器，语义指令作为"机器码"
- 分布式：多节点集群，一致性哈希内存
- Self-Bootstrap: 系统可以修改自身的规则
"""

# 核心层
# Self-Bootstrap 层
from .bootstrap import (
    BootstrapPolicy,
    BootstrapPrograms,
    BootstrapValidator,
    SelfBootstrapExecutor,
    create_bootstrap_executor,
    create_bootstrap_policy,
)
from .core import (
    Capability,
    Context,
    Intent,
    IntentStatus,
    IntentType,
)

# 分布式层
from .distributed import (
    DistributedOpcode,
    DistributedSemanticVM,
    VMNode,
    create_distributed_vm,
    create_node,
)

# 语义 VM 层
from .semantic_vm import (
    SemanticInstruction,
    SemanticOpcode,
    SemanticProgram,
    SemanticVM,
    create_instruction,
    create_program,
    create_semantic_vm,
)

# 版本
__version__ = "6.0.0"

__all__ = [
    # 核心
    "Intent",
    "IntentType",
    "IntentStatus",
    "Context",
    "Capability",
    # 语义 VM
    "SemanticVM",
    "SemanticInstruction",
    "SemanticProgram",
    "SemanticOpcode",
    "create_semantic_vm",
    "create_program",
    "create_instruction",
    # 分布式
    "DistributedSemanticVM",
    "DistributedOpcode",
    "VMNode",
    "create_distributed_vm",
    "create_node",
    # Self-Bootstrap
    "SelfBootstrapExecutor",
    "BootstrapPolicy",
    "BootstrapPrograms",
    "BootstrapValidator",
    "create_bootstrap_executor",
    "create_bootstrap_policy",
]
