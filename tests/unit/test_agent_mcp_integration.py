"""
测试 intentos.agent.mcp_integration - MCP 集成

覆盖:
- MCPIntegration 初始化
- get_connected_servers
- setup_metered_api_gateway
"""

import pytest
from unittest.mock import MagicMock


class TestMCPIntegration:
    """MCP 集成测试"""

    def test_initialization(self):
        from intentos.agent.mcp_integration import MCPIntegration
        mock_registry = MagicMock()
        mcp = MCPIntegration(registry=mock_registry)
        assert mcp.servers == {}

    def test_get_connected_servers_empty(self):
        from intentos.agent.mcp_integration import MCPIntegration
        mock_registry = MagicMock()
        mcp = MCPIntegration(registry=mock_registry)
        servers = mcp.get_connected_servers()
        assert servers == []

    def test_metered_api_gateway_simulation(self):
        from intentos.agent.mcp_integration import MCPIntegration
        mock_registry = MagicMock()
        mock_registry.list_capabilities.return_value = {"cap1": None, "cap2": None}
        mcp = MCPIntegration(registry=mock_registry)
        result = mcp.setup_metered_api_gateway()
        assert isinstance(result, dict)
        assert "endpoint" in result
        assert "status" in result
