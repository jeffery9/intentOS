#!/usr/bin/env python3
"""
测试选举式 PaaS

验证：
1. PaaSNodeElector 选举逻辑
2. DistributedPaaS 激活/休眠
3. 节点选举/罢免流程
4. PaaS 请求转发
"""

import pytest
from intentos.runtime.agent import PaaSNodeElector, DistributedPaaS
from intentos.paas.marketplace import AppMarketplace


class TestPaaSNodeElector:
    """测试 PaaS 节点选举器"""

    def test_init_not_elected(self):
        """初始化时默认为普通节点"""
        elector = PaaSNodeElector("node_001")
        assert elector.is_elected is False
        assert len(elector.paas_nodes) == 0
        assert elector.primary_paas_node is None

    def test_init_elected(self):
        """初始化时被选举为 PaaS 节点"""
        elector = PaaSNodeElector("node_001", is_elected=True)
        assert elector.is_elected is True
        assert "node_001" in elector.paas_nodes
        assert elector.primary_paas_node == "node_001"

    def test_elect_as_paas(self):
        """选举节点成为 PaaS 层"""
        elector = PaaSNodeElector("node_001")
        
        # 选举其他节点
        elector.elect_as_paas("node_002")
        assert "node_002" in elector.paas_nodes
        assert elector.is_elected is False
        assert elector.primary_paas_node == "node_002"
        
        # 选举本节点
        elector.elect_as_paas("node_001")
        assert "node_001" in elector.paas_nodes
        assert elector.is_elected is True

    def test_remove_from_paas(self):
        """罢免 PaaS 节点"""
        elector = PaaSNodeElector("node_001", is_elected=True)
        elector.elect_as_paas("node_002")
        
        # 罢免其他节点
        elector.remove_from_paas("node_002")
        assert "node_002" not in elector.paas_nodes
        assert elector.is_elected is True
        
        # 罢免本节点
        elector.remove_from_paas("node_001")
        assert "node_001" not in elector.paas_nodes
        assert elector.is_elected is False
        assert elector.primary_paas_node is None

    def test_get_paas_nodes(self):
        """获取 PaaS 节点列表"""
        elector = PaaSNodeElector("node_001", is_elected=True)
        elector.elect_as_paas("node_002")
        elector.elect_as_paas("node_003")
        
        nodes = elector.get_paas_nodes()
        assert len(nodes) == 3
        assert set(nodes) == {"node_001", "node_002", "node_003"}

    def test_is_paas_node(self):
        """判断节点是否为 PaaS 节点"""
        elector = PaaSNodeElector("node_001", is_elected=True)
        
        assert elector.is_paas_node("node_001") is True
        assert elector.is_paas_node("node_002") is False
        
        elector.elect_as_paas("node_002")
        assert elector.is_paas_node("node_002") is True

    def test_should_forward_paas_request(self):
        """判断是否应该转发 PaaS 请求"""
        # 没有 PaaS 节点
        elector = PaaSNodeElector("node_001")
        assert elector.should_forward_paas_request() is False
        
        # 本节点是 PaaS 节点
        elector.elect_as_paas("node_001")
        assert elector.should_forward_paas_request() is False
        
        # 本节点不是 PaaS 节点
        elector2 = PaaSNodeElector("node_002")
        elector2.elect_as_paas("node_001")
        assert elector2.should_forward_paas_request() is True
        
        # 指定目标节点
        assert elector2.should_forward_paas_request("node_001") is False
        assert elector2.should_forward_paas_request("node_003") is True

    def test_elect_primary(self):
        """选举主 PaaS 节点"""
        elector = PaaSNodeElector("node_001")
        elector.elect_as_paas("node_002")
        elector.elect_as_paas("node_003")
        
        import asyncio
        primary = asyncio.run(elector.elect_primary())
        # 主节点应该是 PaaS 节点之一（set 无序，不指定具体哪个）
        assert primary in ["node_002", "node_003"]


class TestDistributedPaaS:
    """测试分布式 PaaS"""

    def test_init_not_active(self):
        """初始化时 PaaS 未激活"""
        paas = DistributedPaaS("node_001")
        assert paas.is_active is False

    def test_activate(self):
        """激活 PaaS 服务"""
        paas = DistributedPaaS("node_001")
        paas.activate()
        assert paas.is_active is True
        
        # 验证服务已初始化
        assert paas._tenant_manager is not None
        assert paas._role_manager is not None
        assert paas._metering_service is not None
        assert paas._payment_gateway is not None
        assert paas._marketplace is not None

    def test_deactivate(self):
        """休眠 PaaS 服务"""
        paas = DistributedPaaS("node_001")
        paas.activate()
        assert paas.is_active is True
        
        paas.deactivate()
        assert paas.is_active is False
        
        # 验证服务已释放
        assert paas._tenant_manager is None
        assert paas._role_manager is None

    def test_ensure_active(self):
        """确保 PaaS 已激活"""
        paas = DistributedPaaS("node_001")
        
        # 未激活时访问服务应抛出异常
        with pytest.raises(RuntimeError, match="PaaS 服务未激活"):
            _ = paas.tenant_manager
        
        paas.activate()
        
        # 激活后可以访问
        assert paas.tenant_manager is not None

    def test_get_tenant_context(self):
        """获取租户上下文"""
        paas = DistributedPaaS("node_001")
        paas.activate()
        
        # 创建租户
        tenant = paas.tenant_manager.create_tenant("tenant_001", "测试租户")
        
        # 获取上下文
        ctx = paas.get_tenant_context("tenant_001", "user_123")
        assert ctx["tenant"]["id"] == "tenant_001"
        assert ctx["user"]["user_id"] == "user_123"
        assert "quota_remaining" in ctx

    def test_record_usage(self):
        """记录用量"""
        from intentos.paas.tenant import reset_tenant_services
        from intentos.paas.metering import reset_metering_service
        
        # 重置全局服务（避免测试间干扰）
        reset_tenant_services()
        reset_metering_service()
        
        paas = DistributedPaaS("node_002")  # 使用不同节点避免冲突
        paas.activate()
        
        # 创建租户
        paas.tenant_manager.create_tenant("tenant_002", "测试租户")
        
        # 记录用量
        import asyncio
        asyncio.run(paas.record_usage("tenant_002", "user_123", {
            "tokens": 100,
            "cpu_ms": 50,
            "gas": 1000,
        }))
        
        # 验证用量已记录
        tenant = paas.tenant_manager.get_tenant("tenant_002")
        assert tenant.cumulative_gas_used == 1000

    def test_get_usage_report(self):
        """获取用量报告"""
        from intentos.paas.tenant import reset_tenant_services
        from intentos.paas.metering import reset_metering_service
        
        # 重置全局服务
        reset_tenant_services()
        reset_metering_service()
        
        paas = DistributedPaaS("node_003")  # 使用不同节点
        paas.activate()
        
        # 创建租户
        paas.tenant_manager.create_tenant("tenant_003", "测试租户")
        
        # 获取报告
        report = paas.get_usage_report("tenant_003")
        assert "tenant_id" in report
        assert "usage" in report


class TestPaaSIntegration:
    """测试 PaaS 集成"""

    def test_elect_then_activate(self):
        """选举后激活 PaaS"""
        elector = PaaSNodeElector("node_001")
        paas = DistributedPaaS("node_001")
        
        # 初始状态
        assert elector.is_elected is False
        assert paas.is_active is False
        
        # 选举
        elector.elect_as_paas("node_001")
        assert elector.is_elected is True
        
        # 激活
        paas.activate()
        assert paas.is_active is True

    def test_remove_then_deactivate(self):
        """罢免后休眠 PaaS"""
        elector = PaaSNodeElector("node_001", is_elected=True)
        paas = DistributedPaaS("node_001")
        paas.activate()
        
        # 初始状态
        assert elector.is_elected is True
        assert paas.is_active is True
        
        # 罢免
        elector.remove_from_paas("node_001")
        assert elector.is_elected is False
        
        # 休眠
        paas.deactivate()
        assert paas.is_active is False

    def test_multi_node_cluster(self):
        """多节点集群"""
        # 创建 3 个节点
        elector1 = PaaSNodeElector("node_001", is_elected=True)
        elector2 = PaaSNodeElector("node_002")
        elector3 = PaaSNodeElector("node_003")
        
        # 同步 PaaS 节点信息
        elector2.elect_as_paas("node_001")
        elector3.elect_as_paas("node_001")
        
        # 验证
        assert elector1.is_elected is True
        assert elector2.is_elected is False
        assert elector3.is_elected is False
        
        assert elector1.is_paas_node("node_001")
        assert elector2.is_paas_node("node_001")
        assert elector3.is_paas_node("node_001")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
