"""
API Gateway 测试 - 重构版本

测试新的 API Gateway（服务器模式）
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_os_instance():
    """创建模拟的 OS 实例"""
    os_instance = MagicMock()
    os_instance.execute = AsyncMock(return_value="执行成功")
    os_instance.get_kernel_status = AsyncMock(return_value={
        "cluster": {"nodes": []},
        "memory": {"programs_count": 0, "variables_count": 0},
        "registry": {"templates": [], "capabilities": []},
    })
    
    # Mock VM and Memory
    os_instance.vm = MagicMock()
    os_instance.vm.memory = MagicMock()
    os_instance.vm.memory.get = AsyncMock(return_value="test_value")
    os_instance.vm.memory.set = AsyncMock()
    os_instance.vm.memory.get_nodes = MagicMock(return_value=[])
    os_instance.vm.add_node = AsyncMock(return_value=MagicMock(
        to_dict=lambda: {"host": "localhost", "port": 9000}
    ))
    
    # Mock Registry
    os_instance.registry = MagicMock()
    os_instance.registry.introspect = MagicMock(
        return_value={"templates": [], "capabilities": []}
    )
    
    # Mock Bootstrap
    os_instance.bootstrap = MagicMock()
    os_instance.bootstrap.get_bootstrap_history = MagicMock(return_value=[])
    
    return os_instance


@pytest.fixture
def gateway(mock_os_instance):
    """创建 API Gateway 实例"""
    from intentos.interface.api import IntentOSGateway
    
    # 服务器模式：传入 os_instance
    return IntentOSGateway(os_instance=mock_os_instance)


class TestIntentOSGateway:
    """IntentOS REST API Gateway 测试"""

    @pytest.mark.asyncio
    async def test_handle_execute_success(self, gateway, mock_os_instance):
        """测试执行成功"""
        from aiohttp import web
        
        mock_request = MagicMock(spec=web.Request)
        mock_request.json = AsyncMock(return_value={"intent": "test intent"})
        
        response = await gateway.handle_execute(mock_request)
        assert response.status == 200

    @pytest.mark.asyncio
    async def test_handle_execute_missing_intent(self, gateway):
        """测试缺少 intent 参数"""
        from aiohttp import web
        
        mock_request = MagicMock(spec=web.Request)
        mock_request.json = AsyncMock(return_value={})
        
        response = await gateway.handle_execute(mock_request)
        assert response.status == 400

    @pytest.mark.asyncio
    async def test_handle_status(self, gateway):
        """测试状态查询"""
        from aiohttp import web
        
        mock_request = MagicMock(spec=web.Request)
        
        response = await gateway.handle_status(mock_request)
        assert response.status == 200

    @pytest.mark.asyncio
    async def test_handle_health(self, gateway):
        """测试健康检查"""
        from aiohttp import web
        
        mock_request = MagicMock(spec=web.Request)
        
        response = await gateway.handle_health(mock_request)
        assert response.status == 200

    @pytest.mark.asyncio
    async def test_handle_list_nodes(self, gateway):
        """测试节点列表"""
        from aiohttp import web
        
        mock_request = MagicMock(spec=web.Request)
        
        response = await gateway.handle_list_nodes(mock_request)
        assert response.status == 200


class TestIntentOSGatewayInit:
    """API Gateway 初始化测试"""

    def test_server_mode_initialization(self):
        """测试服务器模式初始化"""
        from intentos.interface.api import IntentOSGateway
        
        mock_os = MagicMock()
        gateway = IntentOSGateway(os_instance=mock_os, host="localhost", port=8080)
        
        assert gateway.os == mock_os
        assert gateway.host == "localhost"
        assert gateway.port == 8080
        assert gateway.app is not None

    def test_routes_registered(self):
        """测试路由已注册"""
        from intentos.interface.api import IntentOSGateway
        
        mock_os = MagicMock()
        gateway = IntentOSGateway(os_instance=mock_os)
        
        # 验证路由已注册
        routes = list(gateway.app.router.routes())
        assert len(routes) > 0
