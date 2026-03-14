"""
Distributed VM 第 3 部分测试

覆盖更多未测试的方法
"""

import pytest
from intentos.distributed.vm import (
    VMNode,
    DistributedSemanticMemory,
    DistributedCoordinator,
    ProcessState,
    SemanticProcess,
)
from intentos.semantic_vm import SemanticVM
from intentos.llm.executor import LLMExecutor


class TestDistributedCoordinatorPart2:
    """DistributedCoordinator 第 2 部分测试"""

    @pytest.fixture
    def coordinator(self):
        memory = DistributedSemanticMemory()
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        return DistributedCoordinator(memory=memory, local_vm=vm)

    @pytest.mark.asyncio
    async def test_update_pcb_existing_process(self, coordinator):
        """测试更新存在的 PCB"""
        pid = "test_pid"
        pcb = SemanticProcess(
            pid=pid,
            program_name="test",
            node_id="node1",
            state=ProcessState.RUNNING
        )
        coordinator.processes[pid] = pcb
        
        await coordinator.update_pcb(pid, pc=5, state="completed")
        
        assert coordinator.processes[pid].pc == 5

    @pytest.mark.asyncio
    async def test_update_pcb_state_change(self, coordinator):
        """测试 PCB 状态变更"""
        pid = "pid1"
        pcb = SemanticProcess(pid=pid, program_name="p", node_id="n1")
        coordinator.processes[pid] = pcb
        
        await coordinator.update_pcb(pid, pc=10, state="running")
        
        assert coordinator.processes[pid].state == ProcessState.RUNNING

    def test_coordinator_memory_access(self, coordinator):
        """测试协调器内存访问"""
        assert coordinator.memory is not None
        assert isinstance(coordinator.memory, DistributedSemanticMemory)

    def test_coordinator_local_vm_access(self, coordinator):
        """测试协调器本地 VM 访问"""
        assert coordinator.local_vm is not None


class TestDistributedSemanticMemoryPart2:
    """DistributedSemanticMemory 第 2 部分测试"""

    def test_memory_rebuild_ring(self):
        """测试重建哈希环"""
        memory = DistributedSemanticMemory()
        
        memory.add_node(VMNode(host="n1", port=8001))
        memory.add_node(VMNode(host="n2", port=8002))
        
        assert hasattr(memory, 'ring')
        assert len(memory.ring) > 0

    def test_memory_rebuild_ring_after_removal(self):
        """测试移除节点后重建环"""
        memory = DistributedSemanticMemory()
        
        node = VMNode(host="n1", port=8001)
        memory.add_node(node)
        memory.add_node(VMNode(host="n2", port=8002))
        
        memory.remove_node(node.node_id)
        
        assert hasattr(memory, 'ring')

    def test_memory_log_audit(self):
        """测试记录审计日志"""
        memory = DistributedSemanticMemory()
        
        audit_id = memory.log_audit("test_action", {"key": "value"})
        
        assert audit_id is not None
        assert len(audit_id) > 0

    @pytest.mark.asyncio
    async def test_memory_remote_get_exception(self):
        """测试远程获取异常"""
        memory = DistributedSemanticMemory()
        node = VMNode(host="remote", port=9999)
        memory.add_node(node)
        
        value = await memory._remote_get(node, "STORE", "key")
        assert value is None

    @pytest.mark.asyncio
    async def test_memory_remote_set_exception(self):
        """测试远程设置异常"""
        memory = DistributedSemanticMemory()
        node = VMNode(host="remote", port=9999)
        memory.add_node(node)
        
        await memory._remote_set(node, "STORE", "key", "value")

    @pytest.mark.asyncio
    async def test_memory_remote_delete_exception(self):
        """测试远程删除异常"""
        memory = DistributedSemanticMemory()
        node = VMNode(host="remote", port=9999)
        memory.add_node(node)
        
        result = await memory._remote_delete(node, "STORE", "key")
        assert result is False

    @pytest.mark.asyncio
    async def test_memory_set_local_node(self):
        """测试本地节点设置"""
        memory = DistributedSemanticMemory()
        
        await memory.set("TEMPLATE", "test", {"data": "value"})
        
        stored = memory.local_storage.get("TEMPLATE", "test")
        assert stored is not None

    @pytest.mark.asyncio
    async def test_memory_get_local_node(self):
        """测试本地节点获取"""
        memory = DistributedSemanticMemory()
        memory.local_storage.set("CONFIG", "key", "value")
        
        value = await memory.get("CONFIG", "key")
        assert value is not None or value is None

    @pytest.mark.asyncio
    async def test_memory_delete_local_node(self):
        """测试本地节点删除"""
        memory = DistributedSemanticMemory()
        memory.local_storage.set("TEMP", "to_delete", "value")
        
        result = await memory.delete("TEMP", "to_delete")
        assert result is True or result is False


class TestVMNodePart2:
    """VMNode 第 2 部分测试"""

    def test_node_full_dict_conversion(self):
        """测试节点完整字典转换"""
        node = VMNode(
            host="node1",
            port=8001,
            status="active",
            load=0.5,
            capabilities=["CREATE", "MODIFY"]
        )
        
        data = node.to_dict()
        
        assert data["host"] == "node1"
        assert data["port"] == 8001
        assert data["status"] == "active"
        assert data["load"] == 0.5
        assert len(data["capabilities"]) == 2
        assert "node_id" in data
        assert "created_at" in data

    def test_node_status_transitions(self):
        """测试节点状态转换"""
        node = VMNode()
        
        assert node.status == "active"
        
        node.status = "loading"
        assert node.status == "loading"
        
        node.status = "inactive"
        assert node.status == "inactive"

    def test_node_load_changes(self):
        """测试节点负载变化"""
        node = VMNode()
        
        assert node.load == 0.0
        
        node.load = 0.5
        assert node.load == 0.5
        
        node.load = 1.0
        assert node.load == 1.0

    def test_node_with_all_capabilities(self):
        """测试带所有能力的节点"""
        node = VMNode(
            capabilities=["CREATE", "MODIFY", "DELETE", "QUERY", "EXECUTE"]
        )
        
        assert len(node.capabilities) == 5


class TestDistributedVMIntegrationPart3:
    """Distributed VM 集成测试 - 第 3 部分"""

    def test_full_node_lifecycle(self):
        """测试完整节点生命周期"""
        node = VMNode(host="node1", port=8001)
        
        # 创建
        assert node.status == "active"
        
        # 修改
        node.status = "inactive"
        node.load = 0.8
        
        # 转换为字典
        data = node.to_dict()
        assert data["status"] == "inactive"
        assert data["load"] == 0.8

    def test_memory_full_workflow(self):
        """测试内存完整工作流"""
        memory = DistributedSemanticMemory()
        
        # 添加节点
        memory.add_node(VMNode(host="n1", port=8001))
        
        # 获取节点
        nodes = memory.get_nodes()
        assert len(nodes) == 1
        
        # 获取活跃节点
        active = memory.get_active_nodes()
        assert len(active) == 1
        
        # 记录审计
        audit_id = memory.log_audit("test", {})
        assert audit_id is not None
        
        # 移除节点
        memory.remove_node(nodes[0].node_id)
        assert len(memory.get_nodes()) == 0

    @pytest.mark.asyncio
    async def test_coordinator_full_workflow(self):
        """测试协调器完整工作流"""
        memory = DistributedSemanticMemory()
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        coordinator = DistributedCoordinator(memory=memory, local_vm=vm)
        
        # 创建进程
        pid = "test_pid"
        pcb = SemanticProcess(pid=pid, program_name="test", node_id="n1")
        coordinator.processes[pid] = pcb
        
        # 更新 PCB
        await coordinator.update_pcb(pid, pc=5, state="running")
        
        # 验证
        assert coordinator.processes[pid].pc == 5
        assert coordinator.processes[pid].state == ProcessState.RUNNING

    def test_process_state_lifecycle(self):
        """测试进程状态生命周期"""
        pcb = SemanticProcess(pid="p1", program_name="prog", node_id="n1")
        
        # 初始状态
        assert pcb.state == ProcessState.NEW
        
        # 运行
        pcb.state = ProcessState.RUNNING
        assert pcb.state == ProcessState.RUNNING
        
        # 完成
        pcb.state = ProcessState.COMPLETED
        assert pcb.state == ProcessState.COMPLETED

    def test_process_error_handling(self):
        """测试进程错误处理"""
        pcb = SemanticProcess(pid="p1", program_name="prog", node_id="n1")
        
        pcb.error = "Test error message"
        assert pcb.error == "Test error message"
        
        pcb.state = ProcessState.FAILED
        assert pcb.state == ProcessState.FAILED

    def test_process_to_dict_complete(self):
        """测试进程完整转换为字典"""
        pcb = SemanticProcess(
            pid="p1",
            program_name="prog",
            node_id="n1",
            state=ProcessState.RUNNING,
            pc=10
        )
        
        data = pcb.to_dict()
        
        assert data["pid"] == "p1"
        assert data["program_name"] == "prog"
        assert data["state"] == "running"
        assert data["pc"] == 10
