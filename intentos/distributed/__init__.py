"""
分布式语义 VM 模块

分布式架构：
- 一致性哈希内存
- 多节点集群
- 容错/复制/分片
- VM 社区共识（单归属约束）
"""

from .cluster_manager import (
    # 成员资格
    ClusterMembership,
    # 共识协议
    CommunityConsensusProtocol,
    # 社区发现
    CommunityDiscoveryProtocol,
    CommunityFullError,
    ConsensusNotReachedError,
    ConsensusVote,
    ConsensusVotingResult,
    MembershipStatus,
    # 异常
    SingleHomingViolationError,
    # VM 社区
    VMCommunity,
    # 节点成员
    VMCommunityMember,
    # 工厂函数
    create_community,
    create_community_member,
    create_consensus_protocol,
)
from .vm import (
    DistributedCoordinator,
    DistributedOpcode,
    DistributedProgramCounter,
    DistributedSemanticMemory,
    DistributedSemanticVM,
    VMNode,
    create_distributed_vm,
    create_node,
)

__all__ = [
    # 分布式 VM
    "DistributedSemanticVM",
    "DistributedSemanticMemory",
    "DistributedCoordinator",
    "DistributedProgramCounter",
    "VMNode",
    "DistributedOpcode",
    "create_distributed_vm",
    "create_node",
    # VM 社区（单归属约束）
    "VMCommunity",
    "ClusterMembership",
    "MembershipStatus",
    "VMCommunityMember",
    "CommunityConsensusProtocol",
    "ConsensusVote",
    "ConsensusVotingResult",
    "CommunityDiscoveryProtocol",
    "SingleHomingViolationError",
    "CommunityFullError",
    "ConsensusNotReachedError",
    "create_community",
    "create_community_member",
    "create_consensus_protocol",
]
