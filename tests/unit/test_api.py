# -*- coding: utf-8 -*-
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import web
from intentos.interface.api import IntentOSGateway

@pytest.fixture
def mock_os():
    with patch("intentos.interface.api.IntentOS") as mock:
        os_instance = mock.return_value
        os_instance.initialize = MagicMock()
        os_instance.execute = AsyncMock(return_value="Success")
        os_instance.get_kernel_status = AsyncMock(return_value={
            "cluster": {"nodes": []},
            "memory": {"programs_count": 0, "variables_count": 0},
            "registry": {"templates": [], "capabilities": []}
        })
        
        # Mock VM and Memory
        os_instance.vm = MagicMock()
        os_instance.vm.memory = MagicMock()
        os_instance.vm.memory.get = AsyncMock(return_value="some_value")
        os_instance.vm.memory.set = AsyncMock()
        os_instance.vm.memory.get_nodes = MagicMock(return_value=[])
        
        # Mock add_node
        node_mock = MagicMock()
        node_mock.to_dict.return_value = {"host": "localhost", "port": 9000}
        os_instance.vm.add_node = AsyncMock(return_value=node_mock)
        
        # Mock Registry
        os_instance.registry = MagicMock()
        os_instance.registry.introspect = MagicMock(return_value={"templates": [], "capabilities": []})
        
        # Mock Bootstrap
        os_instance.bootstrap = MagicMock()
        os_instance.bootstrap.get_bootstrap_history = MagicMock(return_value=[])
        
        yield os_instance

@pytest.fixture
def gateway(mock_os):
    return IntentOSGateway()

class TestIntentOSGateway:
    """IntentOS REST API Gateway 测试"""

    @pytest.mark.asyncio
    async def test_handle_execute_success(self, gateway, mock_os):
        """测试执行成功"""
        mock_request = MagicMock(spec=web.Request)
        mock_request.json = AsyncMock(return_value={"intent": "test intent"})
        
        response = await gateway.handle_execute(mock_request)
        assert response.status == 200
        data = json.loads(response.text)
        assert data["status"] == "success"
        assert data["data"]["result"] == "Success"
        mock_os.execute.assert_called_once_with("test intent")

    @pytest.mark.asyncio
    async def test_handle_execute_missing_intent(self, gateway):
        """测试缺少意图字段"""
        mock_request = MagicMock(spec=web.Request)
        mock_request.json = AsyncMock(return_value={})
        
        response = await gateway.handle_execute(mock_request)
        assert response.status == 400
        data = json.loads(response.text)
        assert data["status"] == "error"
        assert "Missing 'intent' field" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_execute_exception(self, gateway, mock_os):
        """测试执行异常"""
        mock_request = MagicMock(spec=web.Request)
        mock_request.json = AsyncMock(return_value={"intent": "fail"})
        mock_os.execute.side_effect = Exception("Internal error")
        
        response = await gateway.handle_execute(mock_request)
        assert response.status == 500
        data = json.loads(response.text)
        assert data["status"] == "error"
        assert "Internal error" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_status(self, gateway, mock_os):
        """测试获取状态"""
        mock_request = MagicMock(spec=web.Request)
        
        response = await gateway.handle_status(mock_request)
        assert response.status == 200
        data = json.loads(response.text)
        assert data["status"] == "success"
        assert "kernel_version" in data["data"]
        mock_os.get_kernel_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_get_memory(self, gateway, mock_os):
        """测试读取内存"""
        mock_request = MagicMock(spec=web.Request)
        mock_request.match_info = {"store": "KVP", "key": "test_key"}
        
        response = await gateway.handle_get_memory(mock_request)
        assert response.status == 200
        data = json.loads(response.text)
        assert data["data"]["value"] == "some_value"
        mock_os.vm.memory.get.assert_called_with("KVP", "test_key")

    @pytest.mark.asyncio
    async def test_handle_set_memory_success(self, gateway, mock_os):
        """测试写入内存成功"""
        mock_request = MagicMock(spec=web.Request)
        mock_request.json = AsyncMock(return_value={"store": "KVP", "key": "k", "value": "v"})
        
        response = await gateway.handle_set_memory(mock_request)
        assert response.status == 200
        data = json.loads(response.text)
        assert data["data"]["message"] == "Memory updated"
        mock_os.vm.memory.set.assert_called_with("KVP", "k", "v")

    @pytest.mark.asyncio
    async def test_handle_set_memory_missing_fields(self, gateway):
        """测试写入内存缺少字段"""
        mock_request = MagicMock(spec=web.Request)
        mock_request.json = AsyncMock(return_value={"store": "KVP"})
        
        response = await gateway.handle_set_memory(mock_request)
        assert response.status == 400
        data = json.loads(response.text)
        assert "Missing required fields" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_registry(self, gateway, mock_os):
        """测试获取注册表"""
        mock_request = MagicMock(spec=web.Request)
        
        response = await gateway.handle_registry(mock_request)
        assert response.status == 200
        data = json.loads(response.text)
        assert data["status"] == "success"
        mock_os.registry.introspect.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_list_nodes(self, gateway, mock_os):
        """测试列出节点"""
        mock_request = MagicMock(spec=web.Request)
        node_mock = MagicMock()
        node_mock.to_dict.return_value = {"node_id": "123"}
        mock_os.vm.memory.get_nodes.return_value = [node_mock]
        
        response = await gateway.handle_list_nodes(mock_request)
        assert response.status == 200
        data = json.loads(response.text)
        assert len(data["data"]) == 1
        assert data["data"][0]["node_id"] == "123"

    @pytest.mark.asyncio
    async def test_handle_add_node_success(self, gateway, mock_os):
        """测试添加节点成功"""
        mock_request = MagicMock(spec=web.Request)
        mock_request.json = AsyncMock(return_value={"host": "1.2.3.4", "port": "8000"})
        
        response = await gateway.handle_add_node(mock_request)
        assert response.status == 200
        data = json.loads(response.text)
        assert data["data"]["host"] == "localhost" # from mock
        mock_os.vm.add_node.assert_called_with("1.2.3.4", 8000)

    @pytest.mark.asyncio
    async def test_handle_add_node_missing_fields(self, gateway):
        """测试添加节点缺少字段"""
        mock_request = MagicMock(spec=web.Request)
        mock_request.json = AsyncMock(return_value={"host": "1.2.3.4"})
        
        response = await gateway.handle_add_node(mock_request)
        assert response.status == 400
        data = json.loads(response.text)
        assert "Missing host/port" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_audit(self, gateway, mock_os):
        """测试审计历史"""
        mock_request = MagicMock(spec=web.Request)
        audit_mock = MagicMock()
        audit_mock.to_dict.return_value = {"id": "audit1"}
        mock_os.bootstrap.get_bootstrap_history.return_value = [audit_mock]
        
        response = await gateway.handle_audit(mock_request)
        assert response.status == 200
        data = json.loads(response.text)
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "audit1"
        mock_os.bootstrap.get_bootstrap_history.assert_called_with(limit=50)
