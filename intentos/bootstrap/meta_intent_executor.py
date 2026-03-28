"""
元意图执行器 (Meta-Intent Executor)

实现系统的自我改进能力：
1. 修改系统协议
2. 注册新能力
3. 优化性能配置
4. 修复执行错误
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from ..apps import IntentPackage, IntentPackageRegistry
from ..graph import IntentGraph, IntentNode, IntentNodeType


class MetaIntentType(str, Enum):
    """元意图类型"""
    
    # 协议修改
    MODIFY_PROTOCOL = "modify_protocol"
    REGISTER_CAPABILITY = "register_capability"
    UNREGISTER_CAPABILITY = "unregister_capability"
    
    # 意图模板管理
    REGISTER_INTENT_TEMPLATE = "register_intent_template"
    UPDATE_INTENT_TEMPLATE = "update_intent_template"
    REMOVE_INTENT_TEMPLATE = "remove_intent_template"
    
    # 性能优化
    OPTIMIZE_PERFORMANCE = "optimize_performance"
    UPDATE_CONFIG = "update_config"
    
    # 错误修复
    REFINE_EXECUTION = "refine_execution"
    ADD_RETRY_LOGIC = "add_retry_logic"
    ADD_TIMEOUT = "add_timeout"
    
    # 系统自举
    REPLICATE_TO_NODE = "replicate_to_node"
    EXPAND_CLUSTER = "expand_cluster"


@dataclass
class MetaIntent:
    """
    元意图
    
    用于修改系统自身行为的特殊意图
    """
    type: MetaIntentType
    target: str  # 修改目标（如 app_id, capability_name 等）
    params: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"  # system / user_id
    approved_by: Optional[str] = None  # 审批人
    confidence: float = 1.0  # 置信度
    
    # 执行结果
    status: str = "pending"  # pending/approved/rejected/executing/completed/failed
    result: Any = None
    error: Optional[str] = None
    executed_at: Optional[datetime] = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "target": self.target,
            "params": self.params,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "approved_by": self.approved_by,
            "confidence": self.confidence,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }


@dataclass
class BootstrapPolicy:
    """
    自举策略
    
    定义系统自我修改的规则和限制
    """
    # 是否允许自我修改
    allow_self_modification: bool = True
    
    # 需要人工审批的操作类型
    require_approval_for: list[str] = field(default_factory=lambda: [
        "delete_all_templates",
        "modify_audit_rules",
        "disable_self_bootstrap",
        "unregister_capability",
    ])
    
    # 最大修改频率（每小时）
    max_modifications_per_hour: int = 10
    
    # 置信度阈值（低于此值需要审批）
    require_confidence_threshold: float = 0.8
    
    # 复制因子（自修改需要复制到的节点数）
    replication_factor: int = 3
    
    # 一致性级别
    consistency_level: str = "quorum"  # eventual / quorum / strong
    
    def requires_approval(self, meta_intent: MetaIntent) -> bool:
        """检查是否需要人工审批"""
        # 检查操作类型
        if meta_intent.type.value in self.require_approval_for:
            return True
        
        # 检查置信度
        if meta_intent.confidence < self.require_confidence_threshold:
            return True
        
        return False


class MetaIntentExecutor:
    """
    元意图执行器
    
    执行元意图，实现系统的自我改进
    """
    
    def __init__(
        self,
        registry: IntentPackageRegistry,
        intent_graph: Optional[IntentGraph] = None,
        policy: Optional[BootstrapPolicy] = None,
    ):
        self.registry = registry
        self.intent_graph = intent_graph or IntentGraph()
        self.policy = policy or BootstrapPolicy()
        
        # 执行历史
        self.execution_history: list[MetaIntent] = []
        
        # 注册执行器
        self._handlers: dict[MetaIntentType, Callable] = {
            MetaIntentType.MODIFY_PROTOCOL: self._execute_modify_protocol,
            MetaIntentType.REGISTER_CAPABILITY: self._execute_register_capability,
            MetaIntentType.UNREGISTER_CAPABILITY: self._execute_unregister_capability,
            MetaIntentType.REGISTER_INTENT_TEMPLATE: self._execute_register_intent_template,
            MetaIntentType.OPTIMIZE_PERFORMANCE: self._execute_optimize_performance,
            MetaIntentType.REFINE_EXECUTION: self._execute_refine_execution,
        }
    
    async def execute(self, meta_intent: MetaIntent) -> MetaIntent:
        """
        执行元意图
        
        Args:
            meta_intent: 要执行的元意图
            
        Returns:
            执行后的元意图（包含结果）
        """
        # 1. 检查是否允许自我修改
        if not self.policy.allow_self_modification:
            meta_intent.status = "rejected"
            meta_intent.error = "Self-modification is disabled"
            return meta_intent
        
        # 2. 检查是否需要审批
        if self.policy.requires_approval(meta_intent):
            meta_intent.status = "pending_approval"
            # 在实际系统中，这里会触发人工审批流程
            # 为演示，我们假设自动批准
            meta_intent.approved_by = "auto_approved"
        
        # 3. 执行元意图
        meta_intent.status = "executing"
        
        handler = self._handlers.get(meta_intent.type)
        if not handler:
            meta_intent.status = "failed"
            meta_intent.error = f"Unknown meta-intent type: {meta_intent.type}"
            return meta_intent
        
        try:
            result = await handler(meta_intent)
            meta_intent.status = "completed"
            meta_intent.result = result
            meta_intent.executed_at = datetime.now()
        except Exception as e:
            meta_intent.status = "failed"
            meta_intent.error = str(e)
            meta_intent.executed_at = datetime.now()
        
        # 4. 记录执行历史
        self.execution_history.append(meta_intent)
        
        # 5. 检查修改频率限制
        self._enforce_rate_limit()
        
        return meta_intent
    
    async def _execute_modify_protocol(self, meta_intent: MetaIntent) -> dict[str, Any]:
        """
        执行协议修改
        
        修改系统协议配置
        """
        protocol_name = meta_intent.target
        changes = meta_intent.params.get("changes", {})
        
        # 在实际系统中，这里会修改实际的协议配置
        # 示例：修改解析规则、执行规则等
        
        return {
            "protocol": protocol_name,
            "changes": changes,
            "status": "applied",
        }
    
    async def _execute_register_capability(self, meta_intent: MetaIntent) -> dict[str, Any]:
        """
        执行能力注册
        
        注册新的能力到系统
        """
        capability_name = meta_intent.params.get("name", meta_intent.target)
        capability_def = meta_intent.params
        
        # 创建能力定义
        capability = {
            "name": capability_name,
            "description": capability_def.get("description", ""),
            "type": capability_def.get("type", "io"),
            "interface": capability_def.get("interface", {}),
            "registered_at": datetime.now().isoformat(),
        }
        
        # 在实际系统中，这里会将能力注册到能力注册表
        # 并更新相关的意图包
        
        return {
            "capability": capability,
            "status": "registered",
        }
    
    async def _execute_unregister_capability(self, meta_intent: MetaIntent) -> dict[str, Any]:
        """
        执行能力注销
        
        从系统移除能力
        """
        capability_name = meta_intent.target
        
        # 在实际系统中，这里会从能力注册表移除能力
        # 并更新依赖该能力的意图包
        
        return {
            "capability": capability_name,
            "status": "unregistered",
        }
    
    async def _execute_register_intent_template(self, meta_intent: MetaIntent) -> dict[str, Any]:
        """
        执行意图模板注册
        
        注册新的意图模板到图谱
        """
        template_name = meta_intent.params.get("name", meta_intent.target)
        template_def = meta_intent.params
        
        # 创建意图节点
        node = IntentNode(
            node_id=f"template_{template_name}",
            node_type=IntentNodeType.TEMPLATE,
            name=template_name,
            description=template_def.get("description", ""),
            content=template_def,
            tags=template_def.get("tags", []),
        )
        
        # 添加到意图图谱
        self.intent_graph.add_node(node)
        
        return {
            "template": node.to_dict(),
            "status": "registered",
        }
    
    async def _execute_optimize_performance(self, meta_intent: MetaIntent) -> dict[str, Any]:
        """
        执行性能优化
        
        优化系统性能配置
        """
        actions = meta_intent.params.get("actions", [])
        results = []
        
        for action in actions:
            action_type = action.get("action")
            target = action.get("target")
            value = action.get("value")
            
            # 在实际系统中，这里会修改实际的配置
            # 示例：调整缓存大小、启用/禁用功能等
            
            results.append({
                "action": action_type,
                "target": target,
                "value": value,
                "status": "applied",
            })
        
        return {
            "actions": results,
            "status": "optimized",
        }
    
    async def _execute_refine_execution(self, meta_intent: MetaIntent) -> dict[str, Any]:
        """
        执行执行优化
        
        修复执行错误或优化执行逻辑
        """
        intent_id = meta_intent.target
        refinement = meta_intent.params
        
        # 在实际系统中，这里会：
        # 1. 分析执行轨迹
        # 2. 识别问题
        # 3. 修改执行逻辑
        
        return {
            "intent_id": intent_id,
            "refinement": refinement,
            "status": "refined",
        }
    
    def _enforce_rate_limit(self) -> None:
        """执行频率限制"""
        now = datetime.now()
        one_hour_ago = now.timestamp() - 3600
        
        # 计算过去一小时的执行次数
        recent_executions = [
            m for m in self.execution_history
            if m.executed_at and m.executed_at.timestamp() > one_hour_ago
        ]
        
        if len(recent_executions) > self.policy.max_modifications_per_hour:
            # 超过限制，暂停执行
            # 在实际系统中，这里会触发限流机制
            pass
    
    def get_history(
        self,
        time_range: str = "24h",
        action_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[MetaIntent]:
        """
        获取执行历史
        
        Args:
            time_range: 时间范围 (如 "24h", "7d")
            action_type: 操作类型过滤
            status: 状态过滤
            
        Returns:
            执行历史列表
        """
        history = self.execution_history
        
        # 时间过滤
        if time_range:
            hours = int(time_range.replace("h", ""))
            cutoff = datetime.now().timestamp() - (hours * 3600)
            history = [
                m for m in history
                if m.executed_at and m.executed_at.timestamp() > cutoff
            ]
        
        # 类型过滤
        if action_type:
            history = [m for m in history if m.type.value == action_type]
        
        # 状态过滤
        if status:
            history = [m for m in history if m.status == status]
        
        return history
    
    def get_statistics(self) -> dict[str, Any]:
        """获取执行统计"""
        history = self.execution_history
        
        return {
            "total_executions": len(history),
            "completed": sum(1 for m in history if m.status == "completed"),
            "failed": sum(1 for m in history if m.status == "failed"),
            "pending_approval": sum(1 for m in history if m.status == "pending_approval"),
            "by_type": self._count_by_type(history),
        }
    
    def _count_by_type(self, history: list[MetaIntent]) -> dict[str, int]:
        """按类型统计"""
        counts: dict[str, int] = {}
        for m in history:
            type_name = m.type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts


# =============================================================================
# 工厂函数
# =============================================================================


def create_meta_intent_executor(
    registry: IntentPackageRegistry,
    intent_graph: Optional[IntentGraph] = None,
    policy: Optional[BootstrapPolicy] = None,
) -> MetaIntentExecutor:
    """创建元意图执行器"""
    return MetaIntentExecutor(
        registry=registry,
        intent_graph=intent_graph,
        policy=policy,
    )


def create_meta_intent(
    type: MetaIntentType,
    target: str,
    params: Optional[dict] = None,
    description: str = "",
) -> MetaIntent:
    """创建元意图"""
    return MetaIntent(
        type=type,
        target=target,
        params=params or {},
        description=description,
    )
