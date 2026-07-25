"""
测试 intentos.interface.chat_tui - 聊天 TUI
"""

import pytest


class TestChatMessage:
    """聊天消息测试"""

    def test_create_message(self):
        from intentos.interface.chat_tui import ChatMessage
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_ai_message(self):
        from intentos.interface.chat_tui import ChatMessage
        msg = ChatMessage(role="assistant", content="I can help!")
        assert msg.role == "assistant"
