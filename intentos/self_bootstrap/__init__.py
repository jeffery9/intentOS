"""
Self-Bootstrap 内核

IntentOS 的 Self-Bootstrap 能力：
- 元意图 DSL：管理意图的意图
- 系统自省：查询自身状态
- 系统自修改：创建/修改/删除自身组件
- 安全边界：权限/审计/回滚
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
from datetime import datetime
import uuid


# =============================================================================
# 元意图 DSL (Meta-Intent DSL)
# =============================================================================

class MetaAction(Enum):
    """元意图动作"""
    CREATE = "create"     # 创建
    MODIFY = "modify"     # 修改
    DELETE = "delete"     # 删除
    QUERY = "query"       # 查询


class TargetType(Enum):
    """管理目标类型"""
    TEMPLATE = "template"         # 意图模板
    CAPABILITY = "capability"     # 能力
    POLICY = "policy"             # 策略
    CONFIG = "config"             # 配置


@dataclass
class MetaIntent:
    """
    元意图：管理意图的意图
    
    示例:
    ```python
    # 创建意图模板
    meta = MetaIntent(
        action=MetaAction.CREATE,
        target_type=TargetType.TEMPLATE,
        parameters={
            "name": "sales_analysis",
            "template": {...},
        },
    )
    
    # 修改执行策略
    meta = MetaIntent(
        action=MetaAction.MODIFY,
        target_type=TargetType.POLICY,
        target_id="sales_analysis",
        parameters={
            "timeout_seconds": 600,
        },
    )
    
    # 查询意图模板
    meta = MetaIntent(
        action=MetaAction.QUERY,
        target_type=TargetType.TEMPLATE,
        parameters={
            "tags": ["sales"],
        },
    )
    ```
    """
    
    # 元意图动作
    action: MetaAction
    
    # 管理目标类型
    target_type: TargetType
    
    # 目标标识 (MODIFY/DELETE 时必需)
    target_id: Optional[str] = None
    
    # 操作参数
    parameters: dict[str, Any] = field(default_factory=dict)
    
    # 执行约束
    constraints: dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None  # user_id
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "action": self.action.value,
            "target_type": self.target_type.value,
            "target_id": self.target_id,
            "parameters": self.parameters,
            "constraints": self.constraints,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MetaIntent:
        """从字典创建"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            action=MetaAction(data["action"]),
            target_type=TargetType(data["target_type"]),
            target_id=data.get("target_id"),
            parameters=data.get("parameters", {}),
            constraints=data.get("constraints", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            created_by=data.get("created_by"),
        )
    
    def validate(self) -> list[str]:
        """验证元意图有效性"""
        errors = []
        
        # 检查必填字段
        if not self.action:
            errors.append("缺少 action")
        
        if not self.target_type:
            errors.append("缺少 target_type")
        
        # MODIFY/DELETE 需要 target_id
        if self.action in [MetaAction.MODIFY, MetaAction.DELETE]:
            if not self.target_id:
                errors.append(f"{self.action.value} 操作需要 target_id")
        
        # CREATE 需要 parameters
        if self.action == MetaAction.CREATE:
            if not self.parameters:
                errors.append("CREATE 操作需要 parameters")
            if "name" not in self.parameters and self.target_type != TargetType.POLICY:
                errors.append("CREATE 操作需要 parameters.name")
        
        return errors


# =============================================================================
# 权限级别
# =============================================================================

class PermissionLevel(Enum):
    """权限级别"""
    READ = "read"              # 只读：查询
    WRITE = "write"            # 创建/修改：创建模板、修改普通配置
    ADMIN = "admin"            # 删除/策略：删除模板、修改策略
    SUPER_ADMIN = "super_admin" # 系统级：回滚、系统配置


# =============================================================================
# 审计日志
# =============================================================================

@dataclass
class AuditRecord:
    """审计记录"""
    
    # 操作信息
    action: str                    # 操作类型 (create_template, update_policy, ...)
    target_type: TargetType        # 目标类型
    target_id: Optional[str]       # 目标 ID
    
    # 用户信息
    user_id: str                   # 用户 ID
    user_role: str                 # 用户角色
    
    # 操作详情
    parameters: dict[str, Any]     # 操作参数
    result: str                    # 结果 (success/failed)
    error: Optional[str] = None    # 错误信息
    
    # 时间戳
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "action": self.action,
            "target_type": self.target_type.value,
            "target_id": self.target_id,
            "user_id": self.user_id,
            "user_role": self.user_role,
            "parameters": self.parameters,
            "result": self.result,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditRecord:
        """从字典创建"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            action=data["action"],
            target_type=TargetType(data["target_type"]),
            target_id=data.get("target_id"),
            user_id=data["user_id"],
            user_role=data["user_role"],
            parameters=data.get("parameters", {}),
            result=data["result"],
            error=data.get("error"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
        )


# =============================================================================
# 系统检查点 (用于回滚)
# =============================================================================

@dataclass
class SystemCheckpoint:
    """系统检查点"""
    
    # 检查点信息
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    
    # 系统快照
    templates_snapshot: dict[str, Any] = field(default_factory=dict)
    capabilities_snapshot: dict[str, Any] = field(default_factory=dict)
    policies_snapshot: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "created_by": self.created_by,
            "templates_snapshot": self.templates_snapshot,
            "capabilities_snapshot": self.capabilities_snapshot,
            "policies_snapshot": self.policies_snapshot,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SystemCheckpoint:
        """从字典创建"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            created_by=data.get("created_by"),
            templates_snapshot=data.get("templates_snapshot", {}),
            capabilities_snapshot=data.get("capabilities_snapshot", {}),
            policies_snapshot=data.get("policies_snapshot", {}),
        )


# =============================================================================
# 执行结果
# =============================================================================

@dataclass
class MetaResult:
    """元意图执行结果"""
    
    success: bool
    result: Any = None
    error: Optional[str] = None
    audit_id: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "audit_id": self.audit_id,
        }


@dataclass
class CreateResult(MetaResult):
    """创建操作结果"""
    created_id: Optional[str] = None


@dataclass
class UpdateResult(MetaResult):
    """更新操作结果"""
    pass


@dataclass
class DeleteResult(MetaResult):
    """删除操作结果"""
    pass


@dataclass
class QueryResult(MetaResult):
    """查询操作结果"""
    data: Any = None
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["data"] = self.data
        return d
