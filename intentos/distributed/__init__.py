"""
分布式语义 VM 模块

分布式架构：
- 一致性哈希内存
- 多节点集群
- 容错/复制/分片
"""

from .vm import (
    DistributedSemanticVM,
    DistributedSemanticMemory,
    DistributedCoordinator,
    DistributedProgramCounter,
    VMNode,
    DistributedOpcode,
    create_distributed_vm,
    create_node,
)

__all__ = [
    "DistributedSemanticVM",
    "DistributedSemanticMemory",
    "DistributedCoordinator",
    "DistributedProgramCounter",
    "VMNode",
    "DistributedOpcode",
    "create_distributed_vm",
    "create_node",
]
