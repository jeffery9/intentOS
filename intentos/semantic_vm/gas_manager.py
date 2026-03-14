"""
Gas 管理器

管理 Gas 成本计算、消耗追踪、统计报告

设计文档：docs/private/003-gas-mechanism.md
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from .gas import GasCosts, ExecutionBudget, GasReceipt
from ..semantic_vm import SemanticOpcode, SemanticInstruction

logger = logging.getLogger(__name__)


class GasManager:
    """
    Gas 管理器
    
    管理 Gas 成本计算、消耗追踪、统计报告
    """
    
    def __init__(self, costs: Optional[GasCosts] = None):
        self.costs = costs or GasCosts()
        self._receipts: list[GasReceipt] = []
    
    def estimate_gas(
        self,
        instructions: list[SemanticInstruction],
        variables: Optional[dict] = None,
    ) -> int:
        """
        估算程序的 Gas 消耗
        
        Args:
            instructions: 指令列表
            variables: 变量（用于条件评估）
            
        Returns:
            估算的 Gas 总量
        """
        total_gas = 0
        
        for instr in instructions:
            # 基础成本
            opcode = instr.opcode
            gas = self.costs.get_cost(opcode)
            total_gas += gas
            
            # 循环体成本（估算）
            if opcode == SemanticOpcode.LOOP:
                times = instr.parameters.get("times", 1)
                body_gas = self.estimate_gas(instr.body, variables)
                total_gas += body_gas * times
            
            elif opcode == SemanticOpcode.WHILE:
                # WHILE 循环按最大可能次数估算（保守）
                max_iterations = 100  # 可配置
                body_gas = self.estimate_gas(instr.body, variables)
                total_gas += body_gas * max_iterations
            
            elif opcode == SemanticOpcode.IF:
                # IF/ELSE 体取最大值
                if instr.body:
                    body_gas = self.estimate_gas(instr.body, variables)
                    total_gas += body_gas
        
        return total_gas
    
    def consume_gas(
        self,
        budget: ExecutionBudget,
        opcode: Any,
        extra_gas: int = 0,
    ) -> tuple[bool, int]:
        """
        消耗 Gas
        
        Args:
            budget: 执行预算
            opcode: 指令操作码
            extra_gas: 额外 Gas（如循环体）
            
        Returns:
            (是否成功，消耗的 Gas 量)
        """
        base_gas = self.costs.get_cost(opcode)
        total_gas = base_gas + extra_gas
        
        if not budget.consume(total_gas):
            logger.warning(
                f"Gas 不足：需要 {total_gas}, 剩余 {budget.gas_remaining}"
            )
            return False, total_gas
        
        return True, total_gas
    
    def record_receipt(self, receipt: GasReceipt) -> None:
        """记录 Gas 收据"""
        self._receipts.append(receipt)
    
    def get_receipts(self) -> list[GasReceipt]:
        """获取所有收据"""
        return self._receipts.copy()
    
    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        if not self._receipts:
            return {
                "total_executions": 0,
                "total_gas_used": 0,
                "average_gas_per_execution": 0,
                "success_rate": 0.0,
            }
        
        total_gas = sum(r.gas_used for r in self._receipts)
        success_count = sum(1 for r in self._receipts if r.success)
        
        return {
            "total_executions": len(self._receipts),
            "total_gas_used": total_gas,
            "average_gas_per_execution": total_gas / len(self._receipts),
            "success_rate": success_count / len(self._receipts),
        }
