# -*- coding: utf-8 -*-
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from intentos.interface.shell import IntentShell
import json

@pytest.fixture
def mock_os():
    with patch("intentos.interface.shell.IntentOS") as mock:
        os_instance = mock.return_value
        os_instance.initialize = MagicMock()
        os_instance.execute = AsyncMock(return_value="Success")
        os_instance.get_kernel_status = AsyncMock(return_value={
            "cluster": {"nodes": []},
            "memory": {"programs_count": 0, "variables_count": 0},
            "registry": {"templates": [], "capabilities": []},
            "processes": [],
            "bootstrap": []
        })
        os_instance.vm = MagicMock()
        os_instance.vm.kill = AsyncMock(return_value=True)
        os_instance.vm.memory = MagicMock()
        os_instance.vm.memory.get = AsyncMock(return_value="v")
        os_instance.vm.memory.set = AsyncMock()
        os_instance.vm.memory.delete = AsyncMock()
        os_instance.vm.add_node = AsyncMock(return_value=MagicMock(node_id="node1"))
        os_instance.vm.remove_node = AsyncMock()
        yield os_instance

@pytest.fixture
def shell(mock_os):
    # Mock rich Console to avoid terminal output and issues during tests
    with patch("intentos.interface.shell.Console"):
        # We need to mock _print_banner as it's called in __init__
        with patch.object(IntentShell, "_print_banner"):
            return IntentShell()

class TestIntentShell:
    """IntentOS Shell 测试"""

    def test_onecmd_system_command(self, shell):
        """测试系统指令分发 (以 / 开头)"""
        with patch.object(shell, "do_ps") as mock_ps:
            shell.onecmd("/ps")
            mock_ps.assert_called_once_with("")

    def test_onecmd_intent(self, shell, mock_os):
        """测试自然语言意图分发 (非 / 开头)"""
        with patch.object(shell, "_execute_intent", new_callable=AsyncMock) as mock_exec:
            # We mock asyncio.run for the purpose of this test to avoid loop issues
            with patch("asyncio.run", side_effect=lambda x: x if hasattr(x, '__await__') else None):
                shell.onecmd("Analyze sales")
                # Since we mocked onecmd to call _execute_intent directly in our mock_exec
                # we just need to ensure it was called. 
                # Actually IntentShell.onecmd calls asyncio.run(self._execute_intent(line))
                # So mock_exec will be called.
                pass
            # Re-testing without the complex asyncio.run mock if possible
    
    @pytest.mark.asyncio
    async def test_execute_intent(self, shell, mock_os):
        """测试执行意图内部逻辑"""
        # Mock Live and Panel
        with patch("intentos.interface.shell.Live"), patch("intentos.interface.shell.Panel"):
            await shell._execute_intent("hello")
            mock_os.execute.assert_called_with("hello")

    def test_do_ps(self, shell, mock_os):
        """测试 /ps 指令"""
        mock_os.get_kernel_status.return_value = {
            "processes": [
                {
                    "pid": "pid123456",
                    "program_name": "prog1",
                    "node_id": "node123",
                    "state": "RUNNING",
                    "pc": 0,
                    "start_time": "now"
                }
            ]
        }
        shell.do_ps("")
        mock_os.get_kernel_status.assert_called()

    def test_do_kill_success(self, shell, mock_os):
        """测试 /kill 指令成功"""
        shell.do_kill("pid123")
        mock_os.vm.kill.assert_called_with("pid123")

    def test_do_kill_failure(self, shell, mock_os):
        """测试 /kill 指令失败"""
        mock_os.vm.kill.return_value = False
        shell.do_kill("pid_none")
        mock_os.vm.kill.assert_called_with("pid_none")

    def test_do_top(self, shell, mock_os):
        """测试 /top 指令"""
        mock_os.get_kernel_status.return_value = {
            "cluster": {
                "nodes": [
                    {"node_id": "n1", "host": "h1", "port": 1, "status": "OK", "load": 0.5}
                ]
            }
        }
        shell.do_top("")
        mock_os.get_kernel_status.assert_called()

    def test_do_df(self, shell, mock_os):
        """测试 /df 指令"""
        mock_os.get_kernel_status.return_value = {
            "registry": {"templates": [], "capabilities": []},
            "memory": {"programs_count": 5, "variables_count": 10}
        }
        shell.do_df("")
        mock_os.get_kernel_status.assert_called()

    def test_do_mem_summary(self, shell, mock_os):
        """测试 /mem 概览"""
        shell.do_mem("")
        mock_os.get_kernel_status.assert_called()

    def test_do_mem_get(self, shell, mock_os):
        """测试 /mem get"""
        shell.do_mem("get KVP key1")
        mock_os.vm.memory.get.assert_called_with("KVP", "key1")

    def test_do_mem_set(self, shell, mock_os):
        """测试 /mem set"""
        shell.do_mem("set KVP key1 val1")
        mock_os.vm.memory.set.assert_called_with("KVP", "key1", "val1")

    def test_do_mem_delete(self, shell, mock_os):
        """测试 /mem delete"""
        shell.do_mem("delete KVP key1")
        mock_os.vm.memory.delete.assert_called_with("KVP", "key1")

    def test_do_nodes_add(self, shell, mock_os):
        """测试 /nodes add"""
        shell.do_nodes("add localhost 8000")
        mock_os.vm.add_node.assert_called_with("localhost", 8000)

    def test_do_nodes_remove(self, shell, mock_os):
        """测试 /nodes remove"""
        shell.do_nodes("remove node1")
        mock_os.vm.remove_node.assert_called_with("node1")

    def test_do_history(self, shell, mock_os):
        """测试 /history 指令"""
        mock_os.get_kernel_status.return_value = {
            "bootstrap": [
                {"id": "id1", "action": "act", "target": "t", "status": "ok", "timestamp": "t"}
            ]
        }
        shell.do_history("")
        mock_os.get_kernel_status.assert_called()

    def test_do_ls_templates(self, shell, mock_os):
        """测试 /ls 指令"""
        mock_os.get_kernel_status.return_value = {
            "registry": {
                "templates": [{"name": "t1", "description": "d1"}],
                "capabilities": []
            }
        }
        shell.do_ls("templates")
        mock_os.get_kernel_status.assert_called()

    def test_do_ls_capabilities(self, shell, mock_os):
        """测试 /ls capabilities 指令"""
        mock_os.get_kernel_status.return_value = {
            "registry": {
                "templates": [],
                "capabilities": [{"name": "c1", "description": "d1"}]
            }
        }
        shell.do_ls("capabilities")
        mock_os.get_kernel_status.assert_called()

    def test_do_cat_found(self, shell, mock_os):
        """测试 /cat 指令 (找到)"""
        mock_os.get_kernel_status.return_value = {
            "registry": {
                "templates": [{"name": "t1", "details": "..."}]
            }
        }
        shell.do_cat("t1")
        mock_os.get_kernel_status.assert_called()

    def test_do_cat_not_found(self, shell, mock_os):
        """测试 /cat 指令 (未找到)"""
        shell.do_cat("none")
        mock_os.get_kernel_status.assert_called()

    def test_do_exit(self, shell):
        """测试 /exit 指令"""
        assert shell.do_exit("") is True

    def test_do_EOF(self, shell):
        """测试 EOF (Ctrl+D)"""
        assert shell.do_EOF("") is True
