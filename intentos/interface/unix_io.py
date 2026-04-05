"""
IntentOS Unix I/O 支持

提供标准 Unix 输入输出支持：
- stdin 读取意图（支持多行输入）
- stdout 输出执行结果（结构化 JSON/YAML）
- stderr 输出日志和错误信息
- 标准 exit codes
- 管道操作支持

与现有 Rich TUI 界面共存，通过 --plain 或环境变量切换模式。
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import yaml

from intentos.interface.exit_codes import ExitCode


# =============================================================================
# 输出模式枚举
# =============================================================================


class OutputMode(Enum):
    """输出模式"""

    RICH = "rich"  # Rich TUI 格式（默认，交互式）
    PLAIN = "plain"  # 纯文本格式（Unix 管道友好）
    JSON = "json"  # JSON 格式（程序友好）
    YAML = "yaml"  # YAML 格式（人类可读程序友好）


# =============================================================================
# 输出结果数据类
# =============================================================================


@dataclass
class ExecutionResult:
    """执行结果"""

    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    command: str = ""
    exit_code: ExitCode = ExitCode.SUCCESS
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result: dict[str, Any] = {
            "status": "success" if self.success else "error",
            "message": self.message,
            "exit_code": int(self.exit_code),
            "timestamp": datetime.now().isoformat(),
        }

        if self.command:
            result["command"] = self.command

        if self.data is not None:
            result["data"] = self.data

        if self.error:
            result["error"] = self.error

        if self.metadata:
            result["metadata"] = self.metadata

        return result

    def to_json(self, indent: int = 2) -> str:
        """导出为 JSON"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_yaml(self) -> str:
        """导出为 YAML"""
        return yaml.dump(
            self.to_dict(),
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )


# =============================================================================
# Unix I/O 工具函数
# =============================================================================


def detect_output_mode() -> OutputMode:
    """
    检测输出模式

    优先级：
    1. INTENTOS_OUTPUT_MODE 环境变量
    2. --plain / --json / --yaml 参数（由调用者处理）
    3. 检测 stdout 是否为 TTY（非 TTY 自动切换到 plain 模式）
    """
    # 检查环境变量
    env_mode = os.environ.get("INTENTOS_OUTPUT_MODE", "").lower()
    if env_mode in ("plain", "text", "txt"):
        return OutputMode.PLAIN
    elif env_mode == "json":
        return OutputMode.JSON
    elif env_mode == "yaml":
        return OutputMode.YAML
    elif env_mode == "rich":
        return OutputMode.RICH

    # 检测是否为 TTY
    if not sys.stdout.isatty():
        # 非 TTY（管道或重定向），默认 plain 模式
        return OutputMode.PLAIN

    return OutputMode.RICH


def read_intent_from_stdin() -> str:
    """
    从 stdin 读取意图

    支持：
    - 单行输入
    - 多行输入（直到 EOF）
    - 自动检测 JSON/YAML 格式

    Returns:
        意图文本或 PEF 内容

    Raises:
        ValueError: 如果输入为空
    """
    # 读取所有输入
    input_data = sys.stdin.read().strip()

    if not input_data:
        raise ValueError("从 stdin 读取的输入为空")

    return input_data


def write_output(result: ExecutionResult, mode: OutputMode = OutputMode.PLAIN) -> None:
    """
    写入输出到 stdout

    Args:
        result: 执行结果
        mode: 输出模式
    """
    if mode == OutputMode.JSON:
        print(result.to_json())
    elif mode == OutputMode.YAML:
        print(result.to_yaml())
    elif mode == OutputMode.PLAIN:
        if result.success:
            print(result.message)
        else:
            # 错误消息也输出到 stdout（plain 模式）
            print(result.message)
    else:
        # Rich 模式由调用者处理
        pass


def write_error(message: str, mode: OutputMode = OutputMode.PLAIN, exit_code: ExitCode = ExitCode.GENERAL_ERROR) -> None:
    """
    写入错误到 stderr

    Args:
        message: 错误消息
        mode: 输出模式
        exit_code: 退出码
    """
    if mode == OutputMode.JSON:
        error_data = {
            "status": "error",
            "error": message,
            "exit_code": int(exit_code),
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(error_data, indent=2, ensure_ascii=False), file=sys.stderr)
    elif mode == OutputMode.YAML:
        error_data = {
            "status": "error",
            "error": message,
            "exit_code": int(exit_code),
            "timestamp": datetime.now().isoformat(),
        }
        print(
            yaml.dump(error_data, allow_unicode=True, default_flow_style=False),
            file=sys.stderr,
        )
    else:
        # Plain 或 Rich 模式
        print(f"Error: {message}", file=sys.stderr)


def write_log(message: str, level: str = "info", mode: OutputMode = OutputMode.PLAIN) -> None:
    """
    写入日志到 stderr

    Args:
        message: 日志消息
        level: 日志级别（info/warn/error/debug）
        mode: 输出模式
    """
    if mode in (OutputMode.JSON, OutputMode.YAML):
        # 结构化日志
        log_data = {
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        if mode == OutputMode.JSON:
            print(json.dumps(log_data, ensure_ascii=False), file=sys.stderr)
        else:
            print(yaml.dump(log_data, allow_unicode=True), file=sys.stderr)
    else:
        # Plain 模式
        prefix = {
            "info": "ℹ️ ",
            "warn": "⚠️ ",
            "error": "❌",
            "debug": "🔍",
        }.get(level, "")
        print(f"{prefix} {message}", file=sys.stderr)


def exit_with_code(exit_code: ExitCode) -> None:
    """
    使用指定退出码退出

    Args:
        exit_code: 退出码
    """
    sys.exit(int(exit_code))


# =============================================================================
# 管道支持
# =============================================================================


def detect_pipe_input() -> Optional[str]:
    """
    检测是否有管道输入

    Returns:
        管道输入内容，如果没有则返回 None
    """
    # 检查 stdin 是否为管道
    if not sys.stdin.isatty():
        try:
            return read_intent_from_stdin()
        except Exception:
            return None
    return None


def create_pef_from_input(
    input_data: str,
    user_id: str = "stdin_user",
) -> Any:
    """
    从输入创建 PEF

    自动检测输入格式：
    - JSON/YAML: 直接解析为 PEF
    - 纯文本: 作为意图目标编译

    Args:
        input_data: 输入数据
        user_id: 用户 ID

    Returns:
        PEF 实例
    """
    from intentos.compiler import PEF, IntentCompilerV2

    input_stripped = input_data.strip()

    # 检测格式
    if input_stripped.startswith("{"):
        # JSON 格式
        return PEF.from_json(input_stripped)
    elif input_stripped.startswith("version:") or input_stripped.startswith("---"):
        # YAML 格式
        return PEF.from_yaml(input_stripped)
    else:
        # 纯文本，编译为 PEF
        compiler = IntentCompilerV2()
        return compiler.compile(
            goal=input_stripped,
            user_id=user_id,
        )
