"""
PEF (Prompt Executable File) 格式规范 v2.0

人类可读的 YAML/JSON 格式，支持：
- 完整的意图结构表示（包括元意图）
- 能力绑定信息
- 执行上下文
- 版本兼容性
- 支持直接编辑和 Git 版本控制

参考: docs/PEF_FORMAT_SPEC.md
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import yaml

if TYPE_CHECKING:
    from intentos.agent.compiler import PEF as PEFv1


# =============================================================================
# PEF v2.0 数据模型
# =============================================================================


@dataclass
class IntentDeclaration:
    """意图声明段"""

    goal: str = ""  # 目标描述（必填）
    description: str = ""  # 详细说明
    output_format: str = "json"  # json | markdown | text

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "description": self.description,
            "output_format": self.output_format,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IntentDeclaration:
        return cls(
            goal=data.get("goal", ""),
            description=data.get("description", ""),
            output_format=data.get("output_format", "json"),
        )


@dataclass
class ContextBinding:
    """上下文绑定段"""

    user_id: str = ""
    session_id: str = ""
    business_context: dict[str, Any] = field(default_factory=dict)
    technical_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "business_context": self.business_context,
            "technical_context": self.technical_context,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContextBinding:
        return cls(
            user_id=data.get("user_id", ""),
            session_id=data.get("session_id", ""),
            business_context=data.get("business_context", {}),
            technical_context=data.get("technical_context", {}),
        )


@dataclass
class CapabilityBinding:
    """能力绑定段"""

    name: str = ""
    version: str = "*"  # 版本约束
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CapabilityBinding:
        return cls(
            name=data.get("name", ""),
            version=data.get("version", "*"),
            params=data.get("params", {}),
        )


@dataclass
class WorkflowStep:
    """工作流步骤"""

    id: str = ""
    name: str = ""
    capability: str = ""
    depends_on: list[str] = field(default_factory=list)
    output_var: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "capability": self.capability,
            "depends_on": self.depends_on,
            "output_var": self.output_var,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowStep:
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            capability=data.get("capability", ""),
            depends_on=data.get("depends_on", []),
            output_var=data.get("output_var", ""),
        )


@dataclass
class WorkflowDefinition:
    """工作流段（可选）"""

    steps: list[WorkflowStep] = field(default_factory=list)
    on_error: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "steps": [step.to_dict() for step in self.steps],
            "on_error": self.on_error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowDefinition:
        return cls(
            steps=[WorkflowStep.from_dict(s) for s in data.get("steps", [])],
            on_error=data.get("on_error", []),
        )


@dataclass
class PEF:
    """
    PEF (Prompt Executable File) v2.0

    人类可读的 YAML/JSON 格式，支持：
    - 完整的意图结构表示
    - 能力绑定信息
    - 执行上下文
    - 版本兼容性
    - 支持直接编辑和 Git 版本控制
    """

    # Header 段
    version: str = "2.0"
    id: str = ""
    compiled_at: str = ""

    # 核心段
    intent: IntentDeclaration = field(default_factory=IntentDeclaration)
    context: ContextBinding = field(default_factory=ContextBinding)
    capabilities: list[CapabilityBinding] = field(default_factory=list)

    # 可选段
    constraints: dict[str, Any] = field(default_factory=dict)
    workflow: Optional[WorkflowDefinition] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # 向后兼容字段
    _system_prompt: str = field(default="", repr=False)
    _user_prompt: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        """初始化后处理"""
        if not self.id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # 使用更多随机源确保唯一性
            import os
            random_data = f"{timestamp}{os.getpid()}{id(self)}{self.intent.goal}"
            hash_suffix = hashlib.md5(random_data.encode()).hexdigest()[:6]
            self.id = f"pef_{timestamp}_{hash_suffix}"

        if not self.compiled_at:
            self.compiled_at = datetime.now().isoformat()

    # =========================================================================
    # 序列化方法
    # =========================================================================

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result: dict[str, Any] = {
            "version": self.version,
            "id": self.id,
            "compiled_at": self.compiled_at,
            "intent": self.intent.to_dict(),
            "context": self.context.to_dict(),
            "capabilities": [cap.to_dict() for cap in self.capabilities],
        }

        if self.constraints:
            result["constraints"] = self.constraints

        if self.workflow and self.workflow.steps:
            result["workflow"] = self.workflow.to_dict()

        if self.metadata:
            result["metadata"] = self.metadata

        return result

    def to_yaml(self) -> str:
        """导出为 YAML 字符串"""
        return yaml.dump(
            self.to_dict(),
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            Dumper=yaml.SafeDumper,
        )

    def to_json(self, indent: int = 2) -> str:
        """导出为 JSON 字符串"""
        return json.dumps(
            self.to_dict(),
            indent=indent,
            ensure_ascii=False,
        )

    # =========================================================================
    # 反序列化方法
    # =========================================================================

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PEF:
        """从字典创建 PEF"""
        # 处理 Header
        version = data.get("version", "2.0")
        pef_id = data.get("id", "")
        compiled_at = data.get("compiled_at", "")

        # 处理核心段
        intent = IntentDeclaration.from_dict(data.get("intent", {}))
        context = ContextBinding.from_dict(data.get("context", {}))
        capabilities = [
            CapabilityBinding.from_dict(cap)
            for cap in data.get("capabilities", [])
        ]

        # 处理可选段
        constraints = data.get("constraints", {})
        workflow_data = data.get("workflow")
        workflow = (
            WorkflowDefinition.from_dict(workflow_data)
            if workflow_data
            else None
        )
        metadata = data.get("metadata", {})

        return cls(
            version=version,
            id=pef_id,
            compiled_at=compiled_at,
            intent=intent,
            context=context,
            capabilities=capabilities,
            constraints=constraints,
            workflow=workflow,
            metadata=metadata,
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> PEF:
        """从 YAML 字符串创建 PEF"""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)

    @classmethod
    def from_json(cls, json_str: str) -> PEF:
        """从 JSON 字符串创建 PEF"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    # =========================================================================
    # 文件 I/O
    # =========================================================================

    @classmethod
    def from_file(cls, file_path: str | Path) -> PEF:
        """从文件加载 PEF"""
        path = Path(file_path)
        content = path.read_text(encoding="utf-8")

        if path.suffix == ".json" or path.name.endswith(".pef.json"):
            return cls.from_json(content)
        else:
            # 默认使用 YAML
            return cls.from_yaml(content)

    def to_file(self, file_path: str | Path, format: str = "yaml") -> None:
        """保存 PEF 到文件"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json" or path.suffix == ".json":
            content = self.to_json()
        else:
            content = self.to_yaml()

        path.write_text(content, encoding="utf-8")

    # =========================================================================
    # 向后兼容
    # =========================================================================

    @classmethod
    def from_v1(cls, v1_pef: "PEFv1") -> PEF:
        """从 v1.0 PEF 格式转换"""
        # 延迟导入，避免循环导入
        from intentos.agent.compiler import PEF as PEFv1_local

        # 提取意图（从 system_prompt 或 user_prompt）
        intent_text = v1_pef.intent
        if not intent_text:
            # 尝试从 user_prompt 提取
            if v1_pef.user_prompt.startswith("请执行："):
                intent_text = v1_pef.user_prompt[len("请执行：") :]

        return cls(
            version="2.0",
            id=v1_pef.id,
            compiled_at=v1_pef.compiled_at,
            intent=IntentDeclaration(goal=intent_text),
            context=ContextBinding(
                user_id=v1_pef.metadata.get("user_id", ""),
                session_id=v1_pef.metadata.get("session_id", ""),
                business_context={
                    k: v
                    for k, v in v1_pef.metadata.items()
                    if k not in ["user_id", "session_id"]
                },
            ),
            capabilities=[
                CapabilityBinding(name=cap) for cap in v1_pef.capabilities
            ],
            constraints=v1_pef.constraints,
            metadata={
                **v1_pef.metadata,
                "cache_key": v1_pef.cache_key,
                "token_count": v1_pef.token_count,
            },
            _system_prompt=v1_pef.system_prompt,
            _user_prompt=v1_pef.user_prompt,
        )

    def to_v1(self) -> "PEFv1":
        """转换为 v1.0 PEF 格式（向后兼容）"""
        # 延迟导入，避免循环导入
        from intentos.agent.compiler import PEF as PEFv1_local

        return PEFv1_local(
            version=self.version,
            id=self.id,
            intent=self.intent.goal,
            system_prompt=self._system_prompt or self._generate_system_prompt(),
            user_prompt=self._user_prompt or f"请执行：{self.intent.goal}",
            capabilities=[cap.name for cap in self.capabilities],
            constraints=self.constraints,
            metadata={
                **self.metadata,
                **self.context.to_dict(),
            },
            compiled_at=self.compiled_at,
            cache_key=self.metadata.get("cache_key", ""),
            token_count=self.metadata.get("token_count", 0),
        )

    def _generate_system_prompt(self) -> str:
        """生成 system prompt（用于向后兼容）"""
        capabilities_str = ", ".join([cap.name for cap in self.capabilities])
        return (
            f"你是一个 AI 智能助理。"
            f"可用能力：{capabilities_str}。"
            f"用户意图：{self.intent.goal}。"
        )

    # =========================================================================
    # 验证
    # =========================================================================

    def validate(self) -> list[str]:
        """
        验证 PEF 有效性

        Returns:
            错误列表，空列表表示有效
        """
        errors: list[str] = []

        # 必填字段检查
        if not self.version:
            errors.append("version is required")

        if not self.id:
            errors.append("id is required")

        if not self.compiled_at:
            errors.append("compiled_at is required")

        if not self.intent.goal:
            errors.append("intent.goal is required")

        if not self.context.user_id:
            errors.append("context.user_id is required")

        # 能力绑定验证
        for i, cap in enumerate(self.capabilities):
            if not cap.name:
                errors.append(f"capabilities[{i}].name is required")

        # 工作流验证
        if self.workflow and self.workflow.steps:
            step_ids = {step.id for step in self.workflow.steps}
            for step in self.workflow.steps:
                if not step.id:
                    errors.append("workflow step id is required")
                if not step.capability:
                    errors.append(
                        f"workflow step '{step.id}' capability is required"
                    )
                for dep in step.depends_on:
                    if dep not in step_ids:
                        errors.append(
                            f"workflow step '{step.id}' depends on "
                            f"non-existent step '{dep}'"
                        )

        return errors

    # =========================================================================
    # 辅助方法
    # =========================================================================

    @property
    def cache_key(self) -> str:
        """生成缓存键"""
        content = self.to_json()
        return hashlib.blake2b(content.encode("utf-8"), digest_size=16).hexdigest()

    def get_capability_names(self) -> list[str]:
        """获取所有能力名称"""
        return [cap.name for cap in self.capabilities if cap.name]


# =============================================================================
# 便捷函数
# =============================================================================


def load_pef(file_path: str | Path) -> PEF:
    """从文件加载 PEF"""
    return PEF.from_file(file_path)


def save_pef(
    pef: PEF, file_path: str | Path, format: str = "yaml"
) -> None:
    """保存 PEF 到文件"""
    pef.to_file(file_path, format=format)


def create_pef(
    goal: str,
    user_id: str,
    capabilities: list[str] | None = None,
    context: dict[str, Any] | None = None,
    **kwargs: Any,
) -> PEF:
    """
    快速创建 PEF

    Args:
        goal: 意图目标
        user_id: 用户 ID
        capabilities: 能力列表
        context: 业务上下文
        **kwargs: 其他参数

    Returns:
        PEF 实例
    """
    caps = [
        CapabilityBinding(name=cap) for cap in (capabilities or [])
    ]

    ctx = ContextBinding(
        user_id=user_id,
        business_context=context or {},
    )

    return PEF(
        intent=IntentDeclaration(goal=goal),
        context=ctx,
        capabilities=caps,
        **kwargs,
    )
