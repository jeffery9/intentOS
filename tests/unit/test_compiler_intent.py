"""
Intent Compiler 模块测试
"""

import pytest
from intentos.compiler.compiler import (
    CompiledPrompt,
    IntentCompiler,
)
from intentos.core import Intent, IntentType


class TestCompiledPrompt:
    """CompiledPrompt 测试"""

    def test_compiled_prompt_creation(self):
        """测试编译后的 Prompt 创建"""
        intent = Intent(name="test", intent_type=IntentType.ATOMIC)
        prompt = CompiledPrompt(
            system_prompt="System",
            user_prompt="User",
            intent=intent
        )
        assert prompt.system_prompt == "System"
        assert prompt.user_prompt == "User"

    def test_compiled_prompt_with_metadata(self):
        """测试带元数据的编译 Prompt"""
        intent = Intent(name="test", intent_type=IntentType.ATOMIC)
        prompt = CompiledPrompt(
            system_prompt="System",
            user_prompt="User",
            intent=intent,
            metadata={"key": "value"}
        )
        assert prompt.metadata["key"] == "value"

    def test_compiled_prompt_default_metadata(self):
        """测试默认元数据"""
        intent = Intent(name="test", intent_type=IntentType.ATOMIC)
        prompt = CompiledPrompt(
            system_prompt="System",
            user_prompt="User",
            intent=intent
        )
        assert prompt.metadata == {}

    def test_compiled_prompt_messages(self):
        """测试消息格式"""
        intent = Intent(name="test", intent_type=IntentType.ATOMIC)
        prompt = CompiledPrompt(
            system_prompt="System prompt",
            user_prompt="User prompt",
            intent=intent
        )
        messages = prompt.messages
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"


class TestIntentCompiler:
    """IntentCompiler 测试"""

    def test_compiler_creation(self):
        """测试编译器创建"""
        compiler = IntentCompiler()
        assert compiler is not None
        assert compiler._prompt_templates != {}

    def test_compiler_with_registry(self):
        """测试带注册表的编译器"""
        class MockRegistry:
            pass
        registry = MockRegistry()
        compiler = IntentCompiler(registry=registry)
        assert compiler.registry == registry

    def test_compiler_default_templates(self):
        """测试默认模板"""
        compiler = IntentCompiler()
        assert "atomic" in compiler._prompt_templates
        assert "composite" in compiler._prompt_templates

    def test_compile_atomic_intent(self):
        """测试编译原子意图"""
        compiler = IntentCompiler()
        intent = Intent(
            name="test_intent",
            intent_type=IntentType.ATOMIC,
            goal="Test goal",
            description="Test description"
        )
        result = compiler.compile(intent)
        assert result is not None
        assert isinstance(result, CompiledPrompt)

    def test_compile_composite_intent(self):
        """测试编译复合意图"""
        compiler = IntentCompiler()
        intent = Intent(
            name="composite_intent",
            intent_type=IntentType.COMPOSITE,
            goal="Composite goal"
        )
        result = compiler.compile(intent)
        assert result is not None

    def test_compile_scenario_intent(self):
        """测试编译场景意图"""
        compiler = IntentCompiler()
        intent = Intent(
            name="scenario_intent",
            intent_type=IntentType.SCENARIO,
            goal="Scenario goal"
        )
        result = compiler.compile(intent)
        assert result is not None

    def test_compile_meta_intent(self):
        """测试编译元意图"""
        compiler = IntentCompiler()
        intent = Intent(
            name="meta_intent",
            intent_type=IntentType.META,
            goal="Meta goal"
        )
        result = compiler.compile(intent)
        assert result is not None

    def test_compile_with_context(self):
        """测试带上下文编译"""
        from intentos.core import Context
        compiler = IntentCompiler()
        intent = Intent(
            name="test",
            intent_type=IntentType.ATOMIC,
            goal="Goal"
        )
        context = Context(user_id="user_123")
        result = compiler.compile(intent, context)
        assert result is not None

    def test_register_custom_template(self):
        """测试注册自定义模板"""
        compiler = IntentCompiler()
        compiler.register_template("custom", "Custom template: {intent_name}")
        assert "custom" in compiler._prompt_templates

    def test_get_template_existing(self):
        """测试获取存在的模板"""
        compiler = IntentCompiler()
        template = compiler.get_template("atomic")
        assert template is not None
        assert "原子任务" in template or "atomic" in template.lower()

    def test_get_template_nonexistent(self):
        """测试获取不存在的模板"""
        compiler = IntentCompiler()
        template = compiler.get_template("nonexistent")
        assert template is None

    def test_compile_with_params(self):
        """测试带参数编译"""
        compiler = IntentCompiler()
        intent = Intent(
            name="test",
            intent_type=IntentType.ATOMIC,
            goal="Goal",
            params={"key": "value"}
        )
        result = compiler.compile(intent)
        assert result is not None

    def test_compile_with_constraints(self):
        """测试带约束编译"""
        compiler = IntentCompiler()
        intent = Intent(
            name="test",
            intent_type=IntentType.ATOMIC,
            goal="Goal",
            constraints=["constraint1", "constraint2"]
        )
        result = compiler.compile(intent)
        assert result is not None


class TestIntentCompilerIntegration:
    """IntentCompiler 集成测试"""

    def test_full_compile_workflow(self):
        """测试完整编译工作流"""
        from intentos.core import Context
        
        compiler = IntentCompiler()
        
        intent = Intent(
            name="workflow_test",
            intent_type=IntentType.ATOMIC,
            goal="Workflow goal",
            description="Workflow description",
            params={"param1": "value1"}
        )
        
        context = Context(user_id="user_123", user_role="admin")
        
        result = compiler.compile(intent, context)
        
        assert result is not None
        assert isinstance(result, CompiledPrompt)
        assert result.system_prompt is not None
        assert result.user_prompt is not None

    def test_compile_all_intent_types(self):
        """测试编译所有意图类型"""
        compiler = IntentCompiler()
        
        for intent_type in [IntentType.ATOMIC, IntentType.COMPOSITE, IntentType.SCENARIO, IntentType.META]:
            intent = Intent(name=f"test_{intent_type.value}", intent_type=intent_type, goal="Goal")
            result = compiler.compile(intent)
            assert result is not None

    def test_template_customization(self):
        """测试模板自定义"""
        compiler = IntentCompiler()
        
        # 注册自定义模板
        compiler.register_template("custom", "Custom: {intent_name} - {goal}")
        
        intent = Intent(name="custom_test", intent_type=IntentType.ATOMIC, goal="Custom goal")
        result = compiler.compile(intent)
        
        assert result is not None

    def test_multiple_compilations(self):
        """测试多次编译"""
        compiler = IntentCompiler()
        
        intents = [
            Intent(name=f"intent_{i}", intent_type=IntentType.ATOMIC, goal=f"Goal {i}")
            for i in range(5)
        ]
        
        results = [compiler.compile(intent) for intent in intents]
        
        assert len(results) == 5
        assert all(r is not None for r in results)
