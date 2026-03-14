"""
Core Models 模块测试 - 第 2 部分
"""

import pytest
from intentos.core.models import (
    Context,
    Capability,
    IntentStep,
    IntentStatus,
    IntentType,
)


class TestContextAdvanced:
    """Context 高级测试"""

    def test_context_has_permission_with_permission(self):
        ctx = Context(user_id="user_1", permissions=["read", "write"])
        assert ctx.has_permission("read") is True
        assert ctx.has_permission("write") is True
        assert ctx.has_permission("delete") is False

    def test_context_has_permission_admin(self):
        ctx = Context(user_id="admin", permissions=["admin"])
        assert ctx.has_permission("any_permission") is True

    def test_context_get_variable(self):
        ctx = Context(user_id="user_1", variables={"name": "test", "count": 10})
        assert ctx.get_variable("name") == "test"
        assert ctx.get_variable("count") == 10
        assert ctx.get_variable("nonexistent") is None

    def test_context_get_variable_with_default(self):
        ctx = Context(user_id="user_1")
        value = ctx.get_variable("nonexistent", default="default_value")
        assert value == "default_value"

    def test_context_set_variable(self):
        ctx = Context(user_id="user_1")
        ctx.set_variable("new_key", "new_value")
        assert ctx.variables["new_key"] == "new_value"
        assert ctx.get_variable("new_key") == "new_value"

    def test_context_update_variable(self):
        ctx = Context(user_id="user_1", variables={"count": 1})
        ctx.set_variable("count", 100)
        assert ctx.variables["count"] == 100


class TestCapabilityAdvanced:
    """Capability 高级测试"""

    def test_capability_execute_success(self):
        def echo_func(ctx, **kwargs):
            return kwargs.get("data", "echo")
        cap = Capability(
            name="echo",
            description="Echo capability",
            input_schema={},
            output_schema={},
            func=echo_func
        )
        ctx = Context(user_id="user_1")
        result = cap.execute(ctx, data="test_data")
        assert result == "test_data"

    def test_capability_execute_with_permission_check(self):
        def secure_func(ctx, **kwargs):
            return "secure_result"
        cap = Capability(
            name="secure",
            description="Secure capability",
            input_schema={},
            output_schema={},
            func=secure_func,
            requires_permissions=["admin"]
        )
        ctx_with_perm = Context(user_id="admin", permissions=["admin"])
        result = cap.execute(ctx_with_perm)
        assert result == "secure_result"
        ctx_without_perm = Context(user_id="user")
        with pytest.raises(PermissionError):
            cap.execute(ctx_without_perm)

    def test_capability_execute_missing_permission(self):
        def restricted_func(ctx, **kwargs):
            return "restricted"
        cap = Capability(
            name="restricted",
            description="Restricted capability",
            input_schema={},
            output_schema={},
            func=restricted_func,
            requires_permissions=["write"]
        )
        ctx = Context(user_id="user", permissions=["read"])
        with pytest.raises(PermissionError) as exc_info:
            cap.execute(ctx)
        assert "缺少权限" in str(exc_info.value)
        assert "write" in str(exc_info.value)


class TestIntentStepAdvanced:
    """IntentStep 高级测试"""

    def test_step_creation(self):
        step = IntentStep(capability_name="query_data", params={"region": "east"})
        assert step.capability_name == "query_data"
        assert step.params["region"] == "east"
        assert step.condition is None
        assert step.output_var is None

    def test_step_with_all_fields(self):
        step = IntentStep(
            capability_name="analyze",
            params={"data": "sales"},
            condition="data > 0",
            output_var="result"
        )
        assert step.capability_name == "analyze"
        assert step.params["data"] == "sales"
        assert step.condition == "data > 0"
        assert step.output_var == "result"

    def test_step_default_params(self):
        step = IntentStep(capability_name="simple")
        assert step.params == {}
        assert step.condition is None
        assert step.output_var is None


class TestCoreModelsIntegration:
    """Core Models 集成测试"""

    def test_context_and_capability_integration(self):
        ctx = Context(user_id="admin", permissions=["read", "write", "delete"])
        def admin_func(ctx, **kwargs):
            return {"status": "success", "user": ctx.user_id}
        cap = Capability(
            name="admin_operation",
            description="Admin operation",
            input_schema={},
            output_schema={},
            func=admin_func,
            requires_permissions=["admin"]
        )
        result = cap.execute(ctx)
        assert result["status"] == "success"
        assert result["user"] == "admin"

    def test_context_variable_sharing(self):
        ctx = Context(user_id="workflow_user")
        ctx.set_variable("query", "sales_data")
        ctx.set_variable("region", "east")
        def query_func(ctx, **kwargs):
            query = ctx.get_variable("query")
            region = ctx.get_variable("region", "all")
            return f"Querying {query} in {region}"
        cap = Capability(
            name="query",
            description="Query capability",
            input_schema={},
            output_schema={},
            func=query_func
        )
        result = cap.execute(ctx)
        assert "sales_data" in result
        assert "east" in result

    def test_multiple_capabilities_with_context(self):
        ctx = Context(user_id="workflow_user", permissions=["read", "write"], variables={"step": 0})
        def init_func(ctx, **kwargs):
            ctx.set_variable("step", 1)
            return "initialized"
        def process_func(ctx, **kwargs):
            step = ctx.get_variable("step")
            ctx.set_variable("step", step + 1)
            return "processed"
        cap1 = Capability(name="init", description="Initialize", input_schema={}, output_schema={}, func=init_func)
        cap2 = Capability(name="process", description="Process", input_schema={}, output_schema={}, func=process_func)
        result1 = cap1.execute(ctx)
        result2 = cap2.execute(ctx)
        assert result1 == "initialized"
        assert result2 == "processed"
        assert ctx.get_variable("step") == 2

    def test_step_execution_simulation(self):
        ctx = Context(user_id="test_user", permissions=["read", "write"])
        steps = [
            IntentStep(capability_name="validate", params={"input": "data"}, output_var="validated"),
            IntentStep(capability_name="transform", params={"format": "json"}, condition="validated == True", output_var="transformed"),
            IntentStep(capability_name="store", params={"destination": "database"})
        ]
        assert len(steps) == 3
        assert steps[0].capability_name == "validate"
        assert steps[1].condition == "validated == True"
        assert steps[2].output_var is None
