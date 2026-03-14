"""
Engine 模块测试
"""

import pytest
from intentos.engine.engine import ExecutionEngine
from intentos.registry import IntentRegistry


class TestExecutionEngine:
    """ExecutionEngine 测试"""

    @pytest.fixture
    def engine(self):
        registry = IntentRegistry()
        return ExecutionEngine(registry)

    def test_engine_creation(self, engine):
        """测试引擎创建"""
        assert engine is not None
        assert engine.registry is not None

    def test_engine_with_registry(self):
        """测试带注册表的引擎"""
        registry = IntentRegistry()
        engine = ExecutionEngine(registry=registry)
        assert engine.registry == registry

    @pytest.mark.asyncio
    async def test_execute_basic(self, engine):
        """测试基本执行"""
        from intentos.core import Intent
        intent = Intent(name="test", intent_type="atomic", goal="Test goal")
        result = await engine.execute(intent)
        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_with_context(self, engine):
        """测试带上下文执行"""
        from intentos.core import Intent, Context
        intent = Intent(name="test", intent_type="atomic", goal="Test goal")
        context = Context(user_id="test_user")
        result = await engine.execute(intent, context)
        assert result is not None

    def test_get_status(self, engine):
        """测试获取状态"""
        status = engine.get_status()
        assert status is not None
        assert isinstance(status, dict)

    def test_get_capabilities(self, engine):
        """测试获取能力"""
        capabilities = engine.get_capabilities()
        assert capabilities is not None
        assert isinstance(capabilities, list)


class TestExecutionEngineIntegration:
    """ExecutionEngine 集成测试"""

    @pytest.mark.asyncio
    async def test_full_execution_workflow(self):
        """测试完整执行工作流"""
        registry = IntentRegistry()
        engine = ExecutionEngine(registry=registry)
        
        from intentos.core import Intent
        intent = Intent(name="workflow_test", intent_type="atomic", goal="Workflow goal")
        result = await engine.execute(intent)
        
        assert result is not None
        assert hasattr(result, 'success')

    @pytest.mark.asyncio
    async def test_multiple_executions(self):
        """测试多次执行"""
        registry = IntentRegistry()
        engine = ExecutionEngine(registry=registry)
        
        from intentos.core import Intent
        intents = [
            Intent(name=f"test_{i}", intent_type="atomic", goal=f"Goal {i}")
            for i in range(3)
        ]
        
        results = []
        for intent in intents:
            result = await engine.execute(intent)
            results.append(result)
        
        assert len(results) == 3
        assert all(r is not None for r in results)
