"""
Self-Bootstrap 沙箱

提供自修改操作的隔离执行环境

设计文档：docs/private/004-bootstrap-sandbox.md
"""

from __future__ import annotations

import copy
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SandboxLevel(Enum):
    """沙箱隔离级别"""
    NONE = "none"           # 无沙箱
    MEMORY = "memory"       # 内存隔离
    PROCESS = "process"     # 进程隔离
    CONTAINER = "container" # 容器隔离


@dataclass
class SandboxConfig:
    """沙箱配置"""
    
    level: SandboxLevel = SandboxLevel.MEMORY
    max_memory_mb: int = 512
    timeout_seconds: float = 60.0
    enable_audit: bool = True
    
    @classmethod
    def strict(cls) -> SandboxConfig:
        """严格配置"""
        return cls(
            level=SandboxLevel.MEMORY,
            max_memory_mb=256,
            timeout_seconds=30.0,
        )
    
    @classmethod
    def production(cls) -> SandboxConfig:
        """生产环境配置"""
        return cls(
            level=SandboxLevel.MEMORY,
            max_memory_mb=1024,
            timeout_seconds=120.0,
        )


@dataclass
class BootstrapRecord:
    """自举记录"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action: str = ""
    target: str = ""
    old_value: Any = None
    new_value: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    executed_by: str = ""
    status: str = "pending"
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "action": self.action,
            "target": self.target,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp.isoformat(),
            "executed_by": self.executed_by,
            "status": self.status,
        }


class SandboxEnvironment:
    """
    沙箱环境
    
    提供隔离的执行环境
    """
    
    def __init__(self, config: SandboxConfig):
        self.config = config
        self._snapshot: Optional[dict] = None
        self._is_active = False
    
    async def enter(self, state: dict) -> None:
        """进入沙箱环境"""
        self._is_active = True
        
        if self.config.level == SandboxLevel.MEMORY:
            # 创建内存快照
            self._snapshot = copy.deepcopy(state)
        
        logger.debug(f"进入沙箱环境 (级别：{self.config.level})")
    
    async def exit(self, commit: bool = False) -> Optional[dict]:
        """退出沙箱环境"""
        self._is_active = False
        
        if not commit and self._snapshot:
            # 丢弃更改
            logger.debug("退出沙箱，丢弃更改")
        
        snapshot = self._snapshot
        self._snapshot = None
        return snapshot
    
    def execute_in_sandbox(self, action: str, state: dict, new_value: Any) -> dict:
        """在沙箱内执行操作"""
        if not self._is_active:
            raise RuntimeError("沙箱未激活")
        
        # 在副本上执行
        test_state = copy.deepcopy(state)
        
        # 模拟执行
        if action == "modify_prompt":
            test_state["prompts"] = new_value
        elif action == "modify_config":
            test_state["configs"] = new_value
        elif action == "define_instruction":
            test_state["instructions"] = new_value
        
        return test_state


class BootstrapValidator:
    """
    Self-Bootstrap 验证器
    
    验证自修改操作的安全性
    """
    
    FORBIDDEN_PATTERNS = [
        r"delete_all",
        r"drop.*\*",
        r"ignore.*security",
        r"bypass.*auth",
        r"disable.*audit",
    ]
    
    HIGH_RISK_ACTIONS = [
        "modify_processor",
        "delete_policy",
        "define_instruction",
        "modify_audit_rules",
    ]
    
    def __init__(self):
        pass
    
    def validate(
        self,
        action: str,
        target: str,
        new_value: Any,
    ) -> ValidationResult:
        """验证自修改操作"""
        errors = []
        warnings = []
        risk_score = 0.0
        
        # 基础验证
        if not action:
            errors.append("操作类型不能为空")
        
        if not target:
            errors.append("修改目标不能为空")
        
        # 检查禁止模式
        combined = f"{action} {target} {new_value}".lower()
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern.lower() in combined:
                errors.append(f"包含禁止的模式：{pattern}")
                risk_score = min(1.0, risk_score + 0.5)
        
        # 高风险操作警告
        if action in self.HIGH_RISK_ACTIONS:
            warnings.append(f"高风险操作：{action}")
            risk_score = min(1.0, risk_score + 0.3)
        
        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            risk_score=risk_score,
        )
    
    def requires_approval(self, action: str, target: str, new_value: Any) -> bool:
        """检查是否需要人工审批"""
        combined = f"{action} {target} {new_value}".lower()
        
        approval_patterns = [
            "modify.*processor",
            "delete.*policy",
            "modify.*security",
        ]
        
        import re
        for pattern in approval_patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                return True
        
        return False


@dataclass
class ValidationResult:
    """验证结果"""
    
    passed: bool
    errors: list[str]
    warnings: list[str]
    risk_score: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "risk_score": self.risk_score,
        }


class RollbackManager:
    """
    回滚管理器
    
    管理版本快照和回滚操作
    """
    
    def __init__(self, max_snapshots: int = 10):
        self.max_snapshots = max_snapshots
        self._snapshots: list[dict] = []
    
    def create_snapshot(
        self,
        state: dict,
        description: str = "",
    ) -> str:
        """创建快照"""
        snapshot_id = str(uuid.uuid4())[:8]
        
        snapshot = {
            "id": snapshot_id,
            "timestamp": datetime.now(),
            "description": description,
            "state": copy.deepcopy(state),
        }
        
        self._snapshots.append(snapshot)
        
        # 限制快照数量
        if len(self._snapshots) > self.max_snapshots:
            self._snapshots.pop(0)
        
        logger.info(f"创建快照：{snapshot_id} ({description})")
        return snapshot_id
    
    def restore_snapshot(
        self,
        snapshot_id: str,
        current_state: dict,
    ) -> bool:
        """恢复快照"""
        for snapshot in self._snapshots:
            if snapshot["id"] == snapshot_id:
                # 恢复数据
                current_state.clear()
                current_state.update(copy.deepcopy(snapshot["state"]))
                
                logger.info(f"恢复快照：{snapshot_id}")
                return True
        
        logger.error(f"快照不存在：{snapshot_id}")
        return False
    
    def get_latest_snapshot(self) -> Optional[dict]:
        """获取最新快照"""
        if self._snapshots:
            return self._snapshots[-1]
        return None
    
    def list_snapshots(self) -> list[dict]:
        """列出所有快照"""
        return [
            {
                "id": s["id"],
                "timestamp": s["timestamp"].isoformat(),
                "description": s["description"],
            }
            for s in self._snapshots
        ]


class SelfBootstrapExecutor:
    """
    Self-Bootstrap 执行器
    
    执行自修改操作的核心组件
    """
    
    def __init__(
        self,
        sandbox_config: Optional[SandboxConfig] = None,
    ):
        self.sandbox = SandboxEnvironment(sandbox_config or SandboxConfig.strict())
        self.validator = BootstrapValidator()
        self.rollback_manager = RollbackManager()
        self.records: list[BootstrapRecord] = []
    
    async def execute_bootstrap(
        self,
        action: str,
        target: str,
        new_value: Any,
        state: dict,
        program_id: str = "",
    ) -> BootstrapRecord:
        """执行自举操作"""
        record = BootstrapRecord(
            action=action,
            target=target,
            new_value=new_value,
            executed_by=program_id,
        )
        
        try:
            # 1. 验证操作
            validation = self.validator.validate(action, target, new_value)
            if not validation.passed:
                record.status = "rejected"
                record.old_value = f"验证失败：{', '.join(validation.errors)}"
                return record
            
            # 2. 检查是否需要审批
            if self.validator.requires_approval(action, target, new_value):
                record.status = "pending_approval"
                return record
            
            # 3. 创建快照
            snapshot_id = self.rollback_manager.create_snapshot(
                state,
                description=f"Before {action} on {target}",
            )
            
            # 4. 在沙箱中测试
            await self.sandbox.enter(state)
            try:
                test_state = self.sandbox.execute_in_sandbox(
                    action, state, new_value
                )
                
                # 沙箱测试通过
                await self.sandbox.exit(commit=False)
                
            except Exception as e:
                await self.sandbox.exit(commit=False)
                record.status = "failed"
                record.old_value = f"沙箱测试失败：{e}"
                return record
            
            # 5. 应用修改
            self._apply_bootstrap(action, target, new_value, state)
            
            record.status = "completed"
            record.old_value = snapshot_id
            
        except Exception as e:
            record.status = "failed"
            record.old_value = f"执行异常：{e}"
            
            # 自动回滚
            latest_snapshot = self.rollback_manager.get_latest_snapshot()
            if latest_snapshot:
                self.rollback_manager.restore_snapshot(
                    latest_snapshot["id"], state
                )
        
        self.records.append(record)
        return record
    
    def _apply_bootstrap(
        self,
        action: str,
        target: str,
        new_value: Any,
        state: dict,
    ) -> None:
        """应用自修改"""
        if action == "modify_prompt":
            state["prompts"] = new_value
        elif action == "modify_config":
            state["configs"] = new_value
        elif action == "define_instruction":
            if "instructions" not in state:
                state["instructions"] = {}
            state["instructions"][target] = new_value
        elif action == "delete_policy":
            if "policies" in state and target in state["policies"]:
                del state["policies"][target]
    
    async def rollback(self, snapshot_id: str, state: dict) -> bool:
        """手动回滚到指定快照"""
        return self.rollback_manager.restore_snapshot(snapshot_id, state)
    
    def list_snapshots(self) -> list[dict]:
        """列出所有快照"""
        return self.rollback_manager.list_snapshots()
