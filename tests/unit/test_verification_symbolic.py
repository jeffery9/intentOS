"""
Symbolic Verification Unit Tests using Z3 Solver
"""

import pytest
from intentos.verification.formal import DAGNode
from intentos.verification.symbolic import SymbolicVerifier


def test_symbolic_gas_verification_valid():
    """测试 Z3 证明：Gas 充足时的执行路径一定有界且合法"""
    verifier = SymbolicVerifier()

    # 创建一个顺序执行的 DAG 节点列表
    nodes = [
        DAGNode(node_id="step-1", task_type="exec", inputs={"gas_cost": 20}),
        DAGNode(node_id="step-2", task_type="exec", inputs={"gas_cost": 30}),
        DAGNode(node_id="step-3", task_type="exec", inputs={"gas_cost": 15}),
    ]

    # 总消耗 = 20 + 30 + 15 = 65
    # 给定 100 初始 Gas，Z3 应证明绝不会发生 Gas 耗尽（unsat -> True）
    result = verifier.verify_gas_bounded(nodes, initial_gas=100)

    assert result["is_valid"] is True
    assert "Z3 形式化验证成功" in result["message"]


def test_symbolic_gas_verification_invalid():
    """测试 Z3 证明：Gas 不足时能够证明并提供反例"""
    verifier = SymbolicVerifier()

    # 总消耗 = 20 + 30 + 15 = 65
    nodes = [
        DAGNode(node_id="step-1", task_type="exec", inputs={"gas_cost": 20}),
        DAGNode(node_id="step-2", task_type="exec", inputs={"gas_cost": 30}),
        DAGNode(node_id="step-3", task_type="exec", inputs={"gas_cost": 15}),
    ]

    # 给定 40 初始 Gas，在 step-2 后 Gas 变为了 40 - 20 - 30 = -10 < 0
    # Z3 应能发现违反条件 (sat -> False) 并指明具体发生溢出的位置和值
    result = verifier.verify_gas_bounded(nodes, initial_gas=40)

    assert result["is_valid"] is False
    assert "违反定理 B.4" in result["error"]
    assert "counter_example" in result


def test_symbolic_memory_isolation_valid():
    """测试 Z3 证明：在隔离范围内的内存访问完全安全"""
    verifier = SymbolicVerifier()

    # 所有内存读写操作的地址和大小都在 0 - 1000 范围内
    nodes = [
        DAGNode(node_id="step-1", task_type="read", inputs={"memory_address": 100, "memory_size": 20}),
        DAGNode(node_id="step-2", task_type="write", inputs={"memory_address": 500, "memory_size": 400}),
    ]

    result = verifier.verify_memory_isolation(nodes, min_address=0, max_address=1000)

    assert result["is_valid"] is True
    assert "所有符号化内存操作都被限制在安全隔离沙箱内" in result["message"]


def test_symbolic_memory_isolation_invalid():
    """测试 Z3 证明：越界的内存操作会被自动检测并生成反例"""
    verifier = SymbolicVerifier()

    # step-2 访问的物理地址 900 + 200 = 1100，超出了 1000 的高位边界
    nodes = [
        DAGNode(node_id="step-1", task_type="read", inputs={"memory_address": 100, "memory_size": 20}),
        DAGNode(node_id="step-2", task_type="write", inputs={"memory_address": 900, "memory_size": 200}),
    ]

    result = verifier.verify_memory_isolation(nodes, min_address=0, max_address=1000)

    assert result["is_valid"] is False
    assert "潜在的内存越界/沙箱隔离逃逸风险" in result["error"]
    assert "counter_example" in result
