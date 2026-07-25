"""
测试 intentos.memory.shadow_agent - 影子代理
"""

import pytest


class TestShadowAgent:
    """影子代理测试"""

    def test_create_shadow_agent(self):
        from intentos.memory.shadow_agent import ShadowAgent
        agent = ShadowAgent()
        assert agent is not None
