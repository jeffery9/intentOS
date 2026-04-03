"""
IntentGarden v2.0 - 七层架构实现

Cloud-Native 风格的 AI 原生操作系统
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .compiler import IntentCompiler
from .core import Intent, IntentType
from .llm import LLMExecutor
from .prompt_format import (
    IntentDeclaration,
    PromptExecutable,
    SafetyLevel,
)
from .registry import IntentRegistry

# =============================================================================
# 七层架构实现
# =============================================================================

@dataclass
class LayerResult:
    """层执行结果"""
    layer_name: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    metrics: dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0


class IntentLayer:
    """
    L1: 意图层
    解析功能意图 + 操作意图
    """

    def __init__(self, registry: IntentRegistry):
        self.registry = registry
        self.compiler = IntentCompiler(registry)

    async def process(self, prompt: PromptExecutable) -> LayerResult:
        """处理意图层"""
        start = datetime.now()

        try:
            # 解析功能意图
            functional_intent = self._parse_functional_intent(prompt.intent)

            # 解析操作意图 (SLO/SLA)
            operational_intent = self._parse_operational_intent(prompt.ops_model)

            # 编译为执行计划
            execution_plan = self.compiler.compile(functional_intent)

            duration = int((datetime.now() - start).total_seconds() * 1000)

            return LayerResult(
                layer_name="IntentLayer",
                success=True,
                output={
                    "functional_intent": functional_intent,
                    "operational_intent": operational_intent,
                    "execution_plan": execution_plan,
                },
                metrics={"duration_ms": duration},
                duration_ms=duration,
            )
        except Exception as e:
            return LayerResult(
                layer_name="IntentLayer",
                success=False,
                error=str(e),
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )

    def _parse_functional_intent(self, intent_decl: IntentDeclaration) -> Intent:
        """解析功能意图"""
        return Intent(
            name="functional_intent",
            intent_type=IntentType.COMPOSITE,
            goal=intent_decl.goal,
            description=intent_decl.expected_outcome,
            params=intent_decl.inputs,
        )

    def _parse_operational_intent(self, ops_model: Any) -> dict:
        """解析操作意图"""
        return {
            "slo_targets": ops_model.slo_targets,
            "metrics_to_collect": ops_model.metrics_to_collect,
            "alert_rules": ops_model.alert_rules,
        }


class PlanningLayer:
    """
    L2: 规划层
    生成任务 DAG + Ops Model
    """

    async def process(self, prompt: PromptExecutable, intent_result: LayerResult) -> LayerResult:
        """处理规划层"""
        start = datetime.now()

        try:
            # 从工作流生成 DAG
            dag = self._build_dag(prompt.workflow)

            # 编译 Ops Model
            ops_config = self._compile_ops_model(prompt.ops_model)

            duration = int((datetime.now() - start).total_seconds() * 1000)

            return LayerResult(
                layer_name="PlanningLayer",
                success=True,
                output={
                    "dag": dag,
                    "ops_config": ops_config,
                },
                metrics={"duration_ms": duration, "steps_count": len(dag)},
                duration_ms=duration,
            )
        except Exception as e:
            return LayerResult(
                layer_name="PlanningLayer",
                success=False,
                error=str(e),
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )

    def _build_dag(self, workflow: Any) -> list[dict]:
        """构建任务 DAG"""
        dag = []
        for step in workflow.steps:
            dag.append({
                "id": step.id,
                "name": step.name,
                "capability": step.capability,
                "dependencies": step.depends_on,
                "params": step.params,
                "condition": step.condition,
            })
        return dag

    def _compile_ops_model(self, ops_model: Any) -> dict:
        """编译运维模型"""
        return {
            "slo_targets": ops_model.slo_targets,
            "metrics": ops_model.metrics_to_collect,
            "alerts": ops_model.alert_rules,
            "auto_remediation": ops_model.auto_remediation,
        }


class ContextLayer:
    """
    L3: 上下文层
    多模态事件图（指标/日志/代码/文档）
    """

    async def process(self, prompt: PromptExecutable) -> LayerResult:
        """处理上下文层"""
        start = datetime.now()

        try:
            # 收集多模态上下文
            context_graph = self._collect_context(prompt.context)

            duration = int((datetime.now() - start).total_seconds() * 1000)

            return LayerResult(
                layer_name="ContextLayer",
                success=True,
                output={"context_graph": context_graph},
                metrics={
                    "duration_ms": duration,
                    "events_count": len(context_graph.get("event_graph", [])),
                },
                duration_ms=duration,
            )
        except Exception as e:
            return LayerResult(
                layer_name="ContextLayer",
                success=False,
                error=str(e),
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )

    def _collect_context(self, context_binding: Any) -> dict:
        """收集上下文"""
        return {
            "user_id": context_binding.user_id,
            "user_role": context_binding.user_role,
            "business_context": context_binding.business_context,
            "technical_context": context_binding.technical_context,
            "event_graph": context_binding.event_graph,
        }


class SafetyRing:
    """
    L4: 安全环
    权限校验 + Human-in-the-loop 审批
    """

    def __init__(self, registry: IntentRegistry):
        self.registry = registry

    async def process(self, prompt: PromptExecutable, context: dict) -> LayerResult:
        """处理安全环"""
        start = datetime.now()

        try:
            safety_policy = prompt.safety

            # 权限校验
            permission_check = self._check_permissions(context, safety_policy)

            # 检查是否需要人工审批
            requires_approval = self._check_approval_required(safety_policy)

            if requires_approval:
                # 触发人工审批流程
                approval_result = await self._request_approval(safety_policy, context)
                if not approval_result["approved"]:
                    raise PermissionError("审批未通过")

            duration = int((datetime.now() - start).total_seconds() * 1000)

            return LayerResult(
                layer_name="SafetyRing",
                success=True,
                output={
                    "permission_check": permission_check,
                    "requires_approval": requires_approval,
                    "safety_level": safety_policy.level,
                },
                metrics={"duration_ms": duration},
                duration_ms=duration,
            )
        except Exception as e:
            return LayerResult(
                layer_name="SafetyRing",
                success=False,
                error=str(e),
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )

    def _check_permissions(self, context: dict, policy: Any) -> bool:
        """检查权限"""
        # 简化实现
        return True

    def _check_approval_required(self, policy: Any) -> bool:
        """检查是否需要审批"""
        return policy.level in [SafetyLevel.HIGH.value, SafetyLevel.CRITICAL.value]

    async def _request_approval(self, policy: Any, context: dict) -> dict:
        """请求审批"""
        # 简化实现：自动通过
        # 实际实现应该发送通知给审批人并等待响应
        return {"approved": True, "approver": "auto_approved_for_demo"}


class ToolLayer:
    """
    L5: 工具层
    绑定能力调用（API/LLM/传统软件）
    """

    def __init__(self, registry: IntentRegistry):
        self.registry = registry

    async def process(self, prompt: PromptExecutable, dag: list[dict]) -> LayerResult:
        """处理工具层"""
        start = datetime.now()

        try:
            # 绑定能力
            bound_capabilities = self._bind_capabilities(prompt.capabilities)

            duration = int((datetime.now() - start).total_seconds() * 1000)

            return LayerResult(
                layer_name="ToolLayer",
                success=True,
                output={
                    "bound_capabilities": bound_capabilities,
                    "dag_ready": True,
                },
                metrics={
                    "duration_ms": duration,
                    "capabilities_count": len(bound_capabilities),
                },
                duration_ms=duration,
            )
        except Exception as e:
            return LayerResult(
                layer_name="ToolLayer",
                success=False,
                error=str(e),
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )

    def _bind_capabilities(self, capabilities: list) -> list[dict]:
        """绑定能力"""
        bound = []
        for cap in capabilities:
            # 查找注册的能力
            registered_cap = self.registry.get_capability(cap.name)
            bound.append({
                "name": cap.name,
                "endpoint": cap.endpoint,
                "protocol": cap.protocol,
                "llm_config": cap.llm_config,
                "fallback": cap.fallback,
                "registered": registered_cap is not None,
            })
        return bound


class ExecutionLayer:
    """
    L6: 执行层
    分布式调度执行
    """

    def __init__(self, registry: IntentRegistry, llm_executor: LLMExecutor):
        self.registry = registry
        self.llm_executor = llm_executor

    async def process(self, dag: list[dict], capabilities: list[dict]) -> LayerResult:
        """处理执行层"""
        start = datetime.now()

        try:
            # 执行 DAG
            results = await self._execute_dag(dag, capabilities)

            duration = int((datetime.now() - start).total_seconds() * 1000)

            return LayerResult(
                layer_name="ExecutionLayer",
                success=True,
                output={"step_results": results},
                metrics={
                    "duration_ms": duration,
                    "steps_executed": len(results),
                },
                duration_ms=duration,
            )
        except Exception as e:
            return LayerResult(
                layer_name="ExecutionLayer",
                success=False,
                error=str(e),
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )

    async def _execute_dag(self, dag: list[dict], capabilities: list[dict]) -> list[dict]:
        """执行 DAG"""
        results = []
        completed_steps = set()

        # 拓扑排序执行
        for step in dag:
            # 检查依赖
            deps_met = all(dep in completed_steps for dep in step["dependencies"])
            if not deps_met:
                continue

            # 执行步骤
            result = await self._execute_step(step, capabilities)
            results.append(result)
            completed_steps.add(step["id"])

        return results

    async def _execute_step(self, step: dict, capabilities: list[dict]) -> dict:
        """执行单个步骤"""
        # 简化实现
        return {
            "step_id": step["id"],
            "status": "completed",
            "result": {},
        }


class ImprovementLayer:
    """
    L7: 改进层
    意图漂移检测与修复
    """

    async def process(
        self,
        prompt: PromptExecutable,
        execution_result: LayerResult,
        ops_model: dict,
    ) -> LayerResult:
        """处理改进层"""
        start = datetime.now()

        try:
            # 检测意图漂移
            drift_detected = self._detect_drift(prompt, execution_result)

            # 生成改进建议
            improvements = self._generate_improvements(drift_detected, ops_model)

            duration = int((datetime.now() - start).total_seconds() * 1000)

            return LayerResult(
                layer_name="ImprovementLayer",
                success=True,
                output={
                    "drift_detected": drift_detected,
                    "improvements": improvements,
                },
                metrics={"duration_ms": duration},
                duration_ms=duration,
            )
        except Exception as e:
            return LayerResult(
                layer_name="ImprovementLayer",
                success=False,
                error=str(e),
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )

    def _detect_drift(self, prompt: PromptExecutable, result: LayerResult) -> list[dict]:
        """检测意图漂移"""
        # 简化实现：检查 SLO 是否达成
        drifts = []

        slo_targets = prompt.ops_model.slo_targets
        if "latency_p99_ms" in slo_targets:
            actual_latency = result.metrics.get("duration_ms", 0)
            if actual_latency > slo_targets["latency_p99_ms"]:
                drifts.append({
                    "type": "slo_violation",
                    "metric": "latency",
                    "target": slo_targets["latency_p99_ms"],
                    "actual": actual_latency,
                })

        return drifts

    def _generate_improvements(self, drifts: list[dict], ops_model: dict) -> list[dict]:
        """生成改进建议"""
        improvements = []

        for drift in drifts:
            if drift["type"] == "slo_violation":
                improvements.append({
                    "type": "optimize_latency",
                    "suggestion": "考虑使用更小的模型或优化 Prompt",
                    "priority": "high",
                })

        return improvements


# =============================================================================
# IntentGarden v2.0 主类
# =============================================================================

class IntentGarden:
    """
    IntentGarden v2.0
    Cloud-Native AI 原生操作系统
    """

    def __init__(self):
        self.registry = IntentRegistry()
        self.llm_executor = LLMExecutor(provider="mock")

        # 初始化七层架构
        self.layers = {
            "intent": IntentLayer(self.registry),
            "planning": PlanningLayer(),
            "context": ContextLayer(),
            "safety": SafetyRing(self.registry),
            "tool": ToolLayer(self.registry),
            "execution": ExecutionLayer(self.registry, self.llm_executor),
            "improvement": ImprovementLayer(),
        }

        self._initialized = False

    def initialize(self) -> None:
        """初始化系统"""
        self._register_builtin_capabilities()
        self._initialized = True

    def _register_builtin_capabilities(self) -> None:
        """注册内置能力"""
        # 简化实现
        pass

    async def execute(self, prompt: PromptExecutable) -> dict:
        """
        执行 Prompt

        七层处理流程:
        L1: 意图解析
        L2: 规划 DAG
        L3: 上下文收集
        L4: 安全检查
        L5: 工具绑定
        L6: 执行
        L7: 改进
        """
        if not self._initialized:
            self.initialize()

        results = {}
        context = {}

        # L1: 意图层
        intent_result = await self.layers["intent"].process(prompt)
        results["intent"] = intent_result
        if not intent_result.success:
            return self._build_final_result(results, success=False)

        # L2: 规划层
        planning_result = await self.layers["planning"].process(prompt, intent_result)
        results["planning"] = planning_result
        if not planning_result.success:
            return self._build_final_result(results, success=False)

        # L3: 上下文层
        context_result = await self.layers["context"].process(prompt)
        results["context"] = context_result
        context = context_result.output or {}

        # L4: 安全环
        safety_result = await self.layers["safety"].process(prompt, context)
        results["safety"] = safety_result
        if not safety_result.success:
            return self._build_final_result(results, success=False)

        # L5: 工具层
        tool_result = await self.layers["tool"].process(prompt, planning_result.output["dag"])
        results["tool"] = tool_result
        if not tool_result.success:
            return self._build_final_result(results, success=False)

        # L6: 执行层
        execution_result = await self.layers["execution"].process(
            planning_result.output["dag"],
            tool_result.output["bound_capabilities"],
        )
        results["execution"] = execution_result
        if not execution_result.success:
            return self._build_final_result(results, success=False)

        # L7: 改进层
        improvement_result = await self.layers["improvement"].process(
            prompt,
            execution_result,
            planning_result.output["ops_config"],
        )
        results["improvement"] = improvement_result

        return self._build_final_result(results, success=True)

    def _build_final_result(self, layer_results: dict, success: bool) -> dict:
        """构建最终结果"""
        return {
            "success": success,
            "layer_results": {
                name: {
                    "success": result.success,
                    "metrics": result.metrics,
                    "error": result.error,
                }
                for name, result in layer_results.items()
            },
            "total_duration_ms": sum(
                r.metrics.get("duration_ms", 0)
                for r in layer_results.values()
            ),
        }


if __name__ == "__main__":
    import asyncio

    from prompt_format import create_sales_analysis_prompt

    async def main():
        garden = IntentGarden()
        prompt = create_sales_analysis_prompt()

        result = await garden.execute(prompt)

        print("=" * 60)
        print("IntentGarden v2.0 执行结果")
        print("=" * 60)
        print()

        for layer_name, layer_result in result["layer_results"].items():
            status = "✅" if layer_result["success"] else "❌"
            print(f"{status} {layer_name}: {layer_result['metrics']}")

        print(f"\n总耗时：{result['total_duration_ms']}ms")

    asyncio.run(main())
