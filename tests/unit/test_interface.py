"""
Interface 模块测试

测试 IntentOS Interface
"""

import pytest

from intentos.interface.interface import ConversationTurn, IntentInterface


class TestIntentInterface:
    """IntentInterface 测试"""

    @pytest.fixture
    def interface(self):
        return IntentInterface()

    def test_interface_creation(self, interface):
        """测试接口创建"""
        assert interface is not None
        assert interface.parser is not None
        assert interface.engine is not None
        assert interface.context is not None

    def test_interface_with_registry(self):
        """测试带注册表的接口"""
        from intentos.registry import IntentRegistry

        registry = IntentRegistry()
        interface = IntentInterface(registry=registry)
        assert interface.registry == registry

    def test_set_user(self, interface):
        """测试设置用户"""
        interface.set_user("test_user", role="admin", permissions=["read", "write"])
        assert interface.context.user_id == "test_user"
        assert interface.context.user_role == "admin"

    @pytest.mark.asyncio
    async def test_chat_basic(self, interface):
        """测试基本聊天"""
        response = await interface.chat("Hello")
        assert response is not None
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_chat_multiple_turns(self, interface):
        """测试多轮对话"""
        response1 = await interface.chat("First message")
        response2 = await interface.chat("Second message")
        assert response1 is not None
        assert response2 is not None

    def test_get_history(self, interface):
        """测试获取历史"""
        history = interface.get_history()
        assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_chat_updates_history(self, interface):
        """测试聊天更新历史"""
        initial_len = len(interface.get_history())
        await interface.chat("Test message")
        new_len = len(interface.get_history())
        assert new_len == initial_len + 2  # 用户消息 + 系统响应

    def test_generate_response_success(self, interface):
        """测试生成成功响应"""
        from intentos.core import Intent

        intent = Intent(name="test", intent_type="atomic")
        result = type("Result", (), {"success": True, "result": "test result", "error": None})()
        response = interface._generate_response(intent, result)
        assert "✅" in response
        assert "test result" in response

    def test_generate_response_failure(self, interface):
        """测试生成失败响应"""
        from intentos.core import Intent

        intent = Intent(name="test", intent_type="atomic")
        result = type("Result", (), {"success": False, "result": None, "error": "Test error"})()
        response = interface._generate_response(intent, result)
        assert "❌" in response
        assert "Test error" in response


class TestConversationTurn:
    """ConversationTurn 测试"""

    def test_turn_creation(self):
        """测试轮次创建"""
        turn = ConversationTurn(role="user", content="Hello")
        assert turn.role == "user"
        assert turn.content == "Hello"

    def test_turn_with_intent(self):
        """测试带意图的轮次"""
        from intentos.core import Intent

        intent = Intent(name="test", intent_type="atomic")
        turn = ConversationTurn(role="system", content="Response", intent=intent)
        assert turn.intent == intent

    def test_turn_with_artifacts(self):
        """测试带工件的轮次"""
        turn = ConversationTurn(
            role="system", content="Response", artifacts=[{"type": "file", "name": "test.txt"}]
        )
        assert len(turn.artifacts) == 1


class TestIntentInterfaceIntegration:
    """IntentInterface 集成测试"""

    @pytest.mark.asyncio
    async def test_full_conversation(self):
        """测试完整对话"""
        interface = IntentInterface()
        interface.set_user("integration_user")

        response = await interface.chat("Test conversation")
        history = interface.get_history()

        assert len(history) >= 2
        assert response is not None

    @pytest.mark.asyncio
    async def test_conversation_with_context(self):
        """测试带上下文的对话"""
        interface = IntentInterface()

        # 第一轮
        await interface.chat("First")

        # 第二轮（应该有上下文）
        response = await interface.chat("Second")
        assert response is not None
        assert len(interface.context.history) >= 1
