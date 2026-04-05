#!/usr/bin/env python3
"""
IntentOS 统一启动入口

用法:
    python -m intentos daemon     # 启动内核守护进程（服务器）
    python -m intentos cli        # 命令行工具（包含 shell、chat 等）
    python -m intentos "意图"     # 直接执行意图（Unix 工具模式）
"""

import argparse
import sys


def start_daemon(args):
    """启动守护进程（服务器）"""
    from intentos.interface.daemon import start_daemon

    start_daemon(args)


def run_cli(args):
    """运行命令行工具"""
    from intentos.cli.cli import main

    main(args)


def run_unix_cli(args):
    """运行 Unix 工具模式"""
    from intentos.interface.unix_cli import unix_cli_entry

    unix_cli_entry()


def main():
    parser = argparse.ArgumentParser(
        prog="intentos",
        description="IntentOS - AI 原生操作系统",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s 16.0.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="启动模式")

    # daemon 命令
    p_daemon = subparsers.add_parser(
        "daemon",
        help="启动内核守护进程（服务器模式）",
        description="启动 IntentOS 内核并监听 RPC 请求",
    )
    p_daemon.add_argument("--api", action="store_true", help="同时启动 API 网关")
    p_daemon.add_argument("--api-host", default="localhost", help="API 监听地址 (默认：localhost)")
    p_daemon.add_argument("--api-port", type=int, default=8080, help="API 监听端口 (默认：8080)")
    p_daemon.set_defaults(func=start_daemon)

    # cli 命令（包含 shell、chat 等）
    p_cli = subparsers.add_parser(
        "cli", help="命令行工具", description="提供 shell、chat、图谱管理、验证、轨迹等工具命令"
    )
    p_cli.add_argument("--non-interactive", action="store_true", help="运行在非交互模式")
    p_cli.add_argument("--json", action="store_true", help="输出 JSON 格式")
    p_cli.add_argument("--yaml", action="store_true", help="输出 YAML 格式")
    p_cli.add_argument("--plain", action="store_true", help="使用纯文本输出（禁用 Rich 格式）")
    p_cli.add_argument("command", nargs="*", help="要执行的命令（使用 '-' 从 stdin 读取）")
    p_cli.set_defaults(func=run_cli)

    args = parser.parse_args()

    if args.command is None:
        # 检查是否有位置参数（直接执行意图）
        remaining_args = sys.argv[1:]
        if remaining_args and not remaining_args[0].startswith("-"):
            # 直接执行意图（Unix 工具模式）
            run_unix_cli(None)
        else:
            parser.print_help()
            print("\n" + "=" * 60)
            print("快速开始:")
            print("=" * 60)
            print("1. 启动内核（必须先执行）:")
            print("   intentos daemon              # 仅内核")
            print("   intentos daemon --api        # 内核 + API 网关")
            print()
            print("2. 访问内核（使用 CLI）:")
            print("   intentos cli                 # 进入 CLI 主界面")
            print("   intentos cli shell           # 交互式 Shell")
            print("   intentos cli chat            # Chat TUI 界面")
            print("   intentos cli status          # 系统状态")
            print()
            print("3. Unix 工具模式（直接执行）:")
            print('   intentos "分析销售数据"       # 执行意图')
            print('   echo "分析销售数据" | intentos  # 管道输入')
            print('   intentos --json "分析销售数据"  # JSON 输出')
            print("   intentos --file input.pef.yaml  # 从文件执行")
            print("   intentos --validate input.pef.yaml  # 验证 PEF")
            print()
            print("4. API 访问:")
            print("   # 方式 1：集成到 daemon（推荐）")
            print("   intentos daemon --api")
            print()
            print("   curl http://localhost:8080/v1/status")
            print("=" * 60)
            sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
