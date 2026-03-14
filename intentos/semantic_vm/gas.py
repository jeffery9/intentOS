"""
Gas 机制

提供计算量度量和资源限制

设计文档：docs/private/003-gas-mechanism.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GasCosts:
    """
    Gas 成本表

    定义每条指令的 Gas 成本
    """

    # 基础指令（低消耗）
    SET: int = 5  # 设置变量
    GET: int = 5  # 获取变量
    QUERY: int = 10  # 查询状态

    # 写操作（中等消耗）
    CREATE: int = 100  # 创建组件
    MODIFY: int = 100  # 修改组件
    DELETE: int = 50  # 删除组件

    # 控制流（按复杂度）
    IF: int = 10  # 条件分支
    ELSE: int = 5  # Else 分支
    ENDIF: int = 5  # 结束分支
    LOOP: int = 20  # 循环
    WHILE: int = 20  # 条件循环
    ENDLOOP: int = 10  # 结束循环
    JUMP: int = 10  # 跳转
    LABEL: int = 1  # 标签（无操作）

    # 执行指令（高消耗）
    EXECUTE: int = 200  # 执行意图
    CALL: int = 150  # 调用子程序

    # 元指令（极高消耗）
    DEFINE_INSTRUCTION: int = 5000  # 定义新指令
    MODIFY_PROCESSOR: int = 10000  # 修改处理器

    # 分布式指令
    REPLICATE: int = 500  # 复制数据
    SPAWN: int = 1000  # 派生进程
    BROADCAST: int = 300  # 广播消息

    @classmethod
    def get_cost(cls, opcode: Any) -> int:
        """获取指令的 Gas 成本"""
        # 处理 SemanticOpcode 枚举
        if hasattr(opcode, "name"):
            opcode_name = opcode.name.upper()
        else:
            opcode_name = str(opcode).upper()

        return getattr(cls, opcode_name, 100)  # 默认 100

    @classmethod
    def get_all_costs(cls) -> dict[str, int]:
        """获取所有指令的 Gas 成本"""
        return {
            name: value
            for name, value in cls.__dict__.items()
            if not name.startswith("_") and isinstance(value, int)
        }


@dataclass
class ExecutionBudget:
    """
    执行预算

    管理 Gas 使用情况和限制
    """

    # Gas 限制
    gas_limit: int = 1000000  # 默认 100 万 Gas

    # 追踪
    gas_used: int = 0
    gas_refunded: int = 0  # 退款机制（如循环提前结束）

    # 迭代限制（兜底）
    max_iterations: int = 10000
    iteration_count: int = 0

    # 元数据
    program_id: str = ""

    @property
    def gas_remaining(self) -> int:
        """剩余 Gas"""
        return self.gas_limit - self.gas_used + self.gas_refunded

    @property
    def is_exhausted(self) -> bool:
        """Gas 是否耗尽"""
        return self.gas_remaining <= 0

    def consume(self, amount: int) -> bool:
        """
        消耗 Gas

        Args:
            amount: 消耗的 Gas 量

        Returns:
            是否成功消耗（Gas 是否足够）
        """
        if self.gas_remaining < amount:
            return False
        self.gas_used += amount
        return True

    def refund(self, amount: int) -> None:
        """
        退款 Gas（用于循环提前结束等场景）

        Args:
            amount: 退还的 Gas 量
        """
        # 退款不能超过已使用的 Gas
        refund_amount = min(amount, self.gas_used - self.gas_refunded)
        self.gas_refunded += refund_amount

    def increment_iteration(self) -> int:
        """增加迭代计数，返回当前计数"""
        self.iteration_count += 1
        return self.iteration_count

    def check_limits(self) -> tuple[bool, str]:
        """
        检查所有限制

        Returns:
            (是否通过，错误信息)
        """
        if self.is_exhausted:
            return False, f"Gas exhausted (used: {self.gas_used}, limit: {self.gas_limit})"

        if self.iteration_count >= self.max_iterations:
            return False, f"Max iterations exceeded ({self.iteration_count}/{self.max_iterations})"

        return True, ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "gas_limit": self.gas_limit,
            "gas_used": self.gas_used,
            "gas_remaining": self.gas_remaining,
            "gas_refunded": self.gas_refunded,
            "iteration_count": self.iteration_count,
            "max_iterations": self.max_iterations,
            "program_id": self.program_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionBudget:
        """从字典创建"""
        return cls(
            gas_limit=data.get("gas_limit", 1000000),
            gas_used=data.get("gas_used", 0),
            gas_refunded=data.get("gas_refunded", 0),
            max_iterations=data.get("max_iterations", 10000),
            iteration_count=data.get("iteration_count", 0),
            program_id=data.get("program_id", ""),
        )


@dataclass
class GasReceipt:
    """
    Gas 收据

    记录执行后的 Gas 使用情况
    """

    program_id: str
    gas_limit: int
    gas_used: int
    gas_remaining: int
    success: bool
    error: str = ""

    # 详细统计
    instruction_count: int = 0
    breakdown: dict[str, int] = field(default_factory=dict)  # 每类指令的 Gas 消耗

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "program_id": self.program_id,
            "gas_limit": self.gas_limit,
            "gas_used": self.gas_used,
            "gas_remaining": self.gas_remaining,
            "success": self.success,
            "error": self.error,
            "instruction_count": self.instruction_count,
            "breakdown": self.breakdown,
        }
