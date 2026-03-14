"""
LLM Mock Backend 测试

覆盖 MockBackend 的所有方法
"""

import pytest

from intentos.llm.backends.base import LLMUsage, Message, ToolDefinition
from intentos.llm.backends.mock_backend import MockBackend


class TestMockBackend:
    """MockBackend 测试"""

    def test_mock_backend_creation(self):
        """测试 MockBackend 创建"""
        backend = MockBackend()

        assert backend.model == "mock-model"
        assert backend.response_callback is None
        assert backend._call_count == 0

    def test_mock_backend_custom_model(self):
        """测试自定义模型名称"""
        backend = MockBackend(model="custom-mock")

        assert backend.model == "custom-mock"

    def test_mock_backend_with_callback(self):
        """测试带回调的 MockBackend"""

        def callback(messages, tools):
            return "Custom response"

        backend = MockBackend(response_callback=callback)

        assert backend.response_callback == callback

    @pytest.mark.asyncio
    async def test_mock_generate_basic(self):
        """测试基本生成"""
        backend = MockBackend()

        messages = [Message.user("Hello")]
        response = await backend.generate(messages)

        assert response.content is not None
        assert response.model == "mock-model"
        assert response.usage is not None

    @pytest.mark.asyncio
    async def test_mock_generate_with_sales_message(self):
        """测试销售相关消息生成"""
        backend = MockBackend()

        messages = [Message.user("分析销售数据")]
        response = await backend.generate(messages)

        assert response.content is not None
        assert "销售" in response.content or "分析" in response.content

    @pytest.mark.asyncio
    async def test_mock_generate_with_report_message(self):
        """测试报告相关消息生成"""
        backend = MockBackend()

        messages = [Message.user("生成报告")]
        response = await backend.generate(messages)

        assert response.content is not None
        assert "报告" in response.content or "分析" in response.content

    @pytest.mark.asyncio
    async def test_mock_generate_with_tools(self):
        """测试带工具生成"""
        backend = MockBackend()

        tool = ToolDefinition(name="search", description="Search tool", parameters={})

        messages = [Message.user("Search for something")]
        response = await backend.generate(messages, tools=[tool])

        assert response.content is not None
        assert "search" in response.content.lower() or "工具" in response.content

    @pytest.mark.asyncio
    async def test_mock_generate_increments_call_count(self):
        """测试生成增加调用计数"""
        backend = MockBackend()

        assert backend._call_count == 0

        await backend.generate([Message.user("Test")])

        assert backend._call_count == 1

    @pytest.mark.asyncio
    async def test_mock_generate_with_multiple_messages(self):
        """测试带多条消息生成"""
        backend = MockBackend()

        messages = [
            Message.system("You are helpful"),
            Message.user("Hello"),
            Message.assistant("Hi there"),
            Message.user("How are you?"),
        ]

        response = await backend.generate(messages)

        assert response.content is not None

    @pytest.mark.asyncio
    async def test_mock_generate_stream(self):
        """测试流式生成"""
        backend = MockBackend()

        messages = [Message.user("Hello")]

        chunks = []
        async for chunk in backend.generate_stream(messages):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert "".join(chunks).strip() != ""

    @pytest.mark.asyncio
    async def test_mock_generate_stream_with_multiple_words(self):
        """测试流式生成多词响应"""
        backend = MockBackend()

        messages = [Message.user("生成一个长一点的报告")]

        chunks = []
        async for chunk in backend.generate_stream(messages):
            chunks.append(chunk)

        # 流式输出应该有多个 chunk
        assert len(chunks) > 1

    def test_mock_validate_connection(self):
        """测试连接验证"""
        backend = MockBackend()

        result = backend.validate_connection()

        assert result is True

    def test_mock_call_count_property(self):
        """测试调用计数属性"""
        backend = MockBackend()

        assert backend.call_count == 0

    def test_mock_provider_name(self):
        """测试提供商名称"""
        backend = MockBackend()

        assert backend.provider_name == "Mock"

    def test_mock_estimate_usage(self):
        """测试使用量估算"""
        backend = MockBackend()

        messages = [Message.user("Hello world")]
        content = "This is a response"

        usage = backend._estimate_usage(messages, content)

        assert isinstance(usage, LLMUsage)
        assert usage.prompt_tokens > 0
        assert usage.completion_tokens > 0
        assert usage.total_tokens == usage.prompt_tokens + usage.completion_tokens

    def test_mock_parse_tool_calls_no_tools(self):
        """测试无工具时解析"""
        backend = MockBackend()

        result = backend._parse_tool_calls("Some content", None)

        assert result == []

    def test_mock_parse_tool_calls_with_tools(self):
        """测试带工具解析"""
        backend = MockBackend()

        tool = ToolDefinition(name="calculator", description="Calculator tool", parameters={})

        # 内容中提到工具名称
        result = backend._parse_tool_calls("I will use the calculator", [tool])

        assert len(result) == 1
        assert result[0].name == "calculator"

    def test_mock_parse_tool_calls_without_tool_name(self):
        """测试内容中无工具名称"""
        backend = MockBackend()

        tool = ToolDefinition(name="search", description="Search tool", parameters={})

        result = backend._parse_tool_calls("Some random content", [tool])

        assert result == []

    def test_mock_generate_mock_response_sales(self):
        """测试生成销售相关响应"""
        backend = MockBackend()

        response = backend._generate_mock_response("分析销售数据", None)

        assert response is not None
        assert "销售" in response or "分析" in response

    def test_mock_generate_mock_response_report(self):
        """测试生成报告相关响应"""
        backend = MockBackend()

        response = backend._generate_mock_response("生成报告", None)

        assert response is not None
        assert "报告" in response

    def test_mock_generate_mock_response_default(self):
        """测试生成默认响应"""
        backend = MockBackend()

        response = backend._generate_mock_response("Hello world", None)

        assert response is not None
        assert "收到消息" in response or "Hello" in response

    @pytest.mark.asyncio
    async def test_mock_generate_with_temperature(self):
        """测试带温度参数生成"""
        backend = MockBackend()

        messages = [Message.user("Test")]
        response = await backend.generate(messages, temperature=0.9)

        assert response.content is not None

    @pytest.mark.asyncio
    async def test_mock_generate_with_max_tokens(self):
        """测试带最大 token 数生成"""
        backend = MockBackend()

        messages = [Message.user("Test")]
        response = await backend.generate(messages, max_tokens=100)

        assert response.content is not None

    @pytest.mark.asyncio
    async def test_mock_generate_with_stream_flag(self):
        """测试带流式标志生成"""
        backend = MockBackend()

        messages = [Message.user("Test")]
        response = await backend.generate(messages, stream=True)

        assert response.content is not None

    @pytest.mark.asyncio
    async def test_mock_generate_response_has_latency(self):
        """测试响应包含延迟"""
        backend = MockBackend()

        messages = [Message.user("Test")]
        response = await backend.generate(messages)

        assert response.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_mock_generate_response_has_finish_reason(self):
        """测试响应包含完成原因"""
        backend = MockBackend()

        messages = [Message.user("Test")]
        response = await backend.generate(messages)

        assert response.finish_reason is not None

    @pytest.mark.asyncio
    async def test_mock_generate_with_callback_response(self):
        """测试带回调响应"""

        def custom_callback(messages, tools):
            return "Callback response"

        backend = MockBackend(response_callback=custom_callback)

        messages = [Message.user("Test")]
        response = await backend.generate(messages)

        assert response.content == "Callback response"


# =============================================================================
# Integration Tests
# =============================================================================


class TestMockBackendIntegration:
    """MockBackend 集成测试"""

    @pytest.mark.asyncio
    async def test_full_generation_workflow(self):
        """测试完整生成工作流"""
        backend = MockBackend()

        # 1. 验证连接
        assert backend.validate_connection() is True

        # 2. 生成响应
        messages = [
            Message.system("You are a helpful assistant"),
            Message.user("Hello, how are you?"),
        ]
        response = await backend.generate(messages)

        # 3. 验证响应
        assert response.content is not None
        assert response.usage is not None
        assert response.usage.total_tokens > 0

        # 4. 验证调用计数
        assert backend.call_count == 1

    @pytest.mark.asyncio
    async def test_multiple_generations(self):
        """测试多次生成"""
        backend = MockBackend()

        for i in range(5):
            await backend.generate([Message.user(f"Message {i}")])

        assert backend.call_count == 5

    @pytest.mark.asyncio
    async def test_stream_and_non_stream(self):
        """测试流式和非流式生成"""
        backend = MockBackend()

        # 非流式
        response = await backend.generate([Message.user("Test")])
        assert response.content is not None

        # 流式
        chunks = []
        async for chunk in backend.generate_stream([Message.user("Test")]):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert "".join(chunks).strip() != ""

    def test_usage_estimation_accuracy(self):
        """测试使用量估算准确性"""
        backend = MockBackend()

        short_msg = Message.user("Hi")
        long_msg = Message.user("This is a much longer message with more words")

        short_usage = backend._estimate_usage([short_msg], "Short response")
        long_usage = backend._estimate_usage(
            [long_msg], "This is a longer response with more content"
        )

        # 长消息应该使用更多 token
        assert long_usage.prompt_tokens > short_usage.prompt_tokens
        assert long_usage.completion_tokens > short_usage.completion_tokens
