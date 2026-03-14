"""
Gas 机制测试

测试用例覆盖：
1. Gas 成本配置测试
2. 执行预算测试
3. Gas 管理器测试
4. Gas 估算测试
"""

import pytest
from intentos.semantic_vm.gas import GasCosts, ExecutionBudget, GasReceipt
from intentos.semantic_vm.gas_manager import GasManager
from intentos.semantic_vm import SemanticOpcode, SemanticInstruction


class TestGasCosts:
    """Gas 成本测试"""
    
    def test_default_costs(self):
        """测试默认成本"""
        costs = GasCosts()
        assert costs.SET == 5
        assert costs.CREATE == 100
        assert costs.DEFINE_INSTRUCTION == 5000
    
    def test_get_cost(self):
        """测试获取成本"""
        costs = GasCosts()
        assert costs.get_cost(SemanticOpcode.SET) == 5
        assert costs.get_cost(SemanticOpcode.CREATE) == 100
        assert costs.get_cost(SemanticOpcode.DEFINE_INSTRUCTION) == 5000
    
    def test_get_cost_with_string(self):
        """测试字符串操作码"""
        costs = GasCosts()
        assert costs.get_cost("SET") == 5
        assert costs.get_cost("CREATE") == 100
        assert costs.get_cost("UNKNOWN") == 100  # 默认值
    
    def test_get_all_costs(self):
        """测试获取所有成本"""
        costs = GasCosts()
        all_costs = costs.get_all_costs()
        assert "SET" in all_costs
        assert "CREATE" in all_costs
        assert all_costs["SET"] == 5
        assert all_costs["CREATE"] == 100


class TestExecutionBudget:
    """执行预算测试"""
    
    def test_consume_gas(self):
        """测试消耗 Gas"""
        budget = ExecutionBudget(gas_limit=1000)
        
        assert budget.consume(100) is True
        assert budget.gas_used == 100
        assert budget.gas_remaining == 900
        
        assert budget.consume(950) is False  # Gas 不足
        assert budget.consume(900) is True   # 刚好用完
    
    def test_gas_exhausted(self):
        """测试 Gas 耗尽检测"""
        budget = ExecutionBudget(gas_limit=100)
        
        budget.consume(100)
        assert budget.is_exhausted is True
    
    def test_refund_gas(self):
        """测试退款 Gas"""
        budget = ExecutionBudget(gas_limit=1000)
        
        budget.consume(500)
        budget.refund(200)  # 循环提前结束退款
        
        assert budget.gas_remaining == 700  # 1000 - 500 + 200
    
    def test_refund_limit(self):
        """测试退款限制"""
        budget = ExecutionBudget(gas_limit=1000)
        
        budget.consume(500)
        budget.refund(600)  # 超过已使用
        
        # 退款不能超过已使用的 Gas
        assert budget.gas_refunded == 500
        assert budget.gas_remaining == 1000
    
    def test_check_limits_gas_exhausted(self):
        """测试限制检查 - Gas 耗尽"""
        budget = ExecutionBudget(gas_limit=100)
        
        budget.consume(100)
        ok, error = budget.check_limits()
        
        assert ok is False
        assert "exhausted" in error
    
    def test_check_limits_iterations_exceeded(self):
        """测试限制检查 - 迭代超限"""
        budget = ExecutionBudget(gas_limit=1000, max_iterations=10)
        
        for _ in range(10):
            budget.increment_iteration()
        
        ok, error = budget.check_limits()
        
        assert ok is False
        assert "iterations" in error
    
    def test_check_limits_ok(self):
        """测试限制检查 - 通过"""
        budget = ExecutionBudget(gas_limit=1000, max_iterations=100)
        
        budget.consume(500)
        budget.increment_iteration()
        
        ok, error = budget.check_limits()
        
        assert ok is True
    
    def test_to_dict(self):
        """测试转换为字典"""
        budget = ExecutionBudget(
            gas_limit=1000,
            gas_used=500,
            program_id="test-123",
        )
        
        data = budget.to_dict()
        
        assert data["gas_limit"] == 1000
        assert data["gas_used"] == 500
        assert data["gas_remaining"] == 500
        assert data["program_id"] == "test-123"
    
    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "gas_limit": 2000,
            "gas_used": 1000,
            "gas_refunded": 100,
            "iteration_count": 50,
            "program_id": "test-456",
        }
        
        budget = ExecutionBudget.from_dict(data)
        
        assert budget.gas_limit == 2000
        assert budget.gas_used == 1000
        assert budget.gas_refunded == 100
        assert budget.iteration_count == 50
        assert budget.program_id == "test-456"


class TestGasReceipt:
    """Gas 收据测试"""
    
    def test_to_dict(self):
        """测试转换为字典"""
        receipt = GasReceipt(
            program_id="test-123",
            gas_limit=1000,
            gas_used=500,
            gas_remaining=500,
            success=True,
            instruction_count=10,
            breakdown={"SET": 50, "CREATE": 450},
        )
        
        data = receipt.to_dict()
        
        assert data["program_id"] == "test-123"
        assert data["gas_used"] == 500
        assert data["success"] is True
        assert data["instruction_count"] == 10
        assert data["breakdown"]["SET"] == 50


class TestGasManager:
    """Gas 管理器测试"""
    
    def test_estimate_gas_simple(self):
        """测试简单 Gas 估算"""
        manager = GasManager()
        
        instructions = [
            SemanticInstruction(opcode=SemanticOpcode.SET),
            SemanticInstruction(opcode=SemanticOpcode.CREATE),
            SemanticInstruction(opcode=SemanticOpcode.QUERY),
        ]
        
        estimated = manager.estimate_gas(instructions)
        
        # SET(5) + CREATE(100) + QUERY(10) = 115
        assert estimated == 115
    
    def test_estimate_gas_with_loop(self):
        """测试循环 Gas 估算"""
        manager = GasManager()
        
        body = [
            SemanticInstruction(opcode=SemanticOpcode.SET),
        ]
        
        instructions = [
            SemanticInstruction(
                opcode=SemanticOpcode.LOOP,
                parameters={"times": 5},
                body=body,
            ),
        ]
        
        estimated = manager.estimate_gas(instructions)
        
        # LOOP(20) + 5 * SET(5) = 45
        assert estimated == 45
    
    def test_estimate_gas_with_while(self):
        """测试 WHILE 循环 Gas 估算"""
        manager = GasManager()
        
        body = [
            SemanticInstruction(opcode=SemanticOpcode.SET),
        ]
        
        instructions = [
            SemanticInstruction(
                opcode=SemanticOpcode.WHILE,
                body=body,
            ),
        ]
        
        estimated = manager.estimate_gas(instructions)
        
        # WHILE(20) + 100 * SET(5) = 520 (WHILE 按 100 次估算)
        assert estimated == 520
    
    def test_consume_gas(self):
        """测试消耗 Gas"""
        manager = GasManager()
        budget = ExecutionBudget(gas_limit=1000)
        
        success, cost = manager.consume_gas(budget, SemanticOpcode.SET)
        
        assert success is True
        assert cost == 5
        assert budget.gas_used == 5
    
    def test_consume_gas_insufficient(self):
        """测试 Gas 不足"""
        manager = GasManager()
        budget = ExecutionBudget(gas_limit=10)
        
        success, cost = manager.consume_gas(budget, SemanticOpcode.CREATE)
        
        assert success is False
        assert cost == 100
        assert budget.gas_used == 0  # 未消耗
    
    def test_consume_gas_with_extra(self):
        """测试消耗 Gas（含额外）"""
        manager = GasManager()
        budget = ExecutionBudget(gas_limit=1000)
        
        success, cost = manager.consume_gas(
            budget, SemanticOpcode.LOOP, extra_gas=50
        )
        
        assert success is True
        assert cost == 70  # LOOP(20) + extra(50)
        assert budget.gas_used == 70
    
    def test_record_receipt(self):
        """测试记录收据"""
        manager = GasManager()
        
        receipt = GasReceipt(
            program_id="test-123",
            gas_limit=1000,
            gas_used=500,
            gas_remaining=500,
            success=True,
        )
        
        manager.record_receipt(receipt)
        
        receipts = manager.get_receipts()
        assert len(receipts) == 1
        assert receipts[0].program_id == "test-123"
    
    def test_get_statistics(self):
        """测试统计信息"""
        manager = GasManager()
        
        # 无收据时
        stats = manager.get_statistics()
        assert stats["total_executions"] == 0
        
        # 添加收据
        manager.record_receipt(GasReceipt(
            program_id="test-1",
            gas_limit=1000,
            gas_used=500,
            gas_remaining=500,
            success=True,
        ))
        
        manager.record_receipt(GasReceipt(
            program_id="test-2",
            gas_limit=1000,
            gas_used=300,
            gas_remaining=700,
            success=False,
        ))
        
        stats = manager.get_statistics()
        
        assert stats["total_executions"] == 2
        assert stats["total_gas_used"] == 800
        assert stats["average_gas_per_execution"] == 400
        assert stats["success_rate"] == 0.5


class TestGasManagerIntegration:
    """Gas 管理器集成测试"""
    
    def test_full_program_estimation(self):
        """测试完整程序估算"""
        manager = GasManager()
        
        # 创建一个复杂程序
        instructions = [
            SemanticInstruction(opcode=SemanticOpcode.SET, parameters={"name": "x", "value": 0}),
            SemanticInstruction(
                opcode=SemanticOpcode.LOOP,
                parameters={"times": 10},
                body=[
                    SemanticInstruction(opcode=SemanticOpcode.SET, parameters={"name": "x", "value": "x+1"}),
                ],
            ),
            SemanticInstruction(opcode=SemanticOpcode.QUERY, parameters={"target": "x"}),
        ]
        
        estimated = manager.estimate_gas(instructions)
        
        # SET(5) + [LOOP(20) + 10*SET(5)] + QUERY(10) = 5 + 70 + 10 = 85
        assert estimated == 85
    
    def test_budget_enforcement(self):
        """测试预算执行"""
        manager = GasManager()
        budget = ExecutionBudget(gas_limit=100)
        
        # 执行一系列指令
        instructions = [
            SemanticInstruction(opcode=SemanticOpcode.CREATE),  # 100
            SemanticInstruction(opcode=SemanticOpcode.SET),     # 5 (应该失败)
        ]
        
        results = []
        for instr in instructions:
            success, cost = manager.consume_gas(budget, instr.opcode)
            results.append((success, cost))
        
        # 第一个成功，第二个失败
        assert results[0][0] is True
        assert results[0][1] == 100
        assert results[1][0] is False  # Gas 不足
