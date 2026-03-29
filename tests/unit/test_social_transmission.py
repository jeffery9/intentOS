"""
Social Transmission Module Tests

测试社会传播模块：传播节点、传播事件、社区管理
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from intentos.bootstrap.social_transmission import (
    TransmissionType,
    AdoptionStage,
    TransmissionNode,
    TransmissionEvent,
    Community,
)


class TestTransmissionType:
    """测试传播类型枚举"""

    def test_viral_type(self):
        """病毒式传播"""
        assert TransmissionType.VIRAL.value == "viral"

    def test_community_type(self):
        """社区自组织"""
        assert TransmissionType.COMMUNITY.value == "community"

    def test_marketplace_type(self):
        """市场交易"""
        assert TransmissionType.MARKETPLACE.value == "marketplace"

    def test_education_type(self):
        """教育传播"""
        assert TransmissionType.EDUCATION.value == "education"

    def test_enterprise_type(self):
        """企业采用"""
        assert TransmissionType.ENTERPRISE.value == "enterprise"


class TestAdoptionStage:
    """测试采用阶段枚举"""

    def test_unaware_stage(self):
        """不知道阶段"""
        assert AdoptionStage.UNAWARE.value == "unaware"

    def test_aware_stage(self):
        """知道阶段"""
        assert AdoptionStage.AWARE.value == "aware"

    def test_interested_stage(self):
        """感兴趣阶段"""
        assert AdoptionStage.INTERESTED.value == "interested"

    def test_trial_stage(self):
        """试用阶段"""
        assert AdoptionStage.TRIAL.value == "trial"

    def test_adopter_stage(self):
        """采用者阶段"""
        assert AdoptionStage.ADOPTER.value == "adopter"

    def test_advocate_stage(self):
        """倡导者阶段"""
        assert AdoptionStage.ADVOCATE.value == "advocate"


class TestTransmissionNode:
    """测试传播节点"""

    def test_create_node_minimal(self):
        """创建最小节点"""
        node = TransmissionNode()

        assert node.id is not None
        assert node.name == ""
        assert node.type == "individual"
        assert node.stage == AdoptionStage.UNAWARE
        assert node.influence_score == 0.0
        assert node.connections == []

    def test_create_node_individual(self):
        """创建个人节点"""
        node = TransmissionNode(
            name="John Doe",
            type="individual",
            stage=AdoptionStage.INTERESTED,
            location="San Francisco",
            influence_score=75.0
        )

        assert node.name == "John Doe"
        assert node.type == "individual"
        assert node.stage == AdoptionStage.INTERESTED
        assert node.location == "San Francisco"
        assert node.influence_score == 75.0

    def test_create_node_organization(self):
        """创建组织节点"""
        node = TransmissionNode(
            name="Tech Corp",
            type="organization",
            stage=AdoptionStage.ADOPTER,
            location="New York",
            influence_score=95.0,
            metadata={"industry": "Technology", "size": "1000+"}
        )

        assert node.name == "Tech Corp"
        assert node.type == "organization"
        assert node.stage == AdoptionStage.ADOPTER
        assert node.metadata["industry"] == "Technology"

    def test_node_connections(self):
        """节点连接"""
        node = TransmissionNode(
            name="Connector",
            connections=["node1", "node2", "node3"]
        )

        assert len(node.connections) == 3
        assert "node1" in node.connections
        assert "node2" in node.connections
        assert "node3" in node.connections

    def test_node_adopted_at(self):
        """节点采用时间"""
        node = TransmissionNode(
            name="Adopter",
            stage=AdoptionStage.ADOPTER,
            adopted_at="2024-01-15T10:00:00"
        )

        assert node.adopted_at == "2024-01-15T10:00:00"
        assert node.stage == AdoptionStage.ADOPTER


class TestTransmissionEvent:
    """测试传播事件"""

    def test_create_event_minimal(self):
        """创建最小事件"""
        event = TransmissionEvent()

        assert event.id is not None
        assert event.type == TransmissionType.VIRAL
        assert event.source_node == ""
        assert event.target_nodes == []
        assert event.created_at is not None

    def test_create_event_viral(self):
        """创建病毒式传播事件"""
        event = TransmissionEvent(
            type=TransmissionType.VIRAL,
            source_node="influencer1",
            target_nodes=["user1", "user2", "user3"],
            message="Check out IntentOS!",
            channel="twitter",
            reach=10000,
            engagements=500,
            conversion_rate=0.05
        )

        assert event.type == TransmissionType.VIRAL
        assert event.source_node == "influencer1"
        assert len(event.target_nodes) == 3
        assert event.channel == "twitter"
        assert event.reach == 10000
        assert event.engagements == 500

    def test_create_event_community(self):
        """创建社区事件"""
        event = TransmissionEvent(
            type=TransmissionType.COMMUNITY,
            source_node="community_leader",
            target_nodes=["community_members"],
            channel="discord",
            message="IntentOS community meetup"
        )

        assert event.type == TransmissionType.COMMUNITY
        assert event.channel == "discord"

    def test_create_event_enterprise(self):
        """创建企业事件"""
        event = TransmissionEvent(
            type=TransmissionType.ENTERPRISE,
            source_node="sales_team",
            target_nodes=["enterprise_client"],
            channel="conference",
            message="Enterprise solution presentation"
        )

        assert event.type == TransmissionType.ENTERPRISE
        assert event.channel == "conference"


class TestCommunity:
    """测试社区"""

    def test_create_community_minimal(self):
        """创建最小社区"""
        community = Community()

        assert community.id is not None
        assert community.name == ""
        assert community.description == ""
        assert community.platform == ""
        assert community.members == []
        assert community.activity_level == 0.0
        assert community.growth_rate == 0.0

    def test_create_community_discord(self):
        """创建 Discord 社区"""
        community = Community(
            name="IntentOS Users",
            description="IntentOS user community",
            platform="discord",
            members=["user1", "user2", "user3"],
            activity_level=85.0,
            growth_rate=15.0
        )

        assert community.name == "IntentOS Users"
        assert community.platform == "discord"
        assert len(community.members) == 3
        assert community.activity_level == 85.0
        assert community.growth_rate == 15.0

    def test_create_community_github(self):
        """创建 GitHub 社区"""
        community = Community(
            name="IntentOS Contributors",
            description="IntentOS open source contributors",
            platform="github",
            members=["contributor1", "contributor2"],
            activity_level=95.0,
            growth_rate=25.0
        )

        assert community.name == "IntentOS Contributors"
        assert community.platform == "github"
        assert community.activity_level == 95.0


class TestAdoptionStageProgression:
    """测试采用阶段进展"""

    def test_stage_progression_unaware_to_aware(self):
        """阶段进展：不知道 -> 知道"""
        node = TransmissionNode(stage=AdoptionStage.UNAWARE)
        assert node.stage == AdoptionStage.UNAWARE

        node.stage = AdoptionStage.AWARE
        assert node.stage == AdoptionStage.AWARE

    def test_stage_progression_to_adopter(self):
        """阶段进展：到采用者"""
        node = TransmissionNode(
            stage=AdoptionStage.INTERESTED,
            name="Progressive User"
        )

        # 试用
        node.stage = AdoptionStage.TRIAL
        assert node.stage == AdoptionStage.TRIAL

        # 采用
        node.stage = AdoptionStage.ADOPTER
        assert node.stage == AdoptionStage.ADOPTER

    def test_stage_progression_to_advocate(self):
        """阶段进展：到倡导者"""
        node = TransmissionNode(
            stage=AdoptionStage.ADOPTER,
            name="Loyal User"
        )

        # 成为倡导者
        node.stage = AdoptionStage.ADVOCATE
        assert node.stage == AdoptionStage.ADVOCATE


class TestInfluenceScore:
    """测试影响力分数"""

    def test_influence_score_range(self):
        """影响力分数范围"""
        node_low = TransmissionNode(influence_score=0.0)
        node_high = TransmissionNode(influence_score=100.0)

        assert node_low.influence_score == 0.0
        assert node_high.influence_score == 100.0

    def test_influence_score_intermediate(self):
        """中间影响力分数"""
        node = TransmissionNode(influence_score=50.0)
        assert node.influence_score == 50.0

    def test_influence_score_decimal(self):
        """小数影响力分数"""
        node = TransmissionNode(influence_score=75.5)
        assert node.influence_score == 75.5


class TestTransmissionMetrics:
    """测试传播指标"""

    def test_event_conversion_rate(self):
        """事件转化率"""
        event = TransmissionEvent(
            reach=1000,
            engagements=100,
            conversion_rate=0.1
        )

        assert event.reach == 1000
        assert event.engagements == 100
        assert event.conversion_rate == 0.1

    def test_event_engagement_rate(self):
        """事件互动率"""
        event = TransmissionEvent(
            reach=10000,
            engagements=500
        )

        engagement_rate = event.engagements / event.reach
        assert engagement_rate == 0.05

    def test_community_growth(self):
        """社区增长"""
        community = Community(
            members=["m1", "m2", "m3"],
            growth_rate=20.0
        )

        # 计算预期增长
        expected_new_members = len(community.members) * (community.growth_rate / 100)
        assert abs(expected_new_members - 0.6) < 0.001


class TestNetworkEffects:
    """测试网络效应"""

    def test_node_network_size(self):
        """节点网络规模"""
        node = TransmissionNode(
            connections=["c1", "c2", "c3", "c4", "c5"]
        )

        network_size = len(node.connections)
        assert network_size == 5

    def test_community_network_size(self):
        """社区网络规模"""
        community = Community(
            members=["m1"] * 100  # 100 个成员
        )

        assert len(community.members) == 100
