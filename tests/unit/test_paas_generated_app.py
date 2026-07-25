"""
测试 intentos.paas.app_generator.GeneratedApp - 生成的 App 实例
"""

import pytest


class TestGeneratedApp:
    """生成的 App 实例测试"""

    def test_create_generated_app(self):
        from intentos.paas.app_generator import GeneratedApp
        app = GeneratedApp(
            id="app_instance_1",
            app_id="market_app_1",
            tenant_id="tenant_a",
            user_id="user_x",
            version="1.0.0",
            name="测试应用",
            description="这是一个测试应用",
            intents={},
            capabilities={},
            config={"gas_limit": 5000},
            resources={"memory": "512MB"},
          )
        assert app.id == "app_instance_1"
        assert app.status == "idle"

    def test_get_context(self):
        from intentos.paas.app_generator import GeneratedApp
        app = GeneratedApp(
            id="app_1",
            app_id="mkt_1",
            tenant_id="t1",
            user_id="u1",
            version="1.0",
            name="测试",
            description="测试",
            intents={},
            capabilities={},
            config={"gas_limit": 8000},
            resources={},
            metadata={"permissions": ["data:read"]},
          )
        ctx = app.get_context()
        assert ctx["tenant_id"] == "t1"
        assert ctx["user_id"] == "u1"
        assert ctx["gas_limit"] == 8000

    def test_to_dict(self):
        from intentos.paas.app_generator import GeneratedApp
        app = GeneratedApp(
            id="app_2",
            app_id="mkt_2",
            tenant_id="t2",
            user_id="u2",
            version="2.0",
            name="数据应用",
            description="数据应用",
            intents={},
            capabilities={},
            config={},
            resources={},
          )
        d = app.to_dict()
        assert d["id"] == "app_2"
        assert d["status"] == "idle"
