"""
Runtime Agent Module Tests

测试运行时 Agent 的节点功能、API 路由和分布式执行
"""

import pytest
from aiohttp import web

from intentos.runtime.agent import RuntimeAgent


class TestRuntimeAgentInitialization:
    """测试 RuntimeAgent 初始化"""

    def test_init_default(self):
        """默认初始化"""
        agent = RuntimeAgent()

        assert agent.node_id.startswith("node_")
        assert agent.host == "0.0.0.0"
        assert agent.port == 8000
        assert agent.is_seed is False
        assert agent.os is not None

    def test_init_custom_params(self):
        """自定义参数初始化"""
        agent = RuntimeAgent(
            node_id="custom_node",
            host="127.0.0.1",
            port=9000,
            is_seed=True
        )

        assert agent.node_id == "custom_node"
        assert agent.host == "127.0.0.1"
        assert agent.port == 9000
        assert agent.is_seed is True

    def test_init_setup_web_app(self):
        """初始化应设置 Web 应用"""
        agent = RuntimeAgent()

        assert isinstance(agent.app, web.Application)
        # 检查路由是否已设置
        routes = [route.method for route in agent.app.router.routes()]
        assert len(routes) > 0

    def test_node_id_uniqueness(self):
        """节点 ID 应唯一"""
        agent1 = RuntimeAgent()
        agent2 = RuntimeAgent()

        assert agent1.node_id != agent2.node_id


class TestRuntimeAgentRoutes:
    """测试路由设置"""

    def test_routes_exist(self):
        """路由应存在"""
        agent = RuntimeAgent()

        routes = [str(r.resource) for r in agent.app.router.routes()]
        
        # 应包含 RPC 路由
        assert any("rpc" in r for r in routes)
        # 应包含 v1 API 路由
        assert any("v1" in r for r in routes)
        # 应包含 Chat 路由
        assert any("chat" in r for r in routes)

    def test_rpc_routes(self):
        """RPC 路由"""
        agent = RuntimeAgent()

        routes = [str(r.resource) for r in agent.app.router.routes()]
        
        assert any("execute" in r for r in routes)
        assert any("memory" in r for r in routes)
        assert any("status" in r for r in routes)

    def test_v1_routes(self):
        """v1 API 路由"""
        agent = RuntimeAgent()

        routes = [str(r.resource) for r in agent.app.router.routes()]
        
        assert any("/v1/execute" in r for r in routes)
        assert any("/v1/status" in r for r in routes)
        assert any("/v1/registry" in r for r in routes)


class TestRuntimeAgentProperties:
    """测试 Agent 属性"""

    def test_host_port(self):
        """主机和端口"""
        agent = RuntimeAgent(host="localhost", port=8080)
        
        assert agent.host == "localhost"
        assert agent.port == 8080

    def test_is_seed(self):
        """种子节点"""
        agent = RuntimeAgent(is_seed=True)
        assert agent.is_seed is True

    def test_os_instance(self):
        """OS 实例"""
        agent = RuntimeAgent()
        assert agent.os is not None

    def test_web_app(self):
        """Web 应用"""
        agent = RuntimeAgent()
        assert agent.app is not None
        assert isinstance(agent.app, web.Application)
