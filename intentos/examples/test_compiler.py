"""
IntentOS 编译器测试
"""

import pytest
from intentos import (
    Intent,
    IntentType,
    Context,
    IntentCompiler,
    CompiledPrompt,
    LLMExecutor,
    IntentRegistry,
    Capability,
)


class TestIntentCompiler:
    """测试意图编译器"""
    
    def test_compiler_creation(self):
        """测试编译器创建"""
        registry = IntentRegistry()
        compiler = IntentCompiler(registry)
        assert compiler is not None
    
    def test_compile_atomic_intent(self):
        """测试编译原子意图"""
        registry = IntentRegistry()
        compiler = IntentCompiler(registry)
        
        intent = Intent(
            name="query_data",
            intent_type=IntentType.ATOMIC,
            goal="查询数据",
            context=Context(user_id="user_001"),
        )
        
        compiled = compiler.compile(intent)
        
        assert isinstance(compiled, CompiledPrompt)
        assert compiled.intent == intent
        assert compiled.metadata["template"] == "atomic"
    
    def test_compile_composite_intent(self):
        """测试编译复合意图"""
        registry = IntentRegistry()
        compiler = IntentCompiler(registry)
        
        intent = Intent(
            name="analysis_report",
            intent_type=IntentType.COMPOSITE,
            goal="分析并生成报告",
            context=Context(user_id="user_001"),
        )
        
        compiled = compiler.compile(intent)
        
        assert compiled.metadata["template"] == "composite"
    
    def test_compile_scenario_intent(self):
        """测试编译场景意图"""
        registry = IntentRegistry()
        compiler = IntentCompiler(registry)
        
        intent = Intent(
            name="monthly_review",
            intent_type=IntentType.SCENARIO,
            goal="月度复盘",
            context=Context(user_id="manager_001", user_role="manager"),
        )
        
        compiled = compiler.compile(intent)
        
        assert compiled.metadata["template"] == "scenario"
    
    def test_compile_meta_intent(self):
        """测试编译元意图"""
        registry = IntentRegistry()
        compiler = IntentCompiler(registry)
        
        intent = Intent(
            name="system_admin",
            intent_type=IntentType.META,
            goal="管理系统",
            context=Context(user_id="admin"),
            params={"action": "register_capability"},
        )
        
        compiled = compiler.compile(intent)
        
        assert compiled.metadata["template"] == "meta"
    
    def test_compile_to_json(self):
        """测试编译为 JSON"""
        import json
        
        registry = IntentRegistry()
        compiler = IntentCompiler(registry)
        
        intent = Intent(
            name="test",
            intent_type=IntentType.ATOMIC,
            goal="测试",
            context=Context(user_id="user_001"),
            params={"key": "value"},
        )
        
        json_str = compiler.compile_to_json(intent)
        data = json.loads(json_str)
        
        assert data["intent"]["name"] == "test"
        assert data["intent"]["goal"] == "测试"
        assert data["intent"]["params"]["key"] == "value"
    
    def test_compile_with_capabilities(self):
        """测试编译时包含能力列表"""
        registry = IntentRegistry()
        
        # 注册能力
        cap = Capability(
            name="test_cap",
            description="测试能力",
            input_schema={},
            output_schema={},
            func=lambda ctx: None,
        )
        registry.register_capability(cap)
        
        compiler = IntentCompiler(registry)
        intent = Intent(
            name="test",
            intent_type=IntentType.ATOMIC,
            goal="测试",
            context=Context(user_id="user_001"),
        )
        
        compiled = compiler.compile(intent)
        
        assert "test_cap" in compiled.system_prompt
    
    def test_compiled_prompt_messages(self):
        """测试消息格式转换"""
        registry = IntentRegistry()
        compiler = IntentCompiler(registry)
        
        intent = Intent(
            name="test",
            intent_type=IntentType.ATOMIC,
            goal="测试",
            context=Context(user_id="user_001"),
        )
        
        compiled = compiler.compile(intent)
        messages = compiled.messages
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"


class TestLLMExecutor:
    """测试 LLM 执行器"""
    
    @pytest.mark.asyncio
    async def test_mock_llm_execution(self):
        """测试模拟 LLM 执行"""
        from intentos.llm import create_executor, Message
        
        llm = create_executor(provider="mock")
        
        messages = [Message.user("test")]
        response = await llm.execute(messages)
        
        assert response.content is not None
    
    def test_llm_executor_creation(self):
        """测试 LLM 执行器创建"""
        from intentos.llm import create_executor
        
        llm = create_executor(provider="mock")
        assert llm._single_backend.provider_name == "Mock"
    
    def test_llm_with_config(self):
        """测试带配置的 LLM 执行器"""
        from intentos.llm import create_executor
        
        llm = create_executor(provider="mock", timeout=120)
        # MockBackend 不接收额外 kwargs，所以 timeout 是默认值 60
        assert llm._single_backend.timeout == 60


class TestPromptTemplate:
    """测试 Prompt 模板"""
    
    def test_template_creation(self):
        """测试模板创建"""
        from intentos import PromptTemplate
        
        template = PromptTemplate(
            name="test",
            template="Hello, {name}!",
            variables=["name"],
        )
        
        assert template.name == "test"
        assert "name" in template.variables
    
    def test_template_render(self):
        """测试模板渲染"""
        from intentos import PromptTemplate
        
        template = PromptTemplate(
            name="greeting",
            template="Hello, {name}!",
        )
        
        result = template.render(name="World")
        assert result == "Hello, World!"
    
    def test_template_add_variable(self):
        """测试添加变量"""
        from intentos import PromptTemplate
        
        template = PromptTemplate(
            name="test",
            template="Hello, {name}! Today is {day}.",
        )
        
        template.add_variable("day")
        assert "day" in template.variables


class TestLLMResponse:
    """测试 LLM 响应"""
    
    def test_llm_response_creation(self):
        """测试 LLM 响应创建"""
        from intentos.llm import LLMResponse, LLMUsage
        
        response = LLMResponse(
            content="Test response",
            model="test-model",
            usage=LLMUsage(total_tokens=100),
        )
        
        assert response.content == "Test response"
        assert response.tool_calls == []
    
    def test_llm_response_with_tool_calls(self):
        """测试带工具调用的响应"""
        from intentos.llm import LLMResponse, LLMUsage, ToolCall
        
        response = LLMResponse(
            content="Calling tool",
            model="test-model",
            usage=LLMUsage(total_tokens=100),
            tool_calls=[
                ToolCall(id="1", name="test_tool", arguments={"param": "value"}),
            ],
        )
        
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "test_tool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
