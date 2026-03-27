"""
VM 社区共识管理

核心约束：
- 语义 VM 节点可以加入任意 VM 集群/社区
- 但在任意时刻，节点只能属于一个集群（单归属约束）

设计原则：
1. 去中心化：没有专门的 ClusterManager，节点通过共识形成社区
2. 自由加入：节点可以自由选择加入任何集群
3. 单一归属：同时只能属于一个集群
4. 优雅迁移：从一个集群迁移到另一个集群需要优雅切换
5. 共识验证：集群成员资格由社区共识验证
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# =============================================================================
# 成员状态
# =============================================================================


class MembershipStatus(Enum):
    """成员状态"""

    NONE = "none"  # 未加入任何集群
    JOINING = "joining"  # 正在加入
    ACTIVE = "active"  # 活跃成员
    LEAVING = "leaving"  # 正在离开
    SUSPENDED = "suspended"  # 被暂停


@dataclass
class ClusterMembership:
    """
    集群成员资格
    
    单归属约束的核心数据结构
    """
    node_id: str
    cluster_id: Optional[str] = None  # None 表示未加入任何集群
    status: MembershipStatus = MembershipStatus.NONE
    joined_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def is_member(self) -> bool:
        """检查是否属于某个集群"""
        return self.cluster_id is not None and self.status == MembershipStatus.ACTIVE
    
    def can_join(self) -> bool:
        """检查是否可以加入新集群"""
        # 只有未加入任何集群或状态为 SUSPENDED 的节点可以加入新集群
        return (
            self.cluster_id is None or 
            self.status == MembershipStatus.SUSPENDED
        )
    
    def can_leave(self) -> bool:
        """检查是否可以离开当前集群"""
        return self.is_member()
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "cluster_id": self.cluster_id,
            "status": self.status.value,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> ClusterMembership:
        return cls(
            node_id=data["node_id"],
            cluster_id=data.get("cluster_id"),
            status=MembershipStatus(data.get("status", "none")),
            joined_at=datetime.fromisoformat(data["joined_at"]) if data.get("joined_at") else None,
            last_heartbeat=datetime.fromisoformat(data["last_heartbeat"]) if data.get("last_heartbeat") else None,
            metadata=data.get("metadata", {}),
        )


# =============================================================================
# VM 社区/集群
# =============================================================================


@dataclass
class VMCommunity:
    """
    VM 社区（去中心化的集群）
    
    社区由节点共识形成，没有中央管理器
    """
    community_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    founder_id: str = ""  # 创始节点 ID
    consensus_threshold: float = 0.67  # 共识阈值（默认 2/3）
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # 成员列表（由共识维护）
    members: dict[str, ClusterMembership] = field(default_factory=dict)
    
    @property
    def member_count(self) -> int:
        """获取成员数量"""
        return len([m for m in self.members.values() if m.is_member()])
    
    def has_capacity(self, max_nodes: int = 100) -> bool:
        """检查是否有容量"""
        return self.member_count < max_nodes
    
    def get_active_members(self) -> list[str]:
        """获取活跃成员 ID 列表"""
        return [
            node_id for node_id, membership in self.members.items()
            if membership.is_member()
        ]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "community_id": self.community_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "founder_id": self.founder_id,
            "consensus_threshold": self.consensus_threshold,
            "member_count": self.member_count,
            "metadata": self.metadata,
            "members": {
                node_id: m.to_dict()
                for node_id, m in self.members.items()
            },
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> VMCommunity:
        community = cls(
            community_id=data["community_id"],
            name=data.get("name", ""),
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            founder_id=data.get("founder_id", ""),
            consensus_threshold=data.get("consensus_threshold", 0.67),
            metadata=data.get("metadata", {}),
        )
        # 恢复成员列表
        members_data = data.get("members", {})
        community.members = {
            node_id: ClusterMembership.from_dict(m_data)
            for node_id, m_data in members_data.items()
        }
        return community


# =============================================================================
# 单归属约束异常
# =============================================================================


class SingleHomingViolationError(Exception):
    """
    单归属约束违反异常
    
    当节点尝试加入新集群但尚未离开原集群时抛出
    """
    def __init__(self, node_id: str, current_community_id: str, target_community_id: str):
        self.node_id = node_id
        self.current_community_id = current_community_id
        self.target_community_id = target_community_id
        super().__init__(
            f"节点 {node_id} 已属于社区 {current_community_id}，"
            f"无法加入社区 {target_community_id}。请先离开当前社区。"
        )


class CommunityFullError(Exception):
    """社区已满异常"""
    def __init__(self, community_id: str, max_nodes: int):
        self.community_id = community_id
        self.max_nodes = max_nodes
        super().__init__(f"社区 {community_id} 已达到最大节点数 {max_nodes}")


class ConsensusNotReachedError(Exception):
    """共识未达成异常"""
    def __init__(self, community_id: str, votes: int, required: int):
        self.community_id = community_id
        self.votes = votes
        self.required = required
        super().__init__(
            f"社区 {community_id} 共识未达成：{votes}/{required} 票"
        )


# =============================================================================
# 节点社区成员（去中心化）
# =============================================================================


class VMCommunityMember:
    """
    VM 社区成员节点
    
    每个节点独立维护自己的成员资格，通过共识与社区同步
    """
    
    def __init__(self, node_id: Optional[str] = None):
        self.node_id = node_id or str(uuid.uuid4())
        self.membership: ClusterMembership = ClusterMembership(node_id=self.node_id)
        self.known_communities: dict[str, VMCommunity] = {}  # 已知的社区
        self._lock = asyncio.Lock()
    
    async def join_community(
        self,
        community: VMCommunity,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ClusterMembership:
        """
        加入社区
        
        单归属约束：节点在加入新社区前必须离开当前社区
        
        Args:
            community: 要加入的社区
            metadata: 可选的元数据
            
        Returns:
            更新后的成员资格
            
        Raises:
            SingleHomingViolationError: 违反单归属约束
            CommunityFullError: 社区已满
        """
        async with self._lock:
            # 检查单归属约束
            if not self.membership.can_join():
                raise SingleHomingViolationError(
                    self.node_id,
                    self.membership.cluster_id or "unknown",
                    community.community_id,
                )
            
            # 检查社区容量
            if not community.has_capacity():
                raise CommunityFullError(community.community_id, 100)
            
            # 更新本地成员资格
            self.membership.cluster_id = community.community_id
            self.membership.status = MembershipStatus.ACTIVE
            self.membership.joined_at = datetime.now()
            self.membership.last_heartbeat = datetime.now()
            self.membership.metadata = metadata or {}
            
            # 记录已知社区
            self.known_communities[community.community_id] = community
            
            return self.membership
    
    async def leave_community(self) -> ClusterMembership:
        """
        离开当前社区
        
        Returns:
            更新后的成员资格
        """
        async with self._lock:
            if not self.membership.can_leave():
                return self.membership
            
            self.membership.status = MembershipStatus.LEAVING
            self.membership.cluster_id = None
            self.membership.joined_at = None
            self.membership.metadata = {}
            self.membership.status = MembershipStatus.NONE
            
            return self.membership
    
    async def migrate_to_community(
        self,
        target_community: VMCommunity,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ClusterMembership:
        """
        迁移到新社区（原子操作：先离开原社区，再加入新社区）
        """
        async with self._lock:
            if self.membership.is_member():
                await self.leave_community()
            return await self.join_community(target_community, metadata)
    
    def get_current_community(self) -> Optional[VMCommunity]:
        """获取当前所属社区"""
        if not self.membership.cluster_id:
            return None
        return self.known_communities.get(self.membership.cluster_id)
    
    def is_member_of_any_community(self) -> bool:
        """检查是否属于任何社区"""
        return self.membership.is_member()


# =============================================================================
# 社区共识协议（去中心化）
# =============================================================================


class ConsensusVotingResult(Enum):
    """共识投票结果"""
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


@dataclass
class ConsensusVote:
    """共识投票"""
    voter_id: str
    proposal_id: str
    result: ConsensusVotingResult
    timestamp: datetime = field(default_factory=datetime.now)
    reason: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "voter_id": self.voter_id,
            "proposal_id": self.proposal_id,
            "result": self.result.value,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason,
        }


class CommunityConsensusProtocol:
    """
    社区共识协议
    
    去中心化的共识机制，节点通过投票达成成员资格共识
    """
    
    def __init__(self, community: VMCommunity):
        self.community = community
        self.pending_proposals: dict[str, dict] = {}  # proposal_id -> proposal
        self.votes: dict[str, list[ConsensusVote]] = {}  # proposal_id -> votes
    
    async def propose_new_member(
        self,
        node_id: str,
        proposer_id: str,
    ) -> str:
        """
        提议新成员加入
        
        Returns:
            proposal_id
        """
        proposal_id = str(uuid.uuid4())
        self.pending_proposals[proposal_id] = {
            "type": "new_member",
            "node_id": node_id,
            "proposer_id": proposer_id,
            "created_at": datetime.now(),
            "status": "pending",
        }
        self.votes[proposal_id] = []
        return proposal_id
    
    async def vote(
        self,
        proposal_id: str,
        voter_id: str,
        result: ConsensusVotingResult,
        reason: str = "",
    ) -> None:
        """投票"""
        vote = ConsensusVote(
            voter_id=voter_id,
            proposal_id=proposal_id,
            result=result,
            reason=reason,
        )
        self.votes[proposal_id].append(vote)
    
    async def check_consensus(
        self,
        proposal_id: str,
    ) -> tuple[bool, str]:
        """
        检查是否达成共识
        
        Returns:
            (是否达成，结果)
        """
        if proposal_id not in self.pending_proposals:
            return (False, "提案不存在")
        
        proposal = self.pending_proposals[proposal_id]
        votes = self.votes.get(proposal_id, [])
        
        # 统计票数
        approve_votes = len([v for v in votes if v.result == ConsensusVotingResult.APPROVE])
        reject_votes = len([v for v in votes if v.result == ConsensusVotingResult.REJECT])
        
        # 计算所需票数
        active_members = self.community.get_active_members()
        required_votes = int(len(active_members) * self.community.consensus_threshold)
        
        # 检查是否达成
        if approve_votes >= required_votes:
            proposal["status"] = "approved"
            return (True, "approved")
        
        if reject_votes >= required_votes:
            proposal["status"] = "rejected"
            return (True, "rejected")
        
        return (False, "pending")


# =============================================================================
# 分布式社区发现（Gossip 协议）
# =============================================================================


class CommunityDiscoveryProtocol:
    """
    社区发现协议
    
    使用 Gossip 协议在节点间传播社区信息
    """
    
    def __init__(self, node: VMCommunityMember):
        self.node = node
        self.peers: dict[str, str] = {}  # node_id -> address
    
    def add_peer(self, node_id: str, address: str) -> None:
        """添加对等节点"""
        self.peers[node_id] = address
    
    async def gossip_community_info(
        self,
        community: VMCommunity,
    ) -> None:
        """
        Gossip 传播社区信息
        
        向已知对等节点广播社区信息
        """
        # 在实际实现中，这里会通过 HTTP/gRPC 向其他节点发送消息
        # 这里是简化版本
        pass
    
    async def discover_communities(self) -> list[VMCommunity]:
        """
        发现可用的社区
        
        通过向对等节点查询来获取社区列表
        """
        # 在实际实现中，这里会查询对等节点
        return list(self.node.known_communities.values())


# =============================================================================
# 工厂函数
# =============================================================================


def create_community_member(node_id: Optional[str] = None) -> VMCommunityMember:
    """创建社区成员节点"""
    return VMCommunityMember(node_id=node_id)


def create_community(
    name: str = "",
    description: str = "",
    founder_id: str = "",
) -> VMCommunity:
    """创建 VM 社区"""
    return VMCommunity(
        name=name,
        description=description,
        founder_id=founder_id,
    )


def create_consensus_protocol(
    community: VMCommunity,
) -> CommunityConsensusProtocol:
    """创建共识协议"""
    return CommunityConsensusProtocol(community)
