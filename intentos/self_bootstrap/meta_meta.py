"""
元元意图 (Meta-Meta-Intent)

Self-Bootstrap 的最高层级：
- L0: 任务意图 → 执行任务
- L1: 元意图 → 管理系统
- L2: 元元意图 → 管理元意图（自修改的自修改）

核心洞察：
只有 LLM 作为处理器，元元意图才能实现。
因为元元意图需要修改"解析规则"，而解析规则在 Prompt 中（可修改）。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
from datetime import datetime
import uuid

# 导入基础类型
from . import MetaIntent, MetaAction, TargetType


# =============================================================================
# 元元意图层级
# =============================================================================

class IntentLevel(Enum):
    """意图层级"""
    L0_TASK = "l0_task"           # 任务意图：执行任务
    L1_META = "l1_meta"           # 元意图：管理系统
    L2_META_META = "l2_meta_meta" # 元元意图：管理元意图


# =============================================================================
# 元元意图数据结构
# =============================================================================

@dataclass
class MetaMetaIntent:
    """
    元元意图：管理元意图的意图
    
    示例：
    ```python
    # 修改元意图的解析规则
    meta_meta = MetaMetaIntent(
        action=MetaAction.MODIFY,
        target_type=MetaTargetType.META_PARSER,
        target_id="META_PARSER_PROMPT",
        parameters={
            "new_prompt": "...",
        },
    )
    
    # 修改 Self-Bootstrap 的验证规则
    meta_meta = MetaMetaIntent(
        action=MetaAction.MODIFY,
        target_type=MetaTargetType.SELF_BOOTSTRAP_POLICY,
        parameters={
            "allow_self_modification": True,
            "require_approval_for": ["delete_all_templates"],
        },
    )
    ```
    """
    
    # 元元意图动作
    action: MetaAction
    
    # 元元意图目标类型
    target_type: MetaTargetType
    
    # 目标标识
    target_id: Optional[str] = None
    
    # 操作参数
    parameters: dict[str, Any] = field(default_factory=dict)
    
    # 执行约束
    constraints: dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    level: IntentLevel = IntentLevel.L2_META_META
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    
    # 父意图（用于追踪）
    parent_intent_id: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "level": self.level.value,
            "action": self.action.value,
            "target_type": self.target_type.value,
            "target_id": self.target_id,
            "parameters": self.parameters,
            "constraints": self.constraints,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "parent_intent_id": self.parent_intent_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MetaMetaIntent:
        """从字典创建"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            level=IntentLevel(data.get("level", "l2_meta_meta")),
            action=MetaAction(data["action"]),
            target_type=MetaTargetType(data["target_type"]),
            target_id=data.get("target_id"),
            parameters=data.get("parameters", {}),
            constraints=data.get("constraints", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            created_by=data.get("created_by"),
            parent_intent_id=data.get("parent_intent_id"),
        )
    
    def validate(self) -> list[str]:
        """验证元元意图有效性"""
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
        
        return errors
    
    def to_meta_intent(self) -> MetaIntent:
        """
        转换为元意图
        
        元元意图最终需要转换为元意图来执行
        """
        return MetaIntent(
            action=self.action,
            target_type=TargetType(self.target_type.value),
            target_id=self.target_id,
            parameters=self.parameters,
            constraints=self.constraints,
            created_by=self.created_by,
        )


# =============================================================================
# 元元意图目标类型
# =============================================================================

class MetaTargetType(Enum):
    """元元意图的目标类型"""
    
    # 修改解析规则
    META_PARSER = "meta_parser"           # 元意图解析器
    META_PARSER_PROMPT = "meta_parser_prompt"  # 解析 Prompt
    
    # 修改 Self-Bootstrap 规则
    SELF_BOOTSTRAP_POLICY = "self_bootstrap_policy"  # Self-Bootstrap 策略
    META_ACTION_TYPES = "meta_action_types"  # 元动作类型
    META_TARGET_TYPES = "meta_target_types"  # 元目标类型
    
    # 修改系统配置
    SYSTEM_CONFIG = "system_config"       # 系统配置
    PERMISSION_LEVELS = "permission_levels"  # 权限级别
    AUDIT_RULES = "audit_rules"           # 审计规则
    
    # 修改编译器配置
    COMPILER_CONFIG = "compiler_config"   # 编译器配置
    CODE_GENERATOR_TEMPLATES = "code_generator_templates"  # 代码生成模板


# =============================================================================
# 元元意图执行器
# =============================================================================

@dataclass
class MetaMetaResult:
    """元元意图执行结果"""
    
    success: bool
    result: Any = None
    error: Optional[str] = None
    audit_id: Optional[str] = None
    changes_applied: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "audit_id": self.audit_id,
            "changes_applied": self.changes_applied,
        }


class MetaMetaExecutor:
    """
    元元意图执行器
    
    执行元元意图，实现"自修改的自修改"
    """
    
    def __init__(
        self,
        system_config: dict[str, Any],
        audit_logger: Any = None,
    ):
        self.system_config = system_config
        self.audit_logger = audit_logger
    
    async def execute(
        self,
        meta_meta: MetaMetaIntent,
        context: dict[str, Any],
    ) -> MetaMetaResult:
        """
        执行元元意图
        
        Args:
            meta_meta: 元元意图
            context: 执行上下文
        
        Returns:
            执行结果
        """
        changes_applied = []
        audit_id = None
        
        try:
            # 1. 验证元元意图
            errors = meta_meta.validate()
            if errors:
                return MetaMetaResult(
                    success=False,
                    error="; ".join(errors),
                )
            
            # 2. 检查权限 (元元意图需要高级权限)
            if not self._check_permission(context, meta_meta):
                return MetaMetaResult(
                    success=False,
                    error="权限不足：需要 super_admin 权限",
                )
            
            # 3. 执行元元意图
            if meta_meta.target_type == MetaTargetType.META_PARSER_PROMPT:
                # 修改元意图解析 Prompt
                result = await self._modify_meta_parser_prompt(meta_meta, context)
                changes_applied.append("Modified META_PARSER_PROMPT")
            
            elif meta_meta.target_type == MetaTargetType.SELF_BOOTSTRAP_POLICY:
                # 修改 Self-Bootstrap 策略
                result = await self._modify_self_bootstrap_policy(meta_meta, context)
                changes_applied.append("Modified SELF_BOOTSTRAP_POLICY")
            
            elif meta_meta.target_type == MetaTargetType.META_ACTION_TYPES:
                # 修改元动作类型
                result = await self._modify_meta_action_types(meta_meta, context)
                changes_applied.append("Modified META_ACTION_TYPES")
            
            elif meta_meta.target_type == MetaTargetType.SYSTEM_CONFIG:
                # 修改系统配置
                result = await self._modify_system_config(meta_meta, context)
                changes_applied.append("Modified SYSTEM_CONFIG")
            
            else:
                return MetaMetaResult(
                    success=False,
                    error=f"不支持的目标类型：{meta_meta.target_type.value}",
                )
            
            # 4. 记录审计日志
            audit_id = await self._log_audit(
                action="execute_meta_meta",
                target_type=meta_meta.target_type.value,
                target_id=meta_meta.target_id,
                context=context,
                parameters=meta_meta.parameters,
                result="success",
                changes=changes_applied,
            )
            
            return MetaMetaResult(
                success=True,
                result=result,
                audit_id=audit_id,
                changes_applied=changes_applied,
            )
            
        except Exception as e:
            # 记录失败审计
            audit_id = await self._log_audit(
                action="execute_meta_meta",
                target_type=meta_meta.target_type.value,
                target_id=meta_meta.target_id,
                context=context,
                parameters=meta_meta.parameters,
                result="failed",
                error=str(e),
            )
            
            return MetaMetaResult(
                success=False,
                error=str(e),
                audit_id=audit_id,
            )
    
    def _check_permission(self, context: dict, meta_meta: MetaMetaIntent) -> bool:
        """检查权限"""
        # 元元意图需要 super_admin 权限
        user_role = context.get("user_role", "")
        permissions = context.get("permissions", [])
        
        return user_role == "super_admin" or "super_admin" in permissions
    
    async def _modify_meta_parser_prompt(
        self,
        meta_meta: MetaMetaIntent,
        context: dict,
    ) -> dict[str, Any]:
        """修改元意图解析 Prompt"""
        new_prompt = meta_meta.parameters.get("new_prompt")
        
        if not new_prompt:
            raise ValueError("需要提供 new_prompt 参数")
        
        # 更新系统配置中的解析 Prompt
        old_prompt = self.system_config.get("META_PARSER_PROMPT", "")
        self.system_config["META_PARSER_PROMPT"] = new_prompt
        
        return {
            "action": "modify_meta_parser_prompt",
            "old_prompt": old_prompt[:100] + "..." if len(old_prompt) > 100 else old_prompt,
            "new_prompt": new_prompt[:100] + "..." if len(new_prompt) > 100 else new_prompt,
        }
    
    async def _modify_self_bootstrap_policy(
        self,
        meta_meta: MetaMetaIntent,
        context: dict,
    ) -> dict[str, Any]:
        """修改 Self-Bootstrap 策略"""
        new_policy = meta_meta.parameters.get("policy")
        
        if not new_policy:
            raise ValueError("需要提供 policy 参数")
        
        # 更新系统配置中的策略
        old_policy = self.system_config.get("SELF_BOOTSTRAP_POLICY", {})
        self.system_config["SELF_BOOTSTRAP_POLICY"] = {**old_policy, **new_policy}
        
        return {
            "action": "modify_self_bootstrap_policy",
            "old_policy": old_policy,
            "new_policy": self.system_config["SELF_BOOTSTRAP_POLICY"],
        }
    
    async def _modify_meta_action_types(
        self,
        meta_meta: MetaMetaIntent,
        context: dict,
    ) -> dict[str, Any]:
        """修改元动作类型"""
        new_actions = meta_meta.parameters.get("new_actions", [])
        
        # 动态扩展 MetaAction (简化实现，实际应该修改枚举)
        current_actions = self.system_config.get("META_ACTIONS", ["CREATE", "MODIFY", "DELETE", "QUERY"])
        
        for action in new_actions:
            if action not in current_actions:
                current_actions.append(action)
        
        self.system_config["META_ACTIONS"] = current_actions
        
        return {
            "action": "modify_meta_action_types",
            "added_actions": new_actions,
            "current_actions": current_actions,
        }
    
    async def _modify_system_config(
        self,
        meta_meta: MetaMetaIntent,
        context: dict,
    ) -> dict[str, Any]:
        """修改系统配置"""
        new_config = meta_meta.parameters.get("config")
        
        if not new_config:
            raise ValueError("需要提供 config 参数")
        
        # 更新系统配置
        old_config = self.system_config.copy()
        self.system_config.update(new_config)
        
        return {
            "action": "modify_system_config",
            "changes": new_config,
        }
    
    async def _log_audit(
        self,
        action: str,
        target_type: str,
        target_id: Optional[str],
        context: dict,
        parameters: dict,
        result: str,
        error: Optional[str] = None,
        changes: list[str] = None,
    ) -> str:
        """记录审计日志"""
        audit_id = str(uuid.uuid4())
        
        audit_record = {
            "id": audit_id,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "user_id": context.get("user_id"),
            "user_role": context.get("user_role"),
            "parameters": parameters,
            "result": result,
            "error": error,
            "changes": changes or [],
            "timestamp": datetime.now().isoformat(),
            "level": "meta_meta",
        }
        
        # 存储审计日志 (简化实现)
        if self.audit_logger:
            await self.audit_logger.log(audit_record)
        else:
            # 存储到系统配置 (简化)
            if "AUDIT_LOG" not in self.system_config:
                self.system_config["AUDIT_LOG"] = []
            self.system_config["AUDIT_LOG"].append(audit_record)
        
        return audit_id


# =============================================================================
# 导入 (避免循环依赖)
# =============================================================================

# 延迟导入，避免循环依赖
def __getattr__(name: str):
    if name == "MetaIntent":
        from . import MetaIntent
        return MetaIntent
    elif name == "MetaAction":
        from . import MetaAction
        return MetaAction
    elif name == "TargetType":
        from . import TargetType
        return TargetType
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# =============================================================================
# 便捷函数
# =============================================================================

def create_meta_meta_intent(
    action: MetaAction,
    target_type: MetaTargetType,
    target_id: Optional[str] = None,
    **parameters,
) -> MetaMetaIntent:
    """便捷函数：创建元元意图"""
    return MetaMetaIntent(
        action=action,
        target_type=target_type,
        target_id=target_id,
        parameters=parameters,
    )


async def execute_meta_meta(
    executor: MetaMetaExecutor,
    action: MetaAction,
    target_type: MetaTargetType,
    context: dict,
    **parameters,
) -> MetaMetaResult:
    """便捷函数：执行元元意图"""
    meta_meta = create_meta_meta_intent(action, target_type, **parameters)
    return await executor.execute(meta_meta, context)
