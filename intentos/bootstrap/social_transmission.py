"""
IntentOS 社会传播模块

实现系统在人类社会中的病毒式传播、社区自组织、价值网络效应
"""

from __future__ import annotations
import logging

import asyncio
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class TransmissionType(Enum):
    """传播类型"""
    VIRAL = "viral"              # 病毒式传播
    COMMUNITY = "community"      # 社区自组织
    MARKETPLACE = "marketplace"  # 市场交易
    EDUCATION = "education"      # 教育传播
    ENTERPRISE = "enterprise"    # 企业采用


class AdoptionStage(Enum):
    """采用阶段"""
    UNAWARE = "unaware"          # 不知道
    AWARE = "aware"              # 知道
    INTERESTED = "interested"    # 感兴趣
    TRIAL = "trial"              # 试用
    ADOPTER = "adopter"          # 采用者
    ADVOCATE = "advocate"        # 倡导者


@dataclass
class TransmissionNode:
    """传播节点（个人/组织）"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: str = "individual"  # individual / organization
    stage: AdoptionStage = AdoptionStage.UNAWARE
    location: str = ""
    influence_score: float = 0.0  # 影响力分数 0-100
    connections: list[str] = field(default_factory=list)
    adopted_at: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TransmissionEvent:
    """传播事件"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: TransmissionType = TransmissionType.VIRAL
    source_node: str = ""
    target_nodes: list[str] = field(default_factory=list)
    message: str = ""
    channel: str = ""  # github / twitter / blog / conference 等
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    conversion_rate: float = 0.0  # 转化率
    reach: int = 0  # 触达人数
    engagements: int = 0  # 互动数


@dataclass
class Community:
    """社区"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    platform: str = ""  # discord / slack / github 等
    members: list[str] = field(default_factory=list)
    activity_level: float = 0.0  # 活跃度 0-100
    growth_rate: float = 0.0  # 增长率
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ValueNetwork:
    """价值网络"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    participants: list[str] = field(default_factory=list)
    value_flows: list[dict[str, Any]] = field(default_factory=list)
    total_value: float = 0.0  # 总价值
    network_effect: float = 1.0  # 网络效应系数


class SocialTransmission:
    """
    社会传播管理器

    实现 IntentOS 在人类社会中的传播
    """

    def __init__(self):
        self.nodes: dict[str, TransmissionNode] = {}
        self.events: list[TransmissionEvent] = []
        self.communities: dict[str, Community] = {}
        self.value_networks: list[ValueNetwork] = []
        self._load_state()

    def _load_state(self) -> None:
        """加载状态"""
        state_file = '/tmp/intentos_transmission_state.json'
        if os.path.exists(state_file):
            with open(state_file) as f:
                state = json.load(f)
                # 恢复状态...

    def _save_state(self) -> None:
        """保存状态"""
        state_file = '/tmp/intentos_transmission_state.json'
        state = {
            'nodes': {k: vars(v) for k, v in self.nodes.items()},
            'events': [vars(e) for e in self.events],
            'communities': {k: vars(c) for k, c in self.communities.items()},
        }
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

    # ========== 病毒式传播 ==========

    async def start_viral_campaign(self, campaign_config: dict[str, Any]) -> TransmissionEvent:
        """
        启动病毒式传播活动

        Args:
            campaign_config: 活动配置
                - message: 传播信息
                - channels: 传播渠道
                - target_audience: 目标受众
                - incentives: 激励措施

        Returns:
            TransmissionEvent: 传播事件
        """
        print("\n🚀 启动病毒式传播活动...")
        print(f"  信息：{campaign_config.get('message', '')[:50]}...")
        print(f"  渠道：{campaign_config.get('channels', [])}")

        event = TransmissionEvent(
            type=TransmissionType.VIRAL,
            message=campaign_config.get('message', ''),
            channel=','.join(campaign_config.get('channels', [])),
        )

        # 识别种子用户
        seed_users = await self._identify_seed_users(
            campaign_config.get('target_audience', {})
        )
        event.target_nodes = seed_users
        event.source_node = "intentos_official"

        # 执行传播
        await self._execute_viral_transmission(event, campaign_config)

        self.events.append(event)
        self._save_state()

        return event

    async def _identify_seed_users(self, target_audience: dict) -> list[str]:
        """识别种子用户"""
        # 根据目标受众特征识别高影响力用户
        seed_users = []

        # 示例：GitHub 上的开源贡献者
        if target_audience.get('platform') == 'github':
            seed_users = await self._find_github_influencers(
                target_audience.get('keywords', ['ai', 'llm', 'os'])
            )

        # 示例：Twitter 上的技术意见领袖
        elif target_audience.get('platform') == 'twitter':
            seed_users = await self._find_twitter_influencers(
                target_audience.get('topics', ['AI', 'OpenSource'])
            )

        return seed_users

    async def _find_github_influencers(self, keywords: list[str]) -> list[str]:
        """查找 GitHub 影响者"""
        # 实际实现会调用 GitHub API
        # 这里返回示例
        return [
            "github_user_1",
            "github_user_2",
            "github_user_3",
        ]

    async def _find_twitter_influencers(self, topics: list[str]) -> list[str]:
        """查找 Twitter 影响者"""
        # 实际实现会调用 Twitter API
        return [
            "twitter_user_1",
            "twitter_user_2",
        ]

    async def _execute_viral_transmission(
        self,
        event: TransmissionEvent,
        config: dict[str, Any]
    ) -> None:
        """执行病毒式传播"""
        print("  执行传播...")

        # 1. 发布内容
        for channel in config.get('channels', []):
            await self._publish_to_channel(channel, event.message, config)

        # 2. 激励分享
        if config.get('incentives'):
            await self._distribute_incentives(config['incentives'])

        # 3. 追踪转化
        event.reach = await self._track_reach(event)
        event.engagements = await self._track_engagements(event)
        event.conversion_rate = await self._calculate_conversion(event)

        print(f"  ✓ 触达：{event.reach} 人")
        print(f"  ✓ 互动：{event.engagements} 次")
        print(f"  ✓ 转化率：{event.conversion_rate:.2%}")

    async def _publish_to_channel(
        self,
        channel: str,
        message: str,
        config: dict
    ) -> None:
        """发布到渠道"""
        if channel == 'github':
            # 创建 GitHub Release、Issue、PR
            print(f"    → GitHub: 发布 {message[:30]}...")
        elif channel == 'twitter':
            # 发布 Twitter 线程
            print(f"    → Twitter: 发布 {message[:30]}...")
        elif channel == 'reddit':
            # 发布 Reddit 帖子
            print(f"    → Reddit: 发布 {message[:30]}...")
        elif channel == 'product_hunt':
            # 发布 Product Hunt
            print(f"    → Product Hunt: 发布 {message[:30]}...")

    async def _distribute_incentives(self, incentives: dict) -> None:
        """分发激励"""
        # NFT 奖励
        if incentives.get('nft'):
            print("    → 分发 NFT 奖励...")

        # Token 奖励
        if incentives.get('token'):
            print("    → 分发 Token 奖励...")

        # 荣誉奖励
        if incentives.get('badge'):
            print("    → 颁发荣誉徽章...")

    async def _track_reach(self, event: TransmissionEvent) -> int:
        """追踪触达人数"""
        # 实际实现会分析各渠道数据
        return 10000  # 示例

    async def _track_engagements(self, event: TransmissionEvent) -> int:
        """追踪互动数"""
        return 500  # 示例

    async def _calculate_conversion(self, event: TransmissionEvent) -> float:
        """计算转化率"""
        return 0.05  # 5% 示例

    # ========== 社区自组织 ==========

    async def create_community(
        self,
        name: str,
        description: str,
        platform: str = "discord"
    ) -> Community:
        """
        创建社区

        Args:
            name: 社区名称
            description: 社区描述
            platform: 平台

        Returns:
            Community: 社区对象
        """
        print(f"\n🏘️ 创建社区：{name}")
        print(f"  平台：{platform}")

        community = Community(
            name=name,
            description=description,
            platform=platform,
        )

        # 在平台上创建实际社区
        await self._setup_community_platform(community)

        # 邀请初始成员
        founding_members = await self._find_founding_members()
        community.members = founding_members

        self.communities[community.id] = community
        self._save_state()

        print("  ✓ 社区已创建")
        print(f"  ✓ 初始成员：{len(founding_members)} 人")

        return community

    async def _setup_community_platform(self, community: Community) -> None:
        """设置社区平台"""
        if community.platform == 'discord':
            # 创建 Discord 服务器
            print("    → 创建 Discord 服务器...")
        elif community.platform == 'slack':
            # 创建 Slack 工作区
            print("    → 创建 Slack 工作区...")
        elif community.platform == 'github':
            # 创建 GitHub Organization
            print("    → 创建 GitHub Organization...")

    async def _find_founding_members(self) -> list[str]:
        """寻找创始成员"""
        # 从早期采用者中邀请
        return [
            node.id for node in self.nodes.values()
            if node.stage == AdoptionStage.ADVOCATE
        ][:10]  # 前 10 个倡导者

    async def nurture_community(self, community_id: str) -> None:
        """培育社区"""
        community = self.communities.get(community_id)
        if not community:
            return

        print(f"\n🌱 培育社区：{community.name}")

        # 1. 组织活动
        await self._organize_community_events(community)

        # 2. 提供资源
        await self._provide_community_resources(community)

        # 3. 培养领导者
        await self._cultivate_community_leaders(community)

        # 4. 激励贡献
        await self._incentivize_contributions(community)

    async def _organize_community_events(self, community: Community) -> None:
        """组织社区活动"""
        events = [
            "AMA (Ask Me Anything)",
            "Hackathon",
            "Workshop",
            "Meetup",
        ]
        print(f"    → 组织活动：{events}")

    async def _provide_community_resources(self, community: Community) -> None:
        """提供社区资源"""
        resources = [
            "文档",
            "教程",
            "示例代码",
            "开发工具",
        ]
        print(f"    → 提供资源：{resources}")

    async def _cultivate_community_leaders(self, community: Community) -> None:
        """培养社区领导者"""
        print("    → 培养社区领导者...")

    async def _incentivize_contributions(self, community: Community) -> None:
        """激励贡献"""
        incentives = [
            "贡献者排名",
            "月度最佳",
            "NFT 徽章",
            "Token 奖励",
        ]
        print(f"    → 激励措施：{incentives}")

    # ========== 价值网络 ==========

    async def create_value_network(self, name: str) -> ValueNetwork:
        """
        创建价值网络

        Args:
            name: 网络名称

        Returns:
            ValueNetwork: 价值网络
        """
        print(f"\n🕸️ 创建价值网络：{name}")

        network = ValueNetwork(name=name)

        # 邀请参与者
        participants = await self._invite_network_participants()
        network.participants = participants

        # 定义价值流
        network.value_flows = await self._define_value_flows()

        # 计算网络效应
        network.network_effect = len(participants) ** 2  # 梅特卡夫定律
        network.total_value = network.network_effect * 100  # 示例计算

        self.value_networks.append(network)

        print(f"  ✓ 参与者：{len(participants)} 个")
        print(f"  ✓ 网络效应：{network.network_effect:.0f}x")
        print(f"  ✓ 总价值：${network.total_value:,.0f}")

        return network

    async def _invite_network_participants(self) -> list[str]:
        """邀请网络参与者"""
        # 邀请互补的参与者
        return [
            "开发者",
            "用户",
            "投资者",
            "合作伙伴",
            "布道师",
        ]

    async def _define_value_flows(self) -> list[dict[str, Any]]:
        """定义价值流"""
        return [
            {
                'from': '开发者',
                'to': '用户',
                'value': '应用/插件',
            },
            {
                'from': '用户',
                'to': '开发者',
                'value': '反馈/收入',
            },
            {
                'from': '投资者',
                'to': '生态',
                'value': '资金',
            },
            {
                'from': '生态',
                'to': '投资者',
                'value': '回报',
            },
        ]

    # ========== 教育传播 ==========

    async def create_education_program(self, program_config: dict) -> None:
        """
        创建教育项目

        Args:
            program_config: 项目配置
        """
        print("\n📚 创建教育项目...")

        # 大学合作
        if program_config.get('university'):
            await self._partner_with_universities(program_config)

        # 在线课程
        if program_config.get('online_course'):
            await self._create_online_courses(program_config)

        # 认证体系
        if program_config.get('certification'):
            await self._setup_certification(program_config)

    async def _partner_with_universities(self, config: dict) -> None:
        """与大学合作"""
        print("    → 与大学合作...")
        print("       提供课程材料")
        print("       举办讲座")
        print("       实习机会")

    async def _create_online_courses(self, config: dict) -> None:
        """创建在线课程"""
        print("    → 创建在线课程...")
        print("       Coursera / edX / Udemy")
        print("       YouTube 教程")
        print("       交互式学习平台")

    async def _setup_certification(self, config: dict) -> None:
        """建立认证体系"""
        print("    → 建立认证体系...")
        print("       IntentOS 认证开发者")
        print("       IntentOS 认证架构师")
        print("       IntentOS 认证布道师")

    # ========== 企业采用 ==========

    async def enterprise_adoption_program(self) -> None:
        """企业采用计划"""
        print("\n🏢 企业采用计划...")

        # 1. 企业版功能
        await self._develop_enterprise_features()

        # 2. 销售支持
        await self._setup_sales_support()

        # 3. 客户成功
        await self._ensure_customer_success()

        # 4. 案例研究
        await self._create_case_studies()

    async def _develop_enterprise_features(self) -> None:
        """开发企业功能"""
        features = [
            "SSO 单点登录",
            "权限管理",
            "审计日志",
            "SLA 保障",
            "私有部署",
        ]
        print(f"    → 企业功能：{features}")

    async def _setup_sales_support(self) -> None:
        """建立销售支持"""
        print("    → 销售支持...")
        print("       销售团队培训")
        print("       销售材料准备")
        print("       PO C 流程")

    async def _ensure_customer_success(self) -> None:
        """确保客户成功"""
        print("    → 客户成功...")
        print("       客户成功经理")
        print("       技术支持团队")
        print("       最佳实践分享")

    async def _create_case_studies(self) -> None:
        """创建案例研究"""
        print("    → 案例研究...")
        print("       成功客户故事")
        print("       ROI 分析")
        print("       行业解决方案")

    # ========== 传播分析 ==========

    def get_transmission_metrics(self) -> dict[str, Any]:
        """获取传播指标"""
        total_nodes = len(self.nodes)
        adopters = sum(1 for n in self.nodes.values() if n.stage == AdoptionStage.ADOPTER)
        advocates = sum(1 for n in self.nodes.values() if n.stage == AdoptionStage.ADVOCATE)

        total_events = len(self.events)
        avg_conversion = (
            sum(e.conversion_rate for e in self.events) / total_events
            if total_events else 0
        )

        return {
            'total_reach': total_nodes,
            'adopters': adopters,
            'advocates': advocates,
            'adoption_rate': adopters / total_nodes if total_nodes else 0,
            'total_events': total_events,
            'avg_conversion_rate': avg_conversion,
            'communities': len(self.communities),
            'value_networks': len(self.value_networks),
        }

    def plot_transmission_curve(self) -> None:
        """绘制传播曲线"""
        # 实际实现会使用 matplotlib 绘制
        print("\n📊 传播曲线:")
        print("  创新者 (2.5%) → 早期采用者 (13.5%) → 早期大众 (34%) → 晚期大众 (34%) → 落后者 (16%)")

    async def optimize_transmission(self) -> dict[str, Any]:
        """优化传播策略"""
        print("\n🔍 分析传播效果...")

        metrics = self.get_transmission_metrics()
        recommendations = []

        # 分析瓶颈
        if metrics['adoption_rate'] < 0.1:
            recommendations.append({
                'issue': '采用率低',
                'action': '增加激励措施、降低使用门槛',
                'expected_impact': '+20% 采用率',
            })

        if metrics['avg_conversion_rate'] < 0.03:
            recommendations.append({
                'issue': '转化率低',
                'action': '优化 onboarding 流程、改进文档',
                'expected_impact': '+50% 转化率',
            })

        if metrics['advocates'] < metrics['adopters'] * 0.1:
            recommendations.append({
                'issue': '倡导者少',
                'action': '建立布道师计划、增加激励',
                'expected_impact': '+30% 病毒系数',
            })

        print("  建议:")
        for rec in recommendations:
            print(f"    - {rec['issue']}: {rec['action']}")
            print(f"      预期影响：{rec['expected_impact']}")

        return {
            'metrics': metrics,
            'recommendations': recommendations,
        }


async def main():
    """演示社会传播"""
    import argparse

    parser = argparse.ArgumentParser(description='IntentOS 社会传播')
    parser.add_argument('--action', choices=[
        'viral', 'community', 'network', 'education', 'enterprise', 'analyze'
    ], default='analyze')

    args = parser.parse_args()

    transmission = SocialTransmission()

    if args.action == 'viral':
        event = await transmission.start_viral_campaign({
            'message': 'IntentOS: AI 原生操作系统，自我繁殖的数字生命体！',
            'channels': ['github', 'twitter', 'reddit', 'product_hunt'],
            'target_audience': {
                'platform': 'github',
                'keywords': ['ai', 'llm', 'os', 'agent'],
            },
            'incentives': {
                'nft': True,
                'token': True,
                'badge': True,
            },
        })
        print(f"\n活动 ID: {event.id}")
        print(f"触达：{event.reach} 人")

    elif args.action == 'community':
        community = await transmission.create_community(
            name="IntentOS 开发者社区",
            description="AI 原生操作系统的开发者家园",
            platform="discord",
        )
        await transmission.nurture_community(community.id)

    elif args.action == 'network':
        network = await transmission.create_value_network(
            name="IntentOS 生态网络"
        )
        print(f"\n网络价值：${network.total_value:,.0f}")

    elif args.action == 'education':
        await transmission.create_education_program({
            'university': True,
            'online_course': True,
            'certification': True,
        })

    elif args.action == 'enterprise':
        await transmission.enterprise_adoption_program()

    elif args.action == 'analyze':
        metrics = transmission.get_transmission_metrics()
        print("\n📊 传播指标:")
        for k, v in metrics.items():
            print(f"  {k}: {v}")

        await transmission.optimize_transmission()


if __name__ == '__main__':
    asyncio.run(main())
