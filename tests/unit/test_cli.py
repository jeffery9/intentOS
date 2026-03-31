"""
CLI 工具测试 - 重构版本

测试新的统一 CLI 界面
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestCLICommands:
    """CLI 命令测试"""

    @pytest.mark.asyncio
    async def test_rpc_client_connection_error(self):
        """测试 RPC 客户端连接错误"""
        from intentos.cli.cli import RPCClient

        client = RPCClient()

        # 内核未运行时应该抛出连接错误
        with pytest.raises(ConnectionError):
            await client.connect()

    def test_cli_initialization(self):
        """测试 CLI 初始化"""
        import asyncio

        from intentos.cli.cli import IntentOSCLI, RPCClient

        # 创建 mock 客户端
        mock_client = MagicMock(spec=RPCClient)
        mock_client.get_status = AsyncMock(return_value={"running": True, "initialized": True})
        mock_client.get_kernel_status = AsyncMock(
            return_value={
                "registry": {"capabilities": [], "templates": []},
                "cluster": {"nodes": []},
            }
        )
        mock_client.ping = AsyncMock(return_value={"pong": True})
        mock_client.disconnect = AsyncMock()

        # 创建 CLI
        loop = asyncio.new_event_loop()
        cli = IntentOSCLI(mock_client, loop)

        # 验证 CLI 有正确的 prompt
        assert cli.prompt == "intentos> "

        # 验证 CLI 有 intro
        assert "IntentOS CLI" in cli.intro

        loop.close()

    def test_cli_ping_command(self):
        """测试 /ping 命令"""
        import asyncio

        from intentos.cli.cli import IntentOSCLI, RPCClient

        mock_client = MagicMock(spec=RPCClient)
        mock_client.ping = AsyncMock(return_value={"pong": True})

        loop = asyncio.new_event_loop()
        cli = IntentOSCLI(mock_client, loop)

        # 测试 /ping 命令
        cli.do_ping("")
        mock_client.ping.assert_called_once()

        loop.close()

    def test_cli_quit_command(self):
        """测试 /quit 命令"""
        import asyncio

        from intentos.cli.cli import IntentOSCLI, RPCClient

        mock_client = MagicMock(spec=RPCClient)
        mock_client.disconnect = AsyncMock()

        loop = asyncio.new_event_loop()
        cli = IntentOSCLI(mock_client, loop)

        # 测试 /quit 命令
        result = cli.do_quit("")
        assert result is True

        loop.close()


class TestSocketPath:
    """Socket 路径测试"""

    def test_get_socket_path_default(self):
        """测试默认 socket 路径"""
        from intentos.cli.cli import get_socket_path

        # 应该返回 /tmp/intentos.sock 或存在的路径
        path = get_socket_path()
        assert isinstance(path, str)
        assert path.endswith(".sock")

    def test_check_kernel_running(self):
        """测试内核运行检查"""
        from intentos.cli.cli import check_kernel_running

        # 返回布尔值
        result = check_kernel_running()
        assert isinstance(result, bool)

    def test_wait_for_kernel_timeout(self):
        """测试等待内核超时"""
        from intentos.cli.cli import wait_for_kernel

        # 应该超时返回 False
        result = wait_for_kernel(timeout=0.1)
        assert result is False
