"""
LLM Backends Base 模块测试
"""

from intentos.llm.backends.base import (
    LLMError,
    LLMResponse,
    LLMRole,
    LLMUsage,
    Message,
    ToolCall,
    ToolDefinition,
)


class TestLLMRole:
    """LLMRole 测试"""

    def test_role_values(self):
        assert LLMRole.SYSTEM.value == "system"
        assert LLMRole.USER.value == "user"
        assert LLMRole.ASSISTANT.value == "assistant"
        assert LLMRole.TOOL.value == "tool"


class TestMessage:
    """Message 测试"""

    def test_message_creation(self):
        msg = Message(role=LLMRole.USER, content="Hello")
        assert msg.role == LLMRole.USER
        assert msg.content == "Hello"

    def test_message_system_helper(self):
        msg = Message.system("System instruction")
        assert msg.role == LLMRole.SYSTEM

    def test_message_user_helper(self):
        msg = Message.user("User message")
        assert msg.role == LLMRole.USER

    def test_message_assistant_helper(self):
        msg = Message.assistant("Assistant response")
        assert msg.role == LLMRole.ASSISTANT

    def test_message_to_dict(self):
        msg = Message(role=LLMRole.USER, content="Test")
        data = msg.to_dict()
        assert data["role"] == "user"
        assert data["content"] == "Test"

    def test_message_to_dict_with_name(self):
        msg = Message(role=LLMRole.USER, content="Test", name="user1")
        data = msg.to_dict()
        assert data["name"] == "user1"


class TestToolDefinition:
    """ToolDefinition 测试"""

    def test_tool_creation(self):
        tool = ToolDefinition(
            name="search", description="Search the web", parameters={"type": "object"}
        )
        assert tool.name == "search"

    def test_tool_to_dict(self):
        tool = ToolDefinition(
            name="calculator", description="Calculate", parameters={"type": "object"}
        )
        data = tool.to_dict()
        assert data["type"] == "function"
        assert data["function"]["name"] == "calculator"


class TestToolCall:
    """ToolCall 测试"""

    def test_tool_call_creation(self):
        call = ToolCall(id="call_1", name="search", arguments={"query": "test"})
        assert call.id == "call_1"
        assert call.name == "search"

    def test_tool_call_from_dict_openai(self):
        data = {"id": "call_123", "function": {"name": "search", "arguments": '{"q": "test"}'}}
        call = ToolCall.from_dict(data)
        assert call.id == "call_123"
        assert call.name == "search"


class TestLLMUsage:
    """LLMUsage 测试"""

    def test_usage_creation(self):
        usage = LLMUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        assert usage.prompt_tokens == 100
        assert usage.total_tokens == 150


class TestLLMResponse:
    """LLMResponse 测试"""

    def test_response_creation(self):
        usage = LLMUsage(1, 1, 2)
        response = LLMResponse(content="Response text", model="test", usage=usage)
        assert response.content == "Response text"

    def test_response_with_usage(self):
        usage = LLMUsage(10, 20, 30)
        response = LLMResponse(content="Text", model="test", usage=usage)
        assert response.usage is not None


class TestLLMError:
    """LLMError 测试"""

    def test_error_creation(self):
        error = LLMError("Error message")
        assert "Error message" in str(error)


class TestLLMBackendsIntegration:
    """LLM Backends 集成测试"""

    def test_message_tool_call_workflow(self):
        call = ToolCall(id="call_1", name="search", arguments={"q": "test"})
        msg = Message.tool("Result", "search", "call_1")
        data = msg.to_dict()
        assert data["role"] == "tool"
        assert data["tool_call_id"] == "call_1"

    def test_tool_definition_and_call(self):
        tool = ToolDefinition(name="weather", description="Get weather", parameters={})
        call = ToolCall(id="call_1", name="weather", arguments={"city": "NYC"})
        assert tool.name == call.name
