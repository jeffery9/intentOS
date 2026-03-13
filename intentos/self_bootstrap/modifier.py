"""
系统自修改

系统修改自身的能力：
- 创建意图模板
- 修改执行策略
- 注册新能力
- 删除组件
"""

from __future__ import annotations
from typing import Any, Optional, TYPE_CHECKING, Callable
from datetime import datetime
import uuid

from . import (
    MetaIntent,
    MetaAction,
    TargetType,
    MetaResult,
    CreateResult,
    UpdateResult,
    DeleteResult,
    AuditRecord,
)

if TYPE_CHECKING:
    from . import IntentRegistry, ExecutionEngine, Context


class SystemSelfModification:
    """
    系统自修改
    
    提供修改系统自身的能力
    """
    
    def __init__(
        self,
        registry: IntentRegistry,
        engine: ExecutionEngine,
    ):
        self.registry = registry
        self.engine = engine
    
    # =========================================================================
    # 创建意图模板
    # =========================================================================
    
    async def create_template(
        self,
        name: str,
        template_data: dict[str, Any],
        context: Context,
    ) -> CreateResult:
        """
        创建新意图模板
        
        Args:
            name: 模板名称
            template_data: 模板数据
            context: 执行上下文
        
        Returns:
            创建结果
        """
        audit_id = None
        
        try:
            # 1. 检查名称冲突
            existing = self.registry.get_template(name)
            if existing:
                return CreateResult(
                    success=False,
                    error=f"模板已存在：{name}",
                )
            
            # 2. 从数据创建模板对象
            from intentos import IntentTemplate, IntentType
            
            template = IntentTemplate(
                name=name,
                description=template_data.get("description", ""),
                intent_type=IntentType(template_data.get("intent_type", "composite")),
                params_schema=template_data.get("params_schema", {}),
                steps=template_data.get("steps", []),
                constraints=template_data.get("constraints", {}),
                required_permissions=template_data.get("required_permissions", []),
                version=template_data.get("version", "1.0.0"),
                tags=template_data.get("tags", []),
            )
            
            # 3. 注册模板
            self.registry.register_template(template)
            
            # 4. 记录审计日志
            audit_id = await self._log_audit(
                action="create_template",
                target_type=TargetType.TEMPLATE,
                target_id=name,
                context=context,
                parameters={"name": name, **template_data},
                result="success",
            )
            
            return CreateResult(
                success=True,
                created_id=name,
                audit_id=audit_id,
            )
            
        except Exception as e:
            # 记录失败审计
            audit_id = await self._log_audit(
                action="create_template",
                target_type=TargetType.TEMPLATE,
                target_id=name,
                context=context,
                parameters={"name": name, **template_data},
                result="failed",
                error=str(e),
            )
            
            return CreateResult(
                success=False,
                error=str(e),
                audit_id=audit_id,
            )
    
    # =========================================================================
    # 修改执行策略
    # =========================================================================
    
    async def update_policy(
        self,
        intent_type: str,
        policy: dict[str, Any],
        context: Context,
    ) -> UpdateResult:
        """
        修改执行策略
        
        Args:
            intent_type: 意图类型
            policy: 新策略
            context: 执行上下文
        
        Returns:
            更新结果
        """
        audit_id = None
        
        try:
            # 1. 验证策略有效性
            errors = self._validate_policy(policy)
            if errors:
                return UpdateResult(
                    success=False,
                    error="; ".join(errors),
                )
            
            # 2. 更新策略 (这里简化实现，实际应该存储到策略注册表)
            # 实际实现应该更新 engine 的策略配置
            
            # 3. 记录审计日志
            audit_id = await self._log_audit(
                action="update_policy",
                target_type=TargetType.POLICY,
                target_id=intent_type,
                context=context,
                parameters={"intent_type": intent_type, "policy": policy},
                result="success",
            )
            
            return UpdateResult(
                success=True,
                audit_id=audit_id,
            )
            
        except Exception as e:
            audit_id = await self._log_audit(
                action="update_policy",
                target_type=TargetType.POLICY,
                target_id=intent_type,
                context=context,
                parameters={"intent_type": intent_type, "policy": policy},
                result="failed",
                error=str(e),
            )
            
            return UpdateResult(
                success=False,
                error=str(e),
                audit_id=audit_id,
            )
    
    def _validate_policy(self, policy: dict[str, Any]) -> list[str]:
        """验证策略有效性"""
        errors = []
        
        # 检查超时时间
        if "timeout_seconds" in policy:
            if not isinstance(policy["timeout_seconds"], (int, float)):
                errors.append("timeout_seconds 必须是数字")
            elif policy["timeout_seconds"] <= 0:
                errors.append("timeout_seconds 必须大于 0")
        
        # 检查重试次数
        if "retry_count" in policy:
            if not isinstance(policy["retry_count"], int):
                errors.append("retry_count 必须是整数")
            elif policy["retry_count"] < 0:
                errors.append("retry_count 必须 >= 0")
        
        return errors
    
    # =========================================================================
    # 注册新能力
    # =========================================================================
    
    async def register_capability(
        self,
        name: str,
        capability_data: dict[str, Any],
        context: Context,
    ) -> CreateResult:
        """
        注册新能力
        
        Args:
            name: 能力名称
            capability_data: 能力数据
            context: 执行上下文
        
        Returns:
            注册结果
        """
        audit_id = None
        
        try:
            # 1. 检查名称冲突
            existing = self.registry.get_capability(name)
            if existing:
                return CreateResult(
                    success=False,
                    error=f"能力已存在：{name}",
                )
            
            # 2. 从数据创建能力对象
            from intentos import Capability
            
            # 需要 func 参数
            if "func" not in capability_data:
                return CreateResult(
                    success=False,
                    error="注册能力需要提供 func 参数",
                )
            
            func = capability_data["func"]
            
            # 如果是字符串，尝试从已注册函数中查找
            if isinstance(func, str):
                # 这里简化处理，实际应该从函数注册表中查找
                return CreateResult(
                    success=False,
                    error=f"未找到函数：{func}",
                )
            
            capability = Capability(
                name=name,
                description=capability_data.get("description", ""),
                input_schema=capability_data.get("input_schema", {}),
                output_schema=capability_data.get("output_schema", {}),
                func=func,
                requires_permissions=capability_data.get("requires_permissions", []),
                tags=capability_data.get("tags", []),
            )
            
            # 3. 注册能力
            self.registry.register_capability(capability)
            
            # 4. 记录审计日志
            audit_id = await self._log_audit(
                action="register_capability",
                target_type=TargetType.CAPABILITY,
                target_id=name,
                context=context,
                parameters={"name": name, **capability_data},
                result="success",
            )
            
            return CreateResult(
                success=True,
                created_id=name,
                audit_id=audit_id,
            )
            
        except Exception as e:
            audit_id = await self._log_audit(
                action="register_capability",
                target_type=TargetType.CAPABILITY,
                target_id=name,
                context=context,
                parameters={"name": name, **capability_data},
                result="failed",
                error=str(e),
            )
            
            return CreateResult(
                success=False,
                error=str(e),
                audit_id=audit_id,
            )
    
    # =========================================================================
    # 删除组件
    # =========================================================================
    
    async def delete_template(
        self,
        name: str,
        context: Context,
    ) -> DeleteResult:
        """
        删除意图模板
        
        Args:
            name: 模板名称
            context: 执行上下文
        
        Returns:
            删除结果
        """
        audit_id = None
        
        try:
            # 1. 检查模板是否存在
            existing = self.registry.get_template(name)
            if not existing:
                return DeleteResult(
                    success=False,
                    error=f"模板不存在：{name}",
                )
            
            # 2. 删除模板
            self.registry.remove_template(name)
            
            # 3. 记录审计日志
            audit_id = await self._log_audit(
                action="delete_template",
                target_type=TargetType.TEMPLATE,
                target_id=name,
                context=context,
                parameters={"name": name},
                result="success",
            )
            
            return DeleteResult(
                success=True,
                audit_id=audit_id,
            )
            
        except Exception as e:
            audit_id = await self._log_audit(
                action="delete_template",
                target_type=TargetType.TEMPLATE,
                target_id=name,
                context=context,
                parameters={"name": name},
                result="failed",
                error=str(e),
            )
            
            return DeleteResult(
                success=False,
                error=str(e),
                audit_id=audit_id,
            )
    
    async def delete_capability(
        self,
        name: str,
        context: Context,
    ) -> DeleteResult:
        """
        删除能力
        
        Args:
            name: 能力名称
            context: 执行上下文
        
        Returns:
            删除结果
        """
        audit_id = None
        
        try:
            # 1. 检查能力是否存在
            existing = self.registry.get_capability(name)
            if not existing:
                return DeleteResult(
                    success=False,
                    error=f"能力不存在：{name}",
                )
            
            # 2. 删除能力
            self.registry.remove_capability(name)
            
            # 3. 记录审计日志
            audit_id = await self._log_audit(
                action="delete_capability",
                target_type=TargetType.CAPABILITY,
                target_id=name,
                context=context,
                parameters={"name": name},
                result="success",
            )
            
            return DeleteResult(
                success=True,
                audit_id=audit_id,
            )
            
        except Exception as e:
            audit_id = await self._log_audit(
                action="delete_capability",
                target_type=TargetType.CAPABILITY,
                target_id=name,
                context=context,
                parameters={"name": name},
                result="failed",
                error=str(e),
            )
            
            return DeleteResult(
                success=False,
                error=str(e),
                audit_id=audit_id,
            )
    
    # =========================================================================
    # 审计日志
    # =========================================================================
    
    async def _log_audit(
        self,
        action: str,
        target_type: TargetType,
        target_id: Optional[str],
        context: Context,
        parameters: dict[str, Any],
        result: str,
        error: Optional[str] = None,
    ) -> str:
        """记录审计日志"""
        audit = AuditRecord(
            action=action,
            target_type=target_type,
            target_id=target_id,
            user_id=context.user_id,
            user_role=context.user_role,
            parameters=parameters,
            result=result,
            error=error,
        )
        
        # 存储到记忆系统 (简化实现，实际应该使用 AuditLogger)
        # await self.audit_logger.log(audit)
        
        return audit.id


# =============================================================================
# 便捷函数
# =============================================================================

async def create_template(
    modifier: SystemSelfModification,
    name: str,
    template_data: dict,
    context: Context,
) -> CreateResult:
    """便捷函数：创建模板"""
    return await modifier.create_template(name, template_data, context)


async def update_policy(
    modifier: SystemSelfModification,
    intent_type: str,
    policy: dict,
    context: Context,
) -> UpdateResult:
    """便捷函数：更新策略"""
    return await modifier.update_policy(intent_type, policy, context)


async def register_capability(
    modifier: SystemSelfModification,
    name: str,
    capability_data: dict,
    context: Context,
) -> CreateResult:
    """便捷函数：注册能力"""
    return await modifier.register_capability(name, capability_data, context)
