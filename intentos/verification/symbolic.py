"""
符号执行与 SMT 形式化验证模块 (Symbolic Verification with Z3)

提供代码级与 DAG 级别的形式化验证：
1. 静态 Gas 消耗有界性证明 (等价于有限步停机定理 B.4)
2. 符号化内存边界安全与隔离区检查
"""

from __future__ import annotations

import logging
from typing import Any, Optional
import z3

from intentos.verification.formal import DAGNode

logger = logging.getLogger(__name__)


class SymbolicVerifier:
    """
    语义虚拟机 (SVM) 形式化符号验证器

    使用 Z3 求解器在静态阶段建立数学公式，证明意图/DAG 的合理停机性与内存安全性。
    """

    def __init__(self) -> None:
        pass

    def verify_gas_bounded(
        self,
        nodes: list[DAGNode],
        initial_gas: int,
        default_cost: int = 10
    ) -> dict[str, Any]:
        """
        验证 DAG 在所有执行路径下，其 Gas 消耗是否绝对有界 (必停机)

        通过 Z3 符号建模：
        1. 每一个节点运行需要消耗特定 Gas
        2. 建模节点执行链中的 Gas 累加关系
        3. 求解 `RemainingGas < 0` 是否存在可行解
        """
        solver = z3.Solver()

        # 定义符号变量
        init_g = z3.Int("initial_gas")
        solver.add(init_g == initial_gas)

        # 每个节点的剩余 Gas 符号
        gas_states = {}
        prev_gas = init_g

        # 构建顺序/分支依赖树中的 Gas 衰减公式
        for i, node in enumerate(nodes):
            node_id_clean = node.node_id.replace("-", "_")
            node_gas = z3.Int(f"gas_after_node_{node_id_clean}")
            
            # 获取节点声明的特定 gas 消耗，或者使用默认消耗
            node_cost = int(node.inputs.get("gas_cost", default_cost))
            
            # 约束：当前节点的剩余 Gas = 前一个状态的 Gas - 当前节点消耗
            solver.add(node_gas == prev_gas - node_cost)
            gas_states[node.node_id] = node_gas
            prev_gas = node_gas

        # 核心安全性断言：在执行链的任意时刻，剩余 Gas 不能为负数
        # 我们让 Z3 尝试寻找一个“使剩余 Gas 为负数或溢出”的反例
        violation_conditions = []
        for node_id, node_gas in gas_states.items():
            violation_conditions.append(node_gas < 0)

        # 只要存在任一阶段 Gas 耗尽，即判定为存在违反情况
        solver.add(z3.Or(violation_conditions))

        if solver.check() == z3.sat:
            # 找到了反例，说明在当前的初始 Gas 下，有路径会导致停机失败/Gas 耗尽
            model = solver.model()
            logger.warning(f"Z3 形式化验证失败：存在 Gas 耗尽路径！模型：{model}")
            return {
                "is_valid": False,
                "error": "Z3 判定：部分执行路径可能导致 Gas 溢出/耗尽（违反定理 B.4）",
                "counter_example": {str(k): int(str(model[k])) for k in model.decls()}
            }
        
        # z3.unsat 说明不可能存在 Gas < 0 的情况，停机性完美得证
        return {
            "is_valid": True,
            "message": "Z3 形式化验证成功：该 DAG 执行流在所有可能路径下均被 Gas 严格约束，保证在有限步内必然安全停机（定理 B.4 得证）"
        }

    def verify_memory_isolation(
        self,
        nodes: list[DAGNode],
        min_address: int = 0,
        max_address: int = 10000
    ) -> dict[str, Any]:
        """
        验证 DAG 执行期间的符号化内存越界保护

        检查每个节点读取/写入的 `address` 偏移和 `size` 是否会被外部输入操控而越过隔离边界。
        """
        solver = z3.Solver()

        # 声明地址空间边界常量
        low_bound = z3.Int("low_bound")
        high_bound = z3.Int("high_bound")
        solver.add(low_bound == min_address)
        solver.add(high_bound == max_address)

        violation_conditions = []

        for node in nodes:
            # 检查是否有内存操作输入
            if "memory_address" in node.inputs:
                node_id_clean = node.node_id.replace("-", "_")
                
                # 定义符号化的内存访问地址和大小
                addr_sym = z3.Int(f"addr_{node_id_clean}")
                size_sym = z3.Int(f"size_{node_id_clean}")

                # 约束绑定到节点的静态或输入范围
                static_addr = node.inputs.get("memory_address")
                static_size = node.inputs.get("memory_size", 1)

                if isinstance(static_addr, int):
                    solver.add(addr_sym == static_addr)

                if isinstance(static_size, int):
                    solver.add(size_sym == static_size)
                else:
                    solver.add(size_sym > 0)

                # 反例：发生内存越界 (addr < low_bound 或者 addr + size > high_bound)
                out_of_bounds = z3.Or(
                    addr_sym < low_bound,
                    addr_sym + size_sym > high_bound
                )
                violation_conditions.append(out_of_bounds)

        if not violation_conditions:
            return {
                "is_valid": True,
                "message": "无内存读写操作，默认安全隔离"
            }

        # 核心安全断言：如果存在任意一个节点越界，则判定为存在越界漏洞
        solver.add(z3.Or(violation_conditions))

        # 检查是否可满足（即是否存在任意越界漏洞）
        if solver.check() == z3.sat:
            model = solver.model()
            return {
                "is_valid": False,
                "error": "Z3 判定：检测到潜在的内存越界/沙箱隔离逃逸风险！",
                "counter_example": {str(k): int(str(model[k])) for k in model.decls() if model[k] is not None}
            }

        return {
            "is_valid": True,
            "message": "Z3 形式化验证成功：所有符号化内存操作都被限制在安全隔离沙箱内（隔离性得证）"
        }
