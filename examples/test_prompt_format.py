"""
Prompt 规范测试
测试 PEF (Prompt Executable Format)
"""

import pytest
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
    create_sales_analysis_prompt,
)


class TestPromptMetadata:
    """测试元数据段"""
    
    def test_metadata_creation(self):
        """测试元数据创建"""
        metadata = PromptMetadata(
            name="test_prompt",
            description="测试 Prompt",
            author="tester",
        )
        
        assert metadata.name == "test_prompt"
        assert metadata.version == "1.0.0"
        assert metadata.execution_mode == ExecutionMode.SYNC.value
    
    def test_metadata_to_dict(self):
        """测试元数据序列化"""
        metadata = PromptMetadata(name="test")
        d = metadata.to_dict()
        
        assert d["name"] == "test"
        assert d["version"] == "1.0.0"
    
    def test_metadata_with_tags(self):
        """测试带标签的元数据"""
        metadata = PromptMetadata(
            name="test",
            tags=["sales", "analysis"],
            priority=8,
        )
        
        assert len(metadata.tags) == 2
        assert metadata.priority == 8


class TestIntentDeclaration:
    """测试意图声明段"""
    
    def test_functional_intent(self):
        """测试功能意图"""
        intent = IntentDeclaration(
            goal="生成销售报告",
            intent_type="functional",
            expected_outcome="PDF 格式报告",
        )
        
        assert intent.intent_type == "functional"
        assert intent.performance_targets == {}
    
    def test_operational_intent(self):
        """测试操作意图"""
        intent = IntentDeclaration(
            goal="确保 API 可用性≥99.9%",
            intent_type="operational",
            performance_targets={
                "latency_p99_ms": 100,
                "availability": 99.9,
            },
        )
        
        assert intent.intent_type == "operational"
        assert intent.performance_targets["latency_p99_ms"] == 100
    
    def test_intent_to_dict(self):
        """测试意图序列化"""
        intent = IntentDeclaration(
            goal="test",
            inputs={"key": "value"},
        )
        d = intent.to_dict()
        
        assert d["goal"] == "test"
        assert d["inputs"]["key"] == "value"


class TestContextBinding:
    """测试上下文绑定段"""
    
    def test_context_creation(self):
        """测试上下文创建"""
        context = ContextBinding(
            user_id="user_001",
            user_role="admin",
        )
        
        assert context.user_id == "user_001"
        assert context.user_role == "admin"
    
    def test_context_with_event_graph(self):
        """测试带事件图的上下文"""
        context = ContextBinding(
            user_id="user_001",
            event_graph=[
                {"type": "metric", "source": "prometheus"},
                {"type": "log", "source": "elasticsearch"},
            ],
        )
        
        assert len(context.event_graph) == 2
        assert context.event_graph[0]["type"] == "metric"


class TestCapabilityBinding:
    """测试能力绑定段"""
    
    def test_capability_creation(self):
        """测试能力创建"""
        cap = CapabilityBinding(
            name="query_data",
            protocol="http",
            endpoint="https://api.example.com",
        )
        
        assert cap.name == "query_data"
        assert cap.protocol == "http"
    
    def test_llm_capability(self):
        """测试 LLM 能力"""
        cap = CapabilityBinding(
            name="analyze",
            protocol="llm",
            llm_config={"model": "gpt-4o", "temperature": 0.7},
        )
        
        assert cap.protocol == "llm"
        assert cap.llm_config["model"] == "gpt-4o"
    
    def test_capability_with_fallback(self):
        """测试带降级的能力"""
        cap = CapabilityBinding(
            name="primary",
            fallback=["backup1", "backup2"],
        )
        
        assert len(cap.fallback) == 2


class TestWorkflowDefinition:
    """测试工作流定义"""
    
    def test_workflow_step_creation(self):
        """测试工作流步骤"""
        step = WorkflowStep(
            id="step1",
            name="查询数据",
            capability="query_data",
            params={"region": "华东"},
        )
        
        assert step.id == "step1"
        assert len(step.depends_on) == 0
    
    def test_workflow_with_dependencies(self):
        """测试带依赖的工作流"""
        steps = [
            WorkflowStep(id="step1", name="步骤 1", capability="cap1"),
            WorkflowStep(id="step2", name="步骤 2", capability="cap2", depends_on=["step1"]),
            WorkflowStep(id="step3", name="步骤 3", capability="cap3", depends_on=["step1", "step2"]),
        ]
        
        workflow = WorkflowDefinition(steps=steps)
        
        assert len(workflow.steps) == 3
        assert workflow.steps[2].depends_on == ["step1", "step2"]
    
    def test_workflow_to_dict(self):
        """测试工作流序列化"""
        step = WorkflowStep(
            id="step1",
            name="test",
            capability="test_cap",
            output_var="result",
        )
        workflow = WorkflowDefinition(steps=[step])
        d = workflow.to_dict()
        
        assert len(d["steps"]) == 1
        assert d["steps"][0]["output_var"] == "result"


class TestOpsModel:
    """测试运维模型段"""
    
    def test_ops_model_creation(self):
        """测试运维模型创建"""
        ops = OpsModel(
            slo_targets={"latency_p99_ms": 100},
            metrics_to_collect=["duration", "cost"],
        )
        
        assert ops.slo_targets["latency_p99_ms"] == 100
        assert len(ops.metrics_to_collect) == 2
    
    def test_ops_model_with_alerts(self):
        """测试带告警的运维模型"""
        ops = OpsModel(
            alert_rules=[
                {"condition": "latency > 100ms", "notify": "slack"},
            ],
            auto_remediation=[
                {"trigger": "timeout", "action": "retry"},
            ],
        )
        
        assert len(ops.alert_rules) == 1
        assert len(ops.auto_remediation) == 1


class TestSafetyPolicy:
    """测试安全策略段"""
    
    def test_safety_policy_creation(self):
        """测试安全策略创建"""
        policy = SafetyPolicy(
            level=SafetyLevel.MEDIUM.value,
        )
        
        assert policy.level == SafetyLevel.MEDIUM.value
    
    def test_critical_safety_policy(self):
        """测试关键安全策略"""
        policy = SafetyPolicy(
            level=SafetyLevel.CRITICAL.value,
            approvers=["admin1", "admin2"],
            approval_timeout_minutes=15,
        )
        
        assert policy.level == SafetyLevel.CRITICAL.value
        assert len(policy.approvers) == 2
    
    def test_safety_policy_with_audit(self):
        """测试带审计的安全策略"""
        policy = SafetyPolicy(
            audit_config={
                "log_all_actions": True,
                "retention_days": 365,
            },
        )
        
        assert policy.audit_config["log_all_actions"] is True


class TestPromptExecutable:
    """测试完整的 Prompt 可执行文件"""
    
    def test_prompt_creation(self):
        """测试 Prompt 创建"""
        prompt = PromptExecutable(
            metadata=PromptMetadata(name="test_prompt"),
            intent=IntentDeclaration(goal="测试目标"),
        )
        
        assert prompt.metadata.name == "test_prompt"
        assert prompt.intent.goal == "测试目标"
    
    def test_prompt_to_yaml(self):
        """测试 Prompt 导出为 YAML"""
        prompt = PromptExecutable(
            metadata=PromptMetadata(name="test"),
            intent=IntentDeclaration(goal="test goal"),
        )
        
        yaml_str = prompt.to_yaml()
        
        assert "name: test" in yaml_str
        assert "test goal" in yaml_str
    
    def test_prompt_to_json(self):
        """测试 Prompt 导出为 JSON"""
        prompt = PromptExecutable(
            metadata=PromptMetadata(name="test"),
            intent=IntentDeclaration(goal="test goal"),
        )
        
        json_str = prompt.to_json()
        
        assert '"name": "test"' in json_str
        assert '"goal": "test goal"' in json_str
    
    def test_prompt_from_yaml(self):
        """测试从 YAML 加载 Prompt"""
        yaml_str = """
metadata:
  name: loaded_prompt
intent:
  goal: loaded goal
  intent_type: functional
"""
        prompt = PromptExecutable.from_yaml(yaml_str)
        
        assert prompt.metadata.name == "loaded_prompt"
        assert prompt.intent.goal == "loaded goal"
    
    def test_prompt_from_json(self):
        """测试从 JSON 加载 Prompt"""
        json_str = """
{
  "metadata": {"name": "json_prompt"},
  "intent": {"goal": "json goal", "intent_type": "functional"}
}
"""
        prompt = PromptExecutable.from_json(json_str)
        
        assert prompt.metadata.name == "json_prompt"
        assert prompt.intent.goal == "json goal"
    
    def test_prompt_validation_success(self):
        """测试 Prompt 验证成功"""
        prompt = PromptExecutable(
            metadata=PromptMetadata(name="valid_prompt"),
            intent=IntentDeclaration(goal="valid goal"),
        )
        
        errors = prompt.validate()
        assert len(errors) == 0
    
    def test_prompt_validation_missing_name(self):
        """测试验证：缺少名称"""
        prompt = PromptExecutable(
            metadata=PromptMetadata(),  # 没有 name
            intent=IntentDeclaration(goal="goal"),
        )
        
        errors = prompt.validate()
        assert any("name" in e for e in errors)
    
    def test_prompt_validation_missing_goal(self):
        """测试验证：缺少目标"""
        prompt = PromptExecutable(
            metadata=PromptMetadata(name="test"),
            intent=IntentDeclaration(),  # 没有 goal
        )
        
        errors = prompt.validate()
        assert any("goal" in e for e in errors)
    
    def test_prompt_validation_workflow_dependency(self):
        """测试验证：工作流依赖检查"""
        prompt = PromptExecutable(
            metadata=PromptMetadata(name="test"),
            intent=IntentDeclaration(goal="goal"),
            workflow=WorkflowDefinition(
                steps=[
                    WorkflowStep(
                        id="step1",
                        name="test",
                        capability="cap",
                        depends_on=["non_existent_step"],
                    ),
                ],
            ),
        )
        
        errors = prompt.validate()
        assert any("non_existent_step" in e for e in errors)
    
    def test_prompt_validation_critical_safety(self):
        """测试验证：关键安全需要审批人"""
        prompt = PromptExecutable(
            metadata=PromptMetadata(name="test"),
            intent=IntentDeclaration(goal="goal"),
            safety=SafetyPolicy(
                level=SafetyLevel.CRITICAL.value,
                approvers=[],  # 没有审批人
            ),
        )
        
        errors = prompt.validate()
        assert any("approver" in e for e in errors)


class TestPromptTemplates:
    """测试 Prompt 模板"""
    
    def test_create_sales_analysis_prompt(self):
        """测试创建销售分析 Prompt"""
        prompt = create_sales_analysis_prompt()
        
        assert prompt.metadata.name == "sales_analysis_q3"
        assert prompt.intent.intent_type == "functional"
        assert len(prompt.workflow.steps) == 4
        assert len(prompt.capabilities) == 3
        
        # 验证
        errors = prompt.validate()
        assert len(errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
