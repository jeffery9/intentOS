"""
意图执行引擎
负责调度、执行意图
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from ..compiler import IntentCompiler
from ..core import (
    Context,
    Intent,
    IntentExecutionResult,
    IntentStatus,
    IntentType,
)
from ..llm import LLMExecutor
from ..registry import IntentRegistry


class ExecutionEngine:
    """
    意图执行引擎
    负责解析、调度、执行意图

    支持两种执行模式:
    1. 直接执行 - 调用预注册的能力
    2. LLM 执行 - 将意图编译为 Prompt，由 LLM 决定如何执行
    """

    def __init__(
        self,
        registry: IntentRegistry,
        llm_executor: Optional[LLMExecutor] = None,
        use_llm: bool = False,
    ):
        self.registry = registry
        self.llm_executor = llm_executor or LLMExecutor(provider="mock")
        self.use_llm = use_llm  # 是否使用 LLM 执行
        self.compiler = IntentCompiler(registry)
        self._execution_history: list[IntentExecutionResult] = []

    async def execute(self, intent: Intent) -> IntentExecutionResult:
        """
        执行意图

        Args:
            intent: 待执行的意图

        Returns:
            执行结果
        """
        intent.update_status(IntentStatus.SCHEDULING)
        trace: list[dict[str, Any]] = []
        started_at = datetime.now()

        try:
            # 如果使用 LLM 执行模式
            if self.use_llm:
                result = await self._execute_with_llm(intent, trace)
            else:
                # 传统执行模式
                if intent.intent_type == IntentType.ATOMIC:
                    result = await self._execute_atomic(intent, trace)
                elif intent.intent_type == IntentType.COMPOSITE:
                    result = await self._execute_composite(intent, trace)
                elif intent.intent_type == IntentType.SCENARIO:
                    result = await self._execute_scenario(intent, trace)
                elif intent.intent_type == IntentType.META:
                    result = await self._execute_meta(intent, trace)
                else:
                    raise ValueError(f"未知意图类型：{intent.intent_type}")

            intent.update_status(IntentStatus.COMPLETED)
            intent.result = result

            return IntentExecutionResult(
                intent_id=intent.id,
                success=True,
                result=result,
                execution_trace=trace,
                started_at=started_at,
                completed_at=datetime.now(),
            )

        except Exception as e:
            intent.update_status(IntentStatus.FAILED)
            intent.error = str(e)

            return IntentExecutionResult(
                intent_id=intent.id,
                success=False,
                error=str(e),
                execution_trace=trace,
                started_at=started_at,
                completed_at=datetime.now(),
            )

    async def _execute_with_llm(self, intent: Intent, trace: list[dict]) -> Any:
        """
        使用 LLM 执行意图

        流程:
        1. 将意图编译为 Prompt
        2. LLM 分析并决定调用哪些能力
        3. 执行 LLM 选择的工具调用
        4. 返回结果
        """
        # 编译意图为 Prompt
        compiled = self.compiler.compile(intent)

        trace.append(
            {
                "step": "compile_intent",
                "template": compiled.metadata.get("template"),
                "timestamp": datetime.now().isoformat(),
            }
        )

        # LLM 执行
        llm_response = await self.llm_executor.execute(compiled.messages)  # type: ignore

        trace.append(
            {
                "step": "llm_generate",
                "content_length": len(llm_response.content),
                "tool_calls": len(llm_response.tool_calls),
                "timestamp": datetime.now().isoformat(),
            }
        )

        # 处理工具调用
        if llm_response.tool_calls:
            tool_results = []
            for tc in llm_response.tool_calls:
                capability = self.registry.get_capability(tc.name)  # type: ignore
                if capability:
                    result = capability.execute(intent.context, **tc.arguments)  # type: ignore
                    tool_results.append(
                        {
                            "tool": tc.name,  # type: ignore
                            "result": result,
                        }
                    )
                    trace.append(
                        {
                            "step": "tool_call",
                            "tool": tc.name,  # type: ignore
                            "arguments": tc.arguments,  # type: ignore
                            "result": result,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

            return {
                "llm_content": llm_response.content,
                "tool_results": tool_results,
            }

        return {
            "llm_content": llm_response.content,
        }

    async def _execute_atomic(self, intent: Intent, trace: list[dict]) -> Any:
        """执行原子意图"""
        # 查找匹配的能力
        capability = self.registry.get_capability(intent.name)

        if not capability:
            # 尝试从参数中推断能力
            if "capability" in intent.params:
                capability = self.registry.get_capability(intent.params["capability"])

        if not capability:
            raise ValueError(f"未找到能力：{intent.name}")

        # 权限检查
        for perm in capability.requires_permissions:
            if not intent.context.has_permission(perm):
                raise PermissionError(f"缺少权限：{perm}")

        trace.append(
            {
                "step": "execute_capability",
                "capability": capability.name,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # 执行能力
        result = capability.execute(intent.context, **intent.params)
        return result

    async def _execute_composite(self, intent: Intent, trace: list[dict]) -> Any:
        """执行复合意图"""
        results: dict[str, Any] = {}

        for i, step in enumerate(intent.steps):
            # 检查条件
            if step.condition and not self._evaluate_condition(
                step.condition, intent.context, results
            ):
                trace.append(
                    {
                        "step": i,
                        "action": "skipped",
                        "reason": "condition_not_met",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                continue

            trace.append(
                {
                    "step": i,
                    "capability": step.capability_name,
                    "params": step.params,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # 执行步骤
            capability = self.registry.get_capability(step.capability_name)
            if not capability:
                raise ValueError(f"步骤 {i}: 未找到能力 '{step.capability_name}'")

            # 解析参数（替换变量引用）
            resolved_params = self._resolve_params(step.params, results)

            step_result = capability.execute(intent.context, **resolved_params)

            # 绑定输出变量
            if step.output_var:
                results[step.output_var] = step_result

        return results

    async def _execute_scenario(self, intent: Intent, trace: list[dict]) -> Any:
        """执行场景意图"""
        # 场景意图本质上是预定义的复合意图
        return await self._execute_composite(intent, trace)

    async def _execute_meta(self, intent: Intent, trace: list[dict]) -> Any:
        """
        执行元意图
        元意图用于管理意图系统本身
        """
        action = intent.params.get("action")

        if action == "register_template":
            template_data = intent.params.get("template")
            # 动态创建并注册模板
            from .core import IntentTemplate

            template = IntentTemplate(**template_data)
            self.registry.register_template(template)
            return {"status": "registered", "name": template.name}

        elif action == "register_capability":
            # 动态注册能力
            cap_data = intent.params.get("capability")
            from .core import Capability

            capability = Capability(**cap_data)
            self.registry.register_capability(capability)
            return {"status": "registered", "name": capability.name}

        elif action == "introspect":
            return self.registry.introspect()

        elif action == "search":
            query = intent.params.get("query", "")
            return self.registry.search(query)

        else:
            raise ValueError(f"未知元意图动作：{action}")

    def _evaluate_condition(self, condition: str, context: Context, results: dict) -> bool:
        """评估条件表达式"""
        # 简化实现：支持基本的变量检查
        if condition.startswith("exists("):
            var_name = condition[7:-1]
            return var_name in results

        # 默认返回 True
        return True

    def _resolve_params(self, params: dict, results: dict) -> dict:
        """解析参数中的变量引用"""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1]
                resolved[key] = results.get(var_name)
            else:
                resolved[key] = value
        return resolved

    def get_execution_history(self, limit: int = 100) -> list[IntentExecutionResult]:
        """获取执行历史"""
        return self._execution_history[-limit:]
