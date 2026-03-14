"""
Distributed VM 第 4 部分测试

覆盖更多未测试的方法
"""

import pytest

from intentos.distributed.vm import (
    DistributedCoordinator,
    DistributedSemanticMemory,
    ProcessState,
    SemanticProcess,
    VMNode,
)
from intentos.llm.executor import LLMExecutor
from intentos.semantic_vm import SemanticVM


class TestDistributedCoordinatorPart3:
    """DistributedCoordinator 第 3 部分测试"""

    @pytest.fixture
    def coordinator(self):
        memory = DistributedSemanticMemory()
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        return DistributedCoordinator(memory=memory, local_vm=vm)

    @pytest.mark.asyncio
    async def test_update_pcb_with_all_fields(self, coordinator):
        pid = "test_pid"
        pcb = SemanticProcess(
            pid=pid, program_name="test", node_id="node1", state=ProcessState.RUNNING, pc=5
        )
        coordinator.processes[pid] = pcb

        await coordinator.update_pcb(pid, pc=10, state="completed")

        assert coordinator.processes[pid].pc == 10
        assert coordinator.processes[pid].state == ProcessState.COMPLETED

    def test_coordinator_process_management(self, coordinator):
        pid = "pid1"
        pcb = SemanticProcess(pid=pid, program_name="prog", node_id="n1")
        coordinator.processes[pid] = pcb

        assert pid in coordinator.processes
        assert coordinator.processes[pid].program_name == "prog"


class TestDistributedSemanticMemoryPart3:
    """DistributedSemanticMemory 第 3 部分测试"""

    def test_memory_node_operations(self):
        memory = DistributedSemanticMemory()

        node1 = VMNode(host="n1", port=8001)
        node2 = VMNode(host="n2", port=8002)

        memory.add_node(node1)
        memory.add_node(node2)

        nodes = memory.get_nodes()
        assert len(nodes) == 2

        active = memory.get_active_nodes()
        assert len(active) == 2

        memory.remove_node(node1.node_id)
        assert len(memory.get_nodes()) == 1

    def test_memory_ring_rebuild(self):
        memory = DistributedSemanticMemory()

        initial_ring_size = len(memory.ring)

        memory.add_node(VMNode(host="n1", port=8001))
        after_add_size = len(memory.ring)

        memory.remove_node(memory.nodes[0].node_id)
        after_remove_size = len(memory.ring)

        assert after_add_size > initial_ring_size
        assert after_remove_size == initial_ring_size

    @pytest.mark.asyncio
    async def test_memory_audit_log(self):
        memory = DistributedSemanticMemory()

        audit_id1 = memory.log_audit("action1", {"key": "value1"})
        audit_id2 = memory.log_audit("action2", {"key": "value2"})

        assert audit_id1 is not None
        assert audit_id2 is not None
        assert audit_id1 != audit_id2


class TestVMNodePart3:
    """VMNode 第 3 部分测试"""

    def test_node_capabilities_management(self):
        node = VMNode()

        node.capabilities.append("CREATE")
        node.capabilities.append("MODIFY")

        assert len(node.capabilities) == 2
        assert "CREATE" in node.capabilities

    def test_node_load_validation(self):
        node = VMNode()

        node.load = 0.0
        assert node.load == 0.0

        node.load = 0.5
        assert node.load == 0.5

        node.load = 1.0
        assert node.load == 1.0

    def test_node_status_validation(self):
        node = VMNode()

        valid_statuses = ["active", "inactive", "loading"]
        for status in valid_statuses:
            node.status = status
            assert node.status == status


class TestDistributedVMIntegrationPart4:
    """Distributed VM 集成测试 - 第 4 部分"""

    def test_coordinator_and_process_lifecycle(self):
        memory = DistributedSemanticMemory()
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        coordinator = DistributedCoordinator(memory=memory, local_vm=vm)

        pid = "lifecycle_pid"
        pcb = SemanticProcess(pid=pid, program_name="lifecycle_prog", node_id="n1")
        coordinator.processes[pid] = pcb

        assert pcb.state == ProcessState.NEW

        pcb.state = ProcessState.RUNNING
        assert pcb.state == ProcessState.RUNNING

        pcb.state = ProcessState.COMPLETED
        assert pcb.state == ProcessState.COMPLETED

    def test_memory_and_node_integration(self):
        memory = DistributedSemanticMemory()

        for i in range(3):
            node = VMNode(
                host=f"node{i}", port=8000 + i, status="active" if i % 2 == 0 else "inactive"
            )
            memory.add_node(node)

        all_nodes = memory.get_nodes()
        active_nodes = memory.get_active_nodes()

        assert len(all_nodes) == 3
        assert len(active_nodes) == 2

    def test_process_state_transitions_complete(self):
        pcb = SemanticProcess(pid="p1", program_name="prog", node_id="n1")

        transitions = [
            (ProcessState.NEW, ProcessState.RUNNING),
            (ProcessState.RUNNING, ProcessState.COMPLETED),
        ]

        for from_state, to_state in transitions:
            pcb.state = from_state
            assert pcb.state == from_state
            pcb.state = to_state
            assert pcb.state == to_state

    def test_process_error_handling_complete(self):
        pcb = SemanticProcess(pid="p1", program_name="prog", node_id="n1")

        pcb.error = "Error 1"
        assert pcb.error == "Error 1"

        pcb.error = "Error 2"
        assert pcb.error == "Error 2"

        pcb.state = ProcessState.FAILED
        assert pcb.state == ProcessState.FAILED
        assert pcb.error == "Error 2"
