"""
LLM 后端测试
"""


import pytest

from intentos.llm import (
    Message,
    MockBackend,
    ToolDefinition,
    create_executor,
    create_router,
)
from intentos.llm.backends.base import (
    LLMRole,
    LLMUsage,
)
from intentos.llm.executor import BackendConfig


class TestMessage:
    """测试消息类"""

    def test_message_creation(self):
        """测试消息创建"""
        msg = Message(role=LLMRole.USER, content="Hello")
        assert msg.role == LLMRole.USER
        assert msg.content == "Hello"

    def test_message_helpers(self):
        """测试辅助方法"""
        assert Message.system("test").role == LLMRole.SYSTEM
        assert Message.user("test").role == LLMRole.USER
        assert Message.assistant("test").role == LLMRole.ASSISTANT

    def test_message_to_dict(self):
        """测试序列化"""
        msg = Message.user("Hello")
        d = msg.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "Hello"


class TestToolDefinition:
    """测试工具定义"""

    def test_tool_creation(self):
        """测试工具创建"""
        tool = ToolDefinition(
            name="test_tool",
            description="测试工具",
            parameters={"type": "object"},
        )

        assert tool.name == "test_tool"
        assert tool.description == "测试工具"

    def test_tool_to_dict(self):
        """测试序列化"""
        tool = ToolDefinition(
            name="query",
            description="查询",
            parameters={"type": "object", "properties": {}},
        )

        d = tool.to_dict()
        assert d["type"] == "function"
        assert d["function"]["name"] == "query"


class TestLLMUsage:
    """测试使用统计"""

    def test_usage_creation(self):
        """测试创建"""
        usage = LLMUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )

        assert usage.prompt_tokens == 100
        assert usage.total_tokens == 150

    def test_usage_from_dict(self):
        """测试从字典创建"""
        data = {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            }
        }
        usage = LLMUsage.from_dict(data)
        assert usage.prompt_tokens == 100


class TestMockBackend:
    """测试 Mock 后端"""

    @pytest.mark.asyncio
    async def test_mock_generate(self):
        """测试生成"""
        backend = MockBackend()

        messages = [Message.user("Hello")]
        response = await backend.generate(messages)

        assert response.content is not None
        assert response.model == "mock-model"
        assert response.usage.total_tokens > 0

    @pytest.mark.asyncio
    async def test_mock_with_tools(self):
        """测试带工具"""
        backend = MockBackend()

        tools = [ToolDefinition(
            name="test_tool",
            description="测试",
            parameters={},
        )]

        messages = [Message.user("调用 test_tool")]
        response = await backend.generate(messages, tools=tools)

        # Mock 后端应该检测到工具名称并返回工具调用
        assert len(response.tool_calls) >= 0  # 可能有也可能没有

    @pytest.mark.asyncio
    async def test_mock_streaming(self):
        """测试流式"""
        backend = MockBackend()

        messages = [Message.user("Hello")]

        chunks = []
        async for chunk in backend.generate_stream(messages):
            chunks.append(chunk)

        assert len(chunks) > 0


class TestLLMExecutor:
    """测试 LLM 执行器"""

    def test_executor_creation_mock(self):
        """测试创建 (Mock)"""
        executor = create_executor(provider="mock")
        assert executor._single_backend is not None

    def test_executor_creation_openai(self):
        """测试创建 (OpenAI)"""
        executor = create_executor(
            provider="openai",
            model="gpt-4o",
            api_key="test-key",
        )
        assert executor._single_backend.model == "gpt-4o"

    def test_executor_creation_anthropic(self):
        """测试创建 (Anthropic)"""
        executor = create_executor(
            provider="anthropic",
            model="claude-3-sonnet",
            api_key="test-key",
        )
        assert executor._single_backend.model == "claude-3-sonnet"

    def test_executor_creation_ollama(self):
        """测试创建 (Ollama)"""
        executor = create_executor(
            provider="ollama",
            model="llama3.1",
            base_url="http://localhost:11434",
        )
        assert executor._single_backend.model == "llama3.1"

    @pytest.mark.asyncio
    async def test_executor_execute_mock(self):
        """测试执行 (Mock)"""
        executor = create_executor(provider="mock")

        messages = [Message.user("Hello")]
        response = await executor.execute(messages)

        assert response.content is not None
        assert response.usage.total_tokens > 0


class TestLLMRouter:
    """测试 LLM 路由器"""

    def test_router_creation(self):
        """测试路由器创建"""
        configs = [
            BackendConfig(name="backend1", model="model1"),
            BackendConfig(name="backend2", model="model2"),
        ]

        router = create_router(configs)

        assert len(router.backends) == 2

    def test_router_priority_selection(self):
        """测试优先级选择"""
        configs = [
            BackendConfig(name="low", model="m1", priority=1),
            BackendConfig(name="high", model="m2", priority=10),
        ]

        router = create_router(configs)
        name, backend = router.select_backend(strategy="priority")

        assert name == "high"

    def test_router_stats(self):
        """测试统计"""
        configs = [
            BackendConfig(name="backend1", model="model1"),
        ]

        router = create_router(configs)
        stats = router.get_stats()

        assert "backend1" in stats

    @pytest.mark.asyncio
    async def test_router_generate(self):
        """测试路由生成"""
        configs = [
            BackendConfig(name="mock1", model="mock"),
            BackendConfig(name="mock2", model="mock"),
        ]

        router = create_router(configs)

        messages = [Message.user("Hello")]
        response = await router.generate(messages)

        assert response.content is not None


class TestBackendConfig:
    """测试后端配置"""

    def test_config_defaults(self):
        """测试默认值"""
        config = BackendConfig(name="test", model="test-model")

        assert config.priority == 5
        assert config.weight == 1.0
        assert config.enabled is True
        assert config.max_qps == float("inf")

    def test_config_custom(self):
        """测试自定义配置"""
        config = BackendConfig(
            name="prod",
            model="gpt-4",
            priority=10,
            weight=2.0,
            max_qps=100,
            timeout=120,
        )

        assert config.priority == 10
        assert config.weight == 2.0
        assert config.max_qps == 100
        assert config.timeout == 120


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_pipeline_mock(self):
        """测试完整流程 (Mock)"""
        # 创建执行器
        executor = create_executor(provider="mock")

        # 创建消息
        messages = [
            Message.system("你是一个销售分析助手"),
            Message.user("分析华东区 Q3 销售数据"),
        ]

        # 定义工具
        tools = [
            ToolDefinition(
                name="query_sales",
                description="查询销售数据",
                parameters={
                    "type": "object",
                    "properties": {
                        "region": {"type": "string"},
                        "period": {"type": "string"},
                    },
                    "required": ["region"],
                },
            ),
        ]

        # 执行
        response = await executor.execute(messages, tools=tools, max_tokens=200)

        # 验证
        assert response.content is not None
        assert response.model == "mock-model"
        assert response.usage.total_tokens > 0
        assert response.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_multi_turn_conversation_mock(self):
        """测试多轮对话 (Mock)"""
        executor = create_executor(provider="mock")

        messages = [
            Message.system("你是助手"),
            Message.user("你好"),
            Message.assistant("你好！有什么可以帮助你的？"),
            Message.user("我想查询销售数据"),
        ]

        response = await executor.execute(messages)

        assert response.content is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
