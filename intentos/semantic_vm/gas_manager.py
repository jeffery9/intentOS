"""
Gas 管理器 (Gas Manager)

负责语义程序的 Gas 消耗估算、实时监控与审计记录。
体现“Prompt 即可执行文件”的执行成本。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from .gas import GasCost, GasTracker, GasReceipt, OutOfGasError
from .vm import SemanticInstruction, SemanticOpcode

logger = logging.getLogger(__name__)

class GasManager:
    """
    Gas 管理器：语义 OS 的资源调度中心
    """

    def __init__(self):
        self._receipts: list[GasReceipt] = []

    def estimate_gas(self, instructions: list[SemanticInstruction]) -> int:
        """
        基于第一性原理估算 PEF 指令集的 Gas 消耗
        """
        total_gas = 0
        for instr in instructions:
            # 获取指令基础成本
            cost = self._get_base_cost(instr.opcode)
            total_gas += cost

            # 递归处理复合指令 (LOOP/WHILE)
            if hasattr(instr, 'body') and instr.body:
                body_gas = self.estimate_gas(instr.body)
                if instr.opcode == SemanticOpcode.LOOP:
                    times = instr.parameters.get("times", 1)
                    total_gas += body_gas * times
                elif instr.opcode == SemanticOpcode.WHILE:
                    total_gas += body_gas * 100 # 默认最大循环步数
        
        return total_gas

    def _get_base_cost(self, opcode: Any) -> int:
        """映射操作码到 GasCost 枚举"""
        if opcode in (SemanticOpcode.IF, SemanticOpcode.LOOP, SemanticOpcode.WHILE):
            return GasCost.LOOP_ITERATION.value
        if opcode in (SemanticOpcode.CREATE, SemanticOpcode.MODIFY, SemanticOpcode.SET):
            return GasCost.CREATE_OP.value
        if opcode == SemanticOpcode.EXECUTE:
            return GasCost.LLM_CALL.value
        return GasCost.BASE_INSTRUCTION.value

    def create_tracker(self, limit: int) -> GasTracker:
        """为新的语义进程创建追踪器"""
        return GasTracker(limit=limit)

    def record_execution(
        self, 
        program_name: str, 
        limit: int, 
        used: int, 
        success: bool,
        metadata: Optional[dict] = None
    ) -> GasReceipt:
        """记录执行完成后的 Gas 收据"""
        receipt = GasReceipt(
            program_name=program_name,
            gas_limit=limit,
            gas_used=used,
            success=success,
            metadata=metadata or {}
        )
        self._receipts.append(receipt)
        return receipt

    def get_statistics(self) -> dict[str, Any]:
        """获取整个集群或节点的 Gas 消耗统计信息"""
        if not self._receipts:
            return {"total_executions": 0, "total_gas_used": 0}

        total_used = sum(r.gas_used for r in self._receipts)
        return {
            "total_executions": len(self._receipts),
            "total_gas_used": total_used,
            "average_per_execution": total_used / len(self._receipts),
            "success_rate": sum(1 for r in self._receipts if r.success) / len(self._receipts)
        }
