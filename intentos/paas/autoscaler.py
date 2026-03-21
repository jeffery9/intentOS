"""
PaaS Auto-Scaler

负责根据集群负载和平台收益自动伸缩 Runtime Agent 节点。
"""

from __future__ import annotations

import asyncio
import logging

from ..distributed.vm import DistributedSemanticVM
from .reward_system import RewardSystem
from .tenant import TenantManager

logger = logging.getLogger(__name__)

class PaaSAutoScaler:
    """
    PaaS 自动扩容引擎

    第一性原理：扩容应由“需求(Gas 压力)”和“能力(平台资金)”共同驱动。
    """

    def __init__(
        self,
        cluster: DistributedSemanticVM,
        tenant_manager: TenantManager,
        reward_system: RewardSystem,
        node_cost: float = 10.0 # 启动一个新节点的虚拟成本
    ):
        self.cluster = cluster
        self.tenant_manager = tenant_manager
        self.reward_system = reward_system
        self.node_cost = node_cost

        self.is_running = False
        self.check_interval = 60 # 每分钟检查一次

    async def start(self):
        self.is_running = True
        logger.info("PaaS Auto-Scaler started")
        asyncio.create_task(self._monitoring_loop())

    async def _monitoring_loop(self):
        while self.is_running:
            try:
                await self.evaluate_and_scale()
            except Exception as e:
                logger.error(f"Auto-scaling evaluation failed: {e}")
            await asyncio.sleep(self.check_interval)

    async def evaluate_and_scale(self):
        """评估集群状态并决定是否扩容"""
        # 1. 收集集群负载指标
        active_nodes = self.cluster.memory.get_active_nodes()
        avg_load = sum(n.load for n in active_nodes) / len(active_nodes) if active_nodes else 1.0

        # 2. 检查平台经济状况
        reserve = self.reward_system.get_platform_reserve()

        # 3. 扩容策略：
        # 如果平均负载超过 70%，且平台储备金足以支付新节点成本
        if avg_load > 0.7 and reserve >= self.node_cost:
            logger.info(f"Scaling UP: Load={avg_load:.2f}, Reserve={reserve:.2f}")
            await self._provision_new_node()
            # 扣除扩容成本
            self.reward_system.spend_credits("platform_reserve", self.node_cost)

        # 4. 缩容策略：
        # 如果平均负载低于 20%，且节点数大于 1
        elif avg_load < 0.2 and len(active_nodes) > 1:
            logger.info(f"Scaling DOWN: Load={avg_load:.2f}")
            await self._decommission_idle_node()

    async def _provision_new_node(self):
        """
        物理拨备新节点
        在实际生产环境中，这里会调用 AWS/Kubernetes API
        """
        # 模拟启动 Runtime Agent
        new_port = 8000 + len(self.cluster.memory.nodes)
        logger.info(f"🚀 Provisioning new node on port {new_port}...")

        # 在原型中，我们可以通过 subprocess 或内置逻辑增加逻辑节点
        from ..distributed.vm import VMNode
        node = VMNode(host="localhost", port=new_port, status="loading")
        self.cluster.memory.add_node(node)

        # 模拟启动延迟
        await asyncio.sleep(2)
        node.status = "active"
        logger.info(f"✅ New node {node.node_id} is now active")

    async def _decommission_idle_node(self):
        """回收最闲置的节点"""
        active_nodes = self.cluster.memory.get_active_nodes()
        if len(active_nodes) <= 1:
            return

        idle_node = min(active_nodes, key=lambda n: n.load)
        logger.info(f"🛑 Decommissioning idle node {idle_node.node_id}")
        self.cluster.memory.remove_node(idle_node.node_id)
