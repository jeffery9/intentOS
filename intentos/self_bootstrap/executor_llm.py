"""
元元意图执行器 (LLM 驱动版本)

核心理念:
- 元意图处理 → 交给 LLM
- 元元意图处理 → 交给 LLM
- IntentOS 只负责：验证 + 执行 LLM 决定的操作

架构原则:
1. 执行逻辑在 Prompt 中 (非硬编码)
2. LLM 决定如何执行
3. IntentOS 验证并执行
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
import uuid
import json


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
    元元意图执行器 (LLM 驱动)
    
    使用 LLM 决定如何执行元元意图，而不是硬编码 if-else
    """
    
    # 执行 Prompt 模板
    EXECUTE_PROMPT = """
你是一个元元意图执行专家。请分析并执行以下元元意图。

## 元元意图
{meta_meta_json}

## 当前系统状态
{system_config_json}

## 可用操作类型
1. modify_meta_parser_prompt: 修改元意图解析 Prompt
2. modify_self_bootstrap_policy: 修改 Self-Bootstrap 策略
3. modify_meta_action_types: 修改元动作类型 (添加/删除动作)
4. modify_system_config: 修改一般系统配置
5. create_checkpoint: 创建系统检查点 (用于回滚)

## 执行规则
- 需要 super_admin 权限才能执行元元意图
- 修改解析规则可能影响系统行为
- 修改 Self-Bootstrap 策略可能影响自修改能力
- 所有修改都必须记录审计日志

## 输出格式
请返回 JSON 格式:
{{
    "success": true/false,
    "action_taken": "执行的操作名称",
    "changes": {{
        "key": "新值",
        ...
    }},
    "audit_info": {{
        "action": "操作名称",
        "target": "目标",
        "user": "用户 ID"
    }},
    "error": "错误信息 (如果失败)"
}}
"""
    
    def __init__(
        self,
        system_config: dict[str, Any],
        llm_executor: Any,
        audit_logger: Any = None,
    ):
        """
        初始化执行器
        
        Args:
            system_config: 系统配置
            llm_executor: LLM 执行器
            audit_logger: 审计日志记录器
        """
        self.system_config = system_config
        self.llm_executor = llm_executor
        self.audit_logger = audit_logger
    
    async def execute(
        self,
        meta_meta: Any,  # MetaMetaIntent
        context: dict[str, Any],
    ) -> MetaMetaResult:
        """
        执行元元意图 (LLM 驱动)
        
        Args:
            meta_meta: 元元意图
            context: 执行上下文
        
        Returns:
            执行结果
        """
        audit_id = None
        
        try:
            # 1. 验证元元意图
            errors = meta_meta.validate()
            if errors:
                return MetaMetaResult(
                    success=False,
                    error="; ".join(errors),
                )
            
            # 2. 检查权限
            if not self._check_permission(context):
                return MetaMetaResult(
                    success=False,
                    error="权限不足：需要 super_admin 权限",
                )
            
            # 3. 构建执行 Prompt
            exec_prompt = self.EXECUTE_PROMPT.format(
                meta_meta_json=json.dumps(meta_meta.to_dict(), indent=2, ensure_ascii=False),
                system_config_json=json.dumps(self.system_config, indent=2, ensure_ascii=False, default=str),
            )
            
            # 4. LLM 执行
            messages = [
                {"role": "system", "content": "你是一个元元意图执行专家。"},
                {"role": "user", "content": exec_prompt},
            ]
            
            response = await self.llm_executor.execute(messages)
            
            # 5. 解析 LLM 返回的结果
            result = self._parse_llm_response(response.content)
            
            if not result.get("success", False):
                return MetaMetaResult(
                    success=False,
                    error=result.get("error", "执行失败"),
                )
            
            # 6. 执行 LLM 决定的操作
            changes = result.get("changes", {})
            action_taken = result.get("action_taken", "")
            
            await self._apply_changes(action_taken, changes, context)
            
            # 7. 记录审计日志
            audit_info = result.get("audit_info", {})
            audit_id = await self._log_audit(
                action=audit_info.get("action", action_taken),
                target_type=meta_meta.target_type.value,
                target_id=meta_meta.target_id,
                context=context,
                parameters=meta_meta.parameters,
                result="success",
                changes=[f"{k}: {v}" for k, v in changes.items()],
            )
            
            return MetaMetaResult(
                success=True,
                result=result,
                audit_id=audit_id,
                changes_applied=[f"{k} = {v}" for k, v in changes.items()],
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
    
    def _check_permission(self, context: dict) -> bool:
        """检查权限"""
        user_role = context.get("user_role", "")
        permissions = context.get("permissions", [])
        
        return user_role == "super_admin" or "super_admin" in permissions
    
    def _parse_llm_response(self, content: str) -> dict[str, Any]:
        """解析 LLM 返回的 JSON"""
        try:
            # 提取 JSON 部分
            json_str = content.strip()
            
            # 处理 Markdown 代码块
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            
            return json.loads(json_str)
        except Exception as e:
            return {
                "success": False,
                "error": f"解析 LLM 响应失败：{e}",
            }
    
    async def _apply_changes(
        self,
        action_taken: str,
        changes: dict[str, Any],
        context: dict,
    ) -> None:
        """
        应用 LLM 决定的变更
        
        Args:
            action_taken: LLM 决定的操作
            changes: 变更内容
            context: 执行上下文
        """
        # 根据 action_taken 应用变更
        # 这里只做简单的字典更新，实际应该根据操作类型做不同处理
        
        if action_taken == "modify_meta_parser_prompt":
            new_prompt = changes.get("META_PARSER_PROMPT")
            if new_prompt:
                self.system_config["META_PARSER_PROMPT"] = new_prompt
        
        elif action_taken == "modify_self_bootstrap_policy":
            new_policy = changes.get("SELF_BOOTSTRAP_POLICY")
            if new_policy:
                self.system_config["SELF_BOOTSTRAP_POLICY"] = new_policy
        
        elif action_taken == "modify_meta_action_types":
            new_actions = changes.get("META_ACTIONS", [])
            if new_actions:
                self.system_config["META_ACTIONS"] = new_actions
        
        elif action_taken == "modify_system_config":
            for key, value in changes.items():
                self.system_config[key] = value
        
        else:
            # 通用处理：直接更新配置
            for key, value in changes.items():
                self.system_config[key] = value
    
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
        
        # 存储审计日志
        if self.audit_logger:
            await self.audit_logger.log(audit_record)
        else:
            # 存储到系统配置 (简化实现)
            if "AUDIT_LOG" not in self.system_config:
                self.system_config["AUDIT_LOG"] = []
            self.system_config["AUDIT_LOG"].append(audit_record)
        
        return audit_id


# =============================================================================
# 元意图执行器 (LLM 驱动版本)
# =============================================================================

class MetaIntentExecutor:
    """
    元意图执行器 (LLM 驱动)
    
    使用 LLM 决定如何执行元意图
    """
    
    EXECUTE_PROMPT = """
你是一个元意图执行专家。请分析并执行以下元意图。

## 元意图
{meta_intent_json}

## 当前系统状态
{system_config_json}

## 可用操作类型
1. create_template: 创建意图模板
2. modify_template: 修改意图模板
3. delete_template: 删除意图模板
4. register_capability: 注册能力
5. modify_policy: 修改执行策略
6. query_status: 查询系统状态

## 输出格式
请返回 JSON 格式:
{{
    "success": true/false,
    "action_taken": "执行的操作名称",
    "changes": {{...}},
    "result": {{...}},
    "error": "错误信息 (如果失败)"
}}
"""
    
    def __init__(
        self,
        system_config: dict[str, Any],
        llm_executor: Any,
        registry: Any = None,
    ):
        self.system_config = system_config
        self.llm_executor = llm_executor
        self.registry = registry
    
    async def execute(
        self,
        meta_intent: Any,  # MetaIntent
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """执行元意图 (LLM 驱动)"""
        
        # 构建执行 Prompt
        exec_prompt = self.EXECUTE_PROMPT.format(
            meta_intent_json=json.dumps(meta_intent.to_dict(), indent=2, ensure_ascii=False),
            system_config_json=json.dumps(self.system_config, indent=2, ensure_ascii=False, default=str),
        )
        
        # LLM 执行
        messages = [
            {"role": "system", "content": "你是元意图执行专家。"},
            {"role": "user", "content": exec_prompt},
        ]
        
        response = await self.llm_executor.execute(messages)
        
        # 解析并执行
        result = self._parse_llm_response(response.content)
        
        # 应用变更
        if result.get("success"):
            await self._apply_changes(result.get("changes", {}))
        
        return result
    
    def _parse_llm_response(self, content: str) -> dict:
        """解析 LLM 响应"""
        try:
            json_str = content.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            return json.loads(json_str)
        except Exception as e:
            return {"success": False, "error": f"解析失败：{e}"}
    
    async def _apply_changes(self, changes: dict) -> None:
        """应用变更"""
        for key, value in changes.items():
            self.system_config[key] = value


# =============================================================================
# 便捷函数
# =============================================================================

def create_meta_meta_executor(
    system_config: dict,
    llm_executor: Any,
    audit_logger: Any = None,
) -> MetaMetaExecutor:
    """创建元元意图执行器"""
    return MetaMetaExecutor(system_config, llm_executor, audit_logger)


def create_meta_intent_executor(
    system_config: dict,
    llm_executor: Any,
    registry: Any = None,
) -> MetaIntentExecutor:
    """创建元意图执行器"""
    return MetaIntentExecutor(system_config, llm_executor, registry)
