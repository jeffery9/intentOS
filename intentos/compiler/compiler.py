"""
意图编译器
将结构化意图编译为 LLM 可执行的 Prompt
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ..core import Intent, IntentType


@dataclass
class CompiledPrompt:
    """编译后的 Prompt"""
    system_prompt: str
    user_prompt: str
    intent: Intent
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def messages(self) -> list[dict[str, str]]:
        """转换为 LLM 消息格式"""
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.user_prompt},
        ]


class IntentCompiler:
    """
    意图编译器
    将结构化意图编译为 LLM Prompt
    """

    def __init__(self, registry: Optional[Any] = None):
        self.registry = registry
        self._prompt_templates: dict[str, str] = {}
        self._register_default_templates()

    def _register_default_templates(self) -> None:
        """注册默认 Prompt 模板"""
        # 原子意图 Prompt 模板
        self._prompt_templates["atomic"] = """# 任务执行指令

你是一个 AI 原生助手，需要执行用户的意图。

## 意图信息
- **名称**: {intent_name}
- **类型**: 原子任务
- **目标**: {goal}
- **描述**: {description}

## 可用能力
{capabilities}

## 上下文信息
- **用户**: {user_id}
- **角色**: {user_role}
- **会话**: {session_id}

## 参数
{params}

## 约束条件
{constraints}

请根据以上信息，执行意图并返回结果。
结果格式：JSON 对象，包含 success, result, message 字段。
"""

        # 复合意图 Prompt 模板
        self._prompt_templates["composite"] = """# 复合任务执行计划

你是一个 AI 原生助手，需要执行一个多步骤的复合任务。

## 意图信息
- **名称**: {intent_name}
- **类型**: 复合任务
- **目标**: {goal}

## 执行步骤
{steps}

## 上下文信息
- **用户**: {user_id}
- **角色**: {user_role}

## 参数
{params}

请按顺序执行上述步骤，每一步的输出将作为下一步的输入。
最终返回整合后的结果。
"""

        # 场景意图 Prompt 模板
        self._prompt_templates["scenario"] = """# 场景化任务

你是一个 AI 原生助手，需要完成一个业务场景任务。

## 场景信息
- **名称**: {intent_name}
- **场景**: {description}
- **目标**: {goal}

## 业务上下文
- **用户角色**: {user_role}
- **相关权限**: {permissions}

## 场景参数
{params}

## 期望输出
根据场景需求，生成结构化的输出结果。
"""

        # 元意图 Prompt 模板
        self._prompt_templates["meta"] = """# 系统管理指令

你是一个 AI 原生系统的元管理器，需要管理系统自身的结构和行为。

## 元意图信息
- **动作**: {action}
- **目标**: {goal}

## 当前系统状态
{system_state}

## 操作参数
{params}

请执行系统管理操作，并返回操作结果。
"""

    def compile(self, intent: Intent) -> CompiledPrompt:
        """
        将意图编译为 Prompt

        Args:
            intent: 结构化意图

        Returns:
            编译后的 Prompt
        """
        # 根据意图类型选择模板
        template_name = self._get_template_for_intent(intent)
        template = self._prompt_templates.get(template_name, self._prompt_templates["atomic"])

        # 填充模板
        system_prompt = self._fill_template(template, intent)
        user_prompt = self._generate_user_prompt(intent)

        return CompiledPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            intent=intent,
            metadata={
                "template": template_name,
                "intent_type": intent.intent_type.value,
            },
        )

    def _get_template_for_intent(self, intent: Intent) -> str:
        """根据意图类型获取模板"""
        if intent.intent_type == IntentType.ATOMIC:
            return "atomic"
        elif intent.intent_type == IntentType.COMPOSITE:
            return "composite"
        elif intent.intent_type == IntentType.SCENARIO:
            return "scenario"
        elif intent.intent_type == IntentType.META:
            return "meta"
        return "atomic"

    def _fill_template(self, template: str, intent: Intent) -> str:
        """填充模板"""
        # 收集可用能力
        capabilities_str = self._format_capabilities()

        # 格式化步骤（复合意图）
        steps_str = self._format_steps(intent)

        # 格式化系统状态（元意图）
        system_state_str = self._format_system_state()

        return template.format(
            intent_name=intent.name,
            goal=intent.goal,
            description=intent.description,
            capabilities=capabilities_str,
            user_id=intent.context.user_id,
            user_role=intent.context.user_role,
            session_id=intent.context.session_id,
            params=self._format_params(intent.params),
            constraints=self._format_constraints(intent.constraints),
            steps=steps_str,
            permissions=", ".join(intent.context.permissions),
            action=intent.params.get("action", "unknown"),
            system_state=system_state_str,
        )

    def _generate_user_prompt(self, intent: Intent) -> str:
        """生成用户 Prompt"""
        base_prompt = f"请执行：{intent.goal}"

        if intent.params:
            base_prompt += f"\n\n参数：{intent.params}"

        if intent.context.history:
            base_prompt += f"\n\n历史对话：{intent.context.history[-3:]}"

        return base_prompt

    def _format_capabilities(self) -> str:
        """格式化能力列表"""
        if not self.registry:
            return "（无可用能力）"

        capabilities = self.registry.list_capabilities()
        if not capabilities:
            return "（无可用能力）"

        lines = []
        for cap in capabilities:
            lines.append(f"- **{cap.name}**: {cap.description}")
            lines.append(f"  输入：{cap.input_schema}")
            lines.append(f"  输出：{cap.output_schema}")

        return "\n".join(lines)

    def _format_steps(self, intent: Intent) -> str:
        """格式化执行步骤"""
        if not intent.steps:
            return "（无预定义步骤）"

        lines = []
        for i, step in enumerate(intent.steps, 1):
            lines.append(f"**步骤 {i}**: 调用 `{step.capability_name}`")
            if step.params:
                lines.append(f"  参数：{step.params}")
            if step.condition:
                lines.append(f"  条件：{step.condition}")
            if step.output_var:
                lines.append(f"  输出绑定：${{{step.output_var}}}")

        return "\n".join(lines)

    def _format_params(self, params: dict) -> str:
        """格式化参数"""
        if not params:
            return "（无参数）"
        return "\n".join(f"- {k}: {v}" for k, v in params.items())

    def _format_constraints(self, constraints: dict) -> str:
        """格式化约束"""
        if not constraints:
            return "（无约束）"
        return "\n".join(f"- {k}: {v}" for k, v in constraints.items())

    def _format_system_state(self) -> str:
        """格式化系统状态"""
        if not self.registry:
            return "（无法获取系统状态）"

        introspect = self.registry.introspect()
        return (
            f"- 模板数量：{len(introspect.get('templates', {}))}\n"
            f"- 能力数量：{len(introspect.get('capabilities', {}))}\n"
            f"- 策略数量：{len(introspect.get('policies', {}))}"
        )

    def compile_to_json(self, intent: Intent) -> str:
        """
        将意图编译为 JSON 格式的 Prompt
        适用于支持 Function Calling 的 LLM
        """
        import json

        return json.dumps({
            "intent": {
                "name": intent.name,
                "type": intent.intent_type.value,
                "goal": intent.goal,
                "params": intent.params,
                "constraints": intent.constraints,
            },
            "context": {
                "user_id": intent.context.user_id,
                "user_role": intent.context.user_role,
                "session_id": intent.context.session_id,
            },
            "steps": [
                {
                    "capability": step.capability_name,
                    "params": step.params,
                    "condition": step.condition,
                    "output_var": step.output_var,
                }
                for step in intent.steps
            ],
        }, ensure_ascii=False, indent=2)


class PromptTemplate:
    """
    可自定义的 Prompt 模板
    """

    def __init__(self, name: str, template: str, variables: Optional[list[str]] = None):
        self.name = name
        self.template = template
        self.variables = variables or []

    def render(self, **kwargs) -> str:
        """渲染模板"""
        return self.template.format(**kwargs)

    def add_variable(self, name: str, default: Any = None) -> None:
        """添加变量"""
        if name not in self.variables:
            self.variables.append(name)
