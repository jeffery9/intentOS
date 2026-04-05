"""
Unix I/O 和 CLI 测试

测试覆盖:
- Exit codes 定义
- Unix I/O 工具函数
- 输出模式检测
- 结构化输出（JSON/YAML）
- 错误处理
"""

import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest
import yaml

from intentos.interface.exit_codes import (
    ExitCode,
    get_exit_description,
)
from intentos.interface.unix_io import (
    ExecutionResult,
    OutputMode,
    create_pef_from_input,
    detect_output_mode,
    read_intent_from_stdin,
    write_error,
    write_log,
    write_output,
)


# =============================================================================
# Exit Codes 测试
# =============================================================================


class TestExitCodes:
    """退出码测试"""

    def test_exit_code_values(self):
        """测试退出码值"""
        assert ExitCode.SUCCESS == 0
        assert ExitCode.GENERAL_ERROR == 1
        assert ExitCode.PERMISSION_DENIED == 2
        assert ExitCode.USAGE_ERROR == 3
        assert ExitCode.RESOURCE_UNAVAILABLE == 4
        assert ExitCode.TIMEOUT == 5
        assert ExitCode.CONNECTION_FAILED == 6
        assert ExitCode.COMPILE_ERROR == 7
        assert ExitCode.EXECUTION_ERROR == 8
        assert ExitCode.VALIDATION_ERROR == 9
        assert ExitCode.FILE_NOT_FOUND == 10

    def test_exit_code_descriptions(self):
        """测试退出码描述"""
        for code in ExitCode:
            desc = get_exit_description(code)
            assert desc != ""
            assert isinstance(desc, str)

    def test_specific_descriptions(self):
        """测试特定描述"""
        assert get_exit_description(ExitCode.SUCCESS) == "成功"
        assert get_exit_description(ExitCode.PERMISSION_DENIED) == "权限拒绝"
        assert get_exit_description(ExitCode.CONNECTION_FAILED) == "连接失败"


# =============================================================================
# ExecutionResult 测试
# =============================================================================


class TestExecutionResult:
    """执行结果测试"""

    def test_create_success(self):
        """创建成功结果"""
        result = ExecutionResult(
            success=True,
            message="执行成功",
            command="测试命令",
        )

        assert result.success is True
        assert result.message == "执行成功"
        assert result.exit_code == ExitCode.SUCCESS

    def test_create_error(self):
        """创建错误结果"""
        result = ExecutionResult(
            success=False,
            message="执行失败",
            error="详细错误",
            exit_code=ExitCode.EXECUTION_ERROR,
        )

        assert result.success is False
        assert result.error == "详细错误"
        assert result.exit_code == ExitCode.EXECUTION_ERROR

    def test_to_dict_success(self):
        """转换为字典（成功）"""
        result = ExecutionResult(
            success=True,
            message="成功",
            command="测试",
            data={"key": "value"},
        )

        data = result.to_dict()
        assert data["status"] == "success"
        assert data["message"] == "成功"
        assert data["command"] == "测试"
        assert data["data"] == {"key": "value"}
        assert "timestamp" in data

    def test_to_dict_error(self):
        """转换为字典（错误）"""
        result = ExecutionResult(
            success=False,
            message="失败",
            error="错误详情",
            exit_code=ExitCode.PERMISSION_DENIED,
        )

        data = result.to_dict()
        assert data["status"] == "error"
        assert data["error"] == "错误详情"
        assert data["exit_code"] == 2

    def test_to_json(self):
        """导出为 JSON"""
        result = ExecutionResult(
            success=True,
            message="成功",
            command="测试",
        )

        json_str = result.to_json()
        data = json.loads(json_str)
        assert data["status"] == "success"

    def test_to_yaml(self):
        """导出为 YAML"""
        result = ExecutionResult(
            success=True,
            message="成功",
            command="测试",
        )

        yaml_str = result.to_yaml()
        data = yaml.safe_load(yaml_str)
        assert data["status"] == "success"


# =============================================================================
# Output Mode 测试
# =============================================================================


class TestOutputMode:
    """输出模式测试"""

    def test_output_mode_enum(self):
        """测试输出模式枚举"""
        assert OutputMode.RICH.value == "rich"
        assert OutputMode.PLAIN.value == "plain"
        assert OutputMode.JSON.value == "json"
        assert OutputMode.YAML.value == "yaml"

    @patch("sys.stdout.isatty", return_value=True)
    def test_detect_tty_rich(self, mock_isatty):
        """检测 TTY -> Rich 模式"""
        with patch.dict("os.environ", {}, clear=True):
            mode = detect_output_mode()
            assert mode == OutputMode.RICH

    @patch("sys.stdout.isatty", return_value=False)
    def test_detect_pipe_plain(self, mock_isatty):
        """检测管道 -> Plain 模式"""
        with patch.dict("os.environ", {}, clear=True):
            mode = detect_output_mode()
            assert mode == OutputMode.PLAIN

    @patch.dict("os.environ", {"INTENTOS_OUTPUT_MODE": "json"})
    def test_env_json(self):
        """环境变量 JSON"""
        mode = detect_output_mode()
        assert mode == OutputMode.JSON

    @patch.dict("os.environ", {"INTENTOS_OUTPUT_MODE": "yaml"})
    def test_env_yaml(self):
        """环境变量 YAML"""
        mode = detect_output_mode()
        assert mode == OutputMode.YAML

    @patch.dict("os.environ", {"INTENTOS_OUTPUT_MODE": "plain"})
    def test_env_plain(self):
        """环境变量 Plain"""
        mode = detect_output_mode()
        assert mode == OutputMode.PLAIN


# =============================================================================
# Stdin 读取测试
# =============================================================================


class TestStdinRead:
    """Stdin 读取测试"""

    def test_read_non_empty(self):
        """读取非空输入"""
        input_data = "测试意图\n"
        with patch("sys.stdin.read", return_value=input_data):
            result = read_intent_from_stdin()
            assert result == "测试意图"

    def test_read_empty(self):
        """读取空输入"""
        with patch("sys.stdin.read", return_value=""):
            with pytest.raises(ValueError, match="为空"):
                read_intent_from_stdin()

    def test_read_multiline(self):
        """读取多行输入"""
        input_data = "第一行\n第二行\n第三行\n"
        with patch("sys.stdin.read", return_value=input_data):
            result = read_intent_from_stdin()
            assert "第一行" in result
            assert "第二行" in result


# =============================================================================
# 输出写入测试
# =============================================================================


class TestOutputWrite:
    """输出写入测试"""

    def test_write_output_plain(self, capsys):
        """写入 plain 输出"""
        result = ExecutionResult(
            success=True,
            message="成功消息",
            command="测试",
        )

        write_output(result, OutputMode.PLAIN)
        captured = capsys.readouterr()

        assert "成功消息" in captured.out

    def test_write_output_json(self, capsys):
        """写入 JSON 输出"""
        result = ExecutionResult(
            success=True,
            message="成功消息",
            command="测试",
        )

        write_output(result, OutputMode.JSON)
        captured = capsys.readouterr()

        data = json.loads(captured.out)
        assert data["status"] == "success"
        assert data["message"] == "成功消息"

    def test_write_output_yaml(self, capsys):
        """写入 YAML 输出"""
        result = ExecutionResult(
            success=True,
            message="成功消息",
            command="测试",
        )

        write_output(result, OutputMode.YAML)
        captured = capsys.readouterr()

        data = yaml.safe_load(captured.out)
        assert data["status"] == "success"

    def test_write_error_plain(self, capsys):
        """写入错误（plain）"""
        write_error("错误消息", OutputMode.PLAIN, ExitCode.GENERAL_ERROR)
        captured = capsys.readouterr()

        assert "错误消息" in captured.err

    def test_write_error_json(self, capsys):
        """写入错误（JSON）"""
        write_error("错误消息", OutputMode.JSON, ExitCode.PERMISSION_DENIED)
        captured = capsys.readouterr()

        data = json.loads(captured.err)
        assert data["status"] == "error"
        assert data["error"] == "错误消息"
        assert data["exit_code"] == 2

    def test_write_log_plain(self, capsys):
        """写入日志（plain）"""
        write_log("信息消息", "info", OutputMode.PLAIN)
        captured = capsys.readouterr()

        assert "信息消息" in captured.err

    def test_write_log_json(self, capsys):
        """写入日志（JSON）"""
        write_log("信息消息", "info", OutputMode.JSON)
        captured = capsys.readouterr()

        data = json.loads(captured.err)
        assert data["level"] == "info"
        assert data["message"] == "信息消息"


# =============================================================================
# PEF 创建测试
# =============================================================================


class TestPEFCreation:
    """PEF 创建测试"""

    def test_create_from_text(self):
        """从文本创建"""
        input_text = "分析销售数据"
        pef = create_pef_from_input(input_text, user_id="test_user")

        assert pef.intent.goal == "分析销售数据"
        assert pef.context.user_id == "test_user"

    def test_create_from_json(self):
        """从 JSON 创建"""
        json_input = json.dumps({
            "version": "2.0",
            "id": "pef_test",
            "compiled_at": "2026-04-05T14:30:25",
            "intent": {"goal": "JSON 测试"},
            "context": {"user_id": "test_user"},
            "capabilities": [],
        })

        pef = create_pef_from_input(json_input)
        assert pef.intent.goal == "JSON 测试"

    def test_create_from_yaml(self):
        """从 YAML 创建"""
        yaml_input = """
version: "2.0"
id: "pef_yaml_test"
compiled_at: "2026-04-05T14:30:25"
intent:
  goal: "YAML 测试"
context:
  user_id: "test_user"
capabilities: []
"""
        pef = create_pef_from_input(yaml_input)
        assert pef.intent.goal == "YAML 测试"


# =============================================================================
# 集成测试
# =============================================================================


class TestIntegration:
    """集成测试"""

    def test_full_workflow_json(self, capsys):
        """完整工作流（JSON 输出）"""
        # 创建结果
        result = ExecutionResult(
            success=True,
            message="执行成功",
            command="分析销售数据",
            data={"sales": 1000000},
            metadata={"duration_ms": 1500},
        )

        # 输出
        write_output(result, OutputMode.JSON)
        captured = capsys.readouterr()

        # 验证
        data = json.loads(captured.out)
        assert data["status"] == "success"
        assert data["data"]["sales"] == 1000000
        assert data["metadata"]["duration_ms"] == 1500

    def test_error_workflow_yaml(self, capsys):
        """错误工作流（YAML 输出）"""
        # 创建错误结果
        result = ExecutionResult(
            success=False,
            message="权限拒绝",
            error="用户没有执行权限",
            exit_code=ExitCode.PERMISSION_DENIED,
        )

        # 输出到 stdout
        write_output(result, OutputMode.YAML)
        # 错误到 stderr
        write_error(result.error, OutputMode.YAML, result.exit_code)

        captured = capsys.readouterr()

        # 验证 stdout
        stdout_data = yaml.safe_load(captured.out)
        assert stdout_data["status"] == "error"
        assert stdout_data["exit_code"] == 2

        # 验证 stderr
        stderr_data = yaml.safe_load(captured.err)
        assert stderr_data["status"] == "error"
        assert stderr_data["error"] == "用户没有执行权限"
