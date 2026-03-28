"""
双内存自修改操作系统 (Dual-Memory Self-Modifying OS)

架构灵感：
- 双内存设计：左脑（运行中）+ 右脑（升级中）
- 热切换：左脑运行时升级右脑，完成后无缝切换
- 安全回滚：切换失败可立即回退到左脑

核心设计模式：
1. A/B 内存分区
2. 影子复制（Shadow Copy）
3. 原子切换（Atomic Switch）
4. 回滚机制（Rollback）
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


class MemoryBankStatus(str, Enum):
    """内存库状态"""
    ACTIVE = "active"       # 当前运行
    STANDBY = "standby"     # 备用（正在升级）
    UPGRADING = "upgrading" # 升级中
    FAILED = "failed"       # 升级失败


@dataclass
class MemoryBank:
    """
    内存库（左脑/右脑）
    
    包含 OS 的完整状态
    """
    bank_id: str
    name: str  # "left" / "right"
    status: MemoryBankStatus = MemoryBankStatus.STANDBY
    
    # OS 状态
    instructions: dict[str, Callable] = field(default_factory=dict)
    compiler_rules: dict[str, Any] = field(default_factory=dict)
    executor_rules: dict[str, Any] = field(default_factory=dict)
    components: dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    checksum: str = ""
    
    def clone(self) -> MemoryBank:
        """深拷贝内存库"""
        return copy.deepcopy(self)
    
    def compute_checksum(self) -> str:
        """计算校验和"""
        import hashlib
        data = str({
            "instructions": list(self.instructions.keys()),
            "compiler_rules": list(self.compiler_rules.keys()),
            "executor_rules": list(self.executor_rules.keys()),
            "version": self.version,
        })
        return hashlib.md5(data.encode()).hexdigest()
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "bank_id": self.bank_id,
            "name": self.name,
            "status": self.status.value,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "checksum": self.checksum,
            "instructions_count": len(self.instructions),
            "compiler_rules_count": len(self.compiler_rules),
            "executor_rules_count": len(self.executor_rules),
        }


@dataclass
class SwitchHistory:
    """切换历史"""
    switch_id: str
    from_bank: str
    to_bank: str
    timestamp: datetime
    reason: str
    success: bool
    error: Optional[str] = None
    rolled_back: bool = False


class DualMemoryOS:
    """
    双内存自修改操作系统
    
    真正的双脑架构：
    - 左脑运行，右脑升级
    - 升级完成后原子切换
    - 失败时秒级回滚
    """
    
    def __init__(self):
        # 双内存库
        self.left_bank = MemoryBank(bank_id="left", name="left", status=MemoryBankStatus.ACTIVE)
        self.right_bank = MemoryBank(bank_id="right", name="right", status=MemoryBankStatus.STANDBY)
        
        # 当前活动的内存库
        self.active_bank: MemoryBank = self.left_bank
        
        # 切换历史
        self.switch_history: list[SwitchHistory] = []
        
        # 修改日志（用于升级）
        self.modification_log: list[dict] = []
        
        # 初始化基础指令
        self._init_base_instructions()
    
    def _init_base_instructions(self) -> None:
        """初始化基础指令"""
        def query_handler(**kwargs):
            return {"status": "queried", "params": kwargs}
        
        def create_handler(**kwargs):
            return {"status": "created", "params": kwargs}
        
        def modify_handler(**kwargs):
            return {"status": "modified", "params": kwargs}
        
        self.left_bank.instructions["QUERY"] = query_handler
        self.left_bank.instructions["CREATE"] = create_handler
        self.left_bank.instructions["MODIFY"] = modify_handler
        
        # 克隆到右脑
        self.right_bank.instructions = copy.deepcopy(self.left_bank.instructions)
    
    # =========================================================================
    # 核心 API：获取活动内存库
    # =========================================================================
    
    def get_active_bank(self) -> MemoryBank:
        """获取当前活动的内存库（正在运行的脑）"""
        return self.active_bank
    
    def get_standby_bank(self) -> MemoryBank:
        """获取备用内存库（可以安全升级的脑）"""
        return self.right_bank if self.active_bank == self.left_bank else self.left_bank
    
    # =========================================================================
    # 升级流程
    # =========================================================================
    
    def start_upgrade(self) -> MemoryBank:
        """
        开始升级
        
        Returns:
            备用内存库（可以安全修改）
        """
        standby = self.get_standby_bank()
        standby.status = MemoryBankStatus.UPGRADING
        standby.updated_at = datetime.now()
        
        return standby
    
    def upgrade_instruction(
        self,
        name: str,
        handler: Callable,
        description: str = "",
    ) -> None:
        """
        升级指令（在备用内存库中）
        
        Args:
            name: 指令名称
            handler: 指令处理函数
            description: 指令描述
        """
        standby = self.get_standby_bank()
        
        if standby.status != MemoryBankStatus.UPGRADING:
            raise RuntimeError("备用内存库未处于升级状态，请先调用 start_upgrade()")
        
        standby.instructions[name] = handler
        standby.version = self._increment_version(standby.version)
        standby.updated_at = datetime.now()
        
        self.modification_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": "upgrade_instruction",
            "target": name,
            "bank": standby.name,
        })
    
    def upgrade_compiler_rule(self, rule_name: str, new_rule: Any) -> None:
        """升级编译器规则"""
        standby = self.get_standby_bank()
        standby.compiler_rules[rule_name] = new_rule
        standby.updated_at = datetime.now()
        
        self.modification_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": "upgrade_compiler_rule",
            "target": rule_name,
            "bank": standby.name,
        })
    
    def upgrade_executor_rule(self, rule_name: str, new_rule: Any) -> None:
        """升级执行器规则"""
        standby = self.get_standby_bank()
        standby.executor_rules[rule_name] = new_rule
        standby.updated_at = datetime.now()
        
        self.modification_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": "upgrade_executor_rule",
            "target": rule_name,
            "bank": standby.name,
        })
    
    def complete_upgrade(self) -> bool:
        """
        完成升级并切换到新内存库
        
        Returns:
            是否成功
        """
        standby = self.get_standby_bank()
        old_active = self.active_bank
        
        try:
            # 1. 计算校验和
            standby.checksum = standby.compute_checksum()
            
            # 2. 验证升级
            if not self._verify_upgrade(standby):
                raise RuntimeError("升级验证失败")
            
            # 3. 原子切换
            old_active.status = MemoryBankStatus.STANDBY
            standby.status = MemoryBankStatus.ACTIVE
            self.active_bank = standby
            
            # 4. 记录历史
            self.switch_history.append(SwitchHistory(
                switch_id=str(uuid.uuid4()),
                from_bank=old_active.name,
                to_bank=standby.name,
                timestamp=datetime.now(),
                reason="upgrade_completed",
                success=True,
            ))
            
            # 5. 清理修改日志
            self.modification_log.clear()
            
            return True
            
        except Exception as e:
            # 升级失败，回滚
            self._rollback_upgrade(old_active, standby, str(e))
            return False
    
    def _verify_upgrade(self, bank: MemoryBank) -> bool:
        """
        验证升级
        
        检查点：
        1. 基础指令存在
        2. 校验和有效
        3. 无致命错误
        """
        # 检查基础指令
        required_instructions = ["QUERY", "CREATE", "MODIFY"]
        for instr in required_instructions:
            if instr not in bank.instructions:
                raise ValueError(f"缺少必需指令：{instr}")
        
        # 检查校验和
        if not bank.checksum:
            raise ValueError("校验和为空")
        
        return True
    
    def _rollback_upgrade(
        self,
        old_active: MemoryBank,
        failed_standby: MemoryBank,
        error: str,
    ) -> None:
        """回滚升级"""
        # 恢复旧状态
        old_active.status = MemoryBankStatus.ACTIVE
        failed_standby.status = MemoryBankStatus.FAILED
        self.active_bank = old_active
        
        # 记录失败
        self.switch_history.append(SwitchHistory(
            switch_id=str(uuid.uuid4()),
            from_bank=old_active.name,
            to_bank=failed_standby.name,
            timestamp=datetime.now(),
            reason="upgrade_failed",
            success=False,
            error=error,
            rolled_back=True,
        ))
        
        # 清理修改日志
        self.modification_log.clear()
    
    def _increment_version(self, version: str) -> str:
        """版本号递增"""
        parts = version.split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)
    
    # =========================================================================
    # 查询和监控
    # =========================================================================
    
    def get_status(self) -> dict[str, Any]:
        """获取系统状态"""
        return {
            "active_bank": self.active_bank.name,
            "active_version": self.active_bank.version,
            "left_bank": self.left_bank.to_dict(),
            "right_bank": self.right_bank.to_dict(),
            "switch_count": len(self.switch_history),
            "pending_modifications": len(self.modification_log),
        }
    
    def get_switch_history(self, limit: int = 10) -> list[SwitchHistory]:
        """获取切换历史"""
        return self.switch_history[-limit:]
    
    def can_switch_back(self) -> bool:
        """检查是否可以切换回备用库"""
        standby = self.get_standby_bank()
        return standby.status == MemoryBankStatus.STANDBY
    
    def force_switch(self) -> bool:
        """强制切换到备用库（用于紧急回滚）"""
        standby = self.get_standby_bank()
        old_active = self.active_bank
        
        if standby.status not in [MemoryBankStatus.STANDBY, MemoryBankStatus.ACTIVE]:
            return False
        
        # 切换
        old_active.status = MemoryBankStatus.STANDBY
        standby.status = MemoryBankStatus.ACTIVE
        self.active_bank = standby
        
        # 记录
        self.switch_history.append(SwitchHistory(
            switch_id=str(uuid.uuid4()),
            from_bank=old_active.name,
            to_bank=standby.name,
            timestamp=datetime.now(),
            reason="force_switch",
            success=True,
        ))
        
        return True


# =============================================================================
# 工厂函数
# =============================================================================


def create_dual_memory_os() -> DualMemoryOS:
    """创建双内存 OS"""
    return DualMemoryOS()


# =============================================================================
# 使用示例
# =============================================================================


async def demo_dual_memory_os():
    """演示双内存 OS"""
    # 1. 创建系统
    os = create_dual_memory_os()
    
    # 初始状态
    print(f"活动内存库：{os.active_bank.name}")
    print(f"版本：{os.active_bank.version}")
    
    # 2. 开始升级（右脑）
    standby = os.start_upgrade()
    print(f"\n开始升级：{standby.name}")
    
    # 3. 升级指令（不影响左脑运行）
    def new_ar_render(**kwargs):
        return {"status": "ar_rendered", "params": kwargs}
    
    os.upgrade_instruction("AR_RENDER", new_ar_render, "AR 渲染指令")
    os.upgrade_instruction("VR_RENDER", lambda **kw: {"status": "vr"}, "VR 渲染")
    
    # 4. 升级规则
    os.upgrade_compiler_rule("intent_parse", {"strategy": "llm_v2"})
    os.upgrade_executor_rule("task_scheduler", {"max_concurrent": 20})
    
    print(f"升级后版本：{standby.version}")
    print(f"新指令数：{len(standby.instructions)}")
    
    # 5. 验证升级（此时左脑仍在运行）
    print(f"\n左脑状态：{os.left_bank.status}")
    print(f"右脑状态：{os.right_bank.status}")
    
    # 左脑仍然可以正常处理请求
    result = os.left_bank.instructions["QUERY"](test="data")
    print(f"左脑处理请求：{result}")
    
    # 6. 完成升级并切换
    success = os.complete_upgrade()
    
    if success:
        print(f"\n✅ 升级成功！切换到：{os.active_bank.name}")
        print(f"新版本：{os.active_bank.version}")
        
        # 新指令立即可用
        result = os.active_bank.instructions["AR_RENDER"](data=[1, 2, 3])
        print(f"使用新指令：{result}")
    else:
        print(f"\n❌ 升级失败，已回滚")
    
    # 7. 查看状态
    status = os.get_status()
    print(f"\n系统状态：{status}")
    
    # 8. 查看切换历史
    history = os.get_switch_history()
    print(f"\n切换历史：{len(history)} 次")
    for h in history:
        print(f"  {h.timestamp}: {h.from_bank} → {h.to_bank} ({'✓' if h.success else '✗'})")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_dual_memory_os())
