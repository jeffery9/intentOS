"""
IntentOS Unix CLI - 标准 Unix 工具接口

提供：
- 标准 Unix I/O（stdin/stdout/stderr）
- 标准 exit codes
- 管道操作支持
- 与 Rich TUI 共存

用法:
    # 交互式（Rich TUI）
    intentos cli
    intentos cli shell
    intentos cli chat

    # 非交互式（Unix 工具模式）
    intentos "分析销售数据"
    echo "分析销售数据" | intentos
    intentos < input.pef.yaml
    intentos "cmd1" | intentos "cmd2"

    # 指定输出格式
    intentos --json "分析销售数据"
    intentos --yaml "分析销售数据"
    intentos --plain "分析销售数据"

    # 从文件执行
    intentos --file input.pef.yaml

    # 验证 PEF
    intentos --validate input.pef.yaml
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console

from intentos.interface.exit_codes import ExitCode, get_exit_description
from intentos.interface.unix_io import (
    ExecutionResult,
    OutputMode,
    create_pef_from_input,
    detect_output_mode,
    detect_pipe_input,
    read_intent_from_stdin,
    write_error,
    write_log,
    write_output,
)


# =============================================================================
# RPC 客户端（内联，避免循环导入）
# =============================================================================


def _get_rpc_client():
    """延迟导入 RPC 客户端"""
    from intentos.cli.cli import RPCClient

    return RPCClient()


# =============================================================================
# 核心执行函数
# =============================================================================


async def execute_intent(
    intent_text: str,
    output_mode: OutputMode,
    user_id: str = "cli_user",
) -> ExecutionResult:
    """
    执行意图

    Args:
        intent_text: 意图文本
        output_mode: 输出模式
        user_id: 用户 ID

    Returns:
        执行结果
    """
    try:
        # 连接内核
        client = _get_rpc_client()
        await client.connect()

        try:
            # 执行
            result_text = await client.execute(intent_text)

            return ExecutionResult(
                success=True,
                message=result_text,
                command=intent_text,
                exit_code=ExitCode.SUCCESS,
            )
        finally:
            await client.disconnect()

    except ConnectionError as e:
        return ExecutionResult(
            success=False,
            message=f"连接失败: {e}",
            error=str(e),
            command=intent_text,
            exit_code=ExitCode.CONNECTION_FAILED,
        )

    except PermissionError as e:
        return ExecutionResult(
            success=False,
            message=f"权限拒绝: {e}",
            error=str(e),
            command=intent_text,
            exit_code=ExitCode.PERMISSION_DENIED,
        )

    except Exception as e:
        return ExecutionResult(
            success=False,
            message=f"执行失败: {e}",
            error=str(e),
            command=intent_text,
            exit_code=ExitCode.EXECUTION_ERROR,
        )


async def execute_pef_file(
    pef_path: str,
    output_mode: OutputMode,
) -> ExecutionResult:
    """
    执行 PEF 文件

    Args:
        pef_path: PEF 文件路径
        output_mode: 输出模式

    Returns:
        执行结果
    """
    try:
        from intentos.compiler import PEF

        # 加载 PEF
        pef = PEF.from_file(pef_path)

        # 验证
        errors = pef.validate()
        if errors:
            return ExecutionResult(
                success=False,
                message=f"PEF 验证失败: {', '.join(errors)}",
                error="; ".join(errors),
                command=f"execute {pef_path}",
                exit_code=ExitCode.VALIDATION_ERROR,
            )

        # 执行（使用 v1 兼容接口）
        v1_pef = pef.to_v1()
        client = _get_rpc_client()
        await client.connect()

        try:
            result_text = await client.execute(v1_pef.intent)

            return ExecutionResult(
                success=True,
                message=result_text,
                command=f"execute {pef_path}",
                data=pef.to_dict(),
                exit_code=ExitCode.SUCCESS,
            )
        finally:
            await client.disconnect()

    except Exception as e:
        return ExecutionResult(
            success=False,
            message=f"执行 PEF 失败: {e}",
            error=str(e),
            command=f"execute {pef_path}",
            exit_code=ExitCode.EXECUTION_ERROR,
        )


def validate_pef_file(pef_path: str) -> ExecutionResult:
    """
    验证 PEF 文件

    Args:
        pef_path: PEF 文件路径

    Returns:
        验证结果
    """
    try:
        from intentos.compiler import PEF

        # 加载 PEF
        pef = PEF.from_file(pef_path)

        # 验证
        errors = pef.validate()

        if errors:
            return ExecutionResult(
                success=False,
                message=f"PEF 验证失败: {', '.join(errors)}",
                error="; ".join(errors),
                command=f"validate {pef_path}",
                exit_code=ExitCode.VALIDATION_ERROR,
            )
        else:
            return ExecutionResult(
                success=True,
                message="PEF 验证通过",
                command=f"validate {pef_path}",
                data=pef.to_dict(),
                exit_code=ExitCode.SUCCESS,
            )

    except Exception as e:
        return ExecutionResult(
            success=False,
            message=f"验证失败: {e}",
            error=str(e),
            command=f"validate {pef_path}",
            exit_code=ExitCode.GENERAL_ERROR,
        )


# =============================================================================
# CLI 主函数
# =============================================================================


def main(args: Optional[argparse.Namespace] = None) -> None:
    """
    CLI 主函数

    Args:
        args: 命令行参数
    """
    # 解析参数
    parser = create_argument_parser()
    parsed_args = parser.parse_args()

    # 检测输出模式
    if parsed_args.json:
        output_mode = OutputMode.JSON
    elif parsed_args.yaml:
        output_mode = OutputMode.YAML
    elif parsed_args.plain:
        output_mode = OutputMode.PLAIN
    else:
        output_mode = detect_output_mode()

    # 处理 --validate
    if parsed_args.validate:
        result = validate_pef_file(parsed_args.validate)
        _handle_result(result, output_mode)
        return

    # 处理 --file
    if parsed_args.file:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(execute_pef_file(parsed_args.file, output_mode))
            _handle_result(result, output_mode)
        finally:
            loop.close()
        return

    # 获取输入
    intent_text = _get_input(parsed_args, output_mode)

    if not intent_text:
        write_error("未提供有效的输入", output_mode, ExitCode.USAGE_ERROR)
        sys.exit(ExitCode.USAGE_ERROR)

    # 执行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(execute_intent(intent_text, output_mode))
        _handle_result(result, output_mode)
    finally:
        loop.close()


def create_argument_parser() -> argparse.ArgumentParser:
    """创建参数解析器"""
    parser = argparse.ArgumentParser(
        prog="intentos",
        description="IntentOS - AI 原生操作系统（Unix 工具模式）",
        epilog="""
示例:
  # 执行意图
  intentos "分析销售数据"
  echo "分析销售数据" | intentos

  # 指定输出格式
  intentos --json "分析销售数据"
  intentos --yaml "分析销售数据"

  # 从文件执行
  intentos --file input.pef.yaml

  # 验证 PEF
  intentos --validate input.pef.yaml

  # 管道操作
  intentos "查询数据" | intentos "分析趋势"
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 输出格式
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--json",
        action="store_true",
        help="输出 JSON 格式",
    )
    output_group.add_argument(
        "--yaml",
        action="store_true",
        help="输出 YAML 格式",
    )
    output_group.add_argument(
        "--plain",
        action="store_true",
        help="输出纯文本格式",
    )

    # 操作模式
    parser.add_argument(
        "--file",
        type=str,
        help="从 PEF 文件执行",
    )
    parser.add_argument(
        "--validate",
        type=str,
        help="验证 PEF 文件",
    )

    # 位置参数（意图文本）
    parser.add_argument(
        "command",
        nargs="*",
        help="要执行的意图命令",
    )

    return parser


def _get_input(args: argparse.Namespace, output_mode: OutputMode) -> Optional[str]:
    """
    获取输入

    优先级：
    1. --file 参数
    2. 命令行参数
    3. stdin 管道
    """
    # 从文件
    if args.file:
        from intentos.compiler import PEF

        pef = PEF.from_file(args.file)
        return pef.intent.goal

    # 从命令行参数
    if args.command and len(args.command) > 0:
        # 检查是否是 stdin 标记
        if len(args.command) == 1 and args.command[0] == "-":
            # 从 stdin 读取
            try:
                return read_intent_from_stdin()
            except ValueError as e:
                write_error(str(e), output_mode, ExitCode.USAGE_ERROR)
                sys.exit(ExitCode.USAGE_ERROR)
        else:
            return " ".join(args.command)

    # 从管道
    pipe_input = detect_pipe_input()
    if pipe_input:
        return pipe_input

    return None


def _handle_result(result: ExecutionResult, output_mode: OutputMode) -> None:
    """
    处理执行结果

    Args:
        result: 执行结果
        output_mode: 输出模式
    """
    # 输出结果
    if output_mode == OutputMode.RICH:
        # Rich 模式
        console = Console()
        if result.success:
            console.print(result.message)
        else:
            console.print(f"❌ Error: {result.message}", style="red")
    else:
        # Plain/JSON/YAML 模式
        write_output(result, output_mode)

        # 错误额外输出到 stderr
        if not result.success and result.error:
            write_error(result.error, output_mode, result.exit_code)

    # 退出
    sys.exit(int(result.exit_code))


# =============================================================================
# 入口点
# =============================================================================


def unix_cli_entry():
    """Unix CLI 入口点（用于 pyproject.toml scripts）"""
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)  # Ctrl+C
    except BrokenPipeError:
        # 管道断开，正常退出
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(ExitCode.GENERAL_ERROR)


if __name__ == "__main__":
    unix_cli_entry()
