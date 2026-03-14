"""
IntentOS 核心数据模型
定义意图、能力、上下文等核心概念
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


class IntentStatus(Enum):
    """意图执行状态"""

    PENDING = "pending"
    PARSING = "parsing"
    SCHEDULING = "scheduling"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IntentType(Enum):
    """意图类型"""

    ATOMIC = "atomic"  # 原子意图
    COMPOSITE = "composite"  # 复合意图
    SCENARIO = "scenario"  # 场景意图
    META = "meta"  # 元意图（管理其他意图）


@dataclass
class Context:
    """
    执行上下文
    包含用户身份、历史、环境、权限等动态变量
    """

    user_id: str
    user_role: str = "user"
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    history: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def has_permission(self, permission: str) -> bool:
        """检查是否有指定权限"""
        return permission in self.permissions or "admin" in self.permissions

    def get_variable(self, key: str, default: Any = None) -> Any:
        """获取上下文变量"""
        return self.variables.get(key, default)

    def set_variable(self, key: str, value: Any) -> None:
        """设置上下文变量"""
        self.variables[key] = value


@dataclass
class Capability:
    """
    原子能力
    系统可调度的最小执行单元
    """

    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    func: Callable[..., Any]
    requires_permissions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def execute(self, context: Context, **kwargs) -> Any:
        """执行能力"""
        # 权限检查
        for perm in self.requires_permissions:
            if not context.has_permission(perm):
                raise PermissionError(f"缺少权限：{perm}")

        return self.func(context, **kwargs)


@dataclass
class IntentStep:
    """
    意图执行步骤
    用于复合意图中的步骤定义
    """

    capability_name: str
    params: dict[str, Any] = field(default_factory=dict)
    condition: Optional[str] = None  # 执行条件（可选）
    output_var: Optional[str] = None  # 输出绑定变量


@dataclass
class Intent:
    """
    意图
    核心概念：用户目标的结构性表达
    """

    name: str
    intent_type: IntentType
    description: str = ""
    actor: str = "user"
    goal: str = ""
    context: Context = field(default_factory=lambda: Context(user_id="anonymous"))
    params: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)
    steps: list[IntentStep] = field(default_factory=list)  # 复合意图的步骤
    status: IntentStatus = IntentStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    parent_intent: Optional[str] = None  # 父意图 ID（用于嵌套）
    child_intents: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """初始化后处理"""
        if not self.context:
            self.context = Context(user_id="anonymous")

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "intent_type": self.intent_type.value,
            "description": self.description,
            "actor": self.actor,
            "goal": self.goal,
            "params": self.params,
            "constraints": self.constraints,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def update_status(self, status: IntentStatus) -> None:
        """更新状态"""
        self.status = status
        self.updated_at = datetime.now()


@dataclass
class IntentTemplate:
    """
    意图模板
    可复用的意图定义，支持参数化
    """

    name: str
    description: str
    intent_type: IntentType = IntentType.COMPOSITE
    params_schema: dict[str, Any] = field(default_factory=dict)
    steps: list[IntentStep] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    required_permissions: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)

    def instantiate(self, context: Context, **params) -> Intent:
        """根据模板实例化意图"""
        # 参数验证和填充
        instantiated_params = self.params_schema.copy()
        for key, value in params.items():
            instantiated_params[key] = value

        # 步骤中的参数替换
        instantiated_steps = []
        for step in self.steps:
            instantiated_step = IntentStep(
                capability_name=step.capability_name,
                params={k: self._resolve_param(v, params) for k, v in step.params.items()},
                condition=step.condition,
                output_var=step.output_var,
            )
            instantiated_steps.append(instantiated_step)

        return Intent(
            name=self.name,
            intent_type=self.intent_type,
            description=self.description,
            params=instantiated_params,
            constraints=self.constraints,
            steps=instantiated_steps,
            context=context,
        )

    def _resolve_param(self, value: Any, params: dict[str, Any]) -> Any:
        """解析参数中的占位符"""
        if isinstance(value, str):
            for key, param_value in params.items():
                value = value.replace(f"{{{{{key}}}}}", str(param_value))
        return value


@dataclass
class IntentExecutionResult:
    """意图执行结果"""

    intent_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_trace: list[dict[str, Any]] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.completed_at and self.completed_at is not False:
            self.completed_at = datetime.now()
