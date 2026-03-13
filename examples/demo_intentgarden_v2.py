"""
IntentGarden v2.0 演示
展示 Prompt 规范和七层架构执行流程
"""

import asyncio
from intentos.prompt_format import (
    PromptExecutable,
    PromptMetadata,
    IntentDeclaration,
    ContextBinding,
    CapabilityBinding,
    ConstraintDefinition,
    WorkflowDefinition,
    WorkflowStep,
    OpsModel,
    SafetyPolicy,
    SafetyLevel,
    ExecutionMode,
)
from intentos.intentgarden_v2 import IntentGarden


def create_operational_intent_prompt() -> PromptExecutable:
    """创建操作性意图 Prompt 示例"""
    return PromptExecutable(
        metadata=PromptMetadata(
            name="api_latency_optimization",
            description="优化 API 延迟，确保 99% 请求延迟≤100ms",
            author="sre_team",
            tags=["sre", "optimization", "sla"],
            execution_mode=ExecutionMode.DAG.value,
        ),
        intent=IntentDeclaration(
            goal="分析并优化订单服务 API 延迟",
            intent_type="operational",
            expected_outcome="P99 延迟≤100ms，错误率≤0.1%",
            performance_targets={
                "latency_p99_ms": 100,
                "availability": 99.9,
                "error_rate": 0.001,
            },
            inputs={
                "service": "order-service",
                "namespace": "production",
                "time_range": "last_24h",
            },
            output_format="action_plan",
        ),
        context=ContextBinding(
            user_id="sre_engineer_001",
            user_role="sre",
            business_context={
                "priority": "P0",
                "incident_id": "INC-2024-001",
            },
            technical_context={
                "cluster": "prod-us-east-1",
                "namespace": "default",
                "service": "order-service",
            },
            event_graph=[
                {
                    "type": "metric",
                    "source": "prometheus",
                    "query": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))",
                },
                {
                    "type": "log",
                    "source": "elasticsearch",
                    "query": "service:order-service level:ERROR",
                },
                {
                    "type": "alert",
                    "source": "pagerduty",
                    "alert_id": "PD-12345",
                },
            ],
        ),
        capabilities=[
            CapabilityBinding(
                name="query_metrics",
                protocol="http",
                endpoint="https://prometheus.example.com/api/v1/query",
            ),
            CapabilityBinding(
                name="analyze_logs",
                protocol="http",
                endpoint="https://elasticsearch.example.com/search",
            ),
            CapabilityBinding(
                name="root_cause_analysis",
                protocol="llm",
                llm_config={"model": "gpt-4o", "temperature": 0.2},
            ),
            CapabilityBinding(
                name="generate_runbook",
                protocol="llm",
                llm_config={"model": "gpt-4o", "temperature": 0.5},
            ),
        ],
        constraints=ConstraintDefinition(
            resource_limits={
                "max_tokens": 50000,
                "max_api_calls": 50,
                "budget_usd": 5.0,
            },
            time_constraints={
                "deadline": "2024-12-31T23:59:59Z",
            },
            compliance_rules=[
                "SOC2: audit_all_actions",
                "GDPR: no_pii_in_logs",
            ],
        ),
        workflow=WorkflowDefinition(
            steps=[
                WorkflowStep(
                    id="collect_metrics",
                    name="收集性能指标",
                    capability="query_metrics",
                    params={
                        "query": "http_request_duration_seconds",
                        "percentile": 99,
                    },
                    output_var="metrics",
                ),
                WorkflowStep(
                    id="analyze_logs",
                    name="分析错误日志",
                    capability="analyze_logs",
                    depends_on=["collect_metrics"],
                    params={
                        "service": "order-service",
                        "level": "ERROR",
                    },
                    output_var="log_analysis",
                ),
                WorkflowStep(
                    id="root_cause",
                    name="根因分析",
                    capability="root_cause_analysis",
                    depends_on=["collect_metrics", "analyze_logs"],
                    params={
                        "metrics": "${metrics}",
                        "logs": "${log_analysis}",
                    },
                    output_var="rca",
                ),
                WorkflowStep(
                    id="generate_plan",
                    name="生成优化方案",
                    capability="generate_runbook",
                    depends_on=["root_cause"],
                    params={
                        "rca": "${rca}",
                        "target_latency_ms": 100,
                    },
                    output_var="action_plan",
                ),
            ],
            success_condition="all_steps_completed",
            on_error=[
                {"action": "retry", "max_attempts": 3},
                {"action": "notify", "channel": "sre-slack"},
            ],
        ),
        ops_model=OpsModel(
            slo_targets={
                "latency_p99_ms": 100,
                "availability_percent": 99.9,
            },
            metrics_to_collect=[
                "execution_duration",
                "token_usage",
                "api_call_count",
                "cost_usd",
            ],
            alert_rules=[
                {
                    "condition": "execution_duration > 60s",
                    "notify": "team-slack",
                },
                {
                    "condition": "cost_usd > 10",
                    "notify": "finance-alert",
                },
            ],
            auto_remediation=[
                {
                    "trigger": "model_timeout",
                    "action": "switch_to_backup_model",
                },
            ],
        ),
        safety=SafetyPolicy(
            level=SafetyLevel.MEDIUM.value,
            requires_approval_for=[
                "deploy_to_production",
                "change_database_schema",
            ],
            approvers=["tech_lead", "oncall_manager"],
            approval_timeout_minutes=30,
            audit_config={
                "log_all_actions": True,
                "retention_days": 365,
            },
        ),
    )


async def demo_intentgarden_v2():
    """演示 IntentGarden v2.0"""
    print("=" * 70)
    print("IntentGarden v2.0 - Cloud-Native AI 原生操作系统")
    print("=" * 70)
    print()
    
    # 创建 Prompt
    prompt = create_operational_intent_prompt()
    
    print("📄 Prompt 规范预览:")
    print("-" * 40)
    print(f"  名称：{prompt.metadata.name}")
    print(f"  类型：{prompt.intent.intent_type}")
    print(f"  目标：{prompt.intent.goal}")
    print(f"  安全等级：{prompt.safety.level}")
    print(f"  工作流步骤：{len(prompt.workflow.steps)}")
    print()
    
    # 验证 Prompt
    errors = prompt.validate()
    if errors:
        print("❌ 验证错误:")
        for e in errors:
            print(f"  - {e}")
        return
    print("✅ Prompt 验证通过")
    print()
    
    # 导出为 YAML
    print("📋 Prompt YAML (部分):")
    print("-" * 40)
    yaml_str = prompt.to_yaml()
    # 只显示前 1000 字符
    print(yaml_str[:1000] + "...")
    print()
    
    # 执行
    print("🚀 执行七层架构处理流程...")
    print("-" * 40)
    
    garden = IntentGarden()
    garden.initialize()
    
    result = await garden.execute(prompt)
    
    print()
    print("📊 执行结果:")
    print("-" * 40)
    
    for layer_name, layer_result in result["layer_results"].items():
        status = "✅" if layer_result["success"] else "❌"
        duration = layer_result["metrics"].get("duration_ms", 0)
        print(f"{status} {layer_name}: {duration}ms")
    
    print()
    print(f"总耗时：{result['total_duration_ms']}ms")
    print()
    
    # 导出为 JSON
    print("📄 导出为 JSON:")
    print("-" * 40)
    json_str = prompt.to_json()
    print(json_str[:500] + "...")


async def demo_prompt_formats():
    """演示不同格式的 Prompt"""
    print("\n" + "=" * 70)
    print("Prompt 格式示例对比")
    print("=" * 70)
    
    # 功能意图 Prompt
    functional_prompt = PromptExecutable(
        metadata=PromptMetadata(name="sales_report", tags=["sales", "report"]),
        intent=IntentDeclaration(
            goal="生成 Q3 销售报告",
            intent_type="functional",
            expected_outcome="PDF 格式报告",
        ),
    )
    
    # 操作意图 Prompt
    operational_prompt = PromptExecutable(
        metadata=PromptMetadata(name="api_sla", tags=["sre", "sla"]),
        intent=IntentDeclaration(
            goal="确保 API 可用性≥99.9%",
            intent_type="operational",
            performance_targets={"availability": 99.9},
        ),
    )
    
    print("\n功能意图 Prompt:")
    print("-" * 40)
    print(f"  目标：{functional_prompt.intent.goal}")
    print(f"  类型：{functional_prompt.intent.intent_type}")
    
    print("\n操作意图 Prompt:")
    print("-" * 40)
    print(f"  目标：{operational_prompt.intent.goal}")
    print(f"  类型：{operational_prompt.intent.intent_type}")
    print(f"  SLO 目标：{operational_prompt.intent.performance_targets}")


async def main():
    """运行所有演示"""
    print("\n" + "=" * 70)
    print("IntentGarden v2.0 - Prompt 规范演示")
    print("Prompt 作为 AI 原生操作系统的'可执行文件格式'")
    print("=" * 70 + "\n")
    
    await demo_prompt_formats()
    await demo_intentgarden_v2()
    
    print("\n" + "=" * 70)
    print("演示完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
