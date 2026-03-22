"""
语义 Gas 系统测试 (v2.1)

测试核心：
1. 语义指令执行追踪 (GasTracker)
2. PEF 程序消耗估算 (GasManager)
3. 语义执行熔断 (OutOfGasError)
4. 执行凭证审计 (GasReceipt)

遵循原则：Prompt 即可执行文件 · 语义 VM
"""

import pytest
from intentos.semantic_vm.gas import GasCost, GasTracker, GasReceipt, OutOfGasError
from intentos.semantic_vm.gas_manager import GasManager
from intentos.semantic_vm.vm import SemanticInstruction, SemanticOpcode

class TestSemanticGas:
    """测试语义 Gas 计量与管控"""

    def test_gas_tracker_consumption(self):
        """测试基础指令消耗"""
        tracker = GasTracker(limit=100)

        # 消耗基础指令成本
        tracker.consume(GasCost.BASE_INSTRUCTION.value)
        assert tracker.used == 1
        assert tracker.remaining == 99

        # 消耗 LLM 调用成本 - 会触发 OutOfGasError
        with pytest.raises(OutOfGasError):
            tracker.consume(GasCost.LLM_CALL.value)  # 1 + 100 > 100
        
    def test_gas_exhaustion_circuit_breaker(self):
        """测试语义执行熔断机制"""
        tracker = GasTracker(limit=50)
        
        tracker.consume(10)
        with pytest.raises(OutOfGasError) as excinfo:
            tracker.consume(100) # 超过限额
        
        assert "OutOfGas" in str(excinfo.value)
        assert "Limit 50" in str(excinfo.value)

    def test_gas_manager_estimation(self):
        """测试 PEF 程序执行前的静态成本估算"""
        manager = GasManager()
        
        # 构造一个简单的语义程序逻辑
        instructions = [
            SemanticInstruction(opcode=SemanticOpcode.CREATE, target_name="user_profile"),
            SemanticInstruction(opcode=SemanticOpcode.SET, target_name="age", parameters={"value": 25}),
            SemanticInstruction(opcode=SemanticOpcode.EXECUTE, parameters={"intent": "Hello world"})
        ]
        
        # 估算规则: CREATE(10) + SET(10) + EXECUTE(100) = 120
        # 注意：这里的映射由 GasManager._get_base_cost 定义
        estimated = manager.estimate_gas(instructions)
        assert estimated == 120

    def test_complex_loop_estimation(self):
        """测试带循环结构的语义程序估算"""
        manager = GasManager()
        
        loop_body = [SemanticInstruction(opcode=SemanticOpcode.SET, target_name="i")]
        instructions = [
            SemanticInstruction(
                opcode=SemanticOpcode.LOOP, 
                parameters={"times": 10},
                body=loop_body
            )
        ]
        
        # 估算: LOOP_ITER(5) + 10 * SET(10) = 105
        estimated = manager.estimate_gas(instructions)
        assert estimated == 105

    def test_gas_receipt_generation(self):
        """测试执行收据的生成与审计"""
        manager = GasManager()
        
        receipt = manager.record_execution(
            program_name="data_analysis",
            limit=1000,
            used=450,
            success=True,
            metadata={"node": "node_01"}
        )
        
        assert isinstance(receipt, GasReceipt)
        data = receipt.to_dict()
        assert data["gas_used"] == 450
        assert data["gas_remaining"] == 550
        assert data["success"] is True
        assert data["metadata"]["node"] == "node_01"

    def test_gas_statistics(self):
        """测试全局/节点级的用量统计"""
        manager = GasManager()
        
        manager.record_execution("app_1", 100, 50, True)
        manager.record_execution("app_2", 100, 80, False)
        
        stats = manager.get_statistics()
        assert stats["total_executions"] == 2
        assert stats["total_gas_used"] == 130
        assert stats["average_per_execution"] == 65
        assert stats["success_rate"] == 0.5
