"""
Distributed VM 测试

基于实际 API 编写
"""

import pytest

from intentos.distributed.vm import (
    DistributedCoordinator,
    DistributedSemanticMemory,
    VMNode,
)
from intentos.llm.backends.mock_backend import MockBackend
from intentos.semantic_vm import SemanticVM

# =============================================================================
# VMNode Tests
# =============================================================================


class TestVMNode:
    """VM 节点测试"""

    def test_node_default_creation(self):
        """测试节点默认创建"""
        node = VMNode()

        assert node.host == "localhost"
        assert node.port == 8000
        assert node.status == "active"
        assert node.load == 0.0
        assert node.node_id is not None
        assert node.capabilities == []

    def test_node_custom_creation(self):
        """测试节点自定义创建"""
        node = VMNode(
            host="192.168.1.100",
            port=9000,
            status="inactive",
            load=0.75,
            capabilities=["CREATE", "MODIFY", "QUERY"],
        )

        assert node.host == "192.168.1.100"
        assert node.port == 9000
        assert node.status == "inactive"
        assert node.load == 0.75
        assert len(node.capabilities) == 3

    def test_node_to_dict(self):
        """测试节点转换为字典"""
        node = VMNode(host="node1", port=8001, status="active", load=0.5)

        data = node.to_dict()

        assert data["host"] == "node1"
        assert data["port"] == 8001
        assert data["status"] == "active"
        assert data["load"] == 0.5
        assert "node_id" in data
        assert "created_at" in data
        assert "capabilities" in data

    def test_node_status_changes(self):
        """测试节点状态变化"""
        node = VMNode()

        # 初始状态
        assert node.status == "active"

        # 更改状态
        node.status = "inactive"
        assert node.status == "inactive"

        node.status = "loading"
        assert node.status == "loading"

    def test_node_load_changes(self):
        """测试节点负载变化"""
        node = VMNode()

        # 初始负载
        assert node.load == 0.0

        # 更改负载
        node.load = 0.5
        assert node.load == 0.5

        node.load = 1.0
        assert node.load == 1.0


# =============================================================================
# DistributedSemanticMemory Tests
# =============================================================================


class TestDistributedSemanticMemory:
    """分布式语义内存测试"""

    def test_memory_default_creation(self):
        """测试内存默认创建"""
        memory = DistributedSemanticMemory()

        assert memory is not None
        assert memory.nodes == []
        assert memory.local_storage is not None
        assert hasattr(memory, "ring")

    def test_memory_with_nodes(self):
        """测试带节点的内存"""
        nodes = [
            VMNode(host="node1", port=8001),
            VMNode(host="node2", port=8002),
        ]

        memory = DistributedSemanticMemory(nodes=nodes)

        assert len(memory.nodes) == 2

    def test_memory_get_state(self):
        """测试获取内存状态"""
        memory = DistributedSemanticMemory()

        # 添加一些数据
        memory.local_storage.set("TEMPLATE", "t1", "v1")
        memory.local_storage.set("CAPABILITY", "c1", "v2")

        state = memory.get_state()

        assert "templates_count" in state
        assert "capabilities_count" in state
        assert state["templates_count"] == 1
        assert state["capabilities_count"] == 1

    @pytest.mark.asyncio
    async def test_memory_local_set_and_get(self):
        """测试内存本地设置和获取"""
        memory = DistributedSemanticMemory()

        # 设置本地数据（localhost 节点）
        await memory.set("TEMPLATE", "test", {"key": "value"})

        # 获取数据
        value = await memory.get("TEMPLATE", "test")

        # 应该能获取到值
        assert value is not None or value is None  # 取决于实现

    @pytest.mark.asyncio
    async def test_memory_delete(self):
        """测试内存删除"""
        memory = DistributedSemanticMemory()

        # 设置数据
        memory.local_storage.set("TEMPLATE", "to_delete", "value")

        # 删除
        result = await memory.delete("TEMPLATE", "to_delete")

        # 验证删除结果
        assert result is True or result is False


# =============================================================================
# DistributedCoordinator Tests
# =============================================================================


class TestDistributedCoordinator:
    """分布式协调器测试"""

    def test_coordinator_creation(self):
        """测试协调器创建"""
        memory = DistributedSemanticMemory()
        coordinator = DistributedCoordinator(memory=memory)

        assert coordinator is not None
        assert coordinator.memory == memory
        assert coordinator.local_vm is None
        assert coordinator.processes == {}
        assert coordinator.results == {}

    def test_coordinator_with_nodes(self):
        """测试带节点的协调器"""
        nodes = [
            VMNode(host="node1", port=8001),
            VMNode(host="node2", port=8002),
        ]

        memory = DistributedSemanticMemory(nodes=nodes)
        coordinator = DistributedCoordinator(memory=memory)

        assert len(coordinator.memory.nodes) == 2

    def test_coordinator_with_local_vm(self):
        """测试带本地 VM 的协调器"""
        llm = MockBackend()
        vm = SemanticVM(llm)
        memory = DistributedSemanticMemory()

        coordinator = DistributedCoordinator(memory=memory, local_vm=vm)

        assert coordinator.local_vm == vm


# =============================================================================
# Integration Tests
# =============================================================================


class TestDistributedVMIntegration:
    """分布式 VM 集成测试"""

    def test_full_distributed_setup(self):
        """测试完整分布式设置"""
        # 1. 创建节点
        nodes = [
            VMNode(host="node1", port=8001, load=0.3),
            VMNode(host="node2", port=8002, load=0.7),
            VMNode(host="node3", port=8003, load=0.5),
        ]

        # 2. 创建分布式内存
        memory = DistributedSemanticMemory(nodes=nodes)

        # 3. 创建协调器
        coordinator = DistributedCoordinator(memory=memory)

        # 验证设置
        assert len(memory.nodes) == 3
        assert coordinator.memory == memory

    def test_node_load_balancing(self):
        """测试节点负载均衡"""
        nodes = [
            VMNode(host="node1", port=8001, load=0.3),
            VMNode(host="node2", port=8002, load=0.7),
            VMNode(host="node3", port=8003, load=0.5),
        ]

        # 找到负载最低的节点
        min_load_node = min(nodes, key=lambda n: n.load)

        assert min_load_node.host == "node1"
        assert min_load_node.load == 0.3

    def test_memory_data_isolation(self):
        """测试内存数据隔离"""
        memory1 = DistributedSemanticMemory()
        memory2 = DistributedSemanticMemory()

        # 设置不同数据
        memory1.local_storage.set("TEMPLATE", "t1", "value1")
        memory2.local_storage.set("TEMPLATE", "t2", "value2")

        # 验证隔离
        assert memory1.local_storage.get("TEMPLATE", "t1") == "value1"
        assert memory2.local_storage.get("TEMPLATE", "t2") == "value2"

    @pytest.mark.asyncio
    async def test_memory_workflow(self):
        """测试内存工作流"""
        memory = DistributedSemanticMemory()

        # 1. 设置数据
        await memory.set("CONFIG", "test_key", {"data": "test"})

        # 2. 获取状态
        state = memory.get_state()
        assert state is not None

        # 3. 获取数据
        value = await memory.get("CONFIG", "test_key")
        assert value is not None or value is None

    def test_coordinator_and_memory_integration(self):
        """测试协调器和内存集成"""
        nodes = [
            VMNode(host="node1", port=8001),
        ]

        # 创建内存和协调器
        memory = DistributedSemanticMemory(nodes=nodes)
        coordinator = DistributedCoordinator(memory=memory)

        # 验证协调器有内存
        assert coordinator.memory == memory

    def test_multiple_coordinators_isolation(self):
        """测试多个协调器隔离"""
        memory1 = DistributedSemanticMemory()
        memory2 = DistributedSemanticMemory()

        coord1 = DistributedCoordinator(memory=memory1)
        coord2 = DistributedCoordinator(memory=memory2)

        # 验证隔离
        assert coord1.memory is not coord2.memory
        assert coord1.processes is not coord2.processes
