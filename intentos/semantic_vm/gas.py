"""
语义 Gas 系统 (Semantic Gas System)

定义语义指令的执行成本，防止资源滥用。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class GasCost(Enum):
    """基础操作的 Gas 成本"""
    BASE_INSTRUCTION = 1      # 基础跳转/空指令
    MEMORY_READ = 2           # 读取内存
    MEMORY_WRITE = 5          # 写入内存

    # 语义指令
    CREATE_OP = 10            # 创建对象
    MODIFY_OP = 10            # 修改对象
    DELETE_OP = 5             # 删除对象

    # 高级指令
    LLM_CALL = 100            # 调用 LLM 处理器
    IO_CALL = 50              # 执行物理能力 (Agent IO)

    # 控制流
    LOOP_ITERATION = 5        # 循环单次迭代
    BRANCH_EVAL = 2           # 条件分支评估

class OutOfGasError(Exception):
    """Gas 耗尽异常"""
    pass

@dataclass
class GasTracker:
    """Gas 追踪器"""
    limit: int
    used: int = 0

    def consume(self, amount: int):
        if self.used + amount > self.limit:
            raise OutOfGasError(f"OutOfGas: Limit {self.limit}, Required {amount}, Used {self.used}")
        self.used += amount

    @property
    def remaining(self) -> int:
        return self.limit - self.used

@dataclass
class GasReceipt:
    """
    Gas 执行收据 (语义结算凭证)
    """
    program_name: str
    gas_limit: int
    gas_used: int
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "program_name": self.program_name,
            "gas_limit": self.gas_limit,
            "gas_used": self.gas_used,
            "gas_remaining": self.gas_limit - self.gas_used,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
