"""
Distributed VM 高级测试

覆盖更多未测试的方法
"""

import pytest

from intentos.distributed.vm import (
    DistributedCoordinator,
    DistributedSemanticMemory,
    VMNode,
)
from intentos.llm.executor import LLMExecutor
from intentos.semantic_vm import SemanticVM

# =============================================================================
# DistributedSemanticMemory Advanced Tests
# =============================================================================


class TestDistributedSemanticMemoryAdvanced:
    """DistributedSemanticMemory 高级测试"""

    def test_memory_add_node(self):
        """测试添加节点"""
        memory = DistributedSemanticMemory()

        node = VMNode(host="node1", port=8001)
        memory.add_node(node)

        assert len(memory.nodes) == 1
        assert memory.nodes[0].host == "node1"

    def test_memory_add_multiple_nodes(self):
        """测试添加多个节点"""
        memory = DistributedSemanticMemory()

        for i in range(5):
            memory.add_node(VMNode(host=f"node{i}", port=8000 + i))

        assert len(memory.nodes) == 5

    def test_memory_remove_node(self):
        """测试移除节点"""
        memory = DistributedSemanticMemory()

        node = VMNode(host="node1", port=8001)
        memory.add_node(node)

        memory.remove_node(node.node_id)

        assert len(memory.nodes) == 0

    def test_memory_remove_nonexistent_node(self):
        """测试移除不存在的节点"""
        memory = DistributedSemanticMemory()

        memory.add_node(VMNode(host="node1", port=8001))
        memory.remove_node("nonexistent_id")

        assert len(memory.nodes) == 1

    def test_memory_get_nodes(self):
        """测试获取所有节点"""
        memory = DistributedSemanticMemory()

        node1 = VMNode(host="node1", port=8001)
        node2 = VMNode(host="node2", port=8002)
        memory.add_node(node1)
        memory.add_node(node2)

        nodes = memory.get_nodes()

        assert len(nodes) == 2
        assert nodes[0].host == "node1"
        assert nodes[1].host == "node2"

    def test_memory_get_active_nodes(self):
        """测试获取活跃节点"""
        memory = DistributedSemanticMemory()

        active_node = VMNode(host="active", port=8001, status="active")
        inactive_node = VMNode(host="inactive", port=8002, status="inactive")

        memory.add_node(active_node)
        memory.add_node(inactive_node)

        active_nodes = memory.get_active_nodes()

        assert len(active_nodes) == 1
        assert active_nodes[0].host == "active"

    def test_memory_get_active_nodes_all_inactive(self):
        """测试获取活跃节点（全部不活跃）"""
        memory = DistributedSemanticMemory()

        memory.add_node(VMNode(host="node1", port=8001, status="inactive"))
        memory.add_node(VMNode(host="node2", port=8002, status="inactive"))

        active_nodes = memory.get_active_nodes()

        assert len(active_nodes) == 0

    def test_memory_rebuild_ring(self):
        """测试重建哈希环"""
        memory = DistributedSemanticMemory()

        memory.add_node(VMNode(host="node1", port=8001))
        memory.add_node(VMNode(host="node2", port=8002))

        # 环应该被重建
        assert hasattr(memory, "ring")
        assert len(memory.ring) > 0

    def test_memory_log_audit(self):
        """测试记录审计日志"""
        memory = DistributedSemanticMemory()

        audit_id = memory.log_audit("test_action", {"key": "value"})

        assert audit_id is not None
        assert len(audit_id) > 0

    @pytest.mark.asyncio
    async def test_memory_set_local(self):
        """测试本地设置数据"""
        memory = DistributedSemanticMemory()

        # 直接设置到本地存储
        memory.local_storage.set("TEMPLATE", "test", {"data": "value"})

        # 验证数据已设置
        stored = memory.local_storage.get("TEMPLATE", "test")
        assert stored is not None

    @pytest.mark.asyncio
    async def test_memory_get_local(self):
        """测试本地获取数据"""
        memory = DistributedSemanticMemory()

        # 先设置数据
        memory.local_storage.set("CONFIG", "key", "value")

        # 获取数据
        value = memory.local_storage.get("CONFIG", "key")

        assert value == "value"

    @pytest.mark.asyncio
    async def test_memory_delete_local(self):
        """测试本地删除数据"""
        memory = DistributedSemanticMemory()

        # 先设置数据
        memory.local_storage.set("TEMP", "to_delete", "value")

        # 删除数据（可能返回 True 或 None）
        result = memory.local_storage.delete("TEMP", "to_delete")

        # 验证已删除
        stored = memory.local_storage.get("TEMP", "to_delete")
        assert stored is None

    @pytest.mark.asyncio
    async def test_memory_delete_nonexistent(self):
        """测试删除不存在的数据"""
        memory = DistributedSemanticMemory()

        result = memory.local_storage.delete("NONEXISTENT", "key")

        assert result is False

    @pytest.mark.asyncio
    async def test_memory_get_nonexistent(self):
        """测试获取不存在的数据"""
        memory = DistributedSemanticMemory()

        value = memory.local_storage.get("NONEXISTENT", "key")

        assert value is None

    @pytest.mark.asyncio
    async def test_memory_remote_get_exception_handling(self):
        """测试远程获取异常处理"""
        memory = DistributedSemanticMemory()

        # 添加一个远程节点
        node = VMNode(host="remote", port=9999)
        memory.add_node(node)

        # 远程获取应该返回 None（因为连接失败）
        value = await memory._remote_get(node, "STORE", "key")

        assert value is None

    @pytest.mark.asyncio
    async def test_memory_remote_set_exception_handling(self):
        """测试远程设置异常处理"""
        memory = DistributedSemanticMemory()

        node = VMNode(host="remote", port=9999)
        memory.add_node(node)

        # 不应该抛出异常
        await memory._remote_set(node, "STORE", "key", "value")

    @pytest.mark.asyncio
    async def test_memory_remote_delete_exception_handling(self):
        """测试远程删除异常处理"""
        memory = DistributedSemanticMemory()

        node = VMNode(host="remote", port=9999)
        memory.add_node(node)

        # 应该返回 False
        result = await memory._remote_delete(node, "STORE", "key")

        assert result is False


# =============================================================================
# DistributedCoordinator Advanced Tests
# =============================================================================


class TestDistributedCoordinatorAdvanced:
    """DistributedCoordinator 高级测试"""

    @pytest.fixture
    def coordinator(self):
        """创建测试用协调器"""
        memory = DistributedSemanticMemory()
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        return DistributedCoordinator(memory=memory, local_vm=vm)

    def test_coordinator_with_local_vm(self, coordinator):
        """测试带本地 VM 的协调器"""
        assert coordinator.local_vm is not None
        assert coordinator.memory is not None

    def test_coordinator_processes_empty(self, coordinator):
        """测试空的进程表"""
        assert coordinator.processes == {}

    def test_coordinator_results_empty(self, coordinator):
        """测试空的结果"""
        assert coordinator.results == {}

    @pytest.mark.asyncio
    async def test_update_pcb_nonexistent(self, coordinator):
        """测试更新不存在的 PCB"""
        # 不应该抛出异常
        await coordinator.update_pcb("nonexistent_pid", pc=10, state="running")

    @pytest.mark.asyncio
    async def test_update_pcb_existing(self, coordinator):
        """测试更新存在的 PCB"""
        # 先创建一个进程
        from intentos.distributed.vm import ProcessState, SemanticProcess

        pid = "test_pid"
        pcb = SemanticProcess(
            pid=pid, program_name="test_program", node_id="node1", state=ProcessState.RUNNING
        )
        coordinator.processes[pid] = pcb

        # 更新 PCB
        await coordinator.update_pcb(pid, pc=5, state="completed")

        # 验证更新
        assert coordinator.processes[pid].pc == 5
        assert coordinator.processes[pid].state == ProcessState.COMPLETED


# =============================================================================
# Integration Tests
# =============================================================================


class TestDistributedVMIntegration:
    """Distributed VM 集成测试"""

    def test_full_node_lifecycle(self):
        """测试完整节点生命周期"""
        memory = DistributedSemanticMemory()

        # 1. 添加节点
        node = VMNode(host="node1", port=8001)
        memory.add_node(node)
        assert len(memory.nodes) == 1

        # 2. 获取节点
        nodes = memory.get_nodes()
        assert len(nodes) == 1

        # 3. 获取活跃节点
        active = memory.get_active_nodes()
        assert len(active) == 1

        # 4. 移除节点
        memory.remove_node(node.node_id)
        assert len(memory.nodes) == 0

    def test_memory_with_multiple_nodes(self):
        """测试多节点内存"""
        memory = DistributedSemanticMemory()

        # 添加多个节点
        for i in range(3):
            status = "active" if i % 2 == 0 else "inactive"
            memory.add_node(VMNode(host=f"node{i}", port=8000 + i, status=status))

        # 验证
        assert len(memory.get_nodes()) == 3
        assert len(memory.get_active_nodes()) == 2

    @pytest.mark.asyncio
    async def test_memory_operations_workflow(self):
        """测试内存操作工作流"""
        memory = DistributedSemanticMemory()

        # 1. 设置数据（直接到本地存储）
        memory.local_storage.set("CONFIG", "setting1", "value1")

        # 2. 获取数据
        value = memory.local_storage.get("CONFIG", "setting1")
        assert value == "value1"

        # 3. 获取状态
        state = memory.get_state()
        assert state is not None

        # 4. 删除数据
        result = memory.local_storage.delete("CONFIG", "setting1")
        assert result is True

        # 5. 验证删除
        value = memory.local_storage.get("CONFIG", "setting1")
        assert value is None

    def test_coordinator_and_memory_integration(self):
        """测试协调器和内存集成"""
        # 创建内存
        memory = DistributedSemanticMemory()
        memory.add_node(VMNode(host="node1", port=8001))

        # 创建协调器
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        coordinator = DistributedCoordinator(memory=memory, local_vm=vm)

        # 验证集成
        assert coordinator.memory == memory
        assert coordinator.local_vm == vm
        assert len(coordinator.memory.get_nodes()) == 1
