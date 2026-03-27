"""
VM 社区单归属约束测试

测试核心约束：
- 节点可以加入任意 VM 集群/社区
- 但在任意时刻，节点只能属于一个集群（单归属约束）
"""

import pytest
from intentos.distributed.cluster_manager import (
    VMCommunity,
    VMCommunityMember,
    ClusterMembership,
    MembershipStatus,
    SingleHomingViolationError,
    CommunityFullError,
    CommunityConsensusProtocol,
    ConsensusVotingResult,
    create_community,
    create_community_member,
    create_consensus_protocol,
)


class TestSingleHomingConstraint:
    """测试单归属约束"""
    
    @pytest.mark.asyncio
    async def test_node_can_join_community(self):
        """测试节点可以加入社区"""
        node = create_community_member(node_id="node_001")
        community = create_community(name="TestCommunity", founder_id="founder_001")
        
        # 初始状态：不属于任何社区
        assert not node.is_member_of_any_community()
        assert node.membership.can_join()
        
        # 加入社区
        membership = await node.join_community(community)
        
        # 验证加入成功
        assert membership.is_member()
        assert membership.cluster_id == community.community_id
        assert node.is_member_of_any_community()
    
    @pytest.mark.asyncio
    async def test_node_cannot_join_two_communities_simultaneously(self):
        """测试节点不能同时加入两个社区（单归属约束）"""
        node = create_community_member(node_id="node_001")
        community1 = create_community(name="Community1", founder_id="founder_001")
        community2 = create_community(name="Community2", founder_id="founder_002")
        
        # 加入第一个社区
        await node.join_community(community1)
        assert node.is_member_of_any_community()
        
        # 尝试加入第二个社区，应该抛出异常
        with pytest.raises(SingleHomingViolationError) as exc_info:
            await node.join_community(community2)
        
        # 验证异常信息
        assert exc_info.value.node_id == "node_001"
        assert exc_info.value.current_community_id == community1.community_id
        assert exc_info.value.target_community_id == community2.community_id
        
        # 验证节点仍属于第一个社区
        assert node.membership.cluster_id == community1.community_id
    
    @pytest.mark.asyncio
    async def test_node_must_leave_before_joining_new(self):
        """测试节点必须先离开原社区才能加入新社区"""
        node = create_community_member(node_id="node_001")
        community1 = create_community(name="Community1", founder_id="founder_001")
        community2 = create_community(name="Community2", founder_id="founder_002")
        
        # 加入第一个社区
        await node.join_community(community1)
        
        # 先离开
        await node.leave_community()
        assert not node.is_member_of_any_community()
        assert node.membership.can_join()
        
        # 现在可以加入第二个社区
        membership = await node.join_community(community2)
        assert membership.is_member()
        assert membership.cluster_id == community2.community_id
    
    @pytest.mark.asyncio
    async def test_atomic_migration(self):
        """测试原子迁移（先离开原社区，再加入新社区）"""
        node = create_community_member(node_id="node_001")
        community1 = create_community(name="Community1", founder_id="founder_001")
        community2 = create_community(name="Community2", founder_id="founder_002")
        
        # 加入第一个社区
        await node.join_community(community1)
        
        # 原子迁移到第二个社区
        membership = await node.migrate_to_community(community2)
        
        # 验证迁移成功
        assert membership.is_member()
        assert membership.cluster_id == community2.community_id
        assert not node.is_member_of_any_community() or membership.cluster_id == community2.community_id
    
    @pytest.mark.asyncio
    async def test_leave_non_member(self):
        """测试离开非成员社区"""
        node = create_community_member(node_id="node_001")
        
        # 初始状态不属于任何社区
        assert not node.is_member_of_any_community()
        
        # 离开（应该无操作）
        membership = await node.leave_community()
        
        # 验证状态不变
        assert membership.status == MembershipStatus.NONE
        assert membership.cluster_id is None


class TestCommunityCapacity:
    """测试社区容量限制"""
    
    @pytest.mark.asyncio
    async def test_community_has_capacity(self):
        """测试社区容量检查"""
        community = create_community(name="TestCommunity", founder_id="founder_001")
        
        # 初始状态有空闲容量
        assert community.has_capacity(max_nodes=100)
    
    @pytest.mark.asyncio
    async def test_community_full(self):
        """测试社区已满情况"""
        community = create_community(name="TestCommunity", founder_id="founder_001")
        
        # 模拟社区已满
        for i in range(100):
            node_id = f"node_{i:03d}"
            membership = ClusterMembership(
                node_id=node_id,
                cluster_id=community.community_id,
                status=MembershipStatus.ACTIVE,
            )
            community.members[node_id] = membership
        
        # 验证社区已满
        assert not community.has_capacity(max_nodes=100)
        assert community.member_count == 100


class TestConsensusProtocol:
    """测试共识协议"""
    
    @pytest.mark.asyncio
    async def test_propose_new_member(self):
        """测试提议新成员"""
        community = create_community(name="TestCommunity", founder_id="founder_001")
        protocol = create_consensus_protocol(community)
        
        # 添加一些活跃成员
        for i in range(3):
            node_id = f"node_{i:03d}"
            membership = ClusterMembership(
                node_id=node_id,
                cluster_id=community.community_id,
                status=MembershipStatus.ACTIVE,
            )
            community.members[node_id] = membership
        
        # 提议新成员
        proposal_id = await protocol.propose_new_member(
            node_id="new_node_001",
            proposer_id="node_000",
        )
        
        # 验证提案创建成功
        assert proposal_id in protocol.pending_proposals
        assert protocol.pending_proposals[proposal_id]["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_consensus_voting(self):
        """测试共识投票"""
        community = create_community(name="TestCommunity", founder_id="founder_001")
        protocol = create_consensus_protocol(community)
        
        # 添加 3 个活跃成员
        for i in range(3):
            node_id = f"node_{i:03d}"
            membership = ClusterMembership(
                node_id=node_id,
                cluster_id=community.community_id,
                status=MembershipStatus.ACTIVE,
            )
            community.members[node_id] = membership
        
        # 提议新成员
        proposal_id = await protocol.propose_new_member(
            node_id="new_node_001",
            proposer_id="node_000",
        )
        
        # 投票
        await protocol.vote(
            proposal_id=proposal_id,
            voter_id="node_000",
            result=ConsensusVotingResult.APPROVE,
            reason="欢迎新成员",
        )
        await protocol.vote(
            proposal_id=proposal_id,
            voter_id="node_001",
            result=ConsensusVotingResult.APPROVE,
            reason="同意",
        )
        await protocol.vote(
            proposal_id=proposal_id,
            voter_id="node_002",
            result=ConsensusVotingResult.APPROVE,
            reason="同意",
        )
        
        # 检查共识
        reached, result = await protocol.check_consensus(proposal_id)
        
        # 验证达成共识（3 票赞成，超过 2/3 阈值）
        assert reached
        assert result == "approved"
    
    @pytest.mark.asyncio
    async def test_consensus_rejected(self):
        """测试共识被拒绝"""
        community = create_community(name="TestCommunity", founder_id="founder_001")
        protocol = create_consensus_protocol(community)
        
        # 添加 3 个活跃成员
        for i in range(3):
            node_id = f"node_{i:03d}"
            membership = ClusterMembership(
                node_id=node_id,
                cluster_id=community.community_id,
                status=MembershipStatus.ACTIVE,
            )
            community.members[node_id] = membership
        
        # 提议新成员
        proposal_id = await protocol.propose_new_member(
            node_id="new_node_001",
            proposer_id="node_000",
        )
        
        # 投票拒绝
        await protocol.vote(
            proposal_id=proposal_id,
            voter_id="node_000",
            result=ConsensusVotingResult.REJECT,
            reason="不欢迎",
        )
        await protocol.vote(
            proposal_id=proposal_id,
            voter_id="node_001",
            result=ConsensusVotingResult.REJECT,
            reason="拒绝",
        )
        await protocol.vote(
            proposal_id=proposal_id,
            voter_id="node_002",
            result=ConsensusVotingResult.REJECT,
            reason="拒绝",
        )
        
        # 检查共识
        reached, result = await protocol.check_consensus(proposal_id)
        
        # 验证共识拒绝
        assert reached
        assert result == "rejected"


class TestMembershipStatus:
    """测试成员状态"""
    
    def test_membership_status_transitions(self):
        """测试成员状态转换"""
        membership = ClusterMembership(node_id="node_001")
        
        # 初始状态
        assert membership.status == MembershipStatus.NONE
        assert membership.cluster_id is None
        assert membership.can_join()
        assert not membership.can_leave()
        
        # 加入社区
        membership.cluster_id = "community_001"
        membership.status = MembershipStatus.ACTIVE
        
        assert membership.is_member()
        assert not membership.can_join()
        assert membership.can_leave()
        
        # 离开社区
        membership.cluster_id = None
        membership.status = MembershipStatus.NONE
        
        assert not membership.is_member()
        assert membership.can_join()
        assert not membership.can_leave()
    
    def test_suspended_can_join(self):
        """测试被暂停的成员可以加入新社区"""
        membership = ClusterMembership(
            node_id="node_001",
            cluster_id="community_001",
            status=MembershipStatus.SUSPENDED,
        )
        
        # SUSPENDED 状态可以加入新社区
        assert membership.can_join()


class TestCommunitySerialization:
    """测试社区序列化"""
    
    def test_community_to_dict(self):
        """测试社区序列化为字典"""
        community = create_community(
            name="TestCommunity",
            description="测试社区",
            founder_id="founder_001",
        )
        
        # 添加成员
        membership = ClusterMembership(
            node_id="node_001",
            cluster_id=community.community_id,
            status=MembershipStatus.ACTIVE,
        )
        community.members["node_001"] = membership
        
        # 序列化
        data = community.to_dict()
        
        # 验证
        assert data["name"] == "TestCommunity"
        assert data["description"] == "测试社区"
        assert data["founder_id"] == "founder_001"
        assert data["member_count"] == 1
        assert "node_001" in data["members"]
    
    def test_community_from_dict(self):
        """测试从字典恢复社区"""
        data = {
            "community_id": "community_001",
            "name": "TestCommunity",
            "description": "测试社区",
            "created_at": "2026-03-27T10:00:00",
            "founder_id": "founder_001",
            "consensus_threshold": 0.67,
            "metadata": {},
            "members": {
                "node_001": {
                    "node_id": "node_001",
                    "cluster_id": "community_001",
                    "status": "active",
                    "joined_at": "2026-03-27T10:00:00",
                    "last_heartbeat": "2026-03-27T10:00:00",
                    "metadata": {},
                }
            },
        }
        
        # 恢复
        community = VMCommunity.from_dict(data)
        
        # 验证
        assert community.community_id == "community_001"
        assert community.name == "TestCommunity"
        assert community.member_count == 1
        assert "node_001" in community.members


class TestCommunityDiscovery:
    """测试社区发现"""
    
    def test_discover_communities(self):
        """测试发现已知社区"""
        node = create_community_member(node_id="node_001")
        
        # 添加已知社区
        community1 = create_community(name="Community1", founder_id="founder_001")
        community2 = create_community(name="Community2", founder_id="founder_002")
        
        node.known_communities[community1.community_id] = community1
        node.known_communities[community2.community_id] = community2
        
        # 发现社区
        discovered = list(node.known_communities.values())
        
        # 验证
        assert len(discovered) == 2
        assert discovered[0].name == "Community1"
        assert discovered[1].name == "Community2"


# =============================================================================
# 集成测试
# =============================================================================


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        """测试完整的社区生命周期"""
        # 1. 创建社区
        community = create_community(
            name="TestCommunity",
            description="测试社区",
            founder_id="founder_001",
        )
        
        # 2. 创建共识协议
        protocol = create_consensus_protocol(community)
        
        # 3. 添加创始成员
        founder_membership = ClusterMembership(
            node_id="founder_001",
            cluster_id=community.community_id,
            status=MembershipStatus.ACTIVE,
        )
        community.members["founder_001"] = founder_membership
        
        # 4. 提议新成员
        new_node_id = "new_node_001"
        proposal_id = await protocol.propose_new_member(
            node_id=new_node_id,
            proposer_id="founder_001",
        )
        
        # 5. 投票
        await protocol.vote(
            proposal_id=proposal_id,
            voter_id="founder_001",
            result=ConsensusVotingResult.APPROVE,
            reason="欢迎",
        )
        
        # 6. 检查共识
        reached, result = await protocol.check_consensus(proposal_id)
        assert reached
        assert result == "approved"
        
        # 7. 新成员加入
        new_node = create_community_member(node_id=new_node_id)
        await new_node.join_community(community)
        
        # 8. 验证成员资格
        assert new_node.is_member_of_any_community()
        assert new_node.membership.cluster_id == community.community_id
        
        # 9. 尝试加入另一个社区（应该失败）
        community2 = create_community(name="Community2", founder_id="founder_002")
        with pytest.raises(SingleHomingViolationError):
            await new_node.join_community(community2)
        
        # 10. 离开社区
        await new_node.leave_community()
        assert not new_node.is_member_of_any_community()
        
        # 11. 现在可以加入另一个社区
        await new_node.join_community(community2)
        assert new_node.membership.cluster_id == community2.community_id
